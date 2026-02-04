# Z8000 Instruction Test Harness

A Z80-based test harness for verifying Z8000 CPU implementations on FPGA. Uses a TV80 Z80 core as a supervisor to control the Z8000 under test via UART commands.

## Architecture

```
                    +-------------------+
  UART RX/TX <----> |   TV80 Z80 Core   | <---> Z80 RAM (8KB)
                    |   (Supervisor)    |
                    +--------+----------+
                             |
                    +--------v----------+
                    | Shared BRAM (16KB)|
                    +--------+----------+
                             |
                    +--------v----------+
                    |    Z8000 CPU      |
                    |  (Under Test)     |
                    +-------------------+
```

The Z80 supervisor runs firmware that accepts commands over UART to:
- Reset/run the Z8000
- Read/write Z8000 memory
- Read/write Z8000 registers (via memory-mapped register file)
- Monitor Z8000 status (halt, running)

## Target Hardware

- **FPGA**: Tang Nano 20K (Gowin GW2AR-18C)
- **System Clock**: 27MHz
- **Z8000 Clock**: ~4MHz (derived from system clock)
- **UART**: 115200 baud, 8N1

## LED Indicators

| LED | Function |
|-----|----------|
| LED1 | Heartbeat (toggles ~1Hz) |
| LED2 | Z8000 in reset |
| LED3 | Z8000 running |
| LED4 | Z8000 halted |

## UART Command Protocol

All commands are text-based, terminated by CR or LF. Commands are case-insensitive (e.g., `st`, `ST`, `St` all work). Hex values accept both uppercase and lowercase (0-9, A-F, a-f).

### Status Commands

| Command | Description | Response |
|---------|-------------|----------|
| `ST` | Query status | `H` (halted/reset) or `R` (running) |
| `RS` | Assert reset | `OK` |
| `EX` | Release reset, run until halt | `HALT`, `TOUT`, or `NRST` |
| `INIT` | Initialize Z8000 (reset vectors + clear regs) | `OK` |
| `TOxxxxxxxx` | Set cycle timeout (32-bit hex) | `OK` |

**EX command phases:**

| Phase | Description | Timeout | Response |
|-------|-------------|---------|----------|
| 1. Startup | Waits for AS_n assertion (bus_active) | ~200μs (fixed) | `NRST` on timeout |
| 2. Execution | Waits for halt_n LOW or cycle timeout | 1 sec default (configurable) | `HALT` or `TOUT` |

- Cycle and fetch counters are valid after `HALT`

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
- `ST` shows port 0x14 and 0x15 values read
- `EX` shows cycle limit, run status, final port 0x15 status, and cycle count
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
- `src/z80_fw.bin` - Raw binary (~2.4KB, includes embedded bootstrap)
- `src/z80_fw.hex` - Hex file for Verilog `$readmemh`

Note: `make firmware` automatically rebuilds bootstrap if needed.

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
├── .gitignore                  # Excludes generated files
├── test_harness.py             # Python control script
├── z8000_test_harness.gprj     # Gowin IDE project
├── scripts/
│   ├── gen_fw_hex.py           # Z80 firmware hex generator
│   └── gen_bootstrap_inc.py    # Bootstrap to Z80 include converter
├── src/
│   ├── bootstrap.s             # Z8000 bootstrap source (reset vectors, reg init)
│   ├── z80_fw.asm              # Z80 supervisor firmware (includes bootstrap.inc)
│   ├── z80_harness.v           # Z80 harness (TV80 + I/O)
│   ├── z8000_test_harness_tb.v # Simulation testbench
│   ├── z8000_test_harness_top.v # Top module for FPGA
│   ├── uart_rx.v               # UART receiver
│   ├── uart_tx.v               # UART transmitter
│   ├── gowin_dpb.v             # Gowin dual-port BRAM wrapper
│   └── top.cst                 # Pin constraints
└── tv80_official/              # TV80 Z80 core (git submodule)
    └── rtl/core/
        ├── tv80_alu.v
        ├── tv80_core.v
        ├── tv80_mcode.v
        ├── tv80_reg.v
        └── tv80s.v
```

**Generated files** (created by `make bootstrap` and `make firmware`, excluded from git):
- `src/bootstrap.bin`, `src/bootstrap.o`, `src/bootstrap.elf`, `src/bootstrap.lst`, `src/bootstrap.inc`
- `src/z80_fw.bin`, `src/z80_fw.hex`

## Python Control Script

The `test_harness.py` script provides a convenient interface for testing:

```bash
# Interactive mode
python test_harness.py /dev/ttyUSB0

# Single command
python test_harness.py /dev/ttyUSB0 ST

# Run all built-in tests
python test_harness.py /dev/ttyUSB0 all
```

Interactive commands:
- `help` - Show all commands with descriptions
- `all` - Run built-in instruction tests (ADD, SUB, AND, OR, XOR)
- `raw CMD` - Debug: show raw bytes received
- `quit` - Exit

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
ST                      # Status with debug output
[ST]<14=00><15=FF>H
EX                      # Execute with debug output
[L=003D0900][RUN][S=00][C=00000052]HALT
                        # L=cycle limit, S=port 0x15, C=cycle count
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

2. **Shared Memory**: The 16KB BRAM is shared between Z80 (via I/O ports) and Z8000 (via address bus). Z80 has priority when Z8000 is in reset.

3. **Register Access**: Z8000 registers are memory-mapped at 0x0090-0x00AF. The Z80 can read/write these directly when Z8000 is in reset.

4. **Clock Domains**: Z80 runs at 27MHz (system clock), Z8000 runs at ~4MHz (divided).

5. **Cycle-Based Timeout**: Execution timeout is implemented in hardware using the Z8000 cycle counter, not Z80 polling loops. This provides accurate, deterministic timeout behavior independent of Z80 execution speed. Default timeout is 1 second (4M cycles at 4MHz).

6. **Embedded Bootstrap**: The Z8000 bootstrap code (reset vectors, register initialization, dump routines) is embedded in the Z80 firmware. The INIT command copies this data to Z8000 memory, ensuring identical initialization in simulation and hardware. No hardcoded Verilog memory initialization is used.

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
