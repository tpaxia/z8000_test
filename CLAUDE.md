# Z8000 Instruction Test Harness

FPGA-based test harness for a Z8000 CPU implementation using Tang Nano 20K (Gowin GW2AR-18C).

## Project Structure

- `src/` - Verilog source files
  - `test_harness_top.v` - Top-level module (CPU, memory, I/O ports, LED indicators)
  - `test_harness_ctrl.v` - Serial command controller (UART protocol, memory test)
  - `gowin_dpb.v` - Gowin BRAM wrapper using SDPB primitives
  - `uart_tx.v` / `uart_rx.v` - UART modules
  - `z8000_cpu.v` - Z8000 CPU core (copied from ../z8000_micro)
  - `uasm/output/` - Generated microcode files
    - `microcode_rom.v` - CPU microcode ROM
    - `decode_rom.v` - Instruction decode ROM
    - `ucode_defs.v` - Microcode address definitions
  - `bootstrap.s` - Bootstrap/dump routine Z8000 assembly source
  - `test_harness_tb.v` - Simulation testbench
  - `top.cst` - FPGA pin constraints
- `doc/` - Documentation
- `test_harness.gprj` - Gowin EDA project file
- `test_harness.py` - Python test script
- `gen_bram_init.py` - Generate BRAM init values from bootstrap binary
- `Makefile` - Build automation

## Build Commands

```bash
make sim        # Run Icarus Verilog simulation
make wave       # View VCD waveform in GTKWave
make bootstrap  # Assemble bootstrap code (requires z8k-coff-as)
make clean      # Clean build artifacts
```

## Key Details

- **Clock**: 27MHz system, ~4MHz CPU
- **Serial**: 115200 baud, 8N1
- **Memory**: 4KB BRAM (Gowin SDPB primitives)
- **Test code area**: 0x0200-0x0FFF
- **Register dump area**: 0x0090-0x00AF
- **Dump routine**: 0x00C0 (tests jump here when done)

## LED Indicators

| LED | Pin | Function |
|-----|-----|----------|
| led | 15 | Heartbeat (flashing) |
| led2 | 16 | CPU in reset |
| led3 | 17 | CPU running |
| led4 | 18 | CPU halted |

## Serial Protocol

Text commands over UART: `WR`, `RR`, `WM`, `RM`, `WB`, `RB`, `WF`, `RF`, `EX`, `RS`, `ST`, `MT`, `LH`, `DA`

Key commands:
- `RS` - Reset CPU (led2 ON)
- `ST` - Status (H=halted/reset, R=running)
- `MT` - Memory test (returns PASS or FAIL:xxxx)
- `EX` - Execute until halt
- `WM addr data` - Write memory
- `RM addr` - Read memory

## Memory Architecture

Uses `ifdef SIMULATION` to switch between:
- **Simulation**: Behavioral RAM arrays with initial block
- **Synthesis**: Gowin SDPB primitives with INIT_RAM parameters

Bootstrap and dump routines are pre-initialized in BRAM.

## I/O Ports

Simulated I/O at ports 0x0000, 0x0002, 0x0010, 0x0011, 0x0020 for testing IN/OUT instructions.

See README.md for full documentation.
