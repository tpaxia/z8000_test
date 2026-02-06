"""Shift and rotate instruction tests: SLL, SRL, SLA, SRA, RL, RLC, RR, RRC."""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags

# Shift/rotate opcodes: 10110011_Rddd_ssss + count_word
# ssss = shift type: 0001=SLL, 0011=SRL, 1001=SLA, 1011=SRA
# For single shifts: 10110011_Rddd_ssss, #count_word (positive=left, negative=right)
# Actually the Z8000 shift encoding is:
# SLL Rd, #n:  10110011_Rddd_0001 + n (positive count)
# SRL Rd, #n:  10110011_Rddd_0001 + (-n & 0xFFFF) (negative count = right shift)
# SLA Rd, #n:  10110011_Rddd_0011 + n
# SRA Rd, #n:  10110011_Rddd_0011 + (-n & 0xFFFF)
# RL Rd, #n:   10110011_Rddd_0000 + n
# RLC Rd, #n:  10110011_Rddd_0010 + n
# RR Rd, #n:   10110011_Rddd_0000 + (-n & 0xFFFF)
# RRC Rd, #n:  10110011_Rddd_0010 + (-n & 0xFFFF)

TESTS = [
    # =========================================================================
    # SLL Rd, #n (shift left logical)
    # =========================================================================
    TestCase(
        name="sll_r_by1",
        mnemonic="SLL",
        description="SLL R0, #1: 0x0001 << 1 = 0x0002",
        tags=["shift", "word", "R_mode"],
        code=[0xB301, 0x0001],  # SLL R0, #1
        regs={0: 0x0001},
        expected_regs={0: 0x0002},
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="sll_r_carry",
        mnemonic="SLL",
        description="SLL R0, #1: 0x8000 << 1 = 0x0000 (carry out)",
        tags=["shift", "word", "R_mode", "flags"],
        code=[0xB301, 0x0001],
        regs={0: 0x8000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="sll_r_by4",
        mnemonic="SLL",
        description="SLL R0, #4: 0x0012 << 4 = 0x0120",
        tags=["shift", "word", "R_mode"],
        code=[0xB301, 0x0004],
        regs={0: 0x0012},
        expected_regs={0: 0x0120},
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # SRL Rd, #n (shift right logical)
    # =========================================================================
    TestCase(
        name="srl_r_by1",
        mnemonic="SRL",
        description="SRL R0, #1: 0x0002 >> 1 = 0x0001",
        tags=["shift", "word", "R_mode"],
        code=[0xB301, 0xFFFF],  # SRL R0, #1 (count = -1 = 0xFFFF)
        regs={0: 0x0002},
        expected_regs={0: 0x0001},
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="srl_r_carry",
        mnemonic="SRL",
        description="SRL R0, #1: 0x0001 >> 1 = 0x0000 (carry out)",
        tags=["shift", "word", "R_mode", "flags"],
        code=[0xB301, 0xFFFF],
        regs={0: 0x0001},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="srl_r_msb_clear",
        mnemonic="SRL",
        description="SRL R0, #1: 0x8000 >> 1 = 0x4000 (MSB cleared)",
        tags=["shift", "word", "R_mode"],
        code=[0xB301, 0xFFFF],
        regs={0: 0x8000},
        expected_regs={0: 0x4000},
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # SRA Rd, #n (shift right arithmetic - preserves sign)
    # =========================================================================
    TestCase(
        name="sra_r_positive",
        mnemonic="SRA",
        description="SRA R0, #1: 0x0004 >> 1 = 0x0002 (positive, sign preserved)",
        tags=["shift", "word", "R_mode"],
        code=[0xB303, 0xFFFF],  # SRA R0, #1 (arithmetic, count = -1)
        regs={0: 0x0004},
        expected_regs={0: 0x0002},
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="sra_r_negative",
        mnemonic="SRA",
        description="SRA R0, #1: 0x8002 >> 1 = 0xC001 (negative, sign preserved)",
        tags=["shift", "word", "R_mode"],
        code=[0xB303, 0xFFFF],
        regs={0: 0x8002},
        expected_regs={0: 0xC001},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z"],
    ),

    # =========================================================================
    # RL Rd, #n (rotate left)
    # =========================================================================
    TestCase(
        name="rl_r_by1",
        mnemonic="RL",
        description="RL R0, #1: rotate 0x8001 left by 1 = 0x0003",
        tags=["shift", "word", "R_mode"],
        code=[0xB300, 0x0001],  # RL R0, #1
        regs={0: 0x8001},
        expected_regs={0: 0x0003},
        expected_fcw_set=["C"],  # MSB rotated out sets carry
        expected_fcw_clear=["Z", "S"],
    ),

    # =========================================================================
    # RR Rd, #n (rotate right)
    # =========================================================================
    TestCase(
        name="rr_r_by1",
        mnemonic="RR",
        description="RR R0, #1: rotate 0x0001 right by 1 = 0x8000",
        tags=["shift", "word", "R_mode"],
        code=[0xB300, 0xFFFF],  # RR R0, #1 (count = -1)
        regs={0: 0x0001},
        expected_regs={0: 0x8000},
        expected_fcw_set=["C", "S"],  # LSB rotated out sets carry
        expected_fcw_clear=["Z"],
    ),

    # =========================================================================
    # RLC Rd, #n (rotate left through carry)
    # =========================================================================
    TestCase(
        name="rlc_r_carry_in",
        mnemonic="RLC",
        description="RLC R0, #1: rotate with carry=1, 0x0000 -> 0x0001",
        tags=["shift", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[0xB302, 0x0001],  # RLC R0, #1
        regs={0: 0x0000},
        expected_regs={0: 0x0001},
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # RRC Rd, #n (rotate right through carry)
    # =========================================================================
    TestCase(
        name="rrc_r_carry_in",
        mnemonic="RRC",
        description="RRC R0, #1: rotate with carry=1, 0x0000 -> 0x8000",
        tags=["shift", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[0xB302, 0xFFFF],  # RRC R0, #1 (count = -1)
        regs={0: 0x0000},
        expected_regs={0: 0x8000},
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z"],
    ),
]
