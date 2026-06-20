"""Undefined-output masking for golden comparison.

The golden captures (golden/z8001/, golden/z8001-seg/) are faithful recordings
of what the reference Z8001 silicon did.  Some instructions leave outputs that
the architecture explicitly declares *undefined* (e.g. the destination register
and S flag after a DIV that overflows).  In those cases the soft core is free to
produce a different value and still be correct -- so comparing those fields and
reporting a "failure" is misleading.

This module decides, per test, which comparison fields are architecturally
undefined and should therefore be ignored (masked) rather than failed.  Two
sources feed the decision:

  1. **Rule engine** -- general, condition-based rules keyed on the instruction
     and the *golden* result (built-in rules below).  A rule fires for every
     test it matches, current and future, with no per-test maintenance.

  2. **Named sidecar** -- ``tests/golden_masks.json``: explicit per-test field
     lists for one-off cases the rules don't cover.

Both attach a human-readable ``reason`` (citing the manual where relevant) so a
masked field is documented, not silently dropped.  Masking happens only at
compare time; the golden captures themselves are never modified.

Field names match those produced by ``compare_golden`` in golden.py:
``R<n>``, ``flag_<X>`` (C/Z/S/V/DA/H), ``mem_0x<addr>``, ``io_0x<idx>``,
``exec_result``.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional

from .flags import get_flag


DEFAULT_MASKS_PATH = os.path.join(os.path.dirname(__file__), "golden_masks.json")


@dataclass
class MaskRule:
    """A general, condition-based masking rule.

    ``fn`` receives ``(test, golden_entry)`` and returns either ``None`` (rule
    does not apply) or an iterable of comparison field names to mask.  The
    rule's ``reason`` is attached to every field it masks.
    """
    name: str
    reason: str
    fn: Callable[[object, dict], Optional[object]]


# ---------------------------------------------------------------------------
# Built-in rules
# ---------------------------------------------------------------------------

_ALL_REGISTER_FIELDS = {f"R{i}" for i in range(16)}


def _div_dest_from_operand(text):
    """Parse the destination register pair/quad from a DIV/DIVL operand string.

    The dividend/destination is the first operand: ``RRd`` (a pair) for DIV or
    ``RQd`` (a quad) for DIVL.  Parsing is scoped to the first operand so a
    source ``RR``/``RQ`` register is not mistaken for the destination
    (e.g. DIVL RQ0, RR4).  Returns the set of ``R<n>`` field names, or an empty
    set if it can't be parsed.
    """
    text = (text or "").lower()
    # First operand: text after the mnemonic, up to the first comma.
    parts = text.split(None, 1)
    dst = parts[1].split(",", 1)[0] if len(parts) > 1 else ""
    m = re.search(r"\brq(\d+)\b", dst)
    if m:
        d = int(m.group(1))
        return {f"R{d + i}" for i in range(4)}
    m = re.search(r"\brr(\d+)\b", dst)
    if m:
        d = int(m.group(1))
        return {f"R{d}", f"R{d + 1}"}
    return set()


def _div_dest_register_fields(test):
    """Destination register field names for a DIV/DIVL test.

    Tries the ``instruction`` string, then the ``description`` (systematic
    tests carry the operands there, e.g. "DIV RR0, R2: ..."), and falls back to
    all 16 registers.  The fallback is safe for the CASE 3 caller: the quotient
    overflowed so the whole destination is undefined, and DIV/DIVL only ever
    writes its destination register group -- the C/Z/V flags and memory remain
    compared.
    """
    for source in (getattr(test, "instruction", ""),
                   getattr(test, "description", "")):
        fields = _div_dest_from_operand(source)
        if fields:
            return fields
    return set(_ALL_REGISTER_FIELDS)


def _div_overflow_rule(test, golden):
    """DIV/DIVL CASE 3 overflow: destination register and S flag are undefined.

    Per z8000.md (DIV), when the quotient lies outside +/-2^16 (DIV) or
    +/-2^31 (DIVL), the destination register holds an undefined value and the
    sign flag is undefined; only V (=1), C (=0) and Z (=0) are defined.  This
    is distinguished from the other overflow outcomes by the flags themselves:

      - CASE 1 (in range):       V = 0          -> nothing masked
      - CASE 2 (divide by zero): V = 1, Z = 1   -> destination defined (unchanged)
      - CASE 4 (partial result): V = 1, C = 1   -> destination defined (partial)
      - CASE 3 (this rule):      V = 1, C = 0, Z = 0
    """
    if test.mnemonic not in ("DIV", "DIVL"):
        return None
    fcw = golden.get("fcw")
    if fcw is None:
        return None
    if not (get_flag(fcw, "V") == 1 and get_flag(fcw, "C") == 0
            and get_flag(fcw, "Z") == 0):
        return None
    return _div_dest_register_fields(test) | {"flag_S"}


_SHIFT_MNEMONICS = {
    "SDA", "SDAB", "SDAL", "SDL", "SDLB", "SDLL",
    "SLA", "SLAB", "SLAL", "SLL", "SLLB", "SLLL",
    "SRA", "SRAB", "SRAL", "SRL", "SRLB", "SRLL",
}


def _shift_zero_carry_rule(test, golden):
    """Shift by zero positions: the C flag is architecturally undefined.

    Per z8000.md (SDA/SDL/SLL families): "A shift of zero positions does not
    affect the destination; however, the flags are set according to the
    destination value.  The setting of the carry bit is undefined for zero
    shift."  Z and S remain defined (set from the destination), so only C is
    masked.  The 'zero_shift' tag marks the count-0 test variants.
    """
    if test.mnemonic not in _SHIFT_MNEMONICS:
        return None
    if "zero_shift" not in getattr(test, "tags", ()):
        return None
    return {"flag_C"}


_TRANSLATE_MNEMONICS = {"TRDB", "TRDRB", "TRIB", "TRIRB"}


def _translate_zero_flag_rule(test, golden):
    """Translate instructions leave the Z flag architecturally undefined.

    Per z8000.md (TRDB/TRDRB/TRIB/TRIRB): only V is defined (set if the counter
    decrements to zero); C/S/D/H are unaffected and Z is listed as Undefined.
    So Z is masked; everything else is still compared.
    """
    if test.mnemonic not in _TRANSLATE_MNEMONICS:
        return None
    return {"flag_Z"}


BUILTIN_RULES = [
    MaskRule(
        name="div_overflow_case3",
        reason=("DIV/DIVL overflow CASE 3 (quotient outside +/-2^16): "
                "destination register and S flag are architecturally undefined "
                "(z8000.md DIV)."),
        fn=_div_overflow_rule,
    ),
    MaskRule(
        name="shift_zero_carry",
        reason=("Shift by zero positions: the C flag is architecturally "
                "undefined (z8000.md SDA/SDL/SLL: \"undefined for zero shift\")."),
        fn=_shift_zero_carry_rule,
    ),
    MaskRule(
        name="translate_zero_flag",
        reason=("Translate instructions (TRDB/TRDRB/TRIB/TRIRB): the Z flag is "
                "architecturally undefined (z8000.md); only V is defined."),
        fn=_translate_zero_flag_rule,
    ),
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GoldenMasks:
    """Resolves which comparison fields are masked for a given test."""

    def __init__(self, named=None, rules=None):
        # named: {test_name: {"ignore_fields": [...], "reason": "..."}}
        self.named = named or {}
        self.rules = list(rules) if rules is not None else list(BUILTIN_RULES)

    def field_masks(self, test, golden_entry):
        """Return ``{field_name: reason}`` for one test/golden pair.

        First-writer wins so a named sidecar entry can override a rule's reason.
        """
        masks = {}

        entry = self.named.get(getattr(test, "name", None))
        if entry:
            reason = entry.get("reason", "masked (golden_masks.json)")
            for f in entry.get("ignore_fields", []):
                masks.setdefault(f, reason)

        for rule in self.rules:
            try:
                fields = rule.fn(test, golden_entry)
            except Exception:
                fields = None
            if not fields:
                continue
            for f in fields:
                masks.setdefault(f, rule.reason)

        return masks


def load_masks(path=DEFAULT_MASKS_PATH, enable_rules=True):
    """Load the named sidecar and (optionally) the built-in rules.

    A missing sidecar file is fine -- the rule engine still applies.  Pass
    ``enable_rules=False`` to use only explicit named entries.
    """
    named = {}
    if path and os.path.isfile(path):
        with open(path) as f:
            doc = json.load(f)
        named = doc.get("tests", {})
    rules = BUILTIN_RULES if enable_rules else []
    return GoldenMasks(named=named, rules=rules)
