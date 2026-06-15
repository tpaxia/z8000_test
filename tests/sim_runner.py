"""Simulation runner - executes TestCase instances via iverilog/vvp."""

import fnmatch
import os
import struct
import subprocess
import tempfile

from .defs import TestCase, TestResult
from .helpers import (
    CODE_BASE, JP_DUMP, JP_DUMP_SEG, REG_SETUP, FCW_SETUP, FCW_DUMP,
    REG_DUMP, DUMP_ROUTINE,
)
from .verify import verify_result


class SimRunner:
    def __init__(self, target="z8002", verbose=False, project_root=None):
        self.target = target
        self.verbose = verbose
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = project_root
        if target == "z8001-seg":
            self.vvp_path = os.path.join(project_root, "z8001_sim_tb.vvp")
        else:
            self.vvp_path = os.path.join(project_root, "z8000_sim_tb.vvp")
        self._tmpdir = os.path.join(project_root, ".sim_tmp")
        os.makedirs(self._tmpdir, exist_ok=True)

    def compile(self, force=False):
        """Compile the simulation testbench with iverilog. Skips if .vvp exists."""
        if not force and os.path.exists(self.vvp_path):
            if self.verbose:
                print(f"  Using cached {self.vvp_path}")
            return

        src = self.project_root
        z8k_rtl = os.path.join(src, "z8000_micro", "rtl")

        srcs = [
            os.path.join(src, "src", "z8000_sim_tb.v"),
            os.path.join(src, "src", "z8001_bus_fpga.v"),
            os.path.join(src, "src", "ram16.v"),
            os.path.join(src, "src", "z8k_io_ports.v"),
            os.path.join(src, "src", "trace_buffer.v"),
            os.path.join(z8k_rtl, "z8000_cpu.v"),
            os.path.join(z8k_rtl, "z8000_biu.v"),
            os.path.join(z8k_rtl, "z8000_muldiv.v"),
            os.path.join(z8k_rtl, "microcode_rom.v"),
            os.path.join(z8k_rtl, "decode_rom.v"),
        ]

        defines = ["-DSIMULATION"]
        if self.target == "z8001-seg":
            defines.append("-DZ8001_MODE")

        cmd = [
            "iverilog", "-g2012",
            f"-I{z8k_rtl}",
            "-o", self.vvp_path,
        ] + defines + srcs

        if self.verbose:
            print(f"  Compiling: iverilog -> {self.vvp_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"iverilog compilation failed:\n{result.stderr}"
            )

    def _load_bootstrap(self):
        """Load and return the bootstrap binary with target-appropriate reset vectors."""
        if self.target == "z8001-seg":
            bin_path = os.path.join(self.project_root, "src", "bootstrap_seg.bin")
        else:
            bin_path = os.path.join(self.project_root, "src", "bootstrap.bin")
        with open(bin_path, "rb") as f:
            data = f.read()

        body = data[16:]  # 0x0010 onwards

        if self.target == "z8001-seg":
            # Z8001 segmented: FCW=0xC000, PC=seg 0, offset 0x0040
            vectors = struct.pack(">8H", 0x0000, 0xC000, 0x0000, 0x0040, 0, 0, 0, 0)
        else:
            # Z8002 non-segmented: FCW=0x4000, PC=0x0040
            vectors = struct.pack(">8H", 0x0000, 0x4000, 0x0040, 0, 0, 0, 0, 0)
        return vectors + body

    def _build_memory_image(self, tc):
        """Build BRAM hex files for a test case.

        Returns dict with paths: {bram_hi, bram_lo, io_preload (if needed)}.
        """
        # Start with 16384-word memory (32KB), all zeros.
        mem_hi = [0] * 16384
        mem_lo = [0] * 16384

        # Load bootstrap
        bootstrap = self._load_bootstrap()
        for i in range(0, len(bootstrap), 2):
            word_addr = i // 2
            if word_addr < len(mem_hi):
                mem_hi[word_addr] = bootstrap[i]
                mem_lo[word_addr] = bootstrap[i + 1]

        def write_word(byte_addr, value):
            wa = byte_addr // 2
            if wa < len(mem_hi):
                mem_hi[wa] = (value >> 8) & 0xFF
                mem_lo[wa] = value & 0xFF

        # Set FCW in reset vector (0x0002) — already set by bootstrap to 0x4000
        # Override if test uses different FCW
        write_word(0x0002, tc.fcw)

        # Write FCW to setup area (0x0030) — bootstrap loads this with ldctl
        write_word(FCW_SETUP, tc.fcw)

        # Write initial register values to register setup area (0x0010-0x002F)
        for reg, val in tc.regs.items():
            write_word(REG_SETUP + reg * 2, val)

        # Preload test memory
        for addr, val in tc.memory.items():
            write_word(addr, val)

        # Load test code at CODE_BASE + append JP dump_routine
        jp = JP_DUMP_SEG if self.target == "z8001-seg" else JP_DUMP
        code_with_jp = list(tc.code) + jp
        for i, word in enumerate(code_with_jp):
            write_word(CODE_BASE + i * 2, word)

        # Write hex files
        hi_path = os.path.join(self._tmpdir, "bram_hi.hex")
        lo_path = os.path.join(self._tmpdir, "bram_lo.hex")

        with open(hi_path, 'w') as f:
            for b in mem_hi:
                f.write(f"{b:02x}\n")

        with open(lo_path, 'w') as f:
            for b in mem_lo:
                f.write(f"{b:02x}\n")

        paths = {"bram_hi": hi_path, "bram_lo": lo_path}

        # I/O preloads
        if tc.io_preloads:
            io_path = os.path.join(self._tmpdir, "io_preload.hex")
            with open(io_path, 'w') as f:
                for i in range(12):
                    val = tc.io_preloads.get(i, 0)
                    f.write(f"{val:04x}\n")
            paths["io_preload"] = io_path

        return paths

    def _run_vvp(self, paths):
        """Run vvp with plusargs, return stdout."""
        cmd = [
            "vvp", self.vvp_path,
            f"+bram_hi={paths['bram_hi']}",
            f"+bram_lo={paths['bram_lo']}",
        ]
        if "io_preload" in paths:
            cmd.append(f"+io_preload={paths['io_preload']}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 and "DONE" not in result.stdout:
            raise RuntimeError(
                f"vvp failed (rc={result.returncode}):\n{result.stderr}"
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

            elif line.startswith("FETCHES:"):
                v = self._parse_hex(line.split(":", 1)[1])
                result["fetch_count"] = v if v is not None else 0

            elif line.startswith("INSTR_CYCLES:"):
                v = self._parse_hex(line.split(":", 1)[1])
                result["instr_cycle_count"] = v

            elif line.startswith("TRACE:"):
                parts = line.split(":")
                result["trace"].append({
                    "index": self._parse_hex(parts[1]) or 0,
                    "addr": self._parse_hex(parts[2]) or 0,
                    "data": self._parse_hex(parts[3]) or 0,
                    "rw": parts[4],
                    "bw": parts[5],
                    "io": parts[6],
                })

        return result

    def run_test(self, tc):
        """Run a single test case in simulation and return TestResult."""
        paths = self._build_memory_image(tc)
        stdout = self._run_vvp(paths)
        parsed = self._parse_output(stdout)

        exec_result = parsed["exec_result"]
        actual_regs = parsed["regs"]
        actual_fcw = parsed["fcw"]

        # Only include memory addresses we need to verify
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
        if self.target == "z8001-seg":
            allowed = {"z8001-seg"}
        else:
            allowed = {"common"}
        if self.target not in ("common", "z8001-seg"):
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
