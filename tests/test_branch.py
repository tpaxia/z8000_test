"""Branch and jump instruction tests: JP, JR, CALL, CALR, RET, DJNZ."""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import CODE_BASE, STACK_BASE

# Condition codes
CC_F    = 0   # False (never)
CC_LT   = 1   # Less than (signed)
CC_LE   = 2   # Less or equal (signed)
CC_ULE  = 3   # Unsigned less or equal
CC_V    = 4   # Overflow
CC_S    = 5   # Sign (minus)
CC_Z    = 6   # Zero (equal)
CC_C    = 7   # Carry (unsigned less than)
CC_T    = 8   # True (always)
CC_GE   = 9   # Greater or equal (signed)
CC_GT   = 10  # Greater than (signed)
CC_UGT  = 11  # Unsigned greater than
CC_NV   = 12  # No overflow
CC_NS   = 13  # No sign (plus)
CC_NZ   = 14  # Not zero (not equal)
CC_NC   = 15  # No carry (unsigned greater or equal)

TESTS = [
    # =========================================================================
    # JP cc, addr - conditional jump
    # Using register writes to distinguish taken vs not-taken paths
    # =========================================================================
    TestCase(
        name="jp_always",
        mnemonic="JP",
        description="JP T (always): unconditional jump",
        tags=["branch", "word", "DA_mode"],
        # Code layout at 0x0200:
        #   0x0200: JP T, 0x0208      (skip over fall-through marker)
        #   0x0204: LD R0, #0xBAD0    (fall-through - should NOT execute)
        #   0x0208: LD R0, #0x600D    (target - should execute)
        # Then JP dump_routine is appended by runner at 0x020C
        code=[
            0x5E08, 0x0208,  # JP T, 0x0208
            0x2100, 0xBAD0,  # LD R0, #0xBAD0 (fall-through)
            0x2100, 0x600D,  # LD R0, #0x600D (target)
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),
    TestCase(
        name="jp_never",
        mnemonic="JP",
        description="JP F (never): never jump, fall through",
        tags=["branch", "word", "DA_mode"],
        # 0x0200: JP F, 0x0208     (never taken)
        # 0x0204: LD R0, #0x600D   (fall-through, executes)
        # Runner appends JP dump at 0x0208 -> goes to dump
        code=[
            0x5E00, 0x0208,  # JP F, 0x0208 (cc=0 = never)
            0x2100, 0x600D,  # LD R0, #0x600D (fall-through, should execute)
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),
    TestCase(
        name="jp_z_taken",
        mnemonic="JP",
        description="JP Z: zero flag set, jump taken",
        tags=["branch", "word", "DA_mode", "flags"],
        fcw=fcw_with_flags(Z=1),
        code=[
            0x5E06, 0x0208,  # JP Z, 0x0208
            0x2100, 0xBAD0,  # LD R0, #0xBAD0 (fall-through)
            0x2100, 0x600D,  # LD R0, #0x600D (target)
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),
    TestCase(
        name="jp_z_not_taken",
        mnemonic="JP",
        description="JP Z: zero flag clear, not taken",
        tags=["branch", "word", "DA_mode", "flags"],
        fcw=FCW_SYS,  # Z=0
        # 0x0200: JP Z, 0x0208     (Z=0, not taken)
        # 0x0204: LD R0, #0x600D   (fall-through, executes)
        # Runner appends JP dump at 0x0208
        code=[
            0x5E06, 0x0208,  # JP Z, 0x0208 (not taken)
            0x2100, 0x600D,  # LD R0, #0x600D (fall-through)
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),
    TestCase(
        name="jp_c_taken",
        mnemonic="JP",
        description="JP C: carry flag set, jump taken",
        tags=["branch", "word", "DA_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[
            0x5E07, 0x0208,  # JP C, 0x0208
            0x2100, 0xBAD0,
            0x2100, 0x600D,
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),

    # =========================================================================
    # JR cc, disp - relative jump
    # Displacement is in words from PC+2 (after the instruction)
    # =========================================================================
    TestCase(
        name="jr_always",
        mnemonic="JR",
        description="JR T: relative jump forward by 2 words",
        tags=["branch", "word", "RA_mode"],
        # At 0x0200: JR T, +2 -> skip 2 words to 0x0206
        # At 0x0202: LD R0, #0xBAD0 (skipped)
        # At 0x0206: LD R0, #0x600D
        code=[
            0xE802,          # JR T, +2 (disp=2 words forward)
            0x2100, 0xBAD0,  # LD R0, #0xBAD0 (skipped)
            0x2100, 0x600D,  # LD R0, #0x600D (target)
        ],
        regs={0: 0x0000},
        expected_regs={0: 0x600D},
    ),

    # =========================================================================
    # DJNZ Rn, disp - decrement and jump if not zero
    # DJNZ Rn, disp: 1111dddd_nnnn_dddd (nnnn=Rn, dddd_dddddddd=displacement)
    # Wait, actually: 1111nnnn_dddd_dddd
    # =========================================================================
    TestCase(
        name="djnz_loop",
        mnemonic="DJNZ",
        description="DJNZ R1: loop 3 times, incrementing R0",
        tags=["branch", "word", "RA_mode"],
        # At 0x0200: INC R0, #1     (0xA900)
        # At 0x0202: DJNZ R1, 2     (jump back 2 words to 0x0200)
        # DJNZ Rn, disp: 1111nnnn_1ddddddd, n=1, disp=2
        # PC after DJNZ fetch = 0x0204, target = 0x0204 - 2*2 = 0x0200
        code=[
            0xA900,    # INC R0, #1
            0xF182,    # DJNZ R1, 2 (backward disp=2 words)
        ],
        regs={0: 0x0000, 1: 0x0003},
        expected_regs={0: 0x0003, 1: 0x0000},
    ),

    # =========================================================================
    # CALL addr / RET - subroutine call and return
    # CALL address: 01011111_0000_0000 + address = 0x5F00 + addr
    # RET cc: 10011110_0000_cccc
    # =========================================================================
    TestCase(
        name="call_ret_basic",
        mnemonic="CALL",
        description="CALL / RET: basic subroutine call and return",
        tags=["branch", "word", "DA_mode", "stack"],
        # Code layout at 0x0200:
        #   0x0200: LD R0, #0x0001       (before call)
        #   0x0204: CALL 0x0210          (call subroutine at 0x0210)
        #   0x0208: LD R0, #0x0003       (after return - should execute)
        #   0x020C: JP 0x00C0            (explicit jump to dump, skip subroutine)
        #   0x0210: LD R0, #0x0002       (subroutine body)
        #   0x0214: RET T               (return always)
        # Runner appends JP dump at 0x0216 (never reached)
        code=[
            0x2100, 0x0001,  # LD R0, #0x0001
            0x5F00, 0x0210,  # CALL 0x0210
            0x2100, 0x0003,  # LD R0, #0x0003 (after return)
            0x5E08, 0x00C0,  # JP 0x00C0 (explicit dump, skip subroutine)
            0x2100, 0x0002,  # LD R0, #0x0002 (subroutine body)
            0x9E08,          # RET T (always return)
        ],
        regs={0: 0x0000, 15: STACK_BASE},
        expected_regs={0: 0x0003, 15: STACK_BASE},  # SP restored after RET
    ),
]
