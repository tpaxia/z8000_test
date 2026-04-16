"""Logical instruction tests: AND, OR, XOR, COM, CLR."""

from .defs import TestCase
from .flags import FCW_SYS, FCW_SYS_CARRY

TESTS = [
    # =========================================================================
    # AND Rd, Rs (word)
    # =========================================================================
    TestCase(
        name="and_r_r_basic",
        mnemonic="AND",
        instruction="AND R0, R1",
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
        instruction="AND R0, R1",
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
        instruction="AND R0, R1",
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
        instruction="AND R0, #0x00FF",
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
        instruction="OR R0, R1",
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
        instruction="OR R0, R1",
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
        instruction="OR R0, #0xFF00",
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
        instruction="XOR R0, R1",
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
        instruction="XOR R0, R1",
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
        instruction="XOR R0, #0xFFFF",
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
        instruction="COM R0",
        description="COM R0: ~0x00FF = 0xFF00",
        tags=["logical", "word", "R_mode"],
        issues=["Z8002 sets C flag, Z8001 does not; COM should not affect C"],
        code=[0x8D00],  # COM R0: 10001101_0000_0000
        regs={0: 0x00FF},
        expected_regs={0: 0xFF00},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z", "C"],
    ),
    TestCase(
        name="com_r_zero",
        mnemonic="COM",
        instruction="COM R0",
        description="COM R0: ~0xFFFF = 0x0000",
        tags=["logical", "word", "R_mode", "flags"],
        issues=["Z8002 sets C flag, Z8001 does not; COM should not affect C"],
        code=[0x8D00],
        regs={0: 0xFFFF},
        expected_regs={0: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S", "C"],
    ),

    # =========================================================================
    # CLR Rd (word)
    # =========================================================================
    TestCase(
        name="clr_r_basic",
        mnemonic="CLR",
        instruction="CLR R0",
        description="CLR R0: R0 = 0x0000",
        tags=["logical", "word", "R_mode"],
        code=[0x8D08],  # CLR R0: 10001101_0000_1000
        regs={0: 0xDEAD},
        expected_regs={0: 0x0000},
    ),
    TestCase(
        name="clr_r_other_reg",
        mnemonic="CLR",
        instruction="CLR R5",
        description="CLR R5: R5 = 0x0000",
        tags=["logical", "word", "R_mode"],
        code=[0x8D58],  # CLR R5: 10001101_0101_1000
        regs={5: 0xBEEF},
        expected_regs={5: 0x0000},
    ),

    # =========================================================================
    # Flag preservation tests — C and V flags across logical operations
    #
    # Per Z8000 manual: AND/ANDB, OR/ORB, XOR/XORB, TEST/TESTB, COM/COMB
    # all specify C as "Unaffected" and (for word ops) V as "Unaffected".
    #
    # These tests pre-set C=1 (or V=1) via FCW before the instruction.
    # On a correct CPU, the flag must be preserved. A bug that clears C/V
    # during logical ops will show as a golden mismatch.
    #
    # Manual references:
    #   AND  (line 2892): C: Unaffected, P: AND-unaffected; ANDB-parity
    #   OR   (line 6328): C: Unaffected, P: OR-unaffected; ORB-parity
    #   XOR  (line 8979): C: Unaffected
    #   TEST (line 8310): C: Unaffected, P: TEST-unaffected; TESTB-parity
    # =========================================================================

    # ---- C flag preservation (pre-set C=1, verify preserved) ----

    TestCase(
        name="and_r_r_preserve_c",
        mnemonic="AND",
        instruction="AND R0, R1",
        description="AND R0, R1 with C=1 pre-set: C must stay 1 (unaffected)",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,          # C=1 pre-set
        code=[0x8710],               # AND R0, R1
        regs={0: 0xFF00, 1: 0x0F0F},
        expected_regs={0: 0x0F00},
        expected_fcw_set=["C"],      # C must be preserved as 1
    ),
    TestCase(
        name="andb_r_r_preserve_c",
        mnemonic="ANDB",
        instruction="ANDB RH0, RH1",
        description="ANDB RH0, RH1 with C=1 pre-set: C must stay 1",
        tags=["logical", "byte", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8610],               # ANDB RH0, RH1
        regs={0: 0xF000, 1: 0x0F00},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C"],
    ),
    TestCase(
        name="or_r_r_preserve_c",
        mnemonic="OR",
        instruction="OR R0, R1",
        description="OR R0, R1 with C=1 pre-set: C must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8510],               # OR R0, R1
        regs={0: 0x00F0, 1: 0x0F00},
        expected_regs={0: 0x0FF0},
        expected_fcw_set=["C"],
    ),
    TestCase(
        name="orb_r_r_preserve_c",
        mnemonic="ORB",
        instruction="ORB RL0, RL1",
        description="ORB RL0, RL1 with C=1 pre-set: C must stay 1",
        tags=["logical", "byte", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8498],               # ORB RL0, RL1
        regs={0: 0x000F, 1: 0x00F0},
        expected_regs={0: 0x00FF},
        expected_fcw_set=["C"],
    ),
    TestCase(
        name="xor_r_r_preserve_c",
        mnemonic="XOR",
        instruction="XOR R0, R1",
        description="XOR R0, R1 with C=1 pre-set: C must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8910],               # XOR R0, R1
        regs={0: 0xFF00, 1: 0x0FF0},
        expected_regs={0: 0xF0F0},
        expected_fcw_set=["C"],
    ),
    TestCase(
        name="xorb_r_r_preserve_c",
        mnemonic="XORB",
        instruction="XORB RH0, RH1",
        description="XORB RH0, RH1 with C=1 pre-set: C must stay 1",
        tags=["logical", "byte", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8810],               # XORB RH0, RH1
        regs={0: 0xFF00, 1: 0x0F00},
        expected_regs={0: 0xF000},
        expected_fcw_set=["C"],
    ),
    TestCase(
        name="test_r_preserve_c",
        mnemonic="TEST",
        instruction="TEST R0",
        description="TEST R0 with C=1 pre-set: C must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8D04],               # TEST R0
        regs={0: 0x1234},
        expected_regs={0: 0x1234},
        expected_fcw_set=["C"],
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="testb_r_preserve_c",
        mnemonic="TESTB",
        instruction="TESTB RH0",
        description="TESTB RH0 with C=1 pre-set: C must stay 1",
        tags=["logical", "byte", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8C04],               # TESTB RH0
        regs={0: 0x1200},
        expected_regs={0: 0x1200},
        expected_fcw_set=["C"],
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="com_r_preserve_c",
        mnemonic="COM",
        instruction="COM R0",
        description="COM R0 with C=1 pre-set: C must stay 1 (unaffected)",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS_CARRY,
        code=[0x8D00],               # COM R0
        regs={0: 0x00FF},
        expected_regs={0: 0xFF00},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z"],
    ),

    # ---- V flag preservation for word-mode logical ops ----
    # Manual: AND/OR/XOR/TEST (word) — V "Unaffected"
    # Byte ops set P (parity) in the V position, so only test word ops.

    TestCase(
        name="and_r_r_preserve_v",
        mnemonic="AND",
        instruction="AND R0, R1",
        description="AND R0, R1 with V=1 pre-set: V must stay 1 (unaffected)",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0010,       # V=1 pre-set (bit 4)
        code=[0x8710],
        regs={0: 0xFF00, 1: 0x0F0F},
        expected_regs={0: 0x0F00},
        expected_fcw_set=["V"],
    ),
    TestCase(
        name="or_r_r_preserve_v",
        mnemonic="OR",
        instruction="OR R0, R1",
        description="OR R0, R1 with V=1 pre-set: V must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0010,
        code=[0x8510],
        regs={0: 0x00F0, 1: 0x0F00},
        expected_regs={0: 0x0FF0},
        expected_fcw_set=["V"],
    ),
    TestCase(
        name="xor_r_r_preserve_v",
        mnemonic="XOR",
        instruction="XOR R0, R1",
        description="XOR R0, R1 with V=1 pre-set: V must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0010,
        code=[0x8910],
        regs={0: 0xFF00, 1: 0x0FF0},
        expected_regs={0: 0xF0F0},
        expected_fcw_set=["V"],
    ),
    TestCase(
        name="test_r_preserve_v",
        mnemonic="TEST",
        instruction="TEST R0",
        description="TEST R0 with V=1 pre-set: V must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0010,
        code=[0x8D04],
        regs={0: 0x1234},
        expected_regs={0: 0x1234},
        expected_fcw_set=["V"],
    ),
    TestCase(
        name="com_r_preserve_v",
        mnemonic="COM",
        instruction="COM R0",
        description="COM R0 with V=1 pre-set: V must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0010,
        code=[0x8D00],
        regs={0: 0x00FF},
        expected_regs={0: 0xFF00},
        expected_fcw_set=["V"],
    ),

    # ---- Both C and V pre-set (combined test) ----

    TestCase(
        name="and_r_r_preserve_cv",
        mnemonic="AND",
        instruction="AND R0, R1",
        description="AND R0, R1 with C=1 and V=1 pre-set: both must stay 1",
        tags=["logical", "word", "R_mode", "flag_preserve"],
        fcw=FCW_SYS | 0x0090,       # C=1 (bit 7) + V=1 (bit 4)
        code=[0x8710],
        regs={0: 0xF0F0, 1: 0x0F0F},
        expected_regs={0: 0x0000},
        expected_fcw_set=["C", "V", "Z"],
        expected_fcw_clear=["S"],
    ),
]
