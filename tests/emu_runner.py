"""Emulator runner - executes TestCase instances via z8000_emu C++ driver."""

import fnmatch
import os
import subprocess

from .defs import TestCase, TestResult
from .helpers import CODE_BASE
from .verify import verify_result


class EmuRunner:
    def __init__(self, target="z8002", verbose=False, project_root=None):
        self.target = target
        self.verbose = verbose
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = project_root
        self.driver_path = os.path.join(project_root, "emu", "z8000_test_driver")
        self._tmpdir = os.path.join(project_root, ".emu_tmp")
        os.makedirs(self._tmpdir, exist_ok=True)

    def compile(self, force=False):
        """Build the emulator test driver. Skips if binary exists."""
        if not force and os.path.exists(self.driver_path):
            if self.verbose:
                print(f"  Using cached {self.driver_path}")
            return

        emu_dir = os.path.join(self.project_root, "z8000_emu")

        # Build libz8000.a
        if self.verbose:
            print("  Building libz8000.a...")
        result = subprocess.run(
            ["make", "-C", emu_dir, "libz8000"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"libz8000 build failed:\n{result.stderr}"
            )

        # Compile test driver
        if self.verbose:
            print("  Compiling emu/z8000_test_driver...")
        cxx = os.environ.get("CXX", "c++")
        cmd = [
            cxx, "-std=c++17", "-O2",
            f"-I{os.path.join(emu_dir, 'include')}",
            "-o", self.driver_path,
            os.path.join(self.project_root, "emu", "z8000_test_driver.cpp"),
            f"-L{os.path.join(emu_dir, 'build')}",
            "-lz8000",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Test driver compilation failed:\n{result.stderr}"
            )

    def _write_test_spec(self, tc):
        """Write test spec file, return path."""
        spec_path = os.path.join(self._tmpdir, f"{tc.name}.spec")

        lines = []

        # Code words
        if tc.code:
            words = " ".join(f"{w:04X}" for w in tc.code)
            lines.append(f"CODE:{words}")

        # FCW
        lines.append(f"FCW:{tc.fcw:04X}")

        # Registers
        for reg, val in sorted(tc.regs.items()):
            lines.append(f"REG:{reg}:{val:04X}")

        # Memory preloads
        for addr, val in sorted(tc.memory.items()):
            lines.append(f"MEM:{addr:04X}:{val:04X}")

        # I/O preloads
        for idx, val in sorted(tc.io_preloads.items()):
            lines.append(f"IO:{idx}:{val:04X}")

        # Verify memory addresses (from expected_memory)
        for addr in sorted(tc.expected_memory.keys()):
            lines.append(f"VERIFY_MEM:{addr:04X}")

        # Verify I/O indices (from expected_io)
        for idx in sorted(tc.expected_io.keys()):
            lines.append(f"VERIFY_IO:{idx}")

        lines.append("RUN")

        with open(spec_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        return spec_path

    def _run_driver(self, spec_path):
        """Run the test driver subprocess, return stdout."""
        result = subprocess.run(
            [self.driver_path, spec_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 and "RESULT:" not in result.stdout:
            raise RuntimeError(
                f"Driver failed (rc={result.returncode}):\n{result.stderr}"
            )
        return result.stdout

    @staticmethod
    def _parse_hex(s):
        """Parse hex string, returning None for 'x' values."""
        if 'x' in s or 'X' in s:
            return None
        return int(s, 16)

    def _parse_output(self, stdout):
        """Parse tagged output lines into result dict."""
        result = {
            "exec_result": "TOUT",
            "regs": {},
            "fcw": None,
            "memory": {},
            "io": {},
            "trace": [],
            "cycle_count": 0,
            "fetch_count": 0,
            "instr_cycle_count": None,
        }

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("RESULT:"):
                result["exec_result"] = line.split(":", 1)[1]

            elif line.startswith("REG:"):
                parts = line.split(":")
                reg_num = int(parts[1])
                result["regs"][reg_num] = self._parse_hex(parts[2])

            elif line.startswith("FCW:"):
                result["fcw"] = self._parse_hex(line.split(":", 1)[1])

            elif line.startswith("MEM:"):
                parts = line.split(":")
                addr = self._parse_hex(parts[1])
                val = self._parse_hex(parts[2])
                if addr is not None:
                    result["memory"][addr] = val

            elif line.startswith("IO:"):
                parts = line.split(":")
                idx = self._parse_hex(parts[1])
                val = self._parse_hex(parts[2])
                if idx is not None:
                    result["io"][idx] = val

            elif line.startswith("CYCLES:"):
                v = self._parse_hex(line.split(":", 1)[1])
                result["cycle_count"] = v if v is not None else 0

        return result

    def run_test(self, tc):
        """Run a single test case in the emulator and return TestResult."""
        spec_path = self._write_test_spec(tc)
        stdout = self._run_driver(spec_path)
        parsed = self._parse_output(stdout)

        exec_result = parsed["exec_result"]
        actual_regs = parsed["regs"]
        actual_fcw = parsed["fcw"]

        actual_memory = {}
        for addr in tc.expected_memory:
            actual_memory[addr] = parsed["memory"].get(addr)

        actual_io = {}
        for idx in tc.expected_io:
            actual_io[idx] = parsed["io"].get(idx)

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
            cycle_count=parsed["cycle_count"],
            fetch_count=parsed["fetch_count"],
            instr_cycle_count=parsed["instr_cycle_count"],
            trace=parsed["trace"],
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
        allowed = {"common"}
        if self.target == "z8001-seg":
            allowed |= {"z8001", "z8001-seg"}
        elif self.target != "common":
            allowed.add(self.target)

        filtered = []
        for tc in tests:
            if tc.target not in allowed:
                continue
            if tags and not any(t in tc.tags for t in tags):
                continue
            if mnemonic and tc.mnemonic.upper() != mnemonic.upper():
                continue
            if name_pattern and not fnmatch.fnmatch(tc.name, name_pattern):
                continue
            filtered.append(tc)
        return filtered
