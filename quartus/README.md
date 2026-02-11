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

## Project Structure

```
quartus/
├── z8001_ext_test.qpf          # Quartus project file
├── z8001_ext_test.qsf          # Pin assignments (from M20FPGA)
├── z8001_ext_test.sdc          # Timing constraints
├── z8001_ext_test_top.v        # Top-level module
├── z8001_bus_external.v        # External Z8001 bus interface
├── ram16_altera.v              # Dual-port RAM (Altera altsyncram)
├── pll.v                       # PLL wrapper (replace with MegaWizard output)
└── README.md                   # This file
```

## Pin Assignments (from M20FPGA)

### Z8001 CPU Interface

| Signal | Pin | Dir | Description |
|--------|-----|-----|-------------|
| z8k_clk | F1 | Out | 4 MHz CPU clock |
| z8k_reset | B17 | Out | CPU reset (active-high) |
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

### Address/Data Bus (accent SRAM data pins in M20FPGA)

| Signal | Pins | Description |
|--------|------|-------------|
| z8k_ad[7:0] | B7,B9,B13,B16,B15,B14,B10,B8 | AD bus low byte |
| z8k_ad[15:8] | E22,D22,C22,A20,A19,A18,A17,C21 | AD bus high byte |

### System

| Signal | Pin | Description |
|--------|-----|-------------|
| clk_50mhz | T2 | 50 MHz oscillator |
| rst_n | W13 | Reset button (active-low) |
| led | E4 | Status LED |
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

- `z80_harness.v` - Z80 supervisor with UART command interface
- `uart_tx.v` / `uart_rx.v` - UART modules
- `trace_buffer.v` - Bus trace capture
- `tv80_official/` - TV80 Z80 core

## Differences from M20FPGA

| Aspect | M20FPGA | This Project |
|--------|---------|--------------|
| Memory | 512KB external SRAM | 8KB FPGA BRAM |
| Purpose | Full M20 recreation | Test harness only |
| Peripherals | UART, Timer, SD, VGA, PS/2 | UART only |
| Control | Boot ROM | Z80 harness via UART |

## Building

1. Open `z8001_ext_test.qpf` in Quartus II 13.0+ or Quartus Prime
2. Generate PLL using MegaWizard/IP Catalog:
   - Input: 50 MHz
   - Output c0: 16 MHz
   - Output c1: 4 MHz
3. Replace `pll.v` with generated PLL
4. Compile and program

## Serial Protocol

Same as Gowin version - see main project README.md.

Key commands:
- `RS` - Reset Z8001
- `ST` - Status
- `EX` - Execute until halt
- `WMaaaaxxxx` - Write memory word
- `RMaaaa` - Read memory word
- `TC` - Trace count
- `TR` - Dump trace entries

## LED Status

Single LED shows system state:
- **Fast blink**: Z8001 in reset
- **Slow blink**: Z8001 running
- **Solid on**: Z8001 halted

## Notes

- The design uses FPGA BRAM instead of external SRAM (simpler for test harness)
- Only SN[3:0] are wired (sufficient for 16 segments)
- No wait states implemented (z8k_wait_n always high)
- Bus buffer always enabled (buf_oe_n always low)
