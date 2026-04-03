"""Segmented systematic test generator.

Transforms all 826 tests from gen_systematic.py to run under Z8001 segmented mode.
- Non-DA tests: identical code, FCW has SEG bit set
- DA tests: long-form (insert 0x8000 segment word) + short-form (remap to offset < 256)
- Branch/CALL DA: long-form only (targets >= 0x200 can't short-form)
"""

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
    seg_fcw = t.fcw | 0x8000

    # Tests containing CALL DA (0x5F00 opcode in code) -> long-form only
    if 0x5F00 in t.code:
        return [_make_call_long(t, seg_fcw)]

    # Branch JP with DA -> long-form only (targets >= 0x200)
    if 'branch' in tags and 'DA_mode' in tags:
        return [_make_branch_long(t, seg_fcw)]

    # Simple DA (ALU + LD/ST) -> long + short
    if 'DA_mode' in tags:
        return [_make_da_long(t, seg_fcw), _make_da_short(t, seg_fcw)]

    # Indexed DA -> long + short
    if 'X_mode' in tags:
        return [_make_x_long(t, seg_fcw), _make_x_short(t, seg_fcw)]

    # IR_mode: convert indirect register to segmented pointer pair
    if 'IR_mode' in tags:
        return [_make_ir_seg(t, seg_fcw)]

    # Non-DA/IR: identical code, just segmented FCW
    # Add stack verification for CALR tests (opcode 0xDxxx)
    calr_idx = next((i for i, w in enumerate(t.code) if (w & 0xF000) == 0xD000), None)
    if calr_idx is not None and 'call' in tags:
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
    return tc


# --- DA long-form: insert 0x8000 segment word after opcode ---

def _make_da_long(t, fcw):
    """Simple DA -> segmented long-form: [opcode, 0x8000, DA]."""
    code = list(t.code)
    code.insert(1, 0x8000)
    return _clone(t, f"seg_{t.name}_long", fcw, code=code)


def _make_da_short(t, fcw):
    """Simple DA -> segmented short-form: [opcode, short_DA], memory remapped."""
    code = [t.code[0], SEG0_SHORT_ADDR]
    memory = _remap_operand_mem(t.memory)
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, memory=memory)


# --- X mode: indexed DA ---

def _make_x_long(t, fcw):
    """Indexed DA -> segmented long-form: [opcode, 0x8000, DA]."""
    code = list(t.code)
    code.insert(1, 0x8000)
    return _clone(t, f"seg_{t.name}_long", fcw, code=code)


def _make_x_short(t, fcw):
    """Indexed DA -> segmented short-form: [opcode, short_DA], memory remapped."""
    # Extract index register and its value
    index_reg = (t.code[0] >> 4) & 0xF
    index_val = t.regs.get(index_reg, 0)
    new_da = SEG0_SHORT_ADDR - index_val
    code = [t.code[0], new_da]
    # Remap memory: shift by (new_da - OPERAND_BASE)
    delta = new_da - OPERAND_BASE
    memory = {addr + delta: val for addr, val in t.memory.items()}
    return _clone(t, f"seg_{t.name}_short", fcw, code=code, memory=memory)


# --- IR_mode: convert indirect register to segmented pointer pair ---

def _make_ir_seg(t, fcw):
    """IR_mode -> segmented: convert @Rn to @RRn (register pair as segmented pointer).

    In segmented mode, indirect addressing uses a register pair:
      R(n)   = 0x8000 | (segment << 8)  -- long-form segment selector
      R(n+1) = offset
    All existing IR_mode tests use segment 0, so R(n) = 0x8000.
    """
    ireg = (t.code[0] >> 4) & 0xF  # indirect register from opcode bits [7:4]
    flat_addr = t.regs.get(ireg, 0)
    regs = dict(t.regs)
    regs[ireg] = 0x8000       # segment 0, long form
    regs[ireg + 1] = flat_addr  # offset
    return _clone(t, f"seg_{t.name}", fcw, regs=regs)


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
    return {addr + delta: val for addr, val in mem.items()}
