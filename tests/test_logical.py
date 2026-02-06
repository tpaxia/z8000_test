"""Logical instruction tests: AND, OR, XOR, COM, CLR."""

from .defs import TestCase
from .flags import FCW_SYS

TESTS = [
    # =========================================================================
    # AND Rd, Rs (word)
    # =========================================================================
    TestCase(
        name="and_r_r_basic",
        mnemonic="AND",
        description="AND R0, R1: 0xFF00 & 0x0F0F = 0x0F00",
        tags=["logical", "word", "R_mode"],
        code=[0x8710],  # AND R0, R1
        regs={0: 0xFF00, 1: 0x0F0F},
        expected_regs={0: 0x0F00, 1: 0x0F0F},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="and_r_r_zero",
        mnemonic="AND",
        description="AND R0, R1: 0xFF00 & 0x00FF = 0x0000 (zero)",
        tags=["logical", "word", "R_mode", "flags"],
        code=[0x8710],
        regs={0: 0xFF00, 1: 0x00FF},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="and_r_r_sign",
        mnemonic="AND",
        description="AND R0, R1: 0xF0F0 & 0xFF00 = 0xF000 (sign)",
        tags=["logical", "word", "R_mode", "flags"],
        code=[0x8710],
        regs={0: 0xF0F0, 1: 0xFF00},
        expected_regs={0: 0xF000},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z", "V"],
    ),
    TestCase(
        name="and_r_imm",
        mnemonic="AND",
        description="AND R0, #0x00FF: 0x1234 & 0x00FF = 0x0034",
        tags=["logical", "word", "IM_mode"],
        code=[0x0700, 0x00FF],  # AND R0, #0x00FF
        regs={0: 0x1234},
        expected_regs={0: 0x0034},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # OR Rd, Rs (word)
    # =========================================================================
    TestCase(
        name="or_r_r_basic",
        mnemonic="OR",
        description="OR R0, R1: 0xFF00 | 0x00FF = 0xFFFF",
        tags=["logical", "word", "R_mode"],
        code=[0x8510],
        regs={0: 0xFF00, 1: 0x00FF},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z", "V"],
    ),
    TestCase(
        name="or_r_r_zero",
        mnemonic="OR",
        description="OR R0, R1: 0x0000 | 0x0000 = 0x0000 (zero)",
        tags=["logical", "word", "R_mode", "flags"],
        code=[0x8510],
        regs={0: 0x0000, 1: 0x0000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="or_r_imm",
        mnemonic="OR",
        description="OR R0, #0xFF00: 0x00FF | 0xFF00 = 0xFFFF",
        tags=["logical", "word", "IM_mode"],
        code=[0x0500, 0xFF00],  # OR R0, #0xFF00
        regs={0: 0x00FF},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z", "V"],
    ),

    # =========================================================================
    # XOR Rd, Rs (word)
    # =========================================================================
    TestCase(
        name="xor_r_r_basic",
        mnemonic="XOR",
        description="XOR R0, R1: 0xAAAA ^ 0x5555 = 0xFFFF",
        tags=["logical", "word", "R_mode"],
        code=[0x8910],
        regs={0: 0xAAAA, 1: 0x5555},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z", "V"],
    ),
    TestCase(
        name="xor_r_r_zero",
        mnemonic="XOR",
        description="XOR R0, R1: 0x1234 ^ 0x1234 = 0x0000 (zero)",
        tags=["logical", "word", "R_mode", "flags"],
        code=[0x8910],
        regs={0: 0x1234, 1: 0x1234},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="xor_r_imm",
        mnemonic="XOR",
        description="XOR R0, #0xFFFF: 0xAAAA ^ 0xFFFF = 0x5555",
        tags=["logical", "word", "IM_mode"],
        code=[0x0900, 0xFFFF],  # XOR R0, #0xFFFF
        regs={0: 0xAAAA},
        expected_regs={0: 0x5555},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # COM Rd (word, one's complement)
    # =========================================================================
    TestCase(
        name="com_r_basic",
        mnemonic="COM",
        description="COM R0: ~0x00FF = 0xFF00",
        tags=["logical", "word", "R_mode"],
        code=[0x8D00],  # COM R0: 10001101_0000_0000
        regs={0: 0x00FF},
        expected_regs={0: 0xFF00},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="com_r_zero",
        mnemonic="COM",
        description="COM R0: ~0xFFFF = 0x0000",
        tags=["logical", "word", "R_mode", "flags"],
        code=[0x8D00],
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S"],
    ),

    # =========================================================================
    # CLR Rd (word)
    # =========================================================================
    TestCase(
        name="clr_r_basic",
        mnemonic="CLR",
        description="CLR R0: R0 = 0x0000",
        tags=["logical", "word", "R_mode"],
        code=[0x8D08],  # CLR R0: 10001101_0000_1000
        regs={0: 0xDEAD},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="clr_r_other_reg",
        mnemonic="CLR",
        description="CLR R5: R5 = 0x0000",
        tags=["logical", "word", "R_mode"],
        code=[0x8D58],  # CLR R5: 10001101_0101_1000
        regs={5: 0xBEEF},
        expected_regs={5: 0x0000},
    ),
]
