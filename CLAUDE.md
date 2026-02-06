# Z8000 Instruction Test Harness

FPGA-based test harness for a Z8000 CPU implementation using Tang Nano 20K (Gowin GW2AR-18C).

## Project Structure

- `rtl/` - Z8000 CPU core (copied from ../z8000_micro)
  - `z8000_cpu.v` - Main CPU module
  - `microcode_rom.v` - CPU microcode ROM
  - `decode_rom.v` - Instruction decode ROM
  - `ucode_defs.v` - Microcode address definitions
- `src/` - Verilog source files
  - `z8000_test_harness_top.v` - Top-level module (bus interface, dual-port memory, trace buffer)
  - `z8000_bus_fpga.v` - Z8000 bus interface (CPU, ~4MHz clock divider, address latch)
  - `z80_harness.v` - Z80 harness controller (TV80 + I/O ports)
  - `ram16.v` - Behavioral dual-port RAM (simulation)
  - `ram16_gowin.v` - Gowin DPB RAM (synthesis, includes bram_init.vh)
  - `gowin_dpb/` - Gowin true dual-port BRAM IP (4Kx8, WRITE_MODE=01)
  - `gowin_sdpb/` - Gowin semi dual-port BRAM IP (trace buffer)
  - `trace_buffer.v` - Bus trace capture buffer (1024 entries)
  - `uart_tx.v` / `uart_rx.v` - UART modules
  - `bootstrap.s` - Bootstrap/dump routine Z8000 assembly source
  - `z80_fw.asm` - Z80 supervisor firmware
  - `z8000_test_harness_tb.v` - Z80-only simulation testbench
  - `z8000_full_tb.v` - Full system testbench (Z8000 + BRAM, no UART)
  - `top.cst` - FPGA pin constraints
- `scripts/` - Build scripts
  - `gen_fw_hex.py` - Z80 firmware hex generator
  - `gen_bootstrap_inc.py` - Bootstrap to Z80 include converter
  - `gen_bram_init.py` - Generate BRAM init values for synthesis
- `test_harness.py` - Python test/control script
- `z8000_test_harness.gprj` - Gowin EDA project file
- `Makefile` - Build automation

## Build Commands

```bash
make firmware   # Assemble Z80 firmware (z80_fw.asm -> z80_fw.bin/hex)
make bootstrap  # Assemble Z8000 bootstrap code (requires z8k-coff-as)
make bram-init  # Generate BRAM init files for synthesis (bram_init.vh)
make sim        # Run Z80 harness simulation
make sim-full   # Run full system simulation with Z8000 CPU
make wave       # View VCD waveform in GTKWave
make clean      # Clean build artifacts
```

## Key Details

- **Clock**: 27MHz system clock; Z8000 runs at ~3.86MHz (divided from 27MHz)
- **Serial**: 115200 baud, 8N1
- **Memory**: 8KB true dual-port BRAM (Gowin DPB), Port A = Z80, Port B = Z8000
- **Reset**: Debounced rst_n for Z80; z8k_rst_n (Z80-controlled via port 0x14) for Z8000
- **Test code area**: 0x0200-0x0FFF
- **Register dump area**: 0x0090-0x00AF
- **Dump routine**: 0x00C0 (tests jump here when done)

## Serial Protocol

Text commands over UART (no spaces between command and arguments):
`WRnxxxx`, `RRn`, `WMaaaaxxxx`, `RMaaaa`, `EX`, `RS`, `ST`, `MT`, `DA`, `DB`, `DP`,
`INIT`, `TOxxxxxxxx`, `CC`, `FC`, `TC`, `TR`, `TRnnn`

Key commands:
- `RS` - Reset CPU
- `ST` - Status (shows ports 0x14, 0x15, Z8000 ST, and H/R indicator)
- `EX` - Execute until halt (returns HALT, TOUT, or NRST)
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
- **Simulation**: Behavioral RAM arrays (`ram16.v`)
- **Synthesis**: Gowin DPB primitives with `include "bram_init.vh"` (`ram16_gowin.v`)

See README.md for full documentation.
