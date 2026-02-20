# Z8000 Instruction Test Harness

A Z80-based test harness for verifying Z8000 CPU implementations on FPGA. Uses a TV80 Z80 core as a supervisor to control the Z8000 under test via UART commands.

## Architecture

```
                    +-------------------+
  UART RX/TX <----> |   TV80 Z80 Core   | <---> Z80 RAM (8KB)
                    |   (Supervisor)    |
                    +--------+----------+
                             | Port A
                    +--------v----------+
                    |  True Dual-Port   |
                    |   BRAM (8KB)      |
                    +--------+----------+
                             | Port B
                    +--------v----------+
                    | Z8000 Bus I/F     |
                    | (~4MHz clk div +  |
                    |  addr latch)      |
                    +--------+----------+
                             |
                    +--------v----------+
                    |    Z8000 CPU      |
                    |  (Under Test)     |
                    +-------------------+
```

The Z80 supervisor runs firmware that accepts commands over UART to:
- Reset/run the Z8000
- Read/write Z8000 memory (via BRAM Port A)
- Read/write Z8000 registers (via memory-mapped register file)
- Monitor Z8000 status (halt, running)
- Read bus trace buffer

## Target Hardware

- **FPGA**: Tang Nano 20K (Gowin GW2AR-18C)
- **Clock**: 27MHz system clock; Z8000 runs at ~3.86MHz (divided from 27MHz)
- **UART**: 115200 baud, 8N1
- **Reset**: Button-debounced (~20ms) for Z80; Z80-controlled (port 0x14) for Z8000

## LED Indicators

| LED | Function |
|-----|----------|
| LED1 | Heartbeat (toggles ~1Hz) |
| LED2 | Z8000 in reset |
| LED3 | Z8000 running |
| LED4 | Z8000 halted |

## UART Command Protocol

All commands are text-based, terminated by CR or LF. Commands are case-insensitive (e.g., `st`, `ST`, `St` all work). Hex values accept both uppercase and lowercase (0-9, A-F, a-f). **No spaces** between command and arguments (e.g., `WM02008110` not `WM 0200 8110`).

### Status Commands

| Command | Description | Response |
|---------|-------------|----------|
| `ST` | Query status | `14=xx 15=xx ST=x H` or `R` |
| `RS` | Assert reset | `OK` |
| `EX` | Reset, execute, halt (counters preserved) | `HALT`, `TOUT`, or `NRST` |
| `INIT` | Initialize Z8000 (reset vectors + clear regs) | `OK` |
| `TOxxxxxxxx` | Set cycle timeout (32-bit hex) | `OK` |

**EX command phases:**

| Phase | Description | Timeout | Response |
|-------|-------------|---------|----------|
| 0. Reset | Asserts reset (clears counters) | - | - |
| 1. Startup | Releases reset, waits for AS_n (bus_active) | ~200μs (fixed) | `NRST` on timeout |
| 2. Execution | Waits for halt_n LOW or cycle timeout | 1 sec default (configurable) | `HALT` or `TOUT` |

- After HALT/TOUT, the Z8000 stays halted (not reset) so CC/FC/TC are valid
- Next EX will reset and start fresh

**TO command:** Sets cycle-based execution timeout (phase 2)
- Timeout is based on Z8000 clock cycles (not wall-clock time)
- Default: 4,000,000 cycles = 1 second at 4MHz
- `TO00000000` = No timeout (run forever until HALT)
- `TO00001000` = 4,096 cycles (~1ms at 4MHz)
- `TO003D0900` = 4,000,000 cycles (1 second at 4MHz) - default
- `TO00F42400` = 16,000,000 cycles (4 seconds at 4MHz)
- `TOFFFFFFFF` = ~4.3 billion cycles (~18 minutes at 4MHz)

**Instrumentation commands:**
- `CC` - Read cycle count (8 hex digits) - Z8000 clock cycles from reset release to HALT
- `FC` - Read fetch count (4 hex digits) - number of opcode fetches executed
- `TC` - Read trace buffer entry count (3 hex digits, 0-3FF)
- `TR` - Dump first 16 trace entries
- `TRnnn` - Dump trace entry at index nnn (hex)

**INIT command** loads embedded bootstrap code to Z8000 memory:
- Copies ~516 bytes from Z80 firmware to Z8000 memory (0x0000-0x0203)
- Sets up reset vectors: FCW=0x4000, PC=0x0040 (bootstrap entry)
- Bootstrap loads registers R0-R15 from 0x0010-0x002F, then jumps to 0x0200
- Register dump routine at 0x00C0 saves R0-R15 to 0x0090-0x00AF

### Register Commands

Registers R0-R15 are mapped to Z8000 memory at addresses 0x0090-0x00AF.

| Command | Description | Response |
|---------|-------------|----------|
| `WRnxxxx` | Write register Rn with value xxxx | `OK` |
| `RRn` | Read register Rn | `xxxx` (4 hex digits) |
| `DA` | Dump all registers R0-R15 | `R0=xxxx` through `R15=xxxx` |

### Memory Commands

| Command | Description | Response |
|---------|-------------|----------|
| `WMaaaaxxxx` | Write word xxxx to address aaaa | `OK` |
| `RMaaaa` | Read word from address aaaa | `xxxx` (4 hex digits) |
| `MT` | Memory test (writes/reads test patterns) | `PASS` or `FAIL` |

### Debug Commands

| Command | Description | Response |
|---------|-------------|----------|
| `DB` | Toggle debug mode on/off | `DB=0` or `DB=1` |
| `DP` | Dump all I/O port values | Port values P01-P15 |

When debug mode is enabled (`DB=1`), commands output additional diagnostic information:
- `EX` shows cycle limit, run status, final port 0x15 status, cycle count, and fetch count
- `DA` shows loop iteration, addresses, and values at each step
- `RRn` shows the memory address and raw value read

### Error Response

Invalid commands return: `ERR`

## Memory Map

### Z8000 Address Space (after INIT)

| Address | Contents |
|---------|----------|
| 0x0000-0x0005 | Reset vectors (reserved, FCW=0x4000, PC=0x0040) |
| 0x0010-0x002F | Register initial values (loaded to R0-R15 by bootstrap) |
| 0x0030-0x0031 | FCW setup value |
| 0x0040-0x0083 | Bootstrap code (loads registers, jumps to 0x0200) |
| 0x0090-0x00AF | Register dump area (R0-R15 saved here after execution) |
| 0x00C0-0x010F | Register dump routine |
| 0x0200+ | Test code (user writes here) |
| 0x0F00+ | Scratch memory |

### Z80 Supervisor Address Space

| Address | Contents |
|---------|----------|
| 0x0000-0x1FFF | Z80 RAM (8KB) - contains firmware |

### Z80 I/O Port Map

| Port | Read | Write |
|------|------|-------|
| 0x00 | UART RX data | UART TX data |
| 0x01 | UART status (bit0=tx_ready, bit1=rx_valid) | - |
| 0x10 | Z8000 mem addr low | Z8000 mem addr low |
| 0x11 | Z8000 mem addr high | Z8000 mem addr high |
| 0x12 | Z8000 mem data low | Z8000 mem data low |
| 0x13 | Z8000 mem data high | Z8000 mem data high |
| 0x14 | Z8000 control (bit0=reset_n) | Z8000 control (bit0=reset_n, bit1=write_mem) |
| 0x15 | Z8000 status (bit0=halt_n, bit1=bus_active, bit2=cycle_timeout) | - |
| 0x16-0x19 | Cycle count (32-bit, little-endian) | - |
| 0x1A-0x1B | Fetch count (16-bit, little-endian) | - |
| 0x1C-0x1F | - | Cycle limit (32-bit, little-endian) |
| 0x20-0x21 | - | Trace read address (10-bit index) |
| 0x22-0x23 | Trace entry address (16-bit) | - |
| 0x24-0x25 | Trace entry data (16-bit) | - |
| 0x26 | Trace entry flags (bit0=R/W, bit1=B/W, bit2=I/O) | - |
| 0x27-0x28 | Trace write count (10-bit) | - |
| 0x29 | Z8000 ST bus status (4-bit) | - |

## Building

### Prerequisites

- `z80asm` - Z80 assembler
- `z8k-coff-as`, `z8k-coff-ld`, `z8k-coff-objcopy` - Z8000 toolchain (for bootstrap)
- `iverilog` - Icarus Verilog (for simulation)
- `gtkwave` - Waveform viewer (optional)
- Gowin IDE - For FPGA synthesis

### Bootstrap (Z8000 code)

Build the Z8000 bootstrap code:

```bash
make bootstrap
```

This generates:
- `src/bootstrap.bin` - Z8000 binary (reset vectors, register init, dump routines)
- `src/bootstrap.lst` - Assembly listing with addresses and opcodes
- `src/bootstrap.inc` - Z80 assembly include file (embedded in firmware)

### Firmware

Assemble the Z80 firmware (includes bootstrap):

```bash
make firmware
```

This generates:
- `src/z80_fw.bin` - Raw binary (~2.9KB, includes embedded bootstrap)
- `src/z80_fw.hex` - Hex file for Verilog `$readmemh`

Note: `make firmware` automatically rebuilds bootstrap if needed.

### Emulator Test Driver

Build the C++ emulator test driver (for `python -m tests --emu`):

```bash
make emu-build
```

This builds `z8000_emu/build/libz8000.a` and compiles `emu/z8000_test_driver`. The driver is also built automatically on first `--emu` run.

### Simulation

Run the Z80 harness simulation (tests harness commands without Z8000):

```bash
make sim
```

Run full system simulation with Z8000 CPU:

```bash
make sim-full
```

View waveforms:

```bash
make wave
```

### FPGA Synthesis

Open the Gowin IDE project file:

```
z8000_test_harness.gprj
```

## File Structure

```
instructions/
├── Makefile                    # Build automation
├── README.md                   # This file
├── CLAUDE.md                   # AI assistant project context
├── .gitignore                  # Excludes generated files
├── test_harness.py             # Interactive serial console
├── tests/                      # Python test framework
│   ├── __init__.py             # collect_all_tests()
│   ├── __main__.py             # CLI: python -m tests
│   ├── harness.py              # Z8000TestHarness (serial communication)
│   ├── defs.py                 # TestCase, TestResult dataclasses
│   ├── runner.py               # TestRunner (setup, execute, verify)
│   ├── traces.py               # Trace save/load/compare
│   ├── flags.py                # FCW flag definitions and computation
│   ├── helpers.py              # Memory layout constants
│   ├── encoding.py             # Instruction encoding helpers
│   ├── test_arithmetic.py      # ADD, SUB, ADC, SBC, INC, DEC, NEG
│   ├── test_logical.py         # AND, OR, XOR, COM, CLR
│   ├── test_compare.py         # CP, TEST
│   ├── test_load.py            # LD, LDK
│   ├── test_bit.py             # BIT, SET, RES
│   ├── test_shift.py           # SLL, SRL, SRA, RL, RR, RLC, RRC
│   ├── test_branch.py          # JP, JR, DJNZ, CALL/RET
│   ├── test_stack.py           # PUSH, POP
│   ├── test_block.py           # LDI, LDIR, LDD, CPI
│   ├── test_exchange.py        # EX, EXTSB, EXTS
│   ├── test_control.py         # NOP, SETFLG, RESFLG, COMFLG, TCC
│   ├── test_io.py              # IN, OUT (trace-verified)
│   ├── gen_systematic.py       # 797 systematic tests (unrolled, assembler-verified listings)
│   ├── all_tests.s             # Assembly source for 761 single-instruction tests
│   ├── all_tests.lst           # Assembler listing from z8k-coff-as
│   ├── golden.py               # Golden result save/load/compare
│   ├── auto_generate.py        # Generate test file from golden diffs
│   ├── compare.py              # CLI: python -m tests.compare
│   ├── sim_runner.py           # SimRunner (iverilog/vvp backend)
│   ├── emu_runner.py           # EmuRunner (z8000_emu C++ backend)
│   └── verify.py               # Shared result verification logic
├── emu/                        # Emulator test driver
│   ├── z8000_test_driver.cpp   # C++ driver (reads spec, runs z8002_device)
│   └── test_io_ports.h         # Custom I/O ports (replicates z8k_io_ports.v)
├── z8000_emu/                  # Z8000 C++ emulator (git submodule)
│   ├── include/                # z8000.h, z8000_intf.h, memory.h
│   └── build/libz8000.a       # Static library
├── z8000_test_harness.gprj     # Gowin IDE project
├── rtl/                        # Z8000 CPU (copied from ../z8000_micro)
│   ├── z8000_cpu.v             # Main CPU module
│   ├── decode_rom.v            # Instruction decoder
│   ├── microcode_rom.v         # Microcode ROM
│   └── ucode_defs.v            # Microcode definitions
├── golden/                      # Golden reference results
│   └── z8001/                   # Z8001 captured results (797 JSON files)
├── scripts/
│   ├── gen_fw_hex.py           # Z80 firmware hex generator
│   └── gen_bootstrap_inc.py    # Bootstrap to Z80 include converter
├── src/
│   ├── bootstrap.s             # Z8000 bootstrap source (reset vectors, reg init)
│   ├── z80_fw.asm              # Z80 supervisor firmware (includes bootstrap.inc)
│   ├── z80_harness.v           # Z80 harness (TV80 + I/O)
│   ├── z8000_test_harness_top.v # Top module for FPGA
│   ├── z8000_bus_fpga.v        # Z8000 bus interface (CPU, ~4MHz clk, addr latch)
│   ├── z8000_test_harness_tb.v # Z80-only simulation testbench
│   ├── z8000_full_tb.v         # Full system testbench (Z8000 + BRAM, no UART)
│   ├── uart_rx.v               # UART receiver
│   ├── uart_tx.v               # UART transmitter
│   ├── ram16.v                 # Behavioral dual-port RAM (simulation)
│   ├── ram16_gowin.v           # Gowin DPB RAM (synthesis)
│   ├── trace_buffer.v          # Bus trace buffer (1024 entries, address-gated)
│   ├── gowin_dpb/              # Gowin true dual-port BRAM IP (4Kx8)
│   │   ├── gowin_dpb.v
│   │   └── gowin_dpb.ipc
│   ├── gowin_sdpb/             # Gowin semi dual-port BRAM IP (trace buffer)
│   │   ├── gowin_sdpb.v
│   │   └── gowin_sdpb.ipc
│   └── top.cst                 # Pin constraints
└── tv80_official/              # TV80 Z80 core (git submodule)
    └── rtl/core/
        ├── tv80_alu.v
        ├── tv80_core.v
        ├── tv80_mcode.v
        ├── tv80_reg.v
        └── tv80s.v
```

**Generated files** (created by build targets, excluded from git):
- `src/bootstrap.bin`, `src/bootstrap.o`, `src/bootstrap.elf`, `src/bootstrap.lst`, `src/bootstrap.inc`
- `src/z80_fw.bin`, `src/z80_fw.hex`

## Test Framework

The `tests/` package provides a declarative test framework with 138 tests across 48 Z8000 mnemonics. Three execution backends are available: FPGA hardware (via UART), iverilog simulation, and C++ emulator.

### Running Tests

```bash
# Hardware mode (FPGA via UART)
python -m tests -p /dev/ttyUSB0                     # Run all tests
python -m tests -p /dev/ttyUSB0 --tags arithmetic   # Filter by tag
python -m tests -p /dev/ttyUSB0 --mnemonic ADD      # Filter by mnemonic
python -m tests -p /dev/ttyUSB0 --name "add_r_*"    # Filter by name glob
python -m tests -p /dev/ttyUSB0 --target z8002      # Target CPU filter
python -m tests -p /dev/ttyUSB0 --list               # List without running
python -m tests -p /dev/ttyUSB0 -v                   # Verbose output

# Simulation mode (iverilog/vvp, no hardware needed)
python -m tests --sim                                # Run all in simulation
python -m tests --sim --name "add_r_*" -v            # Single test
python -m tests --sim --recompile                    # Force recompile

# Emulator mode (z8000_emu C++ emulator, no hardware or iverilog needed)
python -m tests --emu                                # Run all via emulator
python -m tests --emu --name "add_r_*" -v            # Single test
python -m tests --emu --recompile                    # Force rebuild driver
```

### Target Selection

| `--target`   | Runs tests with `target=`            | Use for                           |
|--------------|--------------------------------------|-----------------------------------|
| `common`     | `common`                             | Tests valid on any Z8000          |
| `z8002`      | `common`, `z8002`                    | Verilog Z8002 implementation      |
| `z8001`      | `common`, `z8001`                    | Physical Z8001, non-segmented     |
| `z8001-seg`  | `common`, `z8001`, `z8001-seg`       | Physical Z8001, segmented mode    |

### Bus Trace Capture and Comparison

The trace buffer captures Z8000 bus transactions during test execution. Tracing is address-gated in hardware: it activates when the first opcode fetch hits the test code area (>= 0x0200) and deactivates when execution leaves that range (jump to dump routine). This captures only the instruction under test and its data accesses.

```bash
# Capture traces from Z8002 Verilog implementation
python -m tests -p /dev/ttyUSB0 --target z8002 --save-traces traces/z8002

# Run on physical Z8001, save traces and compare against Z8002
python -m tests -p /dev/ttyUSB1 --target z8001 --save-traces traces/z8001 \
    --compare-traces traces/z8002
```

Traces are saved as JSON files (one per test). Comparison checks bus transactions entry-by-entry, reporting mismatches in address, data, or cycle type.

### Golden Comparison Testing

The `tests.compare` module provides systematic validation of the Z8002 FPGA against a real Z8001 CPU. It generates ~800 tests covering all Z8000 instruction categories, captures golden results from the Z8001, and diffs the Z8002 against them.

```bash
# 1. Capture golden results from Z8001 (requires --target z8001 for correct reset vectors)
python -m tests.compare --capture --port /dev/ttyUSB0 --target z8001 --golden-dir golden/z8001
python -m tests.compare --capture --port /dev/ttyUSB0 --target z8001 --golden-dir golden/z8001 --mnemonic ADD

# 2. Compare Z8002 against golden (--target z8002 is implicit for --sim/--emu)
python -m tests.compare --port /dev/ttyUSB0 --target z8002 --golden-dir golden/z8001
python -m tests.compare --sim --golden-dir golden/z8001
python -m tests.compare --emu --golden-dir golden/z8001

# 3. Auto-generate test file from diffs
python -m tests.compare --port /dev/ttyUSB0 --target z8002 --golden-dir golden/z8001 --auto-generate

# List systematic tests
python -m tests.compare --list
python -m tests.compare --list -v --mnemonic ADD
```

Golden results are saved as one JSON file per test in `golden/z8001/` (797 files, checked into git). Each test in `gen_systematic.py` has an assembler-verified listing comment from `z8k-coff-as -z8002`. Comparison checks registers, individual flags (C, Z, S, V, DA, H), memory, and execution result. The `--auto-generate` option writes `tests/test_z8001_golden.py` containing only the failing cases with Z8001 values as expected results, which are then picked up by the regular test runner.

**Current status:** 796 match, 1 differ (of 797 tests). Remaining differences:

| Category | Tests | Issue |
|----------|-------|-------|
| DIV | 1 | CASE 3 overflow: R1 and S are undefined per Z8000 manual (implementation-specific) |

### Interactive Console

```bash
python test_harness.py /dev/ttyUSB0                  # Interactive mode
python test_harness.py /dev/ttyUSB0 all              # Run all tests
python test_harness.py /dev/ttyUSB0 ST               # Send raw command
```

Interactive commands: `help`, `all`, `raw CMD`, `quit`

## Quick Start

1. Connect to the FPGA via serial (115200 baud)
2. Initialize the Z8000: `INIT`
3. Write test code at 0x0200
4. Execute: `EX` (default 1 second timeout)
5. Check results: `DA` or `RRn`
6. Optional: Read cycle count with `CC`, fetch count with `FC`

## Example Session

```
$ screen /dev/ttyUSB0 115200

INIT                    # Initialize reset vectors and clear registers
OK
WR01234                 # Set R0 = 0x1234
OK
WR15678                 # Set R1 = 0x5678
OK
WM02008110              # Write ADD R0,R1 at 0x0200
OK
WM02027A00              # Write HALT at 0x0202
OK
EX                      # Execute (1 sec default timeout)
HALT
CC                      # Read cycle count
00000052                # 82 cycles to execute
FC                      # Read fetch count
0003                    # 3 instructions fetched
RR0                     # Read R0 result (0x1234 + 0x5678 = 0x68AC)
68AC
DA                      # Dump all registers
R0=68AC
R1=5678
R2=0000
...
MT                      # Memory test
PASS
```

### Setting Custom Timeout

```
TO00000400              # Set timeout to 1024 cycles (~256μs at 4MHz)
OK
EX                      # Execute with short timeout
TOUT                    # Timed out (test took longer than 1024 cycles)
CC                      # Check how many cycles ran
00000400                # Stopped at exactly 1024 cycles
TO003D0900              # Reset to default 1 second timeout
OK
```

### Using Debug Mode

```
DB                      # Enable debug mode
DB=1
EX                      # Execute with debug output
[L=003D0900][RUN][S=00][C=00000052][F=0003]HALT
                        # L=cycle limit, S=port 0x15, C=cycle count, F=fetch count
DP                      # Dump I/O ports
P01=03
P10=00
P11=00
P12=00
P13=00
P14=00
P15=01
```

## Z8000 Opcode Reference

Common instructions used with the test harness:

| Instruction | Opcode | Description |
|-------------|--------|-------------|
| `LD Rd, #imm` | 0x21_d + imm | Load immediate |
| `ADD Rd, Rs` | 0x81sd | Add register to register |
| `SUB Rd, Rs` | 0x83sd | Subtract |
| `AND Rd, Rs` | 0x87sd | Logical AND |
| `OR Rd, Rs` | 0x85sd | Logical OR |
| `XOR Rd, Rs` | 0x89sd | Logical XOR |
| `JP addr` | 0x5E08 + addr | Unconditional jump |
| `HALT` | 0x7A00 | Halt processor |

Note: `d` = destination register (0-F), `s` = source register (0-F)

## Design Notes

1. **Z80 as Supervisor**: Using a Z80 CPU instead of a Verilog state machine provides flexibility for complex test sequences and easier debugging via readable assembly code.

2. **True Dual-Port BRAM**: The 8KB BRAM uses Gowin DPB (true dual-port) primitives with Port A for Z80 and Port B for Z8000. Both ports operate independently with no arbitration needed. WRITE_MODE is set to 01 (write-through) so reads work without requiring a write cycle.

3. **Register Access**: Z8000 registers are memory-mapped at 0x0090-0x00AF. The Z80 reads/writes these via BRAM Port A while Z8000 accesses via Port B.

4. **Clock Architecture**: The Z80 and all shared logic run at 27MHz. The Z8000 CPU runs at ~3.86MHz via a clock divider (alternating /3 and /4 half-periods from 27MHz — closest to 4MHz without a PLL). The bus interface module (`z8000_bus_fpga.v`) encapsulates the clock divider, CPU, AD bus tristate, and address latch.

5. **Reset Architecture**: Button reset is debounced (~20ms at 27MHz) and resets only the Z80 and harness logic. The Z8000 reset (`z8k_rst_n`) is controlled by Z80 firmware via I/O port 0x14, latched until explicitly changed.

6. **Cycle-Based Timeout**: Execution timeout is implemented in hardware using the Z8000 cycle counter, not Z80 polling loops. This provides accurate, deterministic timeout behavior independent of Z80 execution speed. Default timeout is 1 second (4M cycles at 4MHz).

7. **Trace Buffer**: A 1024-entry buffer captures Z8000 bus transactions (address, data, R/W, B/W, I/O/MEM) on DS_n rising edges. Address-gated: only captures when executing test code (PC >= 0x0200), skipping bootstrap and dump routine overhead. Readable via Z80 I/O ports 0x20-0x28.

8. **Vendor-Neutral RAM**: The RAM uses separate files for simulation (`ram16.v`) and synthesis (`ram16_gowin.v`). Both implement the same `ram16` module interface. To port to other FPGAs, create a new `ram16_<vendor>.v` and update the project file.

9. **Embedded Bootstrap**: The Z8000 bootstrap code (reset vectors, register initialization, dump routines) is embedded in the Z80 firmware. The INIT command copies this data to Z8000 memory at runtime. BRAM starts uninitialized; all memory content is loaded by the Z80 supervisor.

## Troubleshooting

### No UART Response

1. Check baud rate is 115200
2. Verify TX/RX pins on Tang Nano 20K
3. Check USB cable and serial port selection

### Memory Test Fails

1. Verify the design was synthesized with latest sources
2. Check BRAM initialization in synthesis
3. Use `DP` to check I/O port values

### CPU Doesn't Halt

1. Verify test code includes HALT instruction (0x7A00)
2. Check for infinite loops in test code
3. Use `ST` to check if CPU is still running

### Execution Timeout (TOUT)

If EX returns `TOUT` unexpectedly:
1. Test code may be taking longer than expected - increase timeout with `TO`
2. Check cycle count with `CC` to see how many cycles executed
3. Use `TO00000000` to disable timeout for debugging
4. Default timeout is 1 second (4M cycles) - use `TO00F42400` for 4 seconds

### Debugging Issues

Enable debug mode to see internal state:
```
DB              # Toggle debug on (DB=1)
ST              # Shows port values: [ST]<14=XX><15=XX>H
DA              # Shows detailed progress for each register
DP              # Dump all I/O port values
```

Use `raw CMD` in the Python script to see exact bytes received:
```
> raw DA
Sent: 'DA'
  [0] in_waiting=12: b'R0=0000\r\n'
  [1] in_waiting=24: b'R1=0000\r\nR2=0000\r\n'
  ...
```

## License

TV80 Z80 core is under its original license (see tv80_official/).
Z8000 implementation and test harness: same as parent Z8000_FPGA project.
