"""Test runner - executes TestCase instances against the hardware harness."""

import fnmatch
import time

from .defs import TestCase, TestResult
from .helpers import CODE_BASE, JP_DUMP, JP_DUMP_SEG, REG_DUMP_SEG, FCW_DUMP_SEG
from .verify import verify_result


class TestRunner:
    def __init__(self, harness, target="common", verbose=False):
        self.harness = harness
        self.target = target
        self.verbose = verbose

    def run_test(self, tc):
        """Run a single test case and return TestResult."""
        self.harness.init()

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
        jp = JP_DUMP_SEG if self.target == "z8001-seg" else JP_DUMP
        code_with_jp = list(tc.code) + jp
        for i, word in enumerate(code_with_jp):
            self.harness.write_mem(CODE_BASE + i * 2, word)

        # 5. Execute
        exec_result = self.harness.execute()

        # 6. Read back all 16 registers
        actual_regs = {}
        for reg in range(16):
            if self.target == "z8001-seg":
                # Segmented bootstrap dumps registers at 0x0140 instead of 0x0090
                actual_regs[reg] = self.harness.read_mem(REG_DUMP_SEG + reg * 2)
            else:
                actual_regs[reg] = self.harness.read_reg(reg)

        # 7. Read back FCW
        if self.target == "z8001-seg":
            actual_fcw = self.harness.read_mem(FCW_DUMP_SEG)
        else:
            actual_fcw = self.harness.read_fcw()

        # 8. Read back memory requested for verification or golden comparison
        actual_memory = {}
        for addr in sorted(set(tc.expected_memory) | set(tc.observe_memory)):
            actual_memory[addr] = self.harness.read_mem(addr)

        # 9. Read cycle/fetch counts and trace
        cycle_count = self.harness.cycle_count()
        fetch_count = self.harness.fetch_count()
        instr_cycle_count = self.harness.instr_cycle_count()
        trace = self.harness.read_all_trace()

        # 9b. Read I/O port registers (requires reset first)
        actual_io = {}
        io_readback = sorted(set(tc.expected_io) | set(tc.observe_io))
        if io_readback:
            self.harness.reset()
            for idx in io_readback:
                actual_io[idx] = self.harness.read_io_port(idx)

        # 10. Verify
        failures = verify_result(
            tc, exec_result, actual_regs, actual_fcw, actual_memory, actual_io
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
            instr_cycle_count=instr_cycle_count,
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
        # z8001-seg runs: z8001-seg only (different bootstrap layout)
        # z8001 runs:     common + z8001
        # z8002 runs:     common + z8002
        # common runs:    common only
        if self.target == "z8001-seg":
            allowed = {"z8001-seg"}
        else:
            allowed = {"common"}
        if self.target not in ("common", "z8001-seg"):
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
