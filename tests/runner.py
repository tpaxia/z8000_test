"""Test runner - executes TestCase instances against the hardware harness."""

import fnmatch
import time

from .defs import TestCase, TestResult
from .flags import FLAG_BITS, get_flag, format_flags
from .helpers import CODE_BASE, JP_DUMP


class TestRunner:
    def __init__(self, harness, target="common", verbose=False):
        self.harness = harness
        self.target = target
        self.verbose = verbose

    def run_test(self, tc):
        """Run a single test case and return TestResult."""
        self.harness.init()

        failures = []

        # 1. Reset and set up FCW
        self.harness.write_fcw(tc.fcw)

        # 2. Set initial registers
        for reg, val in tc.regs.items():
            self.harness.write_reg(reg, val)

        # 3. Preload test memory
        for addr, val in tc.memory.items():
            self.harness.write_mem(addr, val)

        # 3b. Preload I/O port registers
        for idx, val in tc.io_preloads.items():
            self.harness.write_io_port(idx, val)

        # 4. Load test code at CODE_BASE + append JP dump_routine
        code_with_jp = list(tc.code) + JP_DUMP
        for i, word in enumerate(code_with_jp):
            self.harness.write_mem(CODE_BASE + i * 2, word)

        # 5. Execute
        exec_result = self.harness.execute()

        # 6. Check execution result
        if exec_result != tc.expected_result:
            failures.append(
                f"Execution: expected {tc.expected_result}, got {exec_result}"
            )

        # 7. Read back registers
        actual_regs = {}
        for reg in set(list(tc.expected_regs.keys()) + list(tc.regs.keys())):
            actual_regs[reg] = self.harness.read_reg(reg)

        # 8. Read back FCW
        actual_fcw = self.harness.read_fcw()

        # 9. Read back memory
        actual_memory = {}
        for addr in tc.expected_memory:
            actual_memory[addr] = self.harness.read_mem(addr)

        # 10. Read cycle/fetch counts and trace
        cycle_count = self.harness.cycle_count()
        fetch_count = self.harness.fetch_count()
        trace = self.harness.read_all_trace()

        # 10b. Read I/O port registers (requires reset first)
        actual_io = {}
        if tc.expected_io:
            self.harness.reset()
            for idx in tc.expected_io:
                actual_io[idx] = self.harness.read_io_port(idx)

        # 11. Verify registers
        for reg, expected in tc.expected_regs.items():
            actual = actual_regs.get(reg)
            if actual != expected:
                failures.append(
                    f"R{reg}: expected 0x{expected:04X}, got "
                    f"0x{actual:04X}" if actual is not None else "None"
                )

        # 12. Verify flags
        if actual_fcw is not None:
            for flag_name in tc.expected_fcw_set:
                if get_flag(actual_fcw, flag_name) != 1:
                    failures.append(
                        f"Flag {flag_name}: expected SET, got CLEAR "
                        f"(FCW=0x{actual_fcw:04X} {format_flags(actual_fcw)})"
                    )
            for flag_name in tc.expected_fcw_clear:
                if get_flag(actual_fcw, flag_name) != 0:
                    failures.append(
                        f"Flag {flag_name}: expected CLEAR, got SET "
                        f"(FCW=0x{actual_fcw:04X} {format_flags(actual_fcw)})"
                    )

        # 13. Verify memory
        for addr, expected in tc.expected_memory.items():
            actual = actual_memory.get(addr)
            if actual != expected:
                failures.append(
                    f"Mem[0x{addr:04X}]: expected 0x{expected:04X}, got "
                    f"0x{actual:04X}" if actual is not None else "None"
                )

        # 14. Verify I/O ports
        for idx, expected in tc.expected_io.items():
            actual = actual_io.get(idx)
            if actual != expected:
                failures.append(
                    f"IO[0x{idx:02X}]: expected 0x{expected:04X}, got "
                    f"0x{actual:04X}" if actual is not None else "None"
                )

        passed = len(failures) == 0
        return TestResult(
            test=tc,
            passed=passed,
            exec_result=exec_result,
            failures=failures,
            actual_regs=actual_regs,
            actual_fcw=actual_fcw,
            actual_memory=actual_memory,
            actual_io=actual_io,
            cycle_count=cycle_count,
            fetch_count=fetch_count,
            trace=trace,
        )

    def run_tests(self, tests, tags=None, mnemonic=None, name_pattern=None):
        """Run a filtered set of tests and return results."""
        filtered = self._filter_tests(tests, tags, mnemonic, name_pattern)

        results = []
        passed = 0
        failed = 0

        for tc in filtered:
            if self.verbose:
                print(f"  Running: {tc.name} - {tc.description}")

            result = self.run_test(tc)
            results.append(result)

            if result.passed:
                passed += 1
                if self.verbose:
                    print(f"    PASS ({result.cycle_count} cycles)")
            else:
                failed += 1
                print(f"  FAIL: {tc.name} - {tc.description}")
                for f in result.failures:
                    print(f"    {f}")

        return results, passed, failed

    def _filter_tests(self, tests, tags=None, mnemonic=None, name_pattern=None):
        """Filter tests by target, tags, mnemonic, and name pattern."""
        # Build set of test targets that match the runner target.
        # z8001-seg runs: common + z8001 + z8001-seg
        # z8001 runs:     common + z8001
        # z8002 runs:     common + z8002
        # common runs:    common only
        allowed = {"common"}
        if self.target == "z8001-seg":
            allowed |= {"z8001", "z8001-seg"}
        elif self.target != "common":
            allowed.add(self.target)

        filtered = []
        for tc in tests:
            # Target filter
            if tc.target not in allowed:
                continue

            # Tag filter
            if tags:
                if not any(t in tc.tags for t in tags):
                    continue

            # Mnemonic filter
            if mnemonic:
                if tc.mnemonic.upper() != mnemonic.upper():
                    continue

            # Name pattern filter (glob)
            if name_pattern:
                if not fnmatch.fnmatch(tc.name, name_pattern):
                    continue

            filtered.append(tc)
        return filtered
