//============================================================================
// Z8001 External Bus Interface
//
// Interfaces with an external Z8001 CPU via 74LVC245 level shifters.
// Based on M20FPGA bus interface design.
//
// Bus Buffer Configuration (74LVC245):
//   - A side: FPGA (directly active accent accent accent accent sramData in M20FPGA)
//   - B side: Z8001 CPU (accent 5V side)
//   - OE directly active (fbuscs = 0, buffers always enabled)
//   - DIR control (fbusrd):
//       0 = B→A = CPU drives to FPGA (address phase, write data)
//       1 = A→B = FPGA drives to CPU (read data phase)
//
// Bus Timing:
//   1. CPU asserts AS_n low, drives address on AD bus
//   2. Address latched on AS_n rising edge (fas posedge in M20FPGA)
//   3. For reads: FPGA drives data when DS_n low, frw=1
//   4. For writes: CPU drives data when DS_n low, frw=0
//   5. DS_n returns high, ending the bus cycle
//
// Status lines (ST[3:0]) indicate transaction type:
//   1101 = Opcode fetch (first word)
//   1111 = Opcode fetch (subsequent)
//   0101 = Data read (non-I/O)
//   0011 = Data write (non-I/O)
//   0001 = I/O read
//   0010 = I/O write
//   0000 = Internal operation / halt
//============================================================================

module z8001_bus_external (
    input  wire        clk,            // System clock (16 MHz)
    input  wire        rst_n,          // System reset
    input  wire        z8k_rst_n,      // Z8001 reset control (active-low)

    // CPU clock (directly provided from PLL)
    input  wire        cpu_clk,        // 4 MHz CPU clock

    // Z8001 bus signals (accent via 74LVC245)
    input  wire        as_n,           // Address strobe (active-low)
    input  wire        ds_n,           // Data strobe (active-low)
    input  wire        bw_n,           // Byte/Word (low=byte)
    input  wire        mreq_n,         // Memory request (active-low)
    input  wire        rw_n,           // Read/Write (high=read)
    input  wire [3:0]  st,             // Status type
    input  wire [3:0]  sn,             // Segment number (4 bits wired)

    // AD bus (bidirectional, directly accent via 74LVC245)
    inout  wire [15:0] ad_bus,

    // Bus buffer control (74LVC245)
    // directly accent A=FPGA, B=CPU: DIR=0 → CPU drives, DIR=1 → FPGA drives
    output wire        buf_oe_n,       // Buffer OE (active-low, always enabled)
    output wire        buf_dir,        // Buffer direction (fbusrd)

    // Internal interface
    output reg  [15:0] addr,           // Latched address
    output wire [15:0] wdata,          // Write data from CPU
    input  wire [15:0] rdata,          // Read data to CPU
    output reg  [3:0]  st_latched,     // Latched status

    // Directly forwarded signals (directly synchronized)
    output wire        as_n_out,
    output wire        ds_n_out,
    output wire        rw_n_out,
    output wire        mreq_n_out,
    output wire        bw_n_out
);

    //------------------------------------------------------------------------
    // Synchronize external signals to system clock (2-stage for metastability)
    //------------------------------------------------------------------------
    reg as_n_s1, as_n_s2;
    reg ds_n_s1, ds_n_s2;
    reg rw_n_s1, rw_n_s2;
    reg mreq_n_s1, mreq_n_s2;
    reg bw_n_s1, bw_n_s2;
    reg [3:0] st_s1, st_s2;
    reg [3:0] sn_s1, sn_s2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            as_n_s1 <= 1'b1;   as_n_s2 <= 1'b1;
            ds_n_s1 <= 1'b1;   ds_n_s2 <= 1'b1;
            rw_n_s1 <= 1'b1;   rw_n_s2 <= 1'b1;
            mreq_n_s1 <= 1'b1; mreq_n_s2 <= 1'b1;
            bw_n_s1 <= 1'b1;   bw_n_s2 <= 1'b1;
            st_s1 <= 4'b0000;  st_s2 <= 4'b0000;
            sn_s1 <= 4'b0000;  sn_s2 <= 4'b0000;
        end else begin
            as_n_s1 <= as_n;     as_n_s2 <= as_n_s1;
            ds_n_s1 <= ds_n;     ds_n_s2 <= ds_n_s1;
            rw_n_s1 <= rw_n;     rw_n_s2 <= rw_n_s1;
            mreq_n_s1 <= mreq_n; mreq_n_s2 <= mreq_n_s1;
            bw_n_s1 <= bw_n;     bw_n_s2 <= bw_n_s1;
            st_s1 <= st;         st_s2 <= st_s1;
            sn_s1 <= sn;         sn_s2 <= sn_s1;
        end
    end

    // Forward synchronized signals
    assign as_n_out = as_n_s2;
    assign ds_n_out = ds_n_s2;
    assign rw_n_out = rw_n_s2;
    assign mreq_n_out = mreq_n_s2;
    assign bw_n_out = bw_n_s2;

    //------------------------------------------------------------------------
    // Bus Activity Tracking (matches M20FPGA bus_as_active)
    //------------------------------------------------------------------------
    reg bus_as_active;

    always @(posedge clk or negedge z8k_rst_n) begin
        if (!z8k_rst_n) begin
            bus_as_active <= 1'b0;
        end else if (!as_n_s2) begin
            // Set when AS goes active
            bus_as_active <= 1'b1;
        end
    end

    //------------------------------------------------------------------------
    // Bus Buffer Control (matches M20FPGA logic)
    //------------------------------------------------------------------------
    // OE always enabled
    assign buf_oe_n = 1'b0;

    // Direction control: fbusrd = frw && bus_as_active && fas
    // Note: as_n is active-LOW, so when as_n=1, AS is inactive (data phase possible)
    // When rw_n=1 (read) AND bus active AND AS inactive → FPGA drives to CPU
    // Otherwise → CPU drives to FPGA
    assign buf_dir = rw_n && bus_as_active && as_n;

    //------------------------------------------------------------------------
    // AD Bus Tristate Control
    //------------------------------------------------------------------------
    // FPGA drives the AD bus only during read data phase
    // (when buf_dir=1, meaning FPGA→CPU direction)
    wire fpga_drives = buf_dir && !ds_n;

    assign ad_bus = fpga_drives ? rdata : 16'bz;

    //------------------------------------------------------------------------
    // Write Data
    //------------------------------------------------------------------------
    // Write data is available on AD bus when CPU is driving
    assign wdata = ad_bus;

    //------------------------------------------------------------------------
    // Address Latch (matches M20FPGA: latch on rising edge of fas/AS)
    //------------------------------------------------------------------------
    // In M20FPGA: always @(posedge fas) z8000_addr <= sramData;
    // This latches on AS rising edge (end of address phase)

    // Use raw (unsynchronized) AS for timing-critical address latch
    // to minimize latency, similar to M20FPGA
    reg [15:0] ad_bus_latched;
    reg [3:0]  st_raw_latched;
    reg [3:0]  sn_raw_latched;

    always @(posedge as_n or negedge rst_n) begin
        if (!rst_n) begin
            ad_bus_latched <= 16'h0000;
            st_raw_latched <= 4'b0000;
            sn_raw_latched <= 4'b0000;
        end else begin
            // Latch address and status on AS rising edge
            ad_bus_latched <= ad_bus;
            st_raw_latched <= st;
            sn_raw_latched <= sn;
        end
    end

    // Transfer latched values to synchronized domain
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr <= 16'h0000;
            st_latched <= 4'b0000;
        end else if (!z8k_rst_n) begin
            addr <= 16'h0000;
            st_latched <= 4'b0000;
        end else begin
            addr <= ad_bus_latched;
            st_latched <= st_raw_latched;
        end
    end

endmodule
