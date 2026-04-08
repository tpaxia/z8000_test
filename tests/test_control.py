"""Control instruction tests: NOP, SETFLG, RESFLG, COMFLG, TCC, LDCTL, EI, DI."""

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
        expected_fcw_set=["C", "H"],
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
        expected_fcw_set=["H"],
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
        expected_fcw_set=["C", "Z", "S", "V", "H"],
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

    # =========================================================================
    # LDCTL - load control register
    # LDCTL Rd, FCW:       7d_Rd_02
    # LDCTL FCW, Rs:       7d_Rs_0a
    # LDCTL Rd, PSAPOFF:   7d_Rd_05
    # LDCTL PSAPOFF, Rs:   7d_Rs_0d
    # LDCTL Rd, REFRESH:   7d_Rd_03
    # LDCTL REFRESH, Rs:   7d_Rs_0b
    # =========================================================================
    TestCase(
        name="ldctl_read_fcw",
        mnemonic="LDCTL",
        instruction="LDCTL R0, FCW",
        description="LDCTL R0, FCW: read FCW into R0",
        tags=["control", "word", "ldctl"],
        fcw=fcw_with_flags(C=1, Z=1),  # 0x40C0
        code=[0x7D02],  # ldctl r0, fcw
        regs={0: 0x0000},
        expected_regs={0: 0x40C0},
    ),
    TestCase(
        name="ldctl_read_fcw_all_flags",
        mnemonic="LDCTL",
        instruction="LDCTL R0, FCW",
        description="LDCTL R0, FCW: read FCW with all flags set",
        tags=["control", "word", "ldctl"],
        fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),  # 0x40F0
        code=[0x7D02],  # ldctl r0, fcw
        regs={0: 0x0000},
        expected_regs={0: 0x40F0},
    ),
    TestCase(
        name="ldctl_write_fcw",
        mnemonic="LDCTL",
        instruction="LDCTL FCW, R0",
        description="LDCTL FCW, R0: write R0 into FCW (set all flags)",
        tags=["control", "word", "ldctl", "flags"],
        fcw=FCW_SYS,
        code=[0x7D0A],  # ldctl fcw, r0
        regs={0: 0x40F0},
        expected_fcw_set=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="ldctl_write_fcw_clear_flags",
        mnemonic="LDCTL",
        instruction="LDCTL FCW, R0",
        description="LDCTL FCW, R0: write R0 into FCW (clear all flags)",
        tags=["control", "word", "ldctl", "flags"],
        fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        code=[0x7D0A],  # ldctl fcw, r0
        regs={0: 0x4000},
        expected_fcw_clear=["C", "Z", "S", "V"],
    ),
    TestCase(
        name="ldctl_read_fcw_r1",
        mnemonic="LDCTL",
        instruction="LDCTL R1, FCW",
        description="LDCTL R1, FCW: read FCW into R1 (non-R0 dest)",
        tags=["control", "word", "ldctl"],
        fcw=fcw_with_flags(S=1, V=1),  # 0x4030
        code=[0x7D12],  # ldctl r1, fcw
        regs={1: 0x0000},
        expected_regs={1: 0x4030},
    ),
    TestCase(
        name="ldctl_write_fcw_r1",
        mnemonic="LDCTL",
        instruction="LDCTL FCW, R1",
        description="LDCTL FCW, R1: write R1 into FCW (non-R0 source)",
        tags=["control", "word", "ldctl", "flags"],
        fcw=FCW_SYS,
        code=[0x7D1A],  # ldctl fcw, r1
        regs={1: 0x40F0},
        expected_fcw_set=["C", "Z", "S", "V"],
    ),

    # =========================================================================
    # EI - enable interrupts
    # EI VI:      7c05  (set VIE bit 11)
    # EI NVI:     7c06  (set NVIE bit 12)
    # EI VI,NVI:  7c04  (set both)
    # =========================================================================
    TestCase(
        name="ei_vi",
        mnemonic="EI",
        instruction="EI VI",
        description="EI VI: enable vectored interrupts",
        tags=["control", "interrupt"],
        fcw=FCW_SYS,  # 0x4000, VIE=0, NVIE=0
        code=[0x7C05],  # ei vi
        expected_fcw_set=["VIE"],
        expected_fcw_clear=["NVIE"],
    ),
    TestCase(
        name="ei_nvi",
        mnemonic="EI",
        instruction="EI NVI",
        description="EI NVI: enable non-vectored interrupts",
        tags=["control", "interrupt"],
        fcw=FCW_SYS,
        code=[0x7C06],  # ei nvi
        expected_fcw_set=["NVIE"],
        expected_fcw_clear=["VIE"],
    ),
    TestCase(
        name="ei_vi_nvi",
        mnemonic="EI",
        instruction="EI VI,NVI",
        description="EI VI,NVI: enable both interrupt types",
        tags=["control", "interrupt"],
        fcw=FCW_SYS,
        code=[0x7C04],  # ei vi,nvi
        expected_fcw_set=["VIE", "NVIE"],
    ),

    # =========================================================================
    # DI - disable interrupts
    # DI VI:      7c01  (clear VIE bit 11)
    # DI NVI:     7c02  (clear NVIE bit 12)
    # DI VI,NVI:  7c00  (clear both)
    # =========================================================================
    TestCase(
        name="di_vi",
        mnemonic="DI",
        instruction="DI VI",
        description="DI VI: disable vectored interrupts",
        tags=["control", "interrupt"],
        fcw=FCW_SYS | 0x1800,  # VIE=1, NVIE=1
        code=[0x7C01],  # di vi
        expected_fcw_clear=["VIE"],
        expected_fcw_set=["NVIE"],
    ),
    TestCase(
        name="di_nvi",
        mnemonic="DI",
        instruction="DI NVI",
        description="DI NVI: disable non-vectored interrupts",
        tags=["control", "interrupt"],
        fcw=FCW_SYS | 0x1800,  # VIE=1, NVIE=1
        code=[0x7C02],  # di nvi
        expected_fcw_set=["VIE"],
        expected_fcw_clear=["NVIE"],
    ),
    TestCase(
        name="di_vi_nvi",
        mnemonic="DI",
        instruction="DI VI,NVI",
        description="DI VI,NVI: disable both interrupt types",
        tags=["control", "interrupt"],
        fcw=FCW_SYS | 0x1800,  # VIE=1, NVIE=1
        code=[0x7C00],  # di vi,nvi
        expected_fcw_clear=["VIE", "NVIE"],
    ),
]
