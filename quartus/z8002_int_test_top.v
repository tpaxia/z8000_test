//============================================================================
// Z8002 Internal Test Harness - Top Level Module
// Target: Altera Cyclone IV (Quartus project)
//
// Synthesizes the Verilog Z8002 CPU core on the Cyclone IV FPGA,
// using the same QMTECH board as the Z8001 external test project.
//
// The external Z8001 CPU is held in reset with bus buffers disabled
// and all Z8001-facing pins driven to safe states.
//
// Features:
// - Internal Z8002 CPU core (z8000_cpu)
// - 8KB dual-port BRAM (Port A: Z80, Port B: Z8002)
// - I/O LED latch
// - Direct halt_n from CPU (no opcode sniffing needed)
// - Cycle/fetch counting instrumentation
// - Bus trace capture buffer (1024 entries, address-gated)
//============================================================================

module z8002_int_test_top (
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

    // Z8001 CPU control outputs (directly directly driven to safe states)
    output wire        fclk,            // CPU clock 4MHz (F1) - still driven
    output wire        freset,          // CPU reset, active-high (B17) - held in reset
    output wire        fbreq,           // Bus request (H2)
    output wire        fwait,           // Wait state (J2)
    output wire        fnvi,            // Non-vectored interrupt (F2)
    output wire        fvi,             // Vectored interrupt (B2)
    output wire        fnmi,            // NMI (B3)

    // Z8001 bus buffer control
    output wire        fbuscs,          // Bus buffer OE, active-low (R2) - disabled
    output wire        fbusrd,          // Bus buffer direction (P2)

    // Z8001 CPU inputs (directly directly directly directly directly directly driven as inputs from disconnected CPU)
    input  wire        fas,             // Address strobe (A8)
    input  wire        fds,             // Data strobe (A9)
    input  wire        fbw,             // Byte/Word (A7)
    input  wire        fmreq,           // Memory request (A10)
    input  wire        frw,             // Read/Write (A13)
    input  wire [3:0]  fst,             // Status ST0-ST3 (D2,C1,C2,B1)
    input  wire [3:0]  fsn,             // Segment SN0-SN3 (R1,N1,N2,M1)

    // Z8001 AD bus (directly directly directly directly directly directly directly directly via 74LVC245 - buffers disabled, directly directly directly FPGA does not drive)
    input  wire [15:0] sramData         // Changed to input - FPGA never drives this
);

    //------------------------------------------------------------------------
    // Parameters
    //------------------------------------------------------------------------
    parameter CLK_FRE   = 16;         // 16MHz system clock
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
    // Derived 4MHz CPU Clock (divide-by-4 from 16MHz)
    // Keeps CPU in the same clock domain as the rest of the design.
    // PLL c1 (clk_4mhz) is only used for external Z8001 fclk pin.
    //------------------------------------------------------------------------
    reg [1:0] cpu_clk_div;
    reg       z8k_cpu_clk;

    always @(posedge sys_clk) begin
        if (!pll_locked) begin
            cpu_clk_div <= 2'd0;
            z8k_cpu_clk <= 1'b0;
        end else begin
            if (cpu_clk_div == 2'd1) begin
                cpu_clk_div <= 2'd0;
                z8k_cpu_clk <= ~z8k_cpu_clk;
            end else begin
                cpu_clk_div <= cpu_clk_div + 1'b1;
            end
        end
    end

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
    // The sramData bus is declared as input so FPGA pins are high-Z.
    // fas/fds/fbw/fmreq/frw/fst/fsn are inputs (CPU can't drive with
    // buffers disabled anyway).
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
    // Internal Z8002 CPU
    //------------------------------------------------------------------------
    wire z8k_rst_n;                      // From Z80 harness

    wire [15:0] ad_bus;
    wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
    wire [3:0]  cpu_st;
    wire        cpu_halt_n;
    wire        cpu_busack_n, cpu_ns;

    // Read data driven onto AD bus during CPU read cycles
    reg  [15:0] data_to_cpu;
    assign ad_bus = (cpu_rw_n && ~cpu_ds_n) ? data_to_cpu : 16'bz;

    z8000_cpu cpu (
        .clk        (z8k_cpu_clk),
        .rst_n      (z8k_rst_n),
        .ad         (ad_bus),
        .as_n       (cpu_as_n),
        .ds_n       (cpu_ds_n),
        .rw_n       (cpu_rw_n),
        .mreq_n     (cpu_mreq_n),
        .b_w_n      (cpu_bw_n),
        .st         (cpu_st),
        .wait_n     (1'b1),
        .busreq_n   (1'b1),
        .busack_n   (cpu_busack_n),
        .nmi_n      (1'b1),
        .vi_n       (1'b1),
        .nvi_n      (1'b1),
        .n_s        (cpu_ns),
        .halt_n     (cpu_halt_n)
    );

    // Write data from CPU
    wire [15:0] z8k_wdata = ad_bus;

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
            z8k_addr <= ad_bus;
    end

    //------------------------------------------------------------------------
    // Address Decode
    //------------------------------------------------------------------------
    wire io_std_sel = (cpu_st == 4'b0010);   // Standard I/O (ST=0010)
    wire io_spc_sel = (cpu_st == 4'b0011);   // Special I/O (ST=0011)
    wire io_sel  = io_std_sel || io_spc_sel;
    wire ram_sel = ~cpu_mreq_n && ~io_sel;

    // I/O port address match: Z8000 addresses 0x0100-0x010A
    wire io_port_match = io_sel && (z8k_addr[15:4] == 12'h010);
    // Register index: addr[3:1] (0-5) + 6 if special I/O
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
    reg        prev_cpu_clk;
    reg        counting;
    reg        cycle_timeout;
    wire [31:0] z8k_cycle_limit;

    reg z8k_rst_n_prev;
    always @(posedge sys_clk) z8k_rst_n_prev <= z8k_rst_n;
    wire z8k_start = z8k_rst_n && !z8k_rst_n_prev;

    wire as_falling = prev_as_n && ~cpu_as_n;
    wire opcode_fetch = as_falling && (cpu_st == 4'b1101);
    wire cpu_clk_rising = z8k_cpu_clk && ~prev_cpu_clk;

    always @(posedge sys_clk) begin
        if (z8k_start) begin
            bus_active <= 1'b0;
            cycle_count <= 32'd0;
            fetch_count <= 16'd0;
            prev_as_n <= 1'b1;
            prev_cpu_clk <= 1'b0;
            counting <= 1'b1;
            cycle_timeout <= 1'b0;
        end else begin
            prev_as_n <= cpu_as_n;
            prev_cpu_clk <= z8k_cpu_clk;

            if (as_falling && !bus_active)
                bus_active <= 1'b1;

            if (!cpu_halt_n)
                counting <= 1'b0;

            if (counting && cpu_halt_n && cpu_clk_rising)
                cycle_count <= cycle_count + 1'b1;

            if (counting && cpu_halt_n && opcode_fetch)
                fetch_count <= fetch_count + 1'b1;

            if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit))
                cycle_timeout <= 1'b1;
        end
    end

    //------------------------------------------------------------------------
    // Trace Buffer
    //------------------------------------------------------------------------
    wire [9:0]  trace_rd_addr;
    wire [35:0] trace_rd_data;
    wire [9:0]  trace_wr_count;

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
        .z8k_st     (cpu_st),
        .rd_addr    (trace_rd_addr),
        .rd_data    (trace_rd_data),
        .wr_count   (trace_wr_count)
    );

    //------------------------------------------------------------------------
    // Z80 Harness Controller
    //------------------------------------------------------------------------
    wire        z8k_mem_we;
    wire [14:0] z80_addr;
    wire [15:0] z8k_mem_wdata;
    wire [15:0] z8k_mem_rdata;

    // I/O port register signals (Z80 side)
    wire [3:0]  z80_io_reg_sel;
    wire [7:0]  z80_io_wbyte;
    wire [15:0] z80_io_rdata;
    wire        z80_io_wr_lo;
    wire        z80_io_wr_hi;

    // I/O port register signals (Z8000 side)
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
        .z80_alive      ()
    );

    //------------------------------------------------------------------------
    // Dual-Port BRAM (8KB)
    // Port A: Z80 harness (load/read test code)
    // Port B: Z8002 CPU (fetch/execute)
    //------------------------------------------------------------------------

    // Z8002 write logic - level-based (internal CPU, no synchronizer delay)
    wire z8k_ram_write = ram_sel && ~cpu_rw_n && ~cpu_ds_n;
    wire z8k_we_hi = z8k_ram_write && (cpu_bw_n || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (cpu_bw_n ||  z8k_addr[0]);

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
        // Port B - Z8002 CPU
        .clkb    (sys_clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
        .addrb   (z8k_addr[12:0]),
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
        // Z8000 bus side
        .z8k_reg_sel   (z8k_io_reg_sel),
        .z8k_wdata     (z8k_wdata),
        .z8k_rdata     (z8k_io_rdata),
        .z8k_wr        (z8k_io_wr),
        .z8k_bw_n      (cpu_bw_n),
        .z8k_addr_lsb  (z8k_addr[0]),
        // Z80 side
        .z80_reg_sel   (z80_io_reg_sel),
        .z80_wbyte     (z80_io_wbyte),
        .z80_rdata     (z80_io_rdata),
        .z80_wr_lo     (z80_io_wr_lo),
        .z80_wr_hi     (z80_io_wr_hi)
    );

    // Z8002 data bus mux
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
    // Any Z8002 I/O write captures wdata; LED driven from bit 0
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
