"""Discriminating tests for the MAME z8000 change sets.

Each test here is chosen so that two candidate behaviours produce DIFFERENT
observable state (registers, memory, I/O or flags). Capturing them on the real
Z8001 settles which behaviour is correct.

Two upstream change sets are covered:
  * branch `z8000_fixes` - the PRE-FIX vs POST-FIX MAME core
  * the s8000 PR (9e781163995, now merged to MAME master) - MAME master vs
    z8000_emu, which forked before it

plus a third class: places where MAME and z8000_emu AGREE but the Z8000 CPU
Technical Manual (~/Projects/Z8000_FPGA/z8000_doc/z8000.md) says otherwise, or
where the manual declares a flag undefined and only a capture can say what the
part does. Those carry a `mame_*` tag naming the behaviour rather than a
commit.

Source: ~/Projects/mame_latest/mame (src/devices/cpu/z8000/). The commit hash
or manual citation each test targets is recorded in its comment block.

Only fixes NOT already discriminated by the existing golden set are covered
here. Fixes already pinned by golden/z8001 and golden/z8001-seg are listed at
the bottom of this file.

Tests are captured/compared through the same path as the other generators:
    python -m tests.compare --capture --port /dev/ttyUSB0 --target z8001 \
        --golden-dir golden/z8001 --name 'mame_*'
    python -m tests.compare --capture --port /dev/ttyUSB0 --target z8001-seg \
        --golden-dir golden/z8001-seg --name 'seg_mame_*'

Usage:
    from tests.gen_mame_fixes import generate_mame_fix_tests
    tests = generate_mame_fix_tests()
"""

from .defs import TestCase
from .flags import FCW_SYS, fcw_with_flags
from .helpers import DST_BUF, OPERAND_BASE, SRC_BUF, STACK_BASE

FCW_SEG = 0xC000  # System + segmented

# Harness I/O port register indices (see tests/test_io.py for the full map).
# Port 0x0104 -> standard index 2, special index 8.
IO_STD_BYTE = 2
IO_SPC_BYTE = 8
PORT_BYTE = 0x0104

# Scratch addresses inside the operand window (0x0400-0x05FF).
COMB_DST = OPERAND_BASE          # 0x0400 - byte COMB @R2 must complement
COMB_DECOY = OPERAND_BASE + 0x10  # 0x0410 - byte the pre-fix decode hit instead
TR_PTR = 0x04FF                  # translate pointer, low byte 0xFF (carry case)
TR_PTR_WORD = TR_PTR & 0xFFFE    # 0x04FE
TR_PTR_BORROW = 0x0400           # translate pointer, low byte 0x00 (borrow case)
TR_TABLE = 0x0500                # translate table base


def _tc(name, mnemonic, desc, tags, code, regs=None, fcw=FCW_SYS,
        memory=None, io_preloads=None, observe_memory=None, observe_io=None,
        target="common"):
    return TestCase(
        name=name,
        mnemonic=mnemonic,
        description=desc,
        tags=["mame_fix"] + tags,
        target=target,
        code=code,
        regs=regs or {},
        fcw=fcw,
        memory=memory or {},
        io_preloads=io_preloads or {},
        observe_memory=observe_memory or [],
        observe_io=observe_io or [],
    )


def generate_mame_fix_tests():
    """Tests that fail on pre-fix MAME and pass (or differ) post-fix."""
    tests = []

    # =====================================================================
    # 390cf6af95e - "fix DAB decimal-adjust correction table"
    #
    # makedab.cpp wrote its digit tests as `i & 0x0f < 0x0a`, which C parses
    # as `i & (0x0f < 0x0a)` == `i & 1`. 570 of 2048 table entries changed.
    #
    # The existing goldens already cover two of the three divergent classes:
    #   add C=0 H=1 -> sys_dab_add_low_adj  (golden R0=0x2000, C=0;
    #                                        pre-fix MAME gives 0x80, C=1)
    #   add C=1 H=0 -> sys_dab_add_high_adj (golden C=1 value 0x01;
    #                                        pre-fix MAME gives 0x07)
    # The third class - SUB with a half-borrow (DA=1, H=1, C=0) - has NO
    # existing test. All 256 entries differ: the pre-fix table asserts a carry
    # out unconditionally (`dab[DF+i] = CF | ((i + 0xfa) & 0xff)`), the fixed
    # table propagates the carry in (C=0 stays C=0). The result BYTE is
    # identical in both, so C is the whole discriminator.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b000            dab     rh0
    tests.append(_tc(
        name='mame_dab_sub_half_borrow',
        mnemonic='DAB',
        desc='DAB RH0=0x1E with DA=1 H=1 C=0 (45-27 style half-borrow)',
        tags=['dab', 'byte', 'flags', 'mame_390cf6af'],
        code=[0xB000],
        regs={0: 0x1E00},
        fcw=fcw_with_flags(DA=1, H=1),
        # post-fix: RH0=0x18 C=0    pre-fix: RH0=0x18 C=1
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b000            dab     rh0
    tests.append(_tc(
        name='mame_dab_sub_half_borrow_wrap',
        mnemonic='DAB',
        desc='DAB RH0=0x05 with DA=1 H=1 C=0 (correction wraps to 0xFF)',
        tags=['dab', 'byte', 'flags', 'mame_390cf6af'],
        code=[0xB000],
        regs={0: 0x0500},
        fcw=fcw_with_flags(DA=1, H=1),
        # post-fix: RH0=0xFF S=1 C=0    pre-fix: RH0=0xFF S=1 C=1
    ))

    # =====================================================================
    # 348860d44ad - "fix COMB @Rd destination register decode"
    #
    # Z0C_ddN0_0000 used GET_DST(OP0,NIB3) - always 0 - so COMB @Rd
    # complemented the byte addressed by R0 instead of Rd.
    #
    # R2 (the encoded pointer) and R0 (the pointer the bug used) address two
    # different bytes with different complements, so BOTH memory and the Z/S
    # flags discriminate:
    #   post-fix: mem[0x0400] 0x33->0xCC (S=1 Z=0), mem[0x0410] untouched
    #   pre-fix : mem[0x0410] 0xFF->0x00 (S=0 Z=1), mem[0x0400] untouched
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 0c20            comb    @r2
    tests.append(_tc(
        name='mame_comb_ir_dst_decode',
        mnemonic='COMB',
        desc='COMB @R2 with R0 aimed at a decoy byte (dst nibble decode)',
        tags=['logical', 'byte', 'IR_mode', 'mame_348860d4'],
        code=[0x0C20],
        regs={0: COMB_DECOY, 2: COMB_DST},
        memory={COMB_DST: 0x3311, COMB_DECOY: 0xFF22},
        observe_memory=[COMB_DST, COMB_DECOY],
    ))

    # =====================================================================
    # 9f576c1780a - "preserve the indexed LDA operand across an overlapping
    #                destination"
    #
    # Z74 (LDA Rd,Rs(Rx)) wrote the destination before reading the index, so
    # when Rx == Rd the address used the value just overwritten.
    #   post-fix: R1 = R2 + R1_orig = 0x0400 + 0x0012 = 0x0412
    #   pre-fix : R1 = R2 + R2      = 0x0400 + 0x0400 = 0x0800
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 7421 0100       lda     r1,r2(r1)
    tests.append(_tc(
        name='mame_lda_bx_index_overlap',
        mnemonic='LDA',
        desc='LDA R1, R2(R1): index register is also the destination',
        tags=['load', 'address', 'BX_mode', 'mame_9f576c17'],
        code=[0x7421, 0x0100],
        regs={1: 0x0012, 2: OPERAND_BASE},
    ))

    # =====================================================================
    # f275462713e - "write POPL @Rd,@Rs result to memory"
    #
    # Z15 stored the popped long with RL(dst)=..., clobbering the destination
    # POINTER pair instead of writing through it.
    #   post-fix: mem[0x0700]=0xDEAD mem[0x0702]=0xBEEF, R2=0x0700 R3=0x1234
    #   pre-fix : memory untouched,                      R2=0xDEAD R3=0xBEEF
    # R15 ends at 0x0F00 either way.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 15f2            popl    @r2,@r15
    tests.append(_tc(
        name='mame_popl_ir_dst',
        mnemonic='POPL',
        desc='POPL @R2, @R15: indirect destination must be written to memory',
        tags=['stack', 'long', 'IR_mode', 'mame_f2754627'],
        code=[0x15F2],
        regs={2: DST_BUF, 3: 0x1234, 15: STACK_BASE - 4},
        memory={
            STACK_BASE - 4: 0xDEAD,
            STACK_BASE - 2: 0xBEEF,
            DST_BUF: 0x0000,
            DST_BUF + 2: 0x0000,
        },
        observe_memory=[DST_BUF, DST_BUF + 2],
    ))

    # =====================================================================
    # 1dfab273df8 - "defer RH1 writeback in translate-block instructions"
    #
    # TRIB/TRTIB wrote RH1 BEFORE updating the destination address register.
    # When the destination pointer is R1 itself, the early write corrupts the
    # pointer that the increment then operates on.
    #
    # The pointer low byte is 0xFF so the increment carries into the high
    # byte - that is what makes the two orderings observable:
    #   post-fix: R1 = 0x04FF+1 = 0x0500, then RH1=0x42 -> R1 = 0x4200
    #   pre-fix : RH1=0x42 -> R1 = 0x42FF, then +1      -> R1 = 0x4300
    #
    # Table: byte at TR_PTR is 0x03; TR_TABLE+3 (0x0503) holds 0x42.
    # NOTE: R1 as the pointer of a TRIB is architecturally "RH1 is destroyed"
    # territory - the capture defines what the silicon actually does.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b810 0320       trib    @r1,@r2,r3
    tests.append(_tc(
        name='mame_trib_dst_rh1_overlap',
        mnemonic='TRIB',
        desc='TRIB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'mame_1dfab273'],
        code=[0xB810, 0x0320],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b812 0320       trtib   @r1,@r2,r3
    tests.append(_tc(
        name='mame_trtib_dst_rh1_overlap',
        mnemonic='TRTIB',
        desc='TRTIB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'mame_1dfab273'],
        code=[0xB812, 0x0320],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ---------------------------------------------------------------------
    # Ordering coverage for the rest of the translate family.
    #
    # The RH1 writeback order is only observable when the DESTINATION
    # pointer is R1 - that is the register RH1 lives in.  Every other
    # translate test in the suite puts the destination in R3 and the table
    # in R1, where R1 is never updated and the two orderings agree.  Only
    # TRIB, TRTIB and TRTDB are pinned by a capture today; the five
    # instructions below are unconstrained, and TRIRB and TRTDRB are
    # currently emulated by extrapolation from their non-repeating siblings.
    #
    # Two operand shapes, because they expose different halves of the bug:
    #
    #   carry case  (pointer 0x04FF): the +1 crosses the byte boundary, so
    #       the ordering shows up in the high byte of R1.
    #         RH1 first: RH1=0x42 -> 0x42FF, then +1 -> R1 = 0x4300
    #         RH1 last : +1 -> 0x0500, then RH1=0x42 -> R1 = 0x4200
    #       This shape only pins R1 for the INCREMENTING forms: 0xFF-1 is
    #       0xFE and does not borrow, so a decrementing form lands on
    #       0x42FE under either ordering.  For the decrementing STORING
    #       forms the destination word still separates them; for TRTDRB,
    #       which neither borrows here nor stores, the carry case is
    #       included for completeness but discriminates nothing.
    #
    #   borrow case (pointer 0x0400): the decrement borrows INTO the byte
    #       RH1 is about to receive.  This is the shape that exposed TRTDB
    #       and the only one that pins the decrementing forms.
    #         RH1 first: RH1=0x42 -> 0x4200, then -1 -> R1 = 0x41FF
    #         RH1 last : -1 -> 0x03FF, then RH1=0x42 -> R1 = 0x42FF
    #
    # For the storing forms the destination word is a second, independent
    # signal: if RH1 is written before the store, the byte lands at the
    # corrupted address and the observed word keeps its preloaded value.
    # (The corrupted target itself - 0x42FF / 0x4200 - is deliberately not
    # observed; it is outside the operand window the harness preloads.)
    #
    # Counts are chosen so exactly one iteration runs: 1 for the
    # unconditional repeats (TRIRB/TRDRB), 2 for the translate-and-test
    # repeats (TRTIRB/TRTDRB), which stop early because the translated byte
    # 0x42 is non-zero.
    #
    # Both shapes are non-segmented only.  In segmented mode the pointer is
    # a register PAIR and the encoding forbids RR0 (the `ddN0`/`ssN0`
    # fields), so R1 can never be part of a destination pointer and this
    # overlap is architecturally unreachable.
    # ---------------------------------------------------------------------

    # --- carry case: pointer low byte 0xFF -------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b814 0320       trirb   @r1,@r2,r3
    tests.append(_tc(
        name='mame_trirb_dst_rh1_overlap',
        mnemonic='TRIRB',
        desc='TRIRB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB814, 0x0320],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0001},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b818 0320       trdb    @r1,@r2,r3
    tests.append(_tc(
        name='mame_trdb_dst_rh1_overlap',
        mnemonic='TRDB',
        desc='TRDB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB818, 0x0320],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b81c 0320       trdrb   @r1,@r2,r3
    tests.append(_tc(
        name='mame_trdrb_dst_rh1_overlap',
        mnemonic='TRDRB',
        desc='TRDRB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB81C, 0x0320],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0001},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b816 032e       trtirb  @r1,@r2,r3
    tests.append(_tc(
        name='mame_trtirb_dst_rh1_overlap',
        mnemonic='TRTIRB',
        desc='TRTIRB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB816, 0x032E],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b81e 032e       trtdrb  @r1,@r2,r3
    tests.append(_tc(
        name='mame_trtdrb_dst_rh1_overlap',
        mnemonic='TRTDRB',
        desc='TRTDRB @R1, @R2, R3: pointer register overlaps the RH1 writeback',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB81E, 0x032E],
        regs={1: TR_PTR, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_WORD: 0x0003, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_WORD],
    ))

    # --- borrow case: pointer low byte 0x00, decrementing forms ----------
    #
    # Byte at 0x0400 is 0x03; TR_TABLE+3 (0x0503) holds 0x42, same table as
    # above.

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b818 0320       trdb    @r1,@r2,r3
    tests.append(_tc(
        name='mame_trdb_dst_rh1_overlap_borrow',
        mnemonic='TRDB',
        desc='TRDB @R1, @R2, R3: RH1 overlap where the decrement borrows',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB818, 0x0320],
        regs={1: TR_PTR_BORROW, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_BORROW: 0x0300, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_BORROW],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b81c 0320       trdrb   @r1,@r2,r3
    tests.append(_tc(
        name='mame_trdrb_dst_rh1_overlap_borrow',
        mnemonic='TRDRB',
        desc='TRDRB @R1, @R2, R3: RH1 overlap where the decrement borrows',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB81C, 0x0320],
        regs={1: TR_PTR_BORROW, 2: TR_TABLE, 3: 0x0001},
        memory={TR_PTR_BORROW: 0x0300, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_BORROW],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b81a 0320       trtdb   @r1,@r2,r3
    tests.append(_tc(
        name='mame_trtdb_dst_rh1_overlap_borrow',
        mnemonic='TRTDB',
        desc='TRTDB @R1, @R2, R3: RH1 overlap where the decrement borrows',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB81A, 0x0320],
        regs={1: TR_PTR_BORROW, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_BORROW: 0x0300, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_BORROW],
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b81e 032e       trtdrb  @r1,@r2,r3
    tests.append(_tc(
        name='mame_trtdrb_dst_rh1_overlap_borrow',
        mnemonic='TRTDRB',
        desc='TRTDRB @R1, @R2, R3: RH1 overlap where the decrement borrows',
        tags=['translate', 'byte', 'rh1_overlap', 'mame_1dfab273'],
        code=[0xB81E, 0x032E],
        regs={1: TR_PTR_BORROW, 2: TR_TABLE, 3: 0x0002},
        memory={TR_PTR_BORROW: 0x0300, TR_TABLE + 2: 0xAA42},
        observe_memory=[TR_PTR_BORROW],
    ))

    # ---------------------------------------------------------------------
    # Translate family: count of 0 on entry.
    #
    # This is the ONLY additional shape the architecture permits.  z8000.md
    # states the operand restrictions for the family (spelled out in full
    # under TRDB, and the non-overlap half is repeated in all eight
    # descriptions):
    #
    #   "R0 and R1 in nonsegmented mode, or RR0 in segmented mode, must not
    #    be used as a source or destination pointer, and R1 should not be
    #    used as a counter.  The source, destination, and counter registers
    #    must be separate and non-overlapping registers."
    #
    # That rules out the three other aliasing shapes outright - a table
    # pointer in R1, a counter in R1, and dst == src are all prohibited
    # operand combinations, not edge cases.  They were tried against the
    # Z8001 and the part misbehaved badly enough to take the harness with
    # it, which is what undefined means here.
    #
    # Note the same sentence also forbids R1 as the DESTINATION pointer, so
    # the mame_*_dst_rh1_overlap captures above are pinning undefined
    # behaviour too.  They are kept deliberately: they reproduce cleanly and
    # the emulator wants to be bug-compatible with this part.  Nothing in
    # them should be read as architectural.
    #
    # Count 0 is legal: dst/src/cnt are R2/R3/R4, all distinct and clear of
    # R0/R1.  The decrement wraps to 0xFFFF.  TRIRB and TRDRB are excluded
    # because they repeat unconditionally and would then run 65536 times
    # across memory; the translate-and-test repeats are safe because the
    # non-zero translated byte 0x42 ends them after one pass.
    #
    # ASSEMBLER-VERIFIED LISTINGS (z8k-coff-as, .text=0x200):
    #   -z8002  b820 0430  trib @r2,@r3,r4     b826 043e  trtirb @r2,@r3,r4
    #   -z8001  b820 0740  trib @rr2,@rr4,r7   b826 074e  trtirb @rr2,@rr4,r7
    # Opcode nibble is 0/4/8/c for trib/trirb/trdb/trdrb and 2/6/a/e for
    # trtib/trtirb/trtdb/trtdrb; word 1 ends in 0xe for trtirb/trtdrb only.
    # The segmented counter is r7, clear of both RR2 and RR4.
    # ---------------------------------------------------------------------

    #          mnemonic  op   low   repeats-unconditionally  decrements
    tr_ops = [
        ('TRIB',   0x0, 0x0, False, False),
        ('TRIRB',  0x4, 0x0, True,  False),
        ('TRDB',   0x8, 0x0, False, True),
        ('TRDRB',  0xC, 0x0, True,  True),
        ('TRTIB',  0x2, 0x0, False, False),
        ('TRTIRB', 0x6, 0xE, False, False),
        ('TRTDB',  0xA, 0x0, False, True),
        ('TRTDRB', 0xE, 0xE, False, True),
    ]

    def tr_code(op, low, dst, src, cnt):
        return [0xB800 | (dst << 4) | op, (cnt << 8) | (src << 4) | low]

    TR_STR = 0x0600          # the string a translate walks
    TR_TBL_B = 0x0500        # translation table base

    # Byte at TR_STR+1 is 0x03; TR_TBL_B+3 holds 0x42.
    cnt_mem = {TR_STR: 0x0003, TR_TBL_B + 2: 0xAA42}

    for mnem, op, low, uncond, dec in tr_ops:
        lo = mnem.lower()

        if uncond:
            # TRIRB/TRDRB repeat unconditionally: entered with count 0 they
            # would translate 65536 bytes straight through the harness.
            continue

        # --- count of 0 on entry -----------------------------------------
        tests.append(_tc(
            name=f'mame_{lo}_cnt_zero_entry',
            mnemonic=mnem,
            desc=f'{mnem} @R2, @R3, R4 entered with count 0: decrement wraps',
            tags=['translate', 'byte', 'cnt_zero'],
            code=tr_code(op, low, dst=2, src=3, cnt=4),
            regs={2: TR_STR + 1, 3: TR_TBL_B, 4: 0x0000},
            memory=dict(cnt_mem),
            observe_memory=[TR_STR],
        ))

        tests.append(_tc(
            name=f'seg_mame_{lo}_cnt_zero_entry',
            mnemonic=mnem,
            desc=f'{mnem} @RR2, @RR4, R7 entered with count 0: decrement wraps',
            tags=['segmented', 'seg0', 'translate', 'byte', 'cnt_zero'],
            code=tr_code(op, low, dst=2, src=4, cnt=7),
            regs={2: 0x8000, 3: TR_STR + 1, 4: 0x8000, 5: TR_TBL_B, 7: 0x0000},
            fcw=FCW_SEG,
            memory=dict(cnt_mem),
            observe_memory=[TR_STR],
            target='z8001-seg',
        ))

    # =====================================================================
    # d3b65bf7234 - "fix block-I/O instruction flags and address increment"
    #
    # Every SINIB/INIB/OUTIB/SOUTIB-family handler now sets/clears Z alongside
    # V when the counter is decremented; before, Z was left untouched.
    # FlagsUpdate.md Group O flags this as unverified ("the hardware likely
    # sets Z from the counter decrement. No golden test") - these four
    # captures answer it, in both directions.
    #
    # There are NO block-I/O tests in the existing suite at all (test_io.py
    # covers IN/OUT/SIN/SOUT only), so this whole family is unpinned.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 3a10 0328       inib    @r2,@r1,r3
    tests.append(_tc(
        name='mame_inib_z_count_exhausted',
        mnemonic='INIB',
        desc='INIB @R2, @R1, R3 with count=1: Z on counter exhaustion',
        tags=['io', 'block_io', 'byte', 'flags', 'mame_d3b65bf7'],
        code=[0x3A10, 0x0328],
        regs={1: PORT_BYTE, 2: DST_BUF, 3: 0x0001},
        memory={DST_BUF: 0x0000},
        io_preloads={IO_STD_BYTE: 0xA1B2},
        observe_memory=[DST_BUF],
        observe_io=[IO_STD_BYTE],
        # post-fix: V=1 Z=1    pre-fix: V=1 Z=0 (initial Z preserved)
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 3a10 0328       inib    @r2,@r1,r3
    tests.append(_tc(
        name='mame_inib_z_count_remaining',
        mnemonic='INIB',
        desc='INIB @R2, @R1, R3 with count=2 and Z preset: Z must be cleared',
        tags=['io', 'block_io', 'byte', 'flags', 'mame_d3b65bf7'],
        code=[0x3A10, 0x0328],
        regs={1: PORT_BYTE, 2: DST_BUF, 3: 0x0002},
        fcw=fcw_with_flags(Z=1),
        memory={DST_BUF: 0x0000},
        io_preloads={IO_STD_BYTE: 0xA1B2},
        observe_memory=[DST_BUF],
        observe_io=[IO_STD_BYTE],
        # post-fix: V=0 Z=0    pre-fix: V=0 Z=1 (initial Z preserved)
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 3a12 0328       outib   @r2,@r1,r3
    tests.append(_tc(
        name='mame_outib_z_count_exhausted',
        mnemonic='OUTIB',
        desc='OUTIB @R2, @R1, R3 with count=1: Z on counter exhaustion',
        tags=['io', 'block_io', 'byte', 'flags', 'mame_d3b65bf7'],
        code=[0x3A12, 0x0328],
        regs={1: SRC_BUF, 2: PORT_BYTE, 3: 0x0001},
        memory={SRC_BUF: 0x7788},
        io_preloads={IO_STD_BYTE: 0x0000},
        observe_io=[IO_STD_BYTE],
        # post-fix: V=1 Z=1    pre-fix: V=1 Z=0
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 3a11 0328       sinib   @r2,@r1,r3
    tests.append(_tc(
        name='mame_sinib_z_count_exhausted',
        mnemonic='SINIB',
        desc='SINIB @R2, @R1, R3 with count=1: Z on counter exhaustion',
        tags=['io', 'block_io', 'byte', 'flags', 'special_io',
              'mame_d3b65bf7'],
        code=[0x3A11, 0x0328],
        regs={1: PORT_BYTE, 2: DST_BUF, 3: 0x0001},
        memory={DST_BUF: 0x0000},
        io_preloads={IO_SPC_BYTE: 0xC3D4},
        observe_memory=[DST_BUF],
        observe_io=[IO_SPC_BYTE],
        # post-fix: V=1 Z=1    pre-fix: V=1 Z=0
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 3a13 0328       soutib  @r2,@r1,r3
    tests.append(_tc(
        name='mame_soutib_z_count_exhausted',
        mnemonic='SOUTIB',
        desc='SOUTIB @R2, @R1, R3 with count=1: Z on counter exhaustion',
        tags=['io', 'block_io', 'byte', 'flags', 'special_io',
              'mame_d3b65bf7'],
        code=[0x3A13, 0x0328],
        regs={1: SRC_BUF, 2: PORT_BYTE, 3: 0x0001},
        memory={SRC_BUF: 0x99AA},
        io_preloads={IO_SPC_BYTE: 0x0000},
        observe_io=[IO_SPC_BYTE],
        # post-fix: V=1 Z=1    pre-fix: V=1 Z=0
    ))

    # =====================================================================
    # DIV word CASE 4 - sign flag from the FULL quotient
    #
    # z8000.md DIV CASE 4 (:3852): "all but the sign bit of the quotient ...
    # are left in the destination register ... the sign and zero flags are set
    # according to the value of the quotient", and "the sign flag can be
    # replicated by a subsequent instruction into the high-order half of the
    # destination to produce the two's complement representation of the
    # quotient".  So S is the 17th (sign) bit of the quotient, NOT bit 15 of
    # the truncated 16-bit remnant left in the register.
    #
    # sys_divl_rq_rr_case4 already pins the LONG form in the positive
    # direction.  There is no word-form CASE-4 test at all, and neither form
    # is pinned in the negative direction - which is the case that catches an
    # implementation reading S from the truncated value when the truncated
    # value looks POSITIVE.
    #
    # MAME (z8000_fixes/s8000) uses CHK_XXXW_ZS / CHK_XXXL_ZS here, which cast
    # to int16_t / int32_t - i.e. the truncated remnant.  z8000_emu (bc48c14 /
    # bc64674) uses the full quotient.  These four captures settle it.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9b20            div     rr0,r2
    tests.append(_tc(
        name='mame_div_rr_r_case4_pos',
        mnemonic='DIV',
        desc='DIV RR0,R2: 0x00018000/2 (CASE 4, quotient +0xC000, S must be 0)',
        tags=['mult_div', 'word', 'boundary', 'flags', 'mame_216d1fe1'],
        code=[0x9B20],
        regs={0: 0x0001, 1: 0x8000, 2: 0x0002},
        # quotient +49152: outside +/-2^15, inside +/-2^16 -> V=1 C=1.
        # Positive as a 17-bit value, so S=0 even though the remnant left in
        # R1 (0xC000) has bit 15 set.
        # manual/z8000_emu: R1=0xC000 V=1 C=1 S=0    MAME: S=1
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9b20            div     rr0,r2
    tests.append(_tc(
        name='mame_div_rr_r_case4_neg',
        mnemonic='DIV',
        desc='DIV RR0,R2: 0xFFFE8000/2 (CASE 4, quotient -0xC000, S must be 1)',
        tags=['mult_div', 'word', 'boundary', 'flags', 'mame_216d1fe1'],
        code=[0x9B20],
        regs={0: 0xFFFE, 1: 0x8000, 2: 0x0002},
        # quotient -49152: the remnant left in R1 is 0x4000, which looks
        # POSITIVE. S must still be 1 (the true quotient is negative).
        # manual/z8000_emu: R1=0x4000 V=1 C=1 S=1    MAME: S=0
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9a40            divl    rq0,rr4
    tests.append(_tc(
        name='mame_divl_rq_rr_case4_neg',
        mnemonic='DIVL',
        desc='DIVL RQ0,RR4: -0x180000000/2 (CASE 4, quotient -0xC0000000, S must be 1)',
        tags=['mult_div', 'long', 'boundary', 'flags', 'mame_216d1fe1'],
        code=[0x9A40],
        regs={0: 0xFFFF, 1: 0xFFFE, 2: 0x8000, 3: 0x0000, 4: 0x0000, 5: 0x0002},
        # Negative mirror of sys_divl_rq_rr_case4. Remnant in RR2 is
        # 0x40000000 (looks positive); the true quotient is negative.
        # manual/z8000_emu: RR2=0x40000000 V=1 C=1 S=1    MAME: S=0
    ))

    # =====================================================================
    # MULTL carry boundary - NOT fixed on either branch
    #
    # z8000.md MULT flags (:6031): "MULT - set if product is less than -2^15
    # or greater than or equal to 2^15 ...  MULTL - set if product is less
    # than -2^31 or greater than or equal to 2^31".
    #
    # bdf54b2a429 fixed the WORD form (-0x7fff/0x7fff -> -0x8000/0x8000) and
    # sys_mult_rr_r_bound_pos/neg/over pin it.  The LONG form still reads
    #     if (result < -0x7fffffffL || result >= 0x7fffffffL) SET_C;
    # in BOTH MAME and z8000_emu, so products of exactly +2^31-1 and -2^31 -
    # which DO fit in the low half - wrongly assert carry.  There is no MULTL
    # boundary test in the suite; these three add one.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9840            multl   rq0,rr4
    tests.append(_tc(
        name='mame_multl_c_bound_pos',
        mnemonic='MULTL',
        desc='MULTL RQ0,RR4: 0x7FFFFFFF * 1 = +2^31-1 (fits in int32, C must be 0)',
        tags=['mult', 'long', 'boundary', 'flags', 'mame_multl_carry'],
        code=[0x9840],
        regs={0: 0x0000, 1: 0x0000, 2: 0x7FFF, 3: 0xFFFF, 4: 0x0000, 5: 0x0001},
        # manual: RQ0=0x000000007FFFFFFF C=0    MAME+emu: C=1 (off-by-one)
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9840            multl   rq0,rr4
    tests.append(_tc(
        name='mame_multl_c_bound_neg',
        mnemonic='MULTL',
        desc='MULTL RQ0,RR4: -2^31 * 1 (fits in int32, C must be 0)',
        tags=['mult', 'long', 'boundary', 'flags', 'mame_multl_carry'],
        code=[0x9840],
        regs={0: 0x0000, 1: 0x0000, 2: 0x8000, 3: 0x0000, 4: 0x0000, 5: 0x0001},
        # manual: RQ0=0xFFFFFFFF80000000 C=0    MAME+emu: C=1 (off-by-one)
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 9840            multl   rq0,rr4
    tests.append(_tc(
        name='mame_multl_c_bound_over',
        mnemonic='MULTL',
        desc='MULTL RQ0,RR4: 0x40000000 * 2 = +2^31 (does not fit, C must be 1)',
        tags=['mult', 'long', 'boundary', 'flags', 'mame_multl_carry'],
        code=[0x9840],
        regs={0: 0x0000, 1: 0x0000, 2: 0x4000, 3: 0x0000, 4: 0x0000, 5: 0x0002},
        # Control: all three implementations agree C=1 here. Pins the far side
        # of the boundary so a "fix" cannot simply drop the carry test.
    ))

    # =====================================================================
    # TCC / TCCB - bit 0 must NOT be cleared when the condition is false
    #
    # z8000.md TCC (:8258): "If the condition is satisfied, then the least
    # significant bit of the destination is set. If the condition is not
    # satisfied, bit zero of the destination is NOT CLEARED but retains its
    # previous value. All other bits in the destination are unaffected."
    #
    # MAME (master, z8000_fixes and s8000 alike) starts from
    #     uint8_t tmp = RB(dst) & ~1;
    # which clears bit 0 unconditionally.  z8000_emu dropped the mask.
    #
    # Every existing sys_tcc_*_false / sys_tccb_*_false golden starts with the
    # destination at 0x0000, so bit 0 is already 0 and the two behaviours are
    # indistinguishable.  These presets set bit 0 first.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: af0f            tcc     nc/uge,r0
    tests.append(_tc(
        name='mame_tcc_false_bit0_preserved',
        mnemonic='TCC',
        desc='TCC NC,R0 with C=1 (condition false) and R0 bit 0 already set',
        tags=['control', 'tcc', 'word', 'mame_tcc_bit0'],
        code=[0xAF0F],
        regs={0: 0xA5A5},
        fcw=fcw_with_flags(C=1),
        # manual/z8000_emu: R0=0xA5A5 (unchanged)    MAME: R0=0xA5A4
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: ae0f            tccb    nc/uge,rh0
    tests.append(_tc(
        name='mame_tccb_false_bit0_preserved',
        mnemonic='TCCB',
        desc='TCCB NC,RH0 with C=1 (condition false) and RH0 bit 0 already set',
        tags=['control', 'tcc', 'byte', 'mame_tcc_bit0'],
        code=[0xAE0F],
        regs={0: 0xA5A5},
        fcw=fcw_with_flags(C=1),
        # manual/z8000_emu: R0=0xA5A5 (RH0 unchanged)    MAME: R0=0xA4A5
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: af07            tcc     c/ult,r0
    tests.append(_tc(
        name='mame_tcc_true_sets_bit0',
        mnemonic='TCC',
        desc='TCC C,R0 with C=1 (condition true): bit 0 set, other bits kept',
        tags=['control', 'tcc', 'word', 'mame_tcc_bit0'],
        code=[0xAF07],
        regs={0: 0xA5A4},
        fcw=fcw_with_flags(C=1),
        # Control: both give R0=0xA5A5. Pins that the set path is unaffected.
    ))

    # =====================================================================
    # PUSH / POP with a misaligned stack pointer
    #
    # z8000.md PUSH (:6774) / POP (:6697): the stack pointer is decremented /
    # incremented "by a value which equals the size in bytes of the operand" -
    # 2 for a word, 4 for a long.  No alignment correction is documented.
    #
    # The s8000 PR (9e781163995) added
    #     #define ADD_ALIGNED16(x, value) (x) += (value) - ((x) & 1)
    # to all four of PUSHW/POPW/PUSHL/POPL, so an odd SP is silently forced
    # even and the pointer moves by 3 (or 5) instead of 2 (or 4).
    # z8000_emu does not have this.  The two differ by exactly 1 in R15.
    #
    # The word WRITE/READ address is bit-0-masked by the bus in both cases, so
    # memory contents do NOT discriminate - R15 is the whole answer.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 93f0            push    @r15,r0
    tests.append(_tc(
        name='mame_push_odd_sp',
        mnemonic='PUSH',
        desc='PUSH @R15,R0 with R15 odd (0x0F01): SP must move by exactly 2',
        tags=['stack', 'word', 'mame_s8000_align'],
        code=[0x93F0],
        regs={0: 0x1234, 15: STACK_BASE + 1},
        observe_memory=[STACK_BASE - 2],
        # manual/z8000_emu: R15=0x0EFF    MAME s8000: R15=0x0EFE
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 97f0            pop     r0,@r15
    tests.append(_tc(
        name='mame_pop_odd_sp',
        mnemonic='POP',
        desc='POP R0,@R15 with R15 odd (0x0F01): SP must move by exactly 2',
        tags=['stack', 'word', 'mame_s8000_align'],
        code=[0x97F0],
        regs={0: 0x0000, 15: STACK_BASE + 1},
        memory={STACK_BASE: 0x1234},
        # manual/z8000_emu: R15=0x0F03    MAME s8000: R15=0x0F02
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 91f0            pushl   @r15,rr0
    tests.append(_tc(
        name='mame_pushl_odd_sp',
        mnemonic='PUSHL',
        desc='PUSHL @R15,RR0 with R15 odd (0x0F01): SP must move by exactly 4',
        tags=['stack', 'long', 'mame_s8000_align'],
        code=[0x91F0],
        regs={0: 0xDEAD, 1: 0xBEEF, 15: STACK_BASE + 1},
        observe_memory=[STACK_BASE - 4, STACK_BASE - 2],
        # manual/z8000_emu: R15=0x0EFD    MAME s8000: R15=0x0EFC
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 95f0            popl    rr0,@r15
    tests.append(_tc(
        name='mame_popl_odd_sp',
        mnemonic='POPL',
        desc='POPL RR0,@R15 with R15 odd (0x0F01): SP must move by exactly 4',
        tags=['stack', 'long', 'mame_s8000_align'],
        code=[0x95F0],
        regs={0: 0x0000, 1: 0x0000, 15: STACK_BASE + 1},
        memory={STACK_BASE: 0xDEAD, STACK_BASE + 2: 0xBEEF},
        # manual/z8000_emu: R15=0x0F05    MAME s8000: R15=0x0F04
    ))

    # =====================================================================
    # LDCTL FCW - which bits are writable
    #
    # z8000.md Figure 4-2 (:1047) gives the FCW as
    #     SEG S/N EPA VIE NVIE 0 0 0 | C Z S P/V DA H 0 0
    # so the architecturally writable mask is 0xF8FC.
    #
    # The s8000 PR sanitises the LDCTL FCW write with `RW(src) & 0xd8fc`,
    # which ALSO clears bit 13 (EPA) - a legitimate control bit.  z8000_emu
    # writes the value unmasked.  sys_ldctl_write_fcw uses R0=0x40F0, which
    # has EPA and every reserved bit clear, so it cannot tell these apart.
    #
    # Both tests keep S/N=1 and leave VIE/NVIE clear so the harness stays in
    # system mode and no interrupt can be enabled mid-capture.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 7d0a            ldctl   fcw,r0
    tests.append(_tc(
        name='mame_ldctl_fcw_epa_bit',
        mnemonic='LDCTL',
        desc='LDCTL FCW,R0 with EPA (bit 13) set: is EPA writable?',
        tags=['control', 'ldctl', 'fcw', 'mame_s8000_fcwmask'],
        code=[0x7D0A],
        regs={0: 0x60F0},
        # manual/z8000_emu: FCW=0x60F0    MAME s8000: FCW=0x40F0 (EPA dropped)
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: 7d0a            ldctl   fcw,r0
    tests.append(_tc(
        name='mame_ldctl_fcw_reserved_bits',
        mnemonic='LDCTL',
        desc='LDCTL FCW,R0 with EPA + reserved bits 10,1,0 set',
        tags=['control', 'ldctl', 'fcw', 'mame_s8000_fcwmask'],
        code=[0x7D0A],
        regs={0: 0x64F3},
        # Figure 4-2 says bits 10-8 and 1-0 read as 0.
        # manual: FCW=0x60F0   z8000_emu: FCW=0x64F3   MAME s8000: FCW=0x40F0
    ))

    # =====================================================================
    # SLL / SRL / SDL - V is architecturally UNDEFINED
    #
    # z8000.md: SLL V "Undefined" (:7873), SRL V "Undefined" (:8097),
    # SDL V "Undefined" (:7559).  (SLA/SDA/rotates are defined - "set if the
    # sign of the destination changed during shifting" - and are already
    # pinned by the sys_sda_*/sys_sll_* families.)
    #
    # dc69e30bb8e changed these three from CLR_CZS (V PRESERVED) to CLR_CZSV
    # plus a per-step accumulation, so they now WRITE the undefined flag.
    # z8000_emu carries the same change.  Nothing in the suite presets V
    # before a logical shift, so what the silicon actually does is unrecorded.
    # These captures make the undefined bit an observed fact rather than a
    # guess shared by two emulators.
    # =====================================================================

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b301 0001       sll     r0,#0x1
    tests.append(_tc(
        name='mame_sll_v_undefined',
        mnemonic='SLL',
        desc='SLL R0,#1 (no sign change) with V preset: is V preserved or written?',
        tags=['shift', 'word', 'flags', 'undefined', 'mame_dc69e30b'],
        code=[0xB301, 0x0001],
        regs={0: 0x0001},
        fcw=fcw_with_flags(V=1),
        # post-fix MAME + z8000_emu: V=0 (recomputed)    pre-fix MAME: V=1
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b301 ffff       srl     r0,#0x1
    tests.append(_tc(
        name='mame_srl_v_undefined',
        mnemonic='SRL',
        desc='SRL R0,#1 from 0x8000 (msb drops) with V clear: is V written?',
        tags=['shift', 'word', 'flags', 'undefined', 'mame_dc69e30b'],
        code=[0xB301, 0xFFFF],
        regs={0: 0x8000},
        # post-fix MAME + z8000_emu: V=1 (msb changed)    pre-fix MAME: V=0
    ))

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, .text=0x200)
    #   200: b303 0100       sdl     r0,r1
    tests.append(_tc(
        name='mame_sdl_v_undefined',
        mnemonic='SDL',
        desc='SDL R0,R1 shifting right out of 0x8000 with V clear: is V written?',
        tags=['shift', 'word', 'dynamic', 'flags', 'undefined', 'mame_dc69e30b'],
        code=[0xB303, 0x0100],
        regs={0: 0x8000, 1: 0xFFFF},
        # count -1 => right shift by 1.
        # post-fix MAME + z8000_emu: V=1    pre-fix MAME: V=0
    ))

    # =====================================================================
    # SEGMENTED TESTS (target z8001-seg, golden/z8001-seg)
    #
    # All addresses stay in segment 0. Segmented pointers are built with LDA
    # (never hand-coded) per CLAUDE.md; the assembler does NOT pack a literal
    # segment-1 address correctly, so segment 1 is avoided entirely here.
    # =====================================================================

    # ---------------------------------------------------------------------
    # b1a960d0d80 - "fix addr_to_reg segment mask to replace full high byte"
    #
    # Writing a segmented address back to a register pair masked in only the
    # 7-bit segment field and PRESERVED bit 15 of whatever was in the
    # register:  (RW & 0x80ff) | (seg & 0x7f00)   ->   (RW & 0x00ff) | (seg & 0xff00)
    #
    # Poison R2 with bit 15 set, then LDA a segment-0 address into RR2:
    #   post-fix: R2 = 0x00AA, R3 = 0x0400
    #   pre-fix : R2 = 0x80AA, R3 = 0x0400
    # (Both keep the low byte 0xAA - the capture also tells us whether the
    # silicon keeps it at all.)
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, .text=0x200, SEG0=0x0)
    #   200: 7602 8000 0400  lda     rr2,0x400
    tests.append(_tc(
        name='seg_mame_lda_da_hiword_bit15',
        mnemonic='LDA',
        desc='LDA RR2, <<0>>0x400 with bit 15 poisoned in R2 (segment writeback mask)',
        tags=['segmented', 'seg0', 'lda', 'long_da', 'mame_b1a960d0'],
        code=[0x7602, 0x8000, 0x0400],
        regs={2: 0x80AA, 3: 0x1234},
        fcw=FCW_SEG,
        target='z8001-seg',
    ))

    # ---------------------------------------------------------------------
    # 9f576c1780a (segmented form) - indexed LDA with an overlapping index.
    #
    # LDA RR2, RR4(R2): the index register R2 is the high half of the
    # destination pair, so it is overwritten by `RL(dst) = RL(src)` before the
    # index is read.
    #   post-fix: RR2 = seg0:0x0412 (base 0x400 + index 0x12)
    #   pre-fix : RR2 = seg0:0x0400 (index read back as 0)
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, .text=0x200, SEG0=0x0)
    #   200: 7604 8000 0400  lda     rr4,0x400
    #   206: 7442 0200       lda     rr2,rr4(r2)
    tests.append(_tc(
        name='seg_mame_lda_bx_index_overlap',
        mnemonic='LDA',
        desc='LDA RR2, RR4(R2): index register is inside the destination pair',
        tags=['segmented', 'seg0', 'lda', 'bx_pair', 'mame_9f576c17'],
        code=[0x7604, 0x8000, 0x0400,
              0x7442, 0x0200],
        regs={2: 0x0012, 3: 0x0000, 4: 0x0000, 5: 0x0000},
        fcw=FCW_SEG,
        target='z8001-seg',
    ))

    # ---------------------------------------------------------------------
    # d3b65bf7234 - block-I/O destination increment (segmented form).
    #
    # SINIB used `RW(dst)++`, which bumps the SEGMENT word of the destination
    # pair instead of the offset. add_to_addr_reg advances the offset.
    #   post-fix: R4 = 0x0000, R5 = 0x0701   (offset advanced)
    #   pre-fix : R4 = 0x0001, R5 = 0x0700   (segment bumped to 1)
    # The Z-on-exhaustion difference from the non-segmented tests applies here
    # too (post-fix Z=1, pre-fix Z=0).
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, .text=0x200, SEG0=0x0)
    #   200: 7604 8000 0700  lda     rr4,0x700
    #   206: 3a21 0648       sinib   @rr4,@r2,r6
    tests.append(_tc(
        name='seg_mame_sinib_dst_offset_increment',
        mnemonic='SINIB',
        desc='SINIB @RR4, @R2, R6: destination increment must advance the offset',
        tags=['segmented', 'seg0', 'io', 'block_io', 'byte', 'special_io',
              'mame_d3b65bf7'],
        code=[0x7604, 0x8000, 0x0700,
              0x3A21, 0x0648],
        regs={2: PORT_BYTE, 4: 0x0000, 5: 0x0000, 6: 0x0001},
        fcw=FCW_SEG,
        memory={DST_BUF: 0x0000},
        io_preloads={IO_SPC_BYTE: 0xC3D4},
        observe_memory=[DST_BUF],
        observe_io=[IO_SPC_BYTE],
        target='z8001-seg',
    ))

    # ---------------------------------------------------------------------
    # 85b24e1e1cc - "fix SOTIRB/SOUTIB source not incrementing (bumped
    #                segment word instead of offset)"
    #
    # Same defect on the SOURCE pointer of the special block output. This is
    # the one that broke the Olivetti M40 Z8010 MMU descriptor load.
    #   post-fix: R4 = 0x0000, R5 = 0x0601
    #   pre-fix : R4 = 0x0001, R5 = 0x0600
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, .text=0x200, SEG0=0x0)
    #   200: 7604 8000 0600  lda     rr4,0x600
    #   206: 3a43 0628       soutib  @r2,@rr4,r6
    tests.append(_tc(
        name='seg_mame_soutib_src_offset_increment',
        mnemonic='SOUTIB',
        desc='SOUTIB @R2, @RR4, R6: source increment must advance the offset',
        tags=['segmented', 'seg0', 'io', 'block_io', 'byte', 'special_io',
              'mame_85b24e1e'],
        code=[0x7604, 0x8000, 0x0600,
              0x3A43, 0x0628],
        regs={2: PORT_BYTE, 4: 0x0000, 5: 0x0000, 6: 0x0001},
        fcw=FCW_SEG,
        memory={SRC_BUF: 0x99AA},
        io_preloads={IO_SPC_BYTE: 0x0000},
        observe_io=[IO_SPC_BYTE],
        target='z8001-seg',
    ))

    # ---------------------------------------------------------------------
    # LDAR reserved bits in the destination pair.
    #
    # z8000.md draws a distinction the shared addr_to_reg() helper cannot:
    #   LDA  (:4636) "the address loaded into the destination has an UNDEFINED
    #                 value in all reserved bits (bits 16-23 and bit 31)"
    #   LDAR (:4692) "the address loaded into the destination has all
    #                 'reserved' bits (bits 16-23 and bit 31) CLEARED TO ZERO"
    #
    # seg_mame_lda_da_hiword_bit15 already answers this for LDA: the silicon
    # returned R2=0x8000 from a poisoned 0x80AA, i.e. it DROPS the low byte
    # and SETS bit 31.  (z8000_emu matches; MAME's `(RW & 0x00ff) | ...`
    # returns 0x80AA and does not.)
    #
    # LDAR is NOT pinned the same way: seg_sys_ldar_r_near/fwd both start with
    # the destination at 0x0000, so the captured 0x8000 proves nothing about
    # clearing.  If the silicon really does clear bit 31 for LDAR (as the
    # manual says) then BOTH emulators are wrong here, because both route LDAR
    # through make_segmented_addr(), which unconditionally ORs in 0x80000000.
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001 + ld -Ttext 0x200)
    #   200: 3402 0014       ldar    rr2,0x218
    tests.append(_tc(
        name='seg_mame_ldar_ra_hiword_poison',
        mnemonic='LDAR',
        desc='LDAR RR2,0x218 with R2 poisoned 0xA5AA (reserved bits 16-23 / 31)',
        tags=['segmented', 'seg0', 'ldar', 'ra_mode', 'reserved_bits',
              'mame_b1a960d0'],
        code=[0x3402, 0x0014],
        regs={2: 0xA5AA, 3: 0x1234},
        fcw=FCW_SEG,
        target='z8001-seg',
        # manual:     R2=0x0000, R3=0x0218  (bits 16-23 and 31 cleared)
        # z8000_emu:  R2=0x8000, R3=0x0218  (low byte dropped, bit 31 set)
        # MAME:       R2=0x80AA, R3=0x0218  (low byte preserved, bit 31 set)
    ))

    # ---------------------------------------------------------------------
    # LDCTL PSAPSEG reserved-bit round-trip (companion to
    # seg_ldctl_psapoff_lowbyte, which already pinned PSAPOFF).
    #
    # z8000.md LDCTL PSAPSEG (:4825): `PSAPSEG (8:14) <- Rs (8:14)`, and the
    # readback (:4901) `Rd (8:14) <- PSAPSEG (8:14)`.  Figure 4-2 (:1053)
    # draws the PSAP high word as `0 | SEGMENT NUMBER | 0000000`.  So only
    # bits 8-14 (mask 0x7F00) survive in either direction.
    #
    # The s8000 PR masks both sides with 0x7f00.  z8000_emu leaves PSAPSEG
    # completely unmasked on read AND write, so writing 0xFFFF and reading it
    # back is the discriminator.
    #
    # PSAPOFF is deliberately left alone, so the PSA stays where the harness
    # bootstrap put it.
    # ---------------------------------------------------------------------

    # ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, linked at .text=0x200)
    #   200: 2101 ffff       ld    r1,#0xffff
    #   204: 7d1c            ldctl psapseg,r1
    #   206: 2102 0000       ld    r2,#0x0
    #   20a: 7d24            ldctl r2,psapseg
    tests.append(_tc(
        name='seg_mame_ldctl_psapseg_mask',
        mnemonic='LDCTL',
        desc='LDCTL PSAPSEG,R1(0xFFFF) then LDCTL R2,PSAPSEG (reserved-bit round-trip)',
        tags=['segmented', 'control', 'ldctl', 'psap', 'reserved_bits',
              'mame_s8000_psapmask'],
        code=[0x2101, 0xFFFF,
              0x7D1C,
              0x2102, 0x0000,
              0x7D24],
        regs={1: 0x0000, 2: 0x0000},
        fcw=FCW_SEG,
        target='z8001-seg',
        # manual/MAME s8000: R2=0x7F00    z8000_emu: R2=0xFFFF
        # R1 stays 0xFFFF either way (control).
    ))

    return tests


# =========================================================================
# Fixes on the z8000_fixes branch already discriminated by existing goldens
# (verified against the captured JSON - no new test needed):
#
#   390cf6af95e  DAB table, add side .... sys_dab_add_low_adj  (golden
#                R0=0x2000 C=0; pre-fix MAME: 0x80 C=1)
#                                         sys_dab_add_high_adj
#   e8967880e74  block-move Z flag ...... sys_ldirb_3bytes / sys_ldir_3words
#                (golden FCW=0x4050, Z=1 on exhaustion; pre-fix left Z=0)
#   e8967880e74  CPSIB single iteration . sys_cpsib_match / sys_cpsib_no_match
#   dc69e30bb8e  V accumulate on shifts . sys_sda_r_* / sys_sdl_r_* families
#   929639d8cbb  dynamic shift dispatch . sys_sdlb_r_*_r1/r4, sys_sdll_rr_*_r1/r4,
#                and count sign-extension  sys_sdal_rr_*_r1/r4
#   32e1b90916d  RRDB temp reg + S flag . sys_rrdb_bcd_* / sys_rldb_bcd_*
#   eb4f2e921d5  MULTL multiplicand ..... sys_multl_rq_rr_* (golden recaptured
#   c9e48f98397  MULTL/DIVL word order .. in fb91cfe from a bug-free SGS part)
#   999854723c2  EXTSL quad word order .. sys_extsl_rq_pos/neg/zero
#   94fd50898ae  COMFLG H toggle ........ sys_comflg_* (see FlagsUpdate.md 3.406)
#   bdf54b2a429  MULTW carry boundary ... sys_mult_* (31219ed)
#   216d1fe118e  DIV overflow quotient .. sys_div_* (masked case: DIV CASE 3)
#
# Findings settled by goldens that already exist (no new test needed):
#
#   DIVL CASE-4 sign, positive direction ... sys_divl_rq_rr_case4 /
#                seg_sys_divl_rq_rr_case4. Captured S=0 with the remnant
#                0xC0000000 in RR2, i.e. S comes from the FULL quotient.
#                z8000_emu matches; MAME's CHK_XXXL_ZS would give S=1.
#   LDA reserved bits ...................... seg_mame_lda_da_hiword_bit15.
#                Captured R2=0x8000 from a poisoned 0x80AA: the silicon drops
#                the reserved low byte and sets bit 31. z8000_emu matches;
#                MAME's `(RW & 0x00ff) | ...` (0x80AA) does not.
#   LDCTL PSAPOFF reserved low byte ........ seg_ldctl_psapoff_lowbyte
#                (R1=0x08FF written, R2=0x0800 read back).
#   MULTW carry boundary ................... sys_mult_rr_r_bound_pos/neg/over
#
# Not covered - not reachable from this harness:
#
#   d0a3f540264  4F EPU family trap. Needs the extended-instruction trap to be
#                taken and vectored through the PSA; the harness bootstrap has
#                no trap handler, so the test would end in TOUT/NRST rather
#                than a comparable state. The same applies to the Z8F/0F/8F
#                extended-instruction families and to z8000_emu's commented-out
#                CHECK_EXT_INSTR() in Z8F_imm8.
#
#   PSA address space (program vs data). The s8000 PR moved GET_PC/GET_FCW/
#                read_irq_vector from m_program to m_data. Discriminating this
#                needs a memory system that decodes ST3-ST0 into separate
#                program and data spaces AND a trap/interrupt that vectors
#                through the PSA. The harness has one flat memory and no
#                status-line decode, so both choices look identical here.
#                (z8000.md 7.7.3 says the PSA fetch drives IF_N = 1100 =
#                Program Address Space, so m_program is the documented
#                behaviour - but that is a manual reading, not a capture.)
#
#   Interrupt/trap priority order (z8000.md 7.8). Needs two exceptions raised
#                simultaneously plus PSA-vectored handlers; same blocker as
#                the EPU trap above.
# =========================================================================
