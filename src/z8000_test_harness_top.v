// Z80-based Z8000 Test Harness Top Module
// Uses TV80 Z80 core to control Z8000 testing via UART
//
// Clock: 27MHz (clk) - Single clock domain for all logic
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

parameter CLK_FRE   = 27;     // 27MHz system clock
parameter UART_BAUD = 115200; // Standard baud for 27MHz (234 cycles/bit)

// ===========================================
// Reset Debounce (~20ms at 27MHz)
// ===========================================
reg [19:0] debounce_cnt;
reg        rst_debounced;

always @(posedge clk) begin
    if (rst) begin
        debounce_cnt <= 20'd0;
        rst_debounced <= 1'b1;
    end else if (debounce_cnt < 20'd539_999) begin
        debounce_cnt <= debounce_cnt + 1'b1;
    end else begin
        rst_debounced <= 1'b0;
    end
end

wire rst_n = ~rst_debounced;

// ===========================================
// LED Heartbeat
// ===========================================
reg [23:0] led_counter;
reg        led_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        led_counter <= 24'd0;
        led_reg <= 1'b0;
    end else if (led_counter == 24'd13_499_999) begin  // 0.5s at 27MHz
        led_counter <= 24'd0;
        led_reg <= ~led_reg;
    end else begin
        led_counter <= led_counter + 1'b1;
    end
end

assign led = led_reg;

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
// Signal declarations (before instantiations)
// ===========================================

// Z80 harness interface
wire        z8k_rst_n;
wire        z8k_halt_n;
wire        z8k_mem_we;
wire [14:0] z80_addr;
wire [15:0] z8k_mem_wdata;
wire [15:0] z8k_mem_rdata;
wire [31:0] z8k_cycle_limit;

// Trace buffer signals
wire [9:0]  trace_rd_addr;
wire [35:0] trace_rd_data;
wire [9:0]  trace_wr_count;

// Z8000 CPU signals
wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
wire [3:0]  cpu_st;
wire        cpu_busack_n, cpu_ns, cpu_halt_n_out;
wire [15:0] ad_bus;
reg  [15:0] data_to_cpu;

// Z8000 instrumentation
reg        bus_active;
reg [31:0] cycle_count;
reg [15:0] fetch_count;
reg        prev_as_n;
reg        counting;
reg        cycle_timeout;

// ===========================================
// Z80 Harness Controller
// ===========================================
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

// ===========================================
// Z8000 CPU
// ===========================================
assign ad_bus = (cpu_rw_n && ~cpu_ds_n) ? data_to_cpu : 16'bz;

z8000_cpu cpu (
    .clk        (clk),
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
    .halt_n     (cpu_halt_n_out)
);

assign z8k_halt_n = cpu_halt_n_out;

// ===========================================
// Z8000 Instrumentation
// Resets with z8k_rst_n (Z80-controlled)
// ===========================================

wire as_falling = prev_as_n && ~cpu_as_n;
wire opcode_fetch = as_falling && (cpu_st == 4'b1101);

always @(posedge clk or negedge z8k_rst_n) begin
    if (!z8k_rst_n) begin
        bus_active <= 1'b0;
        cycle_count <= 32'd0;
        fetch_count <= 16'd0;
        prev_as_n <= 1'b1;
        counting <= 1'b1;
        cycle_timeout <= 1'b0;
    end else begin
        prev_as_n <= cpu_as_n;

        if (as_falling && !bus_active)
            bus_active <= 1'b1;

        if (!cpu_halt_n_out)
            counting <= 1'b0;

        if (counting && cpu_halt_n_out)
            cycle_count <= cycle_count + 1'b1;

        if (counting && cpu_halt_n_out && opcode_fetch)
            fetch_count <= fetch_count + 1'b1;

        if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit))
            cycle_timeout <= 1'b1;
    end
end

// LED indicators
assign led2 = ~z8k_rst_n;
assign led3 = z8k_rst_n && cpu_halt_n_out;
assign led4 = ~cpu_halt_n_out;

// ===========================================
// Address Latch
// Level-sensitive capture while AS_n is low.
// ===========================================
reg [15:0] z8k_addr;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        z8k_addr <= 16'd0;
    else if (~cpu_as_n)
        z8k_addr <= ad_bus;
end

// ===========================================
// Address decode
// ===========================================
wire io_sel  = (cpu_st == 4'b0010) || (cpu_st == 4'b0100);
wire ram_sel = ~cpu_mreq_n && ~io_sel;

// ===========================================
// True Dual-Port BRAM (27MHz, Gowin DPB)
// Port A: Z80 harness  - always connected, no mux
// Port B: Z8000 CPU    - always connected, no mux
// Both ports independent, no contention possible.
// ===========================================

// Z8000 write logic
wire z8k_ram_write = ram_sel && ~cpu_rw_n && ~cpu_ds_n;
wire z8k_we_hi = z8k_ram_write && (cpu_bw_n || ~z8k_addr[0]);
wire z8k_we_lo = z8k_ram_write && (cpu_bw_n ||  z8k_addr[0]);

wire [15:0] z80_rd_data;   // Port A read (Z80)
wire [15:0] z8k_rd_data;   // Port B read (Z8000)

ram16 bram (
    // Port A - Z80 harness (load/verify test code)
    .clka    (clk),               // 27MHz
    .wea_hi  (z8k_mem_we),
    .wea_lo  (z8k_mem_we),
    .addra   (z80_addr[12:0]),
    .dina    (z8k_mem_wdata),
    .douta   (z80_rd_data),
    // Port B - Z8000 CPU (fetch/execute)
    .clkb    (clk),               // 27MHz
    .web_hi  (z8k_we_hi),
    .web_lo  (z8k_we_lo),
    .addrb   (z8k_addr[12:0]),
    .dinb    (ad_bus),
    .doutb   (z8k_rd_data)
);

assign z8k_mem_rdata = z80_rd_data;   // Z80 reads via Port A

// Z8000 data bus mux
always @(*) begin
    if (ram_sel)
        data_to_cpu = z8k_rd_data;    // Z8000 reads via Port B
    else
        data_to_cpu = 16'hFFFF;
end

// ===========================================
// Trace Buffer
// ===========================================
wire [15:0] trace_data = cpu_rw_n ? data_to_cpu : ad_bus;

trace_buffer trace (
    .clk        (clk),
    .rst_n      (rst_n),
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

endmodule
