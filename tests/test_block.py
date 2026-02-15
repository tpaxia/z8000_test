"""Block operation tests: LDI, LDIR, LDD, LDDR, CPI, CPIR."""

from .defs import TestCase
from .flags import FCW_SYS
from .helpers import SRC_BUF, DST_BUF

# Encodings from z8002_instructions.csv:
# LDI  @Rd, @Rs, r:  10111011_Rsnz_0001 + 0000_Rrrr_Rdnz_1000
# LDIR @Rd, @Rs, r:  10111011_Rsnz_0001 + 0000_Rrrr_Rdnz_0000
# LDD  @Rd, @Rs, r:  10111011_Rsnz_1001 + 0000_Rrrr_Rdnz_1000
# LDDR @Rd, @Rs, r:  10111011_Rsnz_1001 + 0000_Rrrr_Rdnz_0000
# CPI  Rd, @Rs, r, cc: 10111011_Rsnz_0000 + 0000_Rrrr_Rddd_cccc
# CPIR Rd, @Rs, r, cc: 10111011_Rsnz_0100 + 0000_Rrrr_Rddd_cccc

def _ldi(rs, rr, rd):
    """LDI @Rd, @Rs, Rr"""
    return [0xBB01 | (rs << 4), (rr << 8) | (rd << 4) | 0x08]

def _ldir(rs, rr, rd):
    """LDIR @Rd, @Rs, Rr"""
    return [0xBB01 | (rs << 4), (rr << 8) | (rd << 4) | 0x00]

def _ldd(rs, rr, rd):
    """LDD @Rd, @Rs, Rr"""
    return [0xBB09 | (rs << 4), (rr << 8) | (rd << 4) | 0x08]

def _lddr(rs, rr, rd):
    """LDDR @Rd, @Rs, Rr"""
    return [0xBB09 | (rs << 4), (rr << 8) | (rd << 4) | 0x00]

def _cpi(rs, rr, rd, cc=8):
    """CPI Rd, @Rs, Rr, cc (cc=8=always)"""
    return [0xBB00 | (rs << 4), (rr << 8) | (rd << 4) | cc]

def _cpir(rs, rr, rd, cc=8):
    """CPIR Rd, @Rs, Rr, cc"""
    return [0xBB04 | (rs << 4), (rr << 8) | (rd << 4) | cc]


TESTS = [
    # =========================================================================
    # LDI @Rd, @Rs, Rr - load and increment (single step)
    # Rs=source ptr, Rd=dest ptr, Rr=counter (decremented)
    # =========================================================================
    TestCase(
        name="ldi_basic",
        mnemonic="LDI",
        instruction="LDI @R3, @R1, R2",
        description="LDI @R3, @R1, R2: copy one word, counter=3",
        tags=["block", "word"],
        code=_ldi(rs=1, rr=2, rd=3),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={SRC_BUF: 0xAAAA},
        expected_regs={1: SRC_BUF + 2, 2: 2, 3: DST_BUF + 2},
        expected_memory={DST_BUF: 0xAAAA},
    ),

    # =========================================================================
    # LDIR @Rd, @Rs, Rr - load, increment, repeat until counter=0
    # =========================================================================
    TestCase(
        name="ldir_three_words",
        mnemonic="LDIR",
        instruction="LDIR @R3, @R1, R2",
        description="LDIR @R3, @R1, R2: copy 3 words",
        tags=["block", "word"],
        code=_ldir(rs=1, rr=2, rd=3),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={
            SRC_BUF: 0x1111,
            SRC_BUF + 2: 0x2222,
            SRC_BUF + 4: 0x3333,
        },
        expected_regs={1: SRC_BUF + 6, 2: 0, 3: DST_BUF + 6},
        expected_memory={
            DST_BUF: 0x1111,
            DST_BUF + 2: 0x2222,
            DST_BUF + 4: 0x3333,
        },
    ),

    # =========================================================================
    # LDD @Rd, @Rs, Rr - load and decrement (single step)
    # =========================================================================
    TestCase(
        name="ldd_basic",
        mnemonic="LDD",
        instruction="LDD @R3, @R1, R2",
        description="LDD @R3, @R1, R2: copy one word, decrement ptrs",
        tags=["block", "word"],
        code=_ldd(rs=1, rr=2, rd=3),
        regs={1: SRC_BUF + 4, 2: 3, 3: DST_BUF + 4},
        memory={SRC_BUF + 4: 0xBBBB},
        expected_regs={1: SRC_BUF + 2, 2: 2, 3: DST_BUF + 2},
        expected_memory={DST_BUF + 4: 0xBBBB},
    ),

    # =========================================================================
    # CPI Rd, @Rs, Rr, cc - compare and increment
    # =========================================================================
    TestCase(
        name="cpi_match",
        mnemonic="CPI",
        instruction="CPI R0, @R1, R2, EQ",
        description="CPI R0, @R1, R2, EQ: match found (Z=1)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=6),  # cc=6 (EQ): Z set when comparison is equal
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1234},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_set=["Z"],
        expected_fcw_clear=["V"],  # V=0: counter 3->2, non-zero
    ),
    TestCase(
        name="cpi_no_match",
        mnemonic="CPI",
        instruction="CPI R0, @R1, R2, EQ",
        description="CPI R0, @R1, R2, EQ: no match (Z=0)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=6),  # cc=6 (EQ): Z clear when comparison is not equal
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x5678},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_clear=["Z", "V"],  # Z=0: no match; V=0: counter 3->2, non-zero
    ),
    TestCase(
        name="cpi_counter_zero",
        mnemonic="CPI",
        instruction="CPI R0, @R1, R2, EQ",
        description="CPI R0, @R1, R2, EQ: match with counter=1, V=1 after decrement",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=6),
        regs={0: 0x1234, 1: SRC_BUF, 2: 1},
        memory={SRC_BUF: 0x1234},
        expected_regs={0: 0x1234, 1: SRC_BUF + 2, 2: 0},
        expected_fcw_set=["Z", "V"],  # Z=1: match; V=1: counter decremented to 0
    ),
    TestCase(
        name="cpi_ne_not_equal",
        mnemonic="CPI",
        instruction="CPI R0, @R1, R2, NE",
        description="CPI R0, @R1, R2, NE: values differ, NE condition met (Z=1)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=14),  # cc=14 (NE): Z set when comparison is not equal
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x5678},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_set=["Z"],  # Z=1: NE condition met (values differ)
        expected_fcw_clear=["V"],
    ),
    TestCase(
        name="cpi_ne_equal",
        mnemonic="CPI",
        instruction="CPI R0, @R1, R2, NE",
        description="CPI R0, @R1, R2, NE: values equal, NE condition not met (Z=0)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=14),  # cc=14 (NE): Z clear when comparison is equal
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1234},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_clear=["Z", "V"],  # Z=0: NE condition not met (values are equal)
    ),

    # =========================================================================
    # CPIR Rd, @Rs, Rr, cc - compare, increment, repeat
    # Repeats until condition met (Z=1) or counter exhausted (V=1)
    # =========================================================================
    TestCase(
        name="cpir_match_mid",
        mnemonic="CPIR",
        instruction="CPIR R0, @R1, R2, EQ",
        description="CPIR R0, @R1, R2, EQ: find match at 2nd element",
        tags=["block", "word", "flags"],
        code=_cpir(rs=1, rr=2, rd=0, cc=6),
        regs={0: 0xAAAA, 1: SRC_BUF, 2: 4},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0xAAAA},
        expected_regs={0: 0xAAAA, 1: SRC_BUF + 4, 2: 2},
        expected_fcw_set=["Z"],  # Z=1: match found
        expected_fcw_clear=["V"],  # V=0: counter=2, not exhausted
    ),
    TestCase(
        name="cpir_no_match",
        mnemonic="CPIR",
        instruction="CPIR R0, @R1, R2, EQ",
        description="CPIR R0, @R1, R2, EQ: no match, counter exhausted",
        tags=["block", "word", "flags"],
        code=_cpir(rs=1, rr=2, rd=0, cc=6),
        regs={0: 0xFFFF, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
        expected_regs={0: 0xFFFF, 1: SRC_BUF + 6, 2: 0},
        expected_fcw_clear=["Z"],  # Z=0: no match found
        expected_fcw_set=["V"],  # V=1: counter exhausted
    ),
    TestCase(
        name="cpir_match_first",
        mnemonic="CPIR",
        instruction="CPIR R0, @R1, R2, EQ",
        description="CPIR R0, @R1, R2, EQ: match at first element",
        tags=["block", "word", "flags"],
        code=_cpir(rs=1, rr=2, rd=0, cc=6),
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1234, SRC_BUF + 2: 0x5678},
        expected_regs={0: 0x1234, 1: SRC_BUF + 2, 2: 2},
        expected_fcw_set=["Z"],  # Z=1: match found immediately
        expected_fcw_clear=["V"],  # V=0: counter=2
    ),
]
