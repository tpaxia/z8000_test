// Z80-based Z8000 Test Harness Top Module
// Uses TV80 Z80 core to control Z8000 testing via UART
//
// Clock: 27MHz (clk) - Single clock domain for all logic
//
// Target: Tang Nano 20K (GW2AR-18C)

`timescale 1ns / 1ps

module z8000_test_harness_top (
    input         clk,       // 27MHz system clock
    input         uart_rx,   // UART receive pin
    output        uart_tx,   // UART transmit pin
    output [3:0]  led        // LEDs (active low): [0]=heartbeat, [1]=Z80 alive,
                             //   [2]=Z8000 in reset, [3]=Z8000 halted
);

parameter CLK_FRE   = 27;     // 27MHz system clock
parameter UART_BAUD = 115200; // Standard baud for 27MHz (234 cycles/bit)

// ===========================================
// Power-on Reset (~20ms at 27MHz)
// ===========================================
reg [19:0] por_cnt = 20'd0;
reg        por_active = 1'b1;

always @(posedge clk) begin
    if (por_active) begin
        if (por_cnt < 20'd539_999)
            por_cnt <= por_cnt + 1'b1;
        else
            por_active <= 1'b0;
    end
end

wire sys_rst_n = ~por_active;

// ===========================================
// LED Heartbeat
// ===========================================
reg [23:0] led_counter;
reg        led_reg;

always @(posedge clk or negedge sys_rst_n) begin
    if (!sys_rst_n) begin
        led_counter <= 24'd0;
        led_reg <= 1'b0;
    end else if (led_counter == 24'd13_499_999) begin  // 0.5s at 27MHz
        led_counter <= 24'd0;
        led_reg <= ~led_reg;
    end else begin
        led_counter <= led_counter + 1'b1;
    end
end

// ===========================================
// UART
// ===========================================
wire [7:0]  uart_tx_data, uart_rx_data;
wire        uart_tx_valid, uart_tx_ready, uart_rx_valid, uart_rx_ready;

uart_tx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_tx_inst (
    .clk(clk), .rst_n(sys_rst_n),
    .tx_data(uart_tx_data), .tx_data_valid(uart_tx_valid),
    .tx_data_ready(uart_tx_ready), .tx_pin(uart_tx)
);

uart_rx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(UART_BAUD)) uart_rx_inst (
    .clk(clk), .rst_n(sys_rst_n),
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

// Z8000 bus interface signals
wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
wire [3:0]  cpu_st;
wire        cpu_halt_n_out;
wire [15:0] z8k_addr;
wire [15:0] z8k_wdata;
wire        z8k_cpu_clk;
reg  [15:0] data_to_cpu;

// I/O port register signals (Z80 side)
wire [3:0]  z80_io_reg_sel;
wire [7:0]  z80_io_wbyte;
wire [15:0] z80_io_rdata;
wire        z80_io_wr_lo;
wire        z80_io_wr_hi;

// I/O port register signals (Z8000 side)
wire [15:0] z8k_io_rdata;

// Z80 alive indicator
wire        z80_alive;

// Z8000 instrumentation
reg        bus_active;
reg [31:0] cycle_count;
reg [15:0] fetch_count;
reg        prev_as_n;
reg        prev_z8k_clk;
reg        counting;
reg        cycle_timeout;

// ===========================================
// Z80 Harness Controller
// ===========================================
z80_harness z80 (
    .clk            (clk),
    .rst_n          (sys_rst_n),
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
    .trace_wr_count (trace_wr_count),
    .io_port_reg_sel(z80_io_reg_sel),
    .io_port_wbyte  (z80_io_wbyte),
    .io_port_rdata  (z80_io_rdata),
    .io_port_wr_lo  (z80_io_wr_lo),
    .io_port_wr_hi  (z80_io_wr_hi),
    .z80_alive      (z80_alive)
);

// ===========================================
// Z8000 Bus Interface (CPU + clock divider)
// ===========================================
z8000_bus_fpga bus_if (
    .clk        (clk),
    .rst_n      (sys_rst_n),
    .z8k_rst_n  (z8k_rst_n),
    .rdata      (data_to_cpu),
    .addr       (z8k_addr),
    .wdata      (z8k_wdata),
    .as_n       (cpu_as_n),
    .ds_n       (cpu_ds_n),
    .rw_n       (cpu_rw_n),
    .mreq_n     (cpu_mreq_n),
    .bw_n       (cpu_bw_n),
    .st         (cpu_st),
    .halt_n     (cpu_halt_n_out),
    .cpu_clk    (z8k_cpu_clk)
);

assign z8k_halt_n = cpu_halt_n_out;

// ===========================================
// Z8000 Instrumentation
// Resets with z8k_rst_n (Z80-controlled)
// ===========================================

wire as_falling = prev_as_n && ~cpu_as_n;
wire opcode_fetch = as_falling && (cpu_st == 4'b1101);
wire z8k_clk_rising = z8k_cpu_clk && ~prev_z8k_clk;

always @(posedge clk or negedge z8k_rst_n) begin
    if (!z8k_rst_n) begin
        bus_active <= 1'b0;
        cycle_count <= 32'd0;
        fetch_count <= 16'd0;
        prev_as_n <= 1'b1;
        prev_z8k_clk <= 1'b0;
        counting <= 1'b1;
        cycle_timeout <= 1'b0;
    end else begin
        prev_as_n <= cpu_as_n;
        prev_z8k_clk <= z8k_cpu_clk;

        if (as_falling && !bus_active)
            bus_active <= 1'b1;

        if (!cpu_halt_n_out)
            counting <= 1'b0;

        if (counting && cpu_halt_n_out && z8k_clk_rising)
            cycle_count <= cycle_count + 1'b1;

        if (counting && cpu_halt_n_out && opcode_fetch)
            fetch_count <= fetch_count + 1'b1;

        if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit))
            cycle_timeout <= 1'b1;
    end
end

// LED indicators (active low: 0 = on)
assign led[0] = ~led_reg;                           // Heartbeat
assign led[1] = ~z80_alive;                         // Z80 firmware alive
assign led[2] = z8k_rst_n;                          // Z8000 in reset (on when rst asserted)
assign led[3] = cpu_halt_n_out;                     // Z8000 halted

// ===========================================
// Address decode
// ===========================================
wire io_std_sel = (cpu_st == 4'b0010);   // Standard I/O (ST=0010)
wire io_spc_sel = (cpu_st == 4'b0100);   // Special I/O (ST=0100)
wire io_sel  = io_std_sel || io_spc_sel;
wire ram_sel = ~cpu_mreq_n && ~io_sel;

// I/O port address match: Z8000 addresses 0x0100-0x010A
wire io_port_match = io_sel && (z8k_addr[15:4] == 12'h010);
// Register index: addr[3:1] (0-5) + 6 if special I/O
wire [3:0] z8k_io_reg_sel = z8k_addr[3:1] + (io_spc_sel ? 4'd6 : 4'd0);

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
    .dinb    (z8k_wdata),
    .doutb   (z8k_rd_data)
);

assign z8k_mem_rdata = z80_rd_data;   // Z80 reads via Port A

// ===========================================
// I/O Port Registers
// ===========================================
wire z8k_io_wr = io_port_match && ~cpu_rw_n && ~cpu_ds_n;

z8k_io_ports io_ports (
    .clk           (clk),
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

// Z8000 data bus mux
always @(*) begin
    if (ram_sel)
        data_to_cpu = z8k_rd_data;    // Z8000 reads via Port B
    else if (io_port_match)
        data_to_cpu = z8k_io_rdata;   // I/O port register read
    else
        data_to_cpu = 16'hFFFF;
end

// ===========================================
// Trace Buffer
// ===========================================
wire [15:0] trace_data = cpu_rw_n ? data_to_cpu : z8k_wdata;

trace_buffer trace (
    .clk        (clk),
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

endmodule
