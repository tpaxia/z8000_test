#!/usr/bin/env python3
"""
Z8000 Instruction Test Harness Control Script

This script communicates with the Z8000 test harness via serial port
to test individual instructions.

Usage:
    python test_harness.py [port] [command...]

Examples:
    python test_harness.py /dev/ttyUSB0           # Interactive mode
    python test_harness.py /dev/ttyUSB0 ST        # Check status
    python test_harness.py /dev/ttyUSB0 test_add  # Run ADD test
"""

import sys
import time
import serial
import argparse

class Z8000TestHarness:
    def __init__(self, port, baud=115200, timeout=1):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.1)  # Wait for port to settle

    def send_command(self, cmd):
        """Send command and return response"""
        self.ser.write((cmd + '\r').encode())
        time.sleep(0.01)
        response = self.ser.readline().decode().strip()
        return response

    def write_reg(self, reg, value):
        """Write register initial value"""
        return self.send_command(f'WR {reg:X} {value:04X}')

    def read_reg(self, reg):
        """Read register final value"""
        resp = self.send_command(f'RR {reg:X}')
        try:
            return int(resp, 16)
        except:
            return None

    def write_mem(self, addr, value):
        """Write word to memory"""
        return self.send_command(f'WM {addr:04X} {value:04X}')

    def read_mem(self, addr):
        """Read word from memory"""
        resp = self.send_command(f'RM {addr:04X}')
        try:
            return int(resp, 16)
        except:
            return None

    def write_fcw(self, value):
        """Write initial FCW"""
        return self.send_command(f'WF {value:04X}')

    def read_fcw(self):
        """Read final FCW"""
        resp = self.send_command('RF')
        try:
            return int(resp, 16)
        except:
            return None

    def execute(self):
        """Execute test and wait for halt"""
        return self.send_command('EX')

    def reset(self):
        """Reset CPU"""
        return self.send_command('RS')

    def status(self):
        """Get status (H=halted, R=running)"""
        return self.send_command('ST')

    def dump_regs(self):
        """Dump all registers"""
        return self.send_command('DA')

    def load_instruction(self, addr, *words):
        """Load instruction word(s) at address"""
        for i, word in enumerate(words):
            self.write_mem(addr + i*2, word)

    def setup_test(self, regs=None, code=None, code_addr=0x0200):
        """
        Setup a test with initial registers and code.

        regs: dict of {reg_num: value}
        code: list of instruction words
        code_addr: address to load code (default 0x0200)
        """
        # Set registers
        if regs:
            for reg, val in regs.items():
                self.write_reg(reg, val)

        # Load code
        if code:
            for i, word in enumerate(code):
                self.write_mem(code_addr + i*2, word)
            # Add jump to dump routine
            dump_addr = code_addr + len(code)*2
            self.write_mem(dump_addr, 0x5E08)      # JP
            self.write_mem(dump_addr + 2, 0x00C0)  # 0x00C0

    def run_test(self, regs=None, code=None, expected_regs=None, expected_flags=None):
        """
        Run a complete test and verify results.

        Returns: (passed, message)
        """
        # Setup
        self.setup_test(regs, code)

        # Execute
        result = self.execute()
        if result != 'HALT':
            return False, f"Execution failed: {result}"

        # Check registers
        if expected_regs:
            for reg, expected in expected_regs.items():
                actual = self.read_reg(reg)
                if actual != expected:
                    return False, f"R{reg} mismatch: expected 0x{expected:04X}, got 0x{actual:04X}"

        # Check flags
        if expected_flags:
            fcw = self.read_fcw()
            for flag, expected in expected_flags.items():
                flag_bits = {'C': 0, 'Z': 1, 'S': 2, 'V': 3, 'DA': 4, 'H': 5}
                bit = flag_bits.get(flag, 0)
                actual = (fcw >> bit) & 1
                if actual != expected:
                    return False, f"Flag {flag} mismatch: expected {expected}, got {actual}"

        return True, "PASSED"

    def close(self):
        self.ser.close()


def test_add(harness):
    """Test ADD R0, R1 instruction"""
    print("Test: ADD R0, R1")
    print("  R0 = 0x1234, R1 = 0x5678")
    print("  Expected: R0 = 0x68AC")

    passed, msg = harness.run_test(
        regs={0: 0x1234, 1: 0x5678},
        code=[0x8100],  # ADD R0, R1
        expected_regs={0: 0x68AC, 1: 0x5678}
    )
    print(f"  Result: {msg}")
    return passed


def test_sub(harness):
    """Test SUB R0, R1 instruction"""
    print("Test: SUB R0, R1")
    print("  R0 = 0x5678, R1 = 0x1234")
    print("  Expected: R0 = 0x4444")

    passed, msg = harness.run_test(
        regs={0: 0x5678, 1: 0x1234},
        code=[0x8300],  # SUB R0, R1
        expected_regs={0: 0x4444, 1: 0x1234}
    )
    print(f"  Result: {msg}")
    return passed


def test_and(harness):
    """Test AND R0, R1 instruction"""
    print("Test: AND R0, R1")
    print("  R0 = 0xFF00, R1 = 0x0F0F")
    print("  Expected: R0 = 0x0F00")

    passed, msg = harness.run_test(
        regs={0: 0xFF00, 1: 0x0F0F},
        code=[0x8700],  # AND R0, R1
        expected_regs={0: 0x0F00, 1: 0x0F0F}
    )
    print(f"  Result: {msg}")
    return passed


def test_or(harness):
    """Test OR R0, R1 instruction"""
    print("Test: OR R0, R1")
    print("  R0 = 0xFF00, R1 = 0x00FF")
    print("  Expected: R0 = 0xFFFF")

    passed, msg = harness.run_test(
        regs={0: 0xFF00, 1: 0x00FF},
        code=[0x8500],  # OR R0, R1
        expected_regs={0: 0xFFFF}
    )
    print(f"  Result: {msg}")
    return passed


def test_xor(harness):
    """Test XOR R0, R1 instruction"""
    print("Test: XOR R0, R1")
    print("  R0 = 0xAAAA, R1 = 0x5555")
    print("  Expected: R0 = 0xFFFF")

    passed, msg = harness.run_test(
        regs={0: 0xAAAA, 1: 0x5555},
        code=[0x8900],  # XOR R0, R1
        expected_regs={0: 0xFFFF}
    )
    print(f"  Result: {msg}")
    return passed


def run_all_tests(harness):
    """Run all built-in tests"""
    tests = [test_add, test_sub, test_and, test_or, test_xor]
    passed = 0
    failed = 0

    print("=" * 50)
    print("Running all tests")
    print("=" * 50)

    for test in tests:
        print()
        if test(harness):
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)


def interactive_mode(harness):
    """Interactive command mode"""
    print("Z8000 Test Harness Interactive Mode")
    print("Commands: ST, RS, WR n xxxx, RR n, WM aaaa xxxx, RM aaaa, EX, DA")
    print("Type 'quit' to exit, 'all' to run all tests")
    print()

    while True:
        try:
            cmd = input("> ").strip()
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'all':
                run_all_tests(harness)
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
            elif cmd.startswith('test_'):
                # Run specific test
                test_func = globals().get(cmd)
                if test_func:
                    test_func(harness)
                else:
                    print(f"Unknown test: {cmd}")
            else:
                # Direct command
                response = harness.send_command(cmd)
                print(response)
        else:
            interactive_mode(harness)

        harness.close()

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
