// Unified Z8000 Bus Interface (FPGA internal CPU variant)
// Wraps z8000_cpu with AD bus tristate, address latch, and segment latch.
// Works for both Z8001 (segmented) and Z8002 (non-segmented) modes:
//   Z8001: define Z8001_MODE before z8000_cpu.v -> sn port active
//   Z8002: no define -> sn output tied to 0
//
// BUS_DIVIDER: EU/BIU clock ratio. CPU runs at system clock, BIU divides
// internally. cpu_clk output toggles at bus rate (sys_clk / BUS_DIVIDER)
// for cycle counting.

`timescale 1ns / 1ps

module z8001_bus_fpga #(
    parameter BUS_DIVIDER = 4
) (
    input         clk,        // System clock
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
    output [6:0]  sn,         // Latched segment number (Z8001=active, Z8002=0)
    output        halt_n,
    output        cpu_clk     // Bus-rate clock output (for cycle counting)
);

// ===========================================
// AD Bus and Write Data
// ===========================================
wire [15:0] ad_bus;
wire        cpu_busack_n, cpu_ns;

assign ad_bus = (rw_n && ~ds_n) ? rdata : 16'bz;
assign wdata = ad_bus;

// ===========================================
// Bus-rate reference clock: sys_clk / BUS_DIVIDER (50% duty cycle)
// ===========================================
reg [$clog2(BUS_DIVIDER)-1:0] bus_clk_cnt;
reg bus_clk_ref;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        bus_clk_cnt <= 0;
        bus_clk_ref <= 1'b0;
    end else begin
        if (bus_clk_cnt == BUS_DIVIDER/2 - 1) begin
            bus_clk_cnt <= 0;
            bus_clk_ref <= ~bus_clk_ref;
        end else begin
            bus_clk_cnt <= bus_clk_cnt + 1;
        end
    end
end

assign cpu_clk = bus_clk_ref;

// ===========================================
// Z8000 CPU (runs at system clock, BIU divides internally)
// ===========================================
`ifdef Z8001_MODE
wire [6:0] sn_raw;
`endif

z8000_cpu #(.BUS_DIVIDER(BUS_DIVIDER)) cpu (
    .clk        (clk),
    .rst_n      (z8k_rst_n),
    .ad         (ad_bus),
    .as_n       (as_n),
    .ds_n       (ds_n),
    .rw_n       (rw_n),
    .mreq_n     (mreq_n),
    .b_w_n      (bw_n),
    .st         (st),
`ifdef Z8001_MODE
    .sn         (sn_raw),
`endif
    .wait_n     (1'b1),
    .busreq_n   (1'b1),
    .busack_n   (cpu_busack_n),
    .nmi_n      (1'b1),
    .vi_n       (1'b1),
    .nvi_n      (1'b1),
    .n_s        (cpu_ns),
    .halt_n     (halt_n)
);

// ===========================================
// Address Latch
// Level-sensitive capture while AS_n is low.
// Sampled at system clock for minimum latency.
// ===========================================
reg [15:0] addr_latch;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        addr_latch <= 16'd0;
    else if (~as_n)
        addr_latch <= ad_bus;
end

assign addr = addr_latch;

// ===========================================
// Segment Latch
// Z8001: capture segment number while AS_n is low.
// Z8002: sn tied to 0 (all accesses land in segment 0).
// ===========================================
`ifdef Z8001_MODE
reg [6:0] sn_latch;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        sn_latch <= 7'd0;
    else if (~as_n)
        sn_latch <= sn_raw;
end

assign sn = sn_latch;
`else
assign sn = 7'd0;
`endif

endmodule
