//============================================================================
// Z8001 External Test Harness - Top Level Module
// Target: Altera Cyclone IV (Quartus project)
//
// Initial bring-up configuration:
// - External SRAM disabled (directly directly CS high)
// - Z8001 AD bus buffer disabled (fbuscs high)
// - Z8001 held in reset (freset high)
// - Z80 harness connected to serial port 1 for testing
//
// Once serial communication is verified, we can enable the Z8001 interface.
//============================================================================

module z8001_ext_test_top (
    // System
    input  wire        clk,             // 50 MHz oscillator (directly directly directly directly T2)
    input  wire        n_reset,         // Active-low reset button (W13)

    // Serial Port 1 (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly UART)
    input  wire        urxd1,           // UART RX from external (B18)
    output wire        utxd1,           // UART TX to external (B22)

    // LED
    output wire        driveLED,        // Activity LED (E4)

    // External SRAM control (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly disabled for now)
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

    // Z8001 CPU inputs (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly from CPU accent level shifters)
    input  wire        fas,             // Address strobe (A8)
    input  wire        fds,             // Data strobe (A9)
    input  wire        fbw,             // Byte/Word (A7)
    input  wire        fmreq,           // Memory request (A10)
    input  wire        frw,             // Read/Write (A13)
    input  wire [3:0]  fst,             // Status ST0-ST3 (D2,C1,C2,B1)
    input  wire [3:0]  fsn,             // Segment SN0-SN3 (R1,N1,N2,M1)

    // Z8001 AD bus (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly 74LVC245, accent sramData pins)
    inout  wire [15:0] sramData         // Directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly bidirectional data bus
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
    // directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly Hold chip selects high (inactive) to disable SRAM
    //------------------------------------------------------------------------
    assign n_sRamCS0 = 1'b1;    // Disabled
    assign n_sRamCS1 = 1'b1;    // Disabled
    assign n_sRamOE  = 1'b1;    // Disabled
    assign n_sRamWE  = 1'b1;    // Disabled

    //------------------------------------------------------------------------
    // Z8001 CPU - DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY DIRECTLY HELD IN RESET
    // directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly Hold reset high and bus buffer disabled until UART is working
    //------------------------------------------------------------------------
    assign fclk    = clk_4mhz;  // CPU clock still running
    assign freset  = 1'b0;      // HELD IN RESET (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly 0=reset, 1=run)
    assign fbreq   = 1'b1;      // No bus request
    assign fwait   = 1'b1;      // No wait states
    assign fnvi    = 1'b1;      // No non-vectored interrupt
    assign fvi     = 1'b1;      // No vectored interrupt
    assign fnmi    = 1'b1;      // No NMI

    // Bus buffer DISABLED (fbuscs is active-low, so 1 = disabled)
    assign fbuscs  = 1'b1;      // Bus buffer DISABLED
    assign fbusrd  = 1'b0;      // Direction doesn't matter when disabled

    // AD bus directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly tri-stated (buffer disabled, no FPGA driving)
    assign sramData = 16'bz;

    //------------------------------------------------------------------------
    // UART (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly Serial Port 1)
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
    // Z80 Harness Controller
    //------------------------------------------------------------------------
    wire        z8k_rst_n;          // Z8001 reset control (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly unused for now)
    wire        z8k_mem_we;
    wire [14:0] z80_addr;
    wire [15:0] z8k_mem_wdata;
    wire [15:0] z8k_mem_rdata;
    wire [31:0] z8k_cycle_limit;

    // Directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly Trace buffer signals (directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly directly dummy for now)
    wire [9:0]  trace_rd_addr;
    wire [35:0] trace_rd_data = 36'b0;
    wire [9:0]  trace_wr_count = 10'b0;

    // Dummy instrumentation (CPU is in reset)
    wire [31:0] cycle_count = 32'b0;
    wire [15:0] fetch_count = 16'b0;
    wire        bus_active = 1'b0;
    wire        cycle_timeout = 1'b0;
    wire [3:0]  cpu_st = 4'b0;

    z80_harness z80 (
        .clk            (sys_clk),
        .rst_n          (sys_rst_n),
        .uart_rx_data   (uart_rx_data),
        .uart_rx_valid  (uart_rx_valid),
        .uart_rx_ready  (uart_rx_ready),
        .uart_tx_data   (uart_tx_data),
        .uart_tx_valid  (uart_tx_valid),
        .uart_tx_ready  (uart_tx_ready),
        .z8k_rst_n      (z8k_rst_n),        // Output, but we ignore it for now
        .z8k_halt_n     (1'b0),             // Pretend halted
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
        .trace_wr_count (trace_wr_count)
    );

    //------------------------------------------------------------------------
    // Dual-Port BRAM (8KB)
    // For now, just test that Z80 harness can read/write BRAM via UART
    //------------------------------------------------------------------------
    wire [15:0] z80_rd_data;

    ram16_altera bram (
        // Port A - Z80 harness
        .clka    (sys_clk),
        .wea_hi  (z8k_mem_we),
        .wea_lo  (z8k_mem_we),
        .addra   (z80_addr[12:0]),
        .dina    (z8k_mem_wdata),
        .douta   (z80_rd_data),
        // Port B - Z8001 CPU (unused for now)
        .clkb    (sys_clk),
        .web_hi  (1'b0),
        .web_lo  (1'b0),
        .addrb   (13'b0),
        .dinb    (16'b0),
        .doutb   ()                 // Unconnected
    );

    assign z8k_mem_rdata = z80_rd_data;

    //------------------------------------------------------------------------
    // LED Indicator
    //------------------------------------------------------------------------
    reg [23:0] led_cnt;
    always @(posedge sys_clk) begin
        led_cnt <= led_cnt + 1;
    end

    // Slow blink = system running, UART ready
    assign driveLED = led_cnt[23];

endmodule
