// Z80-based Z8000 Test Harness Top Module
// Uses TV80 Z80 core to control Z8000 testing via UART
//
// Memory: 16KB shared BRAM accessible by both Z80 (via I/O) and Z8000 (via bus)
// Z80 has its own 8KB code/data RAM
//
// Target: Tang Nano 20K (GW2AR-18C)

`timescale 1ns / 1ps

module z8000_test_harness_top (
    input         clk,       // 27MHz system clock
    input         rst,       // Active high reset
    input         uart_rx,   // UART receive pin
    output        uart_tx,   // UART transmit pin
    output        led,       // Heartbeat LED
    output        led2,      // CPU in reset indicator
    output        led3,      // CPU running indicator
    output        led4       // CPU halted indicator
);

parameter CLK_FRE   = 27;
parameter UART_BAUD = 115200;

wire rst_n = ~rst;

// ===========================================
// LED Heartbeat
// ===========================================
reg [24:0] led_counter;
reg        led_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        led_counter <= 25'd0;
        led_reg <= 1'b0;
    end else if (led_counter == 25'd13_499_999) begin
        led_counter <= 25'd0;
        led_reg <= ~led_reg;
    end else begin
        led_counter <= led_counter + 1'b1;
    end
end

assign led = led_reg;

// ===========================================
// Z8000 CPU Clock - ~4MHz from 27MHz
// ===========================================
reg [2:0] z8k_clk_div;
reg       z8k_clk;
reg       toggle_sel;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        z8k_clk_div <= 3'd0;
        z8k_clk <= 1'b0;
        toggle_sel <= 1'b0;
    end else begin
        if ((toggle_sel && z8k_clk_div == 3'd3) || (!toggle_sel && z8k_clk_div == 3'd2)) begin
            z8k_clk_div <= 3'd0;
            z8k_clk <= ~z8k_clk;
            toggle_sel <= ~toggle_sel;
        end else begin
            z8k_clk_div <= z8k_clk_div + 1'b1;
        end
    end
end

// ===========================================
// UART
// ===========================================
wire [7:0]  uart_tx_data, uart_rx_data;
wire        uart_tx_valid, uart_tx_ready, uart_rx_valid, uart_rx_ready;

uart_tx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_tx_inst (
    .clk(clk), .rst_n(rst_n),
    .tx_data(uart_tx_data), .tx_data_valid(uart_tx_valid),
    .tx_data_ready(uart_tx_ready), .tx_pin(uart_tx)
);

uart_rx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_rx_inst (
    .clk(clk), .rst_n(rst_n),
    .rx_data(uart_rx_data), .rx_data_valid(uart_rx_valid),
    .rx_data_ready(uart_rx_ready), .rx_pin(uart_rx)
);

// ===========================================
// Z80 Harness Controller
// ===========================================
wire        z8k_rst_n;
wire        z8k_halt_n;
wire        z8k_mem_we;
wire [14:0] z8k_mem_addr;
wire [15:0] z8k_mem_wdata;
wire [15:0] z8k_mem_rdata;
wire [31:0] z8k_cycle_limit;

z80_harness z80 (
    .clk            (clk),
    .rst_n          (rst_n),
    .uart_rx_data   (uart_rx_data),
    .uart_rx_valid  (uart_rx_valid),
    .uart_rx_ready  (uart_rx_ready),
    .uart_tx_data   (uart_tx_data),
    .uart_tx_valid  (uart_tx_valid),
    .uart_tx_ready  (uart_tx_ready),
    .z8k_rst_n      (z8k_rst_n),
    .z8k_halt_n     (z8k_halt_n),
    .z8k_mem_we     (z8k_mem_we),
    .z8k_mem_addr   (z8k_mem_addr),
    .z8k_mem_wdata  (z8k_mem_wdata),
    .z8k_mem_rdata  (z8k_mem_rdata),
    .z8k_bus_active (bus_active),
    .z8k_cycle_count(cycle_count),
    .z8k_fetch_count(fetch_count),
    .z8k_cycle_limit(z8k_cycle_limit),
    .z8k_cycle_timeout(cycle_timeout)
);

// ===========================================
// Z8000 CPU
// ===========================================
wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
wire [3:0]  cpu_st;
wire        cpu_busack_n, cpu_ns, cpu_halt_n_out;
wire [15:0] ad_bus;
reg  [15:0] data_to_cpu;

assign ad_bus = (cpu_rw_n && ~cpu_ds_n) ? data_to_cpu : 16'bz;

wire cpu_wait_n = 1'b1;  // No wait states for now

z8000_cpu cpu (
    .clk        (z8k_clk),
    .rst_n      (z8k_rst_n),
    .ad         (ad_bus),
    .as_n       (cpu_as_n),
    .ds_n       (cpu_ds_n),
    .rw_n       (cpu_rw_n),
    .mreq_n     (cpu_mreq_n),
    .b_w_n      (cpu_bw_n),
    .st         (cpu_st),
    .wait_n     (cpu_wait_n),
    .busreq_n   (1'b1),
    .busack_n   (cpu_busack_n),
    .nmi_n      (1'b1),
    .vi_n       (1'b1),
    .nvi_n      (1'b1),
    .n_s        (cpu_ns),
    .halt_n     (cpu_halt_n_out)
);

assign z8k_halt_n = cpu_halt_n_out;

// ===========================================
// Z8000 Instrumentation
// ===========================================
// bus_active: Latches when AS_n goes low (first bus cycle after reset)
// cycle_count: Counts Z8000 clock cycles from reset release to HALT
// fetch_count: Counts opcode fetches (ST = 1101 = first instruction word)
// cycle_timeout: Goes HIGH when cycle_count >= cycle_limit

reg        bus_active;
reg [31:0] cycle_count;
reg [15:0] fetch_count;
reg        prev_as_n;
reg        counting;       // True while running (between reset release and halt)
reg        cycle_timeout;  // Set when cycle_count >= cycle_limit

// Detect falling edge of AS_n
wire as_falling = prev_as_n && ~cpu_as_n;

// Detect opcode fetch: ST = 4'b1101 (ST_INST_1ST) with AS falling edge
wire opcode_fetch = as_falling && (cpu_st == 4'b1101);

always @(posedge z8k_clk or negedge rst_n) begin
    if (!rst_n) begin
        bus_active <= 1'b0;
        cycle_count <= 32'd0;
        fetch_count <= 16'd0;
        prev_as_n <= 1'b1;
        counting <= 1'b0;
        cycle_timeout <= 1'b0;
    end else if (!z8k_rst_n) begin
        // Z8000 in reset - clear counters and timeout
        bus_active <= 1'b0;
        cycle_count <= 32'd0;
        fetch_count <= 16'd0;
        prev_as_n <= 1'b1;
        counting <= 1'b0;
        cycle_timeout <= 1'b0;
    end else begin
        prev_as_n <= cpu_as_n;

        // Detect first bus activity
        if (as_falling && !bus_active) begin
            bus_active <= 1'b1;
        end

        // Start counting when reset is released
        if (!counting && z8k_rst_n) begin
            counting <= 1'b1;
        end

        // Stop counting when halted
        if (!cpu_halt_n_out) begin
            counting <= 1'b0;
        end

        // Count cycles while running
        if (counting && cpu_halt_n_out) begin
            cycle_count <= cycle_count + 1'b1;
        end

        // Count opcode fetches
        if (counting && cpu_halt_n_out && opcode_fetch) begin
            fetch_count <= fetch_count + 1'b1;
        end

        // Set timeout flag when cycle_count >= cycle_limit (if limit != 0)
        if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit)) begin
            cycle_timeout <= 1'b1;
        end
    end
end

// LED indicators
assign led2 = ~z8k_rst_n;                        // On when CPU in reset
assign led3 = z8k_rst_n && cpu_halt_n_out;       // On when running
assign led4 = ~cpu_halt_n_out;                   // On when halted

// ===========================================
// Address Latch (Z8000 side)
// Uses synchronous latching like the working monitor example
// Samples address when AS_n is low on 27MHz clock edge
// ===========================================
reg [15:0] latched_addr;
reg [3:0]  latched_st;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        latched_addr <= 16'h0000;
        latched_st <= 4'b0000;
    end else if (~cpu_as_n) begin
        latched_addr <= ad_bus;
        latched_st <= cpu_st;
    end
end

// ===========================================
// Shared Memory - 16KB (directly accent accessible by Z80 and Z8000)
// ===========================================
// Z80 has priority when Z8000 is in reset
wire z80_has_bus = ~z8k_rst_n;

// Memory address selection - use BYTE address (ram16 converts to word internally)
wire [12:0] mem_addr = z80_has_bus ? z8k_mem_addr[12:0] : latched_addr[12:0];

// Write enables
wire cpu_mem_write = ~cpu_mreq_n && ~cpu_rw_n && ~cpu_ds_n && !z80_has_bus;
wire cpu_we_hi = cpu_mem_write && (cpu_bw_n || ~latched_addr[0]);
wire cpu_we_lo = cpu_mem_write && (cpu_bw_n || latched_addr[0]);

wire z80_we_hi = z8k_mem_we && z80_has_bus;
wire z80_we_lo = z8k_mem_we && z80_has_bus;

wire we_hi = z80_we_hi || cpu_we_hi;
wire we_lo = z80_we_lo || cpu_we_lo;

// Write data
wire [15:0] wdata = z80_has_bus ? z8k_mem_wdata : ad_bus;

// Shared RAM - vendor-neutral wrapper (see ram16.v)
wire [15:0] mem_rdata;

ram16 bram (
    .clk    (clk),
    .we_hi  (we_hi),
    .we_lo  (we_lo),
    .addr   (mem_addr),
    .din    (wdata),
    .dout   (mem_rdata)
);

assign z8k_mem_rdata = mem_rdata;

// I/O decode: ST=2 for byte I/O, ST=4 for word I/O (exclude from memory select)
wire io_sel = (cpu_st == 4'b0010) || (cpu_st == 4'b0100);

// Memory select: mreq active, not I/O, address in range
wire mem_sel = ~cpu_mreq_n && ~io_sel && (latched_addr[15] == 1'b0);

always @(*) begin
    if (mem_sel)
        data_to_cpu = mem_rdata;
    else
        data_to_cpu = 16'hFFFF;
end

endmodule
