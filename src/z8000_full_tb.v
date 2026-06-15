// Z8000 Full System Testbench - Direct BRAM test (no UART)
// Writes test data directly to BRAM, releases Z8000, checks bus trace.
// Uses z8000_bus_fpga wrapper (same as FPGA and Python --sim).

`timescale 1ns / 1ps

module z8000_full_tb;

    localparam CLK_PERIOD = 37.037;  // 27MHz

    reg         clk;
    reg         rst_n;
    reg         z8k_rst_n;

    // Bus interface signals
    wire [15:0] z8k_addr;
    wire [15:0] z8k_wdata;
    wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
    wire [3:0]  cpu_st;
    wire        cpu_halt_n;
    wire        z8k_cpu_clk;
    reg  [15:0] data_to_cpu;

    // BRAM
    wire [15:0] rd_data;

    // Clock
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // ==========================================
    // Z8000 Bus Interface (same wrapper as FPGA and Python --sim)
    // ==========================================
    z8000_bus_fpga bus_if (
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
        .halt_n     (cpu_halt_n),
        .cpu_clk    (z8k_cpu_clk)
    );

    // ==========================================
    // Dual-Port BRAM
    // Port A: testbench load (directly from initial block)
    // Port B: Z8000 CPU (via bus_fpga)
    // ==========================================
    // Status latch (ST valid while AS is low)
    reg [3:0] st_latched;
    always @(posedge clk) begin
        if (!rst_n)
            st_latched <= 4'b0;
        else if (~cpu_as_n)
            st_latched <= cpu_st;
    end

    wire io_sel  = (st_latched == 4'b0010) || (st_latched == 4'b0011);
    wire ram_sel = ~cpu_mreq_n && ~io_sel;

    wire z8k_ram_write = ram_sel && ~cpu_rw_n && ~cpu_ds_n;
    wire z8k_we_hi = z8k_ram_write && (~cpu_bw_n || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (~cpu_bw_n ||  z8k_addr[0]);

    ram16 bram (
        // Port A - testbench (unused during CPU run)
        .clka    (clk),
        .wea_hi  (1'b0),
        .wea_lo  (1'b0),
        .addra   (15'd0),
        .dina    (16'd0),
        .douta   (),
        // Port B - Z8000 CPU
        .clkb    (clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
        .addrb   ({2'b00, z8k_addr[12:0]}),
        .dinb    (z8k_wdata),
        .doutb   (rd_data)
    );

    // Data bus mux
    always @(*) begin
        if (ram_sel)
            data_to_cpu = rd_data;
        else
            data_to_cpu = 16'hFFFF;
    end

    // ==========================================
    // Bus monitor - capture on DS_n RISING (end of bus cycle)
    // ==========================================
    reg        prev_ds_n;
    wire       ds_rising = ~prev_ds_n && cpu_ds_n;
    reg [15:0] trace_addr [0:63];
    reg [15:0] trace_data_log [0:63];
    reg        trace_rw   [0:63];
    reg [3:0]  trace_st   [0:63];
    integer    trace_count;

    // Latch data during DS_n active (when data is valid)
    reg [15:0] capture_addr;
    reg [15:0] capture_data;
    reg        capture_rw;
    reg [3:0]  capture_st;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            prev_ds_n <= 1'b1;
        else
            prev_ds_n <= cpu_ds_n;
    end

    // Continuously update capture regs while DS_n is active
    always @(posedge clk) begin
        if (~cpu_ds_n) begin
            capture_addr <= z8k_addr;
            capture_data <= cpu_rw_n ? data_to_cpu : z8k_wdata;
            capture_rw <= cpu_rw_n;
            capture_st <= st_latched;  // Use latched ST (valid from AS phase)
        end
    end

    // Record on DS_n rising (bus cycle complete)
    always @(posedge clk) begin
        if (rst_n && ds_rising && trace_count < 64) begin
            trace_addr[trace_count] = capture_addr;
            trace_data_log[trace_count] = capture_data;
            trace_rw[trace_count] = capture_rw;
            trace_st[trace_count] = capture_st;
            trace_count = trace_count + 1;
        end
    end

    // ==========================================
    // Test
    // ==========================================
    integer i;
    integer pass_count, fail_count;

    initial begin
        $dumpfile("z8000_full.vcd");
        $dumpvars(0, z8000_full_tb);

        rst_n = 0;
        z8k_rst_n = 0;
        trace_count = 0;
        pass_count = 0;
        fail_count = 0;

        $display("");
        $display("========================================");
        $display("Z8000 Full System Test (via z8000_bus_fpga)");
        $display("========================================");

        // Write reset vectors and test code directly into BRAM.
        // Reset vector: FCW = 0x4000 at byte addr 0x0002 (word addr 1)
        bram.mem_hi[1] = 8'h40;
        bram.mem_lo[1] = 8'h00;

        // Reset vector: PC = 0x0040 at byte addr 0x0004 (word addr 2)
        bram.mem_hi[2] = 8'h00;
        bram.mem_lo[2] = 8'h40;

        // HALT at 0x0040 to stop immediately after reset vector
        bram.mem_hi[32] = 8'h7A;   // word addr 32 = byte addr 0x0040
        bram.mem_lo[32] = 8'h00;   // HALT = 0x7A00

        // Release system reset first
        #100;
        $display("Releasing system reset...");
        @(posedge clk);
        rst_n = 1;

        // Then release Z8000 reset (matches Python --sim flow)
        repeat (4) @(posedge clk);
        $display("Releasing Z8000 reset...");
        z8k_rst_n = 1;

        // ---- Wait for HALT or timeout ----
        fork
            begin : wait_halt
                @(negedge cpu_halt_n);
                $display("Z8000 halted after %0d bus cycles.", trace_count);
                disable wait_timeout;
            end
            begin : wait_timeout
                #500000;  // 500us timeout
                $display("*** TIMEOUT - Z8000 did not halt after %0d bus cycles ***", trace_count);
                disable wait_halt;
            end
        join

        // Let bus settle
        #500;

        // ---- Print trace ----
        $display("");
        $display("Bus trace (%0d entries):", trace_count);
        $display("  #   ADDR  DATA  R/W  ST");
        for (i = 0; i < trace_count && i < 32; i = i + 1) begin
            $display("  %03d: %04h  %04h  %s    %04b",
                i, trace_addr[i], trace_data_log[i],
                trace_rw[i] ? "R" : "W", trace_st[i]);
        end

        // ---- Check reset vector reads ----
        $display("");
        if (trace_count >= 2) begin
            if (trace_addr[0] == 16'h0002 && trace_data_log[0] == 16'h4000) begin
                $display("PASS: FCW = 0x4000 from addr 0x0002");
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL: First read addr=%04h data=%04h (expected 0002/4000)",
                    trace_addr[0], trace_data_log[0]);
                fail_count = fail_count + 1;
            end

            if (trace_addr[1] == 16'h0004 && trace_data_log[1] == 16'h0040) begin
                $display("PASS: PC = 0x0040 from addr 0x0004");
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL: Second read addr=%04h data=%04h (expected 0004/0040)",
                    trace_addr[1], trace_data_log[1]);
                fail_count = fail_count + 1;
            end
        end else begin
            $display("FAIL: Not enough bus activity (%0d entries)", trace_count);
            fail_count = fail_count + 2;
        end

        // ---- Check HALT fetch at 0x0040 ----
        if (trace_count >= 3) begin
            if (trace_addr[2] == 16'h0040 && trace_data_log[2] == 16'h7A00 && trace_st[2] == 4'b1101) begin
                $display("PASS: HALT (0x7A00) fetched from addr 0x0040");
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL: Third entry addr=%04h data=%04h st=%04b (expected 0040/7A00/1101)",
                    trace_addr[2], trace_data_log[2], trace_st[2]);
                fail_count = fail_count + 1;
            end
        end

        // ---- Check CPU halted ----
        if (!cpu_halt_n) begin
            $display("PASS: CPU is halted");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: CPU is not halted");
            fail_count = fail_count + 1;
        end

        // ---- Summary ----
        $display("");
        $display("========================================");
        $display("Test Summary: %0d PASS, %0d FAIL", pass_count, fail_count);
        $display("========================================");

        #1000;
        $finish;
    end

endmodule
