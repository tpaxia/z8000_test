"""Exchange and extend instruction tests: EX, EXB, EXTS, EXTSB."""

from .defs import TestCase
from .flags import FCW_SYS

# EX Rd, Rs: 10101101_Rsss_Rddd
# EXTS RRd: 10110001_RRdd_1010  (sign-extend word to long)
# EXTSB Rd: 10110001_Rddd_0000  (sign-extend byte to word)

TESTS = [
    # =========================================================================
    # EX Rd, Rs (exchange registers)
    # =========================================================================
    TestCase(
        name="ex_r_r_basic",
        mnemonic="EX",
        description="EX R0, R1: swap R0 and R1",
        tags=["exchange", "word", "R_mode"],
        code=[0xAD10],  # EX R0, R1
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x5678, 1: 0x1234},
    ),
    TestCase(
        name="ex_r_r_same",
        mnemonic="EX",
        description="EX R0, R0: swap with self (no-op)",
        tags=["exchange", "word", "R_mode"],
        code=[0xAD00],  # EX R0, R0
        regs={0: 0xAAAA},
        expected_regs={0: 0xAAAA},
    ),

    # =========================================================================
    # EXTSB Rd (sign-extend byte to word)
    # =========================================================================
    TestCase(
        name="extsb_positive",
        mnemonic="EXTSB",
        description="EXTSB R0: 0x007F -> 0x007F (positive byte)",
        tags=["exchange", "word", "R_mode"],
        code=[0xB100],  # EXTSB R0
        regs={0: 0xFF7F},  # Low byte = 0x7F (positive)
        expected_regs={0: 0x007F},
    ),
    TestCase(
        name="extsb_negative",
        mnemonic="EXTSB",
        description="EXTSB R0: 0x0080 -> 0xFF80 (negative byte, sign extended)",
        tags=["exchange", "word", "R_mode"],
        code=[0xB100],  # EXTSB R0
        regs={0: 0x0080},  # Low byte = 0x80 (negative)
        expected_regs={0: 0xFF80},
    ),
    TestCase(
        name="extsb_zero",
        mnemonic="EXTSB",
        description="EXTSB R0: 0xFF00 -> 0x0000 (zero byte)",
        tags=["exchange", "word", "R_mode"],
        code=[0xB100],
        regs={0: 0xFF00},  # Low byte = 0x00
        expected_regs={0: 0x0000},
    ),

    # =========================================================================
    # EXTS RRd (sign-extend word to long)
    # =========================================================================
    TestCase(
        name="exts_positive",
        mnemonic="EXTS",
        description="EXTS RR0: R1=0x7FFF -> RR0 = 0x00007FFF",
        tags=["exchange", "long", "R_mode"],
        code=[0xB10A],  # EXTS RR0 (RRd=0, subop=1010)
        regs={0: 0xFFFF, 1: 0x7FFF},  # R0=high, R1=low (word to extend)
        expected_regs={0: 0x0000, 1: 0x7FFF},
    ),
    TestCase(
        name="exts_negative",
        mnemonic="EXTS",
        description="EXTS RR0: R1=0x8000 -> RR0 = 0xFFFF8000",
        tags=["exchange", "long", "R_mode"],
        code=[0xB10A],  # EXTS RR0
        regs={0: 0x0000, 1: 0x8000},
        expected_regs={0: 0xFFFF, 1: 0x8000},
    ),
]
