"""QEMU runner - executes TestCase instances on qemu-system-z8000.

The QEMU Z8000 target lives in https://github.com/tpaxia/qemu (branch
``zeus``).  Its ``z8000-test`` machine loads a memory image, starts from a
given FCW, PC and register set, runs to HALT and writes the final state to a
dump file; ``io-model=z8ktest`` gives it this harness's twelve port
registers.  Each test is one QEMU process.

The binary is taken from ``--qemu-bin`` or ``$Z8K_QEMU``.
"""

import os
import shutil
import struct
import subprocess
import tempfile

from .emu_runner import EmuRunner
from .helpers import CODE_BASE

DUMP_ROUTINE = 0x00C0
HALT_OPCODE = 0x7A00
TIMEOUT_S = 10


class QemuRunner(EmuRunner):
    def __init__(self, target="z8002", verbose=False, project_root=None,
                 qemu_bin=None):
        super().__init__(target=target, verbose=verbose,
                         project_root=project_root)
        self.qemu_bin = qemu_bin or os.environ.get("Z8K_QEMU")
        self.segmented = target == "z8001-seg"
        self._tmpdir = tempfile.mkdtemp(prefix="z8k_qemu_")

    def compile(self, force=False):
        """Nothing to build; check that the binary exists."""
        if not self.qemu_bin:
            raise RuntimeError(
                "QEMU binary not given: use --qemu-bin or set Z8K_QEMU")
        if not (os.path.isfile(self.qemu_bin)
                and os.access(self.qemu_bin, os.X_OK)):
            raise RuntimeError(f"QEMU binary not found: {self.qemu_bin}")

    def close(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # -- address mapping, as in emu/z8000_test_driver.cpp ------------------

    def _xlat(self, flat):
        """Flat harness address -> emulator address.

        Z8002: identity.  Z8001: 4 KiB of each of segments 0 and 1, the
        mapping the FPGA harness gives its block RAM.
        """
        if self.segmented:
            return ((flat >> 12) << 16) | (flat & 0x0FFF)
        return flat

    @property
    def _ram_size(self):
        return 0x20000 if self.segmented else 0x10000

    # -- EmuRunner hooks -----------------------------------------------------

    def _write_test_spec(self, tc):
        """Write the memory image and start-state file; return the test."""
        ram = bytearray(self._ram_size)

        def put(flat_or_addr, value, translate=True):
            addr = self._xlat(flat_or_addr) if translate else flat_or_addr
            # word writes are word-aligned, as on the harness memory
            addr &= (self._ram_size - 1) & ~1
            ram[addr] = (value >> 8) & 0xFF
            ram[addr + 1] = value & 0xFF

        put(DUMP_ROUTINE, HALT_OPCODE)
        base = self._xlat(CODE_BASE)
        for i, word in enumerate(tc.code or []):
            put(base + 2 * i, word, translate=False)
        put(base + 2 * len(tc.code or []), HALT_OPCODE, translate=False)
        for addr, val in sorted(tc.memory.items()):
            put(addr, val)

        # The hardware bootstrap enters the test through a long-form jump,
        # which leaves bit 15 of the PC segment word set; QEMU carries that
        # bit as bit 23 of the PC.
        pc = base | (0x800000 if self.segmented else 0)
        lines = [f"pc {pc:x}", f"fcw {tc.fcw:x}"]
        for reg, val in sorted(tc.regs.items()):
            lines.append(f"reg {reg} {val & 0xFFFF:x}")
        for idx, val in sorted(tc.io_preloads.items()):
            lines.append(f"io {idx} {val & 0xFFFF:x}")
        for idx, values in sorted(tc.io_sequences.items()):
            for slot, val in enumerate(values[:4]):
                lines.append(f"ioseq {idx} {slot} {val & 0xFFFF:x}")

        with open(os.path.join(self._tmpdir, "image.bin"), "wb") as f:
            f.write(ram)
        with open(os.path.join(self._tmpdir, "init.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
        return tc

    def _run_driver(self, tc):
        """Run QEMU; return results in the emulator driver's tagged format."""
        image = os.path.join(self._tmpdir, "image.bin")
        init = os.path.join(self._tmpdir, "init.txt")
        dump = os.path.join(self._tmpdir, "dump.bin")
        if os.path.exists(dump):
            os.unlink(dump)
        machine = (f"z8000-test,io-model=z8ktest,ram-size={self._ram_size},"
                   f"dump-size={self._ram_size},init={init},dump={dump}")
        cmd = [self.qemu_bin, "-M", machine,
               "-cpu", "z8001" if self.segmented else "z8002",
               "-bios", image,
               "-display", "none", "-monitor", "none", "-serial", "none"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return "RESULT:TOUT\n"
        if proc.returncode != 0 or not os.path.exists(dump):
            raise RuntimeError(
                f"QEMU failed (rc={proc.returncode}):\n{proc.stderr}")

        with open(dump, "rb") as f:
            data = f.read()
        if data[:4] != b"Z8KT":
            raise RuntimeError("unexpected dump format from QEMU")
        # 16 registers, PC (2 words), FCW, PSAPSEG, PSAPOFF, REFRESH,
        # NSPSEG, NSPOFF, 12 port registers, port-write log, RAM
        words = struct.unpack(">36H", data[4:76])
        regs, fcw, io = words[:16], words[18], words[24:36]
        nlog = struct.unpack(">I", data[76:80])[0]
        ram = data[80 + 6 * nlog:]

        out = ["RESULT:HALT"]
        out += [f"REG:{i}:{regs[i]:04X}" for i in range(16)]
        out.append(f"FCW:{fcw:04X}")
        for flat in sorted(set(tc.expected_memory) | set(tc.observe_memory)):
            addr = self._xlat(flat) & (self._ram_size - 1) & ~1
            out.append(f"MEM:{flat:04X}:{(ram[addr] << 8) | ram[addr + 1]:04X}")
        for idx in sorted(set(tc.expected_io) | set(tc.observe_io)):
            if 0 <= idx < 12:
                out.append(f"IO:{idx:02X}:{io[idx]:04X}")
        out.append("CYCLES:00000000")
        return "\n".join(out) + "\n"
