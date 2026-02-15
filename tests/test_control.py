"""Control instruction tests: NOP, SETFLG, RESFLG, COMFLG, TCC, LDCTL."""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags

TESTS = [
    # =========================================================================
    # NOP
    # =========================================================================
    TestCase(
        name="nop_basic",
        mnemonic="NOP",
        instruction="NOP",
        description="NOP: no operation, registers unchanged",
        tags=["control", "word"],
        code=[0x8D07],  # NOP
        regs={0: 0x1234, 1: 0x5678},
        expected_regs={0: 0x1234, 1: 0x5678},
    ),

    # =========================================================================
    # SETFLG flags - set flag bits
    # 10001101_CZSV_0001, CZSV maps to FCW bits 7-4
    # Encoding: CZSV nibble: C=bit3, Z=bit2, S=bit1, V=bit0
    # =========================================================================
    TestCase(
        name="setflg_carry",
        mnemonic="SETFLG",
        instruction="SETFLG C",
        description="SETFLG C: set carry flag",
        tags=["control", "flags"],
        fcw=FCW_SYS,  # All flags clear
        code=[0x8D81],  # SETFLG C (CZSV=1000=0x8)
        expected_fcw_set=["C"],
        expected_fcw_clear=["Z", "S", "V"],
    ),
    TestCase(
        name="setflg_zero",
        mnemonic="SETFLG",
        instruction="SETFLG Z",
        description="SETFLG Z: set zero flag",
        tags=["control", "flags"],
        fcw=FCW_SYS,
        code=[0x8D41],  # SETFLG Z (CZSV=0100=0x4)
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S", "V"],
    ),
    TestCase(
        name="setflg_all",
        mnemonic="SETFLG",
        instruction="SETFLG CZSV",
        description="SETFLG CZSV: set all flags",
        tags=["control", "flags"],
        fcw=FCW_SYS,
        code=[0x8DF1],  # SETFLG CZSV (CZSV=1111=0xF)
        expected_fcw_set=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # RESFLG flags - reset flag bits
    # 10001101_CZSV_0011
    # =========================================================================
    TestCase(
        name="resflg_carry",
        mnemonic="RESFLG",
        instruction="RESFLG C",
        description="RESFLG C: clear carry flag",
        tags=["control", "flags"],
        fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        code=[0x8D83],  # RESFLG C (CZSV=1000)
        expected_fcw_clear=["C"],
        expected_fcw_set=["Z", "S", "V"],
    ),
    TestCase(
        name="resflg_all",
        mnemonic="RESFLG",
        instruction="RESFLG CZSV",
        description="RESFLG CZSV: clear all flags",
        tags=["control", "flags"],
        fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        code=[0x8DF3],  # RESFLG CZSV (CZSV=1111)
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # COMFLG flags - complement flag bits
    # 10001101_CZSV_0101
    # =========================================================================
    TestCase(
        name="comflg_carry",
        mnemonic="COMFLG",
        instruction="COMFLG C",
        description="COMFLG C: toggle carry flag (0->1)",
        tags=["control", "flags"],
        issues=["Z8001 also toggles H flag (undocumented); Z8002 does not"],
        fcw=FCW_SYS,
        code=[0x8D85],  # COMFLG C (CZSV=1000)
        expected_fcw_set=["C"],
        expected_fcw_clear=["Z", "S", "V"],
    ),
    TestCase(
        name="comflg_carry_clear",
        mnemonic="COMFLG",
        instruction="COMFLG C",
        description="COMFLG C: toggle carry flag (1->0)",
        tags=["control", "flags"],
        issues=["Z8001 also toggles H flag (undocumented); Z8002 does not"],
        fcw=fcw_with_flags(C=1),
        code=[0x8D85],  # COMFLG C
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="comflg_all",
        mnemonic="COMFLG",
        instruction="COMFLG CZSV",
        description="COMFLG CZSV: toggle all flags (all 0 -> all 1)",
        tags=["control", "flags"],
        issues=["Z8001 also toggles H flag (undocumented); Z8002 does not"],
        fcw=FCW_SYS,
        code=[0x8DF5],  # COMFLG CZSV
        expected_fcw_set=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # TCC cc, Rd - test condition code, set bit 0 of Rd
    # TCC cc, Rd: 10101111_Rddd_cccc
    # =========================================================================
    TestCase(
        name="tcc_z_set",
        mnemonic="TCC",
        instruction="TCC Z, R0",
        description="TCC Z, R0: Z=1, R0 |= 1",
        tags=["control", "word", "R_mode", "flags"],
        fcw=fcw_with_flags(Z=1),
        code=[0xAF06],  # TCC Z, R0
        regs={0: 0x0000},
        expected_regs={0: 0x0001},
    ),
    TestCase(
        name="tcc_z_clear",
        mnemonic="TCC",
        instruction="TCC Z, R0",
        description="TCC Z, R0: Z=0, R0 unchanged",
        tags=["control", "word", "R_mode", "flags"],
        fcw=FCW_SYS,
        code=[0xAF06],  # TCC Z, R0
        regs={0: 0x0000},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="tcc_always",
        mnemonic="TCC",
        instruction="TCC T, R0",
        description="TCC T, R0: always true, R0 |= 1",
        tags=["control", "word", "R_mode"],
        code=[0xAF08],  # TCC T (always), R0
        regs={0: 0xFFF0},
        expected_regs={0: 0xFFF1},
    ),
]
