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
        description="CPI R0, @R1, R2, T: match found (Z=1)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=8),
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1234},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_set=["Z"],
    ),
    TestCase(
        name="cpi_no_match",
        mnemonic="CPI",
        description="CPI R0, @R1, R2, T: no match (Z=0)",
        tags=["block", "word", "flags"],
        code=_cpi(rs=1, rr=2, rd=0, cc=8),
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x5678},
        expected_regs={1: SRC_BUF + 2, 2: 2},
        expected_fcw_clear=["Z"],
    ),
]
