//============================================================================
// Z8001 Internal Test Harness - Top Level Module
// Target: Altera Cyclone IV (Quartus project)
//
// Synthesizes the Verilog Z8000 CPU core in Z8001 (segmented) mode on the
// Cyclone IV FPGA, using the same QMTECH board as the z8002_int_test project.
//
// The external Z8001 CPU is held in reset with bus buffers disabled
// and all Z8001-facing pins driven to safe states (mirrors z8002_int_test).
//
// Key differences from z8002_int_test:
// - CPU core compiled with Z8001_MODE (segmented, RR14 stack, 8-byte PSA)
// - ACTIVE_BUS (split ad_out/ad_in/ad_oe, no internal tri-state bus)
// - 7-bit segment number (sn) latched from CPU; sn[0] extends BRAM address
//   into two 4KB segments (segment 0: 0x0000-0x0FFF, segment 1: 0x1000-0x1FFF)
// - ALTERA_BRAM: microcode ROM in M9K block RAM (~3000 LUTs saved)
//============================================================================

module z8001_int_test_top (
    // System
    input  wire        clk,             // 50 MHz oscillator (T2)
    input  wire        n_reset,         // Active-low reset button (W13)

    // Serial Port 1 (UART)
    input  wire        urxd1,           // UART RX from external (B18)
    output wire        utxd1,           // UART TX to external (B22)

    // LED
    output wire        driveLED,        // Activity LED (E4)

    // External SRAM control (disabled)
    output wire        n_sRamCS0,       // SRAM chip select 0 (B5)
    output wire        n_sRamCS1,       // SRAM chip select 1 (B6)
    output wire        n_sRamOE,        // SRAM output enable (C4)
    output wire        n_sRamWE,        // SRAM write enable (E1)

    // External Z8001 CPU control outputs (driven to safe states)
    output wire        fclk,            // CPU clock 4MHz (F1)
    output wire        freset,          // CPU reset, active-high (B17) - held in reset
    output wire        fbreq,           // Bus request (H2)
    output wire        fwait,           // Wait state (J2)
    output wire        fnvi,            // Non-vectored interrupt (F2)
    output wire        fvi,             // Vectored interrupt (B2)
    output wire        fnmi,            // NMI (B3)

    // External Z8001 bus buffer control
    output wire        fbuscs,          // Bus buffer OE, active-low (R2) - disabled
    output wire        fbusrd,          // Bus buffer direction (P2)

    // External Z8001 CPU inputs (disconnected CPU, pulled up)
    input  wire        fas,             // Address strobe (A8)
    input  wire        fds,             // Data strobe (A9)
    input  wire        fbw,             // Byte/Word (A7)
    input  wire        fmreq,           // Memory request (A10)
    input  wire        frw,             // Read/Write (A13)
    input  wire [3:0]  fst,             // Status ST0-ST3 (D2,C1,C2,B1)
    input  wire [3:0]  fsn,             // Segment SN0-SN3 (R1,N1,N2,M1)

    // External AD bus (buffers disabled - FPGA keeps as input)
    input  wire [15:0] sramData
);

    //------------------------------------------------------------------------
    // Parameters
    //------------------------------------------------------------------------
    parameter CLK_FRE   = 16;         // 16 MHz system clock (sys_clk = PLL c0)
    parameter UART_BAUD = 115200;

    //------------------------------------------------------------------------
    // Clock Generation (PLL)
    //------------------------------------------------------------------------
    wire clk_16mhz;     // 16 MHz system clock
    wire clk_4mhz;      // 4 MHz CPU clock
    wire pll_locked;

    pll pll_inst (
        .inclk0(clk),
        .c0(clk_16mhz),     // 16 MHz
        .c1(clk_4mhz),      // 4 MHz
        .locked(pll_locked)
    );

    wire sys_clk = clk_16mhz;

    //------------------------------------------------------------------------
    // CPU clocking: CPU runs at 16 MHz (sys_clk) with BUS_DIVIDER=4 so bus
    // phase advances every 4th clk (= 4 MHz bus rate). This matches the
    // validated M20FPGA_soft configuration. PLL c1 (clk_4mhz) is only used
    // for the external Z8001 fclk pin, not the soft core.
    //------------------------------------------------------------------------

    //------------------------------------------------------------------------
    // Reset Generation
    //------------------------------------------------------------------------
    reg [19:0] reset_cnt = 0;
    reg        sys_rst_n = 0;

    always @(posedge sys_clk or negedge n_reset) begin
        if (!n_reset) begin
            reset_cnt <= 0;
            sys_rst_n <= 0;
        end else if (!pll_locked) begin
            reset_cnt <= 0;
            sys_rst_n <= 0;
        end else if (reset_cnt < 20'hFFFFF) begin
            reset_cnt <= reset_cnt + 1;
            sys_rst_n <= 0;
        end else begin
            sys_rst_n <= 1;
        end
    end

    //------------------------------------------------------------------------
    // External SRAM - DISABLED
    //------------------------------------------------------------------------
    assign n_sRamCS0 = 1'b1;
    assign n_sRamCS1 = 1'b1;
    assign n_sRamOE  = 1'b1;
    assign n_sRamWE  = 1'b1;

    //------------------------------------------------------------------------
    // External Z8001 - DISABLED
    // Hold in reset, disable bus buffers, drive control pins inactive.
    //------------------------------------------------------------------------
    assign fclk    = clk_4mhz;          // Keep clock running (harmless)
    assign freset  = 1'b0;              // Z8001 freset active-low: 0 = held in reset
    assign fbreq   = 1'b1;              // No bus request (inactive)
    assign fwait   = 1'b1;              // No wait (inactive)
    assign fnvi    = 1'b1;              // No NVI (inactive)
    assign fvi     = 1'b1;              // No VI (inactive)
    assign fnmi    = 1'b1;              // No NMI (inactive)
    assign fbuscs  = 1'b1;              // Bus buffers OE DISABLED (active-low)
    assign fbusrd  = 1'b0;              // Direction don't-care (buffers disabled)

    //------------------------------------------------------------------------
    // Internal Z8001 CPU (ACTIVE_BUS variant)
    //------------------------------------------------------------------------
    wire z8k_rst_n;                     // From Z80 harness

    wire [15:0] ad_out;
    wire        ad_oe;
    reg  [15:0] data_to_cpu;            // mux result (RAM / IO / pull-ups)

    // With ACTIVE_BUS, the CPU drives ad_out when ad_oe=1 (address+write)
    // and reads ad_in when ad_oe=0 (read phase). Loop ad_out back when the
    // CPU is driving so the input mux is clean; otherwise deliver read data.
    wire [15:0] ad_in = ad_oe ? ad_out : data_to_cpu;

    wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
    wire [3:0]  cpu_st;
    wire [6:0]  cpu_sn;
    wire        cpu_halt_n;
    wire        cpu_busack_n, cpu_ns;

    z8000_cpu #(.BUS_DIVIDER(4)) cpu (
        .clk        (sys_clk),
        .rst_n      (z8k_rst_n),
        .ad_out     (ad_out),
        .ad_in      (ad_in),
        .ad_oe      (ad_oe),
        .as_n       (cpu_as_n),
        .ds_n       (cpu_ds_n),
        .rw_n       (cpu_rw_n),
        .mreq_n     (cpu_mreq_n),
        .b_w_n      (cpu_bw_n),
        .st         (cpu_st),
        .sn         (cpu_sn),
        .wait_n     (1'b1),
        .busreq_n   (1'b1),
        .busack_n   (cpu_busack_n),
        .nmi_n      (1'b1),
        .vi_n       (1'b1),
        .nvi_n      (1'b1),
        .n_s        (cpu_ns),
        .halt_n     (cpu_halt_n)
    );

    // Write data from CPU is ad_out during data phase (ad_oe=1, ds_n=0)
    wire [15:0] z8k_wdata = ad_out;

    //------------------------------------------------------------------------
    // Address Latch
    // Level-sensitive capture while AS_n is low.
    // Sampled at 16MHz for minimum latency.
    //------------------------------------------------------------------------
    reg [15:0] z8k_addr;

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            z8k_addr <= 16'd0;
        else if (~cpu_as_n)
            z8k_addr <= ad_out;
    end

    //------------------------------------------------------------------------
    // Segment Number Latch (capture while AS_n low, same as address)
    // Only sn[0] is used to split the 8KB BRAM; rest are still latched
    // for the trace buffer / future use.
    //------------------------------------------------------------------------
    reg [6:0] sn_latched;
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            sn_latched <= 7'd0;
        else if (~cpu_as_n)
            sn_latched <= cpu_sn;
    end

    //------------------------------------------------------------------------
    // Status Latch (ST valid on AS falling edge only)
    //------------------------------------------------------------------------
    reg [3:0] st_latched;
    always @(posedge sys_clk) begin
        if (!sys_rst_n)
            st_latched <= 4'b0;
        else if (as_falling)
            st_latched <= cpu_st;
    end

    //------------------------------------------------------------------------
    // Address Decode
    //------------------------------------------------------------------------
    wire io_std_sel = (st_latched == 4'b0010);   // Standard I/O (ST=0010)
    wire io_spc_sel = (st_latched == 4'b0011);   // Special I/O (ST=0011)
    wire io_sel  = io_std_sel || io_spc_sel;
    wire ram_sel = ~cpu_mreq_n && ~io_sel;

    // I/O port address match: Z8000 addresses 0x0100-0x010A
    wire io_port_match = io_sel && (z8k_addr[15:4] == 12'h010);
    wire [3:0] z8k_io_reg_sel = z8k_addr[3:1] + (io_spc_sel ? 4'd6 : 4'd0);

    //------------------------------------------------------------------------
    // UART
    //------------------------------------------------------------------------
    wire [7:0]  uart_tx_data, uart_rx_data;
    wire        uart_tx_valid, uart_tx_ready, uart_rx_valid, uart_rx_ready;

    uart_tx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_tx_inst (
        .clk(sys_clk),
        .rst_n(sys_rst_n),
        .tx_data(uart_tx_data),
        .tx_data_valid(uart_tx_valid),
        .tx_data_ready(uart_tx_ready),
        .tx_pin(utxd1)
    );

    uart_rx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_rx_inst (
        .clk(sys_clk),
        .rst_n(sys_rst_n),
        .rx_data(uart_rx_data),
        .rx_data_valid(uart_rx_valid),
        .rx_data_ready(uart_rx_ready),
        .rx_pin(urxd1)
    );

    //------------------------------------------------------------------------
    // Instrumentation (Cycle/Fetch Counting)
    // Clears on z8k_rst_n rising edge (reset release = new execution)
    //------------------------------------------------------------------------
    reg        bus_active;
    reg [31:0] cycle_count;
    reg [15:0] fetch_count;
    reg        prev_as_n;
    reg [1:0]  bus_tick_div;
    reg        counting;
    reg        cycle_timeout;
    reg [31:0] instr_cycle_count;
    wire [31:0] z8k_cycle_limit;

    reg z8k_rst_n_prev;
    always @(posedge sys_clk) z8k_rst_n_prev <= z8k_rst_n;
    wire z8k_start = z8k_rst_n && !z8k_rst_n_prev;

    wire as_falling = prev_as_n && ~cpu_as_n;
    wire opcode_fetch = as_falling && (cpu_st == 4'b1101);
    // Bus-rate tick (4 MHz at sys_clk=16MHz, matches BUS_DIVIDER=4). One sys_clk
    // pulse every 4 sys_clks - used as the "Z8000 clock" for cycle counting so
    // CC/FC values stay comparable to the BUS_DIVIDER=1 z8002 harness.
    wire bus_tick = (bus_tick_div == 2'd3);

    always @(posedge sys_clk) begin
        if (z8k_start) begin
            bus_active <= 1'b0;
            cycle_count <= 32'd0;
            fetch_count <= 16'd0;
            prev_as_n <= 1'b1;
            bus_tick_div <= 2'd0;
            counting <= 1'b1;
            cycle_timeout <= 1'b0;
            instr_cycle_count <= 32'd0;
        end else begin
            prev_as_n <= cpu_as_n;
            bus_tick_div <= bus_tick_div + 1'b1;

            if (as_falling && !bus_active)
                bus_active <= 1'b1;

            if (!cpu_halt_n)
                counting <= 1'b0;

            if (counting && cpu_halt_n && bus_tick)
                cycle_count <= cycle_count + 1'b1;

            if (counting && cpu_halt_n && opcode_fetch)
                fetch_count <= fetch_count + 1'b1;

            if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit))
                cycle_timeout <= 1'b1;

            if (trace_active && bus_tick)
                instr_cycle_count <= instr_cycle_count + 1'b1;
        end
    end

    //------------------------------------------------------------------------
    // Trace Buffer
    //------------------------------------------------------------------------
    wire [9:0]  trace_rd_addr;
    wire [35:0] trace_rd_data;
    wire [9:0]  trace_wr_count;
    wire        trace_active;

    wire [15:0] trace_data = cpu_rw_n ? data_to_cpu : z8k_wdata;

    trace_buffer_altera trace (
        .clk        (sys_clk),
        .rst_n      (sys_rst_n),
        .z8k_rst_n  (z8k_rst_n),
        .z8k_addr   (z8k_addr),
        .z8k_data   (trace_data),
        .z8k_as_n   (cpu_as_n),
        .z8k_ds_n   (cpu_ds_n),
        .z8k_rw_n   (cpu_rw_n),
        .z8k_bw_n   (cpu_bw_n),
        .z8k_mreq_n (cpu_mreq_n),
        .z8k_st     (st_latched),
        .rd_addr    (trace_rd_addr),
        .rd_data    (trace_rd_data),
        .wr_count   (trace_wr_count),
        .trace_active(trace_active)
    );

    //------------------------------------------------------------------------
    // Z80 Harness Controller
    //------------------------------------------------------------------------
    wire        z8k_mem_we;
    wire [14:0] z80_addr;
    wire [15:0] z8k_mem_wdata;
    wire [15:0] z8k_mem_rdata;

    wire [3:0]  z80_io_reg_sel;
    wire [7:0]  z80_io_wbyte;
    wire [15:0] z80_io_rdata;
    wire        z80_io_wr_lo;
    wire        z80_io_wr_hi;

    wire [15:0] z8k_io_rdata;

    z80_harness z80 (
        .clk            (sys_clk),
        .rst_n          (sys_rst_n),
        .uart_rx_data   (uart_rx_data),
        .uart_rx_valid  (uart_rx_valid),
        .uart_rx_ready  (uart_rx_ready),
        .uart_tx_data   (uart_tx_data),
        .uart_tx_valid  (uart_tx_valid),
        .uart_tx_ready  (uart_tx_ready),
        .z8k_rst_n      (z8k_rst_n),
        .z8k_halt_n     (cpu_halt_n),
        .z8k_st         (cpu_st),
        .z8k_mem_we     (z8k_mem_we),
        .z80_addr       (z80_addr),
        .z8k_mem_wdata  (z8k_mem_wdata),
        .z8k_mem_rdata  (z8k_mem_rdata),
        .z8k_bus_active (bus_active),
        .z8k_cycle_count(cycle_count),
        .z8k_fetch_count(fetch_count),
        .z8k_cycle_limit(z8k_cycle_limit),
        .z8k_cycle_timeout(cycle_timeout),
        .trace_rd_addr  (trace_rd_addr),
        .trace_rd_data  (trace_rd_data),
        .trace_wr_count (trace_wr_count),
        .io_port_reg_sel(z80_io_reg_sel),
        .io_port_wbyte  (z80_io_wbyte),
        .io_port_rdata  (z80_io_rdata),
        .io_port_wr_lo  (z80_io_wr_lo),
        .io_port_wr_hi  (z80_io_wr_hi),
        .z8k_instr_cycle_count(instr_cycle_count),
        .z80_alive      ()
    );

    //------------------------------------------------------------------------
    // Dual-Port BRAM (8KB)
    // Port A: Z80 harness (load/read test code) - flat 13-bit address
    // Port B: Z8001 CPU (fetch/execute) - {sn[0], addr[11:0]} = 2x4KB segments
    //------------------------------------------------------------------------

    // Z8001 write logic - level-based (internal CPU, no synchronizer delay)
    wire z8k_ram_write = ram_sel && ~cpu_rw_n && ~cpu_ds_n;
    // b_w_n polarity per z8000_biu.v: 0=word, 1=byte.
    wire z8k_we_hi = z8k_ram_write && (~cpu_bw_n || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (~cpu_bw_n ||  z8k_addr[0]);

    wire [15:0] z80_rd_data;
    wire [15:0] z8k_rd_data;

    ram16_altera bram (
        // Port A - Z80 harness
        .clka    (sys_clk),
        .wea_hi  (z8k_mem_we),
        .wea_lo  (z8k_mem_we),
        .addra   (z80_addr[12:0]),
        .dina    (z8k_mem_wdata),
        .douta   (z80_rd_data),
        // Port B - Z8001 CPU with segment bit
        .clkb    (sys_clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
        .addrb   ({sn_latched[0], z8k_addr[11:0]}),
        .dinb    (z8k_wdata),
        .doutb   (z8k_rd_data)
    );

    assign z8k_mem_rdata = z80_rd_data;

    //------------------------------------------------------------------------
    // I/O Port Registers
    //------------------------------------------------------------------------
    wire z8k_io_wr = io_port_match && ~cpu_rw_n && ~cpu_ds_n;

    z8k_io_ports io_ports (
        .clk           (sys_clk),
        .rst_n         (sys_rst_n),
        .z8k_reg_sel   (z8k_io_reg_sel),
        .z8k_wdata     (z8k_wdata),
        .z8k_rdata     (z8k_io_rdata),
        .z8k_wr        (z8k_io_wr),
        .z8k_bw_n      (cpu_bw_n),
        .z8k_addr_lsb  (z8k_addr[0]),
        .z80_reg_sel   (z80_io_reg_sel),
        .z80_wbyte     (z80_io_wbyte),
        .z80_rdata     (z80_io_rdata),
        .z80_wr_lo     (z80_io_wr_lo),
        .z80_wr_hi     (z80_io_wr_hi)
    );

    // Z8001 data bus mux
    always @(*) begin
        if (ram_sel)
            data_to_cpu = z8k_rd_data;
        else if (io_port_match)
            data_to_cpu = z8k_io_rdata;
        else
            data_to_cpu = 16'hFFFF;
    end

    //------------------------------------------------------------------------
    // I/O LED Latch
    //------------------------------------------------------------------------
    reg [15:0] io_led_reg;
    wire io_write = io_sel && ~cpu_rw_n && ~cpu_ds_n;

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            io_led_reg <= 16'h0000;
        else if (io_write)
            io_led_reg <= z8k_wdata;
    end

    assign driveLED = io_led_reg[0];

endmodule
