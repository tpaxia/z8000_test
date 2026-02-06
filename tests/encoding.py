"""Z8000 instruction encoding helpers.

Builds opcodes from mnemonic parameters. Only covers commonly tested formats.
For complex instructions, encode manually in test definitions.
"""


def add_r_r(rd, rs):
    """ADD Rd, Rs (word) - opcode 0x81"""
    return [0x8100 | (rs << 4) | rd]


def addb_r_r(rd, rs):
    """ADDB Rbd, Rbs (byte) - opcode 0x80"""
    return [0x8000 | (rs << 4) | rd]


def add_r_imm(rd, imm):
    """ADD Rd, #imm - opcode 0x01"""
    return [0x0100 | rd, imm & 0xFFFF]


def addb_r_imm(rd, imm):
    """ADDB Rbd, #imm - opcode 0x00"""
    return [0x0000 | rd, (imm & 0xFF) << 8]


def add_r_ir(rd, rs):
    """ADD Rd, @Rs - opcode 0x01"""
    return [0x0100 | (rs << 4) | rd]


def add_r_da(rd, addr):
    """ADD Rd, addr - opcode 0x41"""
    return [0x4100 | rd, addr & 0xFFFF]


def sub_r_r(rd, rs):
    """SUB Rd, Rs (word) - opcode 0x83"""
    return [0x8300 | (rs << 4) | rd]


def subb_r_r(rd, rs):
    """SUBB Rbd, Rbs (byte) - opcode 0x82"""
    return [0x8200 | (rs << 4) | rd]


def sub_r_imm(rd, imm):
    """SUB Rd, #imm - opcode 0x03"""
    return [0x0300 | rd, imm & 0xFFFF]


def adc_r_r(rd, rs):
    """ADC Rd, Rs (word) - opcode 0xB5"""
    return [0xB500 | (rs << 4) | rd]


def sbc_r_r(rd, rs):
    """SBC Rd, Rs (word) - opcode 0xB7"""
    return [0xB700 | (rs << 4) | rd]


def and_r_r(rd, rs):
    """AND Rd, Rs (word) - opcode 0x87"""
    return [0x8700 | (rs << 4) | rd]


def or_r_r(rd, rs):
    """OR Rd, Rs (word) - opcode 0x85"""
    return [0x8500 | (rs << 4) | rd]


def xor_r_r(rd, rs):
    """XOR Rd, Rs (word) - opcode 0x89"""
    return [0x8900 | (rs << 4) | rd]


def cp_r_r(rd, rs):
    """CP Rd, Rs (word) - opcode 0x8B"""
    return [0x8B00 | (rs << 4) | rd]


def cp_r_imm(rd, imm):
    """CP Rd, #imm - opcode 0x0B"""
    return [0x0B00 | rd, imm & 0xFFFF]


def ld_r_r(rd, rs):
    """LD Rd, Rs (word) - opcode 0xA1"""
    return [0xA100 | (rs << 4) | rd]


def ld_r_imm(rd, imm):
    """LD Rd, #imm - opcode 0x21"""
    return [0x2100 | rd, imm & 0xFFFF]


def ld_r_ir(rd, rs):
    """LD Rd, @Rs - opcode 0x21"""
    return [0x2100 | (rs << 4) | rd]


def ld_r_da(rd, addr):
    """LD Rd, addr - opcode 0x61"""
    return [0x6100 | rd, addr & 0xFFFF]


def ld_da_r(rs, addr):
    """LD addr, Rs - opcode 0x6F"""
    return [0x6F00 | rs, addr & 0xFFFF]


def inc_r(rd, n=1):
    """INC Rd, #n - 10101001_Rddd_nnnn (n: 1-16 encoded as 0-15)"""
    return [0xA900 | (rd << 4) | (n - 1)]


def dec_r(rd, n=1):
    """DEC Rd, #n - 10101011_Rddd_nnnn (n: 1-16 encoded as 0-15)"""
    return [0xAB00 | (rd << 4) | (n - 1)]


def neg_r(rd):
    """NEG Rd - 10001101_Rddd_0010"""
    return [0x8D00 | (rd << 4) | 0x02]


def com_r(rd):
    """COM Rd - 10001101_Rddd_0000"""
    return [0x8D00 | (rd << 4) | 0x00]


def test_r(rd):
    """TEST Rd - 10001101_Rddd_0100"""
    return [0x8D00 | (rd << 4) | 0x04]


def clr_r(rd):
    """CLR Rd - 10001101_Rddd_1000"""
    return [0x8D00 | (rd << 4) | 0x08]


def nop():
    """NOP - 10001101_0000_0111"""
    return [0x8D07]


def setflg(flags):
    """SETFLG flags - 10001101_CZSV_0001"""
    return [0x8D01 | (flags << 4)]


def resflg(flags):
    """RESFLG flags - 10001101_CZSV_0011"""
    return [0x8D03 | (flags << 4)]


def comflg(flags):
    """COMFLG flags - 10001101_CZSV_0101"""
    return [0x8D05 | (flags << 4)]


def jp_cc(cc, addr):
    """JP cc, address - 01011110_0000_cccc + address"""
    return [0x5E00 | cc, addr & 0xFFFF]


def jr_cc(cc, disp):
    """JR cc, disp - disp is signed byte displacement in words."""
    return [0xE000 | (cc << 8) | (disp & 0xFF)]


def push_ir_r(rd, rs):
    """PUSH @Rd, Rs - 10010011_Rdnz_Rsss (Rd=stack ptr, Rs=source)"""
    return [0x9300 | (rd << 4) | rs]


def pop_r_ir(rd, rs):
    """POP Rd, @Rs - 10010111_Rsnz_Rddd (Rs=stack ptr, Rd=dest)"""
    return [0x9700 | (rs << 4) | rd]
