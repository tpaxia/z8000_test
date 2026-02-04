# Z8000 Instruction Test Harness

A test harness for the Z8000 CPU implementation that allows testing individual instructions via a serial interface.

## Overview

This project provides an FPGA-based test harness for the Z8000 CPU that can:
- Set up initial register and memory state before test execution
- Execute one or more instructions
- Examine all registers, flags, and memory after execution
- Test I/O port operations
- Run the complete test suite from `../z8000_micro`

## Target Hardware

- **FPGA**: Tang Nano 20K (Gowin GW2AR-18C)
- **Clock**: 27MHz system clock, ~4MHz CPU clock
- **Serial**: 115200 baud, 8N1 via USB-C
- **Memory**: 4KB BRAM (using Gowin SDPB primitives)

## LED Indicators

| LED | Pin | Function |
|-----|-----|----------|
| led | 15 | Heartbeat (flashing ~1Hz) |
| led2 | 16 | CPU in reset (on after `RS` command) |
| led3 | 17 | CPU running (on during `EX` execution) |
| led4 | 18 | CPU halted (on after `HALT` instruction) |

**Expected states:**
- After power-on/reset: led2 ON, led3 OFF, led4 OFF
- During execution (`EX`): led2 OFF, led3 ON, led4 OFF
- After halt: led2 OFF, led3 OFF, led4 ON

## Memory Map

| Address Range | Description |
|--------------|-------------|
| 0x0000-0x0005 | Reset vectors (FCW at 0x0002, PC at 0x0004) |
| 0x0010-0x002F | Register setup area (R0-R15 initial values) |
| 0x0030-0x0031 | Initial FCW value |
| 0x0040-0x0083 | Bootstrap code (loads registers, jumps to test) |
| 0x0090-0x00AF | Register dump area (R0-R15 final values) |
| 0x00B0-0x00B1 | Done flag (set to 0xDEAD when test complete) |
| 0x00C0-0x0108 | Dump routine (stores registers, halts) |
| 0x0200-0x0FFF | Test code and data area |

## Serial Protocol

Commands are text-based, terminated with CR or LF.

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `WR nn xxxx` | Write register n initial value | `WR 0 1234` |
| `RR nn` | Read register n final value | `RR 0` |
| `WM aaaa xxxx` | Write word to memory | `WM 0200 8100` |
| `RM aaaa` | Read word from memory | `RM 0200` |
| `WB aaaa xx` | Write byte to memory | `WB 0200 41` |
| `RB aaaa` | Read byte from memory | `RB 0200` |
| `WF xxxx` | Write initial FCW | `WF 4000` |
| `RF` | Read final FCW | `RF` |
| `EX` | Execute until halt | `EX` |
| `RS` | Reset CPU | `RS` |
| `ST` | Get status (H=halted/reset, R=running) | `ST` |
| `MT` | Memory test (write/read patterns) | `MT` |
| `LH nnnn aaaa` | Load hex (binary mode) | `LH 0010 0200` |
| `DA` | Dump all registers | `DA` |

### Responses

| Response | Meaning |
|----------|---------|
| `OK` | Command successful |
| `xxxx` | Hex value (for read commands) |
| `ERR` | Error |
| `HALT` | CPU halted normally |
| `TOUT` | Execution timeout |
| `H` | Status: Halted or in reset |
| `R` | Status: Running |
| `PASS` | Memory test passed |
| `FAIL:xxxx` | Memory test failed (shows last read value) |

## Test Execution Flow

1. Set up initial register values using `WR` commands
2. Write test code to memory starting at 0x0200 using `WM` commands
3. End test code with `JP 0x00C0` (jump to dump routine)
4. Execute with `EX` command
5. Read results using `RR` commands

## Example: Testing ADD Instruction

```
# Set R0 = 0x1234, R1 = 0x5678
WR 0 1234
WR 1 5678

# Write ADD R0, R1 instruction at 0x0200
# Z8000 ADD Rd,Rs opcode: 0x81sd where s=source, d=dest
# ADD R0, R1 = 0x8110 (s=1, d=0)
WM 0200 8110

# Write JP to dump routine (JP 0x00C0)
# Z8000 JP opcode: 0x5E08 followed by 16-bit address
WM 0202 5E08
WM 0204 00C0

# Execute
EX

# Read result (should be 0x68AC)
RR 0
```

## Z8000 Opcode Reference

Common instructions used with the test harness:

| Instruction | Opcode | Description |
|------------|--------|-------------|
| `LD Rd, @addr` | 0x610d + addr | Load from direct address |
| `ST @addr, Rs` | 0x6F0s + addr | Store to direct address |
| `LD Rd, #imm` | 0x210d + imm | Load immediate |
| `ADD Rd, Rs` | 0x81sd | Add register to register |
| `SUB Rd, Rs` | 0x83sd | Subtract register from register |
| `AND Rd, Rs` | 0x87sd | Logical AND |
| `OR Rd, Rs` | 0x85sd | Logical OR |
| `XOR Rd, Rs` | 0x89sd | Logical XOR |
| `JP addr` | 0x5E08 + addr | Unconditional jump |
| `HALT` | 0x7A00 | Halt processor |
| `IN Rd, port` | 0x3Bd4 + port | Input word from I/O port (direct) |
| `OUT port, Rs` | 0x3Bs6 + port | Output word to I/O port (direct) |
| `IN Rd, @Rs` | 0x3Dds | Input word (register indirect) |
| `OUT @Rd, Rs` | 0x3Fds | Output word (register indirect) |

Note: `d` = destination register (0-F), `s` = source register (0-F)

## I/O Ports

The test harness provides simulated I/O ports:

| Port | Read | Write |
|------|------|-------|
| 0x0000 | Returns io_data_reg (initial: 0x1234) | Sets io_data_reg |
| 0x0002 | Returns io_ctrl_reg | Sets io_ctrl_reg |
| 0x0010 | Returns 0xAA00 | - |
| 0x0011 | Returns 0x0055 | - |
| 0x0020 | Returns sio_data_reg (special I/O) | Sets sio_data_reg |

## Python Test Script

A Python script `test_harness.py` is provided for convenient testing.

### Requirements

```bash
pip install pyserial
```

### Usage

```bash
python test_harness.py [port] [command...]
```

**Arguments:**
- `port` - Serial port (default: `/dev/ttyUSB0`, macOS: `/dev/cu.usbserial-*`)
- `command` - Optional command or test name

### Examples

```bash
# Interactive mode
python test_harness.py /dev/ttyUSB0

# macOS
python test_harness.py /dev/cu.usbserial-1420

# Run all built-in tests
python test_harness.py /dev/ttyUSB0 all

# Run specific test
python test_harness.py /dev/ttyUSB0 test_add
python test_harness.py /dev/ttyUSB0 test_sub

# Send single command
python test_harness.py /dev/ttyUSB0 ST
```

### Interactive Mode Commands

When run without a command, the script enters interactive mode:

```
> ST           # Check status (H=halted/reset, R=running)
> RS           # Reset CPU
> MT           # Run memory test (should return PASS)
> WR 0 1234    # Write R0 initial value = 0x1234
> WR 1 5678    # Write R1 initial value = 0x5678
> WM 0200 8110 # Write ADD R0,R1 instruction at 0x0200
> WM 0202 5E08 # Write JP instruction
> WM 0204 00C0 # Write jump target (dump routine)
> EX           # Execute (returns HALT when done)
> RR 0         # Read R0 result
> RR 1         # Read R1 result
> DA           # Dump all registers
> all          # Run all built-in tests
> quit         # Exit
```

### Built-in Tests

| Test | Description |
|------|-------------|
| `test_add` | ADD R0, R1: 0x1234 + 0x5678 = 0x68AC |
| `test_sub` | SUB R0, R1: 0x5678 - 0x1234 = 0x4444 |
| `test_and` | AND R0, R1: 0xFF00 & 0x0F0F = 0x0F00 |
| `test_or` | OR R0, R1: 0xFF00 \| 0x00FF = 0xFFFF |
| `test_xor` | XOR R0, R1: 0xAAAA ^ 0x5555 = 0xFFFF |

### Python API

```python
from test_harness import Z8000TestHarness

# Connect
harness = Z8000TestHarness('/dev/ttyUSB0')

# Low-level commands
harness.write_reg(0, 0x1234)      # WR 0 1234
harness.write_mem(0x0200, 0x8110) # WM 0200 8110
result = harness.execute()        # EX
value = harness.read_reg(0)       # RR 0

# High-level test
passed, msg = harness.run_test(
    regs={0: 0x1234, 1: 0x5678},   # Initial register values
    code=[0x8110],                  # Instruction(s) to test
    expected_regs={0: 0x68AC}       # Expected results
)

harness.close()
```

## Building

### Bootstrap Assembly

The bootstrap and dump routines are written in Z8000 assembly:

```bash
make bootstrap
```

This assembles `src/bootstrap.s` using the GNU Z8000 toolchain (`z8k-coff-as`).

### Simulation

```bash
make sim
```

### View Waveforms

```bash
make wave
```

### FPGA Synthesis

Open `test_harness.gprj` in Gowin IDE to synthesize and program the design.

## Files

| File | Description |
|------|-------------|
| `src/test_harness_top.v` | Top-level module with CPU, memory, I/O ports |
| `src/test_harness_ctrl.v` | Serial command controller (UART protocol) |
| `src/gowin_dpb.v` | Gowin BRAM wrapper (SDPB primitives) |
| `src/uart_tx.v` | UART transmitter |
| `src/uart_rx.v` | UART receiver |
| `src/z8000_cpu.v` | Z8000 CPU core (copied from z8000_micro) |
| `src/uasm/output/microcode_rom.v` | CPU microcode ROM |
| `src/uasm/output/decode_rom.v` | CPU instruction decode ROM |
| `src/uasm/output/ucode_defs.v` | Microcode address definitions |
| `src/bootstrap.s` | Bootstrap/dump routine assembly source |
| `src/top.cst` | FPGA pin constraints |
| `src/test_harness_tb.v` | Simulation testbench |
| `test_harness.gprj` | Gowin EDA project file |
| `test_harness.py` | Python control script |
| `gen_bram_init.py` | Generate BRAM init from bootstrap binary |
| `Makefile` | Build targets |

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make sim` | Run Verilog simulation |
| `make wave` | Open GTKWave to view waveforms |
| `make bootstrap` | Assemble bootstrap code |
| `make clean` | Remove generated files |

## Troubleshooting

### Memory Test Fails

If `MT` returns `FAIL:xxxx`:
1. The BRAM may not be initialized correctly
2. Check that the design was synthesized with the latest `gowin_dpb.v`
3. Verify the FPGA programming completed successfully

### No UART Response

1. Check baud rate is 115200
2. Verify TX/RX pins (69/70 on Tang Nano 20K)
3. Check USB cable and serial port selection

### CPU Doesn't Halt

1. Verify test code ends with `JP 0x00C0`
2. Check for infinite loops in test code
3. Use `ST` to check if CPU is still running

## License

Same as parent Z8000_FPGA project.
