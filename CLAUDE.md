# Z8000 Instruction Test Harness

FPGA-based test harness for a Z8000 CPU implementation using Tang Nano 20K (Gowin GW2AR-18C).

## Project Structure

- `z8000_micro/` - Z8000 CPU core (git submodule: z8000_micro)
  - `rtl/z8000_cpu.v` - Main CPU module
  - `rtl/microcode_rom.v` - CPU microcode ROM
  - `rtl/decode_rom.v` - Instruction decode ROM
  - `rtl/ucode_defs.v` - Microcode address definitions
- `src/` - Verilog source files
  - `z8000_test_harness_top.v` - Top-level module (bus interface, dual-port memory, trace buffer)
  - `z8000_bus_fpga.v` - Z8000 bus interface (CPU, ~4MHz clock divider, address latch)
  - `z80_harness.v` - Z80 harness controller (TV80 + I/O ports)
  - `ram16.v` - Behavioral dual-port RAM (simulation)
  - `ram16_gowin.v` - Gowin DPB RAM (synthesis)
  - `gowin_dpb/` - Gowin true dual-port BRAM IP (4Kx8, WRITE_MODE=01)
  - `gowin_sdpb/` - Gowin semi dual-port BRAM IP (trace buffer)
  - `trace_buffer.v` - Bus trace capture buffer (1024 entries, address-gated to test code)
  - `z8k_io_ports.v` - Z8000 I/O port registers (12x16-bit, Z8000+Z80 accessible)
  - `uart_tx.v` / `uart_rx.v` - UART modules
  - `bootstrap.s` - Bootstrap/dump routine Z8000 assembly source
  - `z80_fw.asm` - Z80 supervisor firmware
  - `z8000_test_harness_tb.v` - Z80-only simulation testbench
  - `z8000_full_tb.v` - Full system testbench (Z8000 + BRAM, no UART)
  - `top.cst` - FPGA pin constraints
- `tests/` - Python test framework
  - `harness.py` - Z8000TestHarness class (serial communication with FPGA)
  - `defs.py` - TestCase, TestResult dataclasses
  - `runner.py` - TestRunner (setup, execute, verify, report)
  - `traces.py` - Trace save/load/compare utilities
  - `flags.py` - FCW flag bit definitions and reference flag computation
  - `helpers.py` - Memory layout constants and preload helpers
  - `encoding.py` - Instruction encoding helpers (verified against decode_rom)
  - `__init__.py` - collect_all_tests() from all test modules
  - `__main__.py` - CLI entry point (`python -m tests`)
  - `test_arithmetic.py` - ADD, ADDB, SUB, SUBB, ADC, SBC, INC, DEC, NEG
  - `test_logical.py` - AND, OR, XOR, COM, CLR
  - `test_compare.py` - CP, TEST
  - `test_load.py` - LD, LDK
  - `test_bit.py` - BIT, SET, RES
  - `test_shift.py` - SLL, SRL, SLA, SRA, RL, RLC, RR, RRC
  - `test_branch.py` - JP, JR, DJNZ, CALL/RET
  - `test_stack.py` - PUSH, POP
  - `test_block.py` - LDI, LDIR, LDD, CPI
  - `test_exchange.py` - EX, EXTSB, EXTS
  - `test_control.py` - NOP, SETFLG, RESFLG, COMFLG, TCC
  - `test_io.py` - IN, OUT (trace-verified)
- `scripts/` - Build scripts
  - `gen_fw_hex.py` - Z80 firmware hex generator
  - `gen_bootstrap_inc.py` - Bootstrap to Z80 include converter
- `test_harness.py` - Interactive serial console (thin wrapper over tests/harness.py)
- `z8000_test_harness.gprj` - Gowin EDA project file
- `Makefile` - Build automation

## Build Commands

```bash
make firmware   # Assemble Z80 firmware (z80_fw.asm -> z80_fw.bin/hex)
make bootstrap  # Assemble Z8000 bootstrap code (requires z8k-coff-as)
make sim        # Run Z80 harness simulation
make sim-full   # Run full system simulation with Z8000 CPU
make wave       # View VCD waveform in GTKWave
make clean      # Clean build artifacts
```

## Running Tests

```bash
# Full test framework (125 tests across 48 mnemonics)
python -m tests -p /dev/ttyUSB0                     # Run all tests
python -m tests -p /dev/ttyUSB0 --tags arithmetic   # Filter by tag
python -m tests -p /dev/ttyUSB0 --mnemonic ADD      # Filter by mnemonic
python -m tests -p /dev/ttyUSB0 --name "add_r_*"    # Filter by name glob
python -m tests -p /dev/ttyUSB0 --target z8002      # Target CPU filter
python -m tests -p /dev/ttyUSB0 --list               # List without running
python -m tests -p /dev/ttyUSB0 -v                   # Verbose output

# Interactive console
python test_harness.py /dev/ttyUSB0                  # Interactive mode
python test_harness.py /dev/ttyUSB0 all              # Run all tests
python test_harness.py /dev/ttyUSB0 ST               # Send raw command
```

## Target Selection

| `--target`   | Runs tests with `target=`            | Use for                           |
|--------------|--------------------------------------|-----------------------------------|
| `common`     | `common`                             | Tests valid on any Z8000          |
| `z8002`      | `common`, `z8002`                    | Verilog Z8002 implementation      |
| `z8001`      | `common`, `z8001`                    | Physical Z8001, non-segmented     |
| `z8001-seg`  | `common`, `z8001`, `z8001-seg`       | Physical Z8001, segmented mode    |

## Bus Trace Capture

The trace buffer (`trace_buffer.v`) captures Z8000 bus transactions during test
execution. Tracing is address-gated: it activates when the first opcode fetch
hits the test code area (>= 0x0200) and deactivates when execution leaves that
range (e.g. jump to dump routine at 0x00C0). This captures only the instruction
under test and its data accesses, not bootstrap or dump overhead.

```bash
# Capture traces from Z8002 Verilog implementation
python -m tests -p /dev/ttyUSB0 --target z8002 --save-traces traces/z8002

# Run on physical Z8001, save traces and compare against Z8002
python -m tests -p /dev/ttyUSB1 --target z8001 --save-traces traces/z8001 \
    --compare-traces traces/z8002
```

Traces are saved as JSON files (one per test) containing the bus transaction
sequence: address, data, R/W, B/W, MEM/IO. Comparison checks transactions
entry-by-entry, reporting mismatches in address, data, or bus cycle type.

## Test Framework

Tests are declarative `TestCase` dataclasses in `tests/test_*.py`. Each test defines:
- **Initial state**: code words, register values, FCW (flags), memory contents, I/O ports
- **Expected results**: register values, flags set/clear, memory contents, I/O ports
- **Metadata**: name, mnemonic, tags, target (common/z8001/z8001-seg/z8002)

The `TestRunner` in `tests/runner.py` executes each test by:
1. `INIT` (reload bootstrap every test for clean state)
2. Set FCW, write registers, preload memory, write I/O port preloads (via WP)
3. Load test code at 0x0200, append `JP 0x00C0` (dump routine)
4. `EX` (resets, executes, halts - counters preserved after halt)
5. Read back registers, FCW (from 0x00B2), memory, cycle/fetch counts, bus trace
6. If I/O port verification needed: `RS` (z8k_rst_n=0), read ports via RP
7. Compare against expected values

Tags for filtering: `arithmetic`, `logical`, `compare`, `load`, `bit`, `shift`,
`branch`, `stack`, `block`, `exchange`, `control`, `io`, `word`, `byte`,
`R_mode`, `IM_mode`, `IR_mode`, `DA_mode`, `X_mode`, `RA_mode`, `flags`, `store`

## Key Details

- **Clock**: 27MHz system clock; Z8000 runs at ~3.86MHz (divided from 27MHz)
- **Serial**: 115200 baud, 8N1
- **Memory**: 8KB true dual-port BRAM (Gowin DPB), Port A = Z80, Port B = Z8000
- **Reset**: Debounced rst_n for Z80; z8k_rst_n (Z80-controlled via port 0x14) for Z8000
- **FCW flags**: C=bit7, Z=bit6, S=bit5, V=bit4, DA=bit3, H=bit2 (from rtl/z8000_cpu.v)

## Memory Map

| Address       | Purpose                                      |
|---------------|----------------------------------------------|
| 0x0000-0x0005 | Reset vectors (reserved, FCW, PC)            |
| 0x0010-0x002F | Register setup area (R0-R15 initial values)  |
| 0x0030        | FCW setup (loaded by bootstrap via ldctl)    |
| 0x0040-0x008F | Bootstrap code (load FCW, load regs, JP 0x0200) |
| 0x0090-0x00AF | Register dump area (R0-R15 final values)     |
| 0x00B0        | Done flag                                    |
| 0x00B2        | FCW dump (saved by dump routine via ldctl)   |
| 0x00C0-0x010F | Dump routine (save regs, save FCW, halt)     |
| 0x0200-0x03FF | Test code area (512 bytes)                   |
| 0x0400-0x05FF | Memory operand area (DA/IR/X mode tests)     |
| 0x0600-0x06FF | Source buffer (block operations)              |
| 0x0700-0x07FF | Destination buffer (block operations)         |
| 0x0F00        | Stack base (PUSH/POP/CALL/RET tests)         |

## Z8000 I/O Port Registers

12 x 16-bit registers accessible from both Z8000 (via bus cycles) and Z80 (via RP/WP).
Standard (ST=0010) and special (ST=0011) I/O use the same addresses but map to different registers.

| Reg Index | Z8000 Addr | Type           | I/O Type        |
|-----------|-----------|----------------|-----------------|
| 0x00      | 0x0100    | Loopback byte  | Standard        |
| 0x01      | 0x0102    | Loopback word  | Standard        |
| 0x02      | 0x0104    | Output byte    | Standard        |
| 0x03      | 0x0106    | Output word    | Standard        |
| 0x04      | 0x0108    | Input byte     | Standard        |
| 0x05      | 0x010A    | Input word     | Standard        |
| 0x06      | 0x0100    | Loopback byte  | Special         |
| 0x07      | 0x0102    | Loopback word  | Special         |
| 0x08      | 0x0104    | Output byte    | Special         |
| 0x09      | 0x0106    | Output word    | Special         |
| 0x0A      | 0x0108    | Input byte     | Special         |
| 0x0B      | 0x010A    | Input word     | Special         |

Z80 access: `RPnn` reads register, `WPnnxxxx` writes register (nn = hex index).
Z80 I/O ports 0x30-0x47 (low=0x30+N*2, high=0x31+N*2). Access gated on z8k_rst_n=0.

## Serial Protocol

Text commands over UART (no spaces between command and arguments):
`WRnxxxx`, `RRn`, `WMaaaaxxxx`, `RMaaaa`, `WPnnxxxx`, `RPnn`, `EX`, `RS`, `ST`,
`MT`, `DA`, `DB`, `DP`, `INIT`, `TOxxxxxxxx`, `CC`, `FC`, `TC`, `TR`, `TRnnn`

Key commands:
- `RS` - Reset CPU
- `ST` - Status (shows ports 0x14, 0x15, Z8000 ST, and H/R indicator)
- `EX` - Execute until halt (asserts reset first, then releases; returns HALT, TOUT, or NRST; Z8000 stays halted after, counters preserved)
- `WMaaaaxxxx` - Write memory word (no spaces)
- `RMaaaa` - Read memory word (no spaces)
- `TC` - Trace buffer entry count
- `TR` - Dump first 16 trace entries

## Memory Architecture

True dual-port BRAM (Gowin DPB, WRITE_MODE=01 write-through):
- **Port A**: Z80 harness (load/read test code) - always connected
- **Port B**: Z8000 CPU (fetch/execute) - always connected
- No bus arbitration needed; ports are fully independent

Uses `ifdef SIMULATION` to switch between:
- **Simulation**: Behavioral RAM arrays (`ram16.v`), testbench writes data directly
- **Synthesis**: Gowin DPB primitives (`ram16_gowin.v`), Z80 INIT loads bootstrap at runtime

See README.md for full documentation.
