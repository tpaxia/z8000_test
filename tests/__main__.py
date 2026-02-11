"""CLI for running Z8000 instruction tests.

Usage:
    python -m tests --port /dev/ttyUSB0                     # Run all
    python -m tests --port /dev/ttyUSB0 --tags arithmetic   # By tag
    python -m tests --port /dev/ttyUSB0 --mnemonic ADD      # By mnemonic
    python -m tests --port /dev/ttyUSB0 --name "add_r_*"    # By name glob
    python -m tests --port /dev/ttyUSB0 --target z8002      # Target filter
    python -m tests --port /dev/ttyUSB0 --list               # List without running
    python -m tests --port /dev/ttyUSB0 -v                   # Verbose output

Trace capture and comparison:
    python -m tests -p /dev/ttyUSB0 --save-traces traces/z8002
    python -m tests -p /dev/ttyUSB0 --save-traces traces/z8001 --compare-traces traces/z8002
"""

import os
import sys
import argparse
import fnmatch

from . import collect_all_tests
from .runner import TestRunner


def main():
    parser = argparse.ArgumentParser(
        description='Z8000 Systematic Instruction Tests'
    )
    parser.add_argument('--port', '-p', default='/dev/ttyUSB0',
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', '-b', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    parser.add_argument('--tags', '-t', nargs='+',
                        help='Filter by tags')
    parser.add_argument('--mnemonic', '-m',
                        help='Filter by mnemonic (e.g. ADD)')
    parser.add_argument('--name', '-n',
                        help='Filter by name pattern (glob)')
    parser.add_argument('--target', default='common',
                        choices=['common', 'z8001', 'z8001-seg', 'z8002'],
                        help='Target CPU (default: common)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List tests without running')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--save-traces',
                        help='Save bus traces to directory')
    parser.add_argument('--compare-traces',
                        help='Compare against reference traces in directory')

    args = parser.parse_args()

    # Collect all tests
    all_tests = collect_all_tests()

    if not all_tests:
        print("No tests found.")
        sys.exit(1)

    # Pre-filter for listing
    allowed = {"common"}
    if args.target == "z8001-seg":
        allowed |= {"z8001", "z8001-seg"}
    elif args.target != "common":
        allowed.add(args.target)
    filtered = [t for t in all_tests if t.target in allowed]
    if args.tags:
        filtered = [t for t in filtered
                     if any(tag in t.tags for tag in args.tags)]
    if args.mnemonic:
        filtered = [t for t in filtered
                     if t.mnemonic.upper() == args.mnemonic.upper()]
    if args.name:
        filtered = [t for t in filtered
                     if fnmatch.fnmatch(t.name, args.name)]

    if args.list:
        print(f"Tests ({len(filtered)} of {len(all_tests)}):")
        print()
        for tc in filtered:
            tags_str = ', '.join(tc.tags)
            target_str = f" [{tc.target}]" if tc.target != "common" else ""
            print(f"  {tc.name:<35s} {tc.mnemonic:<8s} {tags_str}{target_str}")
            if args.verbose:
                print(f"    {tc.description}")
        sys.exit(0)

    # Connect and run
    try:
        # Import here so --list works without serial
        from .harness import Z8000TestHarness

        harness = Z8000TestHarness(args.port, args.baud)
        print(f"Connected to {args.port}")

        print("Uploading bootstrap...", end=" ", flush=True)
        harness.upload_bootstrap(args.target)
        print("done")
        print()

        runner = TestRunner(harness, target=args.target, verbose=args.verbose)

        print(f"Running {len(filtered)} tests...")
        print("=" * 60)

        results, passed, failed = runner.run_tests(
            all_tests,
            tags=args.tags,
            mnemonic=args.mnemonic,
            name_pattern=args.name,
        )

        print("=" * 60)
        print(f"Results: {passed} passed, {failed} failed "
              f"(of {passed + failed} run)")

        if failed > 0:
            print()
            print("Failed tests:")
            for r in results:
                if not r.passed:
                    print(f"  {r.test.name}: {', '.join(r.failures)}")

        # Save traces
        if args.save_traces:
            from .traces import save_traces
            n = save_traces(results, args.save_traces)
            print(f"\nSaved {n} traces to {args.save_traces}/")

        # Compare against reference traces
        if args.compare_traces:
            from .traces import load_traces, compare_traces

            ref = load_traces(args.compare_traces)
            if not ref:
                print(f"\nNo traces found in {args.compare_traces}/")
                sys.exit(1)

            comparisons = compare_traces(results, ref)
            mismatches = [(n, d) for n, d in comparisons if d]
            matched = len(comparisons) - len(mismatches)

            print(f"\nTrace comparison vs {args.compare_traces}: "
                  f"{matched} match, {len(mismatches)} differ")
            for name, diffs in mismatches:
                print(f"  {name}:")
                for d in diffs:
                    print(f"    {d}")

        harness.close()
        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
