// Z8000 Bus Trace Buffer
// Captures Z8000 memory and I/O operations for debugging
//
// Write port: Captures on DS_n rising edge (end of bus cycle, data valid)
// Read port: Z80 access via I/O ports
//
// Entry format (36 bits):
//   [15:0]  - Address (16 bits)
//   [31:16] - Data (16 bits)
//   [32]    - R/W (1=read, 0=write)
//   [33]    - B/W (0=byte, 1=word)
//   [34]    - MEM/IO (0=memory, 1=I/O)
//   [35]    - Segment bank bit (sn[0]): 0=segment-0 bank, 1=segment-1 bank

module trace_buffer (
    input         clk,            // System clock
    input         rst_n,
    input         z8k_rst_n,      // Z8000 reset (clears buffer)

    // Z8000 bus signals
    input  [15:0] z8k_addr,       // Latched address
    input  [15:0] z8k_data,       // Bus data
    input         z8k_as_n,       // Address strobe
    input         z8k_ds_n,       // Data strobe
    input         z8k_rw_n,       // Read/Write (1=read)
    input         z8k_bw_n,       // Byte/Word (0=word, 1=byte)
    input         z8k_mreq_n,     // Memory request
    input  [3:0]  z8k_st,         // Status (for I/O detect)
    input         z8k_sn,         // Segment bank bit (sn[0]) for this access

    // Z80 read interface
    input  [9:0]  rd_addr,        // Read address (0-1023)
    output [35:0] rd_data,        // Read data (36 bits)
    output [9:0]  wr_count,       // Number of entries captured

    // Address-gated trace active indicator
    output reg    trace_active
);

    // I/O detect (uses latched ST, see below)
    wire io_cycle = (latched_st == 4'b0010) || (latched_st == 4'b0011);

    // Capture on DS_n rising edge (end of bus cycle - data is valid)
    reg ds_n_prev;
    wire ds_rising = ~ds_n_prev && z8k_ds_n;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            ds_n_prev <= 1'b1;
        else
            ds_n_prev <= z8k_ds_n;
    end

    // Write pointer (10 bits for 1024 entries)
    reg [9:0] wr_ptr;
    reg       buffer_full;

    // Edge detect for z8k_rst_n rising (to skip first cycle after CPU reset release)
    reg z8k_rst_n_d;
    wire z8k_rst_rising = z8k_rst_n && !z8k_rst_n_d;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            z8k_rst_n_d <= 1'b0;
        else
            z8k_rst_n_d <= z8k_rst_n;
    end

    // Address-range gating: only trace when executing test code (>= 0x0200).
    // Tracks first opcode fetch (ST=1101) address to set/clear trace_active.
    // All bus cycles (data, I/O, stack) while trace_active are captured.
    wire first_fetch = (z8k_st == 4'b1101);

    // Latch ST at AS_n (valid at start of bus cycle)
    reg [3:0] latched_st;
    reg       as_n_prev;
    wire      as_falling = as_n_prev && ~z8k_as_n;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            as_n_prev <= 1'b1;
        else
            as_n_prev <= z8k_as_n;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            latched_st <= 4'd0;
        else if (as_falling)
            latched_st <= z8k_st;
    end

    // Update trace_active on completed bus cycles that are first opcode fetches
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            trace_active <= 1'b0;
        else if (z8k_rst_rising)
            trace_active <= 1'b0;
        else if (ds_rising && latched_st == 4'b1101) begin
            // First opcode fetch completed - gate on address
            trace_active <= (latched_addr >= 16'h0200);
        end
    end

    // Capture enable: DS rising, buffer not full, CPU not in reset, trace active
    wire capture_en = z8k_rst_n && !z8k_rst_rising && ds_rising && !buffer_full && trace_active;

    // Latch bus signals while DS_n is active (data becomes valid during this phase)
    reg [15:0] latched_addr;
    reg [15:0] latched_data;
    reg        latched_rw_n;
    reg        latched_bw_n;
    reg        latched_io;
    reg        latched_sn;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            latched_addr <= 16'd0;
            latched_data <= 16'd0;
            latched_rw_n <= 1'b1;
            latched_bw_n <= 1'b1;
            latched_io   <= 1'b0;
            latched_sn   <= 1'b0;
        end else if (~z8k_ds_n) begin
            // Continuously update while DS_n is active
            latched_addr <= z8k_addr;
            latched_data <= z8k_data;
            latched_rw_n <= z8k_rw_n;
            latched_bw_n <= z8k_bw_n;
            latched_io   <= io_cycle;
            latched_sn   <= z8k_sn;
        end
    end

    // Build trace entry from latched values (valid at DS_n rising)
    wire [35:0] trace_entry = {
        latched_sn,     // [35] segment bank bit (sn[0])
        latched_io,     // [34] MEM/IO (1=I/O)
        latched_bw_n,   // [33] B/W (1=byte)
        latched_rw_n,   // [32] R/W (1=read)
        latched_data,   // [31:16] data
        latched_addr    // [15:0] address
    };

    // Write pointer and full flag management
    // Clear on global reset OR when Z8000 comes OUT of reset (new execution)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 10'd0;
            buffer_full <= 1'b0;
        end else if (z8k_rst_rising) begin
            // Clear when starting new execution (CPU coming out of reset)
            wr_ptr <= 10'd0;
            buffer_full <= 1'b0;
        end else if (capture_en) begin
            if (wr_ptr == 10'd1023) begin
                buffer_full <= 1'b1;
            end else begin
                wr_ptr <= wr_ptr + 1'b1;
            end
        end
    end

    assign wr_count = wr_ptr;

`ifdef SIMULATION
    // Behavioral model for simulation
    reg [35:0] mem [0:1023];
    reg [35:0] rd_data_reg;

    always @(posedge clk) begin
        if (capture_en)
            mem[wr_ptr] <= trace_entry;
        rd_data_reg <= mem[rd_addr];
    end

    assign rd_data = rd_data_reg;

`else
    // Gowin SDPB for synthesis
    wire [35:0] sdp_dout;

    Gowin_SDPB trace_ram (
        // Write port (directly accent accent accent accent Z8000 capture)
        .clka   (clk),
        .cea    (capture_en),
        .reseta (1'b0),
        .ada    (wr_ptr),
        .din    (trace_entry),

        // Read port (Z80 access)
        .clkb   (clk),
        .ceb    (1'b1),
        .resetb (1'b0),
        .adb    (rd_addr),
        .dout   (sdp_dout),
        .oce    (1'b1)
    );

    assign rd_data = sdp_dout;

`endif

endmodule
