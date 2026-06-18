"""Golden result capture, storage, and comparison utilities.

Saves Z8001 test results to JSON files and compares Z8002 results against them.
Follows the same one-file-per-test pattern as traces.py.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .flags import FLAG_BITS, get_flag


@dataclass
class ComparisonDiff:
    """A single field difference between golden and actual results.

    ``masked`` marks a difference in a field the architecture leaves undefined
    (see golden_masks.py); ``reason`` documents why.  Masked diffs do not count
    toward failure but are retained for display.
    """
    field: str
    ref_value: object
    dut_value: object
    description: str
    masked: bool = False
    reason: str = ""


@dataclass
class ComparisonResult:
    """Result of comparing one test's actual output against golden reference."""
    test_name: str
    match: bool
    diffs: list[ComparisonDiff] = field(default_factory=list)

    @property
    def unmasked_diffs(self):
        """Differences that count as failures (undefined fields excluded)."""
        return [d for d in self.diffs if not d.masked]

    @property
    def masked_diffs(self):
        """Differences ignored because the field is architecturally undefined."""
        return [d for d in self.diffs if d.masked]


def save_golden(results, golden_dir):
    """Save golden results to JSON files (one per test).

    Args:
        results: list of TestResult from running tests on reference CPU
        golden_dir: directory to write JSON files into

    Returns:
        number of files written
    """
    os.makedirs(golden_dir, exist_ok=True)

    count = 0
    for r in results:
        path = os.path.join(golden_dir, f"{r.test.name}.json")
        data = {
            "test": r.test.name,
            "mnemonic": r.test.mnemonic,
            "exec_result": r.exec_result,
            "regs": {str(k): v for k, v in sorted(r.actual_regs.items())},
            "fcw": r.actual_fcw,
            "memory": {str(k): v for k, v in sorted(r.actual_memory.items())},
            "io": {str(k): v for k, v in sorted(r.actual_io.items())},
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        count += 1

    return count


def load_golden(golden_dir):
    """Load all golden results from a directory.

    Returns:
        dict mapping test_name -> golden data dict
    """
    if not os.path.isdir(golden_dir):
        return {}

    golden = {}
    for name in os.listdir(golden_dir):
        if name.endswith('.json'):
            with open(os.path.join(golden_dir, name)) as f:
                data = json.load(f)
            golden[data["test"]] = data
    return golden


def compare_golden(results, golden, masks=None):
    """Compare test results against golden reference data.

    Args:
        results: list of TestResult from DUT
        golden: dict from load_golden()
        masks: optional GoldenMasks (golden_masks.py). Fields it flags as
            architecturally undefined are recorded as masked diffs and do not
            count toward a mismatch.

    Returns:
        list of ComparisonResult
    """
    comparisons = []

    for r in results:
        name = r.test.name
        if name not in golden:
            comparisons.append(ComparisonResult(
                test_name=name,
                match=False,
                diffs=[ComparisonDiff(
                    field="golden",
                    ref_value=None,
                    dut_value=None,
                    description="no golden reference",
                )],
            ))
            continue

        ref = golden[name]
        diffs = []

        # Compare exec_result
        if r.exec_result != ref["exec_result"]:
            diffs.append(ComparisonDiff(
                field="exec_result",
                ref_value=ref["exec_result"],
                dut_value=r.exec_result,
                description=(f"exec_result: ref={ref['exec_result']}, "
                             f"dut={r.exec_result}"),
            ))

        # Compare registers - only those present on either side
        ref_regs = {int(k): v for k, v in ref.get("regs", {}).items()}
        all_reg_keys = set(r.actual_regs.keys()) | set(ref_regs.keys())
        for reg in sorted(all_reg_keys):
            ref_val = ref_regs.get(reg, 0)
            dut_val = r.actual_regs.get(reg, 0)
            if ref_val != dut_val:
                ref_str = f"0x{ref_val:04X}" if ref_val is not None else "None"
                dut_str = f"0x{dut_val:04X}" if dut_val is not None else "None"
                diffs.append(ComparisonDiff(
                    field=f"R{reg}",
                    ref_value=ref_val,
                    dut_value=dut_val,
                    description=(f"R{reg}: ref={ref_str}, "
                                 f"dut={dut_str}"),
                ))

        # Compare flags individually
        ref_fcw = ref.get("fcw")
        dut_fcw = r.actual_fcw
        if ref_fcw is not None and dut_fcw is not None:
            for flag_name in ('C', 'Z', 'S', 'V', 'DA', 'H'):
                ref_flag = get_flag(ref_fcw, flag_name)
                dut_flag = get_flag(dut_fcw, flag_name)
                if ref_flag != dut_flag:
                    diffs.append(ComparisonDiff(
                        field=f"flag_{flag_name}",
                        ref_value=ref_flag,
                        dut_value=dut_flag,
                        description=(f"{flag_name}: ref={ref_flag}, "
                                     f"dut={dut_flag}"),
                    ))

        # Compare requested memory readbacks.
        ref_mem = {int(k): v for k, v in ref.get("memory", {}).items()}
        all_mem_keys = set(r.actual_memory.keys()) | set(ref_mem.keys())
        for addr in sorted(all_mem_keys):
            ref_val = ref_mem.get(addr, 0)
            dut_val = r.actual_memory.get(addr, 0)
            if ref_val != dut_val:
                ref_str = f"0x{ref_val:04X}" if ref_val is not None else "None"
                dut_str = f"0x{dut_val:04X}" if dut_val is not None else "None"
                diffs.append(ComparisonDiff(
                    field=f"mem_0x{addr:04X}",
                    ref_value=ref_val,
                    dut_value=dut_val,
                    description=(f"[0x{addr:04X}]: ref={ref_str}, "
                                 f"dut={dut_str}"),
                ))

        # Compare requested I/O readbacks.
        ref_io = {int(k): v for k, v in ref.get("io", {}).items()}
        all_io_keys = set(r.actual_io.keys()) | set(ref_io.keys())
        for idx in sorted(all_io_keys):
            ref_val = ref_io.get(idx, 0)
            dut_val = r.actual_io.get(idx, 0)
            if ref_val != dut_val:
                ref_str = f"0x{ref_val:04X}" if ref_val is not None else "None"
                dut_str = f"0x{dut_val:04X}" if dut_val is not None else "None"
                diffs.append(ComparisonDiff(
                    field=f"io_0x{idx:02X}",
                    ref_value=ref_val,
                    dut_value=dut_val,
                    description=(f"IO[0x{idx:02X}]: ref={ref_str}, "
                                 f"dut={dut_str}"),
                ))

        # Reclassify diffs in architecturally-undefined fields as masked so
        # they are reported but do not count as failures.
        if masks is not None:
            field_masks = masks.field_masks(r.test, ref)
            for d in diffs:
                if d.field in field_masks:
                    d.masked = True
                    d.reason = field_masks[d.field]

        comparisons.append(ComparisonResult(
            test_name=name,
            match=all(d.masked for d in diffs),
            diffs=diffs,
        ))

    return comparisons
