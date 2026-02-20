"""Systematic test generator for Z8000 instruction validation.

Generates TestCase objects WITHOUT expected values. Run against a reference
CPU (Z8001) to capture golden results, then compare against the DUT (Z8002).

Each test has an assembler-verified listing comment from z8k-coff-as.

Usage:
    from tests.gen_systematic import generate_all_tests
    tests = generate_all_tests()
"""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import (
    CODE_BASE, OPERAND_BASE, SRC_BUF, DST_BUF, STACK_BASE,
    preload_buffer,
)


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


def generate_all_tests():
    return [

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_zero
        #   0000: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_zero',
            mnemonic='ADD',
            desc='ADD R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_normal
        #   0100: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_normal',
            mnemonic='ADD',
            desc='ADD R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_carry
        #   0200: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_carry',
            mnemonic='ADD',
            desc='ADD R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_pos_ovf
        #   0300: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_pos_ovf',
            mnemonic='ADD',
            desc='ADD R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_neg_ovf
        #   0400: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_neg_ovf',
            mnemonic='ADD',
            desc='ADD R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_carry_ovf
        #   0500: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_carry_ovf',
            mnemonic='ADD',
            desc='ADD R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_r_allones
        #   0600: 8110                add	r0,r1
        _tc(
            name='sys_add_r_r_allones',
            mnemonic='ADD',
            desc='ADD R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8110],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_zero
        #   0700: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_zero',
            mnemonic='SUB',
            desc='SUB R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_normal
        #   0800: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_normal',
            mnemonic='SUB',
            desc='SUB R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_carry
        #   0900: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_carry',
            mnemonic='SUB',
            desc='SUB R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_pos_ovf
        #   0a00: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_pos_ovf',
            mnemonic='SUB',
            desc='SUB R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_neg_ovf
        #   0b00: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_neg_ovf',
            mnemonic='SUB',
            desc='SUB R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_carry_ovf
        #   0c00: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_carry_ovf',
            mnemonic='SUB',
            desc='SUB R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_r_allones
        #   0d00: 8310                sub	r0,r1
        _tc(
            name='sys_sub_r_r_allones',
            mnemonic='SUB',
            desc='SUB R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8310],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_zero
        #   0e00: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_zero',
            mnemonic='AND',
            desc='AND R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_normal
        #   0f00: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_normal',
            mnemonic='AND',
            desc='AND R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_carry
        #   1000: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_carry',
            mnemonic='AND',
            desc='AND R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_pos_ovf
        #   1100: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_pos_ovf',
            mnemonic='AND',
            desc='AND R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_neg_ovf
        #   1200: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_neg_ovf',
            mnemonic='AND',
            desc='AND R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_carry_ovf
        #   1300: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_carry_ovf',
            mnemonic='AND',
            desc='AND R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_r_allones
        #   1400: 8710                and	r0,r1
        _tc(
            name='sys_and_r_r_allones',
            mnemonic='AND',
            desc='AND R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8710],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_zero
        #   1500: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_zero',
            mnemonic='OR',
            desc='OR R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_normal
        #   1600: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_normal',
            mnemonic='OR',
            desc='OR R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_carry
        #   1700: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_carry',
            mnemonic='OR',
            desc='OR R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_pos_ovf
        #   1800: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_pos_ovf',
            mnemonic='OR',
            desc='OR R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_neg_ovf
        #   1900: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_neg_ovf',
            mnemonic='OR',
            desc='OR R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_carry_ovf
        #   1a00: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_carry_ovf',
            mnemonic='OR',
            desc='OR R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_r_allones
        #   1b00: 8510                or	r0,r1
        _tc(
            name='sys_or_r_r_allones',
            mnemonic='OR',
            desc='OR R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8510],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_zero
        #   1c00: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_zero',
            mnemonic='XOR',
            desc='XOR R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_normal
        #   1d00: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_normal',
            mnemonic='XOR',
            desc='XOR R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_carry
        #   1e00: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_carry',
            mnemonic='XOR',
            desc='XOR R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_pos_ovf
        #   1f00: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_pos_ovf',
            mnemonic='XOR',
            desc='XOR R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_neg_ovf
        #   2000: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_neg_ovf',
            mnemonic='XOR',
            desc='XOR R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_carry_ovf
        #   2100: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_carry_ovf',
            mnemonic='XOR',
            desc='XOR R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_r_allones
        #   2200: 8910                xor	r0,r1
        _tc(
            name='sys_xor_r_r_allones',
            mnemonic='XOR',
            desc='XOR R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8910],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_zero
        #   2300: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_zero',
            mnemonic='CP',
            desc='CP R0, R1: 0x0000, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_normal
        #   2400: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_normal',
            mnemonic='CP',
            desc='CP R0, R1: 0x1234, 0x5678',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_carry
        #   2500: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_carry',
            mnemonic='CP',
            desc='CP R0, R1: 0xFFFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_pos_ovf
        #   2600: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_pos_ovf',
            mnemonic='CP',
            desc='CP R0, R1: 0x7FFF, 0x0001',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0x7FFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_neg_ovf
        #   2700: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_neg_ovf',
            mnemonic='CP',
            desc='CP R0, R1: 0x8000, 0x8000',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_carry_ovf
        #   2800: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_carry_ovf',
            mnemonic='CP',
            desc='CP R0, R1: 0xFFFF, 0xFFFF',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_r_allones
        #   2900: 8b10                cp	r0,r1
        _tc(
            name='sys_cp_r_r_allones',
            mnemonic='CP',
            desc='CP R0, R1: 0xFFFF, 0x0000',
            tags=['word_alu', 'R_mode'],
            code=[0x8B10],
            regs={0: 0xFFFF, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_im_normal
        #   2a00: 0100 5678           add	r0,#0x5678
        _tc(
            name='sys_add_r_im_normal',
            mnemonic='ADD',
            desc='ADD R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0100, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_im_carry
        #   2b00: 0100 0001           add	r0,#0x1
        _tc(
            name='sys_add_r_im_carry',
            mnemonic='ADD',
            desc='ADD R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0100, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_im_normal
        #   2c00: 0300 5678           sub	r0,#0x5678
        _tc(
            name='sys_sub_r_im_normal',
            mnemonic='SUB',
            desc='SUB R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0300, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_im_carry
        #   2d00: 0300 0001           sub	r0,#0x1
        _tc(
            name='sys_sub_r_im_carry',
            mnemonic='SUB',
            desc='SUB R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0300, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_im_normal
        #   2e00: 0700 5678           and	r0,#0x5678
        _tc(
            name='sys_and_r_im_normal',
            mnemonic='AND',
            desc='AND R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0700, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_im_carry
        #   2f00: 0700 0001           and	r0,#0x1
        _tc(
            name='sys_and_r_im_carry',
            mnemonic='AND',
            desc='AND R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0700, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_im_normal
        #   3000: 0500 5678           or	r0,#0x5678
        _tc(
            name='sys_or_r_im_normal',
            mnemonic='OR',
            desc='OR R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0500, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_im_carry
        #   3100: 0500 0001           or	r0,#0x1
        _tc(
            name='sys_or_r_im_carry',
            mnemonic='OR',
            desc='OR R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0500, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_im_normal
        #   3200: 0900 5678           xor	r0,#0x5678
        _tc(
            name='sys_xor_r_im_normal',
            mnemonic='XOR',
            desc='XOR R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0900, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_im_carry
        #   3300: 0900 0001           xor	r0,#0x1
        _tc(
            name='sys_xor_r_im_carry',
            mnemonic='XOR',
            desc='XOR R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0900, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_im_normal
        #   3400: 0b00 5678           cp	r0,#0x5678
        _tc(
            name='sys_cp_r_im_normal',
            mnemonic='CP',
            desc='CP R0, #0x5678: R0=0x1234',
            tags=['word_alu', 'IM_mode'],
            code=[0x0B00, 0x5678],
            regs={0: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_im_carry
        #   3500: 0b00 0001           cp	r0,#0x1
        _tc(
            name='sys_cp_r_im_carry',
            mnemonic='CP',
            desc='CP R0, #0x0001: R0=0xFFFF',
            tags=['word_alu', 'IM_mode'],
            code=[0x0B00, 0x0001],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_ir_normal
        #   3600: 0120                add	r0,@r2
        _tc(
            name='sys_add_r_ir_normal',
            mnemonic='ADD',
            desc='ADD R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0120],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_ir_carry
        #   3700: 0120                add	r0,@r2
        _tc(
            name='sys_add_r_ir_carry',
            mnemonic='ADD',
            desc='ADD R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0120],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_ir_normal
        #   3800: 0320                sub	r0,@r2
        _tc(
            name='sys_sub_r_ir_normal',
            mnemonic='SUB',
            desc='SUB R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0320],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_ir_carry
        #   3900: 0320                sub	r0,@r2
        _tc(
            name='sys_sub_r_ir_carry',
            mnemonic='SUB',
            desc='SUB R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0320],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_ir_normal
        #   3a00: 0720                and	r0,@r2
        _tc(
            name='sys_and_r_ir_normal',
            mnemonic='AND',
            desc='AND R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0720],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_ir_carry
        #   3b00: 0720                and	r0,@r2
        _tc(
            name='sys_and_r_ir_carry',
            mnemonic='AND',
            desc='AND R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0720],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_ir_normal
        #   3c00: 0520                or	r0,@r2
        _tc(
            name='sys_or_r_ir_normal',
            mnemonic='OR',
            desc='OR R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0520],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_ir_carry
        #   3d00: 0520                or	r0,@r2
        _tc(
            name='sys_or_r_ir_carry',
            mnemonic='OR',
            desc='OR R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0520],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_ir_normal
        #   3e00: 0920                xor	r0,@r2
        _tc(
            name='sys_xor_r_ir_normal',
            mnemonic='XOR',
            desc='XOR R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0920],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_ir_carry
        #   3f00: 0920                xor	r0,@r2
        _tc(
            name='sys_xor_r_ir_carry',
            mnemonic='XOR',
            desc='XOR R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0920],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_ir_normal
        #   4000: 0b20                cp	r0,@r2
        _tc(
            name='sys_cp_r_ir_normal',
            mnemonic='CP',
            desc='CP R0, @R2: R0=0x1234, [R2]=0x5678',
            tags=['word_alu', 'IR_mode'],
            code=[0x0B20],
            regs={0: 0x1234, 2: 0x0400},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_ir_carry
        #   4100: 0b20                cp	r0,@r2
        _tc(
            name='sys_cp_r_ir_carry',
            mnemonic='CP',
            desc='CP R0, @R2: R0=0xFFFF, [R2]=0x0001',
            tags=['word_alu', 'IR_mode'],
            code=[0x0B20],
            regs={0: 0xFFFF, 2: 0x0400},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_da_normal
        #   4200: 4100 0400           add	r0,0x400
        _tc(
            name='sys_add_r_da_normal',
            mnemonic='ADD',
            desc='ADD R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4100, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_add_r_da_carry
        #   4300: 4100 0400           add	r0,0x400
        _tc(
            name='sys_add_r_da_carry',
            mnemonic='ADD',
            desc='ADD R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4100, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_da_normal
        #   4400: 4300 0400           sub	r0,0x400
        _tc(
            name='sys_sub_r_da_normal',
            mnemonic='SUB',
            desc='SUB R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4300, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sub_r_da_carry
        #   4500: 4300 0400           sub	r0,0x400
        _tc(
            name='sys_sub_r_da_carry',
            mnemonic='SUB',
            desc='SUB R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4300, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_da_normal
        #   4600: 4700 0400           and	r0,0x400
        _tc(
            name='sys_and_r_da_normal',
            mnemonic='AND',
            desc='AND R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4700, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_and_r_da_carry
        #   4700: 4700 0400           and	r0,0x400
        _tc(
            name='sys_and_r_da_carry',
            mnemonic='AND',
            desc='AND R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4700, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_da_normal
        #   4800: 4500 0400           or	r0,0x400
        _tc(
            name='sys_or_r_da_normal',
            mnemonic='OR',
            desc='OR R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4500, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_or_r_da_carry
        #   4900: 4500 0400           or	r0,0x400
        _tc(
            name='sys_or_r_da_carry',
            mnemonic='OR',
            desc='OR R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4500, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_da_normal
        #   4a00: 4900 0400           xor	r0,0x400
        _tc(
            name='sys_xor_r_da_normal',
            mnemonic='XOR',
            desc='XOR R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4900, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xor_r_da_carry
        #   4b00: 4900 0400           xor	r0,0x400
        _tc(
            name='sys_xor_r_da_carry',
            mnemonic='XOR',
            desc='XOR R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4900, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_da_normal
        #   4c00: 4b00 0400           cp	r0,0x400
        _tc(
            name='sys_cp_r_da_normal',
            mnemonic='CP',
            desc='CP R0, 0x0400: R0=0x1234, [DA]=0x5678',
            tags=['word_alu', 'DA_mode'],
            code=[0x4B00, 0x0400],
            regs={0: 0x1234},
            memory={0x0400: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cp_r_da_carry
        #   4d00: 4b00 0400           cp	r0,0x400
        _tc(
            name='sys_cp_r_da_carry',
            mnemonic='CP',
            desc='CP R0, 0x0400: R0=0xFFFF, [DA]=0x0001',
            tags=['word_alu', 'DA_mode'],
            code=[0x4B00, 0x0400],
            regs={0: 0xFFFF},
            memory={0x0400: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_zero
        #   4e00: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_zero',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_normal
        #   4f00: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_normal',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_carry
        #   5000: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_carry',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_pos_ovf
        #   5100: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_pos_ovf',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_neg_ovf
        #   5200: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_neg_ovf',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_carry_ovf
        #   5300: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_carry_ovf',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_r_allones
        #   5400: 8010                addb	rh0,rh1
        _tc(
            name='sys_addb_r_r_allones',
            mnemonic='ADDB',
            desc='ADDB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8010],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_zero
        #   5500: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_zero',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_normal
        #   5600: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_normal',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_carry
        #   5700: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_carry',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_pos_ovf
        #   5800: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_pos_ovf',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_neg_ovf
        #   5900: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_neg_ovf',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_carry_ovf
        #   5a00: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_carry_ovf',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_r_allones
        #   5b00: 8210                subb	rh0,rh1
        _tc(
            name='sys_subb_r_r_allones',
            mnemonic='SUBB',
            desc='SUBB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8210],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_zero
        #   5c00: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_zero',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_normal
        #   5d00: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_normal',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_carry
        #   5e00: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_carry',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_pos_ovf
        #   5f00: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_pos_ovf',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_neg_ovf
        #   6000: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_neg_ovf',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_carry_ovf
        #   6100: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_carry_ovf',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_r_allones
        #   6200: 8610                andb	rh0,rh1
        _tc(
            name='sys_andb_r_r_allones',
            mnemonic='ANDB',
            desc='ANDB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8610],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_zero
        #   6300: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_zero',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_normal
        #   6400: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_normal',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_carry
        #   6500: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_carry',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_pos_ovf
        #   6600: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_pos_ovf',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_neg_ovf
        #   6700: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_neg_ovf',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_carry_ovf
        #   6800: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_carry_ovf',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_r_allones
        #   6900: 8410                orb	rh0,rh1
        _tc(
            name='sys_orb_r_r_allones',
            mnemonic='ORB',
            desc='ORB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8410],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_zero
        #   6a00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_zero',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_normal
        #   6b00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_normal',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_carry
        #   6c00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_carry',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_pos_ovf
        #   6d00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_pos_ovf',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_neg_ovf
        #   6e00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_neg_ovf',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_carry_ovf
        #   6f00: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_carry_ovf',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_r_allones
        #   7000: 8810                xorb	rh0,rh1
        _tc(
            name='sys_xorb_r_r_allones',
            mnemonic='XORB',
            desc='XORB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8810],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_zero
        #   7100: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_zero',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0x00, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_normal
        #   7200: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_normal',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0x12, 0x34',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_carry
        #   7300: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_carry',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0xFF, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_pos_ovf
        #   7400: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_pos_ovf',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0x7F, 0x01',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0x7F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_neg_ovf
        #   7500: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_neg_ovf',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0x80, 0x80',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0x8000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_carry_ovf
        #   7600: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_carry_ovf',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0xFF, 0xFF',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_r_allones
        #   7700: 8a10                cpb	rh0,rh1
        _tc(
            name='sys_cpb_r_r_allones',
            mnemonic='CPB',
            desc='CPB RH0, RH1: 0xFF, 0x00',
            tags=['byte_alu', 'R_mode'],
            code=[0x8A10],
            regs={0: 0xFF00, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_im_normal
        #   0200: 0000 3434           addb	rh0,#0x34
        _tc(
            name='sys_addb_r_im_normal',
            mnemonic='ADDB',
            desc='ADDB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0000, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addb_r_im_carry
        #   0210: 0000 0101           addb	rh0,#0x01
        _tc(
            name='sys_addb_r_im_carry',
            mnemonic='ADDB',
            desc='ADDB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0000, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_im_normal
        #   0220: 0200 3434           subb	rh0,#0x34
        _tc(
            name='sys_subb_r_im_normal',
            mnemonic='SUBB',
            desc='SUBB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0200, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subb_r_im_carry
        #   0230: 0200 0101           subb	rh0,#0x01
        _tc(
            name='sys_subb_r_im_carry',
            mnemonic='SUBB',
            desc='SUBB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0200, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_im_normal
        #   0240: 0600 3434           andb	rh0,#0x34
        _tc(
            name='sys_andb_r_im_normal',
            mnemonic='ANDB',
            desc='ANDB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0600, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_andb_r_im_carry
        #   0250: 0600 0101           andb	rh0,#0x01
        _tc(
            name='sys_andb_r_im_carry',
            mnemonic='ANDB',
            desc='ANDB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0600, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_im_normal
        #   0260: 0400 3434           orb	rh0,#0x34
        _tc(
            name='sys_orb_r_im_normal',
            mnemonic='ORB',
            desc='ORB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0400, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_orb_r_im_carry
        #   0270: 0400 0101           orb	rh0,#0x01
        _tc(
            name='sys_orb_r_im_carry',
            mnemonic='ORB',
            desc='ORB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0400, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_im_normal
        #   0280: 0800 3434           xorb	rh0,#0x34
        _tc(
            name='sys_xorb_r_im_normal',
            mnemonic='XORB',
            desc='XORB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0800, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_xorb_r_im_carry
        #   0290: 0800 0101           xorb	rh0,#0x01
        _tc(
            name='sys_xorb_r_im_carry',
            mnemonic='XORB',
            desc='XORB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0800, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_im_normal
        #   02a0: 0a00 3434           cpb	rh0,#0x34
        _tc(
            name='sys_cpb_r_im_normal',
            mnemonic='CPB',
            desc='CPB RH0, #0x34: RH0=0x12',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0A00, 0x3434],
            regs={0: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpb_r_im_carry
        #   02b0: 0a00 0101           cpb	rh0,#0x01
        _tc(
            name='sys_cpb_r_im_carry',
            mnemonic='CPB',
            desc='CPB RH0, #0x01: RH0=0xFF',
            tags=['byte_alu', 'IM_mode'],
            code=[0x0A00, 0x0101],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addl_rr_rr_zero
        #   8400: 9620                addl	rr0,rr2
        _tc(
            name='sys_addl_rr_rr_zero',
            mnemonic='ADDL',
            desc='ADDL RR0, RR2: 0x00000000, 0x00000000',
            tags=['long_alu', 'R_mode'],
            code=[0x9620],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addl_rr_rr_normal
        #   8500: 9620                addl	rr0,rr2
        _tc(
            name='sys_addl_rr_rr_normal',
            mnemonic='ADDL',
            desc='ADDL RR0, RR2: 0x12345678, 0x9ABCDEF0',
            tags=['long_alu', 'R_mode'],
            code=[0x9620],
            regs={0: 0x1234, 1: 0x5678, 2: 0x9ABC, 3: 0xDEF0},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addl_rr_rr_carry
        #   8600: 9620                addl	rr0,rr2
        _tc(
            name='sys_addl_rr_rr_carry',
            mnemonic='ADDL',
            desc='ADDL RR0, RR2: 0xFFFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9620],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addl_rr_rr_pos_ovf
        #   8700: 9620                addl	rr0,rr2
        _tc(
            name='sys_addl_rr_rr_pos_ovf',
            mnemonic='ADDL',
            desc='ADDL RR0, RR2: 0x7FFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9620],
            regs={0: 0x7FFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_addl_rr_rr_max
        #   8800: 9620                addl	rr0,rr2
        _tc(
            name='sys_addl_rr_rr_max',
            mnemonic='ADDL',
            desc='ADDL RR0, RR2: 0xFFFFFFFF, 0xFFFFFFFF',
            tags=['long_alu', 'R_mode'],
            code=[0x9620],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0xFFFF, 3: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subl_rr_rr_zero
        #   8900: 9220                subl	rr0,rr2
        _tc(
            name='sys_subl_rr_rr_zero',
            mnemonic='SUBL',
            desc='SUBL RR0, RR2: 0x00000000, 0x00000000',
            tags=['long_alu', 'R_mode'],
            code=[0x9220],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subl_rr_rr_normal
        #   8a00: 9220                subl	rr0,rr2
        _tc(
            name='sys_subl_rr_rr_normal',
            mnemonic='SUBL',
            desc='SUBL RR0, RR2: 0x12345678, 0x9ABCDEF0',
            tags=['long_alu', 'R_mode'],
            code=[0x9220],
            regs={0: 0x1234, 1: 0x5678, 2: 0x9ABC, 3: 0xDEF0},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subl_rr_rr_carry
        #   8b00: 9220                subl	rr0,rr2
        _tc(
            name='sys_subl_rr_rr_carry',
            mnemonic='SUBL',
            desc='SUBL RR0, RR2: 0xFFFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9220],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subl_rr_rr_pos_ovf
        #   8c00: 9220                subl	rr0,rr2
        _tc(
            name='sys_subl_rr_rr_pos_ovf',
            mnemonic='SUBL',
            desc='SUBL RR0, RR2: 0x7FFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9220],
            regs={0: 0x7FFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_subl_rr_rr_max
        #   8d00: 9220                subl	rr0,rr2
        _tc(
            name='sys_subl_rr_rr_max',
            mnemonic='SUBL',
            desc='SUBL RR0, RR2: 0xFFFFFFFF, 0xFFFFFFFF',
            tags=['long_alu', 'R_mode'],
            code=[0x9220],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0xFFFF, 3: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpl_rr_rr_zero
        #   8e00: 9020                cpl	rr0,rr2
        _tc(
            name='sys_cpl_rr_rr_zero',
            mnemonic='CPL',
            desc='CPL RR0, RR2: 0x00000000, 0x00000000',
            tags=['long_alu', 'R_mode'],
            code=[0x9020],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpl_rr_rr_normal
        #   8f00: 9020                cpl	rr0,rr2
        _tc(
            name='sys_cpl_rr_rr_normal',
            mnemonic='CPL',
            desc='CPL RR0, RR2: 0x12345678, 0x9ABCDEF0',
            tags=['long_alu', 'R_mode'],
            code=[0x9020],
            regs={0: 0x1234, 1: 0x5678, 2: 0x9ABC, 3: 0xDEF0},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpl_rr_rr_carry
        #   9000: 9020                cpl	rr0,rr2
        _tc(
            name='sys_cpl_rr_rr_carry',
            mnemonic='CPL',
            desc='CPL RR0, RR2: 0xFFFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9020],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpl_rr_rr_pos_ovf
        #   9100: 9020                cpl	rr0,rr2
        _tc(
            name='sys_cpl_rr_rr_pos_ovf',
            mnemonic='CPL',
            desc='CPL RR0, RR2: 0x7FFFFFFF, 0x00000001',
            tags=['long_alu', 'R_mode'],
            code=[0x9020],
            regs={0: 0x7FFF, 1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpl_rr_rr_max
        #   9200: 9020                cpl	rr0,rr2
        _tc(
            name='sys_cpl_rr_rr_max',
            mnemonic='CPL',
            desc='CPL RR0, RR2: 0xFFFFFFFF, 0xFFFFFFFF',
            tags=['long_alu', 'R_mode'],
            code=[0x9020],
            regs={0: 0xFFFF, 1: 0xFFFF, 2: 0xFFFF, 3: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_zero_c0
        #   9300: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_zero_c0',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x0000, 0x0000, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_zero_c1
        #   9400: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_zero_c1',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x0000, 0x0000, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x0000, 1: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_normal_c0
        #   9500: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_normal_c0',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x1234, 0x5678, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_normal_c1
        #   9600: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_normal_c1',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x1234, 0x5678, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x1234, 1: 0x5678},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_carry_c0
        #   9700: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_carry_c0',
            mnemonic='ADC',
            desc='ADC R0, R1: 0xFFFF, 0x0001, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_carry_c1
        #   9800: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_carry_c1',
            mnemonic='ADC',
            desc='ADC R0, R1: 0xFFFF, 0x0001, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0xFFFF, 1: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_max_c0
        #   9900: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_max_c0',
            mnemonic='ADC',
            desc='ADC R0, R1: 0xFFFF, 0xFFFF, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_max_c1
        #   9a00: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_max_c1',
            mnemonic='ADC',
            desc='ADC R0, R1: 0xFFFF, 0xFFFF, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0xFFFF, 1: 0xFFFF},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_half_c0
        #   9b00: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_half_c0',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x000F, 0x0001, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x000F, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adc_r_r_half_c1
        #   9c00: b510                adc	r0,r1
        _tc(
            name='sys_adc_r_r_half_c1',
            mnemonic='ADC',
            desc='ADC R0, R1: 0x000F, 0x0001, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB510],
            regs={0: 0x000F, 1: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_zero_c0
        #   9d00: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_zero_c0',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x0000, 0x0000, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_zero_c1
        #   9e00: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_zero_c1',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x0000, 0x0000, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x0000, 1: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_normal_c0
        #   9f00: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_normal_c0',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x1234, 0x5678, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_normal_c1
        #   a000: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_normal_c1',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x1234, 0x5678, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x1234, 1: 0x5678},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_carry_c0
        #   a100: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_carry_c0',
            mnemonic='SBC',
            desc='SBC R0, R1: 0xFFFF, 0x0001, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0xFFFF, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_carry_c1
        #   a200: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_carry_c1',
            mnemonic='SBC',
            desc='SBC R0, R1: 0xFFFF, 0x0001, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0xFFFF, 1: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_max_c0
        #   a300: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_max_c0',
            mnemonic='SBC',
            desc='SBC R0, R1: 0xFFFF, 0xFFFF, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_max_c1
        #   a400: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_max_c1',
            mnemonic='SBC',
            desc='SBC R0, R1: 0xFFFF, 0xFFFF, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0xFFFF, 1: 0xFFFF},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_half_c0
        #   a500: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_half_c0',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x000F, 0x0001, c0',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x000F, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbc_r_r_half_c1
        #   a600: b710                sbc	r0,r1
        _tc(
            name='sys_sbc_r_r_half_c1',
            mnemonic='SBC',
            desc='SBC R0, R1: 0x000F, 0x0001, c1',
            tags=['carry_chain', 'word', 'R_mode'],
            code=[0xB710],
            regs={0: 0x000F, 1: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_zero_c0
        #   a700: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_zero_c0',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x00, 0x00, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_zero_c1
        #   a800: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_zero_c1',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x00, 0x00, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x0000, 1: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_normal_c0
        #   a900: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_normal_c0',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x12, 0x34, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_normal_c1
        #   aa00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_normal_c1',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x12, 0x34, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x1200, 1: 0x3400},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_carry_c0
        #   ab00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_carry_c0',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0xFF, 0x01, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_carry_c1
        #   ac00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_carry_c1',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0xFF, 0x01, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0xFF00, 1: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_max_c0
        #   ad00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_max_c0',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0xFF, 0xFF, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_max_c1
        #   ae00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_max_c1',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0xFF, 0xFF, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0xFF00, 1: 0xFF00},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_half_c0
        #   af00: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_half_c0',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x0F, 0x01, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x0F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_adcb_r_r_half_c1
        #   b000: b410                adcb	rh0,rh1
        _tc(
            name='sys_adcb_r_r_half_c1',
            mnemonic='ADCB',
            desc='ADCB RH0, RH1: 0x0F, 0x01, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB410],
            regs={0: 0x0F00, 1: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_zero_c0
        #   b100: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_zero_c0',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x00, 0x00, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_zero_c1
        #   b200: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_zero_c1',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x00, 0x00, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x0000, 1: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_normal_c0
        #   b300: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_normal_c0',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x12, 0x34, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x1200, 1: 0x3400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_normal_c1
        #   b400: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_normal_c1',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x12, 0x34, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x1200, 1: 0x3400},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_carry_c0
        #   b500: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_carry_c0',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0xFF, 0x01, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0xFF00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_carry_c1
        #   b600: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_carry_c1',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0xFF, 0x01, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0xFF00, 1: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_max_c0
        #   b700: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_max_c0',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0xFF, 0xFF, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0xFF00, 1: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_max_c1
        #   b800: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_max_c1',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0xFF, 0xFF, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0xFF00, 1: 0xFF00},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_half_c0
        #   b900: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_half_c0',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x0F, 0x01, c0',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x0F00, 1: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sbcb_r_r_half_c1
        #   ba00: b610                sbcb	rh0,rh1
        _tc(
            name='sys_sbcb_r_r_half_c1',
            mnemonic='SBCB',
            desc='SBCB RH0, RH1: 0x0F, 0x01, c1',
            tags=['carry_chain', 'byte', 'R_mode'],
            code=[0xB610],
            regs={0: 0x0F00, 1: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_neg_r_zero
        #   bb00: 8d02                neg	r0
        _tc(
            name='sys_neg_r_zero',
            mnemonic='NEG',
            desc='NEG R0: 0x0000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D02],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_neg_r_one
        #   bc00: 8d02                neg	r0
        _tc(
            name='sys_neg_r_one',
            mnemonic='NEG',
            desc='NEG R0: 0x0001',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D02],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_neg_r_pos_max
        #   bd00: 8d02                neg	r0
        _tc(
            name='sys_neg_r_pos_max',
            mnemonic='NEG',
            desc='NEG R0: 0x7FFF',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D02],
            regs={0: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_neg_r_neg_min
        #   be00: 8d02                neg	r0
        _tc(
            name='sys_neg_r_neg_min',
            mnemonic='NEG',
            desc='NEG R0: 0x8000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D02],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_com_r_zero
        #   bf00: 8d00                com	r0
        _tc(
            name='sys_com_r_zero',
            mnemonic='COM',
            desc='COM R0: 0x0000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_com_r_one
        #   c000: 8d00                com	r0
        _tc(
            name='sys_com_r_one',
            mnemonic='COM',
            desc='COM R0: 0x0001',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D00],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_com_r_pos_max
        #   c100: 8d00                com	r0
        _tc(
            name='sys_com_r_pos_max',
            mnemonic='COM',
            desc='COM R0: 0x7FFF',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D00],
            regs={0: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_com_r_neg_min
        #   c200: 8d00                com	r0
        _tc(
            name='sys_com_r_neg_min',
            mnemonic='COM',
            desc='COM R0: 0x8000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D00],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clr_r_zero
        #   c300: 8d08                clr	r0
        _tc(
            name='sys_clr_r_zero',
            mnemonic='CLR',
            desc='CLR R0: 0x0000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clr_r_one
        #   c400: 8d08                clr	r0
        _tc(
            name='sys_clr_r_one',
            mnemonic='CLR',
            desc='CLR R0: 0x0001',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D08],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clr_r_pos_max
        #   c500: 8d08                clr	r0
        _tc(
            name='sys_clr_r_pos_max',
            mnemonic='CLR',
            desc='CLR R0: 0x7FFF',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D08],
            regs={0: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clr_r_neg_min
        #   c600: 8d08                clr	r0
        _tc(
            name='sys_clr_r_neg_min',
            mnemonic='CLR',
            desc='CLR R0: 0x8000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D08],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_test_r_zero
        #   c700: 8d04                test	r0
        _tc(
            name='sys_test_r_zero',
            mnemonic='TEST',
            desc='TEST R0: 0x0000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D04],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_test_r_one
        #   c800: 8d04                test	r0
        _tc(
            name='sys_test_r_one',
            mnemonic='TEST',
            desc='TEST R0: 0x0001',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D04],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_test_r_pos_max
        #   c900: 8d04                test	r0
        _tc(
            name='sys_test_r_pos_max',
            mnemonic='TEST',
            desc='TEST R0: 0x7FFF',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D04],
            regs={0: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_test_r_neg_min
        #   ca00: 8d04                test	r0
        _tc(
            name='sys_test_r_neg_min',
            mnemonic='TEST',
            desc='TEST R0: 0x8000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D04],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tset_r_zero
        #   cb00: 8d06                tset	r0
        _tc(
            name='sys_tset_r_zero',
            mnemonic='TSET',
            desc='TSET R0: 0x0000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D06],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tset_r_one
        #   cc00: 8d06                tset	r0
        _tc(
            name='sys_tset_r_one',
            mnemonic='TSET',
            desc='TSET R0: 0x0001',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D06],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tset_r_pos_max
        #   cd00: 8d06                tset	r0
        _tc(
            name='sys_tset_r_pos_max',
            mnemonic='TSET',
            desc='TSET R0: 0x7FFF',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D06],
            regs={0: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tset_r_neg_min
        #   ce00: 8d06                tset	r0
        _tc(
            name='sys_tset_r_neg_min',
            mnemonic='TSET',
            desc='TSET R0: 0x8000',
            tags=['unary', 'word', 'R_mode'],
            code=[0x8D06],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_negb_r_zero
        #   cf00: 8c02                negb	rh0
        _tc(
            name='sys_negb_r_zero',
            mnemonic='NEGB',
            desc='NEGB RH0: 0x00',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C02],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_negb_r_one
        #   d000: 8c02                negb	rh0
        _tc(
            name='sys_negb_r_one',
            mnemonic='NEGB',
            desc='NEGB RH0: 0x01',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C02],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_negb_r_pos_max
        #   d100: 8c02                negb	rh0
        _tc(
            name='sys_negb_r_pos_max',
            mnemonic='NEGB',
            desc='NEGB RH0: 0x7F',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C02],
            regs={0: 0x7F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_negb_r_neg_min
        #   d200: 8c02                negb	rh0
        _tc(
            name='sys_negb_r_neg_min',
            mnemonic='NEGB',
            desc='NEGB RH0: 0x80',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C02],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comb_r_zero
        #   d300: 8c00                comb	rh0
        _tc(
            name='sys_comb_r_zero',
            mnemonic='COMB',
            desc='COMB RH0: 0x00',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comb_r_one
        #   d400: 8c00                comb	rh0
        _tc(
            name='sys_comb_r_one',
            mnemonic='COMB',
            desc='COMB RH0: 0x01',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C00],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comb_r_pos_max
        #   d500: 8c00                comb	rh0
        _tc(
            name='sys_comb_r_pos_max',
            mnemonic='COMB',
            desc='COMB RH0: 0x7F',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C00],
            regs={0: 0x7F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comb_r_neg_min
        #   d600: 8c00                comb	rh0
        _tc(
            name='sys_comb_r_neg_min',
            mnemonic='COMB',
            desc='COMB RH0: 0x80',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C00],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clrb_r_zero
        #   d700: 8c08                clrb	rh0
        _tc(
            name='sys_clrb_r_zero',
            mnemonic='CLRB',
            desc='CLRB RH0: 0x00',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clrb_r_one
        #   d800: 8c08                clrb	rh0
        _tc(
            name='sys_clrb_r_one',
            mnemonic='CLRB',
            desc='CLRB RH0: 0x01',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C08],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clrb_r_pos_max
        #   d900: 8c08                clrb	rh0
        _tc(
            name='sys_clrb_r_pos_max',
            mnemonic='CLRB',
            desc='CLRB RH0: 0x7F',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C08],
            regs={0: 0x7F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_clrb_r_neg_min
        #   da00: 8c08                clrb	rh0
        _tc(
            name='sys_clrb_r_neg_min',
            mnemonic='CLRB',
            desc='CLRB RH0: 0x80',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C08],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testb_r_zero
        #   db00: 8c04                testb	rh0
        _tc(
            name='sys_testb_r_zero',
            mnemonic='TESTB',
            desc='TESTB RH0: 0x00',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C04],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testb_r_one
        #   dc00: 8c04                testb	rh0
        _tc(
            name='sys_testb_r_one',
            mnemonic='TESTB',
            desc='TESTB RH0: 0x01',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C04],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testb_r_pos_max
        #   dd00: 8c04                testb	rh0
        _tc(
            name='sys_testb_r_pos_max',
            mnemonic='TESTB',
            desc='TESTB RH0: 0x7F',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C04],
            regs={0: 0x7F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testb_r_neg_min
        #   de00: 8c04                testb	rh0
        _tc(
            name='sys_testb_r_neg_min',
            mnemonic='TESTB',
            desc='TESTB RH0: 0x80',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C04],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tsetb_r_zero
        #   df00: 8c06                tsetb	rh0
        _tc(
            name='sys_tsetb_r_zero',
            mnemonic='TSETB',
            desc='TSETB RH0: 0x00',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C06],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tsetb_r_one
        #   e000: 8c06                tsetb	rh0
        _tc(
            name='sys_tsetb_r_one',
            mnemonic='TSETB',
            desc='TSETB RH0: 0x01',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C06],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tsetb_r_pos_max
        #   e100: 8c06                tsetb	rh0
        _tc(
            name='sys_tsetb_r_pos_max',
            mnemonic='TSETB',
            desc='TSETB RH0: 0x7F',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C06],
            regs={0: 0x7F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tsetb_r_neg_min
        #   e200: 8c06                tsetb	rh0
        _tc(
            name='sys_tsetb_r_neg_min',
            mnemonic='TSETB',
            desc='TSETB RH0: 0x80',
            tags=['unary', 'byte', 'R_mode'],
            code=[0x8C06],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testl_rr_zero
        #   e300: 9c08                testl	rr0
        _tc(
            name='sys_testl_rr_zero',
            mnemonic='TESTL',
            desc='TESTL RR0: 0x00000000',
            tags=['unary', 'long', 'R_mode'],
            code=[0x9C08],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testl_rr_one
        #   e400: 9c08                testl	rr0
        _tc(
            name='sys_testl_rr_one',
            mnemonic='TESTL',
            desc='TESTL RR0: 0x00000001',
            tags=['unary', 'long', 'R_mode'],
            code=[0x9C08],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testl_rr_pos_max
        #   e500: 9c08                testl	rr0
        _tc(
            name='sys_testl_rr_pos_max',
            mnemonic='TESTL',
            desc='TESTL RR0: 0x7FFFFFFF',
            tags=['unary', 'long', 'R_mode'],
            code=[0x9C08],
            regs={0: 0x7FFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_testl_rr_neg_min
        #   e600: 9c08                testl	rr0
        _tc(
            name='sys_testl_rr_neg_min',
            mnemonic='TESTL',
            desc='TESTL RR0: 0x80000000',
            tags=['unary', 'long', 'R_mode'],
            code=[0x9C08],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_one_n1
        #   e700: b301 0001           sll	r0,#0x1
        _tc(
            name='sys_sll_r_one_n1',
            mnemonic='SLL',
            desc='SLL R0, #1: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0001],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_one_n1
        #   e800: b301 ffff           srl	r0,#0x1
        _tc(
            name='sys_srl_r_one_n1',
            mnemonic='SRL',
            desc='SRL R0, #1: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFF],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_one_n1
        #   e900: b309 0001           sla	r0,#0x1
        _tc(
            name='sys_sla_r_one_n1',
            mnemonic='SLA',
            desc='SLA R0, #1: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0001],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_one_n1
        #   ea00: b309 ffff           sra	r0,#0x1
        _tc(
            name='sys_sra_r_one_n1',
            mnemonic='SRA',
            desc='SRA R0, #1: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFF],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_one_n4
        #   eb00: b301 0004           sll	r0,#0x4
        _tc(
            name='sys_sll_r_one_n4',
            mnemonic='SLL',
            desc='SLL R0, #4: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0004],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_one_n4
        #   ec00: b301 fffc           srl	r0,#0x4
        _tc(
            name='sys_srl_r_one_n4',
            mnemonic='SRL',
            desc='SRL R0, #4: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFC],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_one_n4
        #   ed00: b309 0004           sla	r0,#0x4
        _tc(
            name='sys_sla_r_one_n4',
            mnemonic='SLA',
            desc='SLA R0, #4: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0004],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_one_n4
        #   ee00: b309 fffc           sra	r0,#0x4
        _tc(
            name='sys_sra_r_one_n4',
            mnemonic='SRA',
            desc='SRA R0, #4: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFC],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_one_n8
        #   ef00: b301 0008           sll	r0,#0x8
        _tc(
            name='sys_sll_r_one_n8',
            mnemonic='SLL',
            desc='SLL R0, #8: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0008],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_one_n8
        #   f000: b301 fff8           srl	r0,#0x8
        _tc(
            name='sys_srl_r_one_n8',
            mnemonic='SRL',
            desc='SRL R0, #8: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFF8],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_one_n8
        #   f100: b309 0008           sla	r0,#0x8
        _tc(
            name='sys_sla_r_one_n8',
            mnemonic='SLA',
            desc='SLA R0, #8: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0008],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_one_n8
        #   f200: b309 fff8           sra	r0,#0x8
        _tc(
            name='sys_sra_r_one_n8',
            mnemonic='SRA',
            desc='SRA R0, #8: 0x0001',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFF8],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_msb_n1
        #   f300: b301 0001           sll	r0,#0x1
        _tc(
            name='sys_sll_r_msb_n1',
            mnemonic='SLL',
            desc='SLL R0, #1: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0001],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_msb_n1
        #   f400: b301 ffff           srl	r0,#0x1
        _tc(
            name='sys_srl_r_msb_n1',
            mnemonic='SRL',
            desc='SRL R0, #1: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFF],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_msb_n1
        #   f500: b309 0001           sla	r0,#0x1
        _tc(
            name='sys_sla_r_msb_n1',
            mnemonic='SLA',
            desc='SLA R0, #1: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0001],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_msb_n1
        #   f600: b309 ffff           sra	r0,#0x1
        _tc(
            name='sys_sra_r_msb_n1',
            mnemonic='SRA',
            desc='SRA R0, #1: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFF],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_msb_n4
        #   f700: b301 0004           sll	r0,#0x4
        _tc(
            name='sys_sll_r_msb_n4',
            mnemonic='SLL',
            desc='SLL R0, #4: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0004],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_msb_n4
        #   f800: b301 fffc           srl	r0,#0x4
        _tc(
            name='sys_srl_r_msb_n4',
            mnemonic='SRL',
            desc='SRL R0, #4: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFC],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_msb_n4
        #   f900: b309 0004           sla	r0,#0x4
        _tc(
            name='sys_sla_r_msb_n4',
            mnemonic='SLA',
            desc='SLA R0, #4: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0004],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_msb_n4
        #   fa00: b309 fffc           sra	r0,#0x4
        _tc(
            name='sys_sra_r_msb_n4',
            mnemonic='SRA',
            desc='SRA R0, #4: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFC],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_msb_n8
        #   fb00: b301 0008           sll	r0,#0x8
        _tc(
            name='sys_sll_r_msb_n8',
            mnemonic='SLL',
            desc='SLL R0, #8: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0008],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_msb_n8
        #   fc00: b301 fff8           srl	r0,#0x8
        _tc(
            name='sys_srl_r_msb_n8',
            mnemonic='SRL',
            desc='SRL R0, #8: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFF8],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_msb_n8
        #   fd00: b309 0008           sla	r0,#0x8
        _tc(
            name='sys_sla_r_msb_n8',
            mnemonic='SLA',
            desc='SLA R0, #8: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0008],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_msb_n8
        #   fe00: b309 fff8           sra	r0,#0x8
        _tc(
            name='sys_sra_r_msb_n8',
            mnemonic='SRA',
            desc='SRA R0, #8: 0x8000',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFF8],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_pattern_n1
        #   ff00: b301 0001           sll	r0,#0x1
        _tc(
            name='sys_sll_r_pattern_n1',
            mnemonic='SLL',
            desc='SLL R0, #1: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0001],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_pattern_n1
        #   10000: b301 ffff           srl	r0,#0x1
        _tc(
            name='sys_srl_r_pattern_n1',
            mnemonic='SRL',
            desc='SRL R0, #1: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFF],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_pattern_n1
        #   10100: b309 0001           sla	r0,#0x1
        _tc(
            name='sys_sla_r_pattern_n1',
            mnemonic='SLA',
            desc='SLA R0, #1: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0001],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_pattern_n1
        #   10200: b309 ffff           sra	r0,#0x1
        _tc(
            name='sys_sra_r_pattern_n1',
            mnemonic='SRA',
            desc='SRA R0, #1: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFF],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_pattern_n4
        #   10300: b301 0004           sll	r0,#0x4
        _tc(
            name='sys_sll_r_pattern_n4',
            mnemonic='SLL',
            desc='SLL R0, #4: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0004],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_pattern_n4
        #   10400: b301 fffc           srl	r0,#0x4
        _tc(
            name='sys_srl_r_pattern_n4',
            mnemonic='SRL',
            desc='SRL R0, #4: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFFC],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_pattern_n4
        #   10500: b309 0004           sla	r0,#0x4
        _tc(
            name='sys_sla_r_pattern_n4',
            mnemonic='SLA',
            desc='SLA R0, #4: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0004],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_pattern_n4
        #   10600: b309 fffc           sra	r0,#0x4
        _tc(
            name='sys_sra_r_pattern_n4',
            mnemonic='SRA',
            desc='SRA R0, #4: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFFC],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sll_r_pattern_n8
        #   10700: b301 0008           sll	r0,#0x8
        _tc(
            name='sys_sll_r_pattern_n8',
            mnemonic='SLL',
            desc='SLL R0, #8: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0x0008],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srl_r_pattern_n8
        #   10800: b301 fff8           srl	r0,#0x8
        _tc(
            name='sys_srl_r_pattern_n8',
            mnemonic='SRL',
            desc='SRL R0, #8: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB301, 0xFFF8],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sla_r_pattern_n8
        #   10900: b309 0008           sla	r0,#0x8
        _tc(
            name='sys_sla_r_pattern_n8',
            mnemonic='SLA',
            desc='SLA R0, #8: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0x0008],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sra_r_pattern_n8
        #   10a00: b309 fff8           sra	r0,#0x8
        _tc(
            name='sys_sra_r_pattern_n8',
            mnemonic='SRA',
            desc='SRA R0, #8: 0xA5A5',
            tags=['shift', 'word', 'R_mode'],
            code=[0xB309, 0xFFF8],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_one_n1
        #   10b00: b201 0001           sllb	rh0,#0x1
        _tc(
            name='sys_sllb_r_one_n1',
            mnemonic='SLLB',
            desc='SLLB RH0, #1: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0001],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_one_n1
        #   10c00: b201 00ff           srlb	rh0,#0x1
        _tc(
            name='sys_srlb_r_one_n1',
            mnemonic='SRLB',
            desc='SRLB RH0, #1: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FF],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_one_n1
        #   10d00: b209 0001           slab	rh0,#0x1
        _tc(
            name='sys_slab_r_one_n1',
            mnemonic='SLAB',
            desc='SLAB RH0, #1: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0001],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_one_n1
        #   10e00: b209 00ff           srab	rh0,#0x1
        _tc(
            name='sys_srab_r_one_n1',
            mnemonic='SRAB',
            desc='SRAB RH0, #1: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FF],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_one_n4
        #   10f00: b201 0004           sllb	rh0,#0x4
        _tc(
            name='sys_sllb_r_one_n4',
            mnemonic='SLLB',
            desc='SLLB RH0, #4: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0004],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_one_n4
        #   11000: b201 00fc           srlb	rh0,#0x4
        _tc(
            name='sys_srlb_r_one_n4',
            mnemonic='SRLB',
            desc='SRLB RH0, #4: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FC],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_one_n4
        #   11100: b209 0004           slab	rh0,#0x4
        _tc(
            name='sys_slab_r_one_n4',
            mnemonic='SLAB',
            desc='SLAB RH0, #4: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0004],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_one_n4
        #   11200: b209 00fc           srab	rh0,#0x4
        _tc(
            name='sys_srab_r_one_n4',
            mnemonic='SRAB',
            desc='SRAB RH0, #4: 0x01',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FC],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_msb_n1
        #   11300: b201 0001           sllb	rh0,#0x1
        _tc(
            name='sys_sllb_r_msb_n1',
            mnemonic='SLLB',
            desc='SLLB RH0, #1: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0001],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_msb_n1
        #   11400: b201 00ff           srlb	rh0,#0x1
        _tc(
            name='sys_srlb_r_msb_n1',
            mnemonic='SRLB',
            desc='SRLB RH0, #1: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FF],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_msb_n1
        #   11500: b209 0001           slab	rh0,#0x1
        _tc(
            name='sys_slab_r_msb_n1',
            mnemonic='SLAB',
            desc='SLAB RH0, #1: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0001],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_msb_n1
        #   11600: b209 00ff           srab	rh0,#0x1
        _tc(
            name='sys_srab_r_msb_n1',
            mnemonic='SRAB',
            desc='SRAB RH0, #1: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FF],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_msb_n4
        #   11700: b201 0004           sllb	rh0,#0x4
        _tc(
            name='sys_sllb_r_msb_n4',
            mnemonic='SLLB',
            desc='SLLB RH0, #4: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0004],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_msb_n4
        #   11800: b201 00fc           srlb	rh0,#0x4
        _tc(
            name='sys_srlb_r_msb_n4',
            mnemonic='SRLB',
            desc='SRLB RH0, #4: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FC],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_msb_n4
        #   11900: b209 0004           slab	rh0,#0x4
        _tc(
            name='sys_slab_r_msb_n4',
            mnemonic='SLAB',
            desc='SLAB RH0, #4: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0004],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_msb_n4
        #   11a00: b209 00fc           srab	rh0,#0x4
        _tc(
            name='sys_srab_r_msb_n4',
            mnemonic='SRAB',
            desc='SRAB RH0, #4: 0x80',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FC],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_pattern_n1
        #   11b00: b201 0001           sllb	rh0,#0x1
        _tc(
            name='sys_sllb_r_pattern_n1',
            mnemonic='SLLB',
            desc='SLLB RH0, #1: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0001],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_pattern_n1
        #   11c00: b201 00ff           srlb	rh0,#0x1
        _tc(
            name='sys_srlb_r_pattern_n1',
            mnemonic='SRLB',
            desc='SRLB RH0, #1: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FF],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_pattern_n1
        #   11d00: b209 0001           slab	rh0,#0x1
        _tc(
            name='sys_slab_r_pattern_n1',
            mnemonic='SLAB',
            desc='SLAB RH0, #1: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0001],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_pattern_n1
        #   11e00: b209 00ff           srab	rh0,#0x1
        _tc(
            name='sys_srab_r_pattern_n1',
            mnemonic='SRAB',
            desc='SRAB RH0, #1: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FF],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sllb_r_pattern_n4
        #   11f00: b201 0004           sllb	rh0,#0x4
        _tc(
            name='sys_sllb_r_pattern_n4',
            mnemonic='SLLB',
            desc='SLLB RH0, #4: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x0004],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srlb_r_pattern_n4
        #   12000: b201 00fc           srlb	rh0,#0x4
        _tc(
            name='sys_srlb_r_pattern_n4',
            mnemonic='SRLB',
            desc='SRLB RH0, #4: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB201, 0x00FC],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slab_r_pattern_n4
        #   12100: b209 0004           slab	rh0,#0x4
        _tc(
            name='sys_slab_r_pattern_n4',
            mnemonic='SLAB',
            desc='SLAB RH0, #4: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x0004],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srab_r_pattern_n4
        #   12200: b209 00fc           srab	rh0,#0x4
        _tc(
            name='sys_srab_r_pattern_n4',
            mnemonic='SRAB',
            desc='SRAB RH0, #4: 0xA5',
            tags=['shift', 'byte', 'R_mode'],
            code=[0xB209, 0x00FC],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slll_rr_one_n1
        #   12300: b305 0001           slll	rr0,#0x1
        _tc(
            name='sys_slll_rr_one_n1',
            mnemonic='SLLL',
            desc='SLLL RR0, #1: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0x0001],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srll_rr_one_n1
        #   12400: b305 ffff           srll	rr0,#0x1
        _tc(
            name='sys_srll_rr_one_n1',
            mnemonic='SRLL',
            desc='SRLL RR0, #1: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0xFFFF],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slal_rr_one_n1
        #   12500: b30d 0001           slal	rr0,#0x1
        _tc(
            name='sys_slal_rr_one_n1',
            mnemonic='SLAL',
            desc='SLAL RR0, #1: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0x0001],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sral_rr_one_n1
        #   12600: b30d ffff           sral	rr0,#0x1
        _tc(
            name='sys_sral_rr_one_n1',
            mnemonic='SRAL',
            desc='SRAL RR0, #1: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0xFFFF],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slll_rr_one_n8
        #   12700: b305 0008           slll	rr0,#0x8
        _tc(
            name='sys_slll_rr_one_n8',
            mnemonic='SLLL',
            desc='SLLL RR0, #8: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0x0008],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srll_rr_one_n8
        #   12800: b305 fff8           srll	rr0,#0x8
        _tc(
            name='sys_srll_rr_one_n8',
            mnemonic='SRLL',
            desc='SRLL RR0, #8: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0xFFF8],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slal_rr_one_n8
        #   12900: b30d 0008           slal	rr0,#0x8
        _tc(
            name='sys_slal_rr_one_n8',
            mnemonic='SLAL',
            desc='SLAL RR0, #8: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0x0008],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sral_rr_one_n8
        #   12a00: b30d fff8           sral	rr0,#0x8
        _tc(
            name='sys_sral_rr_one_n8',
            mnemonic='SRAL',
            desc='SRAL RR0, #8: 0x00000001',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0xFFF8],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slll_rr_msb_n1
        #   12b00: b305 0001           slll	rr0,#0x1
        _tc(
            name='sys_slll_rr_msb_n1',
            mnemonic='SLLL',
            desc='SLLL RR0, #1: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0x0001],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srll_rr_msb_n1
        #   12c00: b305 ffff           srll	rr0,#0x1
        _tc(
            name='sys_srll_rr_msb_n1',
            mnemonic='SRLL',
            desc='SRLL RR0, #1: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0xFFFF],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slal_rr_msb_n1
        #   12d00: b30d 0001           slal	rr0,#0x1
        _tc(
            name='sys_slal_rr_msb_n1',
            mnemonic='SLAL',
            desc='SLAL RR0, #1: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0x0001],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sral_rr_msb_n1
        #   12e00: b30d ffff           sral	rr0,#0x1
        _tc(
            name='sys_sral_rr_msb_n1',
            mnemonic='SRAL',
            desc='SRAL RR0, #1: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0xFFFF],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slll_rr_msb_n8
        #   12f00: b305 0008           slll	rr0,#0x8
        _tc(
            name='sys_slll_rr_msb_n8',
            mnemonic='SLLL',
            desc='SLLL RR0, #8: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0x0008],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_srll_rr_msb_n8
        #   13000: b305 fff8           srll	rr0,#0x8
        _tc(
            name='sys_srll_rr_msb_n8',
            mnemonic='SRLL',
            desc='SRLL RR0, #8: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB305, 0xFFF8],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_slal_rr_msb_n8
        #   13100: b30d 0008           slal	rr0,#0x8
        _tc(
            name='sys_slal_rr_msb_n8',
            mnemonic='SLAL',
            desc='SLAL RR0, #8: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0x0008],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sral_rr_msb_n8
        #   13200: b30d fff8           sral	rr0,#0x8
        _tc(
            name='sys_sral_rr_msb_n8',
            mnemonic='SRAL',
            desc='SRAL RR0, #8: 0x80000000',
            tags=['shift', 'long', 'R_mode'],
            code=[0xB30D, 0xFFF8],
            regs={0: 0x8000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_one_l1
        #   13300: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_one_l1',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x0001, count=1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x0001, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_msb_l1
        #   13400: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_msb_l1',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x8000, count=1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x8000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_one_r1
        #   13500: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_one_r1',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x0001, count=-1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x0001, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_msb_r1
        #   13600: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_msb_r1',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x8000, count=-1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x8000, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_one_l4
        #   13700: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_one_l4',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x0001, count=4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x0001, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_msb_l4
        #   13800: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_msb_l4',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x8000, count=4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x8000, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_one_r4
        #   13900: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_one_r4',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x0001, count=-4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x0001, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sda_r_msb_r4
        #   13a00: b30b 0100           sda	r0,r1
        _tc(
            name='sys_sda_r_msb_r4',
            mnemonic='SDA',
            desc='SDA R0, R1: val=0x8000, count=-4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB30B, 0x0100],
            regs={0: 0x8000, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_one_l1
        #   13b00: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_one_l1',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x0001, count=1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x0001, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_msb_l1
        #   13c00: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_msb_l1',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x8000, count=1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x8000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_one_r1
        #   13d00: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_one_r1',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x0001, count=-1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x0001, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_msb_r1
        #   13e00: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_msb_r1',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x8000, count=-1',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x8000, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_one_l4
        #   13f00: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_one_l4',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x0001, count=4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x0001, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_msb_l4
        #   14000: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_msb_l4',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x8000, count=4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x8000, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_one_r4
        #   14100: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_one_r4',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x0001, count=-4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x0001, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdl_r_msb_r4
        #   14200: b303 0100           sdl	r0,r1
        _tc(
            name='sys_sdl_r_msb_r4',
            mnemonic='SDL',
            desc='SDL R0, R1: val=0x8000, count=-4',
            tags=['shift', 'dynamic', 'word'],
            code=[0xB303, 0x0100],
            regs={0: 0x8000, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_one_l1
        #   14300: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_one_l1',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x01, count=1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x0100, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_msb_l1
        #   14400: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_msb_l1',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x80, count=1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x8000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_one_r1
        #   14500: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_one_r1',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x01, count=-1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x0100, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_msb_r1
        #   14600: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_msb_r1',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x80, count=-1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x8000, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_one_l4
        #   14700: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_one_l4',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x01, count=4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x0100, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_msb_l4
        #   14800: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_msb_l4',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x80, count=4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x8000, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_one_r4
        #   14900: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_one_r4',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x01, count=-4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x0100, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdab_r_msb_r4
        #   14a00: b20b 0100           sdab	rh0,r1
        _tc(
            name='sys_sdab_r_msb_r4',
            mnemonic='SDAB',
            desc='SDAB RH0, R1: val=0x80, count=-4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB20B, 0x0100],
            regs={0: 0x8000, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_one_l1
        #   14b00: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_one_l1',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x01, count=1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x0100, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_msb_l1
        #   14c00: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_msb_l1',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x80, count=1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x8000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_one_r1
        #   14d00: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_one_r1',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x01, count=-1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x0100, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_msb_r1
        #   14e00: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_msb_r1',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x80, count=-1',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x8000, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_one_l4
        #   14f00: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_one_l4',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x01, count=4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x0100, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_msb_l4
        #   15000: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_msb_l4',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x80, count=4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x8000, 1: 0x0004},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_one_r4
        #   15100: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_one_r4',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x01, count=-4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x0100, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdlb_r_msb_r4
        #   15200: b203 0100           sdlb	rh0,r1
        _tc(
            name='sys_sdlb_r_msb_r4',
            mnemonic='SDLB',
            desc='SDLB RH0, R1: val=0x80, count=-4',
            tags=['shift', 'dynamic', 'byte'],
            code=[0xB203, 0x0100],
            regs={0: 0x8000, 1: 0xFFFC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_one_l1
        #   15300: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_one_l1',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x00000001, count=1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0x0001, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_msb_l1
        #   15400: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_msb_l1',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x80000000, count=1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0x0001, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_one_r1
        #   15500: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_one_r1',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x00000001, count=-1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_msb_r1
        #   15600: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_msb_r1',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x80000000, count=-1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0xFFFF, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_one_l4
        #   15700: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_one_l4',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x00000001, count=4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0x0004, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_msb_l4
        #   15800: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_msb_l4',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x80000000, count=4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0x0004, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_one_r4
        #   15900: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_one_r4',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x00000001, count=-4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0xFFFC, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdal_rr_msb_r4
        #   15a00: b32f 0100           sdal	rr2,r1
        _tc(
            name='sys_sdal_rr_msb_r4',
            mnemonic='SDAL',
            desc='SDAL RR2, R1: val=0x80000000, count=-4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB32F, 0x0100],
            regs={1: 0xFFFC, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_one_l1
        #   15b00: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_one_l1',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x00000001, count=1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0x0001, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_msb_l1
        #   15c00: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_msb_l1',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x80000000, count=1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0x0001, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_one_r1
        #   15d00: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_one_r1',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x00000001, count=-1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0xFFFF, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_msb_r1
        #   15e00: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_msb_r1',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x80000000, count=-1',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0xFFFF, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_one_l4
        #   15f00: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_one_l4',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x00000001, count=4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0x0004, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_msb_l4
        #   16000: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_msb_l4',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x80000000, count=4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0x0004, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_one_r4
        #   16100: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_one_r4',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x00000001, count=-4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0xFFFC, 2: 0x0000, 3: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_sdll_rr_msb_r4
        #   16200: b327 0100           sdll	rr2,r1
        _tc(
            name='sys_sdll_rr_msb_r4',
            mnemonic='SDLL',
            desc='SDLL RR2, R1: val=0x80000000, count=-4',
            tags=['shift', 'dynamic', 'long'],
            code=[0xB327, 0x0100],
            regs={1: 0xFFFC, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_one_n1
        #   16300: b300                rl	r0,#0x1
        _tc(
            name='sys_rl_r_one_n1',
            mnemonic='RL',
            desc='RL R0, #1: 0x0001',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB300],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_one_n2
        #   16400: b302                rl	r0,#0x2
        _tc(
            name='sys_rl_r_one_n2',
            mnemonic='RL',
            desc='RL R0, #2: 0x0001',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB302],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_msb_n1
        #   16500: b300                rl	r0,#0x1
        _tc(
            name='sys_rl_r_msb_n1',
            mnemonic='RL',
            desc='RL R0, #1: 0x8000',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB300],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_msb_n2
        #   16600: b302                rl	r0,#0x2
        _tc(
            name='sys_rl_r_msb_n2',
            mnemonic='RL',
            desc='RL R0, #2: 0x8000',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB302],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_pattern_n1
        #   16700: b300                rl	r0,#0x1
        _tc(
            name='sys_rl_r_pattern_n1',
            mnemonic='RL',
            desc='RL R0, #1: 0xA5A5',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB300],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rl_r_pattern_n2
        #   16800: b302                rl	r0,#0x2
        _tc(
            name='sys_rl_r_pattern_n2',
            mnemonic='RL',
            desc='RL R0, #2: 0xA5A5',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB302],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_one_n1
        #   16900: b304                rr	r0,#0x1
        _tc(
            name='sys_rr_r_one_n1',
            mnemonic='RR',
            desc='RR R0, #1: 0x0001',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB304],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_one_n2
        #   16a00: b306                rr	r0,#0x2
        _tc(
            name='sys_rr_r_one_n2',
            mnemonic='RR',
            desc='RR R0, #2: 0x0001',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB306],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_msb_n1
        #   16b00: b304                rr	r0,#0x1
        _tc(
            name='sys_rr_r_msb_n1',
            mnemonic='RR',
            desc='RR R0, #1: 0x8000',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB304],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_msb_n2
        #   16c00: b306                rr	r0,#0x2
        _tc(
            name='sys_rr_r_msb_n2',
            mnemonic='RR',
            desc='RR R0, #2: 0x8000',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB306],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_pattern_n1
        #   16d00: b304                rr	r0,#0x1
        _tc(
            name='sys_rr_r_pattern_n1',
            mnemonic='RR',
            desc='RR R0, #1: 0xA5A5',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB304],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rr_r_pattern_n2
        #   16e00: b306                rr	r0,#0x2
        _tc(
            name='sys_rr_r_pattern_n2',
            mnemonic='RR',
            desc='RR R0, #2: 0xA5A5',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB306],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_one_n1_c0
        #   16f00: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_one_n1_c0',
            mnemonic='RLC',
            desc='RLC R0, #1: 0x0001, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_one_n1_c1
        #   17000: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_one_n1_c1',
            mnemonic='RLC',
            desc='RLC R0, #1: 0x0001, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_one_n2_c0
        #   17100: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_one_n2_c0',
            mnemonic='RLC',
            desc='RLC R0, #2: 0x0001, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_one_n2_c1
        #   17200: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_one_n2_c1',
            mnemonic='RLC',
            desc='RLC R0, #2: 0x0001, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_msb_n1_c0
        #   17300: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_msb_n1_c0',
            mnemonic='RLC',
            desc='RLC R0, #1: 0x8000, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_msb_n1_c1
        #   17400: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_msb_n1_c1',
            mnemonic='RLC',
            desc='RLC R0, #1: 0x8000, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_msb_n2_c0
        #   17500: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_msb_n2_c0',
            mnemonic='RLC',
            desc='RLC R0, #2: 0x8000, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_msb_n2_c1
        #   17600: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_msb_n2_c1',
            mnemonic='RLC',
            desc='RLC R0, #2: 0x8000, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_pattern_n1_c0
        #   17700: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_pattern_n1_c0',
            mnemonic='RLC',
            desc='RLC R0, #1: 0xA5A5, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_pattern_n1_c1
        #   17800: b308                rlc	r0,#0x1
        _tc(
            name='sys_rlc_r_pattern_n1_c1',
            mnemonic='RLC',
            desc='RLC R0, #1: 0xA5A5, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB308],
            regs={0: 0xA5A5},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_pattern_n2_c0
        #   17900: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_pattern_n2_c0',
            mnemonic='RLC',
            desc='RLC R0, #2: 0xA5A5, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlc_r_pattern_n2_c1
        #   17a00: b30a                rlc	r0,#0x2
        _tc(
            name='sys_rlc_r_pattern_n2_c1',
            mnemonic='RLC',
            desc='RLC R0, #2: 0xA5A5, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30A],
            regs={0: 0xA5A5},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_one_n1_c0
        #   17b00: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_one_n1_c0',
            mnemonic='RRC',
            desc='RRC R0, #1: 0x0001, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_one_n1_c1
        #   17c00: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_one_n1_c1',
            mnemonic='RRC',
            desc='RRC R0, #1: 0x0001, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_one_n2_c0
        #   17d00: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_one_n2_c0',
            mnemonic='RRC',
            desc='RRC R0, #2: 0x0001, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_one_n2_c1
        #   17e00: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_one_n2_c1',
            mnemonic='RRC',
            desc='RRC R0, #2: 0x0001, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0x0001},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_msb_n1_c0
        #   17f00: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_msb_n1_c0',
            mnemonic='RRC',
            desc='RRC R0, #1: 0x8000, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_msb_n1_c1
        #   18000: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_msb_n1_c1',
            mnemonic='RRC',
            desc='RRC R0, #1: 0x8000, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_msb_n2_c0
        #   18100: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_msb_n2_c0',
            mnemonic='RRC',
            desc='RRC R0, #2: 0x8000, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_msb_n2_c1
        #   18200: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_msb_n2_c1',
            mnemonic='RRC',
            desc='RRC R0, #2: 0x8000, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_pattern_n1_c0
        #   18300: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_pattern_n1_c0',
            mnemonic='RRC',
            desc='RRC R0, #1: 0xA5A5, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_pattern_n1_c1
        #   18400: b30c                rrc	r0,#0x1
        _tc(
            name='sys_rrc_r_pattern_n1_c1',
            mnemonic='RRC',
            desc='RRC R0, #1: 0xA5A5, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30C],
            regs={0: 0xA5A5},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_pattern_n2_c0
        #   18500: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_pattern_n2_c0',
            mnemonic='RRC',
            desc='RRC R0, #2: 0xA5A5, c0',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0xA5A5},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrc_r_pattern_n2_c1
        #   18600: b30e                rrc	r0,#0x2
        _tc(
            name='sys_rrc_r_pattern_n2_c1',
            mnemonic='RRC',
            desc='RRC R0, #2: 0xA5A5, c1',
            tags=['rotate', 'word', 'R_mode'],
            code=[0xB30E],
            regs={0: 0xA5A5},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_one_n1
        #   18700: b200                rlb	rh0,#0x1
        _tc(
            name='sys_rlb_r_one_n1',
            mnemonic='RLB',
            desc='RLB RH0, #1: 0x01',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB200],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_one_n2
        #   18800: b202                rlb	rh0,#0x2
        _tc(
            name='sys_rlb_r_one_n2',
            mnemonic='RLB',
            desc='RLB RH0, #2: 0x01',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB202],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_msb_n1
        #   18900: b200                rlb	rh0,#0x1
        _tc(
            name='sys_rlb_r_msb_n1',
            mnemonic='RLB',
            desc='RLB RH0, #1: 0x80',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB200],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_msb_n2
        #   18a00: b202                rlb	rh0,#0x2
        _tc(
            name='sys_rlb_r_msb_n2',
            mnemonic='RLB',
            desc='RLB RH0, #2: 0x80',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB202],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_pattern_n1
        #   18b00: b200                rlb	rh0,#0x1
        _tc(
            name='sys_rlb_r_pattern_n1',
            mnemonic='RLB',
            desc='RLB RH0, #1: 0xA5',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB200],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlb_r_pattern_n2
        #   18c00: b202                rlb	rh0,#0x2
        _tc(
            name='sys_rlb_r_pattern_n2',
            mnemonic='RLB',
            desc='RLB RH0, #2: 0xA5',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB202],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_one_n1
        #   18d00: b204                rrb	rh0,#0x1
        _tc(
            name='sys_rrb_r_one_n1',
            mnemonic='RRB',
            desc='RRB RH0, #1: 0x01',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB204],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_one_n2
        #   18e00: b206                rrb	rh0,#0x2
        _tc(
            name='sys_rrb_r_one_n2',
            mnemonic='RRB',
            desc='RRB RH0, #2: 0x01',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB206],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_msb_n1
        #   18f00: b204                rrb	rh0,#0x1
        _tc(
            name='sys_rrb_r_msb_n1',
            mnemonic='RRB',
            desc='RRB RH0, #1: 0x80',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB204],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_msb_n2
        #   19000: b206                rrb	rh0,#0x2
        _tc(
            name='sys_rrb_r_msb_n2',
            mnemonic='RRB',
            desc='RRB RH0, #2: 0x80',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB206],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_pattern_n1
        #   19100: b204                rrb	rh0,#0x1
        _tc(
            name='sys_rrb_r_pattern_n1',
            mnemonic='RRB',
            desc='RRB RH0, #1: 0xA5',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB204],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrb_r_pattern_n2
        #   19200: b206                rrb	rh0,#0x2
        _tc(
            name='sys_rrb_r_pattern_n2',
            mnemonic='RRB',
            desc='RRB RH0, #2: 0xA5',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB206],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_one_n1_c0
        #   19300: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_one_n1_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0x01, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_one_n1_c1
        #   19400: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_one_n1_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0x01, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_one_n2_c0
        #   19500: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_one_n2_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0x01, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_one_n2_c1
        #   19600: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_one_n2_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0x01, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_msb_n1_c0
        #   19700: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_msb_n1_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0x80, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_msb_n1_c1
        #   19800: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_msb_n1_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0x80, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_msb_n2_c0
        #   19900: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_msb_n2_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0x80, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_msb_n2_c1
        #   19a00: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_msb_n2_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0x80, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_pattern_n1_c0
        #   19b00: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_pattern_n1_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0xA5, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_pattern_n1_c1
        #   19c00: b208                rlcb	rh0,#0x1
        _tc(
            name='sys_rlcb_r_pattern_n1_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #1: 0xA5, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB208],
            regs={0: 0xA500},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_pattern_n2_c0
        #   19d00: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_pattern_n2_c0',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0xA5, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rlcb_r_pattern_n2_c1
        #   19e00: b20a                rlcb	rh0,#0x2
        _tc(
            name='sys_rlcb_r_pattern_n2_c1',
            mnemonic='RLCB',
            desc='RLCB RH0, #2: 0xA5, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20A],
            regs={0: 0xA500},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_one_n1_c0
        #   19f00: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_one_n1_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0x01, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_one_n1_c1
        #   1a000: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_one_n1_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0x01, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_one_n2_c0
        #   1a100: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_one_n2_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0x01, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_one_n2_c1
        #   1a200: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_one_n2_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0x01, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0x0100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_msb_n1_c0
        #   1a300: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_msb_n1_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0x80, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_msb_n1_c1
        #   1a400: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_msb_n1_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0x80, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_msb_n2_c0
        #   1a500: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_msb_n2_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0x80, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_msb_n2_c1
        #   1a600: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_msb_n2_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0x80, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0x8000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_pattern_n1_c0
        #   1a700: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_pattern_n1_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0xA5, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_pattern_n1_c1
        #   1a800: b20c                rrcb	rh0,#0x1
        _tc(
            name='sys_rrcb_r_pattern_n1_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #1: 0xA5, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20C],
            regs={0: 0xA500},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_pattern_n2_c0
        #   1a900: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_pattern_n2_c0',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0xA5, c0',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0xA500},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrcb_r_pattern_n2_c1
        #   1aa00: b20e                rrcb	rh0,#0x2
        _tc(
            name='sys_rrcb_r_pattern_n2_c1',
            mnemonic='RRCB',
            desc='RRCB RH0, #2: 0xA5, c1',
            tags=['rotate', 'byte', 'R_mode'],
            code=[0xB20E],
            regs={0: 0xA500},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rldb_bcd_00
        #   1ab00: be18                rldb	rl0,rh1
        _tc(
            name='sys_rldb_bcd_00',
            mnemonic='RLDB',
            desc='RLDB RL0, RH1: RL0=0x00, RH1=0x12',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBE18],
            regs={0: 0x0000, 1: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rldb_bcd_99
        #   1ac00: be18                rldb	rl0,rh1
        _tc(
            name='sys_rldb_bcd_99',
            mnemonic='RLDB',
            desc='RLDB RL0, RH1: RL0=0x99, RH1=0x87',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBE18],
            regs={0: 0x0099, 1: 0x8700},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rldb_bcd_50
        #   1ad00: be18                rldb	rl0,rh1
        _tc(
            name='sys_rldb_bcd_50',
            mnemonic='RLDB',
            desc='RLDB RL0, RH1: RL0=0x50, RH1=0x43',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBE18],
            regs={0: 0x0050, 1: 0x4300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrdb_bcd_00
        #   1ae00: bc18                rrdb	rl0,rh1
        _tc(
            name='sys_rrdb_bcd_00',
            mnemonic='RRDB',
            desc='RRDB RL0, RH1: RL0=0x00, RH1=0x12',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBC18],
            regs={0: 0x0000, 1: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrdb_bcd_99
        #   1af00: bc18                rrdb	rl0,rh1
        _tc(
            name='sys_rrdb_bcd_99',
            mnemonic='RRDB',
            desc='RRDB RL0, RH1: RL0=0x99, RH1=0x87',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBC18],
            regs={0: 0x0099, 1: 0x8700},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_rrdb_bcd_50
        #   1b000: bc18                rrdb	rl0,rh1
        _tc(
            name='sys_rrdb_bcd_50',
            mnemonic='RRDB',
            desc='RRDB RL0, RH1: RL0=0x50, RH1=0x43',
            tags=['rotate', 'digit', 'byte'],
            code=[0xBC18],
            regs={0: 0x0050, 1: 0x4300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b0_zero
        #   1b100: a700                bit	r0,#0x0
        _tc(
            name='sys_bit_r_b0_zero',
            mnemonic='BIT',
            desc='BIT R0, #0: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA700],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b0_allones
        #   1b200: a700                bit	r0,#0x0
        _tc(
            name='sys_bit_r_b0_allones',
            mnemonic='BIT',
            desc='BIT R0, #0: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA700],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b7_zero
        #   1b300: a707                bit	r0,#0x7
        _tc(
            name='sys_bit_r_b7_zero',
            mnemonic='BIT',
            desc='BIT R0, #7: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA707],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b7_allones
        #   1b400: a707                bit	r0,#0x7
        _tc(
            name='sys_bit_r_b7_allones',
            mnemonic='BIT',
            desc='BIT R0, #7: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA707],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b15_zero
        #   1b500: a70f                bit	r0,#0xf
        _tc(
            name='sys_bit_r_b15_zero',
            mnemonic='BIT',
            desc='BIT R0, #15: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA70F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bit_r_b15_allones
        #   1b600: a70f                bit	r0,#0xf
        _tc(
            name='sys_bit_r_b15_allones',
            mnemonic='BIT',
            desc='BIT R0, #15: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA70F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b0_zero
        #   1b700: a500                set	r0,#0x0
        _tc(
            name='sys_set_r_b0_zero',
            mnemonic='SET',
            desc='SET R0, #0: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA500],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b0_allones
        #   1b800: a500                set	r0,#0x0
        _tc(
            name='sys_set_r_b0_allones',
            mnemonic='SET',
            desc='SET R0, #0: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA500],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b7_zero
        #   1b900: a507                set	r0,#0x7
        _tc(
            name='sys_set_r_b7_zero',
            mnemonic='SET',
            desc='SET R0, #7: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA507],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b7_allones
        #   1ba00: a507                set	r0,#0x7
        _tc(
            name='sys_set_r_b7_allones',
            mnemonic='SET',
            desc='SET R0, #7: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA507],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b15_zero
        #   1bb00: a50f                set	r0,#0xf
        _tc(
            name='sys_set_r_b15_zero',
            mnemonic='SET',
            desc='SET R0, #15: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA50F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_set_r_b15_allones
        #   1bc00: a50f                set	r0,#0xf
        _tc(
            name='sys_set_r_b15_allones',
            mnemonic='SET',
            desc='SET R0, #15: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA50F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b0_zero
        #   1bd00: a300                res	r0,#0x0
        _tc(
            name='sys_res_r_b0_zero',
            mnemonic='RES',
            desc='RES R0, #0: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA300],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b0_allones
        #   1be00: a300                res	r0,#0x0
        _tc(
            name='sys_res_r_b0_allones',
            mnemonic='RES',
            desc='RES R0, #0: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA300],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b7_zero
        #   1bf00: a307                res	r0,#0x7
        _tc(
            name='sys_res_r_b7_zero',
            mnemonic='RES',
            desc='RES R0, #7: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA307],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b7_allones
        #   1c000: a307                res	r0,#0x7
        _tc(
            name='sys_res_r_b7_allones',
            mnemonic='RES',
            desc='RES R0, #7: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA307],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b15_zero
        #   1c100: a30f                res	r0,#0xf
        _tc(
            name='sys_res_r_b15_zero',
            mnemonic='RES',
            desc='RES R0, #15: R0=0x0000',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA30F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_res_r_b15_allones
        #   1c200: a30f                res	r0,#0xf
        _tc(
            name='sys_res_r_b15_allones',
            mnemonic='RES',
            desc='RES R0, #15: R0=0xFFFF',
            tags=['bit', 'word', 'R_mode'],
            code=[0xA30F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b0_zero
        #   1c300: a600                bitb	rh0,#0x0
        _tc(
            name='sys_bitb_r_b0_zero',
            mnemonic='BITB',
            desc='BITB RH0, #0: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA600],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b0_allones
        #   1c400: a600                bitb	rh0,#0x0
        _tc(
            name='sys_bitb_r_b0_allones',
            mnemonic='BITB',
            desc='BITB RH0, #0: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA600],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b3_zero
        #   1c500: a603                bitb	rh0,#0x3
        _tc(
            name='sys_bitb_r_b3_zero',
            mnemonic='BITB',
            desc='BITB RH0, #3: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA603],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b3_allones
        #   1c600: a603                bitb	rh0,#0x3
        _tc(
            name='sys_bitb_r_b3_allones',
            mnemonic='BITB',
            desc='BITB RH0, #3: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA603],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b7_zero
        #   1c700: a607                bitb	rh0,#0x7
        _tc(
            name='sys_bitb_r_b7_zero',
            mnemonic='BITB',
            desc='BITB RH0, #7: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA607],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_bitb_r_b7_allones
        #   1c800: a607                bitb	rh0,#0x7
        _tc(
            name='sys_bitb_r_b7_allones',
            mnemonic='BITB',
            desc='BITB RH0, #7: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA607],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b0_zero
        #   1c900: a400                setb	rh0,#0x0
        _tc(
            name='sys_setb_r_b0_zero',
            mnemonic='SETB',
            desc='SETB RH0, #0: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA400],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b0_allones
        #   1ca00: a400                setb	rh0,#0x0
        _tc(
            name='sys_setb_r_b0_allones',
            mnemonic='SETB',
            desc='SETB RH0, #0: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA400],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b3_zero
        #   1cb00: a403                setb	rh0,#0x3
        _tc(
            name='sys_setb_r_b3_zero',
            mnemonic='SETB',
            desc='SETB RH0, #3: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA403],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b3_allones
        #   1cc00: a403                setb	rh0,#0x3
        _tc(
            name='sys_setb_r_b3_allones',
            mnemonic='SETB',
            desc='SETB RH0, #3: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA403],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b7_zero
        #   1cd00: a407                setb	rh0,#0x7
        _tc(
            name='sys_setb_r_b7_zero',
            mnemonic='SETB',
            desc='SETB RH0, #7: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA407],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setb_r_b7_allones
        #   1ce00: a407                setb	rh0,#0x7
        _tc(
            name='sys_setb_r_b7_allones',
            mnemonic='SETB',
            desc='SETB RH0, #7: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA407],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b0_zero
        #   1cf00: a200                resb	rh0,#0x0
        _tc(
            name='sys_resb_r_b0_zero',
            mnemonic='RESB',
            desc='RESB RH0, #0: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA200],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b0_allones
        #   1d000: a200                resb	rh0,#0x0
        _tc(
            name='sys_resb_r_b0_allones',
            mnemonic='RESB',
            desc='RESB RH0, #0: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA200],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b3_zero
        #   1d100: a203                resb	rh0,#0x3
        _tc(
            name='sys_resb_r_b3_zero',
            mnemonic='RESB',
            desc='RESB RH0, #3: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA203],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b3_allones
        #   1d200: a203                resb	rh0,#0x3
        _tc(
            name='sys_resb_r_b3_allones',
            mnemonic='RESB',
            desc='RESB RH0, #3: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA203],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b7_zero
        #   1d300: a207                resb	rh0,#0x7
        _tc(
            name='sys_resb_r_b7_zero',
            mnemonic='RESB',
            desc='RESB RH0, #7: RH0=0x00',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA207],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resb_r_b7_allones
        #   1d400: a207                resb	rh0,#0x7
        _tc(
            name='sys_resb_r_b7_allones',
            mnemonic='RESB',
            desc='RESB RH0, #7: RH0=0xFF',
            tags=['bit', 'byte', 'R_mode'],
            code=[0xA207],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n1_zero
        #   1d500: a900                inc	r0,#0x1
        _tc(
            name='sys_inc_r_n1_zero',
            mnemonic='INC',
            desc='INC R0, #1: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA900],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n1_one
        #   1d600: a900                inc	r0,#0x1
        _tc(
            name='sys_inc_r_n1_one',
            mnemonic='INC',
            desc='INC R0, #1: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA900],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n1_max
        #   1d700: a900                inc	r0,#0x1
        _tc(
            name='sys_inc_r_n1_max',
            mnemonic='INC',
            desc='INC R0, #1: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA900],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n1_half
        #   1d800: a900                inc	r0,#0x1
        _tc(
            name='sys_inc_r_n1_half',
            mnemonic='INC',
            desc='INC R0, #1: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA900],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n2_zero
        #   1d900: a901                inc	r0,#0x2
        _tc(
            name='sys_inc_r_n2_zero',
            mnemonic='INC',
            desc='INC R0, #2: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA901],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n2_one
        #   1da00: a901                inc	r0,#0x2
        _tc(
            name='sys_inc_r_n2_one',
            mnemonic='INC',
            desc='INC R0, #2: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA901],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n2_max
        #   1db00: a901                inc	r0,#0x2
        _tc(
            name='sys_inc_r_n2_max',
            mnemonic='INC',
            desc='INC R0, #2: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA901],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n2_half
        #   1dc00: a901                inc	r0,#0x2
        _tc(
            name='sys_inc_r_n2_half',
            mnemonic='INC',
            desc='INC R0, #2: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA901],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n16_zero
        #   1dd00: a90f                inc	r0,#0x10
        _tc(
            name='sys_inc_r_n16_zero',
            mnemonic='INC',
            desc='INC R0, #16: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA90F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n16_one
        #   1de00: a90f                inc	r0,#0x10
        _tc(
            name='sys_inc_r_n16_one',
            mnemonic='INC',
            desc='INC R0, #16: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA90F],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n16_max
        #   1df00: a90f                inc	r0,#0x10
        _tc(
            name='sys_inc_r_n16_max',
            mnemonic='INC',
            desc='INC R0, #16: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA90F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_r_n16_half
        #   1e000: a90f                inc	r0,#0x10
        _tc(
            name='sys_inc_r_n16_half',
            mnemonic='INC',
            desc='INC R0, #16: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xA90F],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n1_zero
        #   1e100: ab00                dec	r0,#0x1
        _tc(
            name='sys_dec_r_n1_zero',
            mnemonic='DEC',
            desc='DEC R0, #1: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n1_one
        #   1e200: ab00                dec	r0,#0x1
        _tc(
            name='sys_dec_r_n1_one',
            mnemonic='DEC',
            desc='DEC R0, #1: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB00],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n1_max
        #   1e300: ab00                dec	r0,#0x1
        _tc(
            name='sys_dec_r_n1_max',
            mnemonic='DEC',
            desc='DEC R0, #1: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB00],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n1_half
        #   1e400: ab00                dec	r0,#0x1
        _tc(
            name='sys_dec_r_n1_half',
            mnemonic='DEC',
            desc='DEC R0, #1: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB00],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n2_zero
        #   1e500: ab01                dec	r0,#0x2
        _tc(
            name='sys_dec_r_n2_zero',
            mnemonic='DEC',
            desc='DEC R0, #2: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB01],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n2_one
        #   1e600: ab01                dec	r0,#0x2
        _tc(
            name='sys_dec_r_n2_one',
            mnemonic='DEC',
            desc='DEC R0, #2: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB01],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n2_max
        #   1e700: ab01                dec	r0,#0x2
        _tc(
            name='sys_dec_r_n2_max',
            mnemonic='DEC',
            desc='DEC R0, #2: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB01],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n2_half
        #   1e800: ab01                dec	r0,#0x2
        _tc(
            name='sys_dec_r_n2_half',
            mnemonic='DEC',
            desc='DEC R0, #2: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB01],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n16_zero
        #   1e900: ab0f                dec	r0,#0x10
        _tc(
            name='sys_dec_r_n16_zero',
            mnemonic='DEC',
            desc='DEC R0, #16: R0=0x0000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB0F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n16_one
        #   1ea00: ab0f                dec	r0,#0x10
        _tc(
            name='sys_dec_r_n16_one',
            mnemonic='DEC',
            desc='DEC R0, #16: R0=0x0001',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB0F],
            regs={0: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n16_max
        #   1eb00: ab0f                dec	r0,#0x10
        _tc(
            name='sys_dec_r_n16_max',
            mnemonic='DEC',
            desc='DEC R0, #16: R0=0xFFFF',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB0F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_r_n16_half
        #   1ec00: ab0f                dec	r0,#0x10
        _tc(
            name='sys_dec_r_n16_half',
            mnemonic='DEC',
            desc='DEC R0, #16: R0=0x8000',
            tags=['inc_dec', 'word', 'R_mode'],
            code=[0xAB0F],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n1_zero
        #   1ed00: a800                incb	rh0,#0x1
        _tc(
            name='sys_incb_r_n1_zero',
            mnemonic='INCB',
            desc='INCB RH0, #1: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA800],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n1_one
        #   1ee00: a800                incb	rh0,#0x1
        _tc(
            name='sys_incb_r_n1_one',
            mnemonic='INCB',
            desc='INCB RH0, #1: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA800],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n1_max
        #   1ef00: a800                incb	rh0,#0x1
        _tc(
            name='sys_incb_r_n1_max',
            mnemonic='INCB',
            desc='INCB RH0, #1: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA800],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n1_half
        #   1f000: a800                incb	rh0,#0x1
        _tc(
            name='sys_incb_r_n1_half',
            mnemonic='INCB',
            desc='INCB RH0, #1: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA800],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n2_zero
        #   1f100: a801                incb	rh0,#0x2
        _tc(
            name='sys_incb_r_n2_zero',
            mnemonic='INCB',
            desc='INCB RH0, #2: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA801],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n2_one
        #   1f200: a801                incb	rh0,#0x2
        _tc(
            name='sys_incb_r_n2_one',
            mnemonic='INCB',
            desc='INCB RH0, #2: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA801],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n2_max
        #   1f300: a801                incb	rh0,#0x2
        _tc(
            name='sys_incb_r_n2_max',
            mnemonic='INCB',
            desc='INCB RH0, #2: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA801],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n2_half
        #   1f400: a801                incb	rh0,#0x2
        _tc(
            name='sys_incb_r_n2_half',
            mnemonic='INCB',
            desc='INCB RH0, #2: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA801],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n16_zero
        #   1f500: a80f                incb	rh0,#0x10
        _tc(
            name='sys_incb_r_n16_zero',
            mnemonic='INCB',
            desc='INCB RH0, #16: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA80F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n16_one
        #   1f600: a80f                incb	rh0,#0x10
        _tc(
            name='sys_incb_r_n16_one',
            mnemonic='INCB',
            desc='INCB RH0, #16: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA80F],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n16_max
        #   1f700: a80f                incb	rh0,#0x10
        _tc(
            name='sys_incb_r_n16_max',
            mnemonic='INCB',
            desc='INCB RH0, #16: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA80F],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_incb_r_n16_half
        #   1f800: a80f                incb	rh0,#0x10
        _tc(
            name='sys_incb_r_n16_half',
            mnemonic='INCB',
            desc='INCB RH0, #16: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xA80F],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n1_zero
        #   1f900: aa00                decb	rh0,#0x1
        _tc(
            name='sys_decb_r_n1_zero',
            mnemonic='DECB',
            desc='DECB RH0, #1: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n1_one
        #   1fa00: aa00                decb	rh0,#0x1
        _tc(
            name='sys_decb_r_n1_one',
            mnemonic='DECB',
            desc='DECB RH0, #1: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA00],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n1_max
        #   1fb00: aa00                decb	rh0,#0x1
        _tc(
            name='sys_decb_r_n1_max',
            mnemonic='DECB',
            desc='DECB RH0, #1: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA00],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n1_half
        #   1fc00: aa00                decb	rh0,#0x1
        _tc(
            name='sys_decb_r_n1_half',
            mnemonic='DECB',
            desc='DECB RH0, #1: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA00],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n2_zero
        #   1fd00: aa01                decb	rh0,#0x2
        _tc(
            name='sys_decb_r_n2_zero',
            mnemonic='DECB',
            desc='DECB RH0, #2: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA01],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n2_one
        #   1fe00: aa01                decb	rh0,#0x2
        _tc(
            name='sys_decb_r_n2_one',
            mnemonic='DECB',
            desc='DECB RH0, #2: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA01],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n2_max
        #   1ff00: aa01                decb	rh0,#0x2
        _tc(
            name='sys_decb_r_n2_max',
            mnemonic='DECB',
            desc='DECB RH0, #2: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA01],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n2_half
        #   20000: aa01                decb	rh0,#0x2
        _tc(
            name='sys_decb_r_n2_half',
            mnemonic='DECB',
            desc='DECB RH0, #2: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA01],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n16_zero
        #   20100: aa0f                decb	rh0,#0x10
        _tc(
            name='sys_decb_r_n16_zero',
            mnemonic='DECB',
            desc='DECB RH0, #16: RH0=0x00',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA0F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n16_one
        #   20200: aa0f                decb	rh0,#0x10
        _tc(
            name='sys_decb_r_n16_one',
            mnemonic='DECB',
            desc='DECB RH0, #16: RH0=0x01',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA0F],
            regs={0: 0x0100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n16_max
        #   20300: aa0f                decb	rh0,#0x10
        _tc(
            name='sys_decb_r_n16_max',
            mnemonic='DECB',
            desc='DECB RH0, #16: RH0=0xFF',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA0F],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_decb_r_n16_half
        #   20400: aa0f                decb	rh0,#0x10
        _tc(
            name='sys_decb_r_n16_half',
            mnemonic='DECB',
            desc='DECB RH0, #16: RH0=0x80',
            tags=['inc_dec', 'byte', 'R_mode'],
            code=[0xAA0F],
            regs={0: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_ir_n1_normal
        #   20500: 2920                inc	@r2,#0x1
        _tc(
            name='sys_inc_ir_n1_normal',
            mnemonic='INC',
            desc='INC @R2, #1: [R2]=0x1234',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2920],
            regs={2: 0x0400},
            memory={0x0400: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_ir_n1_max
        #   20600: 2920                inc	@r2,#0x1
        _tc(
            name='sys_inc_ir_n1_max',
            mnemonic='INC',
            desc='INC @R2, #1: [R2]=0xFFFF',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2920],
            regs={2: 0x0400},
            memory={0x0400: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_ir_n2_normal
        #   20700: 2921                inc	@r2,#0x2
        _tc(
            name='sys_inc_ir_n2_normal',
            mnemonic='INC',
            desc='INC @R2, #2: [R2]=0x1234',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2921],
            regs={2: 0x0400},
            memory={0x0400: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_inc_ir_n2_max
        #   20800: 2921                inc	@r2,#0x2
        _tc(
            name='sys_inc_ir_n2_max',
            mnemonic='INC',
            desc='INC @R2, #2: [R2]=0xFFFF',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2921],
            regs={2: 0x0400},
            memory={0x0400: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_ir_n1_normal
        #   20900: 2b20                dec	@r2,#0x1
        _tc(
            name='sys_dec_ir_n1_normal',
            mnemonic='DEC',
            desc='DEC @R2, #1: [R2]=0x1234',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2B20],
            regs={2: 0x0400},
            memory={0x0400: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_ir_n1_max
        #   20a00: 2b20                dec	@r2,#0x1
        _tc(
            name='sys_dec_ir_n1_max',
            mnemonic='DEC',
            desc='DEC @R2, #1: [R2]=0xFFFF',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2B20],
            regs={2: 0x0400},
            memory={0x0400: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_ir_n2_normal
        #   20b00: 2b21                dec	@r2,#0x2
        _tc(
            name='sys_dec_ir_n2_normal',
            mnemonic='DEC',
            desc='DEC @R2, #2: [R2]=0x1234',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2B21],
            regs={2: 0x0400},
            memory={0x0400: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dec_ir_n2_max
        #   20c00: 2b21                dec	@r2,#0x2
        _tc(
            name='sys_dec_ir_n2_max',
            mnemonic='DEC',
            desc='DEC @R2, #2: [R2]=0xFFFF',
            tags=['inc_dec', 'word', 'IR_mode'],
            code=[0x2B21],
            regs={2: 0x0400},
            memory={0x0400: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_zero
        #   20d00: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_zero',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0x0000 * R2=0x0000',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_one
        #   20e00: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_one',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0x0001 * R2=0x0001',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0x0001, 2: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_normal
        #   20f00: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_normal',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0x0064 * R2=0x0032',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0x0064, 2: 0x0032},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_large
        #   21000: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_large',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0xFFFF * R2=0x0002',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0xFFFF, 2: 0x0002},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_max
        #   21100: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_max',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0xFFFF * R2=0xFFFF',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0xFFFF, 2: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_mult_rr_r_signed
        #   21200: 9920                mult	rr0,r2
        _tc(
            name='sys_mult_rr_r_signed',
            mnemonic='MULT',
            desc='MULT RR0, R2: R1=0x8000 * R2=0x0002',
            tags=['mult_div', 'word'],
            code=[0x9920],
            regs={0: 0x0000, 1: 0x8000, 2: 0x0002},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_div_rr_r_normal
        #   21300: 9b20                div	rr0,r2
        _tc(
            name='sys_div_rr_r_normal',
            mnemonic='DIV',
            desc='DIV RR0, R2: 0x00001388 / 0x0064',
            tags=['mult_div', 'word'],
            code=[0x9B20],
            regs={0: 0x0000, 1: 0x1388, 2: 0x0064},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_div_rr_r_remainder
        #   21400: 9b20                div	rr0,r2
        _tc(
            name='sys_div_rr_r_remainder',
            mnemonic='DIV',
            desc='DIV RR0, R2: 0x0000000B / 0x0003',
            tags=['mult_div', 'word'],
            code=[0x9B20],
            regs={0: 0x0000, 1: 0x000B, 2: 0x0003},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_div_rr_r_large
        #   21500: 9b20                div	rr0,r2
        _tc(
            name='sys_div_rr_r_large',
            mnemonic='DIV',
            desc='DIV RR0, R2: 0x0001FFFE / 0xFFFF',
            tags=['mult_div', 'word'],
            code=[0x9B20],
            regs={0: 0x0001, 1: 0xFFFE, 2: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_div_rr_r_one
        #   21600: 9b20                div	rr0,r2
        _tc(
            name='sys_div_rr_r_one',
            mnemonic='DIV',
            desc='DIV RR0, R2: 0x00000001 / 0x0001',
            tags=['mult_div', 'word'],
            code=[0x9B20],
            regs={0: 0x0000, 1: 0x0001, 2: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_multl_rq_rr_normal
        #   21700: 9840                multl	rq0,rr4
        _tc(
            name='sys_multl_rq_rr_normal',
            mnemonic='MULTL',
            desc='MULTL RQ0, RR4: 0x00000064 * 0x00000032',
            tags=['mult_div', 'long'],
            code=[0x9840],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0064, 4: 0x0000, 5: 0x0032},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_multl_rq_rr_large
        #   21800: 9840                multl	rq0,rr4
        _tc(
            name='sys_multl_rq_rr_large',
            mnemonic='MULTL',
            desc='MULTL RQ0, RR4: 0x0000FFFF * 0x0000FFFF',
            tags=['mult_div', 'long'],
            code=[0x9840],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0xFFFF, 4: 0x0000, 5: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_divl_rq_rr_normal
        #   21900: 9a40                divl	rq0,rr4
        _tc(
            name='sys_divl_rq_rr_normal',
            mnemonic='DIVL',
            desc='DIVL RQ0, RR4: 0x0000000000001388 / 0x00000064',
            tags=['mult_div', 'long'],
            code=[0x9A40],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x1388, 4: 0x0000, 5: 0x0064},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_divl_rq_rr_large
        #   21a00: 9a40                divl	rq0,rr4
        _tc(
            name='sys_divl_rq_rr_large',
            mnemonic='DIVL',
            desc='DIVL RQ0, RR4: 0x00000000FFFFFFFE / 0x0000FFFF',
            tags=['mult_div', 'long'],
            code=[0x9A40],
            regs={0: 0x0000, 1: 0x0000, 2: 0xFFFF, 3: 0xFFFE, 4: 0x0000, 5: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_add_no_adj
        #   21b00: b000                dab	rh0
        _tc(
            name='sys_dab_add_no_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0x11, flags=0x4000',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0x1100},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_add_low_adj
        #   21c00: b000                dab	rh0
        _tc(
            name='sys_dab_add_low_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0x1A, flags=0x4004',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0x1A00},
            fcw=fcw_with_flags(H=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_add_high_adj
        #   21d00: b000                dab	rh0
        _tc(
            name='sys_dab_add_high_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0xA1, flags=0x4080',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0xA100},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_add_both_adj
        #   21e00: b000                dab	rh0
        _tc(
            name='sys_dab_add_both_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0x9B, flags=0x4084',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0x9B00},
            fcw=fcw_with_flags(C=1, H=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_sub_no_adj
        #   21f00: b000                dab	rh0
        _tc(
            name='sys_dab_sub_no_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0x22, flags=0x4008',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0x2200},
            fcw=fcw_with_flags(DA=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dab_sub_adj
        #   22000: b000                dab	rh0
        _tc(
            name='sys_dab_sub_adj',
            mnemonic='DAB',
            desc='DAB RH0: 0x7A, flags=0x4088',
            tags=['dab', 'byte'],
            code=[0xB000],
            regs={0: 0x7A00},
            fcw=fcw_with_flags(C=1, DA=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsb_r_zero
        #   22100: b100                extsb	r0
        _tc(
            name='sys_extsb_r_zero',
            mnemonic='EXTSB',
            desc='EXTSB R0: low byte=0x00',
            tags=['sign_extend', 'word'],
            code=[0xB100],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsb_r_pos
        #   22200: b100                extsb	r0
        _tc(
            name='sys_extsb_r_pos',
            mnemonic='EXTSB',
            desc='EXTSB R0: low byte=0x7F',
            tags=['sign_extend', 'word'],
            code=[0xB100],
            regs={0: 0x007F},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsb_r_neg
        #   22300: b100                extsb	r0
        _tc(
            name='sys_extsb_r_neg',
            mnemonic='EXTSB',
            desc='EXTSB R0: low byte=0x80',
            tags=['sign_extend', 'word'],
            code=[0xB100],
            regs={0: 0x0080},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_exts_rr_zero
        #   22400: b10a                exts	rr0
        _tc(
            name='sys_exts_rr_zero',
            mnemonic='EXTS',
            desc='EXTS RR0: R1=0x0000',
            tags=['sign_extend', 'long'],
            code=[0xB10A],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_exts_rr_pos
        #   22500: b10a                exts	rr0
        _tc(
            name='sys_exts_rr_pos',
            mnemonic='EXTS',
            desc='EXTS RR0: R1=0x7FFF',
            tags=['sign_extend', 'long'],
            code=[0xB10A],
            regs={0: 0x0000, 1: 0x7FFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_exts_rr_neg
        #   22600: b10a                exts	rr0
        _tc(
            name='sys_exts_rr_neg',
            mnemonic='EXTS',
            desc='EXTS RR0: R1=0x8000',
            tags=['sign_extend', 'long'],
            code=[0xB10A],
            regs={0: 0x0000, 1: 0x8000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsl_rq_zero
        #   22700: b107                extsl	rq0
        _tc(
            name='sys_extsl_rq_zero',
            mnemonic='EXTSL',
            desc='EXTSL RQ0: RR2=0x00000000',
            tags=['sign_extend', 'quad'],
            code=[0xB107],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsl_rq_pos
        #   22800: b107                extsl	rq0
        _tc(
            name='sys_extsl_rq_pos',
            mnemonic='EXTSL',
            desc='EXTSL RQ0: RR2=0x7FFFFFFF',
            tags=['sign_extend', 'quad'],
            code=[0xB107],
            regs={0: 0x0000, 1: 0x0000, 2: 0x7FFF, 3: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_extsl_rq_neg
        #   22900: b107                extsl	rq0
        _tc(
            name='sys_extsl_rq_neg',
            mnemonic='EXTSL',
            desc='EXTSL RQ0: RR2=0x80000000',
            tags=['sign_extend', 'quad'],
            code=[0xB107],
            regs={0: 0x0000, 1: 0x0000, 2: 0x8000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m0
        #   0200: 8d01                setflg
        _tc(
            name='sys_setflg_m0',
            mnemonic='SETFLG',
            desc='SETFLG none (mask=0x0)',
            tags=['flag_manip', 'control'],
            code=[0x8D01],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m1
        #   22b00: 8d11                setflg	p
        _tc(
            name='sys_setflg_m1',
            mnemonic='SETFLG',
            desc='SETFLG P (mask=0x1)',
            tags=['flag_manip', 'control'],
            code=[0x8D11],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m2
        #   22c00: 8d21                setflg	s
        _tc(
            name='sys_setflg_m2',
            mnemonic='SETFLG',
            desc='SETFLG S (mask=0x2)',
            tags=['flag_manip', 'control'],
            code=[0x8D21],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m3
        #   22d00: 8d31                setflg	s,p
        _tc(
            name='sys_setflg_m3',
            mnemonic='SETFLG',
            desc='SETFLG S, P (mask=0x3)',
            tags=['flag_manip', 'control'],
            code=[0x8D31],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m4
        #   22e00: 8d41                setflg	z
        _tc(
            name='sys_setflg_m4',
            mnemonic='SETFLG',
            desc='SETFLG Z (mask=0x4)',
            tags=['flag_manip', 'control'],
            code=[0x8D41],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m5
        #   22f00: 8d51                setflg	z,p
        _tc(
            name='sys_setflg_m5',
            mnemonic='SETFLG',
            desc='SETFLG Z, P (mask=0x5)',
            tags=['flag_manip', 'control'],
            code=[0x8D51],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m6
        #   23000: 8d61                setflg	z,s
        _tc(
            name='sys_setflg_m6',
            mnemonic='SETFLG',
            desc='SETFLG Z, S (mask=0x6)',
            tags=['flag_manip', 'control'],
            code=[0x8D61],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m7
        #   23100: 8d71                setflg	z,s,p
        _tc(
            name='sys_setflg_m7',
            mnemonic='SETFLG',
            desc='SETFLG Z, S, P (mask=0x7)',
            tags=['flag_manip', 'control'],
            code=[0x8D71],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m8
        #   23200: 8d81                setflg	c
        _tc(
            name='sys_setflg_m8',
            mnemonic='SETFLG',
            desc='SETFLG C (mask=0x8)',
            tags=['flag_manip', 'control'],
            code=[0x8D81],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_m9
        #   23300: 8d91                setflg	c,p
        _tc(
            name='sys_setflg_m9',
            mnemonic='SETFLG',
            desc='SETFLG C, P (mask=0x9)',
            tags=['flag_manip', 'control'],
            code=[0x8D91],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_ma
        #   23400: 8da1                setflg	c,s
        _tc(
            name='sys_setflg_ma',
            mnemonic='SETFLG',
            desc='SETFLG C, S (mask=0xA)',
            tags=['flag_manip', 'control'],
            code=[0x8DA1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_mb
        #   23500: 8db1                setflg	c,s,p
        _tc(
            name='sys_setflg_mb',
            mnemonic='SETFLG',
            desc='SETFLG C, S, P (mask=0xB)',
            tags=['flag_manip', 'control'],
            code=[0x8DB1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_mc
        #   23600: 8dc1                setflg	c,z
        _tc(
            name='sys_setflg_mc',
            mnemonic='SETFLG',
            desc='SETFLG C, Z (mask=0xC)',
            tags=['flag_manip', 'control'],
            code=[0x8DC1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_md
        #   23700: 8dd1                setflg	c,z,p
        _tc(
            name='sys_setflg_md',
            mnemonic='SETFLG',
            desc='SETFLG C, Z, P (mask=0xD)',
            tags=['flag_manip', 'control'],
            code=[0x8DD1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_me
        #   23800: 8de1                setflg	c,z,s
        _tc(
            name='sys_setflg_me',
            mnemonic='SETFLG',
            desc='SETFLG C, Z, S (mask=0xE)',
            tags=['flag_manip', 'control'],
            code=[0x8DE1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_setflg_mf
        #   23900: 8df1                setflg	c,z,s,p
        _tc(
            name='sys_setflg_mf',
            mnemonic='SETFLG',
            desc='SETFLG C, Z, S, P (mask=0xF)',
            tags=['flag_manip', 'control'],
            code=[0x8DF1],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m0
        #   0220: 8d03                resflg
        _tc(
            name='sys_resflg_m0',
            mnemonic='RESFLG',
            desc='RESFLG none (mask=0x0)',
            tags=['flag_manip', 'control'],
            code=[0x8D03],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m1
        #   23b00: 8d13                resflg	p
        _tc(
            name='sys_resflg_m1',
            mnemonic='RESFLG',
            desc='RESFLG P (mask=0x1)',
            tags=['flag_manip', 'control'],
            code=[0x8D13],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m2
        #   23c00: 8d23                resflg	s
        _tc(
            name='sys_resflg_m2',
            mnemonic='RESFLG',
            desc='RESFLG S (mask=0x2)',
            tags=['flag_manip', 'control'],
            code=[0x8D23],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m3
        #   23d00: 8d33                resflg	s,p
        _tc(
            name='sys_resflg_m3',
            mnemonic='RESFLG',
            desc='RESFLG S, P (mask=0x3)',
            tags=['flag_manip', 'control'],
            code=[0x8D33],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m4
        #   23e00: 8d43                resflg	z
        _tc(
            name='sys_resflg_m4',
            mnemonic='RESFLG',
            desc='RESFLG Z (mask=0x4)',
            tags=['flag_manip', 'control'],
            code=[0x8D43],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m5
        #   23f00: 8d53                resflg	z,p
        _tc(
            name='sys_resflg_m5',
            mnemonic='RESFLG',
            desc='RESFLG Z, P (mask=0x5)',
            tags=['flag_manip', 'control'],
            code=[0x8D53],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m6
        #   24000: 8d63                resflg	z,s
        _tc(
            name='sys_resflg_m6',
            mnemonic='RESFLG',
            desc='RESFLG Z, S (mask=0x6)',
            tags=['flag_manip', 'control'],
            code=[0x8D63],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m7
        #   24100: 8d73                resflg	z,s,p
        _tc(
            name='sys_resflg_m7',
            mnemonic='RESFLG',
            desc='RESFLG Z, S, P (mask=0x7)',
            tags=['flag_manip', 'control'],
            code=[0x8D73],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m8
        #   24200: 8d83                resflg	c
        _tc(
            name='sys_resflg_m8',
            mnemonic='RESFLG',
            desc='RESFLG C (mask=0x8)',
            tags=['flag_manip', 'control'],
            code=[0x8D83],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_m9
        #   24300: 8d93                resflg	c,p
        _tc(
            name='sys_resflg_m9',
            mnemonic='RESFLG',
            desc='RESFLG C, P (mask=0x9)',
            tags=['flag_manip', 'control'],
            code=[0x8D93],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_ma
        #   24400: 8da3                resflg	c,s
        _tc(
            name='sys_resflg_ma',
            mnemonic='RESFLG',
            desc='RESFLG C, S (mask=0xA)',
            tags=['flag_manip', 'control'],
            code=[0x8DA3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_mb
        #   24500: 8db3                resflg	c,s,p
        _tc(
            name='sys_resflg_mb',
            mnemonic='RESFLG',
            desc='RESFLG C, S, P (mask=0xB)',
            tags=['flag_manip', 'control'],
            code=[0x8DB3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_mc
        #   24600: 8dc3                resflg	c,z
        _tc(
            name='sys_resflg_mc',
            mnemonic='RESFLG',
            desc='RESFLG C, Z (mask=0xC)',
            tags=['flag_manip', 'control'],
            code=[0x8DC3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_md
        #   24700: 8dd3                resflg	c,z,p
        _tc(
            name='sys_resflg_md',
            mnemonic='RESFLG',
            desc='RESFLG C, Z, P (mask=0xD)',
            tags=['flag_manip', 'control'],
            code=[0x8DD3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_me
        #   24800: 8de3                resflg	c,z,s
        _tc(
            name='sys_resflg_me',
            mnemonic='RESFLG',
            desc='RESFLG C, Z, S (mask=0xE)',
            tags=['flag_manip', 'control'],
            code=[0x8DE3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_resflg_mf
        #   24900: 8df3                resflg	c,z,s,p
        _tc(
            name='sys_resflg_mf',
            mnemonic='RESFLG',
            desc='RESFLG C, Z, S, P (mask=0xF)',
            tags=['flag_manip', 'control'],
            code=[0x8DF3],
            fcw=fcw_with_flags(C=1, Z=1, S=1, V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m0
        #   0240: 8d05                comflg
        _tc(
            name='sys_comflg_m0',
            mnemonic='COMFLG',
            desc='COMFLG none (mask=0x0)',
            tags=['flag_manip', 'control'],
            code=[0x8D05],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m1
        #   24b00: 8d15                comflg	p
        _tc(
            name='sys_comflg_m1',
            mnemonic='COMFLG',
            desc='COMFLG P (mask=0x1)',
            tags=['flag_manip', 'control'],
            code=[0x8D15],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m2
        #   24c00: 8d25                comflg	s
        _tc(
            name='sys_comflg_m2',
            mnemonic='COMFLG',
            desc='COMFLG S (mask=0x2)',
            tags=['flag_manip', 'control'],
            code=[0x8D25],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m3
        #   24d00: 8d35                comflg	s,p
        _tc(
            name='sys_comflg_m3',
            mnemonic='COMFLG',
            desc='COMFLG S, P (mask=0x3)',
            tags=['flag_manip', 'control'],
            code=[0x8D35],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m4
        #   24e00: 8d45                comflg	z
        _tc(
            name='sys_comflg_m4',
            mnemonic='COMFLG',
            desc='COMFLG Z (mask=0x4)',
            tags=['flag_manip', 'control'],
            code=[0x8D45],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m5
        #   24f00: 8d55                comflg	z,p
        _tc(
            name='sys_comflg_m5',
            mnemonic='COMFLG',
            desc='COMFLG Z, P (mask=0x5)',
            tags=['flag_manip', 'control'],
            code=[0x8D55],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m6
        #   25000: 8d65                comflg	z,s
        _tc(
            name='sys_comflg_m6',
            mnemonic='COMFLG',
            desc='COMFLG Z, S (mask=0x6)',
            tags=['flag_manip', 'control'],
            code=[0x8D65],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m7
        #   25100: 8d75                comflg	z,s,p
        _tc(
            name='sys_comflg_m7',
            mnemonic='COMFLG',
            desc='COMFLG Z, S, P (mask=0x7)',
            tags=['flag_manip', 'control'],
            code=[0x8D75],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m8
        #   25200: 8d85                comflg	c
        _tc(
            name='sys_comflg_m8',
            mnemonic='COMFLG',
            desc='COMFLG C (mask=0x8)',
            tags=['flag_manip', 'control'],
            code=[0x8D85],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_m9
        #   25300: 8d95                comflg	c,p
        _tc(
            name='sys_comflg_m9',
            mnemonic='COMFLG',
            desc='COMFLG C, P (mask=0x9)',
            tags=['flag_manip', 'control'],
            code=[0x8D95],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_ma
        #   25400: 8da5                comflg	c,s
        _tc(
            name='sys_comflg_ma',
            mnemonic='COMFLG',
            desc='COMFLG C, S (mask=0xA)',
            tags=['flag_manip', 'control'],
            code=[0x8DA5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_mb
        #   25500: 8db5                comflg	c,s,p
        _tc(
            name='sys_comflg_mb',
            mnemonic='COMFLG',
            desc='COMFLG C, S, P (mask=0xB)',
            tags=['flag_manip', 'control'],
            code=[0x8DB5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_mc
        #   25600: 8dc5                comflg	c,z
        _tc(
            name='sys_comflg_mc',
            mnemonic='COMFLG',
            desc='COMFLG C, Z (mask=0xC)',
            tags=['flag_manip', 'control'],
            code=[0x8DC5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_md
        #   25700: 8dd5                comflg	c,z,p
        _tc(
            name='sys_comflg_md',
            mnemonic='COMFLG',
            desc='COMFLG C, Z, P (mask=0xD)',
            tags=['flag_manip', 'control'],
            code=[0x8DD5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_me
        #   25800: 8de5                comflg	c,z,s
        _tc(
            name='sys_comflg_me',
            mnemonic='COMFLG',
            desc='COMFLG C, Z, S (mask=0xE)',
            tags=['flag_manip', 'control'],
            code=[0x8DE5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_comflg_mf
        #   25900: 8df5                comflg	c,z,s,p
        _tc(
            name='sys_comflg_mf',
            mnemonic='COMFLG',
            desc='COMFLG C, Z, S, P (mask=0xF)',
            tags=['flag_manip', 'control'],
            code=[0x8DF5],
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_f_true
        #   25a00: af00                tcc	f,r0
        _tc(
            name='sys_tcc_f_true',
            mnemonic='TCC',
            desc='TCC F, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_f_false
        #   25b00: af00                tcc	f,r0
        _tc(
            name='sys_tcc_f_false',
            mnemonic='TCC',
            desc='TCC F, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_f_true
        #   25c00: ae00                tccb	f,rh0
        _tc(
            name='sys_tccb_f_true',
            mnemonic='TCCB',
            desc='TCCB F, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_f_false
        #   25d00: ae00                tccb	f,rh0
        _tc(
            name='sys_tccb_f_false',
            mnemonic='TCCB',
            desc='TCCB F, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE00],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_lt_true
        #   25e00: af01                tcc	lt,r0
        _tc(
            name='sys_tcc_lt_true',
            mnemonic='TCC',
            desc='TCC LT, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF01],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_lt_false
        #   25f00: af01                tcc	lt,r0
        _tc(
            name='sys_tcc_lt_false',
            mnemonic='TCC',
            desc='TCC LT, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF01],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_lt_true
        #   26000: ae01                tccb	lt,rh0
        _tc(
            name='sys_tccb_lt_true',
            mnemonic='TCCB',
            desc='TCCB LT, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE01],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_lt_false
        #   26100: ae01                tccb	lt,rh0
        _tc(
            name='sys_tccb_lt_false',
            mnemonic='TCCB',
            desc='TCCB LT, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE01],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_le_true
        #   26200: af02                tcc	le,r0
        _tc(
            name='sys_tcc_le_true',
            mnemonic='TCC',
            desc='TCC LE, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF02],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_le_false
        #   26300: af02                tcc	le,r0
        _tc(
            name='sys_tcc_le_false',
            mnemonic='TCC',
            desc='TCC LE, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF02],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_le_true
        #   26400: ae02                tccb	le,rh0
        _tc(
            name='sys_tccb_le_true',
            mnemonic='TCCB',
            desc='TCCB LE, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE02],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_le_false
        #   26500: ae02                tccb	le,rh0
        _tc(
            name='sys_tccb_le_false',
            mnemonic='TCCB',
            desc='TCCB LE, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE02],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ule_true
        #   26600: af03                tcc	ule,r0
        _tc(
            name='sys_tcc_ule_true',
            mnemonic='TCC',
            desc='TCC ULE, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF03],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ule_false
        #   26700: af03                tcc	ule,r0
        _tc(
            name='sys_tcc_ule_false',
            mnemonic='TCC',
            desc='TCC ULE, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF03],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ule_true
        #   26800: ae03                tccb	ule,rh0
        _tc(
            name='sys_tccb_ule_true',
            mnemonic='TCCB',
            desc='TCCB ULE, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE03],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ule_false
        #   26900: ae03                tccb	ule,rh0
        _tc(
            name='sys_tccb_ule_false',
            mnemonic='TCCB',
            desc='TCCB ULE, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE03],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ov_true
        #   26a00: af04                tcc	ov/pe,r0
        _tc(
            name='sys_tcc_ov_true',
            mnemonic='TCC',
            desc='TCC OV, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF04],
            regs={0: 0x0000},
            fcw=fcw_with_flags(V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ov_false
        #   26b00: af04                tcc	ov/pe,r0
        _tc(
            name='sys_tcc_ov_false',
            mnemonic='TCC',
            desc='TCC OV, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF04],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ov_true
        #   26c00: ae04                tccb	ov/pe,rh0
        _tc(
            name='sys_tccb_ov_true',
            mnemonic='TCCB',
            desc='TCCB OV, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE04],
            regs={0: 0x0000},
            fcw=fcw_with_flags(V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ov_false
        #   26d00: ae04                tccb	ov/pe,rh0
        _tc(
            name='sys_tccb_ov_false',
            mnemonic='TCCB',
            desc='TCCB OV, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE04],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_mi_true
        #   26e00: af05                tcc	mi,r0
        _tc(
            name='sys_tcc_mi_true',
            mnemonic='TCC',
            desc='TCC MI, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF05],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_mi_false
        #   26f00: af05                tcc	mi,r0
        _tc(
            name='sys_tcc_mi_false',
            mnemonic='TCC',
            desc='TCC MI, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF05],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_mi_true
        #   27000: ae05                tccb	mi,rh0
        _tc(
            name='sys_tccb_mi_true',
            mnemonic='TCCB',
            desc='TCCB MI, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE05],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_mi_false
        #   27100: ae05                tccb	mi,rh0
        _tc(
            name='sys_tccb_mi_false',
            mnemonic='TCCB',
            desc='TCCB MI, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE05],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_eq_true
        #   27200: af06                tcc	eq,r0
        _tc(
            name='sys_tcc_eq_true',
            mnemonic='TCC',
            desc='TCC EQ, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF06],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_eq_false
        #   27300: af06                tcc	eq,r0
        _tc(
            name='sys_tcc_eq_false',
            mnemonic='TCC',
            desc='TCC EQ, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF06],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_eq_true
        #   27400: ae06                tccb	eq,rh0
        _tc(
            name='sys_tccb_eq_true',
            mnemonic='TCCB',
            desc='TCCB EQ, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE06],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_eq_false
        #   27500: ae06                tccb	eq,rh0
        _tc(
            name='sys_tccb_eq_false',
            mnemonic='TCCB',
            desc='TCCB EQ, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE06],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_c_true
        #   27600: af07                tcc	c/ult,r0
        _tc(
            name='sys_tcc_c_true',
            mnemonic='TCC',
            desc='TCC C, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF07],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_c_false
        #   27700: af07                tcc	c/ult,r0
        _tc(
            name='sys_tcc_c_false',
            mnemonic='TCC',
            desc='TCC C, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF07],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_c_true
        #   27800: ae07                tccb	c/ult,rh0
        _tc(
            name='sys_tccb_c_true',
            mnemonic='TCCB',
            desc='TCCB C, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE07],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_c_false
        #   27900: ae07                tccb	c/ult,rh0
        _tc(
            name='sys_tccb_c_false',
            mnemonic='TCCB',
            desc='TCCB C, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE07],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_t_true
        #   27a00: af08                tcc	t,r0
        _tc(
            name='sys_tcc_t_true',
            mnemonic='TCC',
            desc='TCC T, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_t_false
        #   27b00: af08                tcc	t,r0
        _tc(
            name='sys_tcc_t_false',
            mnemonic='TCC',
            desc='TCC T, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_t_true
        #   27c00: ae08                tccb	t,rh0
        _tc(
            name='sys_tccb_t_true',
            mnemonic='TCCB',
            desc='TCCB T, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_t_false
        #   27d00: ae08                tccb	t,rh0
        _tc(
            name='sys_tccb_t_false',
            mnemonic='TCCB',
            desc='TCCB T, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE08],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ge_true
        #   27e00: af09                tcc	ge,r0
        _tc(
            name='sys_tcc_ge_true',
            mnemonic='TCC',
            desc='TCC GE, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF09],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ge_false
        #   27f00: af09                tcc	ge,r0
        _tc(
            name='sys_tcc_ge_false',
            mnemonic='TCC',
            desc='TCC GE, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF09],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ge_true
        #   28000: ae09                tccb	ge,rh0
        _tc(
            name='sys_tccb_ge_true',
            mnemonic='TCCB',
            desc='TCCB GE, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE09],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ge_false
        #   28100: ae09                tccb	ge,rh0
        _tc(
            name='sys_tccb_ge_false',
            mnemonic='TCCB',
            desc='TCCB GE, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE09],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_gt_true
        #   28200: af0a                tcc	gt,r0
        _tc(
            name='sys_tcc_gt_true',
            mnemonic='TCC',
            desc='TCC GT, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0A],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_gt_false
        #   28300: af0a                tcc	gt,r0
        _tc(
            name='sys_tcc_gt_false',
            mnemonic='TCC',
            desc='TCC GT, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0A],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_gt_true
        #   28400: ae0a                tccb	gt,rh0
        _tc(
            name='sys_tccb_gt_true',
            mnemonic='TCCB',
            desc='TCCB GT, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0A],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_gt_false
        #   28500: ae0a                tccb	gt,rh0
        _tc(
            name='sys_tccb_gt_false',
            mnemonic='TCCB',
            desc='TCCB GT, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0A],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ugt_true
        #   28600: af0b                tcc	ugt,r0
        _tc(
            name='sys_tcc_ugt_true',
            mnemonic='TCC',
            desc='TCC UGT, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0B],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ugt_false
        #   28700: af0b                tcc	ugt,r0
        _tc(
            name='sys_tcc_ugt_false',
            mnemonic='TCC',
            desc='TCC UGT, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0B],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ugt_true
        #   28800: ae0b                tccb	ugt,rh0
        _tc(
            name='sys_tccb_ugt_true',
            mnemonic='TCCB',
            desc='TCCB UGT, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0B],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ugt_false
        #   28900: ae0b                tccb	ugt,rh0
        _tc(
            name='sys_tccb_ugt_false',
            mnemonic='TCCB',
            desc='TCCB UGT, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0B],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_nov_true
        #   28a00: af0c                tcc	nov/po,r0
        _tc(
            name='sys_tcc_nov_true',
            mnemonic='TCC',
            desc='TCC NOV, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0C],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_nov_false
        #   28b00: af0c                tcc	nov/po,r0
        _tc(
            name='sys_tcc_nov_false',
            mnemonic='TCC',
            desc='TCC NOV, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0C],
            regs={0: 0x0000},
            fcw=fcw_with_flags(V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_nov_true
        #   28c00: ae0c                tccb	nov/po,rh0
        _tc(
            name='sys_tccb_nov_true',
            mnemonic='TCCB',
            desc='TCCB NOV, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0C],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_nov_false
        #   28d00: ae0c                tccb	nov/po,rh0
        _tc(
            name='sys_tccb_nov_false',
            mnemonic='TCCB',
            desc='TCCB NOV, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0C],
            regs={0: 0x0000},
            fcw=fcw_with_flags(V=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_pl_true
        #   28e00: af0d                tcc	pl,r0
        _tc(
            name='sys_tcc_pl_true',
            mnemonic='TCC',
            desc='TCC PL, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_pl_false
        #   28f00: af0d                tcc	pl,r0
        _tc(
            name='sys_tcc_pl_false',
            mnemonic='TCC',
            desc='TCC PL, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_pl_true
        #   29000: ae0d                tccb	pl,rh0
        _tc(
            name='sys_tccb_pl_true',
            mnemonic='TCCB',
            desc='TCCB PL, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_pl_false
        #   29100: ae0d                tccb	pl,rh0
        _tc(
            name='sys_tccb_pl_false',
            mnemonic='TCCB',
            desc='TCCB PL, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ne_true
        #   29200: af0e                tcc	ne,r0
        _tc(
            name='sys_tcc_ne_true',
            mnemonic='TCC',
            desc='TCC NE, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0E],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_ne_false
        #   29300: af0e                tcc	ne,r0
        _tc(
            name='sys_tcc_ne_false',
            mnemonic='TCC',
            desc='TCC NE, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0E],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ne_true
        #   29400: ae0e                tccb	ne,rh0
        _tc(
            name='sys_tccb_ne_true',
            mnemonic='TCCB',
            desc='TCCB NE, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0E],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_ne_false
        #   29500: ae0e                tccb	ne,rh0
        _tc(
            name='sys_tccb_ne_false',
            mnemonic='TCCB',
            desc='TCCB NE, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0E],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_nc_true
        #   29600: af0f                tcc	nc/uge,r0
        _tc(
            name='sys_tcc_nc_true',
            mnemonic='TCC',
            desc='TCC NC, R0: condition true',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tcc_nc_false
        #   29700: af0f                tcc	nc/uge,r0
        _tc(
            name='sys_tcc_nc_false',
            mnemonic='TCC',
            desc='TCC NC, R0: condition false',
            tags=['tcc', 'word', 'control'],
            code=[0xAF0F],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_nc_true
        #   29800: ae0f                tccb	nc/uge,rh0
        _tc(
            name='sys_tccb_nc_true',
            mnemonic='TCCB',
            desc='TCCB NC, RH0: condition true',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0F],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_tccb_nc_false
        #   29900: ae0f                tccb	nc/uge,rh0
        _tc(
            name='sys_tccb_nc_false',
            mnemonic='TCCB',
            desc='TCCB NC, RH0: condition false',
            tags=['tcc', 'byte', 'control'],
            code=[0xAE0F],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_r_normal
        #   29a00: a110                ld	r0,r1
        _tc(
            name='sys_ld_r_r_normal',
            mnemonic='LD',
            desc='LD R0, R1: R1=0x1234',
            tags=['load', 'word', 'R_mode'],
            code=[0xA110],
            regs={0: 0x0000, 1: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_r_zero
        #   29b00: a110                ld	r0,r1
        _tc(
            name='sys_ld_r_r_zero',
            mnemonic='LD',
            desc='LD R0, R1: R1=0x0000',
            tags=['load', 'word', 'R_mode'],
            code=[0xA110],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_r_max
        #   29c00: a110                ld	r0,r1
        _tc(
            name='sys_ld_r_r_max',
            mnemonic='LD',
            desc='LD R0, R1: R1=0xFFFF',
            tags=['load', 'word', 'R_mode'],
            code=[0xA110],
            regs={0: 0x0000, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_im_normal
        #   29d00: 2100 1234           ld	r0,#0x1234
        _tc(
            name='sys_ld_r_im_normal',
            mnemonic='LD',
            desc='LD R0, #0x1234',
            tags=['load', 'word', 'IM_mode'],
            code=[0x2100, 0x1234],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_im_zero
        #   29e00: 2100 0000           ld	r0,#0x0
        _tc(
            name='sys_ld_r_im_zero',
            mnemonic='LD',
            desc='LD R0, #0x0000',
            tags=['load', 'word', 'IM_mode'],
            code=[0x2100, 0x0000],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_im_max
        #   29f00: 2100 ffff           ld	r0,#0xffff
        _tc(
            name='sys_ld_r_im_max',
            mnemonic='LD',
            desc='LD R0, #0xFFFF',
            tags=['load', 'word', 'IM_mode'],
            code=[0x2100, 0xFFFF],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_ir_normal
        #   2a000: 2120                ld	r0,@r2
        _tc(
            name='sys_ld_r_ir_normal',
            mnemonic='LD',
            desc='LD R0, @R2: [R2]=0xABCD',
            tags=['load', 'word', 'IR_mode'],
            code=[0x2120],
            regs={0: 0x0000, 2: 0x0400},
            memory={0x0400: 0xABCD},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_ir_zero
        #   2a100: 2120                ld	r0,@r2
        _tc(
            name='sys_ld_r_ir_zero',
            mnemonic='LD',
            desc='LD R0, @R2: [R2]=0x0000',
            tags=['load', 'word', 'IR_mode'],
            code=[0x2120],
            regs={0: 0x0000, 2: 0x0400},
            memory={0x0400: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_da_normal
        #   2a200: 6100 0400           ld	r0,0x400
        _tc(
            name='sys_ld_r_da_normal',
            mnemonic='LD',
            desc='LD R0, 0x0400: [DA]=0xDEAD',
            tags=['load', 'word', 'DA_mode'],
            code=[0x6100, 0x0400],
            regs={0: 0x0000},
            memory={0x0400: 0xDEAD},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_da_zero
        #   2a300: 6100 0400           ld	r0,0x400
        _tc(
            name='sys_ld_r_da_zero',
            mnemonic='LD',
            desc='LD R0, 0x0400: [DA]=0x0000',
            tags=['load', 'word', 'DA_mode'],
            code=[0x6100, 0x0400],
            regs={0: 0x0000},
            memory={0x0400: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_da_r_normal
        #   2a400: 6f00 0400           ld	0x400,r0
        _tc(
            name='sys_ld_da_r_normal',
            mnemonic='LD',
            desc='LD 0x0400, R0: R0=0xCAFE',
            tags=['load', 'word', 'DA_mode', 'store'],
            code=[0x6F00, 0x0400],
            regs={0: 0xCAFE},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_da_r_zero
        #   2a500: 6f00 0400           ld	0x400,r0
        _tc(
            name='sys_ld_da_r_zero',
            mnemonic='LD',
            desc='LD 0x0400, R0: R0=0x0000',
            tags=['load', 'word', 'DA_mode', 'store'],
            code=[0x6F00, 0x0400],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_r_x_basic
        #   2a600: 6120 0400           ld	r0,0x400(r2)
        _tc(
            name='sys_ld_r_x_basic',
            mnemonic='LD',
            desc='LD R0, 0x0400(R2): indexed load',
            tags=['load', 'word', 'X_mode'],
            code=[0x6120, 0x0400],
            regs={0: 0x0000, 2: 0x0004},
            memory={0x0404: 0xBEEF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ld_ir_r_basic
        #   2a700: 2f20                ld	@r2,r0
        _tc(
            name='sys_ld_ir_r_basic',
            mnemonic='LD',
            desc='LD @R2, R0: indirect store',
            tags=['load', 'word', 'IR_mode', 'store'],
            code=[0x2F20],
            regs={0: 0x1234, 2: 0x0400},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldb_r_r_normal
        #   2a800: a010                ldb	rh0,rh1
        _tc(
            name='sys_ldb_r_r_normal',
            mnemonic='LDB',
            desc='LDB RH0, RH1: RH1=0x42',
            tags=['load', 'byte', 'R_mode'],
            code=[0xA010],
            regs={0: 0x0000, 1: 0x4200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldb_r_r_zero
        #   2a900: a010                ldb	rh0,rh1
        _tc(
            name='sys_ldb_r_r_zero',
            mnemonic='LDB',
            desc='LDB RH0, RH1: RH1=0x00',
            tags=['load', 'byte', 'R_mode'],
            code=[0xA010],
            regs={0: 0x0000, 1: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldb_r_im_normal
        #   02c0: c042                ldb	rh0,#0x42
        _tc(
            name='sys_ldb_r_im_normal',
            mnemonic='LDB',
            desc='LDB RH0, #0x42',
            tags=['load', 'byte', 'IM_mode'],
            code=[0xC042],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldb_r_im_max
        #   02d0: c0ff                ldb	rh0,#0xff
        _tc(
            name='sys_ldb_r_im_max',
            mnemonic='LDB',
            desc='LDB RH0, #0xFF',
            tags=['load', 'byte', 'IM_mode'],
            code=[0xC0FF],
            regs={0: 0xFF00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldl_rr_rr_normal
        #   2ac00: 9420                ldl	rr0,rr2
        _tc(
            name='sys_ldl_rr_rr_normal',
            mnemonic='LDL',
            desc='LDL RR0, RR2: 0x12345678',
            tags=['load', 'long', 'R_mode'],
            code=[0x9420],
            regs={0: 0x0000, 1: 0x0000, 2: 0x1234, 3: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldl_rr_rr_zero
        #   2ad00: 9420                ldl	rr0,rr2
        _tc(
            name='sys_ldl_rr_rr_zero',
            mnemonic='LDL',
            desc='LDL RR0, RR2: 0x00000000',
            tags=['load', 'long', 'R_mode'],
            code=[0x9420],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0000, 3: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldl_rr_im_normal
        #   0200: 1400 dead beef      ldl rr0,#0xDEADBEEF
        _tc(
            name='sys_ldl_rr_im_normal',
            mnemonic='LDL',
            desc='LDL RR0, #0xDEADBEEF',
            tags=['load', 'long', 'IM_mode'],
            code=[0x1400, 0xDEAD, 0xBEEF],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldl_rr_im_zero
        #   0200: 1400 0000 0000      ldl rr0,#0x00000000
        _tc(
            name='sys_ldl_rr_im_zero',
            mnemonic='LDL',
            desc='LDL RR0, #0x00000000',
            tags=['load', 'long', 'IM_mode'],
            code=[0x1400, 0x0000, 0x0000],
            regs={0: 0xFFFF, 1: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldl_rr_ir_basic
        #   2b000: 1420                ldl	rr0,@r2
        _tc(
            name='sys_ldl_rr_ir_basic',
            mnemonic='LDL',
            desc='LDL RR0, @R2: load long from memory',
            tags=['load', 'long', 'IR_mode'],
            code=[0x1420],
            regs={0: 0x0000, 1: 0x0000, 2: 0x0400},
            memory={0x0400: 0xDEAD, 0x0402: 0xBEEF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldk_r_n0
        #   2b100: bd00                ldk	r0,#0x0
        _tc(
            name='sys_ldk_r_n0',
            mnemonic='LDK',
            desc='LDK R0, #0',
            tags=['load', 'word', 'R_mode'],
            code=[0xBD00],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldk_r_n5
        #   2b200: bd05                ldk	r0,#0x5
        _tc(
            name='sys_ldk_r_n5',
            mnemonic='LDK',
            desc='LDK R0, #5',
            tags=['load', 'word', 'R_mode'],
            code=[0xBD05],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldk_r_n15
        #   2b300: bd0f                ldk	r0,#0xf
        _tc(
            name='sys_ldk_r_n15',
            mnemonic='LDK',
            desc='LDK R0, #15',
            tags=['load', 'word', 'R_mode'],
            code=[0xBD0F],
            regs={0: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldm_load_3
        #   2b400: 1c21 0302           ldm	r3,@r2,#0x3
        _tc(
            name='sys_ldm_load_3',
            mnemonic='LDM',
            desc='LDM R3, @R2, #3: load 3 regs from memory',
            tags=['load', 'word', 'IR_mode'],
            code=[0x1C21, 0x0302],
            regs={2: 0x0400, 3: 0x0000, 4: 0x0000, 5: 0x0000},
            memory={0x0400: 0x1111, 0x0402: 0x2222, 0x0404: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldm_store_3
        #   2b500: 1c29 0302           ldm	@r2,r3,#0x3
        _tc(
            name='sys_ldm_store_3',
            mnemonic='LDM',
            desc='LDM @R2, R3, #3: store 3 regs to memory',
            tags=['load', 'word', 'IR_mode', 'store'],
            code=[0x1C29, 0x0302],
            regs={2: 0x0400, 3: 0xAAAA, 4: 0xBBBB, 5: 0xCCCC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ex_r_r_normal
        #   2b600: ad10                ex	r0,r1
        _tc(
            name='sys_ex_r_r_normal',
            mnemonic='EX',
            desc='EX R0, R1: 0x1234, 0x5678',
            tags=['exchange', 'word', 'R_mode'],
            code=[0xAD10],
            regs={0: 0x1234, 1: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ex_r_r_same
        #   2b700: ad10                ex	r0,r1
        _tc(
            name='sys_ex_r_r_same',
            mnemonic='EX',
            desc='EX R0, R1: 0xAAAA, 0xAAAA',
            tags=['exchange', 'word', 'R_mode'],
            code=[0xAD10],
            regs={0: 0xAAAA, 1: 0xAAAA},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_exb_r_r_normal
        #   2b800: ac10                exb	rh0,rh1
        _tc(
            name='sys_exb_r_r_normal',
            mnemonic='EXB',
            desc='EXB RH0, RH1: 0x12, 0x56',
            tags=['exchange', 'byte', 'R_mode'],
            code=[0xAC10],
            regs={0: 0x1200, 1: 0x5600},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_exb_r_r_same
        #   2b900: ac10                exb	rh0,rh1
        _tc(
            name='sys_exb_r_r_same',
            mnemonic='EXB',
            desc='EXB RH0, RH1: 0xAA, 0xAA',
            tags=['exchange', 'byte', 'R_mode'],
            code=[0xAC10],
            regs={0: 0xAA00, 1: 0xAA00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_push_r_normal
        #   2ba00: 93f0                push	@r15,r0
        _tc(
            name='sys_push_r_normal',
            mnemonic='PUSH',
            desc='PUSH @R15, R0: 0x1234',
            tags=['stack', 'word'],
            code=[0x93F0],
            regs={0: 0x1234, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_push_r_max
        #   2bb00: 93f0                push	@r15,r0
        _tc(
            name='sys_push_r_max',
            mnemonic='PUSH',
            desc='PUSH @R15, R0: 0xFFFF',
            tags=['stack', 'word'],
            code=[0x93F0],
            regs={0: 0xFFFF, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_pop_r_normal
        #   2bc00: 97f0                pop	r0,@r15
        _tc(
            name='sys_pop_r_normal',
            mnemonic='POP',
            desc='POP R0, @R15: [SP]=0xABCD',
            tags=['stack', 'word'],
            code=[0x97F0],
            regs={0: 0x0000, 15: 0x0EFE},
            memory={0x0EFE: 0xABCD},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_pop_r_zero
        #   2bd00: 97f0                pop	r0,@r15
        _tc(
            name='sys_pop_r_zero',
            mnemonic='POP',
            desc='POP R0, @R15: [SP]=0x0000',
            tags=['stack', 'word'],
            code=[0x97F0],
            regs={0: 0x0000, 15: 0x0EFE},
            memory={0x0EFE: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_pushl_rr_normal
        #   2be00: 91f0                pushl	@r15,rr0
        _tc(
            name='sys_pushl_rr_normal',
            mnemonic='PUSHL',
            desc='PUSHL @R15, RR0: 0x12345678',
            tags=['stack', 'long'],
            code=[0x91F0],
            regs={0: 0x1234, 1: 0x5678, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_pushl_rr_zero
        #   2bf00: 91f0                pushl	@r15,rr0
        _tc(
            name='sys_pushl_rr_zero',
            mnemonic='PUSHL',
            desc='PUSHL @R15, RR0: 0x00000000',
            tags=['stack', 'long'],
            code=[0x91F0],
            regs={0: 0x0000, 1: 0x0000, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_popl_rr_normal
        #   2c000: 95f0                popl	rr0,@r15
        _tc(
            name='sys_popl_rr_normal',
            mnemonic='POPL',
            desc='POPL RR0, @R15: 0xDEADBEEF',
            tags=['stack', 'long'],
            code=[0x95F0],
            regs={0: 0x0000, 1: 0x0000, 15: 0x0EFC},
            memory={0x0EFC: 0xDEAD, 0x0EFE: 0xBEEF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_popl_rr_zero
        #   2c100: 95f0                popl	rr0,@r15
        _tc(
            name='sys_popl_rr_zero',
            mnemonic='POPL',
            desc='POPL RR0, @R15: 0x00000000',
            tags=['stack', 'long'],
            code=[0x95F0],
            regs={0: 0x0000, 1: 0x0000, 15: 0x0EFC},
            memory={0x0EFC: 0x0000, 0x0EFE: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_eq_taken
        #   0200: 5e06 0208           jp eq,.Ltarget
        #   0204: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0208: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_eq_taken',
            mnemonic='JP',
            desc='JP EQ: taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E06, 0x0208, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_eq_not_taken
        #   0200: 5e06 0204           jp eq,.Ltarget
        #         .Ltarget:
        #   0204: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_eq_not_taken',
            mnemonic='JP',
            desc='JP EQ: not taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E06, 0x0204, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_eq_taken
        #   0200: e602                jr eq,.Ltarget
        #   0202: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0206: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_eq_taken',
            mnemonic='JR',
            desc='JR EQ: taken (+2)',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE602, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_eq_not_taken
        #   0200: e600                jr eq,.Ltarget
        #         .Ltarget:
        #   0202: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_eq_not_taken',
            mnemonic='JR',
            desc='JR EQ: not taken',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE600, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_c_taken
        #   0200: 5e07 0208           jp c/ult,.Ltarget
        #   0204: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0208: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_c_taken',
            mnemonic='JP',
            desc='JP C: taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E07, 0x0208, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_c_not_taken
        #   0200: 5e07 0204           jp c/ult,.Ltarget
        #         .Ltarget:
        #   0204: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_c_not_taken',
            mnemonic='JP',
            desc='JP C: not taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E07, 0x0204, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_c_taken
        #   0200: e702                jr c/ult,.Ltarget
        #   0202: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0206: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_c_taken',
            mnemonic='JR',
            desc='JR C: taken (+2)',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE702, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_c_not_taken
        #   0200: e700                jr c/ult,.Ltarget
        #         .Ltarget:
        #   0202: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_c_not_taken',
            mnemonic='JR',
            desc='JR C: not taken',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE700, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_mi_taken
        #   0200: 5e05 0208           jp mi,.Ltarget
        #   0204: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0208: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_mi_taken',
            mnemonic='JP',
            desc='JP MI: taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E05, 0x0208, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_mi_not_taken
        #   0200: 5e05 0204           jp mi,.Ltarget
        #         .Ltarget:
        #   0204: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_mi_not_taken',
            mnemonic='JP',
            desc='JP MI: not taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E05, 0x0204, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_mi_taken
        #   0200: e502                jr mi,.Ltarget
        #   0202: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0206: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_mi_taken',
            mnemonic='JR',
            desc='JR MI: taken (+2)',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE502, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_mi_not_taken
        #   0200: e500                jr mi,.Ltarget
        #         .Ltarget:
        #   0202: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_mi_not_taken',
            mnemonic='JR',
            desc='JR MI: not taken',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xE500, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_ne_taken
        #   0200: 5e0e 0208           jp ne,.Ltarget
        #   0204: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0208: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_ne_taken',
            mnemonic='JP',
            desc='JP NE: taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E0E, 0x0208, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jp_ne_not_taken
        #   0200: 5e0e 0204           jp ne,.Ltarget
        #         .Ltarget:
        #   0204: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jp_ne_not_taken',
            mnemonic='JP',
            desc='JP NE: not taken',
            tags=['branch', 'word', 'DA_mode'],
            code=[0x5E0E, 0x0204, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_ne_taken
        #   0200: ee02                jr ne,.Ltarget
        #   0202: 2100 bad0           ld r0,#0xbad0
        #         .Ltarget:
        #   0206: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_ne_taken',
            mnemonic='JR',
            desc='JR NE: taken (+2)',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xEE02, 0x2100, 0xBAD0, 0x2100, 0x600D],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_jr_ne_not_taken
        #   0200: ee00                jr ne,.Ltarget
        #         .Ltarget:
        #   0202: 2100 600d           ld r0,#0x600d
        _tc(
            name='sys_jr_ne_not_taken',
            mnemonic='JR',
            desc='JR NE: not taken',
            tags=['branch', 'word', 'RA_mode'],
            code=[0xEE00, 0x2100, 0x600D],
            regs={0: 0x0000},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_djnz_loop
        #         .Ldjnz_loop_top:
        #   0200: a900                inc	r0,#1
        #   0202: f182                djnz	r1,.Ldjnz_loop_top
        _tc(
            name='sys_djnz_loop',
            mnemonic='DJNZ',
            desc='INC R0,#1; DJNZ R1: loop 3 times, R0 counts iterations',
            tags=['branch', 'djnz', 'word'],
            code=[0xA900, 0xF182],
            regs={0: 0x0000, 1: 0x0003},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_djnz_no_loop
        #         .Ldjnz_noloop_top:
        #   0210: a900                inc	r0,#1
        #   0212: f182                djnz	r1,.Ldjnz_noloop_top
        _tc(
            name='sys_djnz_no_loop',
            mnemonic='DJNZ',
            desc='INC R0,#1; DJNZ R1: counter=1, no loop, R0 counts iterations',
            tags=['branch', 'djnz', 'word'],
            code=[0xA900, 0xF182],
            regs={0: 0x0000, 1: 0x0001},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dbjnz_loop
        #         .Ldbjnz_loop_top:
        #   0220: a900                inc	r0,#1
        #   0222: f102                dbjnz	rh1,.Ldbjnz_loop_top
        _tc(
            name='sys_dbjnz_loop',
            mnemonic='DBJNZ',
            desc='INC R0,#1; DBJNZ RH1: loop 3 times, R0 counts iterations, RL1 preserved',
            tags=['branch', 'djnz', 'byte'],
            code=[0xA900, 0xF102],
            regs={0: 0x0000, 1: 0x0342},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_dbjnz_no_loop
        #         .Ldbjnz_noloop_top:
        #   0230: a900                inc	r0,#1
        #   0232: f102                dbjnz	rh1,.Ldbjnz_noloop_top
        _tc(
            name='sys_dbjnz_no_loop',
            mnemonic='DBJNZ',
            desc='INC R0,#1; DBJNZ RH1: counter=1, no loop, R0 counts iterations, RL1 preserved',
            tags=['branch', 'djnz', 'byte'],
            code=[0xA900, 0xF102],
            regs={0: 0x0000, 1: 0x0142},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_call_ret_basic
        #   0200: 2100 0001           ld r0,#0x1
        #   0204: 5f00 0210           call .Lsub
        #   0208: 2100 0003           ld r0,#0x3
        #   020c: 5e08 00c0           jp t,0x00c0
        #         .Lsub:
        #   0210: 2100 0002           ld r0,#0x2
        #   0214: 9e08                ret t
        _tc(
            name='sys_call_ret_basic',
            mnemonic='CALL',
            desc='CALL 0x0210; RET T: basic call/return',
            tags=['branch', 'call', 'stack'],
            code=[0x2100, 0x0001, 0x5F00, 0x0210, 0x2100, 0x0003, 0x5E08, 0x00C0, 0x2100, 0x0002, 0x9E08],
            regs={0: 0x0000, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_calr_ret_basic
        #   0200: 2100 0001           ld r0,#0x1
        #   0204: dffc                calr .Lsub
        #   0206: 2100 0003           ld r0,#0x3
        #   020a: 5e08 00c0           jp t,0x00c0
        #         .Lsub:
        #   020e: 2100 0002           ld r0,#0x2
        #   0212: 9e08                ret t
        _tc(
            name='sys_calr_ret_basic',
            mnemonic='CALR',
            desc='CALR +5; RET T: relative call/return',
            tags=['branch', 'call', 'stack'],
            code=[0x2100, 0x0001, 0xDFFC, 0x2100, 0x0003, 0x5E08, 0x00C0, 0x2100, 0x0002, 0x9E08],
            regs={0: 0x0000, 15: 0x0F00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ret_cc_taken
        #   0200: 2100 0001           ld r0,#0x1
        #   0204: 5f00 0210           call .Lsub
        #   0208: 2100 0003           ld r0,#0x3
        #   020c: 5e08 00c0           jp t,0x00c0
        #         .Lsub:
        #   0210: 2100 0002           ld r0,#0x2
        #   0214: 9e06                ret eq
        _tc(
            name='sys_ret_cc_taken',
            mnemonic='RET',
            desc='RET Z: conditional return (Z=1, taken)',
            tags=['branch', 'call', 'stack'],
            code=[0x2100, 0x0001, 0x5F00, 0x0210, 0x2100, 0x0003, 0x5E08, 0x00C0, 0x2100, 0x0002, 0x9E06],
            regs={0: 0x0000, 15: 0x0F00},
            fcw=fcw_with_flags(Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldi_single
        #   2d900: bb11 0238           ldi	@r3,@r1,r2
        _tc(
            name='sys_ldi_single',
            mnemonic='LDI',
            desc='LDI @R3, @R1, R2: copy 1 word',
            tags=['block', 'word'],
            code=[0xBB11, 0x0238],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0xAAAA},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldi_last
        #   2da00: bb11 0238           ldi	@r3,@r1,r2
        _tc(
            name='sys_ldi_last',
            mnemonic='LDI',
            desc='LDI @R3, @R1, R2: counter=1',
            tags=['block', 'word'],
            code=[0xBB11, 0x0238],
            regs={1: 0x0600, 2: 0x0001, 3: 0x0700},
            memory={0x0600: 0xBBBB},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldir_3words
        #   2db00: bb11 0230           ldir	@r3,@r1,r2
        _tc(
            name='sys_ldir_3words',
            mnemonic='LDIR',
            desc='LDIR @R3, @R1, R2: copy 3 words',
            tags=['block', 'word'],
            code=[0xBB11, 0x0230],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldir_1word
        #   2dc00: bb11 0230           ldir	@r3,@r1,r2
        _tc(
            name='sys_ldir_1word',
            mnemonic='LDIR',
            desc='LDIR @R3, @R1, R2: copy 1 word',
            tags=['block', 'word'],
            code=[0xBB11, 0x0230],
            regs={1: 0x0600, 2: 0x0001, 3: 0x0700},
            memory={0x0600: 0xDDDD},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldd_single
        #   2dd00: bb19 0238           ldd	@r3,@r1,r2
        _tc(
            name='sys_ldd_single',
            mnemonic='LDD',
            desc='LDD @R3, @R1, R2: copy 1 word (decrement)',
            tags=['block', 'word'],
            code=[0xBB19, 0x0238],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0xCCCC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldd_last
        #   2de00: bb19 0238           ldd	@r3,@r1,r2
        _tc(
            name='sys_ldd_last',
            mnemonic='LDD',
            desc='LDD @R3, @R1, R2: counter=1',
            tags=['block', 'word'],
            code=[0xBB19, 0x0238],
            regs={1: 0x0604, 2: 0x0001, 3: 0x0704},
            memory={0x0604: 0xEEEE},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lddr_3words
        #   2df00: bb19 0230           lddr	@r3,@r1,r2
        _tc(
            name='sys_lddr_3words',
            mnemonic='LDDR',
            desc='LDDR @R3, @R1, R2: copy 3 words (decrement)',
            tags=['block', 'word'],
            code=[0xBB19, 0x0230],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lddr_1word
        #   2e000: bb19 0230           lddr	@r3,@r1,r2
        _tc(
            name='sys_lddr_1word',
            mnemonic='LDDR',
            desc='LDDR @R3, @R1, R2: copy 1 word (decrement)',
            tags=['block', 'word'],
            code=[0xBB19, 0x0230],
            regs={1: 0x0600, 2: 0x0001, 3: 0x0700},
            memory={0x0600: 0xFFFF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldib_single
        #   2e100: ba11 0238           ldib	@r3,@r1,r2
        _tc(
            name='sys_ldib_single',
            mnemonic='LDIB',
            desc='LDIB @R3, @R1, R2: copy 1 byte',
            tags=['block', 'byte'],
            code=[0xBA11, 0x0238],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0xAA00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldirb_3bytes
        #   2e200: ba11 0230           ldirb	@r3,@r1,r2
        _tc(
            name='sys_ldirb_3bytes',
            mnemonic='LDIRB',
            desc='LDIRB @R3, @R1, R2: copy 3 bytes',
            tags=['block', 'byte'],
            code=[0xBA11, 0x0230],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1122, 0x0602: 0x3300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lddb_single
        #   2e300: ba19 0238           lddb	@r3,@r1,r2
        _tc(
            name='sys_lddb_single',
            mnemonic='LDDB',
            desc='LDDB @R3, @R1, R2: copy 1 byte (decrement)',
            tags=['block', 'byte'],
            code=[0xBA19, 0x0238],
            regs={1: 0x0602, 2: 0x0003, 3: 0x0702},
            memory={0x0602: 0xBB00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lddrb_3bytes
        #   2e400: ba19 0230           lddrb	@r3,@r1,r2
        _tc(
            name='sys_lddrb_3bytes',
            mnemonic='LDDRB',
            desc='LDDRB @R3, @R1, R2: copy 3 bytes (decrement)',
            tags=['block', 'byte'],
            code=[0xBA19, 0x0230],
            regs={1: 0x0602, 2: 0x0003, 3: 0x0702},
            memory={0x0600: 0x1122, 0x0602: 0x3300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpi_match
        #   2e500: bb10 0206           cpi	r0,@r1,r2,eq
        _tc(
            name='sys_cpi_match',
            mnemonic='CPI',
            desc='CPI R0, @R1, R2, EQ: match found',
            tags=['block', 'compare', 'word'],
            code=[0xBB10, 0x0206],
            regs={0: 0x1234, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpi_no_match
        #   2e600: bb10 0206           cpi	r0,@r1,r2,eq
        _tc(
            name='sys_cpi_no_match',
            mnemonic='CPI',
            desc='CPI R0, @R1, R2, EQ: no match',
            tags=['block', 'compare', 'word'],
            code=[0xBB10, 0x0206],
            regs={0: 0x1234, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpir_match_mid
        #   2e700: bb14 0206           cpir	r0,@r1,r2,eq
        _tc(
            name='sys_cpir_match_mid',
            mnemonic='CPIR',
            desc='CPIR R0, @R1, R2, EQ: match at element 2',
            tags=['block', 'compare', 'word'],
            code=[0xBB14, 0x0206],
            regs={0: 0xAAAA, 1: 0x0600, 2: 0x0004},
            memory={0x0600: 0x1111, 0x0602: 0xAAAA},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpir_no_match
        #   2e800: bb14 0206           cpir	r0,@r1,r2,eq
        _tc(
            name='sys_cpir_no_match',
            mnemonic='CPIR',
            desc='CPIR R0, @R1, R2, EQ: exhausted',
            tags=['block', 'compare', 'word'],
            code=[0xBB14, 0x0206],
            regs={0: 0xFFFF, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpd_match
        #   2e900: bb18 0206           cpd	r0,@r1,r2,eq
        _tc(
            name='sys_cpd_match',
            mnemonic='CPD',
            desc='CPD R0, @R1, R2, EQ: match (decrement)',
            tags=['block', 'compare', 'word'],
            code=[0xBB18, 0x0206],
            regs={0: 0x1234, 1: 0x0604, 2: 0x0003},
            memory={0x0604: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpd_no_match
        #   2ea00: bb18 0206           cpd	r0,@r1,r2,eq
        _tc(
            name='sys_cpd_no_match',
            mnemonic='CPD',
            desc='CPD R0, @R1, R2, EQ: no match (decrement)',
            tags=['block', 'compare', 'word'],
            code=[0xBB18, 0x0206],
            regs={0: 0x1234, 1: 0x0604, 2: 0x0003},
            memory={0x0604: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpdr_match
        #   2eb00: bb1c 0206           cpdr	r0,@r1,r2,eq
        _tc(
            name='sys_cpdr_match',
            mnemonic='CPDR',
            desc='CPDR R0, @R1, R2, EQ: match (repeat decrement)',
            tags=['block', 'compare', 'word'],
            code=[0xBB1C, 0x0206],
            regs={0: 0x1111, 1: 0x0604, 2: 0x0003},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpdr_no_match
        #   2ec00: bb1c 0206           cpdr	r0,@r1,r2,eq
        _tc(
            name='sys_cpdr_no_match',
            mnemonic='CPDR',
            desc='CPDR R0, @R1, R2, EQ: exhausted (repeat decrement)',
            tags=['block', 'compare', 'word'],
            code=[0xBB1C, 0x0206],
            regs={0: 0xFFFF, 1: 0x0604, 2: 0x0003},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpib_match
        #   2ed00: ba10 0206           cpib	rh0,@r1,r2,eq
        _tc(
            name='sys_cpib_match',
            mnemonic='CPIB',
            desc='CPIB RH0, @R1, R2, EQ: byte match',
            tags=['block', 'compare', 'byte'],
            code=[0xBA10, 0x0206],
            regs={0: 0x1200, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpib_no_match
        #   2ee00: ba10 0206           cpib	rh0,@r1,r2,eq
        _tc(
            name='sys_cpib_no_match',
            mnemonic='CPIB',
            desc='CPIB RH0, @R1, R2, EQ: byte no match',
            tags=['block', 'compare', 'byte'],
            code=[0xBA10, 0x0206],
            regs={0: 0x1200, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x5600},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpirb_match
        #   2ef00: ba14 0206           cpirb	rh0,@r1,r2,eq
        _tc(
            name='sys_cpirb_match',
            mnemonic='CPIRB',
            desc='CPIRB RH0, @R1, R2, EQ: byte repeat match',
            tags=['block', 'compare', 'byte'],
            code=[0xBA14, 0x0206],
            regs={0: 0xAA00, 1: 0x0600, 2: 0x0004},
            memory={0x0600: 0x1100, 0x0601: 0xAA00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpirb_no_match
        #   2f000: ba14 0206           cpirb	rh0,@r1,r2,eq
        _tc(
            name='sys_cpirb_no_match',
            mnemonic='CPIRB',
            desc='CPIRB RH0, @R1, R2, EQ: byte exhausted',
            tags=['block', 'compare', 'byte'],
            code=[0xBA14, 0x0206],
            regs={0: 0xFF00, 1: 0x0600, 2: 0x0003},
            memory={0x0600: 0x1122, 0x0602: 0x3300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpdb_match
        #   2f100: ba18 0206           cpdb	rh0,@r1,r2,eq
        _tc(
            name='sys_cpdb_match',
            mnemonic='CPDB',
            desc='CPDB RH0, @R1, R2, EQ: byte match (decrement)',
            tags=['block', 'compare', 'byte'],
            code=[0xBA18, 0x0206],
            regs={0: 0x1200, 1: 0x0602, 2: 0x0003},
            memory={0x0602: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpdrb_no_match
        #   2f200: ba1c 0206           cpdrb	rh0,@r1,r2,eq
        _tc(
            name='sys_cpdrb_no_match',
            mnemonic='CPDRB',
            desc='CPDRB RH0, @R1, R2, EQ: byte exhausted (repeat decrement)',
            tags=['block', 'compare', 'byte'],
            code=[0xBA1C, 0x0206],
            regs={0: 0xFF00, 1: 0x0602, 2: 0x0003},
            memory={0x0600: 0x1122, 0x0602: 0x3300},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsi_match
        #   2f300: bb12 0236           cpsi	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsi_match',
            mnemonic='CPSI',
            desc='CPSI @R3, @R1, R2, EQ: string match',
            tags=['block', 'string', 'word'],
            code=[0xBB12, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1234, 0x0700: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsi_no_match
        #   2f400: bb12 0236           cpsi	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsi_no_match',
            mnemonic='CPSI',
            desc='CPSI @R3, @R1, R2, EQ: string no match',
            tags=['block', 'string', 'word'],
            code=[0xBB12, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1234, 0x0700: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsib_match
        #   2f500: ba12 0236           cpsib	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsib_match',
            mnemonic='CPSIB',
            desc='CPSIB @R3, @R1, R2, EQ: byte string match',
            tags=['block', 'string', 'byte'],
            code=[0xBA12, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1200, 0x0700: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsib_no_match
        #   2f600: ba12 0236           cpsib	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsib_no_match',
            mnemonic='CPSIB',
            desc='CPSIB @R3, @R1, R2, EQ: byte string no match',
            tags=['block', 'string', 'byte'],
            code=[0xBA12, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1200, 0x0700: 0x5600},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsir_match
        #   2f700: bb16 0236           cpsir	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsir_match',
            mnemonic='CPSIR',
            desc='CPSIR @R3, @R1, R2, EQ: string match',
            tags=['block', 'string', 'word'],
            code=[0xBB16, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1234, 0x0700: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsir_no_match
        #   2f800: bb16 0236           cpsir	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsir_no_match',
            mnemonic='CPSIR',
            desc='CPSIR @R3, @R1, R2, EQ: string no match',
            tags=['block', 'string', 'word'],
            code=[0xBB16, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333,
                    0x0700: 0xAAAA, 0x0702: 0xBBBB, 0x0704: 0xCCCC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsirb_match
        #   2f900: ba16 0236           cpsirb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsirb_match',
            mnemonic='CPSIRB',
            desc='CPSIRB @R3, @R1, R2, EQ: byte string match',
            tags=['block', 'string', 'byte'],
            code=[0xBA16, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1200, 0x0700: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsirb_no_match
        #   2fa00: ba16 0236           cpsirb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsirb_no_match',
            mnemonic='CPSIRB',
            desc='CPSIRB @R3, @R1, R2, EQ: byte string no match',
            tags=['block', 'string', 'byte'],
            code=[0xBA16, 0x0236],
            regs={1: 0x0600, 2: 0x0003, 3: 0x0700},
            memory={0x0600: 0x1200, 0x0700: 0x5600},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsd_match
        #   2fb00: bb1a 0236           cpsd	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsd_match',
            mnemonic='CPSD',
            desc='CPSD @R3, @R1, R2, EQ: string match',
            tags=['block', 'string', 'word'],
            code=[0xBB1A, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1234, 0x0704: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsd_no_match
        #   2fc00: bb1a 0236           cpsd	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsd_no_match',
            mnemonic='CPSD',
            desc='CPSD @R3, @R1, R2, EQ: string no match',
            tags=['block', 'string', 'word'],
            code=[0xBB1A, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1234, 0x0704: 0x5678},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdb_match
        #   2fd00: ba1a 0236           cpsdb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdb_match',
            mnemonic='CPSDB',
            desc='CPSDB @R3, @R1, R2, EQ: byte string match',
            tags=['block', 'string', 'byte'],
            code=[0xBA1A, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1200, 0x0704: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdb_no_match
        #   2fe00: ba1a 0236           cpsdb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdb_no_match',
            mnemonic='CPSDB',
            desc='CPSDB @R3, @R1, R2, EQ: byte string no match',
            tags=['block', 'string', 'byte'],
            code=[0xBA1A, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1200, 0x0704: 0x5600},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdr_match
        #   2ff00: bb1e 0236           cpsdr	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdr_match',
            mnemonic='CPSDR',
            desc='CPSDR @R3, @R1, R2, EQ: string match',
            tags=['block', 'string', 'word'],
            code=[0xBB1E, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1234, 0x0704: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdr_no_match
        #   30000: bb1e 0236           cpsdr	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdr_no_match',
            mnemonic='CPSDR',
            desc='CPSDR @R3, @R1, R2, EQ: string no match',
            tags=['block', 'string', 'word'],
            code=[0xBB1E, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0600: 0x1111, 0x0602: 0x2222, 0x0604: 0x3333,
                    0x0700: 0xAAAA, 0x0702: 0xBBBB, 0x0704: 0xCCCC},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdrb_match
        #   30100: ba1e 0236           cpsdrb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdrb_match',
            mnemonic='CPSDRB',
            desc='CPSDRB @R3, @R1, R2, EQ: byte string match',
            tags=['block', 'string', 'byte'],
            code=[0xBA1E, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0604: 0x1200, 0x0704: 0x1200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_cpsdrb_no_match
        #   30200: ba1e 0236           cpsdrb	@r3,@r1,r2,eq
        _tc(
            name='sys_cpsdrb_no_match',
            mnemonic='CPSDRB',
            desc='CPSDRB @R3, @R1, R2, EQ: byte string no match',
            tags=['block', 'string', 'byte'],
            code=[0xBA1E, 0x0236],
            regs={1: 0x0604, 2: 0x0003, 3: 0x0704},
            memory={0x0602: 0x1122, 0x0604: 0x3300,
                    0x0702: 0xAABB, 0x0704: 0xCC00},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trib_basic
        #   30300: b830 0210           trib	@r3,@r1,r2
        _tc(
            name='sys_trib_basic',
            mnemonic='TRIB',
            desc='TRIB @R3, @R1, R2: translate byte',
            tags=['translate', 'byte'],
            code=[0xB830, 0x0210],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0600: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trib_zero
        #   30400: b830 0210           trib	@r3,@r1,r2
        _tc(
            name='sys_trib_zero',
            mnemonic='TRIB',
            desc='TRIB @R3, @R1, R2: translate zero byte',
            tags=['translate', 'byte'],
            code=[0xB830, 0x0210],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0600: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trirb_basic
        #   30500: b834 0210           trirb	@r3,@r1,r2
        _tc(
            name='sys_trirb_basic',
            mnemonic='TRIRB',
            desc='TRIRB @R3, @R1, R2: translate byte',
            tags=['translate', 'byte'],
            code=[0xB834, 0x0210],
            regs={1: 0x0400, 2: 0x0001, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0600: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trirb_zero
        #   30600: b834 0210           trirb	@r3,@r1,r2
        _tc(
            name='sys_trirb_zero',
            mnemonic='TRIRB',
            desc='TRIRB @R3, @R1, R2: translate zero byte',
            tags=['translate', 'byte'],
            code=[0xB834, 0x0210],
            regs={1: 0x0400, 2: 0x0001, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0600: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trdb_basic
        #   30700: b838 0210           trdb	@r3,@r1,r2
        _tc(
            name='sys_trdb_basic',
            mnemonic='TRDB',
            desc='TRDB @R3, @R1, R2: translate byte',
            tags=['translate', 'byte'],
            code=[0xB838, 0x0210],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trdb_zero
        #   30800: b838 0210           trdb	@r3,@r1,r2
        _tc(
            name='sys_trdb_zero',
            mnemonic='TRDB',
            desc='TRDB @R3, @R1, R2: translate zero byte',
            tags=['translate', 'byte'],
            code=[0xB838, 0x0210],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trdrb_basic
        #   30900: b83c 0210           trdrb	@r3,@r1,r2
        _tc(
            name='sys_trdrb_basic',
            mnemonic='TRDRB',
            desc='TRDRB @R3, @R1, R2: translate byte',
            tags=['translate', 'byte'],
            code=[0xB83C, 0x0210],
            regs={1: 0x0400, 2: 0x0001, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trdrb_zero
        #   30a00: b83c 0210           trdrb	@r3,@r1,r2
        _tc(
            name='sys_trdrb_zero',
            mnemonic='TRDRB',
            desc='TRDRB @R3, @R1, R2: translate zero byte',
            tags=['translate', 'byte'],
            code=[0xB83C, 0x0210],
            regs={1: 0x0400, 2: 0x0001, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trtib_basic
        #   30b00: b812 0230           trtib	@r1,@r3,r2
        _tc(
            name='sys_trtib_basic',
            mnemonic='TRTIB',
            desc='TRTIB @R3, @R1, R2: translate and test',
            tags=['translate', 'byte'],
            code=[0xB812, 0x0230],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0600: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trtib_zero
        #   30c00: b812 0230           trtib	@r1,@r3,r2
        _tc(
            name='sys_trtib_zero',
            mnemonic='TRTIB',
            desc='TRTIB @R3, @R1, R2: translate and test zero',
            tags=['translate', 'byte'],
            code=[0xB812, 0x0230],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0600},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trtdb_basic
        #   30d00: b81a 0230           trtdb	@r1,@r3,r2
        _tc(
            name='sys_trtdb_basic',
            mnemonic='TRTDB',
            desc='TRTDB @R3, @R1, R2: translate and test',
            tags=['translate', 'byte'],
            code=[0xB81A, 0x0230],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x4100,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_trtdb_zero
        #   30e00: b81a 0230           trtdb	@r1,@r3,r2
        _tc(
            name='sys_trtdb_zero',
            mnemonic='TRTDB',
            desc='TRTDB @R3, @R1, R2: translate and test zero',
            tags=['translate', 'byte'],
            code=[0xB81A, 0x0230],
            regs={1: 0x0400, 2: 0x0003, 3: 0x0602},
            memory={
                0x0400: 0x0102,
                0x0402: 0x0304,
                0x0404: 0x0506,
                0x0406: 0x0708,
                0x0408: 0x090A,
                0x040A: 0x0B0C,
                0x040C: 0x0D0E,
                0x040E: 0x0F10,
                0x0410: 0x1112,
                0x0412: 0x1314,
                0x0414: 0x1516,
                0x0416: 0x1718,
                0x0418: 0x191A,
                0x041A: 0x1B1C,
                0x041C: 0x1D1E,
                0x041E: 0x1F20,
                0x0420: 0x2122,
                0x0422: 0x2324,
                0x0424: 0x2526,
                0x0426: 0x2728,
                0x0428: 0x292A,
                0x042A: 0x2B2C,
                0x042C: 0x2D2E,
                0x042E: 0x2F30,
                0x0430: 0x3132,
                0x0432: 0x3334,
                0x0434: 0x3536,
                0x0436: 0x3738,
                0x0438: 0x393A,
                0x043A: 0x3B3C,
                0x043C: 0x3D3E,
                0x043E: 0x3F40,
                0x0440: 0x4142,
                0x0442: 0x4344,
                0x0444: 0x4546,
                0x0446: 0x4748,
                0x0448: 0x494A,
                0x044A: 0x4B4C,
                0x044C: 0x4D4E,
                0x044E: 0x4F50,
                0x0450: 0x5152,
                0x0452: 0x5354,
                0x0454: 0x5556,
                0x0456: 0x5758,
                0x0458: 0x595A,
                0x045A: 0x5B5C,
                0x045C: 0x5D5E,
                0x045E: 0x5F60,
                0x0460: 0x6162,
                0x0462: 0x6364,
                0x0464: 0x6566,
                0x0466: 0x6768,
                0x0468: 0x696A,
                0x046A: 0x6B6C,
                0x046C: 0x6D6E,
                0x046E: 0x6F70,
                0x0470: 0x7172,
                0x0472: 0x7374,
                0x0474: 0x7576,
                0x0476: 0x7778,
                0x0478: 0x797A,
                0x047A: 0x7B7C,
                0x047C: 0x7D7E,
                0x047E: 0x7F80,
                0x0480: 0x8182,
                0x0482: 0x8384,
                0x0484: 0x8586,
                0x0486: 0x8788,
                0x0488: 0x898A,
                0x048A: 0x8B8C,
                0x048C: 0x8D8E,
                0x048E: 0x8F90,
                0x0490: 0x9192,
                0x0492: 0x9394,
                0x0494: 0x9596,
                0x0496: 0x9798,
                0x0498: 0x999A,
                0x049A: 0x9B9C,
                0x049C: 0x9D9E,
                0x049E: 0x9FA0,
                0x04A0: 0xA1A2,
                0x04A2: 0xA3A4,
                0x04A4: 0xA5A6,
                0x04A6: 0xA7A8,
                0x04A8: 0xA9AA,
                0x04AA: 0xABAC,
                0x04AC: 0xADAE,
                0x04AE: 0xAFB0,
                0x04B0: 0xB1B2,
                0x04B2: 0xB3B4,
                0x04B4: 0xB5B6,
                0x04B6: 0xB7B8,
                0x04B8: 0xB9BA,
                0x04BA: 0xBBBC,
                0x04BC: 0xBDBE,
                0x04BE: 0xBFC0,
                0x04C0: 0xC1C2,
                0x04C2: 0xC3C4,
                0x04C4: 0xC5C6,
                0x04C6: 0xC7C8,
                0x04C8: 0xC9CA,
                0x04CA: 0xCBCC,
                0x04CC: 0xCDCE,
                0x04CE: 0xCFD0,
                0x04D0: 0xD1D2,
                0x04D2: 0xD3D4,
                0x04D4: 0xD5D6,
                0x04D6: 0xD7D8,
                0x04D8: 0xD9DA,
                0x04DA: 0xDBDC,
                0x04DC: 0xDDDE,
                0x04DE: 0xDFE0,
                0x04E0: 0xE1E2,
                0x04E2: 0xE3E4,
                0x04E4: 0xE5E6,
                0x04E6: 0xE7E8,
                0x04E8: 0xE9EA,
                0x04EA: 0xEBEC,
                0x04EC: 0xEDEE,
                0x04EE: 0xEFF0,
                0x04F0: 0xF1F2,
                0x04F2: 0xF3F4,
                0x04F4: 0xF5F6,
                0x04F6: 0xF7F8,
                0x04F8: 0xF9FA,
                0x04FA: 0xFBFC,
                0x04FC: 0xFDFE,
                0x04FE: 0xFF00,
                0x0602: 0x0000,
            },
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lda_r_da_operand
        #   30f00: 7600 0400           lda	r0,0x400
        _tc(
            name='sys_lda_r_da_operand',
            mnemonic='LDA',
            desc='LDA R0, 0x0400',
            tags=['load', 'address', 'DA_mode'],
            code=[0x7600, 0x0400],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_lda_r_da_src
        #   31000: 7600 0600           lda	r0,0x600
        _tc(
            name='sys_lda_r_da_src',
            mnemonic='LDA',
            desc='LDA R0, 0x0600',
            tags=['load', 'address', 'DA_mode'],
            code=[0x7600, 0x0600],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldar_r_fwd
        #   0200: 3400 0204           ldar r0,0x0404
        _tc(
            name='sys_ldar_r_fwd',
            mnemonic='LDAR',
            desc='LDAR R0, disp=0x0200',
            tags=['load', 'address', 'RA_mode'],
            code=[0x3400, 0x0204],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldar_r_near
        #   0200: 3400 0014           ldar r0,0x0214
        _tc(
            name='sys_ldar_r_near',
            mnemonic='LDAR',
            desc='LDAR R0, disp=0x0010',
            tags=['load', 'address', 'RA_mode'],
            code=[0x3400, 0x0014],
            regs={0: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldr_r_normal
        #   0200: 3100 0204           ldr r0,0x0404
        _tc(
            name='sys_ldr_r_normal',
            mnemonic='LDR',
            desc='LDR R0, disp=0x0200: [target]=0x1234',
            tags=['load', 'word', 'RA_mode'],
            code=[0x3100, 0x0204],
            regs={0: 0x0000},
            memory={0x0408: 0x1234},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldr_r_zero
        #   0200: 3100 0204           ldr r0,0x0404
        _tc(
            name='sys_ldr_r_zero',
            mnemonic='LDR',
            desc='LDR R0, disp=0x0200: [target]=0x0000',
            tags=['load', 'word', 'RA_mode'],
            code=[0x3100, 0x0204],
            regs={0: 0x0000},
            memory={0x0408: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldrb_r_normal
        #   0200: 3000 0204           ldrb rh0,0x0404
        _tc(
            name='sys_ldrb_r_normal',
            mnemonic='LDRB',
            desc='LDRB RH0, disp=0x0200: [target]=0x42xx',
            tags=['load', 'byte', 'RA_mode'],
            code=[0x3000, 0x0204],
            regs={0: 0x0000},
            memory={0x0408: 0x4200},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldrb_r_zero
        #   0200: 3000 0204           ldrb rh0,0x0404
        _tc(
            name='sys_ldrb_r_zero',
            mnemonic='LDRB',
            desc='LDRB RH0, disp=0x0200: [target]=0x00xx',
            tags=['load', 'byte', 'RA_mode'],
            code=[0x3000, 0x0204],
            regs={0: 0x0000},
            memory={0x0408: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldrl_rr_normal
        #   0200: 3500 0204           ldrl rr0,0x0404
        _tc(
            name='sys_ldrl_rr_normal',
            mnemonic='LDRL',
            desc='LDRL RR0, disp=0x0200: 0xDEADBEEF',
            tags=['load', 'long', 'RA_mode'],
            code=[0x3500, 0x0204],
            regs={0: 0x0000, 1: 0x0000},
            memory={0x0408: 0xDEAD, 0x040A: 0xBEEF},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldrl_rr_zero
        #   0200: 3500 0204           ldrl rr0,0x0404
        _tc(
            name='sys_ldrl_rr_zero',
            mnemonic='LDRL',
            desc='LDRL RR0, disp=0x0200: 0x00000000',
            tags=['load', 'long', 'RA_mode'],
            code=[0x3500, 0x0204],
            regs={0: 0x0000, 1: 0x0000},
            memory={0x0408: 0x0000, 0x040A: 0x0000},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldctl_read_fcw
        #   31900: 7d02                ldctl	r0,fcw
        _tc(
            name='sys_ldctl_read_fcw',
            mnemonic='LDCTL',
            desc='LDCTL R0, FCW: read FCW into R0',
            tags=['control', 'ldctl'],
            code=[0x7D02],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1, Z=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldctl_write_fcw
        #   31a00: 7d0a                ldctl	fcw,r0
        _tc(
            name='sys_ldctl_write_fcw',
            mnemonic='LDCTL',
            desc='LDCTL FCW, R0: write R0 into FCW',
            tags=['control', 'ldctl'],
            code=[0x7D0A],
            regs={0: 0x40F0},
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldctlb_read_flags
        #   31b00: 8c01                ldctlb	rh0,flags
        _tc(
            name='sys_ldctlb_read_flags',
            mnemonic='LDCTLB',
            desc='LDCTLB RH0, FLAGS: read flags byte',
            tags=['control', 'ldctl', 'byte'],
            code=[0x8C01],
            regs={0: 0x0000},
            fcw=fcw_with_flags(C=1, S=1),
        ),

        # ASSEMBLER-VERIFIED LISTING — DO NOT MODIFY:sys_ldctlb_write_flags
        #   31c00: 8c09                ldctlb	flags,rh0
        _tc(
            name='sys_ldctlb_write_flags',
            mnemonic='LDCTLB',
            desc='LDCTLB FLAGS, RH0: write flags byte',
            tags=['control', 'ldctl', 'byte'],
            code=[0x8C09],
            regs={0: 0xF000},
        ),
    ]
