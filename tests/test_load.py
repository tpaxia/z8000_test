"""Load instruction tests: LD, LDK, LDA, LDM."""

from .defs import TestCase
from .flags import FCW_SYS
from .helpers import OPERAND_BASE

TESTS = [
    # =========================================================================
    # LD Rd, Rs (word, register-register)
    # =========================================================================
    TestCase(
        name="ld_r_r_basic",
        mnemonic="LD",
        description="LD R0, R1: R0 = R1 = 0x1234",
        tags=["load", "word", "R_mode"],
        code=[0xA110],  # LD R0, R1
        regs={0: 0x0000, 1: 0x1234},
        expected_regs={0: 0x1234, 1: 0x1234},
    ),
    TestCase(
        name="ld_r_r_self",
        mnemonic="LD",
        description="LD R0, R0: R0 unchanged",
        tags=["load", "word", "R_mode"],
        code=[0xA100],  # LD R0, R0
        regs={0: 0xBEEF},
        expected_regs={0: 0xBEEF},
    ),

    # =========================================================================
    # LD Rd, #imm (word, immediate)
    # =========================================================================
    TestCase(
        name="ld_r_imm_basic",
        mnemonic="LD",
        description="LD R0, #0x1234",
        tags=["load", "word", "IM_mode"],
        code=[0x2100, 0x1234],  # LD R0, #0x1234
        regs={0: 0x0000},
        expected_regs={0: 0x1234},
    ),
    TestCase(
        name="ld_r_imm_zero",
        mnemonic="LD",
        description="LD R0, #0x0000",
        tags=["load", "word", "IM_mode"],
        code=[0x2100, 0x0000],
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="ld_r_imm_ffff",
        mnemonic="LD",
        description="LD R0, #0xFFFF",
        tags=["load", "word", "IM_mode"],
        code=[0x2100, 0xFFFF],
        regs={0: 0x0000},
        expected_regs={0: 0xFFFF},
    ),

    # =========================================================================
    # LD Rd, @Rs (word, indirect register)
    # =========================================================================
    TestCase(
        name="ld_r_ir_basic",
        mnemonic="LD",
        description="LD R0, @R2: load from memory pointed by R2",
        tags=["load", "word", "IR_mode"],
        code=[0x2120],  # LD R0, @R2
        regs={0: 0x0000, 2: OPERAND_BASE},
        memory={OPERAND_BASE: 0xABCD},
        expected_regs={0: 0xABCD, 2: OPERAND_BASE},
    ),

    # =========================================================================
    # LD Rd, addr (word, direct address)
    # =========================================================================
    TestCase(
        name="ld_r_da_basic",
        mnemonic="LD",
        description="LD R0, 0x0400: load from direct address",
        tags=["load", "word", "DA_mode"],
        code=[0x6100, OPERAND_BASE],  # LD R0, 0x0400
        regs={0: 0x0000},
        memory={OPERAND_BASE: 0xDEAD},
        expected_regs={0: 0xDEAD},
    ),

    # =========================================================================
    # LD addr, Rs (word, store to direct address)
    # =========================================================================
    TestCase(
        name="ld_da_r_basic",
        mnemonic="LD",
        description="LD 0x0400, R0: store to direct address",
        tags=["load", "word", "DA_mode", "store"],
        code=[0x6F00, OPERAND_BASE],  # LD 0x0400, R0
        regs={0: 0xCAFE},
        expected_regs={0: 0xCAFE},
        expected_memory={OPERAND_BASE: 0xCAFE},
    ),

    # =========================================================================
    # LD Rd, addr(Rs) (word, indexed)
    # =========================================================================
    TestCase(
        name="ld_r_x_basic",
        mnemonic="LD",
        description="LD R0, 0x0400(R2): indexed load, base+offset",
        tags=["load", "word", "X_mode"],
        # LD Rd, addr(Rs): 01100001_Rsnz_Rddd + address
        code=[0x6120, OPERAND_BASE],  # LD R0, 0x0400(R2)
        regs={0: 0x0000, 2: 0x0004},
        memory={OPERAND_BASE + 0x0004: 0xBEEF},
        expected_regs={0: 0xBEEF},
    ),

    # =========================================================================
    # LDK Rd, #nibble (load constant 0-15)
    # =========================================================================
    TestCase(
        name="ldk_r_basic",
        mnemonic="LDK",
        description="LDK R0, #5: R0 = 0x0005",
        tags=["load", "word", "R_mode"],
        # LDK Rd, #data: 10111101_Rddd_dddd (4-bit data in bits 3-0)
        code=[0xBD05],  # LDK R0, #5
        regs={0: 0xFFFF},
        expected_regs={0: 0x0005},
    ),
    TestCase(
        name="ldk_r_zero",
        mnemonic="LDK",
        description="LDK R0, #0: R0 = 0x0000",
        tags=["load", "word", "R_mode"],
        code=[0xBD00],  # LDK R0, #0
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="ldk_r_fifteen",
        mnemonic="LDK",
        description="LDK R0, #15: R0 = 0x000F",
        tags=["load", "word", "R_mode"],
        code=[0xBD0F],  # LDK R0, #15
        regs={0: 0xFFFF},
        expected_regs={0: 0x000F},
    ),
]
