"""Bit manipulation tests: BIT, SET, RES, TSET."""

from .defs import TestCase
from .flags import FCW_SYS

TESTS = [
    # =========================================================================
    # BIT Rd, #b (test bit)
    # BIT Rd, b: 10100111_Rddd_bbbb (word, static bit)
    # =========================================================================
    TestCase(
        name="bit_r_set",
        mnemonic="BIT",
        instruction="BIT R0, #0",
        description="BIT R0, #0: bit 0 is set (Z=0)",
        tags=["bit", "word", "R_mode"],
        code=[0xA700],  # BIT R0, #0
        regs={0: 0x0001},
        expected_regs={0: 0x0001},  # Unchanged
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="bit_r_clear",
        mnemonic="BIT",
        instruction="BIT R0, #0",
        description="BIT R0, #0: bit 0 is clear (Z=1)",
        tags=["bit", "word", "R_mode", "flags"],
        code=[0xA700],  # BIT R0, #0
        regs={0: 0xFFFE},
        expected_regs={0: 0xFFFE},
        expected_fcw_set=["Z"],
    ),
    TestCase(
        name="bit_r_high",
        mnemonic="BIT",
        instruction="BIT R0, #15",
        description="BIT R0, #15: test bit 15",
        tags=["bit", "word", "R_mode"],
        code=[0xA70F],  # BIT R0, #15
        regs={0: 0x8000},
        expected_regs={0: 0x8000},
        expected_fcw_clear=["Z"],
    ),

    # =========================================================================
    # SET Rd, #b (set bit)
    # SET Rd, b: 10100101_Rddd_bbbb (word, static bit)
    # =========================================================================
    TestCase(
        name="set_r_basic",
        mnemonic="SET",
        instruction="SET R0, #0",
        description="SET R0, #0: set bit 0",
        tags=["bit", "word", "R_mode"],
        code=[0xA500],  # SET R0, #0
        regs={0: 0x0000},
        expected_regs={0: 0x0001},
    ),
    TestCase(
        name="set_r_already_set",
        mnemonic="SET",
        instruction="SET R0, #0",
        description="SET R0, #0: bit already set",
        tags=["bit", "word", "R_mode"],
        code=[0xA500],
        regs={0: 0xFFFF},
        expected_regs={0: 0xFFFF},
    ),
    TestCase(
        name="set_r_high_bit",
        mnemonic="SET",
        instruction="SET R0, #15",
        description="SET R0, #15: set bit 15",
        tags=["bit", "word", "R_mode"],
        code=[0xA50F],  # SET R0, #15
        regs={0: 0x0000},
        expected_regs={0: 0x8000},
    ),

    # =========================================================================
    # RES Rd, #b (reset/clear bit)
    # RES Rd, b: 10100011_Rddd_bbbb (word, static bit)
    # =========================================================================
    TestCase(
        name="res_r_basic",
        mnemonic="RES",
        instruction="RES R0, #0",
        description="RES R0, #0: clear bit 0",
        tags=["bit", "word", "R_mode"],
        code=[0xA300],  # RES R0, #0
        regs={0: 0xFFFF},
        expected_regs={0: 0xFFFE},
    ),
    TestCase(
        name="res_r_already_clear",
        mnemonic="RES",
        instruction="RES R0, #0",
        description="RES R0, #0: bit already clear",
        tags=["bit", "word", "R_mode"],
        code=[0xA300],
        regs={0: 0x0000},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="res_r_high_bit",
        mnemonic="RES",
        instruction="RES R0, #15",
        description="RES R0, #15: clear bit 15",
        tags=["bit", "word", "R_mode"],
        code=[0xA30F],  # RES R0, #15
        regs={0: 0xFFFF},
        expected_regs={0: 0x7FFF},
    ),
]
