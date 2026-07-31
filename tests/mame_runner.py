"""MAME runner - executes TestCase instances against MAME's Z8000 core.

MAME hosts the `z8ktest01`/`z8ktest02` machines, which model the Quartus
z8001_ext_test FPGA rig: a Z80 supervisor sharing a dual-port BRAM with the
Z8000 under test, driven by the same firmware and the same ASCII command
protocol as the real hardware. Because the rig is reproduced rather than
reimplemented, this backend reuses TestRunner unchanged - the bootstrap, the
register dump area, the JP-to-dump convention, HALT/TOUT detection and the
I/O port model all come from the firmware, exactly as they do on silicon.

The only thing that differs from the hardware path is the transport: the
machine's UART is a host socket instead of a serial line, so the pacing
delays pyserial needs are dropped.

Requires a MAME build carrying src/mame/zilog/z8ktest.cpp. Point at it with
    export Z8K_MAME_DIR=/path/to/mame
otherwise ~/Projects/mame_latest/mame is assumed.

Usage:
    python -m tests.compare --mame --golden-dir golden/z8001
    python -m tests.compare --mame --target z8001-seg --golden-dir golden/z8001-seg
"""

import os
import socket
import subprocess
import time

from .harness import Z8000TestHarness
from .runner import TestRunner

DEFAULT_MAME_DIR = os.path.expanduser("~/Projects/mame_latest/mame")
DEFAULT_PORT = 5800

# The Z8001 machine covers both the non-segmented and segmented targets; the
# distinction is an FCW bit applied by the bootstrap, not a different CPU.
MACHINE_FOR_TARGET = {
    "z8002": "z8ktest02",
    "z8001": "z8ktest01",
    "z8001-seg": "z8ktest01",
    "common": "z8ktest02",
}


class _SocketSerial:
    """The slice of the pyserial API that harness.py uses, over a socket."""

    def __init__(self, conn, timeout=10.0):
        self.conn = conn
        self.conn.setblocking(False)
        self.buf = bytearray()
        self.timeout = timeout

    def _pump(self, wait=0.0):
        end = time.time() + wait
        while True:
            try:
                chunk = self.conn.recv(4096)
                if chunk:
                    self.buf += chunk
                    continue
            except BlockingIOError:
                pass
            except OSError:
                return
            if time.time() >= end:
                return
            time.sleep(0.0002)

    def write(self, data):
        self.conn.sendall(data)
        return len(data)

    def reset_input_buffer(self):
        self._pump()
        self.buf.clear()

    @property
    def in_waiting(self):
        self._pump()
        return len(self.buf)

    def read(self, n):
        self._pump()
        out = bytes(self.buf[:n])
        del self.buf[:len(out)]
        return out

    def readline(self):
        deadline = time.time() + self.timeout
        while b"\n" not in self.buf and time.time() < deadline:
            self._pump(0.002)
        idx = self.buf.find(b"\n")
        if idx < 0:
            out = bytes(self.buf)
            self.buf.clear()
            return out
        out = bytes(self.buf[:idx + 1])
        del self.buf[:idx + 1]
        return out


class MameHarness(Z8000TestHarness):
    """Z8000TestHarness speaking to a MAME z8ktest machine over a socket."""

    def __init__(self, target="z8002", mame_dir=None, port=DEFAULT_PORT,
                 machine=None, verbose=False):
        self.mame_dir = mame_dir or os.environ.get("Z8K_MAME_DIR",
                                                   DEFAULT_MAME_DIR)
        binary = os.path.join(self.mame_dir, "mame")
        if not os.path.exists(binary):
            raise RuntimeError(
                f"MAME binary not found at {binary}. Build it with:\n"
                f"  cd {self.mame_dir} && "
                f"make SOURCES=src/mame/zilog/z8ktest.cpp -j8\n"
                f"or set Z8K_MAME_DIR to a build that has z8ktest.cpp.")

        self.machine = machine or MACHINE_FOR_TARGET.get(target, "z8ktest02")
        self.verbose = verbose

        # The machine connects out at machine_start, so listen first.
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(1)
        srv.settimeout(30)

        self._log_path = os.path.join(self.mame_dir, "z8ktest_mame.log")
        self._log = open(self._log_path, "w")
        self.proc = subprocess.Popen(
            [binary, self.machine,
             "-video", "none", "-sound", "none", "-nothrottle",
             "-skip_gameinfo", "-rompath", "roms"],
            cwd=self.mame_dir, stdout=self._log, stderr=subprocess.STDOUT)
        try:
            conn, _ = srv.accept()
        except socket.timeout:
            self.close()
            raise RuntimeError(
                f"MAME never connected to the link on port {port}. "
                f"See {self._log_path}")
        finally:
            srv.close()

        self.ser = _SocketSerial(conn)

    def send_command(self, cmd, multiline=False):
        """Socket transport: no pacing delays, read until the line lands."""
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r").encode())

        if multiline or cmd.strip().upper() in ("DA", "DP"):
            data = b""
            quiet_deadline = time.time() + 2.0
            while time.time() < quiet_deadline:
                n = self.ser.in_waiting
                if n:
                    data += self.ser.read(n)
                    quiet_deadline = time.time() + 0.05
                else:
                    time.sleep(0.001)
            lines = [l.strip() for l in data.decode(errors="replace").split("\n")
                     if l.strip()]
            return "\n".join(lines)

        return self.ser.readline().decode(errors="replace").strip()

    def close(self):
        proc = getattr(self, "proc", None)
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        log = getattr(self, "_log", None)
        if log is not None and not log.closed:
            log.close()


class MameRunner(TestRunner):
    """TestRunner bound to a MAME-hosted harness.

    Nothing is overridden: the value of modelling the rig is that the same
    runner drives silicon, the FPGA and MAME.
    """

    def __init__(self, target="z8002", verbose=False, mame_dir=None,
                 port=DEFAULT_PORT):
        harness = MameHarness(target=target, mame_dir=mame_dir, port=port,
                              verbose=verbose)
        harness.upload_bootstrap(target)
        super().__init__(harness, target=target, verbose=verbose)

    def close(self):
        self.harness.close()
