"""Segmented systematic test generator.

Transforms all 826 tests from gen_systematic.py to run under Z8001 segmented mode.
- Non-DA tests: identical code, FCW has SEG bit set
- DA tests: long-form (insert 0x8000 segment word) + short-form (remap to offset < 256)
- Branch/CALL DA: long-form only (targets >= 0x200 can't short-form)
"""

import re

from .gen_systematic import generate_all_tests
from .defs import TestCase
from .helpers import CODE_BASE, STACK_BASE

SEG0_SHORT_ADDR = 0x00B4  # Short-form DA in seg 0 gap (between bootstrap and dump)
OPERAND_BASE = 0x0400

_SKIP_TESTS = {
    'sys_lda_r_da_operand',   # LDA semantics change in segmented mode
    'sys_lda_r_da_src',       # LDA semantics change in segmented mode
    'sys_ldctl_write_fcw',    # Would clear SEG bit, breaking dump routine
}

_PORT_INDIRECT_MNEMONICS = {'IN', 'INB', 'OUT', 'OUTB'}


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
        expected_trace=t.expected_trace,
        expected_result=t.expected_result,
    )
    for key, val in overrides.items():
        setattr(tc, key, val)
    if tc.fcw & 0x8000 and tc.mnemonic not in _PORT_INDIRECT_MNEMONICS:
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
    code[_address_word_index(t)] = SEG0_SHORT_ADDR
    memory = _remap_operand_mem(t.memory)
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, memory=memory)


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
    target = (SEG0_SHORT_ADDR & ~1) | orig_parity
    new_da = target - index_val
    regs = dict(t.regs)
    if new_da < 0 or new_da >= 0x8000:
        index_val = 0x0010
        regs[index_reg] = index_val
        new_da = target - index_val
    code = list(t.code)
    code[address_idx] = new_da & 0xFFFF
    delta = target - ((orig_da + t.regs.get(index_reg, 0)) & 0xFFFF)
    memory = {((addr + delta) & 0xFFFF): val for addr, val in t.memory.items()}
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, regs=regs, memory=memory)


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

def _remap_operand_mem(mem):
    """Remap memory addresses from OPERAND_BASE region to SEG0_SHORT_ADDR."""
    delta = SEG0_SHORT_ADDR - OPERAND_BASE
    return {((addr + delta) & 0xFFFF): val for addr, val in mem.items()}
