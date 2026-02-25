"""Segmented mode test generator for Z8001.

Generates TestCase objects for Z8001 segmented addressing tests.
Each test is assembled with z8k-coff-as -z8001 to get correct segmented
DA encodings (the assembler handles short-form vs long-form automatically).

Requires z8k-coff-as, z8k-coff-ld, z8k-coff-objcopy toolchain.

**** IMPORTANT: NEVER hand-code Z8001 segmented values. ****
**** This includes opcodes, DA words, AND register pair values for ****
**** segmented pointers (e.g. @RRn). The encoding is NOT obvious: ****
****   segment 1, offset 0x200 in a register pair = R_even=0x8100, ****
****   R_odd=0x0200 (bit 15=1 for long-form, segment in bits 14:8). ****
**** ALWAYS use the assembler (LDA instruction) to generate segmented ****
**** pointer values. See CLAUDE.md. ****

Usage:
    from tests.gen_segmented import generate_segmented_tests
    tests = generate_segmented_tests()
"""

import os
import subprocess
import tempfile

from .defs import TestCase
from .helpers import OPERAND_BASE, STACK_BASE

# Segmented FCW: System + Segmented
FCW_SEG = 0xC000

# Segment 0 short-form data address (offset < 256, in gap of bootstrap area)
SEG0_SHORT_ADDR = 0x00B4

# Segment 0 long-form data address (offset >= 256)
SEG0_LONG_ADDR = OPERAND_BASE  # 0x0400

# Segment 1 data base offset and corresponding Z80/BRAM address
SEG1_DATA_OFFSET = 0x0200
SEG1_Z80_ADDR = 0x1200  # Z80 flat address for segment 1, offset 0x0200

# Linker script template for segmented tests.
# Sections: .text at seg0:0x200, .s0short at seg0:SEG0_SHORT_ADDR,
# .s0long at seg0:SEG0_LONG_ADDR, .s1data at seg1:SEG1_DATA_OFFSET
LINKER_SCRIPT = f"""\
OUTPUT_FORMAT("coff-z8k")
OUTPUT_ARCH("z8001")
MEMORY {{
    SEG0 : ORIGIN = 0x00000, LENGTH = 4K
    SEG1 : ORIGIN = 0x10000, LENGTH = 4K
}}
SECTIONS {{
    .text 0x00200 : {{ *(.text) }} > SEG0
    .s0short 0x{SEG0_SHORT_ADDR:05X} : {{ *(.s0short) }} > SEG0
    .s0long 0x{SEG0_LONG_ADDR:05X} : {{ *(.s0long) }} > SEG0
    .s0stk 0x{STACK_BASE:05X} : {{ *(.s0stk) }} > SEG0
    .s1data 0x1{SEG1_DATA_OFFSET:04X} : {{ *(.s1data) }} > SEG1
}}
"""


def _assemble(asm_source):
    """Assemble Z8001 segmented code and return list of 16-bit code words.

    Uses the linker script to place sections at correct segmented addresses.
    Only the .text section binary is extracted (data sections are preloaded
    by the test harness).

    Returns list of 16-bit words.
    Raises RuntimeError on assembly/link failure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write assembly source
        src_path = os.path.join(tmpdir, "test.s")
        with open(src_path, "w") as f:
            f.write(asm_source)

        # Write linker script
        ld_path = os.path.join(tmpdir, "test.ld")
        with open(ld_path, "w") as f:
            f.write(LINKER_SCRIPT)

        # Assemble
        obj_path = os.path.join(tmpdir, "test.o")
        result = subprocess.run(
            ["z8k-coff-as", "-z8001", src_path, "-o", obj_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Assembly failed:\n{result.stderr}")

        # Link
        elf_path = os.path.join(tmpdir, "test.elf")
        result = subprocess.run(
            ["z8k-coff-ld", "-mz8001", "-T", ld_path, obj_path, "-o", elf_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Link failed:\n{result.stderr}")

        # Extract .text section binary
        bin_path = os.path.join(tmpdir, "test.bin")
        result = subprocess.run(
            ["z8k-coff-objcopy", "-O", "binary", "--only-section=.text",
             elf_path, bin_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"objcopy failed:\n{result.stderr}")

        # Read binary and convert to word list
        with open(bin_path, "rb") as f:
            data = f.read()

        words = []
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                words.append((data[i] << 8) | data[i + 1])
            else:
                words.append(data[i] << 8)

        return words


def _tc(name, mnemonic, desc, tags, code, regs=None, memory=None):
    """Create a segmented test case."""
    return TestCase(
        name=name,
        mnemonic=mnemonic,
        description=desc,
        tags=["systematic", "segmented"] + tags,
        target="z8001-seg",
        code=code,
        regs=regs or {},
        fcw=FCW_SEG,
        memory=memory or {},
    )


# Assembly source templates. All start with "segm\n" and define _start in .text.
# Data sections (.s0short, .s0long, .s1data) hold placeholder labels for the
# linker to resolve cross-section references.

def _asm_seg0_short_ld():
    """LD R0 from segment 0, short-form DA (offset < 256)."""
    return """\
        segm
        .section .s0short
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, seg0_val
"""


def _asm_seg0_short_st():
    """ST R0 to segment 0, short-form DA."""
    return """\
        segm
        .section .s0short
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      seg0_val, r0
"""


def _asm_seg0_long_ld():
    """LD R0 from segment 0, long-form DA (offset >= 256)."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, seg0_val
"""


def _asm_seg0_long_st():
    """ST R0 to segment 0, long-form DA."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      seg0_val, r0
"""


def _asm_seg1_ld():
    """LD R0 from segment 1 (cross-segment, always long-form)."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, seg1_val
"""


def _asm_seg1_st():
    """ST R0 to segment 1."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      seg1_val, r0
"""


def _asm_seg1_ldb():
    """LDB RH0 from segment 1 (byte load cross-segment)."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ldb     rh0, seg1_val
"""


def _asm_seg1_stb():
    """STB RH0 to segment 1 (byte store cross-segment)."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ldb     seg1_val, rh0
"""


def _asm_seg0_ir_ld():
    """LD R0, @RR2 (indirect via register pair, segment 0).
    Uses LDA to set up RR2 — never hand-code segmented pointer registers."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        lda     rr2, seg0_val
        ld      r0, @rr2
"""


def _asm_seg1_ir_ld():
    """LD R0, @RR2 (indirect via register pair, segment 1).
    Uses LDA to set up RR2 — never hand-code segmented pointer registers."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        lda     rr2, seg1_val
        ld      r0, @rr2
"""


def _asm_seg1_ir_st():
    """ST R0, @RR2 (indirect store cross-segment).
    Uses LDA to set up RR2 — never hand-code segmented pointer registers."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        lda     rr2, seg1_val
        ld      @rr2, r0
"""


def _asm_seg0_x_ld():
    """LD R0, addr(R5) segment 0 (indexed addressing)."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, seg0_val(r5)
"""


def _asm_seg1_x_ld():
    """LD R0, addr(R5) segment 1 (indexed addressing, cross-segment)."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, seg1_val(r5)
"""


def _asm_seg_isolation():
    """Write same offset in seg 0 and seg 1, verify both."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .section .s1data
seg1_val:
        .word   0x0000
        .text
        .global _start
_start:
        ld      r0, #0xAAAA
        ld      seg0_val, r0
        ld      r0, #0x5555
        ld      seg1_val, r0
        ld      r1, seg0_val
        ld      r2, seg1_val
"""


def _asm_seg0_jp():
    """JP label (intra-segment jump within segment 0)."""
    return """\
        segm
        .text
        .global _start
_start:
        ld      r0, #0x1234
        jp      target
        ld      r0, #0xDEAD
target:
        ld      r1, #0x5678
"""


def _asm_seg0_call_ret():
    """Segmented CALL pushes seg:offset, RET restores.
    Uses LDA to set up RR14 stack pointer — never hand-code segmented pointers."""
    return """\
        segm
        .section .s0stk
stack_base:
        .space  2
        .text
        .global _start
_start:
        lda     rr14, stack_base
        ld      r0, #0x0000
        call    subroutine
        ld      r0, #0xAAAA
        jp      done
subroutine:
        ld      r0, #0x1234
        ret
done:
"""


def _asm_seg0_push_pop():
    """Segmented PUSH/POP @RR14 stack operations.
    Uses LDA to set up RR14 stack pointer — never hand-code segmented pointers."""
    return """\
        segm
        .section .s0stk
stack_base:
        .space  2
        .text
        .global _start
_start:
        lda     rr14, stack_base
        ld      r0, #0xBEEF
        push    @rr14, r0
        ld      r0, #0x0000
        pop     r0, @rr14
"""


def _asm_seg1_ldl():
    """LDL RR0 from segment 1 (32-bit load cross-segment)."""
    return """\
        segm
        .section .s1data
seg1_val:
        .word   0x0000
        .word   0x0000
        .text
        .global _start
_start:
        ldl     rr0, seg1_val
"""


def _asm_seg0_lda():
    """LDA RR2, seg0_data (load address, extracts seg:offset pair)."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        lda     rr2, seg0_val
"""


def _asm_seg0_add_da():
    """ADD R0, seg0_da (arithmetic with DA addressing in segment 0)."""
    return """\
        segm
        .section .s0long
seg0_val:
        .word   0x0000
        .text
        .global _start
_start:
        add     r0, seg0_val
"""


def generate_segmented_tests():
    """Generate segmented mode tests for Z8001.

    Returns a list of TestCase objects. Each test uses assembler-verified
    instruction encodings for segmented DA mode.

    Returns empty list if z8k toolchain is not available.
    """
    # Check toolchain availability
    try:
        result = subprocess.run(
            ["z8k-coff-as", "--version"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return []
    except FileNotFoundError:
        return []

    tests = []

    # ---- Test 1: LD R0 from segment 0, short-form DA ----
    code = _assemble(_asm_seg0_short_ld())
    tests.append(_tc(
        name='seg_ld_r_seg0_short',
        mnemonic='LD',
        desc='LD R0, seg0:0xB4 (short-form DA)',
        tags=['segmented', 'seg0', 'short_da'],
        code=code,
        regs={0: 0x0000},
        memory={SEG0_SHORT_ADDR: 0xBEEF},
    ))

    # ---- Test 2: ST R0 to segment 0, short-form DA ----
    code = _assemble(_asm_seg0_short_st())
    tests.append(_tc(
        name='seg_st_r_seg0_short',
        mnemonic='ST',
        desc='ST R0, seg0:0xB4 (short-form DA)',
        tags=['segmented', 'seg0', 'short_da'],
        code=code,
        regs={0: 0xCAFE},
        memory={},
    ))
    tests[-1].expected_memory = {SEG0_SHORT_ADDR: 0xCAFE}

    # ---- Test 3: LD R0 from segment 0, long-form DA ----
    code = _assemble(_asm_seg0_long_ld())
    tests.append(_tc(
        name='seg_ld_r_seg0_long',
        mnemonic='LD',
        desc='LD R0, seg0:0x400 (long-form DA)',
        tags=['segmented', 'seg0', 'long_da'],
        code=code,
        regs={0: 0x0000},
        memory={SEG0_LONG_ADDR: 0xDEAD},
    ))

    # ---- Test 4: ST R0 to segment 0, long-form DA ----
    code = _assemble(_asm_seg0_long_st())
    tests.append(_tc(
        name='seg_st_r_seg0_long',
        mnemonic='ST',
        desc='ST R0, seg0:0x400 (long-form DA)',
        tags=['segmented', 'seg0', 'long_da'],
        code=code,
        regs={0: 0xFACE},
        memory={},
    ))
    tests[-1].expected_memory = {SEG0_LONG_ADDR: 0xFACE}

    # ---- Test 5: LD R0 from segment 1 (cross-segment) ----
    code = _assemble(_asm_seg1_ld())
    tests.append(_tc(
        name='seg_ld_r_seg1',
        mnemonic='LD',
        desc='LD R0, seg1:0x200 (cross-segment load)',
        tags=['segmented', 'seg1', 'cross_segment'],
        code=code,
        regs={0: 0x0000},
        memory={SEG1_Z80_ADDR: 0x1234},
    ))

    # ---- Test 6: ST R0 to segment 1 (cross-segment) ----
    code = _assemble(_asm_seg1_st())
    tests.append(_tc(
        name='seg_st_r_seg1',
        mnemonic='ST',
        desc='ST R0, seg1:0x200 (cross-segment store)',
        tags=['segmented', 'seg1', 'cross_segment'],
        code=code,
        regs={0: 0xABCD},
        memory={},
    ))
    tests[-1].expected_memory = {SEG1_Z80_ADDR: 0xABCD}

    # ---- Test 7: LDB RH0 from segment 1 (byte load) ----
    code = _assemble(_asm_seg1_ldb())
    tests.append(_tc(
        name='seg_ldb_rh0_seg1',
        mnemonic='LDB',
        desc='LDB RH0, seg1:0x200 (byte load cross-segment)',
        tags=['segmented', 'seg1', 'byte', 'cross_segment'],
        code=code,
        regs={0: 0x0000},
        memory={SEG1_Z80_ADDR: 0xAB00},
    ))

    # ---- Test 8: STB RH0 to segment 1 (byte store) ----
    code = _assemble(_asm_seg1_stb())
    tests.append(_tc(
        name='seg_stb_rh0_seg1',
        mnemonic='STB',
        desc='STB RH0, seg1:0x200 (byte store cross-segment)',
        tags=['segmented', 'seg1', 'byte', 'cross_segment'],
        code=code,
        regs={0: 0xCD00},
        memory={SEG1_Z80_ADDR: 0x0000},
    ))
    tests[-1].expected_memory = {SEG1_Z80_ADDR: 0xCD00}

    # ---- Test 9: LD R0, @RR2 (indirect, segment 0) ----
    # RR2 is set up by LDA in the assembly — NOT hand-coded in regs
    code = _assemble(_asm_seg0_ir_ld())
    tests.append(_tc(
        name='seg_ld_r_ir_seg0',
        mnemonic='LD',
        desc='LD R0, @RR2 (indirect, seg 0 offset 0x400)',
        tags=['segmented', 'seg0', 'indirect'],
        code=code,
        regs={0: 0x0000},
        memory={SEG0_LONG_ADDR: 0x9876},
    ))

    # ---- Test 10: LD R0, @RR2 (indirect, segment 1) ----
    # RR2 is set up by LDA in the assembly — NOT hand-coded in regs
    code = _assemble(_asm_seg1_ir_ld())
    tests.append(_tc(
        name='seg_ld_r_ir_seg1',
        mnemonic='LD',
        desc='LD R0, @RR2 (indirect, seg 1 offset 0x200)',
        tags=['segmented', 'seg1', 'indirect', 'cross_segment'],
        code=code,
        regs={0: 0x0000},
        memory={SEG1_Z80_ADDR: 0x5432},
    ))

    # ---- Test 11: ST R0, @RR2 (indirect store, segment 1) ----
    # RR2 is set up by LDA in the assembly — NOT hand-coded in regs
    code = _assemble(_asm_seg1_ir_st())
    tests.append(_tc(
        name='seg_st_r_ir_seg1',
        mnemonic='ST',
        desc='ST R0, @RR2 (indirect store, seg 1 offset 0x200)',
        tags=['segmented', 'seg1', 'indirect', 'cross_segment'],
        code=code,
        regs={0: 0xFEDC},
        memory={},
    ))
    tests[-1].expected_memory = {SEG1_Z80_ADDR: 0xFEDC}

    # ---- Test 12: LD R0, addr(R5) segment 0 (indexed) ----
    code = _assemble(_asm_seg0_x_ld())
    tests.append(_tc(
        name='seg_ld_r_x_seg0',
        mnemonic='LD',
        desc='LD R0, seg0:0x400(R5) (indexed, R5=4)',
        tags=['segmented', 'seg0', 'indexed'],
        code=code,
        regs={0: 0x0000, 5: 0x0004},
        memory={SEG0_LONG_ADDR + 4: 0x4321},
    ))

    # ---- Test 13: LD R0, addr(R5) segment 1 (indexed, cross-segment) ----
    code = _assemble(_asm_seg1_x_ld())
    tests.append(_tc(
        name='seg_ld_r_x_seg1',
        mnemonic='LD',
        desc='LD R0, seg1:0x200(R5) (indexed, R5=6)',
        tags=['segmented', 'seg1', 'indexed', 'cross_segment'],
        code=code,
        regs={0: 0x0000, 5: 0x0006},
        memory={SEG1_Z80_ADDR + 6: 0x8765},
    ))

    # ---- Test 14: Segment isolation ----
    code = _assemble(_asm_seg_isolation())
    tests.append(_tc(
        name='seg_isolation',
        mnemonic='ST',
        desc='Write seg0:0x400=0xAAAA, seg1:0x200=0x5555, verify both',
        tags=['segmented', 'seg0', 'seg1', 'cross_segment', 'isolation'],
        code=code,
        regs={0: 0x0000, 1: 0x0000, 2: 0x0000},
        memory={SEG0_LONG_ADDR: 0x0000, SEG1_Z80_ADDR: 0x0000},
    ))
    tests[-1].expected_memory = {
        SEG0_LONG_ADDR: 0xAAAA,
        SEG1_Z80_ADDR: 0x5555,
    }

    # ---- Test 15: JP label (intra-segment) ----
    code = _assemble(_asm_seg0_jp())
    tests.append(_tc(
        name='seg_jp_seg0',
        mnemonic='JP',
        desc='JP target (intra-segment jump, skip one instruction)',
        tags=['segmented', 'seg0', 'branch'],
        code=code,
        regs={0: 0x0000, 1: 0x0000},
    ))

    # ---- Test 16: CALL/RET (segment 0) ----
    # RR14 stack pointer set up by LDA in the assembly — NOT hand-coded in regs
    code = _assemble(_asm_seg0_call_ret())
    tests.append(_tc(
        name='seg_call_ret_seg0',
        mnemonic='CALL',
        desc='CALL subroutine / RET (segmented stack)',
        tags=['segmented', 'seg0', 'call', 'ret'],
        code=code,
        regs={0: 0x0000},
    ))

    # ---- Test 17: PUSH/POP @RR14 (segmented stack) ----
    # RR14 stack pointer set up by LDA in the assembly — NOT hand-coded in regs
    code = _assemble(_asm_seg0_push_pop())
    tests.append(_tc(
        name='seg_push_pop_seg0',
        mnemonic='PUSH',
        desc='PUSH @RR14, R0 / POP R0, @RR14 (segmented stack)',
        tags=['segmented', 'seg0', 'push', 'pop', 'stack'],
        code=code,
        regs={0: 0x0000},
    ))

    # ---- Test 18: LDL RR0 from segment 1 (32-bit load) ----
    code = _assemble(_asm_seg1_ldl())
    tests.append(_tc(
        name='seg_ldl_rr0_seg1',
        mnemonic='LDL',
        desc='LDL RR0, seg1:0x200 (32-bit load cross-segment)',
        tags=['segmented', 'seg1', 'long_word', 'cross_segment'],
        code=code,
        regs={0: 0x0000, 1: 0x0000},
        memory={SEG1_Z80_ADDR: 0x1234, SEG1_Z80_ADDR + 2: 0x5678},
    ))

    # ---- Test 19: LDA RR2, seg0_data (load address) ----
    code = _assemble(_asm_seg0_lda())
    tests.append(_tc(
        name='seg_lda_rr2_seg0',
        mnemonic='LDA',
        desc='LDA RR2, seg0:0x400 (load segmented address)',
        tags=['segmented', 'seg0', 'load_address'],
        code=code,
        regs={2: 0x0000, 3: 0x0000},
    ))

    # ---- Test 20: ADD R0, seg0_da (arithmetic with DA mode) ----
    code = _assemble(_asm_seg0_add_da())
    tests.append(_tc(
        name='seg_add_r_da_seg0',
        mnemonic='ADD',
        desc='ADD R0, seg0:0x400 (arithmetic with DA addressing)',
        tags=['segmented', 'seg0', 'arithmetic', 'da_mode'],
        code=code,
        regs={0: 0x1000},
        memory={SEG0_LONG_ADDR: 0x0234},
    ))

    return tests
