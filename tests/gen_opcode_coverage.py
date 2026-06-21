"""Opcode-variant coverage tests generated from z8000_opcodes.csv.

These tests are intended for golden capture/compare coverage.  They generate
one assembler-verified smoke test for each safe instruction form that can be
run as a single instruction before the normal dump trampoline.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
import tempfile
from functools import lru_cache

from .defs import TestCase
from .flags import FCW_SYS
from .helpers import CODE_BASE, OPERAND_BASE, STACK_BASE
from .observability import add_observations


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPCODES_CSV = os.path.join(PROJECT_ROOT, "z8000_micro", "z8000_opcodes.csv")

# Forms that do not naturally fall through to the dump routine, alter machine
# control state too aggressively for a smoke test, or are already covered by
# targeted control-flow tests.
SKIP_MNEMONICS = {
    "CALL",
    "CALR",
    "HALT",
    "IRET",
    "LDCTL",
    "LDCTLB",
    "LDPS",
    "MBIT",
    "MREQ",
    "MRES",
    "MSET",
    "RET",
    "SC",
}

DYNAMIC_SHIFT_MNEMONICS = {"SDA", "SDAB", "SDAL", "SDL", "SDLB", "SDLL"}
DYNAMIC_BIT_MNEMONICS = {"BIT", "BITB", "SET", "SETB", "RES", "RESB"}
RELATIVE_LOAD_MNEMONICS = {"LDR", "LDRB", "LDRL"}
TRANSLATE_MNEMONICS = {"TRDB", "TRDRB", "TRIB", "TRIRB"}
TRANSLATE_TEST_MNEMONICS = {"TRTDB", "TRTDRB", "TRTIB", "TRTIRB"}
BLOCK_POINTER_MNEMONICS = {
    "CPI", "CPIR", "CPD", "CPDR", "CPIB", "CPIRB", "CPDB", "CPDRB",
    "CPSI", "CPSIR", "CPSD", "CPSDR", "CPSIB", "CPSIRB", "CPSDB", "CPSDRB",
    "LDI", "LDIR", "LDD", "LDDR", "LDIB", "LDIRB", "LDDB", "LDDRB",
    "TRDB", "TRDRB", "TRIB", "TRIRB",
    "TRTDB", "TRTDRB", "TRTIB", "TRTIRB",
}
BLOCK_INPUT_MNEMONICS = {
    "IND", "INDB", "INDR", "INDRB", "INI", "INIB", "INIR", "INIRB",
    "SIND", "SINDB", "SINDR", "SINDRB", "SINI", "SINIB", "SINIR", "SINIRB",
}
BLOCK_OUTPUT_MNEMONICS = {
    "OUTD", "OUTDB", "OUTI", "OUTIB", "OTDR", "OTDRB", "OTIR", "OTIRB",
    "SOUTD", "SOUTDB", "SOUTI", "SOUTIB", "SOTDR", "SOTDRB", "SOTIR", "SOTIRB",
}
# Block instructions that WRITE memory at @Rdest (transfer, translate, input).
# Their opcode-coverage destination pointer is relocated to a safe scratch
# offset so the write can never land on the bootstrap dump routine.  This
# mirrors the segmented side (gen_seg_systematic._SEG_BLOCK_DST_OFFSET); using
# the same offset keeps the two modes consistent.
BLOCK_WRITE_MNEMONICS = (
    {"LDD", "LDDB", "LDDR", "LDDRB", "LDI", "LDIB", "LDIR", "LDIRB"}
    | {"TRDB", "TRDRB", "TRIB", "TRIRB", "TRTDB", "TRTDRB", "TRTIB", "TRTIRB"}
    | {"IND", "INDB", "INDR", "INDRB", "INI", "INIB", "INIR", "INIRB",
       "SIND", "SINDB", "SINDR", "SINDRB", "SINI", "SINIB", "SINIR", "SINIRB"}
)
BLOCK_WRITE_DST_OFFSET = 0x0800
OUTPUT_MNEMONICS = {
    "OUT", "OUTB", "OUTD", "OUTDB", "OUTI", "OUTIB", "OTDR", "OTDRB",
    "OTIR", "OTIRB", "SOUTD", "SOUTDB", "SOUTI", "SOUTIB", "SOTDR",
    "SOTDRB", "SOTIR", "SOTIRB",
}
INPUT_MNEMONICS = {
    "IN", "INB", "IND", "INDB", "INDR", "INDRB", "INI", "INIB", "INIR",
    "INIRB", "SIND", "SINDB", "SINDR", "SINDRB", "SINI", "SINIB",
    "SINIR", "SINIRB",
}


def generate_opcode_coverage_tests():
    """Generate non-segmented opcode coverage tests."""
    tests = []
    for index, row in enumerate(_opcode_rows(), start=1):
        tc = _make_test(index, row)
        if tc is not None:
            tests.append(tc)
    return tests


def generate_segmented_opcode_coverage_tests():
    """Generate segmented variants of opcode coverage tests."""
    from .gen_seg_systematic import _transform

    tests = []
    for index, row in enumerate(_opcode_rows(), start=1):
        tc = _make_test(index, row, segmented=True)
        if tc is not None:
            tests.extend(_transform(tc))
    return tests


def _opcode_rows():
    with open(OPCODES_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _make_test(index, row, segmented=False):
    mnemonic = row["instruction"]
    if mnemonic in SKIP_MNEMONICS:
        return None

    mode = row["addressing_mode"]
    asm = _instantiate(row["syntax"], segmented=segmented, mode=mode)
    use_z8001_asm = segmented and mode in {"IR", "BA", "BX"}
    words = _assemble(asm, z8001=use_z8001_asm)
    if words is None:
        return None

    name = (
        f"cov_{index:03d}_{mnemonic.lower()}_"
        f"{_mode_name(mode)}_{_slug(row['syntax'])}"
    )
    tags = ["opcode_coverage", f"{_mode_name(mode)}_mode"]
    memory = _base_memory()
    if mnemonic == "CPB" and "#data" in row["syntax"] and row["addressing_mode"] in {"IR", "DA", "X"}:
        memory[OPERAND_BASE] = 0x0000
        memory[OPERAND_BASE + 0x10] = 0x0000
    elif mnemonic in RELATIVE_LOAD_MNEMONICS:
        _setup_relative_load_memory(memory, asm, words)
    elif mnemonic in TRANSLATE_MNEMONICS:
        memory[OPERAND_BASE] = 0x0000
        memory[OPERAND_BASE - 2] = 0x0000
        memory[0x0500] = 0x0000

    regs = _base_regs(mnemonic, asm)
    if mnemonic in BLOCK_WRITE_MNEMONICS:
        # Define the relocated destination word.  The translate ops (TR*/TRT*)
        # read this byte as the table index, so leaving it uninitialized makes
        # the result depend on RAM contents (sim reads 0, hardware reads
        # garbage).  Harmless for the write-only ops, which overwrite it.  Set
        # for both modes so the segmented clone inherits it.
        memory[BLOCK_WRITE_DST_OFFSET] = 0x0000
        # Non-segmented block writes: relocate @Rdest off the dump routine.  The
        # segmented path relocates its own pointers in gen_seg_systematic.
        if not segmented:
            m = re.search(r"@rr?(\d+)", asm)
            if m:
                regs[int(m.group(1))] = BLOCK_WRITE_DST_OFFSET

    tc = TestCase(
        name=name,
        mnemonic=mnemonic,
        description=f"Opcode coverage: {asm}",
        tags=tags,
        instruction=asm,
        code=words,
        regs=regs,
        fcw=FCW_SYS,
        memory=memory,
        io_preloads={
            0: 0x1234, 1: 0x5678, 2: 0x9ABC, 3: 0xDEF0,
            6: 0x4321, 7: 0x8765, 8: 0xCBA9, 9: 0x0FED,
        },
    )
    return add_observations(tc)


def _base_regs(mnemonic=None, asm=""):
    regs = {
        0: 0x1111,
        1: OPERAND_BASE,
        2: OPERAND_BASE,
        3: 0x0010,
        4: 0x0001,
        5: 0x2222,
        6: 0x3333,
        7: 0x4444,
        8: 0x1111,
        9: 0x2222,
        10: 0x3333,
        11: 0x0010,
        12: 0x4444,
        13: 0x0004,
        14: STACK_BASE,
        15: STACK_BASE,
    }
    if mnemonic in DYNAMIC_SHIFT_MNEMONICS | DYNAMIC_BIT_MNEMONICS:
        regs[4] = 0x0001
    elif mnemonic in TRANSLATE_MNEMONICS:
        regs[1] = 0x0500
        regs[2] = OPERAND_BASE
        regs[4] = 0x0001
    if mnemonic not in BLOCK_POINTER_MNEMONICS:
        for reg in _indirect_registers(asm):
            regs[reg] = _pointer_base_for(mnemonic, asm, reg)
    for reg in _address_index_registers(asm):
        regs[reg] = OPERAND_BASE
    for reg in _base_displacement_registers(asm):
        regs[reg] = OPERAND_BASE
    for reg in _base_index_base_registers(asm):
        regs[reg] = OPERAND_BASE
    for reg in _base_index_registers(asm):
        regs[reg] = 0x0010
    return regs


def _indirect_registers(asm):
    return {
        int(m.group(1) or m.group(2))
        for m in re.finditer(r"@(?:rr(\d+)|r(\d+))", asm)
    }


def _address_index_registers(asm):
    return {int(m.group(1)) for m in re.finditer(r"0x[0-9a-fA-F]+\(r(\d+)\)", asm)}


def _base_index_registers(asm):
    return {
        int(m.group(1))
        for m in re.finditer(r"\b(?:rr?\d+)\(r(\d+)\)", asm)
    }


def _base_index_base_registers(asm):
    return {
        int(m.group(1))
        for m in re.finditer(r"\b(?:rr|r)(\d+)\(r\d+\)", asm)
    }


def _base_displacement_registers(asm):
    return {
        int(m.group(1))
        for m in re.finditer(r"\b(?:rr|r)(\d+)\(#", asm)
    }


def _pointer_base_for(mnemonic, asm, reg):
    if reg == 15:
        return STACK_BASE
    if mnemonic in OUTPUT_MNEMONICS:
        regs = _indirect_registers_ordered(asm)
        if regs and regs[0] == reg:
            return _io_port_for(mnemonic)
    if mnemonic in INPUT_MNEMONICS:
        regs = _indirect_registers_ordered(asm)
        if regs and regs[-1] == reg:
            return _io_port_for(mnemonic)
    if mnemonic in TRANSLATE_MNEMONICS and "@r5" in asm and reg == 5:
        return 0x0500
    if mnemonic.startswith("TRT") and reg == 5:
        return 0x0500
    return OPERAND_BASE


def _indirect_registers_ordered(asm):
    return [int(m.group(1)) for m in re.finditer(r"@r(\d+)", asm)]


def _io_port_for(mnemonic):
    return 0x0104 if mnemonic.endswith("B") else 0x0106


def _base_memory():
    mem = {}
    for off, val in enumerate((0x0001, 0x0002, 0x0003, 0x0004)):
        mem[OPERAND_BASE + off * 2] = val
        mem[OPERAND_BASE + 0x10 + off * 2] = val
        mem[STACK_BASE + off * 2] = val
    return mem


def _setup_relative_load_memory(memory, asm, words):
    if len(words) < 2:
        return
    displacement = words[1]
    if displacement & 0x8000:
        displacement -= 0x10000
    target = (CODE_BASE + len(words) * 2 + displacement) & 0xFFFF

    if asm.startswith("ldr ") and ", 0x" in asm:
        memory[target] = 0x0602
    elif asm.startswith("ldrb ") and ", 0x" in asm:
        memory[target] = 0x0602
    elif asm.startswith("ldrl ") and ", 0x" in asm:
        memory[target] = 0x0602
        memory[(target + 2) & 0xFFFF] = 0x0604


def _instantiate(syntax, segmented=False, mode=None):
    parts = syntax.split(" ", 1)
    mnemonic = parts[0]
    operands = parts[1] if len(parts) > 1 else ""

    # Use non-zero indirect/index registers because R0 is illegal for IR/X.
    replacements = _segmented_replacements() if segmented else [
        ("Rs1", "r3"),
        ("Rs2", "r1"),
        ("Rbs", "rh1"),
        ("Rbd", "rh0"),
        ("RRs", "rr2"),
        ("RRd", "rr0"),
        ("RQd", "rq0"),
        ("Rx", "r3"),
        ("Rd", "r2"),
        ("Rs", "r1"),
        ("Rb", "rh0"),
        ("FCW", "fcw"),
        ("FLAGS", "flags"),
        ("REFRESH", "refresh"),
        ("PSAPSEG", "psapseg"),
        ("PSAP", "psap"),
        ("NSPSEG", "nspseg"),
        ("NSP", "nsp"),
        ("cc", "f"),
        ("flags", "c"),
        ("int", "vi"),
        ("address", "0x0400"),
        ("addr", "0x0010"),
        ("#data", "#0x0001"),
        ("#disp", "#0x0010"),
        ("#src", "#0"),
        ("#n", "#1"),
        ("#b", "#1"),
    ]
    for src, dst in replacements:
        operands = operands.replace(src, dst)
    operands = operands.replace("port", f"#{_io_port_for(mnemonic):#06x}")

    if segmented and mode in {"BA", "BX"} and mnemonic == "LDA":
        operands = re.sub(r"^r8(?=,|$)", "rr8", operands)

    if segmented and mode in {"BA", "BX"}:
        operands = _segmented_pair_base_operands(operands)

    if segmented and mode == "IR":
        operands = _segmented_indirect_operands(mnemonic, operands)

    src_reg = "r5" if segmented else "r1"

    if mnemonic in DYNAMIC_SHIFT_MNEMONICS | DYNAMIC_BIT_MNEMONICS:
        operands = re.sub(rf", {src_reg}$", ", r4", operands)
    elif mnemonic in TRANSLATE_MNEMONICS:
        pass
    elif mnemonic == "POP":
        stack_reg = "r14" if segmented else "r15"
        operands = operands.replace(f"@{src_reg}", f"@{stack_reg}")
    elif mnemonic == "POPL":
        stack_reg = "r14" if segmented else "r15"
        operands = operands.replace(f"@{src_reg}", f"@{stack_reg}")
        operands = operands.replace("rr0,", "rr4,").replace("rr8,", "rr4,")

    operands = re.sub(r"(?<=, )r(?=,|$)", "r4", operands)
    operands = re.sub(r"(?<= )R(?=,|$)", "r2", operands)
    operands = operands.replace("(0x0010)r1", "0x0010(r1)")
    operands = operands.replace("(0x0010)r2", "0x0010(r2)")
    operands = operands.replace("(0x0010)r3", "0x0010(r3)")
    operands = operands.replace("(0x0010)r5", "0x0010(r5)")
    operands = operands.replace("(0x0010)r8", "0x0010(r8)")
    operands = operands.replace("(0x0010)r11", "0x0010(r11)")
    operands = re.sub(r"(r\d+)\((0x[0-9a-fA-F]+)\)", r"\2(\1)", operands)

    # Keep branch smoke tests non-taking so they fall through to the dump jump.
    if mnemonic in {"JP", "JR"}:
        operands = operands.replace("t,", "f,")

    if mnemonic == "DJNZ":
        operands = operands.replace("R,", "r4,")
    elif mnemonic == "DBJNZ":
        operands = operands.replace("Rb,", "rh0,")
    elif mnemonic == "LDK":
        operands = operands.replace("#0x0001", "#1")

    return (mnemonic + (f" {operands}" if operands else "")).lower()


def _segmented_pair_base_operands(operands):
    """Use Z8001 register-pair syntax for BA/BX memory base operands."""
    operands = re.sub(r"\br5(?=\(#)", "rr4", operands)
    operands = re.sub(r"\br5(?=\(r)", "rr4", operands)
    operands = re.sub(r"\br8(?=\(#)", "rr8", operands)
    operands = re.sub(r"\br8(?=\(r)", "rr8", operands)
    return operands


def _segmented_indirect_operands(mnemonic, operands):
    """Use Z8001 pair syntax only for operands that address memory."""
    if mnemonic in BLOCK_INPUT_MNEMONICS:
        operands = re.sub(r"@r8\b", "@rr8", operands)
    elif mnemonic in BLOCK_OUTPUT_MNEMONICS:
        operands = re.sub(r"@r5\b", "@rr4", operands)
    elif mnemonic in TRANSLATE_MNEMONICS | TRANSLATE_TEST_MNEMONICS:
        operands = re.sub(r"@r9\b", "@rr8", operands)
        operands = re.sub(r"@r8\b", "@rr8", operands)
        operands = re.sub(r"@r5\b", "@rr4", operands)
    else:
        operands = re.sub(r"@r5\b", "@rr4", operands)
        operands = re.sub(r"@r8\b", "@rr8", operands)
    return operands


def _segmented_replacements():
    return [
        ("Rs1", "r9"),
        ("Rs2", "r5"),
        ("Rbs", "rh1"),
        ("Rbd", "rh0"),
        ("RRs", "rr12"),
        ("RRd", "rr8"),
        ("RQd", "rq8"),
        ("Rx", "r11"),
        ("Rd", "r8"),
        ("Rs", "r5"),
        ("Rb", "rh0"),
        ("FCW", "fcw"),
        ("FLAGS", "flags"),
        ("REFRESH", "refresh"),
        ("PSAPSEG", "psapseg"),
        ("PSAP", "psap"),
        ("NSPSEG", "nspseg"),
        ("NSP", "nsp"),
        ("cc", "f"),
        ("flags", "c"),
        ("int", "vi"),
        ("address", "0x0400"),
        ("addr", "0x0010"),
        ("#data", "#0x0001"),
        ("#disp", "#0x0010"),
        ("#src", "#0"),
        ("#n", "#1"),
        ("#b", "#1"),
    ]


@lru_cache(maxsize=None)
def _assemble(asm, z8001=False):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "test.s")
        obj = os.path.join(td, "test.o")
        with open(src, "w") as f:
            f.write(f"    {asm}\n")

        cpu = "-z8001" if z8001 else "-z8002"
        result = subprocess.run(
            ["z8k-coff-as", cpu, src, "-o", obj],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        dump = subprocess.run(
            ["z8k-coff-objdump", "-d", obj],
            capture_output=True,
            text=True,
            check=True,
        )
    return _parse_objdump_words(dump.stdout)


def _parse_objdump_words(output):
    words = []
    for line in output.splitlines():
        # Stop at the disassembled mnemonic column. Some mnemonics, e.g. "decb",
        # are also valid hex text and must not be parsed as instruction words.
        m = re.match(r"\s*[0-9a-f]+:\s+((?:[0-9a-f]{4}\s)+)", line)
        if not m:
            continue
        words.extend(int(w, 16) for w in m.group(1).split())
    return words


def _mode_name(mode):
    return "none" if mode == "-" else mode.lower()


def _slug(value):
    value = value.lower()
    value = value.replace("#", "imm")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")
