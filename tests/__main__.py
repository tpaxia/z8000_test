"""CLI for running Z8000 instruction tests.

Usage:
    python -m tests --port /dev/ttyUSB0                     # Run all
    python -m tests --port /dev/ttyUSB0 --tags arithmetic   # By tag
    python -m tests --port /dev/ttyUSB0 --mnemonic ADD      # By mnemonic
    python -m tests --port /dev/ttyUSB0 --name "add_r_*"    # By name glob
    python -m tests --port /dev/ttyUSB0 --target z8002      # Target filter
    python -m tests --port /dev/ttyUSB0 --list               # List without running
    python -m tests --port /dev/ttyUSB0 -v                   # Verbose output

Simulation mode (no hardware needed):
    python -m tests --sim                                    # Run all in simulation
    python -m tests --sim --name "add_r_*" -v                # Single test
    python -m tests --sim --recompile                        # Force recompile

Emulator mode (no hardware or iverilog needed):
    python -m tests --emu                                    # Run all via emulator
    python -m tests --emu --name "add_r_*" -v                # Single test
    python -m tests --emu --recompile                        # Force rebuild driver

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
    parser.add_argument('--port', '-p', default=None,
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', '-b', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    parser.add_argument('--sim', action='store_true',
                        help='Run in simulation mode (iverilog/vvp, no hardware)')
    parser.add_argument('--emu', action='store_true',
                        help='Run via z8000_emu emulator (no hardware or iverilog)')
    parser.add_argument('--recompile', action='store_true',
                        help='Force recompile of simulation testbench or emu driver')
    parser.add_argument('--tags', '-t', nargs='+',
                        help='Filter by tags')
    parser.add_argument('--mnemonic', '-m',
                        help='Filter by mnemonic (e.g. ADD)')
    parser.add_argument('--name', '-n',
                        help='Filter by name pattern (glob)')
    parser.add_argument('--target', default=None,
                        choices=['common', 'z8001', 'z8001-seg', 'z8002'],
                        help='Target CPU (default: common, or z8002 with --sim)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List tests without running')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--save-traces',
                        help='Save bus traces to directory')
    parser.add_argument('--compare-traces',
                        help='Compare against reference traces in directory')

    args = parser.parse_args()

    # --sim and --emu are mutually exclusive
    if args.sim and args.emu:
        parser.error("--sim and --emu are mutually exclusive")

    # --sim/--emu implies z8002 target
    if (args.sim or args.emu) and args.target is None:
        args.target = "z8002"
    elif args.target is None:
        args.target = "common"

    # --port defaults
    if not args.sim and not args.emu and args.port is None:
        args.port = "/dev/ttyUSB0"

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

    if args.sim:
        _run_sim(args, all_tests, filtered)
    elif args.emu:
        _run_emu(args, all_tests, filtered)
    else:
        _run_hardware(args, all_tests, filtered)


def _run_sim(args, all_tests, filtered):
    """Run tests in simulation mode."""
    from .sim_runner import SimRunner

    try:
        runner = SimRunner(target=args.target, verbose=args.verbose)

        print("Compiling simulation...", end=" ", flush=True)
        runner.compile(force=args.recompile)
        print("done")
        print()

        print(f"Running {len(filtered)} tests (simulation)...")
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

        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _run_emu(args, all_tests, filtered):
    """Run tests via z8000_emu emulator."""
    from .emu_runner import EmuRunner

    try:
        runner = EmuRunner(target=args.target, verbose=args.verbose)

        print("Building emulator driver...", end=" ", flush=True)
        runner.compile(force=args.recompile)
        print("done")
        print()

        print(f"Running {len(filtered)} tests (emulator)...")
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

        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _run_hardware(args, all_tests, filtered):
    """Run tests on FPGA hardware via serial."""
    try:
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
