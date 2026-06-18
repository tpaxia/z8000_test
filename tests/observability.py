"""Readback observation helpers for golden capture tests."""

from __future__ import annotations

import re


WORD_DEST_MNEMONICS = {
    "CLR", "COM", "DEC", "INC", "LD", "LDR", "NEG", "RES", "SET", "TSET",
}
BYTE_DEST_MNEMONICS = {
    "CLRB", "COMB", "DECB", "INCB", "LDB", "LDRB", "NEGB", "RESB", "SETB",
    "TSETB",
}
LONG_DEST_MNEMONICS = {"LDL", "LDRL"}
LDM_MNEMONICS = {"LDM"}
BLOCK_WORD_WRITE_MNEMONICS = {"LDI", "LDIR", "LDD", "LDDR"}
BLOCK_BYTE_WRITE_MNEMONICS = {"LDIB", "LDIRB", "LDDB", "LDDRB"}
INPUT_BLOCK_MNEMONICS = {
    "IND", "INDR", "INI", "INIR", "SIND", "SINDR", "SINI", "SINIR",
}
INPUT_BLOCK_BYTE_MNEMONICS = {
    "INDB", "INDRB", "INIB", "INIRB", "SINDB", "SINDRB", "SINIB", "SINIRB",
}
OUTPUT_MNEMONICS = {
    "OUT", "OUTB", "SOUT", "SOUTB",
    "OUTD", "OUTDB", "OUTI", "OUTIB", "OTDR", "OTDRB", "OTIR", "OTIRB",
    "SOUTD", "SOUTDB", "SOUTI", "SOUTIB", "SOTDR", "SOTDRB", "SOTIR", "SOTIRB",
}
TRANSLATE_MNEMONICS = {
    "TRDB", "TRDRB", "TRIB", "TRIRB", "TRTDB", "TRTDRB", "TRTIB", "TRTIRB",
}
PUSH_MNEMONICS = {"PUSH", "PUSHL"}
POP_MNEMONICS = {"POP", "POPL"}


def add_observations(tc):
    """Populate observe_memory/observe_io for generated golden tests."""
    mem = set(tc.observe_memory)
    io = set(tc.observe_io)

    if tc.instruction:
        _add_instruction_observations(tc, mem, io)
    else:
        _add_systematic_observations(tc, mem, io)

    tc.observe_memory = sorted(a & 0xFFFF for a in mem)
    tc.observe_io = sorted(i for i in io if 0 <= i < 12)
    return tc


def _add_instruction_observations(tc, mem, io):
    mnemonic, operands = _parse_instruction(tc.instruction)
    if not mnemonic:
        return

    regs = {i: 0 for i in range(16)}
    regs.update(tc.regs)

    if mnemonic in WORD_DEST_MNEMONICS:
        _observe_operand(mem, _operand(operands, 0), regs, words=1)
    elif mnemonic in BYTE_DEST_MNEMONICS:
        _observe_operand(mem, _operand(operands, 0), regs, bytes_=1)
    elif mnemonic in LONG_DEST_MNEMONICS:
        _observe_operand(mem, _operand(operands, 0), regs, words=2)
    elif mnemonic in LDM_MNEMONICS:
        count = _immediate_count(_operand(operands, 2), default=1)
        _observe_operand(mem, _operand(operands, 0), regs, words=count)
    elif mnemonic in BLOCK_WORD_WRITE_MNEMONICS:
        _observe_block(mem, operands, regs, byte_mode=False,
                       repeat=mnemonic.endswith("R"), decrement="D" in mnemonic)
    elif mnemonic in BLOCK_BYTE_WRITE_MNEMONICS:
        _observe_block(mem, operands, regs, byte_mode=True,
                       repeat=mnemonic.endswith("R"), decrement="D" in mnemonic)
    elif mnemonic in INPUT_BLOCK_MNEMONICS:
        _observe_block(mem, operands, regs, byte_mode=False,
                       repeat=mnemonic.endswith("R"), decrement="D" in mnemonic)
    elif mnemonic in INPUT_BLOCK_BYTE_MNEMONICS:
        _observe_block(mem, operands, regs, byte_mode=True,
                       repeat=mnemonic.endswith("R"), decrement="D" in mnemonic)
    elif mnemonic in OUTPUT_MNEMONICS:
        _observe_io_operand(io, _operand(operands, 0), regs,
                            special=mnemonic.startswith("S"))
    elif mnemonic in TRANSLATE_MNEMONICS:
        _observe_block(mem, operands, regs, byte_mode=True,
                       repeat=mnemonic.endswith("R"), decrement="D" in mnemonic)
    elif mnemonic in PUSH_MNEMONICS:
        _observe_push(mem, _operand(operands, 0), regs, long_mode=mnemonic == "PUSHL")
    elif mnemonic in POP_MNEMONICS:
        _observe_operand(mem, _operand(operands, 0), regs,
                         words=2 if mnemonic == "POPL" else 1)


def _add_systematic_observations(tc, mem, io):
    name = tc.name
    m = tc.mnemonic.upper()

    if "store" in tc.tags:
        if name.startswith("sys_ld_da_r_"):
            mem.add(0x0400)
        elif name.startswith("sys_ld_ir_r_"):
            mem.add(tc.regs.get(2, 0))
        elif name.startswith("sys_ldb_x_r_"):
            mem.add((tc.regs.get(2, 0) + 0x0400) & 0xFFFE)
        elif name.startswith("sys_ldb_ba_r_even"):
            mem.add((tc.regs.get(2, 0) + 0x0034) & 0xFFFE)
        elif name.startswith("sys_ldb_ba_r_odd"):
            mem.add((tc.regs.get(2, 0) + 0x0033) & 0xFFFE)
        elif name == "sys_ldm_store_3":
            base = tc.regs.get(2, 0)
            mem.update({base, base + 2, base + 4})

    if name.startswith(("sys_inc_ir_", "sys_dec_ir_")):
        mem.add(tc.regs.get(2, 0))

    if name.startswith("sys_push_r_"):
        sp = tc.regs.get(15, 0)
        mem.add((sp - 2) & 0xFFFF)
    elif name.startswith("sys_pushl_rr_"):
        sp = tc.regs.get(15, 0)
        mem.update({(sp - 4) & 0xFFFF, (sp - 2) & 0xFFFF})

    if m in BLOCK_WORD_WRITE_MNEMONICS:
        _observe_systematic_block(mem, tc, byte_mode=False,
                                  repeat=m.endswith("R"), decrement="D" in m)
    elif m in BLOCK_BYTE_WRITE_MNEMONICS:
        _observe_systematic_block(mem, tc, byte_mode=True,
                                  repeat=m.endswith("R"), decrement="D" in m)
    elif m in TRANSLATE_MNEMONICS:
        _observe_systematic_block(mem, tc, byte_mode=True,
                                  repeat=m.endswith("R"), decrement="D" in m)


def _parse_instruction(instruction):
    parts = instruction.strip().lower().split(None, 1)
    if not parts:
        return "", []
    operands = []
    if len(parts) > 1:
        operands = [p.strip() for p in parts[1].split(",")]
    return parts[0].upper(), operands


def _operand(operands, idx):
    return operands[idx] if idx < len(operands) else ""


def _observe_operand(mem, operand, regs, words=0, bytes_=0):
    addr = _effective_addr(operand, regs)
    if addr is None:
        return
    if bytes_:
        mem.add(addr & 0xFFFE)
        return
    for i in range(words):
        mem.add((addr + i * 2) & 0xFFFF)


def _observe_io_operand(io, operand, regs, special):
    addr = _effective_addr(operand, regs)
    if addr is None:
        return
    if (addr & 0xFFF0) != 0x0100 or (addr & 0x000E) > 0x000A:
        return
    idx = ((addr >> 1) & 0x07) + (6 if special else 0)
    io.add(idx)


def _observe_block(mem, operands, regs, byte_mode, repeat, decrement):
    dest = _effective_addr(_operand(operands, 0), regs)
    if dest is None:
        return
    count = regs.get(_reg_num(_operand(operands, 2)), 1) if repeat else 1
    _observe_range(mem, dest, count, byte_mode=byte_mode, decrement=decrement)


def _observe_systematic_block(mem, tc, byte_mode, repeat, decrement):
    dest = tc.regs.get(3, 0)
    count = tc.regs.get(2, 1) if repeat else 1
    _observe_range(mem, dest, count, byte_mode=byte_mode, decrement=decrement)


def _observe_range(mem, dest, count, byte_mode, decrement):
    step = -1 if byte_mode and decrement else -2 if decrement else 1 if byte_mode else 2
    count = max(1, min(count, 16))
    for i in range(count):
        addr = (dest + i * step) & 0xFFFF
        mem.add(addr & 0xFFFE)


def _observe_push(mem, operand, regs, long_mode):
    sp = _effective_addr(operand, regs)
    if sp is None:
        return
    if long_mode:
        mem.update({(sp - 4) & 0xFFFF, (sp - 2) & 0xFFFF})
    else:
        mem.add((sp - 2) & 0xFFFF)


def _effective_addr(operand, regs):
    operand = operand.strip().lower()
    if not operand:
        return None
    if operand.startswith("@"):
        return regs.get(_reg_num(operand[1:]), 0)

    m = re.fullmatch(r"#?0x([0-9a-f]+)", operand)
    if m:
        return int(m.group(1), 16)

    m = re.fullmatch(r"0x([0-9a-f]+)\(r(\d+)\)", operand)
    if m:
        return (int(m.group(1), 16) + regs.get(int(m.group(2)), 0)) & 0xFFFF

    m = re.fullmatch(r"(?:rr|r)(\d+)\(#0x([0-9a-f]+)\)", operand)
    if m:
        return (regs.get(int(m.group(1)), 0) + int(m.group(2), 16)) & 0xFFFF

    m = re.fullmatch(r"(?:rr|r)(\d+)\(#([0-9]+)\)", operand)
    if m:
        return (regs.get(int(m.group(1)), 0) + int(m.group(2), 10)) & 0xFFFF

    m = re.fullmatch(r"(?:rr|r)(\d+)\(r(\d+)\)", operand)
    if m:
        return (regs.get(int(m.group(1)), 0) + regs.get(int(m.group(2)), 0)) & 0xFFFF

    return None


def _reg_num(operand):
    m = re.search(r"r(?:h|l)?(\d+)|rr(\d+)|rq(\d+)", operand.lower())
    if not m:
        return None
    for group in m.groups():
        if group is not None:
            return int(group)
    return None


def _immediate_count(operand, default):
    m = re.search(r"#(?:0x)?([0-9a-f]+)", operand.lower())
    if not m:
        return default
    return int(m.group(1), 16 if "0x" in m.group(0) else 10)
