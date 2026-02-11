//============================================================================
// Z8001 External Test Harness - Top Level Module
// Target: Altera Cyclone IV (Quartus project)
//
// Wires an external Z8001 CPU to FPGA BRAM via 74LVC245 level shifters.
// Z80 harness controller manages test execution over UART.
//
// Features:
// - Z8001 bus interface via z8001_bus_external
// - 8KB dual-port BRAM (Port A: Z80, Port B: Z8001)
// - I/O LED latch (any Z8001 I/O write sets LED register)
// - Halt detection via opcode sniffing (0x7A00 on first fetch)
// - Cycle/fetch counting instrumentation
// - Bus trace capture buffer (1024 entries, address-gated)
//============================================================================

module z8001_ext_test_top (
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

    // Z8001 CPU control outputs
    output wire        fclk,            // CPU clock 4MHz (F1)
    output wire        freset,          // CPU reset, active-high (B17)
    output wire        fbreq,           // Bus request (H2)
    output wire        fwait,           // Wait state (J2)
    output wire        fnvi,            // Non-vectored interrupt (F2)
    output wire        fvi,             // Vectored interrupt (B2)
    output wire        fnmi,            // NMI (B3)

    // Z8001 bus buffer control
    output wire        fbuscs,          // Bus buffer OE, active-low (R2)
    output wire        fbusrd,          // Bus buffer direction (P2)

    // Z8001 CPU inputs (from CPU via level shifters)
    input  wire        fas,             // Address strobe (A8)
    input  wire        fds,             // Data strobe (A9)
    input  wire        fbw,             // Byte/Word (A7)
    input  wire        fmreq,           // Memory request (A10)
    input  wire        frw,             // Read/Write (A13)
    input  wire [3:0]  fst,             // Status ST0-ST3 (D2,C1,C2,B1)
    input  wire [3:0]  fsn,             // Segment SN0-SN3 (R1,N1,N2,M1)

    // Z8001 AD bus (via 74LVC245)
    inout  wire [15:0] sramData         // Bidirectional data bus
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
    // Z8001 CPU Control
    //------------------------------------------------------------------------
    wire z8k_rst_n;                      // From Z80 harness

    assign fclk    = clk_4mhz;
    assign freset  = z8k_rst_n;         // 0=reset, 1=run (matches original bring-up convention)
    assign fbreq   = 1'b1;              // No bus request
    assign fwait   = 1'b1;              // No wait states
    assign fnvi    = 1'b1;              // No non-vectored interrupt
    assign fvi     = 1'b1;              // No vectored interrupt
    assign fnmi    = 1'b1;              // No NMI

    //------------------------------------------------------------------------
    // Z8001 Bus Interface
    //------------------------------------------------------------------------
    wire [15:0] z8k_addr;               // Latched address from bus interface
    wire [15:0] z8k_wdata;              // Write data from CPU
    wire [15:0] data_to_cpu;            // Read data to CPU
    wire [3:0]  z8k_st;                 // Latched status
    wire        z8k_as_n_sync;          // Synchronized AS
    wire        z8k_ds_n_sync;          // Synchronized DS
    wire        z8k_rw_n_sync;          // Synchronized R/W
    wire        z8k_mreq_n_sync;        // Synchronized MREQ
    wire        z8k_bw_n_sync;          // Synchronized B/W

    z8001_bus_external bus_if (
        .clk        (sys_clk),
        .rst_n      (sys_rst_n),
        .z8k_rst_n  (z8k_rst_n),
        .cpu_clk    (clk_4mhz),
        .as_n       (fas),
        .ds_n       (fds),
        .bw_n       (fbw),
        .mreq_n     (fmreq),
        .rw_n       (frw),
        .st         (fst),
        .sn         (fsn),
        .ad_bus     (sramData),
        .buf_oe_n   (fbuscs),
        .buf_dir    (fbusrd),
        .addr       (z8k_addr),
        .wdata      (z8k_wdata),
        .rdata      (data_to_cpu),
        .st_latched (z8k_st),
        .as_n_out   (z8k_as_n_sync),
        .ds_n_out   (z8k_ds_n_sync),
        .rw_n_out   (z8k_rw_n_sync),
        .mreq_n_out (z8k_mreq_n_sync),
        .bw_n_out   (z8k_bw_n_sync)
    );

    //------------------------------------------------------------------------
    // Address Decode
    //------------------------------------------------------------------------
    wire io_sel  = (z8k_st == 4'b0010) || (z8k_st == 4'b0100);
    wire ram_sel = ~z8k_mreq_n_sync && ~io_sel;

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
    // Halt Detection - Opcode Sniffing
    // Detect HALT by matching opcode 0x7A00 during first opcode fetch (ST=1101)
    //
    // data_to_cpu depends on ram_sel (uses synchronized MREQ). At ds_rising,
    // MREQ may have already deasserted, making data_to_cpu = 0xFFFF.
    // Fix: latch data_to_cpu while DS is active, check latched value at ds_rising.
    //------------------------------------------------------------------------
    reg halt_detected;
    reg ds_n_prev;
    wire ds_rising = ~ds_n_prev && z8k_ds_n_sync;
    wire first_fetch_cycle = (z8k_st == 4'b1101);

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            ds_n_prev <= 1'b1;
        else
            ds_n_prev <= z8k_ds_n_sync;
    end

    // Latch data while DS is active (ram_sel still valid during data phase)
    reg [15:0] latched_cpu_data;
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            latched_cpu_data <= 16'h0000;
        else if (~z8k_ds_n_sync)
            latched_cpu_data <= data_to_cpu;
    end

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            halt_detected <= 1'b0;
        else if (!z8k_rst_n)
            halt_detected <= 1'b0;      // Clear on CPU reset
        else if (ds_rising && first_fetch_cycle && latched_cpu_data == 16'h7A00)
            halt_detected <= 1'b1;       // HALT opcode fetched
    end

    wire z8k_halt_n = ~halt_detected;

    //------------------------------------------------------------------------
    // Instrumentation (Cycle/Fetch Counting)
    //------------------------------------------------------------------------
    reg        bus_active;
    reg [31:0] cycle_count;
    reg [15:0] fetch_count;
    reg        prev_as_n;
    reg        prev_cpu_clk;
    reg        counting;
    reg        cycle_timeout;
    wire [31:0] z8k_cycle_limit;

    wire as_falling = prev_as_n && ~z8k_as_n_sync;
    wire opcode_fetch = as_falling && (z8k_st == 4'b1101);
    wire cpu_clk_rising = clk_4mhz && ~prev_cpu_clk;

    always @(posedge sys_clk or negedge z8k_rst_n) begin
        if (!z8k_rst_n) begin
            bus_active <= 1'b0;
            cycle_count <= 32'd0;
            fetch_count <= 16'd0;
            prev_as_n <= 1'b1;
            prev_cpu_clk <= 1'b0;
            counting <= 1'b1;
            cycle_timeout <= 1'b0;
        end else begin
            prev_as_n <= z8k_as_n_sync;
            prev_cpu_clk <= clk_4mhz;

            if (as_falling && !bus_active)
                bus_active <= 1'b1;

            if (halt_detected)
                counting <= 1'b0;

            if (counting && !halt_detected && cpu_clk_rising)
                cycle_count <= cycle_count + 1'b1;

            if (counting && !halt_detected && opcode_fetch)
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

    wire [15:0] trace_data = z8k_rw_n_sync ? data_to_cpu : z8k_wdata;

    trace_buffer_altera trace (
        .clk        (sys_clk),
        .rst_n      (sys_rst_n),
        .z8k_rst_n  (z8k_rst_n),
        .z8k_addr   (z8k_addr),
        .z8k_data   (trace_data),
        .z8k_as_n   (z8k_as_n_sync),
        .z8k_ds_n   (z8k_ds_n_sync),
        .z8k_rw_n   (z8k_rw_n_sync),
        .z8k_bw_n   (z8k_bw_n_sync),
        .z8k_mreq_n (z8k_mreq_n_sync),
        .z8k_st     (z8k_st),
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
        .z8k_halt_n     (z8k_halt_n),
        .z8k_st         (z8k_st),
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
        .trace_wr_count (trace_wr_count)
    );

    //------------------------------------------------------------------------
    // Dual-Port BRAM (8KB)
    // Port A: Z80 harness (load/read test code)
    // Port B: Z8001 CPU (fetch/execute)
    //------------------------------------------------------------------------

    // Z8001 write logic
    wire z8k_ram_write = ram_sel && ~z8k_rw_n_sync && ~z8k_ds_n_sync;
    wire z8k_we_hi = z8k_ram_write && (z8k_bw_n_sync || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (z8k_bw_n_sync ||  z8k_addr[0]);

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
        // Port B - Z8001 CPU
        .clkb    (sys_clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
        .addrb   (z8k_addr[12:0]),
        .dinb    (z8k_wdata),
        .doutb   (z8k_rd_data)
    );

    assign z8k_mem_rdata = z80_rd_data;

    // Z8001 data bus mux: BRAM for memory reads, 0xFFFF for I/O (no I/O read ports yet)
    assign data_to_cpu = ram_sel ? z8k_rd_data : 16'hFFFF;

    //------------------------------------------------------------------------
    // I/O LED Latch
    // Any Z8001 I/O write captures wdata; LED driven from bit 0
    //------------------------------------------------------------------------
    reg [15:0] io_led_reg;
    wire io_write = io_sel && ~z8k_rw_n_sync && ~z8k_ds_n_sync;

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            io_led_reg <= 16'h0000;
        else if (io_write)
            io_led_reg <= z8k_wdata;
    end

    assign driveLED = io_led_reg[0];

endmodule
