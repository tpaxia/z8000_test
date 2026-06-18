"""CLI for dual-CPU comparison testing.

Capture golden results from Z8001, compare Z8002 against them,
and auto-generate test files from diffs.

Usage:
    # Capture golden from Z8001
    python -m tests.compare --capture --port /dev/ttyUSB0 --golden-dir golden/z8001
    python -m tests.compare --capture --port /dev/ttyUSB0 --golden-dir golden/z8001 --mnemonic ADD

    # Compare Z8002 against golden (hardware)
    python -m tests.compare --port /dev/ttyUSB0 --golden-dir golden/z8001
    python -m tests.compare --port /dev/ttyUSB0 --golden-dir golden/z8001 --mnemonic ADD -v

    # Compare via sim or emu
    python -m tests.compare --sim --golden-dir golden/z8001
    python -m tests.compare --emu --golden-dir golden/z8001

    # Auto-generate test file from diffs
    python -m tests.compare --port /dev/ttyUSB0 --golden-dir golden/z8001 --auto-generate

    # List tests without running
    python -m tests.compare --list
"""

import os
import sys
import argparse
import fnmatch
import json

from .gen_systematic import generate_all_tests
from .gen_segmented import generate_segmented_tests
from .gen_seg_systematic import generate_seg_systematic_tests
from .gen_opcode_coverage import (
    generate_opcode_coverage_tests,
    generate_segmented_opcode_coverage_tests,
)
from . import test_io
from .golden import save_golden, load_golden, compare_golden
from .golden_masks import load_masks, DEFAULT_MASKS_PATH
from .auto_generate import generate_golden_test_file
from .runner import TestRunner


def main():
    parser = argparse.ArgumentParser(
        description='Z8000 Dual-CPU Comparison Test System'
    )
    parser.add_argument('--port', '-p', default=None,
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', '-b', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    parser.add_argument('--sim', action='store_true',
                        help='Run DUT in simulation mode')
    parser.add_argument('--emu', action='store_true',
                        help='Run DUT via emulator')
    parser.add_argument('--recompile', action='store_true',
                        help='Force recompile sim/emu')
    parser.add_argument('--capture', action='store_true',
                        help='Capture golden results from reference CPU')
    parser.add_argument('--golden-dir', default='golden/z8001',
                        help='Directory for golden result files')
    parser.add_argument('--masks', default=DEFAULT_MASKS_PATH,
                        help='Sidecar JSON of per-test undefined-field masks')
    parser.add_argument('--no-masks', action='store_true',
                        help='Disable undefined-field masking (compare every field)')
    parser.add_argument('--auto-generate', action='store_true',
                        help='Auto-generate test file from diffs')
    parser.add_argument('--output', default='tests/test_z8001_golden.py',
                        help='Output file for auto-generated tests')
    parser.add_argument('--save-json', default=None,
                        help='Save comparison results to JSON file')
    parser.add_argument('--save-traces', default=None,
                        help='Save per-test bus traces to a directory')
    parser.add_argument('--mnemonic', '-m', default=None,
                        help='Filter by mnemonic (e.g. ADD)')
    parser.add_argument('--name', '-n', default=None,
                        help='Filter by name pattern (glob)')
    parser.add_argument('--category', default=None,
                        help='Filter by category tag')
    parser.add_argument('--target', default=None,
                        choices=['common', 'z8001', 'z8002', 'z8001-seg'],
                        help='Target CPU type')
    parser.add_argument('--opcode-coverage', action='store_true',
                        help='Add assembler-generated opcode variant coverage tests')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List tests without running')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.sim and args.emu:
        parser.error("--sim and --emu are mutually exclusive")

    # Default target
    if args.target is None:
        args.target = "z8002" if (args.sim or args.emu) else "common"

    # Default port
    if not args.sim and not args.emu and args.port is None:
        args.port = "/dev/ttyUSB0"

    # Generate tests
    all_tests = list(generate_all_tests())
    all_tests.extend(test_io.TESTS)
    if args.opcode_coverage and args.target != "z8001-seg":
        all_tests.extend(generate_opcode_coverage_tests())

    # Add segmented tests when targeting z8001-seg
    if args.target == "z8001-seg":
        seg_tests = generate_segmented_tests()
        seg_sys_tests = generate_seg_systematic_tests()
        all_tests.extend(seg_tests)
        all_tests.extend(seg_sys_tests)
        if args.opcode_coverage:
            all_tests.extend(generate_segmented_opcode_coverage_tests())

    if not all_tests:
        print("No tests generated.")
        sys.exit(1)

    # Apply filters
    filtered = _filter_tests(all_tests, args)

    if args.list:
        _list_tests(filtered, all_tests, args.verbose)
        sys.exit(0)

    if args.capture:
        _run_capture(args, all_tests, filtered)
    else:
        _run_compare(args, all_tests, filtered)


def _filter_tests(tests, args):
    """Filter tests by target, mnemonic, name, and category."""
    filtered = list(tests)

    # Filter by target compatibility
    if args.target == "z8001-seg":
        # Segmented mode: only run tests explicitly targeting z8001-seg
        filtered = [t for t in filtered if t.target == "z8001-seg"]
    elif args.target:
        # Non-segmented: run "common" tests + target-specific tests
        filtered = [t for t in filtered
                     if t.target in ("common", args.target)]

    if args.mnemonic:
        filtered = [t for t in filtered
                     if t.mnemonic.upper() == args.mnemonic.upper()]
    if args.name:
        filtered = [t for t in filtered
                     if fnmatch.fnmatch(t.name, args.name)]
    if args.category:
        filtered = [t for t in filtered
                     if args.category in t.tags]
    return filtered


def _list_tests(filtered, all_tests, verbose):
    """List tests without running."""
    print(f"Systematic tests ({len(filtered)} of {len(all_tests)}):")
    print()

    # Group by mnemonic
    by_mnemonic = {}
    for tc in filtered:
        by_mnemonic.setdefault(tc.mnemonic, []).append(tc)

    for mnem in sorted(by_mnemonic.keys()):
        tcs = by_mnemonic[mnem]
        print(f"  {mnem:<10s} ({len(tcs)} tests)")
        if verbose:
            for tc in tcs:
                tags_str = ', '.join(t for t in tc.tags if t != 'systematic')
                print(f"    {tc.name:<45s} {tags_str}")


def _run_capture(args, all_tests, filtered):
    """Capture golden results from reference CPU."""
    print(f"Capturing golden results to {args.golden_dir}/")
    print(f"Running {len(filtered)} tests...")
    print()

    runner = _make_runner(args, all_tests)

    print("=" * 60)
    results, passed, failed = runner.run_tests(
        all_tests,
        mnemonic=args.mnemonic,
        name_pattern=args.name,
        tags=[args.category] if args.category else None,
    )
    print("=" * 60)
    print(f"Executed: {passed + failed} ({passed} passed, {failed} failed)")

    # Save golden results for all tests (even failed ones - golden captures
    # the actual behavior of the reference CPU)
    count = save_golden(results, args.golden_dir)
    print(f"Saved {count} golden results to {args.golden_dir}/")

    # Save bus traces
    if args.save_traces:
        from .traces import save_traces
        n = save_traces(results, args.save_traces)
        print(f"Saved {n} traces to {args.save_traces}/")

    sys.exit(0)


def _run_compare(args, all_tests, filtered):
    """Compare DUT against golden results."""
    # Load golden
    golden = load_golden(args.golden_dir)
    if not golden:
        print(f"No golden results found in {args.golden_dir}/")
        print("Run with --capture first to generate golden reference.")
        sys.exit(1)

    # Count how many of our filtered tests have golden data
    have_golden = [t for t in filtered if t.name in golden]
    missing = len(filtered) - len(have_golden)

    print(f"Loaded {len(golden)} golden results from {args.golden_dir}/")
    if missing > 0:
        print(f"  ({missing} tests have no golden reference)")
    print(f"Running {len(filtered)} tests...")
    print()

    runner = _make_runner(args, all_tests)

    print("=" * 60)
    results, passed, failed = runner.run_tests(
        all_tests,
        mnemonic=args.mnemonic,
        name_pattern=args.name,
        tags=[args.category] if args.category else None,
    )
    print("=" * 60)

    # Compare against golden (masking architecturally-undefined fields)
    masks = None if args.no_masks else load_masks(args.masks)
    comparisons = compare_golden(results, golden, masks=masks)
    matches = sum(1 for c in comparisons if c.match)
    diffs = [c for c in comparisons if not c.match]
    no_ref = sum(1 for c in comparisons
                  if not c.match and len(c.diffs) == 1
                  and c.diffs[0].field == "golden")
    ignored = sum(1 for c in comparisons if c.match and c.masked_diffs)

    print()
    extra = f", {ignored} with undefined fields ignored" if ignored else ""
    print(f"Golden comparison: {matches} match{extra}, {len(diffs)} differ"
          f" ({no_ref} missing reference)")

    if diffs and args.verbose:
        print()
        # Group diffs by mnemonic
        tc_map = {tc.name: tc for tc in all_tests}
        by_mnemonic = {}
        for c in diffs:
            tc = tc_map.get(c.test_name)
            mnem = tc.mnemonic if tc else "?"
            by_mnemonic.setdefault(mnem, []).append(c)

        for mnem in sorted(by_mnemonic.keys()):
            comps = by_mnemonic[mnem]
            print(f"  {mnem}:")
            for c in comps:
                print(f"    {c.test_name}:")
                for d in c.diffs:
                    tag = "  [undefined, ignored]" if d.masked else ""
                    print(f"      {d.description}{tag}")

    if ignored and args.verbose:
        print()
        print("Undefined fields ignored (counted as match):")
        for c in comparisons:
            if c.match and c.masked_diffs:
                print(f"  {c.test_name}:")
                for d in c.masked_diffs:
                    print(f"      {d.description}")
                    print(f"        -> {d.reason}")

    if diffs and not args.verbose:
        # Brief summary
        print()
        tc_map = {tc.name: tc for tc in all_tests}
        by_mnemonic = {}
        for c in diffs:
            tc = tc_map.get(c.test_name)
            mnem = tc.mnemonic if tc else "?"
            by_mnemonic.setdefault(mnem, []).append(c)

        print("Differing mnemonics:")
        for mnem in sorted(by_mnemonic.keys()):
            comps = by_mnemonic[mnem]
            print(f"  {mnem}: {len(comps)} tests differ")

    # Save JSON
    if args.save_json:
        _save_comparison_json(comparisons, all_tests, args.save_json)
        print(f"\nSaved comparison results to {args.save_json}")

    # Save bus traces
    if args.save_traces:
        from .traces import save_traces
        n = save_traces(results, args.save_traces)
        print(f"Saved {n} traces to {args.save_traces}/")

    # Auto-generate test file
    real_diffs = [c for c in diffs
                   if not (len(c.diffs) == 1 and c.diffs[0].field == "golden")]
    if args.auto_generate and real_diffs:
        count = generate_golden_test_file(
            real_diffs, golden, all_tests, args.output
        )
        print(f"\nGenerated {count} test cases in {args.output}")
    elif args.auto_generate:
        print("\nNo diffs to generate tests from.")

    sys.exit(0 if not real_diffs else 1)


def _make_runner(args, all_tests):
    """Create a TestRunner for the appropriate backend."""
    if args.sim:
        from .sim_runner import SimRunner
        runner = SimRunner(target=args.target, verbose=args.verbose)
        print("Compiling simulation...", end=" ", flush=True)
        runner.compile(force=args.recompile)
        print("done")
        return runner
    elif args.emu:
        from .emu_runner import EmuRunner
        runner = EmuRunner(target=args.target, verbose=args.verbose)
        print("Building emulator driver...", end=" ", flush=True)
        runner.compile(force=args.recompile)
        print("done")
        return runner
    else:
        from .harness import Z8000TestHarness
        harness = Z8000TestHarness(args.port, args.baud)
        print(f"Connected to {args.port}")
        print("Uploading bootstrap...", end=" ", flush=True)
        harness.upload_bootstrap(args.target)
        print("done")
        return TestRunner(harness, target=args.target, verbose=args.verbose)


def _save_comparison_json(comparisons, all_tests, path):
    """Save comparison results as JSON."""
    tc_map = {tc.name: tc for tc in all_tests}
    data = []
    for c in comparisons:
        tc = tc_map.get(c.test_name)
        entry = {
            "test": c.test_name,
            "mnemonic": tc.mnemonic if tc else "?",
            "match": c.match,
            "diffs": [
                {
                    "field": d.field,
                    "ref": d.ref_value,
                    "dut": d.dut_value,
                    "description": d.description,
                    "masked": d.masked,
                    "reason": d.reason,
                }
                for d in c.diffs
            ],
        }
        data.append(entry)

    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':
    main()
