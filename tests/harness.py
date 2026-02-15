"""Z8000 Test Harness - serial communication with the FPGA test harness."""

import os
import struct
import time
import serial


class Z8000TestHarness:
    def __init__(self, port, baud=115200, timeout=1):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.1)  # Wait for port to settle

    def send_command(self, cmd, multiline=False):
        """Send command and return response.

        If multiline=True or cmd is known multi-line (DA, DP), read all lines.
        """
        self.ser.reset_input_buffer()
        self.ser.write((cmd + '\r').encode())

        # Commands that return multiple lines
        cmd_upper = cmd.strip().upper()
        if multiline or cmd_upper in ('DA', 'DP'):
            # Read multi-line response - wait for data, then read until quiet
            time.sleep(0.1)  # Initial wait for response to start
            data = b''
            while True:
                n = self.ser.in_waiting
                if n > 0:
                    data += self.ser.read(n)
                    time.sleep(0.05)  # Brief wait to see if more data coming
                else:
                    break
            lines = [l.strip() for l in data.decode().split('\n') if l.strip()]
            return '\n'.join(lines)
        else:
            time.sleep(0.01)
            response = self.ser.readline().decode().strip()
            return response

    def write_reg(self, reg, value):
        """Write register initial value"""
        return self.send_command(f'WR{reg:X}{value:04X}')

    def read_reg(self, reg):
        """Read register final value"""
        resp = self.send_command(f'RR{reg:X}')
        try:
            return int(resp, 16)
        except:
            return None

    def write_mem(self, addr, value):
        """Write word to memory"""
        return self.send_command(f'WM{addr:04X}{value:04X}')

    def read_mem(self, addr):
        """Read word from memory"""
        resp = self.send_command(f'RM{addr:04X}')
        try:
            return int(resp, 16)
        except:
            return None

    def write_io_port(self, index, value):
        """Write I/O port register (index 0-11, value 16-bit)"""
        return self.send_command(f'WP{index:02X}{value:04X}')

    def read_io_port(self, index):
        """Read I/O port register (index 0-11, returns 16-bit value)"""
        resp = self.send_command(f'RP{index:02X}')
        try:
            return int(resp, 16)
        except:
            return None

    def write_fcw(self, value):
        """Write initial FCW to reset vector (0x0002) and fcw_setup (0x0030)"""
        self.write_mem(0x0002, value)
        return self.write_mem(0x0030, value)

    def read_fcw(self):
        """Read final FCW from fcw_dump area (0x00B2)"""
        return self.read_mem(0x00B2)

    def trace_count(self):
        """Read trace buffer entry count"""
        resp = self.send_command('TC')
        try:
            return int(resp, 16)
        except:
            return None

    def read_trace_entry(self, index):
        """Read a single trace entry by index. Returns parsed dict or raw string."""
        resp = self.send_command(f'TR{index:03X}')
        return self._parse_trace_line(resp)

    def read_all_trace(self):
        """Read all trace entries. Returns list of parsed dicts."""
        count = self.trace_count()
        if not count:
            return []
        return [self.read_trace_entry(i) for i in range(count)]

    def _parse_trace_line(self, line):
        """Parse a trace entry line like '000: 0040 4100 R W M'"""
        line = line.strip()
        if not line or ':' not in line:
            return None
        try:
            idx_str, rest = line.split(':', 1)
            parts = rest.split()
            if len(parts) >= 5:
                return {
                    'index': int(idx_str.strip(), 16),
                    'addr': int(parts[0], 16),
                    'data': int(parts[1], 16),
                    'rw': parts[2],       # 'R' or 'W'
                    'bw': parts[3],       # 'W' (word) or 'B' (byte)
                    'io': parts[4],       # 'M' (memory) or 'I' (I/O)
                }
        except (ValueError, IndexError):
            pass
        return None

    def execute(self):
        """Execute test and wait for halt"""
        return self.send_command('EX')

    def reset(self):
        """Reset CPU"""
        return self.send_command('RS')

    def init(self):
        """Initialize Z8000 - set reset vectors and clear registers"""
        return self.send_command('INIT')

    def set_timeout(self, value):
        """Set execution timeout (0x0000-0xFFFF, 0=max ~126ms)"""
        return self.send_command(f'TO{value:04X}')

    def upload_bootstrap(self, target="z8002", bin_path=None):
        """Upload Z8000 bootstrap binary to BRAM shadow area (0x1000).

        Reads src/bootstrap.bin, replaces reset vectors for the target CPU,
        and uploads to BRAM shadow area. The Z80 INIT command will copy from
        shadow to active area (0x0000) on each test.

        Args:
            target: "z8002", "z8001", or "z8001-seg"
            bin_path: path to bootstrap.bin (default: auto-detect relative to project)
        """
        if bin_path is None:
            # Find bootstrap.bin relative to this file (tests/harness.py -> src/bootstrap.bin)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bin_path = os.path.join(project_root, "src", "bootstrap.bin")

        with open(bin_path, "rb") as f:
            data = f.read()

        # bootstrap.bin starts at 0x0000. First 8 words (16 bytes) are reset vectors,
        # which are target-specific. Replace with appropriate vectors.
        body = data[16:]  # 0x0010 onwards — same for all targets

        if target in ("z8001", "z8001-seg"):
            # Z8001: 4-word segmented reset vector, padded to 8 words
            vectors = struct.pack(">8H", 0x0000, 0x4000, 0x0000, 0x0040, 0, 0, 0, 0)
        else:
            # Z8002: 3-word non-segmented reset vector, padded to 8 words
            vectors = struct.pack(">8H", 0x0000, 0x4000, 0x0040, 0, 0, 0, 0, 0)

        full_image = vectors + body
        word_count = len(full_image) // 2

        # Upload to BRAM shadow area at 0x1000
        for i in range(0, len(full_image), 2):
            word = (full_image[i] << 8) | full_image[i + 1]
            self.write_mem(0x1000 + i, word)

        # Write word count to 0x1FFE
        self.write_mem(0x1FFE, word_count)

    def cycle_count(self):
        """Read cycle count (Z8000 clocks from reset to halt)"""
        resp = self.send_command('CC')
        try:
            return int(resp, 16)
        except:
            return None

    def instr_cycle_count(self):
        """Read instruction cycle count (address-gated, test code only)"""
        resp = self.send_command('IC')
        try:
            return int(resp, 16)
        except:
            return None

    def fetch_count(self):
        """Read opcode fetch count (instructions fetched)"""
        resp = self.send_command('FC')
        try:
            return int(resp, 16)
        except:
            return None

    def status(self):
        """Get status (H=halted, R=running)"""
        return self.send_command('ST')

    def dump_regs(self):
        """Dump all registers - returns list of 16 lines"""
        self.ser.reset_input_buffer()
        self.ser.write(('DA' + '\r').encode())
        time.sleep(0.2)  # Wait for all lines to arrive
        n = self.ser.in_waiting
        data = self.ser.read(n).decode() if n > 0 else ''
        lines = [l.strip() for l in data.split('\n') if l.strip()]
        return lines

    def debug_raw(self, cmd):
        """Debug: send command and show raw bytes received"""
        self.ser.reset_input_buffer()
        self.ser.write((cmd + '\r').encode())
        print(f"Sent: {repr(cmd)}")
        for i in range(20):  # Read for 2 seconds
            time.sleep(0.1)
            n = self.ser.in_waiting
            if n > 0:
                data = self.ser.read(n)
                print(f"  [{i}] in_waiting={n}: {repr(data)}")
        print("Done")

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

    def close(self):
        self.ser.close()
