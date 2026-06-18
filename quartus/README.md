# Z8001 External Test Harness - Quartus Project

This is a Quartus project for testing an **external Z8001 CPU** using the same
test infrastructure as the Gowin-based z8000_test project.

Pin assignments and bus interface logic are based on the **M20FPGA** project.

## Target Hardware

- **FPGA**: Altera Cyclone IV EP4CE15F23C8 (QMTECH board)
- **CPU**: External Zilog Z8001 (40-pin DIP, segmented addressing mode)
- **Level Shifters**: 74LVC245 for 3.3V ↔ 5V translation

## Hardware Architecture (from M20FPGA)

```
                    +------------------+
                    |   Z8001 CPU      |
                    |   (5V, 40-pin)   |
                    +--------+---------+
                             |
            AD0-15, SN0-3, ST0-3, AS, DS, MREQ, R/W, B/W
                             |
                    +--------+---------+
                    |   74LVC245       |
                    |   Bus Buffers    |
                    |   (B=CPU, A=FPGA)|
                    +--------+---------+
                             |
        fbuscs (OE), fbusrd (DIR)      sramData[15:0]
                             |
    +------------------------+------------------------+
    |                        |                        |
    |              +---------+---------+              |
    |              |    CYCLONE IV     |              |
    |              |      FPGA         |              |
    |              |                   |              |
    |              |  - Z80 Harness    |              |
    |              |  - BRAM (8KB)     |              |
    |              |  - Trace Buffer   |              |
    |              |  - UART           |              |
    |              |  - I/O LED Latch  |              |
    |              +---------+---------+              |
    |                        |                        |
    |                   UART TXD/RXD                  |
    |                        |                        |
    +------------------------+------------------------+
```

## Bus Buffer Control (74LVC245)

The 74LVC245 buffers provide level shifting between 5V CPU and 3.3V FPGA:

| Pin | Signal | Value | Meaning |
|-----|--------|-------|---------|
| OE | `buf_oe_n` (fbuscs) | 0 | Always enabled |
| DIR | `buf_dir` (fbusrd) | 0 | B→A: CPU drives to FPGA |
| DIR | `buf_dir` (fbusrd) | 1 | A→B: FPGA drives to CPU |

**Direction Control Logic** (from M20FPGA):
```verilog
buf_dir = rw_n && bus_as_active && as_n;
```

- **Address phase** (AS active/low): `buf_dir=0` → CPU drives address
- **Write data phase** (rw_n=0): `buf_dir=0` → CPU drives data
- **Read data phase** (rw_n=1, AS inactive): `buf_dir=1` → FPGA drives data

`bus_as_active` continuously tracks raw AS state on `negedge clk` (matching
M20FPGA pattern), ensuring correct direction transitions each bus cycle.

## Project Structure

```
quartus/
├── z8001_ext_test.qpf          # Quartus project file
├── z8001_ext_test.qsf          # Pin assignments and source file list
├── z8001_ext_test.sdc          # Timing constraints
├── z8001_ext_test_top.v        # Top-level module (bus wiring, halt detect, instrumentation)
├── z8001_bus_external.v        # External Z8001 bus interface (sync, latch, buffer control)
├── trace_buffer_altera.v       # Bus trace capture (behavioral RAM, no Gowin SDPB)
├── z80_fw_ram_altera.v         # Altera altsyncram implementation of Z80 firmware RAM
├── ram16_altera.v              # Dual-port RAM (Altera altsyncram)
├── pll.v                       # PLL wrapper (replace with MegaWizard output)
├── z80_fw_echo.asm             # Z80 test runner firmware (pyz80 syntax)
├── z80_fw_minimal.py           # Z80 echo firmware generator (deprecated)
├── gen_mif.py                  # Binary-to-MIF converter
├── z80_fw.bin                  # Assembled firmware binary
├── z80_fw.hex                  # Firmware in hex format
├── z80_fw.mif                  # Firmware in Altera MIF format
├── Makefile                    # Build automation
└── README.md                   # This file
```

## Top-Level Architecture

The top module (`z8001_ext_test_top.v`) wires together:

- **Z8001 bus interface** (`z8001_bus_external`): 2-stage synchronizers, address
  latch on AS rising edge, buffer direction control, status latching
- **Dual-port BRAM** (8KB): Port A for Z80 harness, Port B for Z8001 CPU with
  byte write enables
- **Address decode**: `io_sel` for I/O cycles (ST=0010/0100), `ram_sel` for
  memory cycles. Data mux returns BRAM for memory, 0xFFFF for I/O reads.
- **Halt detection**: Opcode sniffing — latches `data_to_cpu` while DS is active,
  checks for HALT opcode (0x7A00) on first fetch (ST=1101) at DS rising edge
- **Instrumentation**: Cycle count (on 4MHz clock rising edges), fetch count
  (on AS falling + ST=1101), bus_active flag, cycle timeout
- **Trace buffer** (`trace_buffer_altera`): 1024-entry bus transaction capture,
  address-gated to test code area (>= 0x0200)
- **I/O LED latch**: Any Z8001 I/O write captures wdata; LED driven from bit 0
- **Z80 harness**: Full command interface over UART (same I/O port map as Gowin)

## Z80 Firmware

The firmware (`z80_fw_echo.asm`) is a self-contained test runner:

1. Writes Z8001 segmented reset vectors to BRAM (FCW=0x4000, PC=0x0200)
2. Writes test program at 0x0200: `LD R1,#1; OUT DA,R1,0x00FE; HALT`
3. Sets cycle limit (4,000,000 = ~1s at 4MHz)
4. Releases Z8001, polls for halt or timeout
5. Prints cycle count, fetch count, trace count
6. Dumps all trace entries (AAAA DDDD RBM format)
7. Waits for keypress, resets Z8001, re-runs

**Expected serial output:**
```
Z8001 Bus Test
HALT
CC=000000xx
FC=0004
TC=006
0202 0001 RWM
0204 3B16 RWM
0206 00FE RWM
00FE 0001 WWI
0208 7A00 RWM
DONE
```

## Pin Assignments (from M20FPGA)

### Z8001 CPU Interface

| Signal | Pin | Dir | Description |
|--------|-----|-----|-------------|
| z8k_clk | F1 | Out | 4 MHz CPU clock |
| z8k_reset | B17 | Out | CPU reset (0=reset, 1=run) |
| z8k_busreq_n | H2 | Out | Bus request |
| z8k_wait_n | J2 | Out | Wait state |
| z8k_nvi_n | F2 | Out | Non-vectored interrupt |
| z8k_vi_n | B2 | Out | Vectored interrupt |
| z8k_nmi_n | B3 | Out | NMI |
| z8k_st[3:0] | B1,C2,C1,D2 | In | Status lines |
| z8k_sn[3:0] | M1,N2,N1,R1 | In | Segment number |
| z8k_as_n | A8 | In | Address strobe |
| z8k_ds_n | A9 | In | Data strobe |
| z8k_bw_n | A7 | In | Byte/Word |
| z8k_mreq_n | A10 | In | Memory request |
| z8k_rw_n | A13 | In | Read/Write |

### Bus Buffer Control

| Signal | Pin | Dir | Description |
|--------|-----|-----|-------------|
| bus_buf_oe_n | R2 | Out | Buffer OE (active-low, always 0) |
| bus_buf_dir | P2 | Out | Buffer direction |

### Address/Data Bus (via SRAM data pins in M20FPGA)

| Signal | Pins | Description |
|--------|------|-------------|
| z8k_ad[7:0] | B7,B9,B13,B16,B15,B14,B10,B8 | AD bus low byte |
| z8k_ad[15:8] | E22,D22,C22,A20,A19,A18,A17,C21 | AD bus high byte |

### System

| Signal | Pin | Description |
|--------|-----|-------------|
| clk_50mhz | T2 | 50 MHz oscillator |
| rst_n | W13 | Reset button (active-low) |
| led | E4 | I/O LED (bit 0 of Z8001 I/O write data) |
| uart_rxd | B18 | Serial receive |
| uart_txd | B22 | Serial transmit |

## Clock Architecture

```
50 MHz oscillator (PIN_T2)
    │
    └─→ ALTPLL
           ├─→ 16 MHz (system clock - FPGA logic)
           └─→ 4 MHz  (CPU clock - z8k_clk output)
```

## Shared Code (from ../src/)

These modules are shared with the Gowin project:

- `uart_tx.v` / `uart_rx.v` - UART modules
- `tv80_official/` - TV80 Z80 core

Quartus-specific support modules:

- `z80_fw_ram_altera.v` - Altera altsyncram implementation used by shared `../src/z80_harness.v`
- `ram16_altera.v` - Dual-port BRAM with Altera altsyncram
- `trace_buffer_altera.v` - Trace buffer with behavioral RAM (no Gowin SDPB)

## Differences from Gowin Version

| Aspect | Gowin (Tang Nano 20K) | Quartus (Cyclone IV) |
|--------|----------------------|---------------------|
| CPU | Verilog Z8002 (internal) | Physical Z8001 (external) |
| Clock | 27MHz, /3.5 divider for ~3.86MHz | 50MHz PLL → 16MHz sys + 4MHz CPU |
| BRAM | Gowin DPB primitives | Altera altsyncram |
| Trace RAM | Gowin SDPB | Behavioral (Quartus infers BRAM) |
| Z80 RAM | Behavioral + $readmemh | Altera altsyncram + MIF init |
| Halt detect | Direct halt_n from CPU | Opcode sniffing (0x7A00 on ST=1101) |
| I/O ports | 12x16-bit register file | Single I/O LED latch (no read-back) |
| Firmware | Full command-based supervisor | Self-contained test runner |
| Bus interface | Direct CPU wires | 74LVC245 level shifters + synchronizers |

## Differences from M20FPGA

| Aspect | M20FPGA | This Project |
|--------|---------|--------------|
| Memory | 512KB external SRAM | 8KB FPGA BRAM |
| Purpose | Full M20 recreation | Test harness only |
| Peripherals | UART, Timer, SD, VGA, PS/2 | UART only |
| Control | Boot ROM | Z80 harness via UART |

## Sibling Projects: Internal (Soft-CPU) Test Harnesses

This directory also contains two additional Quartus projects that synthesize the
**Verilog `z8000_micro` soft CPU core** inside the FPGA instead of driving a
physical external Z8001. They share the same QMTECH board, PLL, Z80 harness,
trace buffer, BRAM, UART, and I/O port file as the external project.

| Project | Top Module | CPU Variant | Verilog Macros |
|---------|-----------|-------------|----------------|
| `z8002_int_test` | `z8002_int_test_top.v` | Z8002 (non-segmented) | `ACTIVE_BUS=1`, `ALTERA_BRAM=1` |
| `z8001_int_test` | `z8001_int_test_top.v` | Z8001 (segmented) | `Z8001_MODE=1`, `ACTIVE_BUS=1`, `ALTERA_BRAM=1` |

In both projects the external Z8001 socket is **disabled**: the CPU is held in
reset (`freset=0`), bus buffers are off (`fbuscs=1`), all Z8001-facing control
pins are driven inactive, and the `sramData` bus is declared as an input so the
FPGA never drives the level shifters.

### Shared vs. external project

The internal harnesses reuse the same support modules as `z8001_ext_test`:

- `pll.v`, `trace_buffer_altera.v`, `ram16_altera.v`, `z80_fw_ram_altera.v`
- `../src/z80_harness.v`
- `../src/uart_tx.v`, `../src/uart_rx.v`
- `../src/z8k_io_ports.v` — full 12×16-bit I/O port register file (Z80 ↔ Z8000),
  giving these projects the same I/O port map as the Gowin reference design
  (richer than the external project's single LED latch)
- `../src/boot_master.v` — Z80-only bootstrap master store (CPU cannot reach it)

The soft CPU itself comes from the `../z8000_micro/rtl/` submodule:
`z8000_cpu.v`, `z8000_biu.v`, `z8000_muldiv.v`, `decode_rom.v`, `microcode_rom.v`.

### Key implementation details (common to both)

- **CPU clocking**: the soft core runs at 16 MHz (`sys_clk`, PLL c0) instantiated
  with `BUS_DIVIDER=4`, so the bus phase advances every 4th clock (≈4 MHz bus
  rate). PLL c1 (4 MHz) only feeds the unused external `fclk` pin.
- **`ACTIVE_BUS`**: the core exposes split `ad_out` / `ad_in` / `ad_oe` signals
  (no internal tri-state). `ad_in = ad_oe ? ad_out : data_to_cpu`.
- **`ALTERA_BRAM`**: the microcode ROM is placed in M9K block RAM (≈3000 LUTs
  saved). The `SEARCH_PATH ..` assignment lets `altsyncram` resolve the hard-coded
  `z8000_micro/rtl/microcode_rom_z800{1,2}.mif` INIT_FILE path.
- **Halt detection**: direct `halt_n` from the core — no opcode sniffing needed
  (unlike the external project, which sniffs `0x7A00` on `ST=1101`).
- **Address/status latches**: address captured level-sensitively while `as_n` is
  low; status latched on the `AS` falling edge.
- **Instrumentation & trace**: identical cycle/fetch counters and 1024-entry
  trace buffer as the external project, clocked off the 4 MHz `bus_tick`.

### Z8001 vs. Z8002 internal differences

`z8001_int_test` adds the following over `z8002_int_test`:

- CPU compiled with `Z8001_MODE` (segmented addressing, RR14 stack, 8-byte PSA).
- A 7-bit segment number (`sn`) is latched from the core alongside the address.
- `sn[0]` extends the BRAM Port B address (`{sn[0], addr[11:0]}`), splitting the
  8 KB BRAM into two 4 KB segments — segment 0 at `0x0000–0x0FFF`, segment 1 at
  `0x1000–0x1FFF`. (`z8002_int_test` uses a flat `addr[12:0]`.)

### Building the internal projects

```bash
make firmware                       # Z80 firmware MIF (shared by all three projects)
```

Then open `z8002_int_test.qpf` or `z8001_int_test.qpf` in Quartus, generate/replace
the PLL as described below, and compile. Each project has its own
`.qsf` (source/pin/macro list) and `.sdc` (timing constraints).

## Building

### Prerequisites

- Quartus II 13.0+ or Quartus Prime
- Python 3 with `pyz80` assembler: `pip install pyz80`

### Firmware

```bash
make firmware   # Assemble z80_fw_echo.asm -> z80_fw.bin -> z80_fw.hex -> z80_fw.mif
```

### FPGA

1. Open `z8001_ext_test.qpf` in Quartus
2. Generate PLL using MegaWizard/IP Catalog:
   - Input: 50 MHz
   - Output c0: 16 MHz
   - Output c1: 4 MHz
3. Replace `pll.v` with generated PLL
4. Compile and program

### Serial Connection

- 115200 baud, 8N1
- Connect to the UART pins (urxd1/utxd1) via USB-serial adapter

## LED Status

Single LED driven by Z8001 I/O write data (bit 0):
- **OFF**: Z8001 hasn't executed an I/O write yet (or wrote 0)
- **ON**: Z8001 wrote data with bit 0 = 1 to any I/O address

## Notes

- The design uses FPGA BRAM instead of external SRAM (simpler for test harness)
- External SRAM chip selects held high (disabled)
- Only SN[3:0] are wired (sufficient for 16 segments)
- No wait states implemented (z8k_wait_n always high)
- Bus buffer always enabled (buf_oe_n always low)
- `freset` polarity: 0=reset, 1=run (matching original M20FPGA convention)
- Trace buffer address-gated: only captures bus cycles when executing code at >= 0x0200
- Halt detection uses data latching to avoid MREQ/DS synchronizer race condition
