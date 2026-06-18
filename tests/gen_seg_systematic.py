"""Segmented systematic test generator.

Transforms all 826 tests from gen_systematic.py to run under Z8001 segmented mode.
- Non-DA tests: identical code, FCW has SEG bit set
- DA tests: long-form (insert 0x8000 segment word) + short-form (no segment word)
- Branch/CALL DA: long-form only (targets >= 0x200 can't short-form)
"""

import re

from .gen_systematic import generate_all_tests
from .defs import TestCase
from .helpers import CODE_BASE, STACK_BASE

SEG1_SHORT_WORD = 0x0180  # Short-form DA: segment 1, offset 0x80
SEG1_SHORT_OFFSET = SEG1_SHORT_WORD & 0x00FF
SEG1_SHORT_PHYS_ADDR = 0x1000 + SEG1_SHORT_OFFSET
OPERAND_BASE = 0x0400

_SKIP_TESTS = {
    'sys_lda_r_da_operand',   # LDA semantics change in segmented mode
    'sys_lda_r_da_src',       # LDA semantics change in segmented mode
    'sys_ldctl_write_fcw',    # Would clear SEG bit, breaking dump routine
}

_PORT_INDIRECT_MNEMONICS = {'IN', 'INB', 'OUT', 'OUTB'}
_BLOCK_TRANSFER_MNEMONICS = {
    'LDI', 'LDIR', 'LDD', 'LDDR',
    'LDIB', 'LDIRB', 'LDDB', 'LDDRB',
}
_BLOCK_COMPARE_MNEMONICS = {
    'CPI', 'CPIR', 'CPD', 'CPDR',
    'CPIB', 'CPIRB', 'CPDB', 'CPDRB',
}
_BLOCK_STRING_MNEMONICS = {
    'CPSI', 'CPSIR', 'CPSD', 'CPSDR',
    'CPSIB', 'CPSIRB', 'CPSDB', 'CPSDRB',
}
_TRANSLATE_MNEMONICS = {
    'TRIB', 'TRIRB', 'TRDB', 'TRDRB',
    'TRTIB', 'TRTIRB', 'TRTDB', 'TRTDRB',
}
_SEG_BLOCK_SRC_REG = 8
_SEG_BLOCK_DST_REG = 10
_SEG_BLOCK_COUNT_REG = 4
_SEG_BLOCK_CMP_REG = 0
_ALL_BLOCK_MNEMONICS = (
    _BLOCK_TRANSFER_MNEMONICS | _BLOCK_COMPARE_MNEMONICS |
    _BLOCK_STRING_MNEMONICS | _TRANSLATE_MNEMONICS
)


def generate_seg_systematic_tests():
    """Generate segmented variants of all systematic tests."""
    results = []
    for t in generate_all_tests():
        if t.name in _SKIP_TESTS:
            continue
        results.extend(_transform(t))
    return results


def _transform(t):
    """Transform a single test into segmented variant(s)."""
    tags = set(t.tags)
    tag_names = {tag.lower() for tag in tags}
    seg_fcw = t.fcw | 0x8000

    # Tests containing CALL DA (0x5F00 opcode in code) -> long-form only
    if 0x5F00 in t.code:
        return [_make_call_long(t, seg_fcw)]

    # Branch JP with DA -> long-form only (targets >= 0x200)
    if 'branch' in tag_names and 'da_mode' in tag_names:
        return [_make_branch_long(t, seg_fcw)]

    # Block instructions use address registers. In segmented mode those are
    # register pairs, so the source, destination, and counter must not overlap.
    if t.mnemonic in _BLOCK_TRANSFER_MNEMONICS:
        return [_make_block_transfer_seg(t, seg_fcw)]
    if t.mnemonic in _BLOCK_COMPARE_MNEMONICS:
        return [_make_block_compare_seg(t, seg_fcw)]
    if t.mnemonic in _BLOCK_STRING_MNEMONICS:
        return [_make_block_string_seg(t, seg_fcw)]
    if t.mnemonic in _TRANSLATE_MNEMONICS:
        return [_make_translate_seg(t, seg_fcw)]

    # Simple DA (ALU + LD/ST) -> long + short
    if 'da_mode' in tag_names:
        return [_make_da_long(t, seg_fcw), _make_da_short(t, seg_fcw)]

    # Indexed DA -> long + short
    if 'x_mode' in tag_names:
        return [_make_x_long(t, seg_fcw), _make_x_short(t, seg_fcw)]

    # IR_mode: convert indirect register to segmented pointer pair
    if 'ir_mode' in tag_names:
        return [_make_ir_seg(t, seg_fcw)]

    # BA_mode: base register becomes segmented pointer pair; displacement stays
    if 'ba_mode' in tag_names:
        return [_make_ba_seg(t, seg_fcw)]

    # BX_mode: base register becomes segmented pointer pair; index stays scalar
    if 'bx_mode' in tag_names:
        return [_make_bx_seg(t, seg_fcw)]

    # Non-DA/IR: identical code, just segmented FCW
    # Add stack verification for CALR tests (opcode 0xDxxx)
    calr_idx = next((i for i, w in enumerate(t.code) if (w & 0xF000) == 0xD000), None)
    if calr_idx is not None and 'call' in tag_names:
        ret_addr = CODE_BASE + (calr_idx + 1) * 2
        expected_memory = dict(t.expected_memory)
        expected_memory[STACK_BASE - 4] = 0x8000   # PCSEG
        expected_memory[STACK_BASE - 2] = ret_addr  # PC offset
        return [_clone(t, f"seg_{t.name}", seg_fcw,
                        expected_memory=expected_memory)]
    return [_clone(t, f"seg_{t.name}", seg_fcw)]


def _clone(t, name, fcw, **overrides):
    """Clone a test case with new name, FCW, and optional field overrides."""
    tc = TestCase(
        name=name,
        mnemonic=t.mnemonic,
        description=t.description,
        tags=["systematic", "segmented"] + [x for x in t.tags if x != "systematic"],
        instruction=t.instruction,
        target="z8001-seg",
        issues=list(t.issues),
        code=list(t.code),
        regs=dict(t.regs),
        fcw=fcw,
        memory=dict(t.memory),
        io_preloads=dict(t.io_preloads),
        expected_regs=dict(t.expected_regs),
        expected_fcw_set=list(t.expected_fcw_set),
        expected_fcw_clear=list(t.expected_fcw_clear),
        expected_memory=dict(t.expected_memory),
        expected_io=dict(t.expected_io),
        observe_memory=list(t.observe_memory),
        observe_io=list(t.observe_io),
        expected_trace=t.expected_trace,
        expected_result=t.expected_result,
    )
    for key, val in overrides.items():
        setattr(tc, key, val)
    if (tc.fcw & 0x8000 and
            tc.mnemonic not in _PORT_INDIRECT_MNEMONICS and
            tc.mnemonic not in _ALL_BLOCK_MNEMONICS):
        tc.regs = _with_segmented_indirect_regs(tc)
    return tc


def _with_segmented_indirect_regs(t):
    regs = dict(t.regs)
    for ireg in _assembly_indirect_regs(t):
        if ireg >= 15:
            raise ValueError(f"{t.name}: @r{ireg} cannot form a segmented pointer")
        if regs.get(ireg) == 0x8000:
            continue
        flat_addr = regs.get(ireg, 0)
        regs[ireg] = 0x8000
        regs[ireg + 1] = flat_addr
    return regs


# --- DA long-form: insert 0x8000 segment word after opcode ---

def _make_da_long(t, fcw):
    """Simple DA -> segmented long-form: [opcode, 0x8000, DA]."""
    code = list(t.code)
    code.insert(_address_word_index(t), 0x8000)
    return _clone(t, f"seg_{t.name}_long", fcw, code=code)


def _make_da_short(t, fcw):
    """Simple DA -> segmented short-form: [opcode, short_DA], memory remapped."""
    code = list(t.code)
    code[_address_word_index(t)] = SEG1_SHORT_WORD
    memory = _remap_operand_mem(t.memory)
    observe_memory = _remap_operand_addrs(t.observe_memory)
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, memory=memory,
                  observe_memory=observe_memory)


# --- X mode: indexed DA ---

def _make_x_long(t, fcw):
    """Indexed DA -> segmented long-form: [opcode, 0x8000, DA]."""
    code = list(t.code)
    code.insert(_address_word_index(t), 0x8000)
    return _clone(t, f"seg_{t.name}_long", fcw, code=code)


def _make_x_short(t, fcw):
    """Indexed DA -> segmented short-form: [opcode, short_DA], memory remapped.

    Preserves the parity of the effective address so byte-at-odd-address tests
    keep their odd effective addr in short form.
    """
    index_reg = (t.code[0] >> 4) & 0xF
    index_val = t.regs.get(index_reg, 0)
    address_idx = _address_word_index(t)
    orig_da = t.code[address_idx]
    orig_parity = (orig_da + index_val) & 1
    target_offset = (SEG1_SHORT_OFFSET & ~1) | orig_parity
    new_da = target_offset - index_val
    regs = dict(t.regs)
    if new_da < 0 or new_da > 0x00FF:
        index_val = 0x0010
        regs[index_reg] = index_val
        new_da = target_offset - index_val
    code = list(t.code)
    code[address_idx] = (SEG1_SHORT_WORD & 0x7F00) | (new_da & 0x00FF)
    target_phys = 0x1000 + target_offset
    delta = target_phys - ((orig_da + t.regs.get(index_reg, 0)) & 0xFFFF)
    memory = _remap_operand_mem(t.memory, delta)
    observe_memory = _remap_operand_addrs(t.observe_memory, delta)
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, regs=regs,
                  memory=memory, observe_memory=observe_memory)


def _address_word_index(t):
    """Return the code word containing the DA/X address operand."""
    return 2 if t.mnemonic == "LDM" and len(t.code) > 2 else 1


# --- IR_mode: convert indirect register to segmented pointer pair ---

def _make_ir_seg(t, fcw):
    """IR_mode -> segmented: convert every @Rn to a segmented pointer pair.

    In segmented mode, indirect addressing uses a register pair:
      R(n)   = 0x8000 | (segment << 8)  -- long-form segment selector
      R(n+1) = offset
    All generated IR_mode tests use segment 0, so R(n) = 0x8000.
    """
    regs = dict(t.regs)
    for ireg in _indirect_regs(t):
        flat_addr = regs.get(ireg, 0)
        regs[ireg] = 0x8000       # segment 0, long form
        regs[ireg + 1] = flat_addr  # offset
    return _clone(t, f"seg_{t.name}", fcw, regs=regs)


# --- BA_mode: base register becomes segmented pointer pair ---

def _make_ba_seg(t, fcw):
    """BA_mode -> segmented: base register pair holds segmented pointer.

    In segmented mode the base of a base+displacement access is a register
    pair: R(n) = 0x8000 (seg 0, long form), R(n+1) = offset. The 16-bit
    displacement word in the instruction is unchanged.
    """
    breg = (t.code[0] >> 4) & 0xF  # base register from opcode bits [7:4]
    flat_addr = t.regs.get(breg, 0)
    regs = dict(t.regs)
    regs[breg] = 0x8000
    regs[breg + 1] = flat_addr
    return _clone(t, f"seg_{t.name}", fcw, regs=regs)


def _make_bx_seg(t, fcw):
    """BX_mode -> segmented: base register pair holds segmented pointer.

    The index register remains a scalar displacement. Tests must choose a base
    register pair that does not overlap the index or destination registers.
    """
    breg = (t.code[0] >> 4) & 0xF
    flat_addr = t.regs.get(breg, 0)
    regs = dict(t.regs)
    regs[breg] = 0x8000
    regs[breg + 1] = flat_addr
    return _clone(t, f"seg_{t.name}", fcw, regs=regs)


# --- Block instructions: use non-overlapping segmented register pairs ---

def _make_block_transfer_seg(t, fcw):
    """LDI/LDD family: @RRsrc, @RRdst, and count must not overlap."""
    src_old, count_old, dst_old = _block_fields(t)
    regs = _block_regs(t, src_old, count_old, dst_old)
    code = _block_code(t, _SEG_BLOCK_SRC_REG, _SEG_BLOCK_COUNT_REG,
                       _SEG_BLOCK_DST_REG)
    return _clone(t, f"seg_{t.name}", fcw, code=code, regs=regs)


def _make_block_compare_seg(t, fcw):
    """CPI/CPD family: source pointer pair must not overlap the counter."""
    src_old, count_old, cmp_old = _block_fields(t)
    regs = dict(t.regs)
    src_offset = t.regs.get(src_old, 0)
    cmp_value = t.regs.get(cmp_old, 0)
    regs.pop(src_old, None)
    regs.pop(count_old, None)
    regs.pop(cmp_old, None)
    regs[_SEG_BLOCK_COUNT_REG] = t.regs.get(count_old, 0)
    regs[_SEG_BLOCK_CMP_REG] = cmp_value
    _put_seg_ptr(regs, _SEG_BLOCK_SRC_REG, src_offset)
    code = _block_code(t, _SEG_BLOCK_SRC_REG, _SEG_BLOCK_COUNT_REG,
                       _SEG_BLOCK_CMP_REG)
    return _clone(t, f"seg_{t.name}", fcw, code=code, regs=regs)


def _make_block_string_seg(t, fcw):
    """CPSI/CPSD family: both memory operands are segmented pointer pairs."""
    src_old, count_old, dst_old = _block_fields(t)
    regs = _block_regs(t, src_old, count_old, dst_old)
    code = _block_code(t, _SEG_BLOCK_SRC_REG, _SEG_BLOCK_COUNT_REG,
                       _SEG_BLOCK_DST_REG)
    return _clone(t, f"seg_{t.name}", fcw, code=code, regs=regs)


def _make_translate_seg(t, fcw):
    """TR*/TRT* family: destination/string, table, and count must not overlap."""
    dst_old = (t.code[0] >> 4) & 0xF
    count_old = (t.code[1] >> 8) & 0xF
    table_old = (t.code[1] >> 4) & 0xF
    regs = dict(t.regs)
    dst_offset = t.regs.get(dst_old, 0)
    table_offset = t.regs.get(table_old, 0)
    count = t.regs.get(count_old, 0)
    for old in (dst_old, count_old, table_old):
        regs.pop(old, None)
    _put_seg_ptr(regs, _SEG_BLOCK_DST_REG, dst_offset)
    _put_seg_ptr(regs, _SEG_BLOCK_SRC_REG, table_offset)
    regs[_SEG_BLOCK_COUNT_REG] = count
    code = list(t.code)
    code[0] = (code[0] & 0xFF0F) | (_SEG_BLOCK_DST_REG << 4)
    code[1] = ((code[1] & 0xF00F) |
               (_SEG_BLOCK_COUNT_REG << 8) |
               (_SEG_BLOCK_SRC_REG << 4))
    return _clone(t, f"seg_{t.name}", fcw, code=code, regs=regs)


def _block_fields(t):
    """Return source, counter, and destination/compare fields."""
    return (t.code[0] >> 4) & 0xF, (t.code[1] >> 8) & 0xF, (t.code[1] >> 4) & 0xF


def _block_code(t, src_reg, count_reg, dst_or_cmp_reg):
    code = list(t.code)
    code[0] = (code[0] & 0xFF0F) | (src_reg << 4)
    code[1] = (code[1] & 0xF00F) | (count_reg << 8) | (dst_or_cmp_reg << 4)
    return code


def _block_regs(t, src_old, count_old, dst_old):
    regs = dict(t.regs)
    src_offset = t.regs.get(src_old, 0)
    dst_offset = t.regs.get(dst_old, 0)
    count = t.regs.get(count_old, 0)
    if dst_offset == src_offset:
        dst_offset = (dst_offset + 0x10) & 0xFFFF
    for old in (src_old, count_old, dst_old):
        regs.pop(old, None)
    _put_seg_ptr(regs, _SEG_BLOCK_SRC_REG, src_offset)
    _put_seg_ptr(regs, _SEG_BLOCK_DST_REG, dst_offset)
    regs[_SEG_BLOCK_COUNT_REG] = count
    return regs


def _put_seg_ptr(regs, reg, offset):
    regs[reg] = 0x8000
    regs[reg + 1] = offset


def _indirect_regs(t):
    regs = _assembly_indirect_regs(t)
    if not regs:
        regs.add((t.code[0] >> 4) & 0xF)
    return regs


def _assembly_indirect_regs(t):
    return {int(m.group(1)) for m in re.finditer(r"@r(\d+)", t.instruction or "")}


# --- Branch JP with DA: long-form only, target += 2 ---

def _make_branch_long(t, fcw):
    """Branch JP DA -> segmented long-form: insert segment word, adjust target."""
    code = list(t.code)
    code[1] += 2  # adjust target for inserted segment word
    code.insert(1, 0x8000)
    return _clone(t, f"seg_{t.name}", fcw, code=code)


# --- CALL DA: long-form only, adjust target ---

def _make_call_long(t, fcw):
    """CALL DA -> segmented long-form: insert segment word after CALL opcode."""
    code = list(t.code)
    idx = code.index(0x5F00)
    code[idx + 1] += 2  # adjust target
    code.insert(idx + 1, 0x8000)
    # Verify stack residue: CALL is 3 words in seg long-form,
    # return address = CODE_BASE + (idx + 3) * 2
    ret_addr = CODE_BASE + (idx + 3) * 2
    expected_memory = dict(t.expected_memory)
    expected_memory[STACK_BASE - 4] = 0x8000   # PCSEG (segment 0, long form)
    expected_memory[STACK_BASE - 2] = ret_addr  # PC offset
    return _clone(t, f"seg_{t.name}", fcw, code=code,
                  expected_memory=expected_memory)


# --- Memory remapping ---

def _remap_operand_mem(mem, delta=None):
    """Remap memory addresses from OPERAND_BASE region to segment-1 short space."""
    if delta is None:
        delta = SEG1_SHORT_PHYS_ADDR - OPERAND_BASE
    return {
        (((addr + delta) & 0xFFFF) if _is_operand_mem(addr) else addr): val
        for addr, val in mem.items()
    }


def _remap_operand_addrs(addrs, delta=None):
    """Remap observed flat operand addresses to segment-1 short physical space."""
    if delta is None:
        delta = SEG1_SHORT_PHYS_ADDR - OPERAND_BASE
    return [
        (((addr + delta) & 0xFFFF) if _is_operand_mem(addr) else addr)
        for addr in addrs
    ]


def _is_operand_mem(addr):
    return OPERAND_BASE - 0x20 <= addr < OPERAND_BASE + 0x40
