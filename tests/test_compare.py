"""Compare and test instruction tests: CP, CPB, TEST, TESTB."""

from .defs import TestCase
from .flags import FCW_SYS

TESTS = [
    # =========================================================================
    # CP Rd, Rs (word, compare - sets flags, no register change)
    # =========================================================================
    TestCase(
        name="cp_r_r_equal",
        mnemonic="CP",
        instruction="CP R0, R1",
        description="CP R0, R1: 0x1234 - 0x1234 (equal, Z=1)",
        tags=["compare", "word", "R_mode"],
        code=[0x8B10],  # CP R0, R1
        regs={0: 0x1234, 1: 0x1234},
        expected_regs={0: 0x1234, 1: 0x1234},  # Unchanged
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="cp_r_r_greater",
        mnemonic="CP",
        instruction="CP R0, R1",
        description="CP R0, R1: 0x5678 - 0x1234 (R0 > R1)",
        tags=["compare", "word", "R_mode"],
        code=[0x8B10],
        regs={0: 0x5678, 1: 0x1234},
        expected_regs={0: 0x5678, 1: 0x1234},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="cp_r_r_less",
        mnemonic="CP",
        instruction="CP R0, R1",
        description="CP R0, R1: 0x1234 - 0x5678 (R0 < R1, borrow)",
        tags=["compare", "word", "R_mode", "flags"],
        code=[0x8B10],
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x1234, 1: 0x5678},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),
    TestCase(
        name="cp_r_imm_equal",
        mnemonic="CP",
        instruction="CP R0, #0x1234",
        description="CP R0, #0x1234: equal",
        tags=["compare", "word", "IM_mode"],
        code=[0x0B00, 0x1234],  # CP R0, #0x1234
        regs={0: 0x1234},
        expected_regs={0: 0x1234},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),

    # =========================================================================
    # TEST Rd (word, test - AND with self to set flags)
    # =========================================================================
    TestCase(
        name="test_r_nonzero",
        mnemonic="TEST",
        instruction="TEST R0",
        description="TEST R0: 0x1234 (nonzero, positive)",
        tags=["compare", "word", "R_mode"],
        code=[0x8D04],  # TEST R0: 10001101_0000_0100
        regs={0: 0x1234},
        expected_regs={0: 0x1234},  # Unchanged
        expected_fcw_clear=["Z", "S"],
    ),
    TestCase(
        name="test_r_zero",
        mnemonic="TEST",
        instruction="TEST R0",
        description="TEST R0: 0x0000 (zero flag)",
        tags=["compare", "word", "R_mode", "flags"],
        code=[0x8D04],
        regs={0: 0x0000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="test_r_negative",
        mnemonic="TEST",
        instruction="TEST R0",
        description="TEST R0: 0x8000 (sign flag)",
        tags=["compare", "word", "R_mode", "flags"],
        code=[0x8D04],
        regs={0: 0x8000},
        expected_regs={0: 0x8000},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z"],
    ),
]
