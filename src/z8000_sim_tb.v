// Z8000 Simulation Testbench for Python Test Framework
// Mirrors the FPGA top module bus architecture (z8000_test_harness_top.v):
//   z8000_bus_fpga + ram16 + z8k_io_ports + trace_buffer
//
// Memory loaded via $readmemh plusargs (+bram_hi=, +bram_lo=, +io_preload=).
// After halt (or timeout), prints parseable results to stdout.

`timescale 1ns / 1ps

module z8000_sim_tb;

    localparam CLK_PERIOD = 37.037;  // 27MHz

    reg         clk;
    reg         rst_n;
    reg         z8k_rst_n;

    // Clock
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // ==========================================
    // Signal declarations
    // ==========================================
    wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
    wire [3:0]  cpu_st;
    wire        cpu_halt_n;
    wire [15:0] z8k_addr;
    wire [15:0] z8k_wdata;
    wire [6:0]  z8k_sn;
    wire        z8k_cpu_clk;
    reg  [15:0] data_to_cpu;

    // Trace buffer signals
    reg  [9:0]  trace_rd_addr;
    wire [35:0] trace_rd_data;
    wire [9:0]  trace_wr_count;
    wire        trace_active;

    // I/O port signals
    wire [15:0] z8k_io_rdata;

    // Instrumentation
    reg [31:0] cycle_count = 32'd0;
    reg [15:0] fetch_count = 16'd0;
    reg [31:0] instr_cycle_count = 32'd0;
    reg        prev_as_n = 1'b1;
    reg        counting = 1'b1;

    // ==========================================
    // Z8000 Bus Interface (CPU + clock divider)
    // ==========================================
    z8001_bus_fpga bus_if (
        .clk        (clk),
        .rst_n      (rst_n),
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
        .sn         (z8k_sn),
        .halt_n     (cpu_halt_n),
        .cpu_clk    (z8k_cpu_clk)
    );

    // ==========================================
    // Instrumentation (simplified for simulation)
    // ==========================================
    // Count CPU clock cycles from reset release to halt
    always @(posedge z8k_cpu_clk or negedge z8k_rst_n) begin
        if (!z8k_rst_n) begin
            cycle_count <= 32'd0;
            counting <= 1'b1;
        end else if (counting) begin
            if (!cpu_halt_n)
                counting <= 1'b0;
            else
                cycle_count <= cycle_count + 1'b1;
        end
    end

    // Count opcode fetches (AS falling with ST=1101)
    always @(posedge clk) begin
        if (!z8k_rst_n) begin
            fetch_count <= 16'd0;
            prev_as_n <= 1'b1;
        end else begin
            prev_as_n <= cpu_as_n;
            if (prev_as_n && ~cpu_as_n && cpu_st == 4'b1101)
                fetch_count <= fetch_count + 1'b1;
        end
    end

    // Count CPU clock cycles while trace_active (address-gated test code)
    reg prev_cpu_clk_ic = 1'b0;
    always @(posedge clk) begin
        if (!z8k_rst_n) begin
            instr_cycle_count <= 32'd0;
            prev_cpu_clk_ic <= 1'b0;
        end else begin
            prev_cpu_clk_ic <= z8k_cpu_clk;
            if (trace_active && z8k_cpu_clk && ~prev_cpu_clk_ic)
                instr_cycle_count <= instr_cycle_count + 1'b1;
        end
    end

    // ==========================================
    // Status latch (ST valid on AS falling edge only)
    // ==========================================
    reg [3:0] st_latched;
    always @(posedge clk) begin
        if (!z8k_rst_n)
            st_latched <= 4'b0;
        else if (prev_as_n && ~cpu_as_n)
            st_latched <= cpu_st;
    end

    // ==========================================
    // Address decode (same as top module)
    // ==========================================
    wire io_std_sel = (st_latched == 4'b0010);   // Standard I/O (ST=0010)
    wire io_spc_sel = (st_latched == 4'b0011);   // Special I/O (ST=0011)
    wire io_sel  = io_std_sel || io_spc_sel;
    wire ram_sel = ~cpu_mreq_n && ~io_sel;

    wire io_port_match = io_sel && (z8k_addr[15:4] == 12'h010);
    // Register index: addr[3:1] (0-5) + 6 if special I/O
    wire [3:0] z8k_io_reg_sel = z8k_addr[3:1] + (io_spc_sel ? 4'd6 : 4'd0);

    // ==========================================
    // True Dual-Port BRAM (behavioral)
    // ==========================================
    wire z8k_ram_write = ram_sel && ~cpu_rw_n && ~cpu_ds_n;
    wire z8k_we_hi = z8k_ram_write && (~cpu_bw_n || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (~cpu_bw_n ||  z8k_addr[0]);

    wire [15:0] z8k_rd_data;

    ram16 bram (
        // Port A - unused (testbench loads via $readmemh)
        .clka    (clk),
        .wea_hi  (1'b0),
        .wea_lo  (1'b0),
        .addra   (13'd0),
        .dina    (16'd0),
        .douta   (),
        // Port B - Z8000 CPU (segment-addressed: sn[0] banks upper 4KB)
        .clkb    (clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
`ifdef Z8001_MODE
        .addrb   ({z8k_sn[0], z8k_addr[11:0]}),
`else
        .addrb   (z8k_addr[12:0]),
`endif
        .dinb    (z8k_wdata),
        .doutb   (z8k_rd_data)
    );

    // ==========================================
    // I/O Port Registers
    // ==========================================
    wire z8k_io_wr = io_port_match && ~cpu_rw_n && ~cpu_ds_n;

    z8k_io_ports io_ports (
        .clk           (clk),
        .rst_n         (rst_n),
        .z8k_reg_sel   (z8k_io_reg_sel),
        .z8k_wdata     (z8k_wdata),
        .z8k_rdata     (z8k_io_rdata),
        .z8k_wr        (z8k_io_wr),
        .z8k_bw_n      (cpu_bw_n),
        .z8k_addr_lsb  (z8k_addr[0]),
        // Z80 side - unused in sim
        .z80_reg_sel   (4'd0),
        .z80_wbyte     (8'd0),
        .z80_rdata     (),
        .z80_wr_lo     (1'b0),
        .z80_wr_hi     (1'b0)
    );

    // ==========================================
    // Data bus mux (same as top module)
    // ==========================================
    always @(*) begin
        if (ram_sel)
            data_to_cpu = z8k_rd_data;
        else if (io_port_match)
            data_to_cpu = z8k_io_rdata;
        else
            data_to_cpu = 16'hFFFF;
    end

    // ==========================================
    // Trace Buffer
    // ==========================================
    wire [15:0] trace_data = cpu_rw_n ? data_to_cpu : z8k_wdata;

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
        .wr_count   (trace_wr_count),
        .trace_active(trace_active)
    );

    // ==========================================
    // Simulation
    // ==========================================
    reg [1024*8-1:0] bram_hi_path;
    reg [1024*8-1:0] bram_lo_path;
    reg [1024*8-1:0] io_preload_path;
    integer i;
    reg got_halt;

    // Temp regs for trace readback
    reg [15:0] t_addr;
    reg [15:0] t_data;
    reg        t_rw;
    reg        t_bw;
    reg        t_io;

    initial begin
        rst_n = 0;
        z8k_rst_n = 0;
        trace_rd_addr = 10'd0;
        got_halt = 0;

        // Load memory images
        if ($value$plusargs("bram_hi=%s", bram_hi_path))
            $readmemh(bram_hi_path, bram.mem_hi);
        if ($value$plusargs("bram_lo=%s", bram_lo_path))
            $readmemh(bram_lo_path, bram.mem_lo);

        // Release system reset
        #100;
        @(posedge clk);
        rst_n = 1;

        // Wait for reset to propagate (clears I/O regs)
        repeat (2) @(posedge clk);

        // Load I/O preloads AFTER reset (so they aren't cleared by rst_n)
        if ($value$plusargs("io_preload=%s", io_preload_path))
            $readmemh(io_preload_path, io_ports.regs);

        // Release Z8000 reset
        repeat (2) @(posedge clk);
        z8k_rst_n = 1;

        // Wait for halt or timeout
        fork
            begin : wait_halt
                @(negedge cpu_halt_n);
                got_halt = 1;
                disable wait_timeout;
            end
            begin : wait_timeout
                #2000000;  // 2ms timeout
                disable wait_halt;
            end
        join

        // Let bus settle
        repeat (10) @(posedge clk);

        // ---- Output results ----

        // Execution result
        if (got_halt)
            $display("RESULT:HALT");
        else
            $display("RESULT:TOUT");

        // Registers from dump area
`ifdef Z8001_MODE
        // Segmented: 0x0140-0x015F = word addrs 160-175
        for (i = 0; i < 16; i = i + 1) begin
            $display("REG:%0d:%04x", i,
                {bram.mem_hi[160 + i], bram.mem_lo[160 + i]});
        end
        // FCW from dump area (0x0162 = word addr 177)
        $display("FCW:%04x", {bram.mem_hi[177], bram.mem_lo[177]});
`else
        // Non-segmented: 0x0090-0x00AF = word addrs 72-87
        for (i = 0; i < 16; i = i + 1) begin
            $display("REG:%0d:%04x", i,
                {bram.mem_hi[72 + i], bram.mem_lo[72 + i]});
        end
        // FCW from dump area (0x00B2 = word addr 89)
        $display("FCW:%04x", {bram.mem_hi[89], bram.mem_lo[89]});
`endif

`ifdef Z8001_MODE
        // Seg 0 short-DA area: 0x0090-0x013F (word addrs 90-159)
        // Covers gap between non-seg dump area and seg dump area,
        // where short-form DA tests (offset < 256) store data.
        for (i = 90; i < 160; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
`endif
        // Memory readback: test code + operand + block + stack areas
        // 0x0200-0x07FF (word addrs 256-1023)
        for (i = 256; i < 1024; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
        // 0x0E00-0x0F0F (word addrs 1792-1927) — stack area
        for (i = 1792; i < 1928; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
`ifdef Z8001_MODE
        // Segment 1 area: word addrs 2048+256..2048+1023 = 2304..3071
        // Maps to byte addrs 0x1200-0x17FE (seg 1 offsets 0x200-0x7FE)
        for (i = 2304; i < 3072; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
`endif
        // Dump area
`ifdef Z8001_MODE
        // 0x0140-0x0163 (word addrs 160-177) — segmented dump area
        for (i = 160; i < 178; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
`else
        // 0x0090-0x00B3 (word addrs 72-89) — non-segmented dump area
        for (i = 72; i < 90; i = i + 1) begin
            $display("MEM:%04h:%04h", i[12:0] * 2,
                {bram.mem_hi[i], bram.mem_lo[i]});
        end
`endif

        // I/O port registers
        for (i = 0; i < 12; i = i + 1) begin
            $display("IO:%02x:%04x", i, io_ports.regs[i]);
        end

        // Cycle/fetch counts
        $display("CYCLES:%08x", cycle_count);
        $display("FETCHES:%04x", fetch_count);
        $display("INSTR_CYCLES:%08x", instr_cycle_count);

        // Trace entries — synchronous BRAM read, need clock edges
        for (i = 0; i < trace_wr_count; i = i + 1) begin
            trace_rd_addr = i[9:0];
            @(posedge clk);  // Address registered
            @(posedge clk);  // Data available
            t_addr = trace_rd_data[15:0];
            t_data = trace_rd_data[31:16];
            t_rw   = trace_rd_data[32];
            t_bw   = trace_rd_data[33];
            t_io   = trace_rd_data[34];
            $display("TRACE:%03x:%04x:%04x:%s:%s:%s",
                i, t_addr, t_data,
                t_rw ? "R" : "W",
                t_bw ? "B" : "W",
                t_io ? "I" : "M");
        end

        $display("DONE");
        $finish;
    end

endmodule
