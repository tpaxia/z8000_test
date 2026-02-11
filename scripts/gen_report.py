#!/usr/bin/env python3
"""Generate a verification report from Z8000 test results.

Runs the full test suite and produces a JSON results file plus a
human-readable markdown summary grouped by mnemonic and failure category.

Usage:
    python scripts/gen_report.py -p /dev/cu.usbserial-11401
    python scripts/gen_report.py -p /dev/cu.usbserial-11401 -o results/z8002_20260211
    python scripts/gen_report.py -p /dev/cu.usbserial-11401 --target z8001
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests import collect_all_tests
from tests.runner import TestRunner
from tests.harness import Z8000TestHarness
from tests.flags import format_flags


def classify_failure(failures):
    """Classify a failure into a category for grouping."""
    categories = set()
    for f in failures:
        if f.startswith("Flag "):
            categories.add("flags")
        elif f.startswith("R") and ": expected" in f:
            categories.add("result")
        elif f.startswith("Mem["):
            categories.add("memory")
        elif f.startswith("IO["):
            categories.add("io")
        elif f.startswith("Execution:"):
            if "TOUT" in f:
                categories.add("timeout")
            elif "NRST" in f:
                categories.add("no_halt")
            else:
                categories.add("execution")
    return categories or {"unknown"}


def result_to_dict(r):
    """Convert a TestResult to a serializable dict."""
    return {
        "name": r.test.name,
        "mnemonic": r.test.mnemonic,
        "description": r.test.description,
        "tags": r.test.tags,
        "target": r.test.target,
        "passed": r.passed,
        "exec_result": r.exec_result,
        "failures": r.failures,
        "actual_regs": {str(k): f"0x{v:04X}" if v is not None else None
                        for k, v in r.actual_regs.items()},
        "actual_fcw": f"0x{r.actual_fcw:04X}" if r.actual_fcw is not None else None,
        "cycle_count": r.cycle_count,
        "fetch_count": r.fetch_count,
    }


def generate_report(results, target, output_dir):
    """Generate JSON results and markdown report."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    # --- JSON results ---
    json_data = {
        "timestamp": timestamp,
        "target": target,
        "summary": {
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
        },
        "results": [result_to_dict(r) for r in results],
    }
    json_path = os.path.join(output_dir, "results.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    # --- Markdown report ---
    # Group by mnemonic
    by_mnemonic = defaultdict(lambda: {"passed": [], "failed": []})
    for r in results:
        key = "passed" if r.passed else "failed"
        by_mnemonic[r.test.mnemonic][key].append(r)

    # Group failures by category
    by_category = defaultdict(list)
    for r in failed:
        cats = classify_failure(r.failures)
        for cat in cats:
            by_category[cat].append(r)

    lines = []
    lines.append(f"# Z8000 Verification Report")
    lines.append(f"")
    lines.append(f"- **Date**: {timestamp}")
    lines.append(f"- **Target**: {target}")
    lines.append(f"- **Total**: {len(results)} tests")
    lines.append(f"- **Passed**: {len(passed)}")
    lines.append(f"- **Failed**: {len(failed)}")
    lines.append(f"")

    # Summary table by mnemonic
    lines.append(f"## Results by Mnemonic")
    lines.append(f"")
    lines.append(f"| Mnemonic | Pass | Fail | Total | Status |")
    lines.append(f"|----------|------|------|-------|--------|")
    for mnem in sorted(by_mnemonic.keys()):
        d = by_mnemonic[mnem]
        p, f = len(d["passed"]), len(d["failed"])
        status = "PASS" if f == 0 else "FAIL"
        lines.append(f"| {mnem:<8s} | {p:>4d} | {f:>4d} | {p+f:>5d} | {status} |")
    lines.append(f"")

    # Failure details
    if failed:
        lines.append(f"## Failures by Category")
        lines.append(f"")

        cat_names = {
            "flags": "Flag computation errors",
            "result": "Wrong register result",
            "memory": "Wrong memory content",
            "io": "Wrong I/O port value",
            "timeout": "Execution timeout (hung)",
            "no_halt": "Did not halt",
            "execution": "Unexpected execution result",
            "unknown": "Other",
        }

        for cat in ["timeout", "no_halt", "result", "flags", "memory", "io", "execution", "unknown"]:
            if cat not in by_category:
                continue
            cat_results = by_category[cat]
            lines.append(f"### {cat_names.get(cat, cat)} ({len(cat_results)})")
            lines.append(f"")

            for r in cat_results:
                lines.append(f"- **{r.test.mnemonic}** `{r.test.name}`: {r.test.description}")
                for fail in r.failures:
                    lines.append(f"  - {fail}")
            lines.append(f"")

    # Write markdown
    md_path = os.path.join(output_dir, "report.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Generate Z8000 verification report")
    parser.add_argument("--port", "-p", required=True, help="Serial port")
    parser.add_argument("--baud", "-b", type=int, default=115200)
    parser.add_argument("--target", default="z8002",
                        choices=["common", "z8001", "z8001-seg", "z8002"])
    parser.add_argument("--output", "-o",
                        help="Output directory (default: results/<target>_<date>)")
    args = parser.parse_args()

    if not args.output:
        args.output = os.path.join(
            "results", f"{args.target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    all_tests = collect_all_tests()
    harness = Z8000TestHarness(args.port, args.baud)
    print(f"Connected to {args.port}")

    print("Uploading bootstrap...", end=" ", flush=True)
    harness.upload_bootstrap(args.target)
    print("done")

    runner = TestRunner(harness, target=args.target, verbose=True)
    results, passed, failed = runner.run_tests(all_tests)

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed (of {passed+failed} run)")

    json_path, md_path = generate_report(results, args.target, args.output)
    print(f"\nReport: {md_path}")
    print(f"Data:   {json_path}")

    harness.close()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
