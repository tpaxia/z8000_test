"""Arithmetic instruction tests: ADD, ADDB, SUB, SUBB, ADC, SBC, INC, DEC, NEG."""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import OPERAND_BASE

TESTS = [
    # =========================================================================
    # ADD Rd, Rs (word, register-register)
    # =========================================================================
    TestCase(
        name="add_r_r_basic",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0x1234 + 0x5678 = 0x68AC",
        tags=["arithmetic", "word", "R_mode"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x68AC, 1: 0x5678},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="add_r_r_zero",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0x0000 + 0x0000 = 0x0000 (zero flag)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0x0000, 1: 0x0000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="add_r_r_carry",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0xFFFF + 0x0001 = 0x0000 (carry + zero)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0xFFFF, 1: 0x0001},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S", "V"],
    ),
    TestCase(
        name="add_r_r_sign",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0x7000 + 0x1000 = 0x8000 (sign flag)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0x7000, 1: 0x1000},
        expected_regs={0: 0x8000},
        expected_fcw_set=["S", "V"],  # Positive + positive = negative => overflow
        expected_fcw_clear=["C", "Z"],
    ),
    TestCase(
        name="add_r_r_overflow",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0x7FFF + 0x0001 = 0x8000 (signed overflow)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0x7FFF, 1: 0x0001},
        expected_regs={0: 0x8000},
        expected_fcw_set=["S", "V"],
        expected_fcw_clear=["C", "Z"],
    ),
    TestCase(
        name="add_r_r_carry_no_overflow",
        mnemonic="ADD",
        instruction="ADD R0, R1",
        description="ADD R0, R1: 0x8000 + 0x8000 = 0x0000 (carry, no signed overflow)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8110],  # ADD R0, R1
        regs={0: 0x8000, 1: 0x8000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z", "V"],  # Negative + negative = positive => overflow
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="add_r_r_no_flag_change",
        mnemonic="ADD",
        instruction="ADD R2, R3",
        description="ADD R2, R3: uses different register pair",
        tags=["arithmetic", "word", "R_mode"],
        code=[0x8132],  # ADD R2, R3
        regs={2: 0x0100, 3: 0x0200},
        expected_regs={2: 0x0300, 3: 0x0200},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # ADD Rd, #imm (word, immediate)
    # =========================================================================
    TestCase(
        name="add_r_imm_basic",
        mnemonic="ADD",
        instruction="ADD R0, #0x0100",
        description="ADD R0, #0x0100: 0x0200 + 0x0100 = 0x0300",
        tags=["arithmetic", "word", "IM_mode"],
        code=[0x0100, 0x0100],  # ADD R0, #0x0100
        regs={0: 0x0200},
        expected_regs={0: 0x0300},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="add_r_imm_carry",
        mnemonic="ADD",
        instruction="ADD R0, #0x0001",
        description="ADD R0, #0x0001: 0xFFFF + 0x0001 = 0x0000 (carry)",
        tags=["arithmetic", "word", "IM_mode", "flags"],
        code=[0x0100, 0x0001],  # ADD R0, #0x0001
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S", "V"],
    ),

    # =========================================================================
    # ADD Rd, @Rs (word, indirect register)
    # =========================================================================
    TestCase(
        name="add_r_ir_basic",
        mnemonic="ADD",
        instruction="ADD R0, @R2",
        description="ADD R0, @R2: R2 points to memory with 0x5678",
        tags=["arithmetic", "word", "IR_mode"],
        code=[0x0120],  # ADD R0, @R2
        regs={0: 0x1234, 2: OPERAND_BASE},
        memory={OPERAND_BASE: 0x5678},
        expected_regs={0: 0x68AC},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # ADD Rd, addr (word, direct address)
    # =========================================================================
    TestCase(
        name="add_r_da_basic",
        mnemonic="ADD",
        instruction="ADD R0, 0x0400",
        description="ADD R0, 0x0400: R0 + mem[0x0400]",
        tags=["arithmetic", "word", "DA_mode"],
        code=[0x4100, OPERAND_BASE],  # ADD R0, 0x0400
        regs={0: 0x1111},
        memory={OPERAND_BASE: 0x2222},
        expected_regs={0: 0x3333},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # SUB Rd, Rs (word, register-register)
    # =========================================================================
    TestCase(
        name="sub_r_r_basic",
        mnemonic="SUB",
        instruction="SUB R0, R1",
        description="SUB R0, R1: 0x5678 - 0x1234 = 0x4444",
        tags=["arithmetic", "word", "R_mode"],
        code=[0x8310],  # SUB R0, R1
        regs={0: 0x5678, 1: 0x1234},
        expected_regs={0: 0x4444, 1: 0x1234},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="sub_r_r_zero",
        mnemonic="SUB",
        instruction="SUB R0, R1",
        description="SUB R0, R1: 0x1234 - 0x1234 = 0x0000 (zero flag)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8310],  # SUB R0, R1
        regs={0: 0x1234, 1: 0x1234},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="sub_r_r_borrow",
        mnemonic="SUB",
        instruction="SUB R0, R1",
        description="SUB R0, R1: 0x0000 - 0x0001 = 0xFFFF (borrow/carry)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8310],  # SUB R0, R1
        regs={0: 0x0000, 1: 0x0001},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),
    TestCase(
        name="sub_r_r_overflow",
        mnemonic="SUB",
        instruction="SUB R0, R1",
        description="SUB R0, R1: 0x8000 - 0x0001 = 0x7FFF (signed overflow)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8310],  # SUB R0, R1
        regs={0: 0x8000, 1: 0x0001},
        expected_regs={0: 0x7FFF},
        expected_fcw_set=["V"],
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # SUB Rd, #imm (word, immediate)
    # =========================================================================
    TestCase(
        name="sub_r_imm_basic",
        mnemonic="SUB",
        instruction="SUB R0, #0x0100",
        description="SUB R0, #0x0100: 0x0300 - 0x0100 = 0x0200",
        tags=["arithmetic", "word", "IM_mode"],
        code=[0x0300, 0x0100],  # SUB R0, #0x0100
        regs={0: 0x0300},
        expected_regs={0: 0x0200},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # ADC Rd, Rs (word, add with carry)
    # =========================================================================
    TestCase(
        name="adc_r_r_no_carry_in",
        mnemonic="ADC",
        instruction="ADC R0, R1",
        description="ADC R0, R1: 0x1234 + 0x5678 + C=0 = 0x68AC",
        tags=["arithmetic", "word", "R_mode"],
        fcw=FCW_SYS,  # Carry clear
        code=[0xB510],  # ADC R0, R1
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x68AC},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="adc_r_r_carry_in",
        mnemonic="ADC",
        instruction="ADC R0, R1",
        description="ADC R0, R1: 0x1234 + 0x5678 + C=1 = 0x68AD",
        tags=["arithmetic", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),  # Carry set
        code=[0xB510],  # ADC R0, R1
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x68AD},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="adc_r_r_carry_in_carry_out",
        mnemonic="ADC",
        instruction="ADC R0, R1",
        description="ADC R0, R1: 0xFFFF + 0x0000 + C=1 = 0x0000 (carry out)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[0xB510],  # ADC R0, R1
        regs={0: 0xFFFF, 1: 0x0000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S", "V"],
    ),

    # =========================================================================
    # SBC Rd, Rs (word, subtract with carry/borrow)
    # =========================================================================
    TestCase(
        name="sbc_r_r_no_carry_in",
        mnemonic="SBC",
        instruction="SBC R0, R1",
        description="SBC R0, R1: 0x5678 - 0x1234 - C=0 = 0x4444",
        tags=["arithmetic", "word", "R_mode"],
        fcw=FCW_SYS,
        code=[0xB710],  # SBC R0, R1
        regs={0: 0x5678, 1: 0x1234},
        expected_regs={0: 0x4444},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="sbc_r_r_carry_in",
        mnemonic="SBC",
        instruction="SBC R0, R1",
        description="SBC R0, R1: 0x5678 - 0x1234 - C=1 = 0x4443",
        tags=["arithmetic", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[0xB710],  # SBC R0, R1
        regs={0: 0x5678, 1: 0x1234},
        expected_regs={0: 0x4443},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="sbc_r_r_borrow_out",
        mnemonic="SBC",
        instruction="SBC R0, R1",
        description="SBC R0, R1: 0x0000 - 0x0000 - C=1 = 0xFFFF (borrow)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(C=1),
        code=[0xB710],  # SBC R0, R1
        regs={0: 0x0000, 1: 0x0000},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),

    # =========================================================================
    # INC Rd, #n (word, increment by 1-16)
    # =========================================================================
    TestCase(
        name="inc_r_by1",
        mnemonic="INC",
        instruction="INC R0, #1",
        description="INC R0, #1: 0x0000 + 1 = 0x0001",
        tags=["arithmetic", "word", "R_mode"],
        code=[0xA900],  # INC R0, #1 (n-1=0 in bits 3-0, Rd=0 in bits 7-4)
        regs={0: 0x0000},
        expected_regs={0: 0x0001},
        expected_fcw_clear=["Z", "S", "V"],
    ),
    TestCase(
        name="inc_r_by1_overflow",
        mnemonic="INC",
        instruction="INC R0, #1",
        description="INC R0, #1: 0xFFFF + 1 = 0x0000 (overflow, no carry change)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0xA900],  # INC R0, #1
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        # Note: INC does not affect carry flag
    ),
    TestCase(
        name="inc_r_by2",
        mnemonic="INC",
        instruction="INC R0, #2",
        description="INC R0, #2: 0x0010 + 2 = 0x0012",
        tags=["arithmetic", "word", "R_mode"],
        code=[0xA901],  # INC R0, #2 (n-1=1)
        regs={0: 0x0010},
        expected_regs={0: 0x0012},
        expected_fcw_clear=["Z", "S", "V"],
    ),

    # =========================================================================
    # DEC Rd, #n (word, decrement by 1-16)
    # =========================================================================
    TestCase(
        name="dec_r_by1",
        mnemonic="DEC",
        instruction="DEC R0, #1",
        description="DEC R0, #1: 0x0005 - 1 = 0x0004",
        tags=["arithmetic", "word", "R_mode"],
        code=[0xAB00],  # DEC R0, #1
        regs={0: 0x0005},
        expected_regs={0: 0x0004},
        expected_fcw_clear=["Z", "S", "V"],
    ),
    TestCase(
        name="dec_r_by1_zero",
        mnemonic="DEC",
        instruction="DEC R0, #1",
        description="DEC R0, #1: 0x0001 - 1 = 0x0000 (zero flag)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0xAB00],  # DEC R0, #1
        regs={0: 0x0001},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S", "V"],
        # Note: DEC does not affect carry flag
    ),
    TestCase(
        name="dec_r_by1_underflow",
        mnemonic="DEC",
        instruction="DEC R0, #1",
        description="DEC R0, #1: 0x0000 - 1 = 0xFFFF",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0xAB00],  # DEC R0, #1
        regs={0: 0x0000},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z"],
        # Note: DEC does not affect carry flag
    ),

    # =========================================================================
    # NEG Rd (word, negate/two's complement)
    # =========================================================================
    TestCase(
        name="neg_r_positive",
        mnemonic="NEG",
        instruction="NEG R0",
        description="NEG R0: 0 - 0x0001 = 0xFFFF",
        tags=["arithmetic", "word", "R_mode"],
        code=[0x8D02],  # NEG R0: 10001101_0000_0010
        regs={0: 0x0001},
        expected_regs={0: 0xFFFF},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),
    TestCase(
        name="neg_r_zero",
        mnemonic="NEG",
        instruction="NEG R0",
        description="NEG R0: 0 - 0x0000 = 0x0000",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8D02],  # NEG R0
        regs={0: 0x0000},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="neg_r_8000",
        mnemonic="NEG",
        instruction="NEG R0",
        description="NEG R0: 0 - 0x8000 = 0x8000 (overflow)",
        tags=["arithmetic", "word", "R_mode", "flags"],
        code=[0x8D02],  # NEG R0
        regs={0: 0x8000},
        expected_regs={0: 0x8000},
        expected_fcw_set=["C", "S", "V"],
        expected_fcw_clear=["Z"],
    ),

    # =========================================================================
    # ADDB Rbd, Rbs (byte, register-register)
    # Byte register encoding: RH0-RH7 = 0-7, RL0-RL7 = 8-15
    # =========================================================================
    TestCase(
        name="addb_r_r_basic",
        mnemonic="ADDB",
        instruction="ADDB RH0, RL0",
        description="ADDB RH0, RL0: 0x12 + 0x34 = 0x46",
        tags=["arithmetic", "byte", "R_mode"],
        # ADDB Rbd, Rbs: 10000000_Rbss_Rbdd
        # RH0=0, RL0=8 -> Rbss=1000, Rbdd=0000 -> 0x8080
        code=[0x8080],
        regs={0: 0x1234},  # RH0=0x12, RL0=0x34
        expected_regs={0: 0x4634},  # RH0 = 0x12+0x34 = 0x46, RL0 unchanged
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # SUBB Rbd, Rbs (byte, register-register)
    # =========================================================================
    TestCase(
        name="subb_r_r_basic",
        mnemonic="SUBB",
        instruction="SUBB RH0, RL0",
        description="SUBB RH0, RL0: 0xFF - 0x01 = 0xFE",
        tags=["arithmetic", "byte", "R_mode"],
        # SUBB Rbd, Rbs: 10000010_Rbss_Rbdd
        # RH0=0, RL0=8 -> Rbss=1000, Rbdd=0000 -> 0x8280
        code=[0x8280],
        regs={0: 0xFF01},  # RH0=0xFF, RL0=0x01
        expected_regs={0: 0xFE01},  # RH0 = 0xFF-0x01 = 0xFE, RL0 unchanged
        expected_fcw_set=["S"],
        expected_fcw_clear=["C", "Z", "V"],
    ),
]
