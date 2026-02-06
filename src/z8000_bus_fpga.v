// Z8000 Bus Interface (FPGA internal CPU variant)
// Wraps z8000_cpu with ~4MHz clock divider, AD bus tristate, and address latch.
//
// Clock divider: alternating /3 and /4 half-periods from 27MHz
//   -> ~3.86MHz (closest to 4MHz without a PLL)

`timescale 1ns / 1ps

module z8000_bus_fpga (
    input         clk,        // 27MHz system clock
    input         rst_n,      // System reset
    input         z8k_rst_n,  // Z8000 reset (from Z80 harness)
    input  [15:0] rdata,      // Read data from memory/IO back to CPU
    output [15:0] addr,       // Latched address
    output [15:0] wdata,      // Write data (AD bus during CPU writes)
    output        as_n,
    output        ds_n,
    output        rw_n,
    output        mreq_n,
    output        bw_n,
    output [3:0]  st,
    output        halt_n,
    output        cpu_clk     // ~4MHz clock output (for cycle counting)
);

// ===========================================
// ~3.86MHz Clock Divider (alternating /3 and /4)
// ===========================================
// 27MHz / 3.5 = 7.714MHz toggle rate -> ~3.86MHz clock
// Achieved by alternating: 3 ticks high, 4 ticks low, 3 ticks high, ...

reg [2:0] clk_cnt;
reg       z8k_clk;
reg       phase;    // 0 = count to 3, 1 = count to 4

wire [2:0] clk_limit = phase ? 3'd3 : 3'd2;  // 4-1 or 3-1

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        clk_cnt <= 3'd0;
        z8k_clk <= 1'b0;
        phase   <= 1'b0;
    end else begin
        if (clk_cnt == clk_limit) begin
            clk_cnt <= 3'd0;
            z8k_clk <= ~z8k_clk;
            phase   <= ~phase;
        end else begin
            clk_cnt <= clk_cnt + 1'b1;
        end
    end
end

assign cpu_clk = z8k_clk;

// ===========================================
// Z8000 CPU
// ===========================================
wire [15:0] ad_bus;
wire        cpu_busack_n, cpu_ns;

assign ad_bus = (rw_n && ~ds_n) ? rdata : 16'bz;

z8000_cpu cpu (
    .clk        (z8k_clk),
    .rst_n      (z8k_rst_n),
    .ad         (ad_bus),
    .as_n       (as_n),
    .ds_n       (ds_n),
    .rw_n       (rw_n),
    .mreq_n     (mreq_n),
    .b_w_n      (bw_n),
    .st         (st),
    .wait_n     (1'b1),
    .busreq_n   (1'b1),
    .busack_n   (cpu_busack_n),
    .nmi_n      (1'b1),
    .vi_n       (1'b1),
    .nvi_n      (1'b1),
    .n_s        (cpu_ns),
    .halt_n     (halt_n)
);

// Write data is the AD bus value during CPU write cycles
assign wdata = ad_bus;

// ===========================================
// Address Latch
// Level-sensitive capture while AS_n is low.
// Sampled at 27MHz for minimum latency.
// ===========================================
reg [15:0] addr_latch;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        addr_latch <= 16'd0;
    else if (~as_n)
        addr_latch <= ad_bus;
end

assign addr = addr_latch;

endmodule
