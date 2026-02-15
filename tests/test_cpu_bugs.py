"""Tests targeting known CPU core issues.

Each test is tagged with the issue number it targets. These tests are expected
to FAIL on the current CPU core and PASS once the corresponding fix is applied.

Issues:
 1. H flag never computed (DAB can't work correctly)
 2. DAB doesn't update C/Z/S flags
 3. INC/DEC/NEG memory modes (IR/DA/X) skip flag updates entirely
 4. ADDL/SUBL 32-bit Z flag only checks high word
 5. CPL 32-bit Z flag only checks high word
 6. TESTL S flag computed from high|low instead of bit 31
 7. RRDB doesn't update the link register (Rd)
 8. SDAL/SDLL/SLAL/SLLL flags reflect exhausted counter, not actual 32-bit result
 9. CPSI/CPSD single-step: counter not decremented, V/Z wrong
10. TRT instructions don't load translated value into RH1
"""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import OPERAND_BASE, SRC_BUF, DST_BUF


# =========================================================================
# Issue 1: H flag never computed
# After ADDB with half-carry (low nibble carry), H flag should be set.
# =========================================================================

TESTS = [
    TestCase(
        name="addb_half_carry_set",
        mnemonic="ADDB",
        instruction="ADDB RH0, RL0",
        description="ADDB RH0, RL0: 0x09 + 0x08 = 0x11, H=1 (low nibble 9+8=17>15)",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug1_h_flag"],
        # ADDB RH0(0), RL0(8): 10000000_1000_0000 = 0x8080
        code=[0x8080],
        regs={0: 0x0908},  # RH0=0x09, RL0=0x08
        expected_regs={0: 0x1108},  # RH0=0x11, RL0=0x08 unchanged
        expected_fcw_set=["H"],
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="addb_half_carry_clear",
        mnemonic="ADDB",
        instruction="ADDB RH0, RL0",
        description="ADDB RH0, RL0: 0x01 + 0x02 = 0x03, H=0 (low nibble 1+2=3<16)",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug1_h_flag"],
        code=[0x8080],
        regs={0: 0x0102},  # RH0=0x01, RL0=0x02
        expected_regs={0: 0x0302},  # RH0=0x03
        expected_fcw_clear=["H", "C", "Z", "S"],
    ),
    TestCase(
        name="subb_half_borrow",
        mnemonic="SUBB",
        instruction="SUBB RH0, RL0",
        description="SUBB RH0, RL0: 0x10 - 0x01 = 0x0F, H=1 (borrow from bit 4)",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug1_h_flag"],
        # SUBB RH0(0), RL0(8): 10000010_1000_0000 = 0x8280
        code=[0x8280],
        regs={0: 0x1001},  # RH0=0x10, RL0=0x01
        expected_regs={0: 0x0F01},  # RH0=0x0F
        expected_fcw_set=["H"],
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # Issue 2: DAB doesn't update C/Z/S flags
    # DAB after ADDB should set C when BCD result > 99, Z when result = 0.
    # =========================================================================
    TestCase(
        name="dab_carry_zero",
        mnemonic="DAB",
        instruction="ADDB RH0, RL0; DAB RH0",
        description="ADDB 0x99+0x01=0x9A, DAB -> 0x00, C=1 Z=1 S=0",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug2_dab_flags"],
        # ADDB RH0, RL0 then DAB RH0
        # ADDB: 0x8080, DAB RH0: 10110000_0000_0000 = 0xB000
        code=[0x8080, 0xB000],
        regs={0: 0x9901},  # RH0=0x99, RL0=0x01
        expected_regs={0: 0x0001},  # RH0=0x00 after DAB, RL0 unchanged
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="dab_sign_flag",
        mnemonic="DAB",
        instruction="ADDB RH0, RL0; DAB RH0",
        description="ADDB 0x50+0x49=0x99, DAB -> 0x99, S=1 Z=0 C=0 V=1",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug2_dab_flags"],
        issues=["Z8001 sets V=1, Z8002 does not; DAB V flag behavior is undefined per databook"],
        code=[0x8080, 0xB000],
        regs={0: 0x5049},  # RH0=0x50, RL0=0x49
        expected_regs={0: 0x9949},  # RH0=0x99 (BCD 50+49=99)
        expected_fcw_set=["S", "V"],
        expected_fcw_clear=["C", "Z"],
    ),

    # =========================================================================
    # Issue 3: INC/DEC/NEG memory modes (IR/DA/X) skip flag updates
    # =========================================================================
    TestCase(
        name="inc_ir_zero_flag",
        mnemonic="INC",
        instruction="INC @R1, #1",
        description="INC @R1, #1: 0xFFFF + 1 = 0x0000, Z must be set",
        tags=["arithmetic", "word", "IR_mode", "flags", "bug3_mem_flags"],
        # INC @Rs, #n: 00101001_ssss_nnnn = 0x2900 | (rs << 4) | (n-1)
        code=[0x2910],  # INC @R1, #1
        regs={1: OPERAND_BASE},
        memory={OPERAND_BASE: 0xFFFF},
        expected_memory={OPERAND_BASE: 0x0000},
        expected_fcw_set=["Z"],
    ),
    TestCase(
        name="inc_ir_sign_flag",
        mnemonic="INC",
        instruction="INC @R1, #1",
        description="INC @R1, #1: 0x7FFF + 1 = 0x8000, S=1 V=1",
        tags=["arithmetic", "word", "IR_mode", "flags", "bug3_mem_flags"],
        code=[0x2910],
        regs={1: OPERAND_BASE},
        memory={OPERAND_BASE: 0x7FFF},
        expected_memory={OPERAND_BASE: 0x8000},
        expected_fcw_set=["S", "V"],
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="dec_ir_zero_flag",
        mnemonic="DEC",
        instruction="DEC @R1, #1",
        description="DEC @R1, #1: 0x0001 - 1 = 0x0000, Z must be set",
        tags=["arithmetic", "word", "IR_mode", "flags", "bug3_mem_flags"],
        # DEC @Rs, #n: 00101011_ssss_nnnn = 0x2B00 | (rs << 4) | (n-1)
        code=[0x2B10],  # DEC @R1, #1
        regs={1: OPERAND_BASE},
        memory={OPERAND_BASE: 0x0001},
        expected_memory={OPERAND_BASE: 0x0000},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="neg_ir_flags",
        mnemonic="NEG",
        instruction="NEG @R1",
        description="NEG @R1: 0 - 0x0001 = 0xFFFF, C=1 S=1",
        tags=["arithmetic", "word", "IR_mode", "flags", "bug3_mem_flags"],
        # NEG @Rs: 00001101_ssss_0010 = 0x0D00 | (rs << 4) | 0x02
        code=[0x0D12],  # NEG @R1
        regs={1: OPERAND_BASE},
        memory={OPERAND_BASE: 0x0001},
        expected_memory={OPERAND_BASE: 0xFFFF},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),
    TestCase(
        name="inc_da_zero_flag",
        mnemonic="INC",
        instruction="INC 0x0400, #1",
        description="INC 0x0400, #1: 0xFFFF + 1 = 0x0000, Z must be set",
        tags=["arithmetic", "word", "DA_mode", "flags", "bug3_mem_flags"],
        # INC addr, #n: [0x6900 | (n-1), addr]
        code=[0x6900, OPERAND_BASE],
        memory={OPERAND_BASE: 0xFFFF},
        expected_memory={OPERAND_BASE: 0x0000},
        expected_fcw_set=["Z"],
    ),
    TestCase(
        name="neg_da_flags",
        mnemonic="NEG",
        instruction="NEG 0x0400",
        description="NEG 0x0400: 0 - 0x0001 = 0xFFFF, C=1 S=1",
        tags=["arithmetic", "word", "DA_mode", "flags", "bug3_mem_flags"],
        # NEG addr: [0x4D02, addr]
        code=[0x4D02, OPERAND_BASE],
        memory={OPERAND_BASE: 0x0001},
        expected_memory={OPERAND_BASE: 0xFFFF},
        expected_fcw_set=["C", "S"],
        expected_fcw_clear=["Z", "V"],
    ),

    # =========================================================================
    # Issue 4: ADDL/SUBL 32-bit Z flag only checks high word
    # If high word is zero but low word is non-zero, Z must be clear.
    # =========================================================================
    TestCase(
        name="addl_z_flag_low_nonzero",
        mnemonic="ADDL",
        instruction="ADDL RR0, RR2",
        description="ADDL RR0, RR2: 0xFFFF0000+0x00010001=0x00000001, Z must be clear",
        tags=["arithmetic", "word", "R_mode", "flags", "bug4_long_z"],
        # ADDL RRd, RRs: 10010110_ssss_dddd = 0x9600 | (rs << 4) | rd
        code=[0x9620],  # ADDL RR0, RR2
        regs={0: 0xFFFF, 1: 0x0000, 2: 0x0001, 3: 0x0001},
        expected_regs={0: 0x0000, 1: 0x0001},
        expected_fcw_set=["C"],    # carry from 0xFFFF + 0x0001
        expected_fcw_clear=["Z"],  # low word = 0x0001, not zero
    ),
    TestCase(
        name="addl_z_flag_true_zero",
        mnemonic="ADDL",
        instruction="ADDL RR0, RR2",
        description="ADDL RR0, RR2: 0xFFFFFFFF+0x00000001=0x00000000, Z must be set",
        tags=["arithmetic", "word", "R_mode", "flags", "bug4_long_z"],
        code=[0x9620],
        regs={0: 0xFFFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        expected_regs={0: 0x0000, 1: 0x0000},
        expected_fcw_set=["C", "Z"],
    ),
    TestCase(
        name="subl_z_flag_low_nonzero",
        mnemonic="SUBL",
        instruction="SUBL RR0, RR2",
        description="SUBL RR0, RR2: 0x00010005-0x00010001=0x00000004, Z must be clear",
        tags=["arithmetic", "word", "R_mode", "flags", "bug4_long_z"],
        # SUBL RRd, RRs: 10010010_ssss_dddd
        code=[0x9220],  # SUBL RR0, RR2
        regs={0: 0x0001, 1: 0x0005, 2: 0x0001, 3: 0x0001},
        expected_regs={0: 0x0000, 1: 0x0004},
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # Issue 5: CPL 32-bit Z flag only checks high word
    # =========================================================================
    TestCase(
        name="cpl_z_flag_low_differs",
        mnemonic="CPL",
        instruction="CPL RR0, RR2",
        description="CPL RR0, RR2: 0x00001234 vs 0x00005678, Z must be clear",
        tags=["compare", "word", "R_mode", "flags", "bug5_cpl_z"],
        # CPL RRd, RRs: 10010000_ssss_dddd
        code=[0x9020],  # CPL RR0, RR2
        regs={0: 0x0000, 1: 0x1234, 2: 0x0000, 3: 0x5678},
        # CPL doesn't modify registers
        expected_regs={0: 0x0000, 1: 0x1234, 2: 0x0000, 3: 0x5678},
        expected_fcw_clear=["Z"],  # values differ in low word
        expected_fcw_set=["C", "S"],  # 0x1234 < 0x5678 → borrow, result negative
    ),
    TestCase(
        name="cpl_z_flag_equal",
        mnemonic="CPL",
        instruction="CPL RR0, RR2",
        description="CPL RR0, RR2: 0x12345678 vs 0x12345678, Z must be set",
        tags=["compare", "word", "R_mode", "flags", "bug5_cpl_z"],
        code=[0x9020],
        regs={0: 0x1234, 1: 0x5678, 2: 0x1234, 3: 0x5678},
        expected_regs={0: 0x1234, 1: 0x5678, 2: 0x1234, 3: 0x5678},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["C", "S"],
    ),

    # =========================================================================
    # Issue 6: TESTL S flag computed from high|low instead of bit 31
    # S should be bit 31 (bit 15 of high word), not sign of (high|low).
    # =========================================================================
    TestCase(
        name="testl_s_flag_high_zero",
        mnemonic="TESTL",
        instruction="TESTL RR0",
        description="TESTL RR0: 0x00008000 - S=0 (bit31=0), Z=0",
        tags=["compare", "word", "R_mode", "flags", "bug6_testl_s"],
        # TESTL RRd: 10011100_dddd_1000
        code=[0x9C08],  # TESTL RR0
        regs={0: 0x0000, 1: 0x8000},
        expected_fcw_clear=["S", "Z"],  # bit31=0, non-zero value
    ),
    TestCase(
        name="testl_s_flag_negative",
        mnemonic="TESTL",
        instruction="TESTL RR0",
        description="TESTL RR0: 0x80000000 - S=1 (bit31=1), Z=0",
        tags=["compare", "word", "R_mode", "flags", "bug6_testl_s"],
        code=[0x9C08],
        regs={0: 0x8000, 1: 0x0000},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z"],
    ),

    # =========================================================================
    # Issue 7: RRDB doesn't update the link register (Rd)
    # RRDB Rbl, Rbs: before [X|A][B|C], after [X|C][A|B]
    # =========================================================================
    TestCase(
        name="rrdb_link_update",
        mnemonic="RRDB",
        instruction="RRDB RH0, RL0",
        description="RRDB RH0, RL0: [A5][B3] -> [A3][5B], link reg must update",
        tags=["shift", "byte", "R_mode", "bug7_rrdb"],
        # RRDB Rbl, Rbs: 10111100_Rbss_Rbdd
        # Rbl=RH0(0), Rbs=RL0(8): 0xBC80
        code=[0xBC80],
        regs={0: 0xA5B3},  # RH0=0xA5, RL0=0xB3
        expected_regs={0: 0xA35B},  # RH0=[A|3], RL0=[5|B]
    ),
    TestCase(
        name="rrdb_link_update_zeros",
        mnemonic="RRDB",
        instruction="RRDB RH0, RL0",
        description="RRDB RH0, RL0: [00][12] -> [02][01]",
        tags=["shift", "byte", "R_mode", "bug7_rrdb"],
        code=[0xBC80],
        regs={0: 0x0012},  # RH0=0x00, RL0=0x12
        expected_regs={0: 0x0201},  # RH0=[0|2], RL0=[0|1]
    ),

    # =========================================================================
    # Issue 8: SDAL/SDLL flags reflect exhausted counter, not actual result
    # After a 32-bit shift, Z/S/C should reflect the 32-bit result.
    # =========================================================================
    TestCase(
        name="sdll_left_z_clear",
        mnemonic="SDLL",
        instruction="SDLL RR0, R2",
        description="SDLL RR0, R2: 0x00000001 << 1 = 0x00000002, Z must be clear",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SDLL RR0, R2: B307 0200
        code=[0xB307, 0x0200],
        regs={0: 0x0000, 1: 0x0001, 2: 1},
        expected_regs={0: 0x0000, 1: 0x0002},
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="sdll_left_carry",
        mnemonic="SDLL",
        instruction="SDLL RR0, R2",
        description="SDLL RR0, R2: 0x80000000 << 1 = 0x00000000, C=1 Z=1",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SDLL RR0, R2: B307 0200
        code=[0xB307, 0x0200],
        regs={0: 0x8000, 1: 0x0000, 2: 1},
        expected_regs={0: 0x0000, 1: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="sdal_left_sign",
        mnemonic="SDAL",
        instruction="SDAL RR0, R2",
        description="SDAL RR0, R2: 0x40000000 << 1 = 0x80000000, S=1",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SDAL RR0, R2: B30F 0200
        code=[0xB30F, 0x0200],
        regs={0: 0x4000, 1: 0x0000, 2: 1},
        expected_regs={0: 0x8000, 1: 0x0000},
        expected_fcw_set=["S"],
        expected_fcw_clear=["Z"],
    ),
    TestCase(
        name="sdll_right_nonzero",
        mnemonic="SDLL",
        instruction="SDLL RR0, R2",
        description="SDLL RR0, R2: 0x00020000 >> 1 = 0x00010000, Z must be clear",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SDLL RR0, R2: B307 0200 (R2=-1 for right shift by 1)
        code=[0xB307, 0x0200],
        regs={0: 0x0002, 1: 0x0000, 2: 0xFFFF},  # R2=-1 (shift right by 1)
        expected_regs={0: 0x0001, 1: 0x0000},
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # Issue 9: CPSI/CPSD single-step: counter not decremented, V/Z wrong
    # CPSI/CPSD compare @Rd with @Rs (memory-to-memory), unlike CPI which
    # compares register Rd with @Rs.
    # =========================================================================
    TestCase(
        name="cpsi_counter_decrement",
        mnemonic="CPSI",
        instruction="CPSI @R3, @R1, R0, always",
        description="CPSI @R3, @R1, R0, always: match, counter 3->2",
        tags=["block", "word", "flags", "bug9_cpsi"],
        # CPSI: 10111011_ssss_0010 + 0000_rrrr_dddd_cccc
        # Rs=R1, Rr=R0, Rd=R3, cc=8 (always)
        code=[0xBB12, 0x0038],
        regs={0: 3, 1: SRC_BUF, 3: DST_BUF},
        memory={SRC_BUF: 0x1234, DST_BUF: 0x1234},
        expected_regs={0: 2, 1: SRC_BUF + 2, 3: DST_BUF + 2},
        expected_fcw_set=["Z"],    # condition met (always)
        expected_fcw_clear=["V"],  # counter 3->2, not exhausted
    ),
    TestCase(
        name="cpsi_counter_exhausted",
        mnemonic="CPSI",
        instruction="CPSI @R3, @R1, R0, always",
        description="CPSI @R3, @R1, R0, always: counter 1->0, V=1",
        tags=["block", "word", "flags", "bug9_cpsi"],
        code=[0xBB12, 0x0038],
        regs={0: 1, 1: SRC_BUF, 3: DST_BUF},
        memory={SRC_BUF: 0xAAAA, DST_BUF: 0xAAAA},
        expected_regs={0: 0, 1: SRC_BUF + 2, 3: DST_BUF + 2},
        expected_fcw_set=["Z", "V"],  # Z=condition met, V=counter exhausted
    ),
    TestCase(
        name="cpsd_counter_decrement",
        mnemonic="CPSD",
        instruction="CPSD @R3, @R1, R0, always",
        description="CPSD @R3, @R1, R0, always: match, counter 3->2, ptrs decremented",
        tags=["block", "word", "flags", "bug9_cpsi"],
        # CPSD: 10111011_ssss_1010
        code=[0xBB1A, 0x0038],
        regs={0: 3, 1: SRC_BUF + 4, 3: DST_BUF + 4},
        memory={SRC_BUF + 4: 0x5678, DST_BUF + 4: 0x5678},
        expected_regs={0: 2, 1: SRC_BUF + 2, 3: DST_BUF + 2},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["V"],
    ),

    # =========================================================================
    # Issue 10: TRT instructions don't load translated value into RH1
    # TRTIB reads source byte, uses it as index into translation table,
    # stores the translated byte into RH1 (high byte of R1).
    # =========================================================================
    TestCase(
        name="trtib_rh1_load",
        mnemonic="TRTIB",
        instruction="TRTIB @R3, @R4, R2",
        description="TRTIB: source byte 0x02, table[2]=0xAB -> RH1 must be 0xAB",
        tags=["block", "byte", "flags", "bug10_trt"],
        issues=["Z8002 sets S flag, Z8001 does not"],
        # TRTIB @Rs, @Rd, Rr: 10111000_ssss_0010 + 0000_rrrr_dddd_0000
        # Rs=R3 (source ptr), Rd=R4 (table base), Rr=R2 (counter)
        code=[0xB832, 0x0240],
        regs={1: 0x0000, 2: 3, 3: SRC_BUF, 4: OPERAND_BASE},
        expected_fcw_clear=["S"],
        memory={
            SRC_BUF: 0x0200,            # source byte = 0x02 (high byte at even addr)
            OPERAND_BASE + 2: 0xAB00,   # table[2] = 0xAB (high byte at even addr)
        },
        expected_regs={
            1: 0xAB00,     # RH1 = 0xAB (translated byte), RL1 = 0x00
            2: 2,          # counter decremented
            3: SRC_BUF + 1,  # source ptr incremented by 1 (byte)
        },
    ),

    # =========================================================================
    # Issue 1 (continued): ADCB/SBCB H flag
    # =========================================================================
    TestCase(
        name="adcb_half_carry",
        mnemonic="ADCB",
        instruction="ADCB RH0, RL0",
        description="ADCB RH0, RL0 with C=1: 0x08 + 0x08 + 1 = 0x11, H=1",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug1_h_flag"],
        # ADCB RH0(0), RL0(8): 10110100_1000_0000 = 0xB480
        code=[0xB480],
        fcw=fcw_with_flags(C=1),
        regs={0: 0x0808},  # RH0=0x08, RL0=0x08
        expected_regs={0: 0x1108},  # 0x08+0x08+1=0x11
        expected_fcw_set=["H"],
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="sbcb_half_borrow",
        mnemonic="SBCB",
        instruction="SBCB RH0, RL0",
        description="SBCB RH0, RL0 with C=1: 0x10 - 0x02 - 1 = 0x0D, H=1",
        tags=["arithmetic", "byte", "R_mode", "flags", "bug1_h_flag"],
        # SBCB RH0(0), RL0(8): 10110110_1000_0000 = 0xB680
        code=[0xB680],
        fcw=fcw_with_flags(C=1),
        regs={0: 0x1002},  # RH0=0x10, RL0=0x02
        expected_regs={0: 0x0D02},  # 0x10-0x02-1=0x0D
        expected_fcw_set=["H"],
        expected_fcw_clear=["C", "Z", "S"],
    ),

    # =========================================================================
    # Issue 7 (continued): RLDB link register + Z flag, RRDB Z flag
    # =========================================================================
    TestCase(
        name="rldb_link_update",
        mnemonic="RLDB",
        instruction="RLDB RH0, RL0",
        description="RLDB RH0, RL0: [A5][B3] -> [AB][35], link reg must update",
        tags=["shift", "byte", "R_mode", "bug7_rrdb"],
        # RLDB Rbl, Rbs: 10111110_Rbss_Rbdd = 0xBE80
        code=[0xBE80],
        regs={0: 0xA5B3},  # RH0=0xA5, RL0=0xB3
        expected_regs={0: 0xAB35},  # RH0=[A|B], RL0=[3|5]
    ),
    TestCase(
        name="rldb_z_flag_set",
        mnemonic="RLDB",
        instruction="RLDB RH0, RL0",
        description="RLDB RH0, RL0: [0A][0B] -> [00][BA], Z=1 S=0 (link=0x00)",
        tags=["shift", "byte", "R_mode", "flags", "bug7_rrdb"],
        # Z/S flags are from link register (Rbl=RH0), not source
        # After: RH0=[old_high|old_src_high]=[0|0]=0x00, RL0=[B|A]=0xBA
        code=[0xBE80],
        regs={0: 0x0A0B},  # RH0=0x0A, RL0=0x0B
        expected_regs={0: 0x00BA},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="rrdb_z_flag_set",
        mnemonic="RRDB",
        instruction="RRDB RH0, RL0",
        description="RRDB RH0, RL0: [05][B0] -> [00][5B], Z=1 S=0 (link=0x00)",
        tags=["shift", "byte", "R_mode", "flags", "bug7_rrdb"],
        # After: RH0=[old_high|old_src_low]=[0|0]=0x00, RL0=[5|B]=0x5B
        code=[0xBC80],
        regs={0: 0x05B0},  # RH0=0x05, RL0=0xB0
        expected_regs={0: 0x005B},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["S"],
    ),

    # =========================================================================
    # Issue 8 (continued): SLLL/SLAL 32-bit shift flags
    # These are static (shift-by-1) long shift instructions.
    # =========================================================================
    TestCase(
        name="slll_cross_word",
        mnemonic="SLLL",
        instruction="SLLL RR0, #1",
        description="SLLL RR0: 0x00008000 << 1 = 0x00010000, bit crosses word boundary",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SLLL RRd, #n: B305 followed by shift count word
        code=[0xB305, 0x0001],
        regs={0: 0x0000, 1: 0x8000},
        expected_regs={0: 0x0001, 1: 0x0000},
        expected_fcw_clear=["C", "Z", "S"],
    ),
    TestCase(
        name="slll_carry_zero",
        mnemonic="SLLL",
        instruction="SLLL RR0, #1",
        description="SLLL RR0: 0x80000000 << 1 = 0x00000000, C=1 Z=1",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        code=[0xB305, 0x0001],
        regs={0: 0x8000, 1: 0x0000},
        expected_regs={0: 0x0000, 1: 0x0000},
        expected_fcw_set=["C", "Z"],
        expected_fcw_clear=["S"],
    ),
    TestCase(
        name="slal_sign_overflow",
        mnemonic="SLAL",
        instruction="SLAL RR0, #1",
        description="SLAL RR0: 0x40000000 << 1 = 0x80000000, S=1 V=1",
        tags=["shift", "word", "R_mode", "flags", "bug8_long_shift_flags"],
        # SLAL RRd, #n: B30D followed by shift count word
        code=[0xB30D, 0x0001],
        regs={0: 0x4000, 1: 0x0000},
        expected_regs={0: 0x8000, 1: 0x0000},
        expected_fcw_set=["S", "V"],
        expected_fcw_clear=["C", "Z"],
    ),

    # =========================================================================
    # Issue 9 (continued): CPSIR/CPSDR repeat variants
    # CPSIR/CPSDR repeat until condition met or counter exhausted.
    # V=0 on match, V=1 on counter exhaustion.
    # =========================================================================
    TestCase(
        name="cpsir_match_found",
        mnemonic="CPSIR",
        instruction="CPSIR @R3, @R1, R0, eq",
        description="CPSIR @R3, @R1, R0, eq: match on 1st element, V=0",
        tags=["block", "word", "flags", "bug9_cpsi"],
        # CPSIR: 10111011_ssss_0110 + 0000_rrrr_dddd_cccc
        # Rs=R1, Rr=R0, Rd=R3, cc=6 (Z/equal)
        code=[0xBB16, 0x0036],
        regs={0: 3, 1: SRC_BUF, 3: DST_BUF},
        memory={SRC_BUF: 0x1234, DST_BUF: 0x1234},
        expected_regs={0: 2, 1: SRC_BUF + 2, 3: DST_BUF + 2},
        expected_fcw_set=["Z"],     # match found
        expected_fcw_clear=["V"],   # not exhausted
    ),
    TestCase(
        name="cpsir_exhausted",
        mnemonic="CPSIR",
        instruction="CPSIR @R3, @R1, R0, eq",
        description="CPSIR @R3, @R1, R0, eq: no match, counter 2->0, V=1",
        tags=["block", "word", "flags", "bug9_cpsi"],
        issues=["Z8002 has 2 extra bus cycles per repeat iteration (opcode re-fetch); Z8001 loops internally"],
        code=[0xBB16, 0x0036],
        regs={0: 2, 1: SRC_BUF, 3: DST_BUF},
        memory={
            SRC_BUF: 0x1111, SRC_BUF + 2: 0x3333,
            DST_BUF: 0x2222, DST_BUF + 2: 0x4444,
        },
        expected_regs={0: 0, 1: SRC_BUF + 4, 3: DST_BUF + 4},
        expected_fcw_clear=["Z"],   # last comparison was not equal
        expected_fcw_set=["V"],     # counter exhausted
    ),
    TestCase(
        name="cpsdr_match_found",
        mnemonic="CPSDR",
        instruction="CPSDR @R3, @R1, R0, eq",
        description="CPSDR @R3, @R1, R0, eq: match on 1st element, V=0, ptrs decremented",
        tags=["block", "word", "flags", "bug9_cpsi"],
        # CPSDR: 10111011_ssss_1110
        code=[0xBB1E, 0x0036],
        regs={0: 3, 1: SRC_BUF + 4, 3: DST_BUF + 4},
        memory={SRC_BUF + 4: 0x5678, DST_BUF + 4: 0x5678},
        expected_regs={0: 2, 1: SRC_BUF + 2, 3: DST_BUF + 2},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["V"],
    ),
]
