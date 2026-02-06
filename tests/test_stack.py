"""Stack operation tests: PUSH, POP."""

from .defs import TestCase
from .flags import FCW_SYS
from .helpers import STACK_BASE

# PUSH @Rd, Rs: 10010011_Rdnz_Rsss (Rd=stack ptr, Rs=source)
# POP Rd, @Rs:  10010111_Rsnz_Rddd (Rs=stack ptr, Rd=dest)

TESTS = [
    # =========================================================================
    # PUSH @Rd, Rs (word)
    # =========================================================================
    TestCase(
        name="push_basic",
        mnemonic="PUSH",
        description="PUSH @R15, R0: push R0 onto stack",
        tags=["stack", "word", "R_mode"],
        code=[0x93F0],  # PUSH @R15, R0
        regs={0: 0x1234, 15: STACK_BASE},
        expected_regs={0: 0x1234, 15: STACK_BASE - 2},
        expected_memory={STACK_BASE - 2: 0x1234},
    ),
    TestCase(
        name="push_multiple",
        mnemonic="PUSH",
        description="PUSH @R15, R0 then PUSH @R15, R1",
        tags=["stack", "word", "R_mode"],
        code=[
            0x93F0,  # PUSH @R15, R0
            0x93F1,  # PUSH @R15, R1
        ],
        regs={0: 0x1111, 1: 0x2222, 15: STACK_BASE},
        expected_regs={0: 0x1111, 1: 0x2222, 15: STACK_BASE - 4},
        expected_memory={
            STACK_BASE - 2: 0x1111,
            STACK_BASE - 4: 0x2222,
        },
    ),

    # =========================================================================
    # POP Rd, @Rs (word)
    # =========================================================================
    TestCase(
        name="pop_basic",
        mnemonic="POP",
        description="POP R0, @R15: pop from stack into R0",
        tags=["stack", "word", "R_mode"],
        code=[0x97F0],  # POP R0, @R15
        regs={0: 0x0000, 15: STACK_BASE - 2},
        memory={STACK_BASE - 2: 0xABCD},
        expected_regs={0: 0xABCD, 15: STACK_BASE},
    ),

    # =========================================================================
    # PUSH + POP round-trip
    # =========================================================================
    TestCase(
        name="push_pop_roundtrip",
        mnemonic="PUSH",
        description="PUSH R0, then POP into R1: round-trip test",
        tags=["stack", "word", "R_mode"],
        code=[
            0x93F0,  # PUSH @R15, R0
            0x97F1,  # POP R1, @R15
        ],
        regs={0: 0xDEAD, 1: 0x0000, 15: STACK_BASE},
        expected_regs={0: 0xDEAD, 1: 0xDEAD, 15: STACK_BASE},
    ),
]
