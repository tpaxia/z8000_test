#!/usr/bin/env python3
"""
Z8000 Test Harness - Interactive control and quick tests.

Usage:
    python test_harness.py [port] [command...]

Examples:
    python test_harness.py /dev/ttyUSB0           # Interactive mode
    python test_harness.py /dev/ttyUSB0 ST        # Send command
    python test_harness.py /dev/ttyUSB0 all       # Run all tests
"""

import sys
import argparse

# Re-export for backwards compatibility
from tests.harness import Z8000TestHarness


def print_help():
    """Print help for all commands"""
    help_text = """
Z8000 Test Harness Commands
===========================

Status & Control:
  ST            Status - returns H (halted/reset) or R (running)
  RS            Reset - assert Z8000 reset, returns OK
  EX            Execute - release reset, run until halt
                Returns: HALT (success), TOUT (timeout), NRST (didn't start)
  INIT          Initialize - set up reset vectors and clear registers
                Sets FCW=0x4000, PC=0x0200, clears R0-R15
  TOxxxx        Set execution timeout (0000=max ~126ms, default)
  CC            Read cycle count (Z8000 clocks from reset to halt)
  FC            Read fetch count (opcode fetches executed)

Register Access (active when Z8000 in reset):
  WRnxxxx       Write register Rn with value xxxx (hex, no spaces)
                Example: WR01234 - write 0x1234 to R0
  RRn           Read register Rn, returns 4 hex digits (no spaces)
                Example: RR0 - read R0
  DA            Dump All - show R0-R15 values

Memory Access (active when Z8000 in reset):
  WMaaaaxxxx    Write word xxxx to address aaaa (hex, no spaces)
                Example: WM02005A5A - write 0x5A5A to 0x0200
  RMaaaa        Read word from address aaaa, returns 4 hex digits (no spaces)
                Example: RM0200 - read from 0x0200
  MT            Memory Test - write/read test patterns
                Returns PASS or FAIL

Debug:
  DB            Toggle debug mode (DB=0 off, DB=1 on)
                When on, commands show internal state
  DP            Dump Ports - show all I/O port values

Local Commands:
  help          Show this help
  all           Run all tests (via tests/ framework)
  raw CMD       Debug: show raw bytes received for CMD
  quit          Exit interactive mode
"""
    print(help_text)


def run_all_tests(harness):
    """Run all tests using the new framework."""
    from tests import collect_all_tests
    from tests.runner import TestRunner

    all_tests = collect_all_tests()
    runner = TestRunner(harness, verbose=True)

    print("=" * 60)
    print(f"Running {len(all_tests)} tests")
    print("=" * 60)

    results, passed, failed = runner.run_tests(all_tests)

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)


def interactive_mode(harness):
    """Interactive command mode"""
    print("Z8000 Test Harness Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit")
    print()

    while True:
        try:
            cmd = input("> ").strip()
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'help':
                print_help()
            elif cmd.lower() == 'all':
                run_all_tests(harness)
            elif cmd.lower().startswith('raw '):
                harness.debug_raw(cmd[4:])
            elif cmd:
                response = harness.send_command(cmd)
                print(response)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Z8000 Test Harness Control')
    parser.add_argument('port', nargs='?', default='/dev/ttyUSB0',
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('command', nargs='*',
                        help='Command to execute (or test name)')
    parser.add_argument('-b', '--baud', type=int, default=115200,
                        help='Baud rate (default: 115200)')

    args = parser.parse_args()

    try:
        harness = Z8000TestHarness(args.port, args.baud)
        print(f"Connected to {args.port}")

        if args.command:
            cmd = ' '.join(args.command)
            if cmd == 'all':
                run_all_tests(harness)
            else:
                response = harness.send_command(cmd)
                print(response)
        else:
            interactive_mode(harness)

        harness.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
