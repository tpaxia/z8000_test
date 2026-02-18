"""Systematic test generator for Z8000 instruction validation.

Generates TestCase objects WITHOUT expected values. Run against a reference
CPU (Z8001) to capture golden results, then compare against the DUT (Z8002).

Usage:
    from tests.gen_systematic import generate_all_tests
    tests = generate_all_tests()  # ~850 TestCase objects
"""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import (
    CODE_BASE, OPERAND_BASE, SRC_BUF, DST_BUF, STACK_BASE,
    preload_buffer,
)

# ============================================================================
# Value pair tables
# ============================================================================

# Word ALU: (suffix, operand_a, operand_b)
_WORD_VALS = [
    ('zero', 0x0000, 0x0000),
    ('normal', 0x1234, 0x5678),
    ('carry', 0xFFFF, 0x0001),
    ('pos_ovf', 0x7FFF, 0x0001),
    ('neg_ovf', 0x8000, 0x8000),
    ('carry_ovf', 0xFFFF, 0xFFFF),
    ('allones', 0xFFFF, 0x0000),
]

# Byte ALU: (suffix, operand_a, operand_b)
_BYTE_VALS = [
    ('zero', 0x00, 0x00),
    ('normal', 0x12, 0x34),
    ('carry', 0xFF, 0x01),
    ('pos_ovf', 0x7F, 0x01),
    ('neg_ovf', 0x80, 0x80),
    ('carry_ovf', 0xFF, 0xFF),
    ('allones', 0xFF, 0x00),
]

# Long ALU: (suffix, operand_a_32bit, operand_b_32bit)
_LONG_VALS = [
    ('zero', 0x00000000, 0x00000000),
    ('normal', 0x12345678, 0x9ABCDEF0),
    ('carry', 0xFFFFFFFF, 0x00000001),
    ('pos_ovf', 0x7FFFFFFF, 0x00000001),
    ('max', 0xFFFFFFFF, 0xFFFFFFFF),
]

# Carry-chain: (suffix, operand_a, operand_b)
_CARRY_WORD_VALS = [
    ('zero', 0x0000, 0x0000),
    ('normal', 0x1234, 0x5678),
    ('carry', 0xFFFF, 0x0001),
    ('max', 0xFFFF, 0xFFFF),
    ('half', 0x000F, 0x0001),
]

_CARRY_BYTE_VALS = [
    ('zero', 0x00, 0x00),
    ('normal', 0x12, 0x34),
    ('carry', 0xFF, 0x01),
    ('max', 0xFF, 0xFF),
    ('half', 0x0F, 0x01),
]

# Unary values: (suffix, value)
_UNARY_W = [('zero', 0x0000), ('one', 0x0001),
            ('pos_max', 0x7FFF), ('neg_min', 0x8000)]
_UNARY_B = [('zero', 0x00), ('one', 0x01),
            ('pos_max', 0x7F), ('neg_min', 0x80)]
_UNARY_L = [('zero', 0x00000000), ('one', 0x00000001),
            ('pos_max', 0x7FFFFFFF), ('neg_min', 0x80000000)]

# Shift values
_SHIFT_W = [('one', 0x0001), ('msb', 0x8000), ('pattern', 0xA5A5)]
_SHIFT_B = [('one', 0x01), ('msb', 0x80), ('pattern', 0xA5)]
_SHIFT_L = [('one', 0x00000001), ('msb', 0x80000000)]

# Condition codes
_CC_NAMES = {
    0: 'F', 1: 'LT', 2: 'LE', 3: 'ULE', 4: 'OV', 5: 'MI',
    6: 'EQ', 7: 'C', 8: 'T', 9: 'GE', 10: 'GT', 11: 'UGT',
    12: 'NOV', 13: 'PL', 14: 'NE', 15: 'NC',
}

# FCW values that make each condition code true/false
# (fcw_for_true, fcw_for_false)
_CC_FCW = {
    0:  (FCW_SYS, FCW_SYS),                                          # F: never
    1:  (fcw_with_flags(S=1), FCW_SYS),                              # LT: S^V
    2:  (fcw_with_flags(Z=1), FCW_SYS),                              # LE: Z|(S^V)
    3:  (fcw_with_flags(C=1), fcw_with_flags(S=1)),                  # ULE: C|Z
    4:  (fcw_with_flags(V=1), FCW_SYS),                              # OV
    5:  (fcw_with_flags(S=1), FCW_SYS),                              # MI
    6:  (fcw_with_flags(Z=1), FCW_SYS),                              # EQ
    7:  (fcw_with_flags(C=1), FCW_SYS),                              # C
    8:  (FCW_SYS, FCW_SYS),                                          # T: always
    9:  (FCW_SYS, fcw_with_flags(S=1)),                              # GE: !(S^V)
    10: (FCW_SYS, fcw_with_flags(Z=1)),                              # GT
    11: (FCW_SYS, fcw_with_flags(C=1)),                              # UGT
    12: (FCW_SYS, fcw_with_flags(V=1)),                              # NOV
    13: (FCW_SYS, fcw_with_flags(S=1)),                              # PL
    14: (FCW_SYS, fcw_with_flags(Z=1)),                              # NE
    15: (FCW_SYS, fcw_with_flags(C=1)),                              # NC
}


# ============================================================================
# Encoding helpers
# ============================================================================

def _enc_rr(base, rd, rs):
    """Register-register: base | (rs << 4) | rd."""
    return [base | (rs << 4) | rd]


def _enc_im_w(base, rd, imm):
    """Word immediate: base | rd, imm16."""
    return [base | rd, imm & 0xFFFF]


def _enc_im_b(base, rbd, imm):
    """Byte immediate: base | rbd, (imm8 << 8)."""
    return [base | rbd, (imm & 0xFF) << 8]


def _enc_ir(base, rd, rs):
    """Indirect register: base | (rs << 4) | rd  (rs != 0)."""
    return [base | (rs << 4) | rd]


def _enc_da(base, rd, addr):
    """Direct address: base | rd, addr16."""
    return [base | rd, addr & 0xFFFF]


def _long_regs(rrd, val32):
    """Set up register pair for a 32-bit value. RRd = Rd:Rd+1."""
    return {rrd: (val32 >> 16) & 0xFFFF, rrd + 1: val32 & 0xFFFF}


def _quad_regs(rqd, val_hi32, val_lo32):
    """Set up register quad for 64-bit value. RQd = Rd:Rd+1:Rd+2:Rd+3."""
    return {
        rqd: (val_hi32 >> 16) & 0xFFFF,
        rqd + 1: val_hi32 & 0xFFFF,
        rqd + 2: (val_lo32 >> 16) & 0xFFFF,
        rqd + 3: val_lo32 & 0xFFFF,
    }


def _tc(name, mnemonic, desc, tags, code, regs=None, fcw=FCW_SYS,
        memory=None):
    """Shorthand TestCase constructor for systematic tests."""
    return TestCase(
        name=name,
        mnemonic=mnemonic,
        description=desc,
        tags=["systematic"] + tags,
        code=code,
        regs=regs or {},
        fcw=fcw,
        memory=memory or {},
    )


# ============================================================================
# Category 1: Word ALU register-register (42 tests)
# ============================================================================

def generate_word_alu_tests():
    """ADD, SUB, AND, OR, XOR, CP in R,R mode x 7 value pairs."""
    OPS = [
        ('ADD', 0x8100), ('SUB', 0x8300), ('AND', 0x8700),
        ('OR', 0x8500), ('XOR', 0x8900), ('CP', 0x8B00),
    ]
    tests = []
    for mnem, base in OPS:
        for sfx, a, b in _WORD_VALS:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_r_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} R0, R1: 0x{a:04X}, 0x{b:04X}",
                tags=["word_alu", "R_mode"],
                code=_enc_rr(base, 0, 1),
                regs={0: a, 1: b},
            ))
    return tests


# ============================================================================
# Category 2: Word ALU IM/IR/DA modes (36 tests)
# ============================================================================

def generate_word_alu_mode_tests():
    """ADD, SUB, AND, OR, XOR, CP in IM, IR, DA modes x 2 values."""
    IM_OPS = [
        ('ADD', 0x0100), ('SUB', 0x0300), ('AND', 0x0700),
        ('OR', 0x0500), ('XOR', 0x0900), ('CP', 0x0B00),
    ]
    DA_OPS = [
        ('ADD', 0x4100), ('SUB', 0x4300), ('AND', 0x4700),
        ('OR', 0x4500), ('XOR', 0x4900), ('CP', 0x4B00),
    ]
    VALS = [('normal', 0x1234, 0x5678), ('carry', 0xFFFF, 0x0001)]
    tests = []

    for mnem, base in IM_OPS:
        for sfx, a, b in VALS:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_im_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} R0, #0x{b:04X}: R0=0x{a:04X}",
                tags=["word_alu", "IM_mode"],
                code=_enc_im_w(base, 0, b),
                regs={0: a},
            ))

    for mnem, base in IM_OPS:  # IR uses same upper byte as IM
        for sfx, a, b in VALS:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_ir_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} R0, @R2: R0=0x{a:04X}, [R2]=0x{b:04X}",
                tags=["word_alu", "IR_mode"],
                code=_enc_ir(base, 0, 2),
                regs={0: a, 2: OPERAND_BASE},
                memory={OPERAND_BASE: b},
            ))

    for mnem, base in DA_OPS:
        for sfx, a, b in VALS:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_da_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} R0, 0x{OPERAND_BASE:04X}: R0=0x{a:04X}, [DA]=0x{b:04X}",
                tags=["word_alu", "DA_mode"],
                code=_enc_da(base, 0, OPERAND_BASE),
                regs={0: a},
                memory={OPERAND_BASE: b},
            ))

    return tests


# ============================================================================
# Category 3: Byte ALU register-register (42 tests)
# ============================================================================

def generate_byte_alu_tests():
    """ADDB, SUBB, ANDB, ORB, XORB, CPB in R,R mode x 7 value pairs.

    Uses RH0 (byte reg 0, high byte of R0) and RH1 (byte reg 1, high byte of R1).
    """
    OPS = [
        ('ADDB', 0x8000), ('SUBB', 0x8200), ('ANDB', 0x8600),
        ('ORB', 0x8400), ('XORB', 0x8800), ('CPB', 0x8A00),
    ]
    tests = []
    for mnem, base in OPS:
        for sfx, a, b in _BYTE_VALS:
            # RH0=byte reg 0 (high byte of R0), RH1=byte reg 1 (high byte of R1)
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_r_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} RH0, RH1: 0x{a:02X}, 0x{b:02X}",
                tags=["byte_alu", "R_mode"],
                code=_enc_rr(base, 0, 1),  # ADDB RH0, RH1
                regs={0: a << 8, 1: b << 8},
            ))
    return tests


# ============================================================================
# Category 4: Byte ALU immediate (12 tests)
# ============================================================================

def generate_byte_alu_im_tests():
    """ADDB, SUBB, ANDB, ORB, XORB, CPB immediate x 2 values."""
    OPS = [
        ('ADDB', 0x0000), ('SUBB', 0x0200), ('ANDB', 0x0600),
        ('ORB', 0x0400), ('XORB', 0x0800), ('CPB', 0x0A00),
    ]
    VALS = [('normal', 0x12, 0x34), ('carry', 0xFF, 0x01)]
    tests = []
    for mnem, base in OPS:
        for sfx, a, b in VALS:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_im_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} RH0, #0x{b:02X}: RH0=0x{a:02X}",
                tags=["byte_alu", "IM_mode"],
                code=_enc_im_b(base, 0, b),  # ADDB RH0, #imm
                regs={0: a << 8},
            ))
    return tests


# ============================================================================
# Category 5: Long ALU register-register (15 tests)
# ============================================================================

def generate_long_alu_tests():
    """ADDL, SUBL, CPL in RR,RR mode x 5 value pairs.

    RR0 (R0:R1) and RR2 (R2:R3).
    """
    OPS = [('ADDL', 0x9600), ('SUBL', 0x9200), ('CPL', 0x9000)]
    tests = []
    for mnem, base in OPS:
        for sfx, a, b in _LONG_VALS:
            regs = {}
            regs.update(_long_regs(0, a))
            regs.update(_long_regs(2, b))
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_rr_rr_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} RR0, RR2: 0x{a:08X}, 0x{b:08X}",
                tags=["long_alu", "R_mode"],
                code=_enc_rr(base, 0, 2),
                regs=regs,
            ))
    return tests


# ============================================================================
# Category 6: Carry-chain (40 tests)
# ============================================================================

def generate_carry_chain_tests():
    """ADC, SBC (word) and ADCB, SBCB (byte) x 5 values x 2 FCW states."""
    tests = []

    # Word: ADC, SBC using R0, R1
    for mnem, base in [('ADC', 0xB500), ('SBC', 0xB700)]:
        for sfx, a, b in _CARRY_WORD_VALS:
            for c_name, fcw in [('c0', FCW_SYS), ('c1', fcw_with_flags(C=1))]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_r_{sfx}_{c_name}",
                    mnemonic=mnem,
                    desc=f"{mnem} R0, R1: 0x{a:04X}, 0x{b:04X}, {c_name}",
                    tags=["carry_chain", "word", "R_mode"],
                    code=_enc_rr(base, 0, 1),
                    regs={0: a, 1: b},
                    fcw=fcw,
                ))

    # Byte: ADCB, SBCB using RH0, RH1
    for mnem, base in [('ADCB', 0xB400), ('SBCB', 0xB600)]:
        for sfx, a, b in _CARRY_BYTE_VALS:
            for c_name, fcw in [('c0', FCW_SYS), ('c1', fcw_with_flags(C=1))]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_r_{sfx}_{c_name}",
                    mnemonic=mnem,
                    desc=f"{mnem} RH0, RH1: 0x{a:02X}, 0x{b:02X}, {c_name}",
                    tags=["carry_chain", "byte", "R_mode"],
                    code=_enc_rr(base, 0, 1),
                    regs={0: a << 8, 1: b << 8},
                    fcw=fcw,
                ))

    return tests


# ============================================================================
# Category 7: Unary word (20 tests)
# ============================================================================

def generate_unary_word_tests():
    """NEG, COM, CLR, TEST, TSET x 4 values."""
    # Encoding: 0x8D00 | (Rd << 4) | subop
    OPS = [
        ('NEG', 0x02), ('COM', 0x00), ('CLR', 0x08),
        ('TEST', 0x04), ('TSET', 0x06),
    ]
    tests = []
    for mnem, subop in OPS:
        for sfx, val in _UNARY_W:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} R0: 0x{val:04X}",
                tags=["unary", "word", "R_mode"],
                code=[0x8D00 | subop],  # Rd=R0
                regs={0: val},
            ))
    return tests


# ============================================================================
# Category 8: Unary byte (20 tests)
# ============================================================================

def generate_unary_byte_tests():
    """NEGB, COMB, CLRB, TESTB, TSETB x 4 values."""
    # Encoding: 0x8C00 | (Rbd << 4) | subop
    OPS = [
        ('NEGB', 0x02), ('COMB', 0x00), ('CLRB', 0x08),
        ('TESTB', 0x04), ('TSETB', 0x06),
    ]
    tests = []
    for mnem, subop in OPS:
        for sfx, val in _UNARY_B:
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_r_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} RH0: 0x{val:02X}",
                tags=["unary", "byte", "R_mode"],
                code=[0x8C00 | subop],  # Rbd=RH0
                regs={0: val << 8},
            ))
    return tests


# ============================================================================
# Category 9: Unary long (4 tests)
# ============================================================================

def generate_unary_long_tests():
    """TESTL x 4 values."""
    # TESTL RRd: 0x9C08 | (RRd << 4)
    tests = []
    for sfx, val in _UNARY_L:
        regs = _long_regs(0, val)
        tests.append(_tc(
            name=f"sys_testl_rr_{sfx}",
            mnemonic="TESTL",
            desc=f"TESTL RR0: 0x{val:08X}",
            tags=["unary", "long", "R_mode"],
            code=[0x9C08],  # TESTL RR0
            regs=regs,
        ))
    return tests


# ============================================================================
# Category 10: Static shifts word (36 tests)
# ============================================================================

def generate_shift_word_tests():
    """SLL, SRL, SLA, SRA x 3 counts x 3 values."""
    # SLL/SRL: 0xB301 | (Rd << 4), count (positive=left, negative=right)
    # SLA/SRA: 0xB309 | (Rd << 4), count (positive=left, negative=right)
    COUNTS = [1, 4, 8]
    tests = []
    for sfx_v, val in _SHIFT_W:
        for n in COUNTS:
            # SLL: left logical
            tests.append(_tc(
                name=f"sys_sll_r_{sfx_v}_n{n}",
                mnemonic="SLL",
                desc=f"SLL R0, #{n}: 0x{val:04X}",
                tags=["shift", "word", "R_mode"],
                code=[0xB301, n],
                regs={0: val},
            ))
            # SRL: right logical (negative count)
            tests.append(_tc(
                name=f"sys_srl_r_{sfx_v}_n{n}",
                mnemonic="SRL",
                desc=f"SRL R0, #{n}: 0x{val:04X}",
                tags=["shift", "word", "R_mode"],
                code=[0xB301, (-n) & 0xFFFF],
                regs={0: val},
            ))
            # SLA: left arithmetic
            tests.append(_tc(
                name=f"sys_sla_r_{sfx_v}_n{n}",
                mnemonic="SLA",
                desc=f"SLA R0, #{n}: 0x{val:04X}",
                tags=["shift", "word", "R_mode"],
                code=[0xB309, n],
                regs={0: val},
            ))
            # SRA: right arithmetic (negative count)
            tests.append(_tc(
                name=f"sys_sra_r_{sfx_v}_n{n}",
                mnemonic="SRA",
                desc=f"SRA R0, #{n}: 0x{val:04X}",
                tags=["shift", "word", "R_mode"],
                code=[0xB309, (-n) & 0xFFFF],
                regs={0: val},
            ))
    return tests


# ============================================================================
# Category 11: Static shifts byte (24 tests)
# ============================================================================

def generate_shift_byte_tests():
    """SLLB, SRLB, SLAB, SRAB x 2 counts x 3 values."""
    # SLLB/SRLB: 0xB201, count
    # SLAB/SRAB: 0xB209, count
    COUNTS = [1, 4]
    tests = []
    for sfx_v, val in _SHIFT_B:
        for n in COUNTS:
            tests.append(_tc(
                name=f"sys_sllb_r_{sfx_v}_n{n}",
                mnemonic="SLLB",
                desc=f"SLLB RH0, #{n}: 0x{val:02X}",
                tags=["shift", "byte", "R_mode"],
                code=[0xB201, n],
                regs={0: val << 8},
            ))
            tests.append(_tc(
                name=f"sys_srlb_r_{sfx_v}_n{n}",
                mnemonic="SRLB",
                desc=f"SRLB RH0, #{n}: 0x{val:02X}",
                tags=["shift", "byte", "R_mode"],
                code=[0xB201, (-n) & 0xFFFF],
                regs={0: val << 8},
            ))
            tests.append(_tc(
                name=f"sys_slab_r_{sfx_v}_n{n}",
                mnemonic="SLAB",
                desc=f"SLAB RH0, #{n}: 0x{val:02X}",
                tags=["shift", "byte", "R_mode"],
                code=[0xB209, n],
                regs={0: val << 8},
            ))
            tests.append(_tc(
                name=f"sys_srab_r_{sfx_v}_n{n}",
                mnemonic="SRAB",
                desc=f"SRAB RH0, #{n}: 0x{val:02X}",
                tags=["shift", "byte", "R_mode"],
                code=[0xB209, (-n) & 0xFFFF],
                regs={0: val << 8},
            ))
    return tests


# ============================================================================
# Category 12: Static shifts long (16 tests)
# ============================================================================

def generate_shift_long_tests():
    """SLLL, SRLL, SLAL, SRAL x 2 counts x 2 values."""
    # SLLL/SRLL: 0xB305, count
    # SLAL/SRAL: 0xB30D, count
    COUNTS = [1, 8]
    tests = []
    for sfx_v, val in _SHIFT_L:
        for n in COUNTS:
            regs = _long_regs(0, val)
            tests.append(_tc(
                name=f"sys_slll_rr_{sfx_v}_n{n}",
                mnemonic="SLLL",
                desc=f"SLLL RR0, #{n}: 0x{val:08X}",
                tags=["shift", "long", "R_mode"],
                code=[0xB305, n],
                regs=regs,
            ))
            regs = _long_regs(0, val)
            tests.append(_tc(
                name=f"sys_srll_rr_{sfx_v}_n{n}",
                mnemonic="SRLL",
                desc=f"SRLL RR0, #{n}: 0x{val:08X}",
                tags=["shift", "long", "R_mode"],
                code=[0xB305, (-n) & 0xFFFF],
                regs=regs,
            ))
            regs = _long_regs(0, val)
            tests.append(_tc(
                name=f"sys_slal_rr_{sfx_v}_n{n}",
                mnemonic="SLAL",
                desc=f"SLAL RR0, #{n}: 0x{val:08X}",
                tags=["shift", "long", "R_mode"],
                code=[0xB30D, n],
                regs=regs,
            ))
            regs = _long_regs(0, val)
            tests.append(_tc(
                name=f"sys_sral_rr_{sfx_v}_n{n}",
                mnemonic="SRAL",
                desc=f"SRAL RR0, #{n}: 0x{val:08X}",
                tags=["shift", "long", "R_mode"],
                code=[0xB30D, (-n) & 0xFFFF],
                regs=regs,
            ))
    return tests


# ============================================================================
# Category 13: Dynamic shifts (48 tests)
# ============================================================================

def generate_dynamic_shift_tests():
    """SDA, SDL, SDAB, SDLB, SDAL, SDLL x 4 amounts x 2 values.

    Dynamic shifts use Rs as the shift count (positive=left, negative=right).
    Encoding: word1 = base | (Rs << 4) | subop, word2 = 0x0000 | (Rd << 8)
    """
    # Word dynamic: SDA=0xB30B, SDL=0xB303
    # Byte dynamic: SDAB=0xB20B, SDLB=0xB203
    # Long dynamic: SDAL=0xB30F, SDLL=0xB307
    AMOUNTS = [('l1', 1), ('r1', -1), ('l4', 4), ('r4', -4)]
    tests = []

    # Word: SDA, SDL - use R0 as dest, R1 as count
    for mnem, subop in [('SDA', 0x0B), ('SDL', 0x03)]:
        for sfx_a, amt in AMOUNTS:
            for sfx_v, val in [('one', 0x0001), ('msb', 0x8000)]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_{sfx_v}_{sfx_a}",
                    mnemonic=mnem,
                    desc=f"{mnem} R0, R1: val=0x{val:04X}, count={amt}",
                    tags=["shift", "dynamic", "word"],
                    code=[0xB300 | (1 << 4) | subop, 0x0000],  # Rs=R1, Rd=R0
                    regs={0: val, 1: amt & 0xFFFF},
                ))

    # Byte: SDAB, SDLB - use RH0 as dest, R1 as count
    for mnem, subop in [('SDAB', 0x0B), ('SDLB', 0x03)]:
        for sfx_a, amt in AMOUNTS:
            for sfx_v, val in [('one', 0x01), ('msb', 0x80)]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_{sfx_v}_{sfx_a}",
                    mnemonic=mnem,
                    desc=f"{mnem} RH0, R1: val=0x{val:02X}, count={amt}",
                    tags=["shift", "dynamic", "byte"],
                    code=[0xB200 | (1 << 4) | subop, 0x0000],  # Rs=R1, Rbd=RH0
                    regs={0: val << 8, 1: amt & 0xFFFF},
                ))

    # Long: SDAL, SDLL - use RR2 as dest, R1 as count
    for mnem, subop in [('SDAL', 0x0F), ('SDLL', 0x07)]:
        for sfx_a, amt in AMOUNTS:
            for sfx_v, val in [('one', 0x00000001), ('msb', 0x80000000)]:
                regs = {1: amt & 0xFFFF}
                regs.update(_long_regs(2, val))
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_rr_{sfx_v}_{sfx_a}",
                    mnemonic=mnem,
                    desc=f"{mnem} RR2, R1: val=0x{val:08X}, count={amt}",
                    tags=["shift", "dynamic", "long"],
                    code=[0xB300 | (1 << 4) | subop, 0x0200],  # Rs=R1, RRd=RR2
                    regs=regs,
                ))

    return tests


# ============================================================================
# Category 14: Rotates word (32 tests)
# ============================================================================

def generate_rotate_word_tests():
    """RL, RR, RLC, RRC with #1 and #2 counts."""
    # RL #1: 0xB300, RL #2: 0xB302
    # RR #1: 0xB304, RR #2: 0xB306
    # RLC #1: 0xB308, RLC #2: 0xB30A
    # RRC #1: 0xB30C, RRC #2: 0xB30E
    VALS = [('one', 0x0001), ('msb', 0x8000), ('pattern', 0xA5A5)]
    tests = []

    # RL, RR: no carry dependency
    for mnem, op1, op2 in [('RL', 0xB300, 0xB302), ('RR', 0xB304, 0xB306)]:
        for sfx_v, val in VALS:
            for cnt_name, opcode in [('n1', op1), ('n2', op2)]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_{sfx_v}_{cnt_name}",
                    mnemonic=mnem,
                    desc=f"{mnem} R0, #{cnt_name[-1]}: 0x{val:04X}",
                    tags=["rotate", "word", "R_mode"],
                    code=[opcode],
                    regs={0: val},
                ))

    # RLC, RRC: test with C=0 and C=1
    for mnem, op1, op2 in [('RLC', 0xB308, 0xB30A), ('RRC', 0xB30C, 0xB30E)]:
        for sfx_v, val in VALS:
            for cnt_name, opcode in [('n1', op1), ('n2', op2)]:
                for c_name, fcw in [('c0', FCW_SYS), ('c1', fcw_with_flags(C=1))]:
                    tests.append(_tc(
                        name=f"sys_{mnem.lower()}_r_{sfx_v}_{cnt_name}_{c_name}",
                        mnemonic=mnem,
                        desc=f"{mnem} R0, #{cnt_name[-1]}: 0x{val:04X}, {c_name}",
                        tags=["rotate", "word", "R_mode"],
                        code=[opcode],
                        regs={0: val},
                        fcw=fcw,
                    ))

    return tests


# ============================================================================
# Category 15: Rotates byte (32 tests)
# ============================================================================

def generate_rotate_byte_tests():
    """RLB, RRB, RLCB, RRCB with #1 and #2 counts."""
    # Same as word but 0xB2xx instead of 0xB3xx
    VALS = [('one', 0x01), ('msb', 0x80), ('pattern', 0xA5)]
    tests = []

    for mnem, op1, op2 in [('RLB', 0xB200, 0xB202), ('RRB', 0xB204, 0xB206)]:
        for sfx_v, val in VALS:
            for cnt_name, opcode in [('n1', op1), ('n2', op2)]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_{sfx_v}_{cnt_name}",
                    mnemonic=mnem,
                    desc=f"{mnem} RH0, #{cnt_name[-1]}: 0x{val:02X}",
                    tags=["rotate", "byte", "R_mode"],
                    code=[opcode],
                    regs={0: val << 8},
                ))

    for mnem, op1, op2 in [('RLCB', 0xB208, 0xB20A), ('RRCB', 0xB20C, 0xB20E)]:
        for sfx_v, val in VALS:
            for cnt_name, opcode in [('n1', op1), ('n2', op2)]:
                for c_name, fcw in [('c0', FCW_SYS), ('c1', fcw_with_flags(C=1))]:
                    tests.append(_tc(
                        name=f"sys_{mnem.lower()}_r_{sfx_v}_{cnt_name}_{c_name}",
                        mnemonic=mnem,
                        desc=f"{mnem} RH0, #{cnt_name[-1]}: 0x{val:02X}, {c_name}",
                        tags=["rotate", "byte", "R_mode"],
                        code=[opcode],
                        regs={0: val << 8},
                        fcw=fcw,
                    ))

    return tests


# ============================================================================
# Category 16: Rotate digit (6 tests)
# ============================================================================

def generate_rotate_digit_tests():
    """RLDB, RRDB x 3 values.

    RLDB Rbl, Rbs: 0xBE00 | (Rbs << 4) | Rbl
    RRDB Rbl, Rbs: 0xBC00 | (Rbs << 4) | Rbl
    Uses RL0 (byte reg 8, low byte of R0) and RH1 (byte reg 1, high byte of R1).
    """
    VALS = [('bcd_00', 0x00, 0x12), ('bcd_99', 0x99, 0x87), ('bcd_50', 0x50, 0x43)]
    tests = []
    for mnem, base in [('RLDB', 0xBE00), ('RRDB', 0xBC00)]:
        for sfx, v_lo, v_hi in VALS:
            # Rbl=RL0 (byte reg 8), Rbs=RH1 (byte reg 1)
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_{sfx}",
                mnemonic=mnem,
                desc=f"{mnem} RL0, RH1: RL0=0x{v_lo:02X}, RH1=0x{v_hi:02X}",
                tags=["rotate", "digit", "byte"],
                code=[base | (1 << 4) | 8],  # Rbs=RH1(1), Rbl=RL0(8)
                regs={0: v_lo, 1: v_hi << 8},  # RL0=low byte of R0, RH1=high byte of R1
            ))
    return tests


# ============================================================================
# Category 17: Bit operations word (18 tests)
# ============================================================================

def generate_bit_word_tests():
    """BIT, SET, RES x 3 bit positions x 2 values."""
    # BIT Rd, #b: 0xA700 | (Rd << 4) | b
    # SET Rd, #b: 0xA500 | (Rd << 4) | b
    # RES Rd, #b: 0xA300 | (Rd << 4) | b
    OPS = [('BIT', 0xA700), ('SET', 0xA500), ('RES', 0xA300)]
    BITS = [0, 7, 15]
    VALS = [('zero', 0x0000), ('allones', 0xFFFF)]
    tests = []
    for mnem, base in OPS:
        for bit in BITS:
            for sfx, val in VALS:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_b{bit}_{sfx}",
                    mnemonic=mnem,
                    desc=f"{mnem} R0, #{bit}: R0=0x{val:04X}",
                    tags=["bit", "word", "R_mode"],
                    code=[base | bit],  # Rd=R0
                    regs={0: val},
                ))
    return tests


# ============================================================================
# Category 18: Bit operations byte (18 tests)
# ============================================================================

def generate_bit_byte_tests():
    """BITB, SETB, RESB x 3 bit positions x 2 values."""
    # BITB Rbd, #b: 0xA600 | (Rbd << 4) | b
    # SETB Rbd, #b: 0xA400 | (Rbd << 4) | b
    # RESB Rbd, #b: 0xA200 | (Rbd << 4) | b
    OPS = [('BITB', 0xA600), ('SETB', 0xA400), ('RESB', 0xA200)]
    BITS = [0, 3, 7]
    VALS = [('zero', 0x00), ('allones', 0xFF)]
    tests = []
    for mnem, base in OPS:
        for bit in BITS:
            for sfx, val in VALS:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_b{bit}_{sfx}",
                    mnemonic=mnem,
                    desc=f"{mnem} RH0, #{bit}: RH0=0x{val:02X}",
                    tags=["bit", "byte", "R_mode"],
                    code=[base | bit],  # Rbd=RH0
                    regs={0: val << 8},
                ))
    return tests


# ============================================================================
# Category 19: INC/DEC word (24 tests)
# ============================================================================

def generate_inc_dec_word_tests():
    """INC, DEC x 3 n-values x 4 operands."""
    # INC Rd, #n: 0xA900 | (Rd << 4) | (n-1)
    # DEC Rd, #n: 0xAB00 | (Rd << 4) | (n-1)
    N_VALS = [1, 2, 16]
    OPERANDS = [('zero', 0x0000), ('one', 0x0001), ('max', 0xFFFF), ('half', 0x8000)]
    tests = []
    for mnem, base in [('INC', 0xA900), ('DEC', 0xAB00)]:
        for n in N_VALS:
            for sfx, val in OPERANDS:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_n{n}_{sfx}",
                    mnemonic=mnem,
                    desc=f"{mnem} R0, #{n}: R0=0x{val:04X}",
                    tags=["inc_dec", "word", "R_mode"],
                    code=[base | (n - 1)],  # Rd=R0
                    regs={0: val},
                ))
    return tests


# ============================================================================
# Category 20: INC/DEC byte (24 tests)
# ============================================================================

def generate_inc_dec_byte_tests():
    """INCB, DECB x 3 n-values x 4 operands."""
    # INCB Rbd, #n: 0xA800 | (Rbd << 4) | (n-1)
    # DECB Rbd, #n: 0xAA00 | (Rbd << 4) | (n-1)
    N_VALS = [1, 2, 16]
    OPERANDS = [('zero', 0x00), ('one', 0x01), ('max', 0xFF), ('half', 0x80)]
    tests = []
    for mnem, base in [('INCB', 0xA800), ('DECB', 0xAA00)]:
        for n in N_VALS:
            for sfx, val in OPERANDS:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_r_n{n}_{sfx}",
                    mnemonic=mnem,
                    desc=f"{mnem} RH0, #{n}: RH0=0x{val:02X}",
                    tags=["inc_dec", "byte", "R_mode"],
                    code=[base | (n - 1)],  # Rbd=RH0
                    regs={0: val << 8},
                ))
    return tests


# ============================================================================
# Category 21: INC/DEC memory (8 tests)
# ============================================================================

def generate_inc_dec_mem_tests():
    """INC @Rd, DEC @Rd x 2 n-values x 2 operands."""
    # INC @Rd, #n: 0x2900 | (Rd << 4) | (n-1)
    # DEC @Rd, #n: 0x2B00 | (Rd << 4) | (n-1)
    tests = []
    for mnem, base in [('INC', 0x2900), ('DEC', 0x2B00)]:
        for n in [1, 2]:
            for sfx, val in [('normal', 0x1234), ('max', 0xFFFF)]:
                tests.append(_tc(
                    name=f"sys_{mnem.lower()}_ir_n{n}_{sfx}",
                    mnemonic=mnem,
                    desc=f"{mnem} @R2, #{n}: [R2]=0x{val:04X}",
                    tags=["inc_dec", "word", "IR_mode"],
                    code=[base | (2 << 4) | (n - 1)],  # Rd=R2
                    regs={2: OPERAND_BASE},
                    memory={OPERAND_BASE: val},
                ))
    return tests


# ============================================================================
# Category 22: MULT/DIV (20 tests)
# ============================================================================

def generate_mult_div_tests():
    """MULT, DIV, MULTL, DIVL with various values."""
    tests = []

    # MULT RRd, Rs: 0x9900 | (Rs << 4) | RRd
    # Multiplies Rd_low_word * Rs -> RRd (32-bit result)
    # Using RR0 (R0:R1), R2
    MULT_VALS = [
        ('zero', 0x0000, 0x0000),
        ('one', 0x0001, 0x0001),
        ('normal', 0x0064, 0x0032),  # 100 * 50 = 5000
        ('large', 0xFFFF, 0x0002),
        ('max', 0xFFFF, 0xFFFF),
        ('signed', 0x8000, 0x0002),  # -32768 * 2 (signed)
    ]
    for sfx, a, b in MULT_VALS:
        tests.append(_tc(
            name=f"sys_mult_rr_r_{sfx}",
            mnemonic="MULT",
            desc=f"MULT RR0, R2: R1=0x{a:04X} * R2=0x{b:04X}",
            tags=["mult_div", "word"],
            code=[0x9920],  # MULT RR0, R2
            regs={1: a, 2: b},
        ))

    # DIV RRd, Rs: 0x9B00 | (Rs << 4) | RRd
    # Divides RRd (32-bit) / Rs -> quotient in R1, remainder in R0
    DIV_VALS = [
        ('normal', 0x00001388, 0x0064),  # 5000 / 100 = 50 r 0
        ('remainder', 0x0000000B, 0x0003),  # 11 / 3 = 3 r 2
        ('large', 0x0001FFFE, 0xFFFF),  # 131070 / 65535 = 2 r 0
        ('one', 0x00000001, 0x0001),
    ]
    for sfx, dividend, divisor in DIV_VALS:
        regs = _long_regs(0, dividend)
        regs[2] = divisor
        tests.append(_tc(
            name=f"sys_div_rr_r_{sfx}",
            mnemonic="DIV",
            desc=f"DIV RR0, R2: 0x{dividend:08X} / 0x{divisor:04X}",
            tags=["mult_div", "word"],
            code=[0x9B20],  # DIV RR0, R2
            regs=regs,
        ))

    # MULTL RQd, RRs: 0x9800 | (RRs << 4) | RQd
    # Using RQ0 (R0:R1:R2:R3), RR4 (R4:R5)
    for sfx, a, b in [('normal', 0x00000064, 0x00000032),
                       ('large', 0x0000FFFF, 0x0000FFFF)]:
        regs = _long_regs(2, a)  # Low pair of RQ0
        regs.update(_long_regs(4, b))
        tests.append(_tc(
            name=f"sys_multl_rq_rr_{sfx}",
            mnemonic="MULTL",
            desc=f"MULTL RQ0, RR4: 0x{a:08X} * 0x{b:08X}",
            tags=["mult_div", "long"],
            code=[0x9840],  # MULTL RQ0, RR4
            regs=regs,
        ))

    # DIVL RQd, RRs: 0x9A00 | (RRs << 4) | RQd
    for sfx, dividend_hi, dividend_lo, divisor in [
            ('normal', 0x00000000, 0x00001388, 0x00000064),
            ('large', 0x00000000, 0xFFFFFFFE, 0x0000FFFF)]:
        regs = _long_regs(0, dividend_hi)
        regs.update(_long_regs(2, dividend_lo))
        regs.update(_long_regs(4, divisor))
        tests.append(_tc(
            name=f"sys_divl_rq_rr_{sfx}",
            mnemonic="DIVL",
            desc=f"DIVL RQ0, RR4: 0x{dividend_hi:08X}{dividend_lo:08X} / 0x{divisor:08X}",
            tags=["mult_div", "long"],
            code=[0x9A40],  # DIVL RQ0, RR4
            regs=regs,
        ))

    return tests


# ============================================================================
# Category 23: DAB (6 tests)
# ============================================================================

def generate_dab_tests():
    """DAB with various BCD setups (varying C/H/DA flags)."""
    # DAB Rbd: 0xB000 | (Rbd << 4)
    CASES = [
        ('add_no_adj', 0x11, FCW_SYS),
        ('add_low_adj', 0x1A, fcw_with_flags(H=1)),
        ('add_high_adj', 0xA1, fcw_with_flags(C=1)),
        ('add_both_adj', 0x9B, fcw_with_flags(C=1, H=1)),
        ('sub_no_adj', 0x22, fcw_with_flags(DA=1)),
        ('sub_adj', 0x7A, fcw_with_flags(DA=1, C=1)),
    ]
    tests = []
    for sfx, val, fcw in CASES:
        tests.append(_tc(
            name=f"sys_dab_{sfx}",
            mnemonic="DAB",
            desc=f"DAB RH0: 0x{val:02X}, flags={fcw:#06x}",
            tags=["dab", "byte"],
            code=[0xB000],  # DAB RH0
            regs={0: val << 8},
            fcw=fcw,
        ))
    return tests


# ============================================================================
# Category 24: Sign extend (9 tests)
# ============================================================================

def generate_sign_extend_tests():
    """EXTSB, EXTS, EXTSL x 3 values each."""
    tests = []

    # EXTSB Rd: 0xB100 | (Rd << 4) - sign extend byte to word
    for sfx, val in [('zero', 0x0000), ('pos', 0x007F), ('neg', 0x0080)]:
        tests.append(_tc(
            name=f"sys_extsb_r_{sfx}",
            mnemonic="EXTSB",
            desc=f"EXTSB R0: low byte=0x{val & 0xFF:02X}",
            tags=["sign_extend", "word"],
            code=[0xB100],  # EXTSB R0
            regs={0: val},
        ))

    # EXTS RRd: 0xB10A | (RRd << 4) - sign extend word to long
    for sfx, val in [('zero', 0x0000), ('pos', 0x7FFF), ('neg', 0x8000)]:
        tests.append(_tc(
            name=f"sys_exts_rr_{sfx}",
            mnemonic="EXTS",
            desc=f"EXTS RR0: R1=0x{val:04X}",
            tags=["sign_extend", "long"],
            code=[0xB10A],  # EXTS RR0
            regs={0: 0x0000, 1: val},
        ))

    # EXTSL RQd: 0xB107 | (RQd << 4) - sign extend long to quad
    for sfx, val in [('zero', 0x00000000), ('pos', 0x7FFFFFFF), ('neg', 0x80000000)]:
        regs = _long_regs(2, val)  # Low pair of RQ0
        regs[0] = 0
        regs[1] = 0
        tests.append(_tc(
            name=f"sys_extsl_rq_{sfx}",
            mnemonic="EXTSL",
            desc=f"EXTSL RQ0: RR2=0x{val:08X}",
            tags=["sign_extend", "quad"],
            code=[0xB107],  # EXTSL RQ0
            regs=regs,
        ))

    return tests


# ============================================================================
# Category 25: Flag manipulation (48 tests)
# ============================================================================

def generate_flag_manip_tests():
    """SETFLG, RESFLG, COMFLG x all 16 mask combinations."""
    # SETFLG: 0x8D01 | (mask << 4)
    # RESFLG: 0x8D03 | (mask << 4)
    # COMFLG: 0x8D05 | (mask << 4)
    OPS = [('SETFLG', 0x8D01), ('RESFLG', 0x8D03), ('COMFLG', 0x8D05)]
    tests = []
    for mnem, base in OPS:
        for mask in range(16):
            # Use flags-set FCW for RESFLG, flags-clear for SETFLG
            if mnem == 'RESFLG':
                fcw = fcw_with_flags(C=1, Z=1, S=1, V=1)
            else:
                fcw = FCW_SYS
            flags_str = ''.join(
                f for i, f in enumerate(['C', 'Z', 'S', 'V'])
                if mask & (8 >> i)
            ) or 'none'
            tests.append(_tc(
                name=f"sys_{mnem.lower()}_m{mask:x}",
                mnemonic=mnem,
                desc=f"{mnem} {flags_str} (mask=0x{mask:X})",
                tags=["flag_manip", "control"],
                code=[base | (mask << 4)],
                fcw=fcw,
            ))
    return tests


# ============================================================================
# Category 26: TCC/TCCB (64 tests)
# ============================================================================

def generate_tcc_tests():
    """TCC and TCCB x 16 conditions x 2 flag states."""
    # TCC cc, Rd: 0xAF00 | (Rd << 4) | cc
    # TCCB cc, Rbd: 0xAE00 | (Rbd << 4) | cc
    tests = []
    for cc in range(16):
        cc_name = _CC_NAMES[cc]
        fcw_true, fcw_false = _CC_FCW[cc]

        # TCC (word) - R0 starts at 0, becomes 1 if condition met
        tests.append(_tc(
            name=f"sys_tcc_{cc_name.lower()}_true",
            mnemonic="TCC",
            desc=f"TCC {cc_name}, R0: condition true",
            tags=["tcc", "word", "control"],
            code=[0xAF00 | cc],  # Rd=R0
            regs={0: 0x0000},
            fcw=fcw_true,
        ))
        tests.append(_tc(
            name=f"sys_tcc_{cc_name.lower()}_false",
            mnemonic="TCC",
            desc=f"TCC {cc_name}, R0: condition false",
            tags=["tcc", "word", "control"],
            code=[0xAF00 | cc],
            regs={0: 0x0000},
            fcw=fcw_false,
        ))

        # TCCB (byte) - RH0 starts at 0, becomes 1 if condition met
        tests.append(_tc(
            name=f"sys_tccb_{cc_name.lower()}_true",
            mnemonic="TCCB",
            desc=f"TCCB {cc_name}, RH0: condition true",
            tags=["tcc", "byte", "control"],
            code=[0xAE00 | cc],  # Rbd=RH0
            regs={0: 0x0000},
            fcw=fcw_true,
        ))
        tests.append(_tc(
            name=f"sys_tccb_{cc_name.lower()}_false",
            mnemonic="TCCB",
            desc=f"TCCB {cc_name}, RH0: condition false",
            tags=["tcc", "byte", "control"],
            code=[0xAE00 | cc],
            regs={0: 0x0000},
            fcw=fcw_false,
        ))

    return tests


# ============================================================================
# Category 27: Load W/B/L (42 tests)
# ============================================================================

def generate_load_tests():
    """LD, LDB, LDL, LDK, LDM with various modes."""
    tests = []

    # LD Rd, Rs (register)
    for sfx, val in [('normal', 0x1234), ('zero', 0x0000), ('max', 0xFFFF)]:
        tests.append(_tc(
            name=f"sys_ld_r_r_{sfx}",
            mnemonic="LD",
            desc=f"LD R0, R1: R1=0x{val:04X}",
            tags=["load", "word", "R_mode"],
            code=[0xA110],
            regs={0: 0x0000, 1: val},
        ))

    # LD Rd, #imm (immediate)
    for sfx, val in [('normal', 0x1234), ('zero', 0x0000), ('max', 0xFFFF)]:
        tests.append(_tc(
            name=f"sys_ld_r_im_{sfx}",
            mnemonic="LD",
            desc=f"LD R0, #0x{val:04X}",
            tags=["load", "word", "IM_mode"],
            code=[0x2100, val],
            regs={0: 0xFFFF},
        ))

    # LD Rd, @Rs (indirect)
    for sfx, val in [('normal', 0xABCD), ('zero', 0x0000)]:
        tests.append(_tc(
            name=f"sys_ld_r_ir_{sfx}",
            mnemonic="LD",
            desc=f"LD R0, @R2: [R2]=0x{val:04X}",
            tags=["load", "word", "IR_mode"],
            code=[0x2120],
            regs={0: 0x0000, 2: OPERAND_BASE},
            memory={OPERAND_BASE: val},
        ))

    # LD Rd, DA (direct address)
    for sfx, val in [('normal', 0xDEAD), ('zero', 0x0000)]:
        tests.append(_tc(
            name=f"sys_ld_r_da_{sfx}",
            mnemonic="LD",
            desc=f"LD R0, 0x{OPERAND_BASE:04X}: [DA]=0x{val:04X}",
            tags=["load", "word", "DA_mode"],
            code=[0x6100, OPERAND_BASE],
            regs={0: 0x0000},
            memory={OPERAND_BASE: val},
        ))

    # LD DA, Rs (store)
    for sfx, val in [('normal', 0xCAFE), ('zero', 0x0000)]:
        tests.append(_tc(
            name=f"sys_ld_da_r_{sfx}",
            mnemonic="LD",
            desc=f"LD 0x{OPERAND_BASE:04X}, R0: R0=0x{val:04X}",
            tags=["load", "word", "DA_mode", "store"],
            code=[0x6F00, OPERAND_BASE],
            regs={0: val},
        ))

    # LD Rd, X(Rs) (indexed)
    tests.append(_tc(
        name="sys_ld_r_x_basic",
        mnemonic="LD",
        desc=f"LD R0, 0x{OPERAND_BASE:04X}(R2): indexed load",
        tags=["load", "word", "X_mode"],
        code=[0x6120, OPERAND_BASE],
        regs={0: 0x0000, 2: 0x0004},
        memory={OPERAND_BASE + 4: 0xBEEF},
    ))

    # LD @Rd, Rs (indirect store)
    tests.append(_tc(
        name="sys_ld_ir_r_basic",
        mnemonic="LD",
        desc="LD @R2, R0: indirect store",
        tags=["load", "word", "IR_mode", "store"],
        code=[0x2F20],  # LD @R2, R0: 0010_1111_Rsss_Rdnz = 0x2F00 | (0 << 4) | 2
        regs={0: 0x1234, 2: OPERAND_BASE},
    ))

    # LDB Rbd, Rbs (byte register)
    for sfx, val in [('normal', 0x42), ('zero', 0x00)]:
        tests.append(_tc(
            name=f"sys_ldb_r_r_{sfx}",
            mnemonic="LDB",
            desc=f"LDB RH0, RH1: RH1=0x{val:02X}",
            tags=["load", "byte", "R_mode"],
            code=[0xA010],  # LDB RH0, RH1
            regs={0: 0x0000, 1: val << 8},
        ))

    # LDB Rbd, #imm
    for sfx, val in [('normal', 0x42), ('max', 0xFF)]:
        tests.append(_tc(
            name=f"sys_ldb_r_im_{sfx}",
            mnemonic="LDB",
            desc=f"LDB RH0, #0x{val:02X}",
            tags=["load", "byte", "IM_mode"],
            code=[0x2000, val << 8],  # LDB RH0, #imm
            regs={0: 0xFF00},
        ))

    # LDL RRd, RRs (long register)
    for sfx, val in [('normal', 0x12345678), ('zero', 0x00000000)]:
        regs = {0: 0, 1: 0}
        regs.update(_long_regs(2, val))
        tests.append(_tc(
            name=f"sys_ldl_rr_rr_{sfx}",
            mnemonic="LDL",
            desc=f"LDL RR0, RR2: 0x{val:08X}",
            tags=["load", "long", "R_mode"],
            code=[0x9420],  # LDL RR0, RR2
            regs=regs,
        ))

    # LDL RRd, #imm32
    for sfx, val in [('normal', 0xDEADBEEF), ('zero', 0x00000000)]:
        tests.append(_tc(
            name=f"sys_ldl_rr_im_{sfx}",
            mnemonic="LDL",
            desc=f"LDL RR0, #0x{val:08X}",
            tags=["load", "long", "IM_mode"],
            code=[0x1400, (val >> 16) & 0xFFFF, val & 0xFFFF],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ))

    # LDL RRd, @Rs
    tests.append(_tc(
        name="sys_ldl_rr_ir_basic",
        mnemonic="LDL",
        desc="LDL RR0, @R2: load long from memory",
        tags=["load", "long", "IR_mode"],
        code=[0x1420],  # LDL RR0, @R2
        regs={0: 0, 1: 0, 2: OPERAND_BASE},
        memory={OPERAND_BASE: 0xDEAD, OPERAND_BASE + 2: 0xBEEF},
    ))

    # LDK Rd, #n (load constant 0-15)
    for n in [0, 5, 15]:
        tests.append(_tc(
            name=f"sys_ldk_r_n{n}",
            mnemonic="LDK",
            desc=f"LDK R0, #{n}",
            tags=["load", "word", "R_mode"],
            code=[0xBD00 | n],  # LDK R0, #n
            regs={0: 0xFFFF},
        ))

    # LDM Rd, @Rs, #n (load multiple)
    # LDM Rd, @Rs, n: word1 = 0x1C01 | (Rs << 4), word2 = (Rd << 8) | (n-1)
    tests.append(_tc(
        name="sys_ldm_load_3",
        mnemonic="LDM",
        desc="LDM R3, @R2, #3: load 3 regs from memory",
        tags=["load", "word", "IR_mode"],
        code=[0x1C21, 0x0302],  # Rs=R2, Rd=R3, n=3
        regs={2: OPERAND_BASE, 3: 0, 4: 0, 5: 0},
        memory={OPERAND_BASE: 0x1111, OPERAND_BASE + 2: 0x2222, OPERAND_BASE + 4: 0x3333},
    ))

    # LDM @Rd, Rs, #n (store multiple)
    # word1 = 0x1C09 | (Rd << 4), word2 = (Rs << 8) | (n-1)
    tests.append(_tc(
        name="sys_ldm_store_3",
        mnemonic="LDM",
        desc="LDM @R2, R3, #3: store 3 regs to memory",
        tags=["load", "word", "IR_mode", "store"],
        code=[0x1C29, 0x0302],  # Rd=R2, Rs=R3, n=3
        regs={2: OPERAND_BASE, 3: 0xAAAA, 4: 0xBBBB, 5: 0xCCCC},
    ))

    return tests


# ============================================================================
# Category 28: Exchange (4 tests)
# ============================================================================

def generate_exchange_tests():
    """EX, EXB x 2 values each."""
    tests = []

    # EX Rd, Rs: 0xAD00 | (Rs << 4) | Rd
    for sfx, a, b in [('normal', 0x1234, 0x5678), ('same', 0xAAAA, 0xAAAA)]:
        tests.append(_tc(
            name=f"sys_ex_r_r_{sfx}",
            mnemonic="EX",
            desc=f"EX R0, R1: 0x{a:04X}, 0x{b:04X}",
            tags=["exchange", "word", "R_mode"],
            code=[0xAD10],
            regs={0: a, 1: b},
        ))

    # EXB Rbd, Rbs: 0xAC00 | (Rbs << 4) | Rbd
    for sfx, a, b in [('normal', 0x12, 0x56), ('same', 0xAA, 0xAA)]:
        tests.append(_tc(
            name=f"sys_exb_r_r_{sfx}",
            mnemonic="EXB",
            desc=f"EXB RH0, RH1: 0x{a:02X}, 0x{b:02X}",
            tags=["exchange", "byte", "R_mode"],
            code=[0xAC10],
            regs={0: a << 8, 1: b << 8},
        ))

    return tests


# ============================================================================
# Category 29: Stack (8 tests)
# ============================================================================

def generate_stack_tests():
    """PUSH, POP, PUSHL, POPL x 2 values each."""
    tests = []

    # PUSH @R15, Rs: 0x9300 | (15 << 4) | Rs
    for sfx, val in [('normal', 0x1234), ('max', 0xFFFF)]:
        tests.append(_tc(
            name=f"sys_push_r_{sfx}",
            mnemonic="PUSH",
            desc=f"PUSH @R15, R0: 0x{val:04X}",
            tags=["stack", "word"],
            code=[0x93F0],
            regs={0: val, 15: STACK_BASE},
        ))

    # POP Rd, @R15: 0x9700 | (15 << 4) | Rd
    for sfx, val in [('normal', 0xABCD), ('zero', 0x0000)]:
        tests.append(_tc(
            name=f"sys_pop_r_{sfx}",
            mnemonic="POP",
            desc=f"POP R0, @R15: [SP]=0x{val:04X}",
            tags=["stack", "word"],
            code=[0x97F0],
            regs={0: 0x0000, 15: STACK_BASE - 2},
            memory={STACK_BASE - 2: val},
        ))

    # PUSHL @R15, RRs: 0x9100 | (15 << 4) | RRs
    for sfx, val in [('normal', 0x12345678), ('zero', 0x00000000)]:
        regs = {15: STACK_BASE}
        regs.update(_long_regs(0, val))
        tests.append(_tc(
            name=f"sys_pushl_rr_{sfx}",
            mnemonic="PUSHL",
            desc=f"PUSHL @R15, RR0: 0x{val:08X}",
            tags=["stack", "long"],
            code=[0x91F0],  # PUSHL @R15, RR0
            regs=regs,
        ))

    # POPL RRd, @R15: 0x9500 | (15 << 4) | RRd
    for sfx, val in [('normal', 0xDEADBEEF), ('zero', 0x00000000)]:
        tests.append(_tc(
            name=f"sys_popl_rr_{sfx}",
            mnemonic="POPL",
            desc=f"POPL RR0, @R15: 0x{val:08X}",
            tags=["stack", "long"],
            code=[0x95F0],  # POPL RR0, @R15
            regs={0: 0, 1: 0, 15: STACK_BASE - 4},
            memory={STACK_BASE - 4: (val >> 16) & 0xFFFF,
                    STACK_BASE - 2: val & 0xFFFF},
        ))

    return tests


# ============================================================================
# Category 30: Branch (16 tests)
# ============================================================================

def generate_branch_tests():
    """JP and JR with 4 condition codes x taken/not-taken."""
    tests = []
    CCS = [
        (6, 'EQ', fcw_with_flags(Z=1), FCW_SYS),
        (7, 'C', fcw_with_flags(C=1), FCW_SYS),
        (5, 'MI', fcw_with_flags(S=1), FCW_SYS),
        (14, 'NE', FCW_SYS, fcw_with_flags(Z=1)),
    ]

    for cc, cc_name, fcw_taken, fcw_not in CCS:
        # JP taken: jump over bad marker to good marker
        tests.append(_tc(
            name=f"sys_jp_{cc_name.lower()}_taken",
            mnemonic="JP",
            desc=f"JP {cc_name}: taken",
            tags=["branch", "word", "DA_mode"],
            code=[
                0x5E00 | cc, 0x0208,  # JP cc, 0x0208
                0x2100, 0xBAD0,       # LD R0, #0xBAD0 (fall-through)
                0x2100, 0x600D,       # LD R0, #0x600D (target)
            ],
            regs={0: 0x0000},
            fcw=fcw_taken,
        ))
        # JP not taken: fall through to good marker
        tests.append(_tc(
            name=f"sys_jp_{cc_name.lower()}_not_taken",
            mnemonic="JP",
            desc=f"JP {cc_name}: not taken",
            tags=["branch", "word", "DA_mode"],
            code=[
                0x5E00 | cc, 0x0208,  # JP cc, 0x0208 (not taken)
                0x2100, 0x600D,       # LD R0, #0x600D (fall-through)
            ],
            regs={0: 0x0000},
            fcw=fcw_not,
        ))

        # JR taken: relative jump +2 words forward
        tests.append(_tc(
            name=f"sys_jr_{cc_name.lower()}_taken",
            mnemonic="JR",
            desc=f"JR {cc_name}: taken (+2)",
            tags=["branch", "word", "RA_mode"],
            code=[
                0xE000 | (cc << 8) | 0x02,  # JR cc, +2
                0x2100, 0xBAD0,              # LD R0, #0xBAD0
                0x2100, 0x600D,              # LD R0, #0x600D (target)
            ],
            regs={0: 0x0000},
            fcw=fcw_taken,
        ))
        # JR not taken
        tests.append(_tc(
            name=f"sys_jr_{cc_name.lower()}_not_taken",
            mnemonic="JR",
            desc=f"JR {cc_name}: not taken",
            tags=["branch", "word", "RA_mode"],
            code=[
                0xE000 | (cc << 8) | 0x02,  # JR cc, +2 (not taken)
                0x2100, 0x600D,              # LD R0, #0x600D
            ],
            regs={0: 0x0000},
            fcw=fcw_not,
        ))

    return tests


# ============================================================================
# Category 31: DJNZ/DBJNZ (4 tests)
# ============================================================================

def generate_djnz_tests():
    """DJNZ and DBJNZ: loop and no-loop cases."""
    tests = []

    # DJNZ Rn, disp: 1111_nnnn_1_ddddddd
    # Loop 3 times: INC R0; DJNZ R1, back
    tests.append(_tc(
        name="sys_djnz_loop",
        mnemonic="DJNZ",
        desc="DJNZ R1: loop 3 times",
        tags=["branch", "djnz", "word"],
        code=[0xA900, 0xF182],  # INC R0, #1; DJNZ R1, -2
        regs={0: 0x0000, 1: 0x0003},
    ))
    # DJNZ with counter=1 (no loop, just decrement)
    tests.append(_tc(
        name="sys_djnz_no_loop",
        mnemonic="DJNZ",
        desc="DJNZ R1: counter=1, no loop",
        tags=["branch", "djnz", "word"],
        code=[0xA900, 0xF182],  # INC R0, #1; DJNZ R1, -2
        regs={0: 0x0000, 1: 0x0001},
    ))

    # DBJNZ Rbn, disp: 1111_nnnn_0_ddddddd
    # Use RH1 (byte reg 1) as counter
    tests.append(_tc(
        name="sys_dbjnz_loop",
        mnemonic="DBJNZ",
        desc="DBJNZ RH1: loop 3 times",
        tags=["branch", "djnz", "byte"],
        code=[0xA900, 0xF102],  # INC R0, #1; DBJNZ RH1, -2
        regs={0: 0x0000, 1: 0x0300},  # RH1 = 3
    ))
    tests.append(_tc(
        name="sys_dbjnz_no_loop",
        mnemonic="DBJNZ",
        desc="DBJNZ RH1: counter=1, no loop",
        tags=["branch", "djnz", "byte"],
        code=[0xA900, 0xF102],
        regs={0: 0x0000, 1: 0x0100},  # RH1 = 1
    ))

    return tests


# ============================================================================
# Category 32: CALL/RET (3 tests)
# ============================================================================

def generate_call_ret_tests():
    """CALL, CALR, RET."""
    tests = []

    # CALL addr, RET T
    # Layout: LD R0,#1; CALL sub; LD R0,#3; JP dump; sub: LD R0,#2; RET T
    tests.append(_tc(
        name="sys_call_ret_basic",
        mnemonic="CALL",
        desc="CALL 0x0210; RET T: basic call/return",
        tags=["branch", "call", "stack"],
        code=[
            0x2100, 0x0001,  # LD R0, #1
            0x5F00, 0x0210,  # CALL 0x0210
            0x2100, 0x0003,  # LD R0, #3 (after return)
            0x5E08, 0x00C0,  # JP T, dump
            0x2100, 0x0002,  # LD R0, #2 (subroutine)
            0x9E08,          # RET T
        ],
        regs={0: 0x0000, 15: STACK_BASE},
    ))

    # CALR disp: 1101_dddddddddddd
    # Layout: LD R0,#1; CALR sub(+3); LD R0,#3; JP dump; sub: LD R0,#2; RET T
    # CALR at 0x0204, target = 0x0210
    # disp = (0x0210 - 0x0206) / 2 = 5
    tests.append(_tc(
        name="sys_calr_ret_basic",
        mnemonic="CALR",
        desc="CALR +5; RET T: relative call/return",
        tags=["branch", "call", "stack"],
        code=[
            0x2100, 0x0001,  # LD R0, #1
            0xD005,          # CALR +5 -> 0x0210
            0x2100, 0x0003,  # LD R0, #3 (after return)
            0x5E08, 0x00C0,  # JP T, dump
            0x2100, 0x0002,  # LD R0, #2 (subroutine)
            0x9E08,          # RET T
        ],
        regs={0: 0x0000, 15: STACK_BASE},
    ))

    # RET cc (conditional return) - return when condition met
    tests.append(_tc(
        name="sys_ret_cc_taken",
        mnemonic="RET",
        desc="RET Z: conditional return (Z=1, taken)",
        tags=["branch", "call", "stack"],
        code=[
            0x2100, 0x0001,  # LD R0, #1
            0x5F00, 0x0210,  # CALL 0x0210
            0x2100, 0x0003,  # LD R0, #3 (after return)
            0x5E08, 0x00C0,  # JP T, dump
            0x2100, 0x0002,  # LD R0, #2 (subroutine)
            0x9E06,          # RET Z (return if Z=1)
        ],
        regs={0: 0x0000, 15: STACK_BASE},
        fcw=fcw_with_flags(Z=1),
    ))

    return tests


# ============================================================================
# Category 33: Block load operations (16 tests)
# ============================================================================

def _block_load(op_byte, rs, rr, rd, repeat):
    """Encode block load: LDI/LDIR/LDD/LDDR and byte variants."""
    w1 = op_byte | (rs << 4)
    w2 = (rr << 8) | (rd << 4) | (0x00 if repeat else 0x08)
    return [w1, w2]


def generate_block_load_tests():
    """LDI, LDIR, LDD, LDDR + byte variants x 2 each."""
    tests = []

    # Word block: 0xBB01 (inc), 0xBB09 (dec)
    # Byte block: 0xBA01 (inc), 0xBA09 (dec)
    # Rs=R1 (src ptr), Rr=R2 (counter), Rd=R3 (dst ptr)

    # LDI (single step)
    tests.append(_tc(
        name="sys_ldi_single",
        mnemonic="LDI",
        desc="LDI @R3, @R1, R2: copy 1 word",
        tags=["block", "word"],
        code=_block_load(0xBB01, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={SRC_BUF: 0xAAAA},
    ))
    tests.append(_tc(
        name="sys_ldi_last",
        mnemonic="LDI",
        desc="LDI @R3, @R1, R2: counter=1",
        tags=["block", "word"],
        code=_block_load(0xBB01, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF, 2: 1, 3: DST_BUF},
        memory={SRC_BUF: 0xBBBB},
    ))

    # LDIR (repeat)
    tests.append(_tc(
        name="sys_ldir_3words",
        mnemonic="LDIR",
        desc="LDIR @R3, @R1, R2: copy 3 words",
        tags=["block", "word"],
        code=_block_load(0xBB01, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
    ))
    tests.append(_tc(
        name="sys_ldir_1word",
        mnemonic="LDIR",
        desc="LDIR @R3, @R1, R2: copy 1 word",
        tags=["block", "word"],
        code=_block_load(0xBB01, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF, 2: 1, 3: DST_BUF},
        memory={SRC_BUF: 0xDDDD},
    ))

    # LDD (single step, decrement)
    tests.append(_tc(
        name="sys_ldd_single",
        mnemonic="LDD",
        desc="LDD @R3, @R1, R2: copy 1 word (decrement)",
        tags=["block", "word"],
        code=_block_load(0xBB09, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF + 4, 2: 3, 3: DST_BUF + 4},
        memory={SRC_BUF + 4: 0xCCCC},
    ))
    tests.append(_tc(
        name="sys_ldd_last",
        mnemonic="LDD",
        desc="LDD @R3, @R1, R2: counter=1",
        tags=["block", "word"],
        code=_block_load(0xBB09, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF + 4, 2: 1, 3: DST_BUF + 4},
        memory={SRC_BUF + 4: 0xEEEE},
    ))

    # LDDR (repeat, decrement)
    tests.append(_tc(
        name="sys_lddr_3words",
        mnemonic="LDDR",
        desc="LDDR @R3, @R1, R2: copy 3 words (decrement)",
        tags=["block", "word"],
        code=_block_load(0xBB09, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF + 4, 2: 3, 3: DST_BUF + 4},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
    ))
    tests.append(_tc(
        name="sys_lddr_1word",
        mnemonic="LDDR",
        desc="LDDR @R3, @R1, R2: copy 1 word (decrement)",
        tags=["block", "word"],
        code=_block_load(0xBB09, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF, 2: 1, 3: DST_BUF},
        memory={SRC_BUF: 0xFFFF},
    ))

    # Byte variants: LDIB, LDIRB, LDDB, LDDRB (0xBA instead of 0xBB)
    tests.append(_tc(
        name="sys_ldib_single",
        mnemonic="LDIB",
        desc="LDIB @R3, @R1, R2: copy 1 byte",
        tags=["block", "byte"],
        code=_block_load(0xBA01, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={SRC_BUF: 0xAA00},
    ))
    tests.append(_tc(
        name="sys_ldirb_3bytes",
        mnemonic="LDIRB",
        desc="LDIRB @R3, @R1, R2: copy 3 bytes",
        tags=["block", "byte"],
        code=_block_load(0xBA01, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF, 2: 3, 3: DST_BUF},
        memory={SRC_BUF: 0x1122, SRC_BUF + 2: 0x3300},
    ))
    tests.append(_tc(
        name="sys_lddb_single",
        mnemonic="LDDB",
        desc="LDDB @R3, @R1, R2: copy 1 byte (decrement)",
        tags=["block", "byte"],
        code=_block_load(0xBA09, 1, 2, 3, repeat=False),
        regs={1: SRC_BUF + 2, 2: 3, 3: DST_BUF + 2},
        memory={SRC_BUF + 2: 0xBB00},
    ))
    tests.append(_tc(
        name="sys_lddrb_3bytes",
        mnemonic="LDDRB",
        desc="LDDRB @R3, @R1, R2: copy 3 bytes (decrement)",
        tags=["block", "byte"],
        code=_block_load(0xBA09, 1, 2, 3, repeat=True),
        regs={1: SRC_BUF + 2, 2: 3, 3: DST_BUF + 2},
        memory={SRC_BUF: 0x1122, SRC_BUF + 2: 0x3300},
    ))

    return tests


# ============================================================================
# Category 34: Block compare operations (16 tests)
# ============================================================================

def _block_cmp(op_byte, rs, rr, rd, cc):
    """Encode block compare: CPI/CPIR/CPD/CPDR and byte variants."""
    return [op_byte | (rs << 4), (rr << 8) | (rd << 4) | cc]


def generate_block_compare_tests():
    """CPI, CPIR, CPD, CPDR + byte variants x 2 each."""
    tests = []

    # Word compare: Rs=R1 (src ptr), Rr=R2 (counter), Rd=R0 (compare value)
    # CPI: 0xBB00, CPIR: 0xBB04, CPD: 0xBB08, CPDR: 0xBB0C
    # cc=6 (EQ), cc=14 (NE)

    # CPI match
    tests.append(_tc(
        name="sys_cpi_match",
        mnemonic="CPI",
        desc="CPI R0, @R1, R2, EQ: match found",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB00, 1, 2, 0, 6),
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1234},
    ))
    tests.append(_tc(
        name="sys_cpi_no_match",
        mnemonic="CPI",
        desc="CPI R0, @R1, R2, EQ: no match",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB00, 1, 2, 0, 6),
        regs={0: 0x1234, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x5678},
    ))

    # CPIR
    tests.append(_tc(
        name="sys_cpir_match_mid",
        mnemonic="CPIR",
        desc="CPIR R0, @R1, R2, EQ: match at element 2",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB04, 1, 2, 0, 6),
        regs={0: 0xAAAA, 1: SRC_BUF, 2: 4},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0xAAAA},
    ))
    tests.append(_tc(
        name="sys_cpir_no_match",
        mnemonic="CPIR",
        desc="CPIR R0, @R1, R2, EQ: exhausted",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB04, 1, 2, 0, 6),
        regs={0: 0xFFFF, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
    ))

    # CPD
    tests.append(_tc(
        name="sys_cpd_match",
        mnemonic="CPD",
        desc="CPD R0, @R1, R2, EQ: match (decrement)",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB08, 1, 2, 0, 6),
        regs={0: 0x1234, 1: SRC_BUF + 4, 2: 3},
        memory={SRC_BUF + 4: 0x1234},
    ))
    tests.append(_tc(
        name="sys_cpd_no_match",
        mnemonic="CPD",
        desc="CPD R0, @R1, R2, EQ: no match (decrement)",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB08, 1, 2, 0, 6),
        regs={0: 0x1234, 1: SRC_BUF + 4, 2: 3},
        memory={SRC_BUF + 4: 0x5678},
    ))

    # CPDR
    tests.append(_tc(
        name="sys_cpdr_match",
        mnemonic="CPDR",
        desc="CPDR R0, @R1, R2, EQ: match (repeat decrement)",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB0C, 1, 2, 0, 6),
        regs={0: 0x1111, 1: SRC_BUF + 4, 2: 3},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
    ))
    tests.append(_tc(
        name="sys_cpdr_no_match",
        mnemonic="CPDR",
        desc="CPDR R0, @R1, R2, EQ: exhausted (repeat decrement)",
        tags=["block", "compare", "word"],
        code=_block_cmp(0xBB0C, 1, 2, 0, 6),
        regs={0: 0xFFFF, 1: SRC_BUF + 4, 2: 3},
        memory={SRC_BUF: 0x1111, SRC_BUF + 2: 0x2222, SRC_BUF + 4: 0x3333},
    ))

    # Byte variants: CPIB, CPIRB, CPDB, CPDRB (0xBA instead of 0xBB)
    tests.append(_tc(
        name="sys_cpib_match",
        mnemonic="CPIB",
        desc="CPIB RH0, @R1, R2, EQ: byte match",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA00, 1, 2, 0, 6),
        regs={0: 0x1200, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1200},
    ))
    tests.append(_tc(
        name="sys_cpib_no_match",
        mnemonic="CPIB",
        desc="CPIB RH0, @R1, R2, EQ: byte no match",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA00, 1, 2, 0, 6),
        regs={0: 0x1200, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x5600},
    ))
    tests.append(_tc(
        name="sys_cpirb_match",
        mnemonic="CPIRB",
        desc="CPIRB RH0, @R1, R2, EQ: byte repeat match",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA04, 1, 2, 0, 6),
        regs={0: 0xAA00, 1: SRC_BUF, 2: 4},
        memory={SRC_BUF: 0x1100, SRC_BUF + 1: 0xAA00},
    ))
    tests.append(_tc(
        name="sys_cpirb_no_match",
        mnemonic="CPIRB",
        desc="CPIRB RH0, @R1, R2, EQ: byte exhausted",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA04, 1, 2, 0, 6),
        regs={0: 0xFF00, 1: SRC_BUF, 2: 3},
        memory={SRC_BUF: 0x1122, SRC_BUF + 2: 0x3300},
    ))
    tests.append(_tc(
        name="sys_cpdb_match",
        mnemonic="CPDB",
        desc="CPDB RH0, @R1, R2, EQ: byte match (decrement)",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA08, 1, 2, 0, 6),
        regs={0: 0x1200, 1: SRC_BUF + 2, 2: 3},
        memory={SRC_BUF + 2: 0x1200},
    ))
    tests.append(_tc(
        name="sys_cpdrb_no_match",
        mnemonic="CPDRB",
        desc="CPDRB RH0, @R1, R2, EQ: byte exhausted (repeat decrement)",
        tags=["block", "compare", "byte"],
        code=_block_cmp(0xBA0C, 1, 2, 0, 6),
        regs={0: 0xFF00, 1: SRC_BUF + 2, 2: 3},
        memory={SRC_BUF: 0x1122, SRC_BUF + 2: 0x3300},
    ))

    return tests


# ============================================================================
# Category 35: Block string compare (16 tests)
# ============================================================================

def generate_block_string_tests():
    """CPSI, CPSIR, CPSD, CPSDR + byte variants x 2 each.

    CPS compares memory @Rd against memory @Rs.
    Encoding: word1 = 0xBB0A | (Rs << 4) (increment) or 0xBB0E (repeat inc)
              word2 = (Rr << 8) | (Rd << 4) | cc
    Note: CPS sub-opcodes are 0x02/0x06/0x0A/0x0E for CPSI/CPSIR/CPSD/CPSDR.
    """
    # Rs=R1 (src ptr), Rr=R2 (counter), Rd=R3 (dst ptr)
    tests = []

    for mnem, w1_base, byte_base in [
        ('CPSI', 0xBB02, 0xBA02),
        ('CPSIR', 0xBB06, 0xBA06),
        ('CPSD', 0xBB0A, 0xBA0A),
        ('CPSDR', 0xBB0E, 0xBA0E),
    ]:
        is_dec = 'D' in mnem
        src_start = SRC_BUF + 4 if is_dec else SRC_BUF
        dst_start = DST_BUF + 4 if is_dec else DST_BUF

        # Word match
        tests.append(_tc(
            name=f"sys_{mnem.lower()}_match",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2, EQ: string match",
            tags=["block", "string", "word"],
            code=[w1_base | (1 << 4), (2 << 8) | (3 << 4) | 6],
            regs={1: src_start, 2: 3, 3: dst_start},
            memory={src_start: 0x1234, dst_start: 0x1234},
        ))
        # Word no match
        tests.append(_tc(
            name=f"sys_{mnem.lower()}_no_match",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2, EQ: string no match",
            tags=["block", "string", "word"],
            code=[w1_base | (1 << 4), (2 << 8) | (3 << 4) | 6],
            regs={1: src_start, 2: 3, 3: dst_start},
            memory={src_start: 0x1234, dst_start: 0x5678},
        ))

        # Byte variant
        bsfx = mnem + 'B' if not mnem.endswith('B') else mnem
        tests.append(_tc(
            name=f"sys_{mnem.lower()}b_match",
            mnemonic=bsfx,
            desc=f"{bsfx} @R3, @R1, R2, EQ: byte string match",
            tags=["block", "string", "byte"],
            code=[byte_base | (1 << 4), (2 << 8) | (3 << 4) | 6],
            regs={1: src_start, 2: 3, 3: dst_start},
            memory={src_start: 0x1200, dst_start: 0x1200},
        ))
        tests.append(_tc(
            name=f"sys_{mnem.lower()}b_no_match",
            mnemonic=bsfx,
            desc=f"{bsfx} @R3, @R1, R2, EQ: byte string no match",
            tags=["block", "string", "byte"],
            code=[byte_base | (1 << 4), (2 << 8) | (3 << 4) | 6],
            regs={1: src_start, 2: 3, 3: dst_start},
            memory={src_start: 0x1200, dst_start: 0x5600},
        ))

    return tests


# ============================================================================
# Category 36: Translate operations (16 tests)
# ============================================================================

def generate_translate_tests():
    """TRDB, TRIB, TRTDB, TRTIB + repeat variants x 2 each.

    TRDB @Rd, @Rs, Rr: translate and decrement byte
    Encoding: word1 = 0xB800 | (Rs << 4) | subop
              word2 = 0x0000 | (Rr << 8) | (Rd << 4) | 0
    Sub-opcodes: TRIB=0, TRDB=8, TRTIB=2, TRTDB=A, repeat: +4
    """
    # Rs=R1 (table ptr), Rr=R2 (counter), Rd=R3 (data ptr)
    tests = []

    # Build a simple 256-byte translation table at OPERAND_BASE
    # Table maps each byte to itself + 1 (mod 256)
    table_mem = {}
    for i in range(0, 256, 2):
        # Two bytes per word: high byte = translate(i), low byte = translate(i+1)
        table_mem[OPERAND_BASE + i] = (((i + 1) & 0xFF) << 8) | ((i + 2) & 0xFF)

    for mnem, subop in [
        ('TRIB', 0x00), ('TRIRB', 0x04),
        ('TRDB', 0x08), ('TRDRB', 0x0C),
    ]:
        is_dec = 'D' in mnem
        data_start = SRC_BUF + 2 if is_dec else SRC_BUF

        mem = dict(table_mem)
        mem[data_start] = 0x4100  # Source byte = 0x41 ('A')

        tests.append(_tc(
            name=f"sys_{mnem.lower()}_basic",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2: translate byte",
            tags=["translate", "byte"],
            code=[0xB800 | (1 << 4) | subop, (2 << 8) | (3 << 4)],
            regs={1: OPERAND_BASE, 2: 3, 3: data_start},
            memory=mem,
        ))

        mem2 = dict(table_mem)
        mem2[data_start] = 0x0000  # Source byte = 0x00

        tests.append(_tc(
            name=f"sys_{mnem.lower()}_zero",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2: translate zero byte",
            tags=["translate", "byte"],
            code=[0xB800 | (1 << 4) | subop, (2 << 8) | (3 << 4)],
            regs={1: OPERAND_BASE, 2: 3, 3: data_start},
            memory=mem2,
        ))

    # TRTIB, TRTDB (translate and test)
    for mnem, subop in [('TRTIB', 0x02), ('TRTDB', 0x0A)]:
        is_dec = 'D' in mnem
        data_start = SRC_BUF + 2 if is_dec else SRC_BUF

        mem = dict(table_mem)
        mem[data_start] = 0x4100

        tests.append(_tc(
            name=f"sys_{mnem.lower()}_basic",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2: translate and test",
            tags=["translate", "byte"],
            code=[0xB800 | (1 << 4) | subop, (2 << 8) | (3 << 4) | 0x0E],
            regs={1: OPERAND_BASE, 2: 3, 3: data_start},
            memory=mem,
        ))
        tests.append(_tc(
            name=f"sys_{mnem.lower()}_zero",
            mnemonic=mnem,
            desc=f"{mnem} @R3, @R1, R2: translate and test zero",
            tags=["translate", "byte"],
            code=[0xB800 | (1 << 4) | subop, (2 << 8) | (3 << 4) | 0x0E],
            regs={1: OPERAND_BASE, 2: 3, 3: data_start},
            memory=mem2,
        ))

    return tests


# ============================================================================
# Category 37: LDA/LDR (10 tests)
# ============================================================================

def generate_lda_ldr_tests():
    """LDA, LDAR, LDR, LDRB, LDRL x 2 each."""
    tests = []

    # LDA Rd, addr: 0x7600 | Rd, addr
    for sfx, addr in [('operand', OPERAND_BASE), ('src', SRC_BUF)]:
        tests.append(_tc(
            name=f"sys_lda_r_da_{sfx}",
            mnemonic="LDA",
            desc=f"LDA R0, 0x{addr:04X}",
            tags=["load", "address", "DA_mode"],
            code=[0x7600, addr],
            regs={0: 0x0000},
        ))

    # LDAR Rd, disp: 0x3400 | Rd, disp16
    # At CODE_BASE (0x0200), load address of OPERAND_BASE: disp = 0x0400-0x0200 = 0x0200
    for sfx, disp in [('fwd', 0x0200), ('near', 0x0010)]:
        tests.append(_tc(
            name=f"sys_ldar_r_{sfx}",
            mnemonic="LDAR",
            desc=f"LDAR R0, disp=0x{disp:04X}",
            tags=["load", "address", "RA_mode"],
            code=[0x3400, disp],
            regs={0: 0x0000},
        ))

    # LDR Rd, disp: 0x3100 | Rd, disp16
    for sfx, val in [('normal', 0x1234), ('zero', 0x0000)]:
        disp = OPERAND_BASE - CODE_BASE  # 0x0200
        tests.append(_tc(
            name=f"sys_ldr_r_{sfx}",
            mnemonic="LDR",
            desc=f"LDR R0, disp=0x{disp:04X}: [target]=0x{val:04X}",
            tags=["load", "word", "RA_mode"],
            code=[0x3100, disp],
            regs={0: 0x0000},
            memory={OPERAND_BASE: val},
        ))

    # LDRB Rbd, disp: 0x3000 | Rbd, disp16
    for sfx, val in [('normal', 0x42), ('zero', 0x00)]:
        disp = OPERAND_BASE - CODE_BASE
        tests.append(_tc(
            name=f"sys_ldrb_r_{sfx}",
            mnemonic="LDRB",
            desc=f"LDRB RH0, disp=0x{disp:04X}: [target]=0x{val:02X}xx",
            tags=["load", "byte", "RA_mode"],
            code=[0x3000, disp],
            regs={0: 0x0000},
            memory={OPERAND_BASE: val << 8},
        ))

    # LDRL RRd, disp: 0x3500 | RRd, disp16
    for sfx, val in [('normal', 0xDEADBEEF), ('zero', 0x00000000)]:
        disp = OPERAND_BASE - CODE_BASE
        tests.append(_tc(
            name=f"sys_ldrl_rr_{sfx}",
            mnemonic="LDRL",
            desc=f"LDRL RR0, disp=0x{disp:04X}: 0x{val:08X}",
            tags=["load", "long", "RA_mode"],
            code=[0x3500, disp],
            regs={0: 0, 1: 0},
            memory={OPERAND_BASE: (val >> 16) & 0xFFFF,
                    OPERAND_BASE + 2: val & 0xFFFF},
        ))

    return tests


# ============================================================================
# Category 38: LDCTL (4 tests)
# ============================================================================

def generate_ldctl_tests():
    """LDCTL FCW read/write, LDCTLB FLAGS read/write."""
    tests = []

    # LDCTL Rd, FCW: 0x7D01 | (Rd << 4) - read FCW into Rd
    tests.append(_tc(
        name="sys_ldctl_read_fcw",
        mnemonic="LDCTL",
        desc="LDCTL R0, FCW: read FCW into R0",
        tags=["control", "ldctl"],
        code=[0x7D01],  # LDCTL R0, FCW
        regs={0: 0x0000},
        fcw=fcw_with_flags(C=1, Z=1),
    ))

    # LDCTL FCW, Rs: 0x7D09 | (Rs << 4) - write Rs into FCW
    # Be careful: this changes FCW, which affects subsequent flag checks.
    # Set R0 to a known value and write it to FCW.
    tests.append(_tc(
        name="sys_ldctl_write_fcw",
        mnemonic="LDCTL",
        desc="LDCTL FCW, R0: write R0 into FCW",
        tags=["control", "ldctl"],
        code=[0x7D09],  # LDCTL FCW, R0
        regs={0: 0x40F0},  # System mode + all flags set
    ))

    # LDCTLB Rbd, FLAGS: 0x8C01 | (Rbd << 4) - read FLAGS byte
    tests.append(_tc(
        name="sys_ldctlb_read_flags",
        mnemonic="LDCTLB",
        desc="LDCTLB RH0, FLAGS: read flags byte",
        tags=["control", "ldctl", "byte"],
        code=[0x8C01],  # LDCTLB RH0, FLAGS
        regs={0: 0x0000},
        fcw=fcw_with_flags(C=1, S=1),
    ))

    # LDCTLB FLAGS, Rbs: 0x8C09 | (Rbs << 4) - write byte to FLAGS
    tests.append(_tc(
        name="sys_ldctlb_write_flags",
        mnemonic="LDCTLB",
        desc="LDCTLB FLAGS, RH0: write flags byte",
        tags=["control", "ldctl", "byte"],
        code=[0x8C09],  # LDCTLB FLAGS, RH0
        regs={0: 0xF000},  # All flags set in high byte
    ))

    return tests


# ============================================================================
# Public API
# ============================================================================

def generate_all_tests():
    """Generate all systematic tests (~850 total).

    Returns:
        list[TestCase]: all generated tests, no expected values set.
    """
    generators = [
        generate_word_alu_tests,         # 42
        generate_word_alu_mode_tests,    # 36
        generate_byte_alu_tests,         # 42
        generate_byte_alu_im_tests,      # 12
        generate_long_alu_tests,         # 15
        generate_carry_chain_tests,      # 40
        generate_unary_word_tests,       # 20
        generate_unary_byte_tests,       # 20
        generate_unary_long_tests,       # 4
        generate_shift_word_tests,       # 36
        generate_shift_byte_tests,       # 24
        generate_shift_long_tests,       # 16
        generate_dynamic_shift_tests,    # 48
        generate_rotate_word_tests,      # ~36
        generate_rotate_byte_tests,      # ~36
        generate_rotate_digit_tests,     # 6
        generate_bit_word_tests,         # 18
        generate_bit_byte_tests,         # 18
        generate_inc_dec_word_tests,     # 24
        generate_inc_dec_byte_tests,     # 24
        generate_inc_dec_mem_tests,      # 8
        generate_mult_div_tests,         # ~20
        generate_dab_tests,              # 6
        generate_sign_extend_tests,      # 9
        generate_flag_manip_tests,       # 48
        generate_tcc_tests,              # 64
        generate_load_tests,             # ~42
        generate_exchange_tests,         # 4
        generate_stack_tests,            # 8
        generate_branch_tests,           # 16
        generate_djnz_tests,            # 4
        generate_call_ret_tests,         # 3
        generate_block_load_tests,       # 16
        generate_block_compare_tests,    # 16
        generate_block_string_tests,     # ~32
        generate_translate_tests,        # ~16
        generate_lda_ldr_tests,          # 10
        generate_ldctl_tests,            # 4
    ]

    tests = []
    for gen in generators:
        tests.extend(gen())
    return tests
