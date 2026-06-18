//============================================================================
// Z8001 External Test Harness - Top Level Module
// Target: Altera Cyclone IV (Quartus project)
//
// Wires an external Z8001 CPU to FPGA BRAM via 74LVC245 level shifters.
// Z80 harness controller manages test execution over UART.
//
// Features:
// - Z8001 bus interface via z8001_bus_external
// - 8KB dual-port BRAM (Port A: Z80, Port B: Z8001)
// - I/O LED latch (any Z8001 I/O write sets LED register)
// - Halt detection via opcode sniffing (0x7A00 on first fetch)
// - Cycle/fetch counting instrumentation
// - Bus trace capture buffer (1024 entries, address-gated)
//============================================================================

module z8001_ext_test_top (
    // System
    input  wire        clk,             // 50 MHz oscillator (T2)
    input  wire        n_reset,         // Active-low reset button (W13)

    // Serial Port 1 (UART)
    input  wire        urxd1,           // UART RX from external (B18)
    output wire        utxd1,           // UART TX to external (B22)

    // LED
    output wire        driveLED,        // Activity LED (E4)

    // External SRAM control (disabled)
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

    // Z8001 CPU inputs (from CPU via level shifters)
    input  wire        fas,             // Address strobe (A8)
    input  wire        fds,             // Data strobe (A9)
    input  wire        fbw,             // Byte/Word (A7)
    input  wire        fmreq,           // Memory request (A10)
    input  wire        frw,             // Read/Write (A13)
    input  wire [3:0]  fst,             // Status ST0-ST3 (D2,C1,C2,B1)
    input  wire [3:0]  fsn,             // Segment SN0-SN3 (R1,N1,N2,M1)

    // Z8001 AD bus (via 74LVC245)
    inout  wire [15:0] sramData         // Bidirectional data bus
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
    //------------------------------------------------------------------------
    assign n_sRamCS0 = 1'b1;
    assign n_sRamCS1 = 1'b1;
    assign n_sRamOE  = 1'b1;
    assign n_sRamWE  = 1'b1;

    //------------------------------------------------------------------------
    // Z8001 CPU Control
    //------------------------------------------------------------------------
    wire z8k_rst_n;                      // From Z80 harness

    assign fclk    = clk_4mhz;
    assign freset  = z8k_rst_n;         // 0=reset, 1=run (matches original bring-up convention)
    assign fbreq   = 1'b1;              // No bus request
    assign fwait   = 1'b1;              // No wait states
    assign fnvi    = 1'b1;              // No non-vectored interrupt
    assign fvi     = 1'b1;              // No vectored interrupt
    assign fnmi    = 1'b1;              // No NMI

    //------------------------------------------------------------------------
    // Z8001 Bus Interface
    //------------------------------------------------------------------------
    wire [15:0] z8k_addr;               // Latched address from bus interface
    wire [15:0] z8k_wdata;              // Write data from CPU
    wire [15:0] data_to_cpu;            // Read data to CPU
    wire [3:0]  z8k_st;                 // Latched status
    wire        z8k_as_n_sync;          // Synchronized AS
    wire        z8k_ds_n_sync;          // Synchronized DS
    wire        z8k_rw_n_sync;          // Synchronized R/W
    wire        z8k_mreq_n_sync;        // Synchronized MREQ
    wire        z8k_bw_n_sync;          // Synchronized B/W

    z8001_bus_external bus_if (
        .clk        (sys_clk),
        .rst_n      (sys_rst_n),
        .z8k_rst_n  (z8k_rst_n),
        .cpu_clk    (clk_4mhz),
        .as_n       (fas),
        .ds_n       (fds),
        .bw_n       (fbw),
        .mreq_n     (fmreq),
        .rw_n       (frw),
        .st         (fst),
        .sn         (fsn),
        .ad_bus     (sramData),
        .buf_oe_n   (fbuscs),
        .buf_dir    (fbusrd),
        .addr       (z8k_addr),
        .wdata      (z8k_wdata),
        .rdata      (data_to_cpu),
        .st_latched (z8k_st),
        .as_n_out   (z8k_as_n_sync),
        .ds_n_out   (z8k_ds_n_sync),
        .rw_n_out   (z8k_rw_n_sync),
        .mreq_n_out (z8k_mreq_n_sync),
        .bw_n_out   (z8k_bw_n_sync)
    );

    //------------------------------------------------------------------------
    // Segment Number Latch
    // Latch SN on AS rising edge (same timing as bus_if internal latch).
    // SN[0] is used as BRAM address bit 12 to split 8KB BRAM into 2x4KB:
    //   SN=0 → BRAM 0x0000-0x0FFF (Z8001 segment 0)
    //   SN=1 → BRAM 0x1000-0x1FFF (Z8001 segment 1)
    // Backward-compatible: non-segmented tests use SN=0, all addresses < 0x1000.
    //------------------------------------------------------------------------
    reg [3:0] sn_latched;
    always @(posedge fas or negedge sys_rst_n) begin
        if (!sys_rst_n)
            sn_latched <= 4'b0000;
        else
            sn_latched <= fsn;
    end

    //------------------------------------------------------------------------
    // Address Decode
    //------------------------------------------------------------------------
    wire io_std_sel = (z8k_st == 4'b0010);   // Standard I/O (ST=0010)
    wire io_spc_sel = (z8k_st == 4'b0011);   // Special I/O (ST=0011)
    wire io_sel  = io_std_sel || io_spc_sel;
    wire ram_sel = ~z8k_mreq_n_sync && ~io_sel;

    // I/O port address match: Z8000 addresses 0x0100-0x010A
    wire io_port_match = io_sel && (z8k_addr[15:4] == 12'h010);
    // Register index: addr[3:1] (0-5) + 6 if special I/O
    wire [3:0] z8k_io_reg_sel = z8k_addr[3:1] + (io_spc_sel ? 4'd6 : 4'd0);

    //------------------------------------------------------------------------
    // UART
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
    // Halt Detection - Opcode Sniffing
    // Detect HALT by matching opcode 0x7A00 during first opcode fetch (ST=1101)
    //
    // data_to_cpu depends on ram_sel (uses synchronized MREQ). At ds_rising,
    // MREQ may have already deasserted, making data_to_cpu = 0xFFFF.
    // Fix: latch data_to_cpu while DS is active, check latched value at ds_rising.
    //------------------------------------------------------------------------
    reg halt_detected;
    reg ds_n_prev;
    wire ds_rising = ~ds_n_prev && z8k_ds_n_sync;
    wire z8k_ds_falling = ds_n_prev && ~z8k_ds_n_sync;
    wire first_fetch_cycle = (z8k_st == 4'b1101);

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            ds_n_prev <= 1'b1;
        else
            ds_n_prev <= z8k_ds_n_sync;
    end

    // Latch data while DS is active (ram_sel still valid during data phase)
    reg [15:0] latched_cpu_data;
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            latched_cpu_data <= 16'h0000;
        else if (~z8k_ds_n_sync)
            latched_cpu_data <= data_to_cpu;
    end

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            halt_detected <= 1'b0;
        else if (!z8k_rst_n)
            halt_detected <= 1'b0;      // Clear on CPU reset
        else if (ds_rising && first_fetch_cycle && latched_cpu_data == 16'h7A00)
            halt_detected <= 1'b1;       // HALT opcode fetched
    end

    wire z8k_halt_n = ~halt_detected;

    //------------------------------------------------------------------------
    // Instrumentation (Cycle/Fetch Counting)
    // Clears on z8k_rst_n rising edge (reset release = new execution)
    //------------------------------------------------------------------------
    reg        bus_active;
    reg [31:0] cycle_count;
    reg [15:0] fetch_count;
    reg        prev_as_n;
    reg        counting;
    reg        cycle_timeout;
    reg [31:0] instr_cycle_count;
    wire [31:0] z8k_cycle_limit;

    reg z8k_rst_n_prev;
    always @(posedge sys_clk) z8k_rst_n_prev <= z8k_rst_n;
    wire z8k_start = z8k_rst_n && !z8k_rst_n_prev;

    wire as_falling = prev_as_n && ~z8k_as_n_sync;
    wire opcode_fetch = as_falling && (z8k_st == 4'b1101);

    // CPU clock edge detection: clk_4mhz is a PLL output on the global
    // clock network and cannot be sampled as data by sys_clk flip-flops.
    // Use a toggle register in the clk_4mhz domain, then detect edges
    // of the synchronized toggle in the sys_clk domain.
    reg cpu_clk_toggle;
    always @(posedge clk_4mhz or negedge sys_rst_n) begin
        if (!sys_rst_n)
            cpu_clk_toggle <= 1'b0;
        else
            cpu_clk_toggle <= ~cpu_clk_toggle;
    end

    reg cpu_clk_toggle_s1, cpu_clk_toggle_s2;
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n) begin
            cpu_clk_toggle_s1 <= 1'b0;
            cpu_clk_toggle_s2 <= 1'b0;
        end else begin
            cpu_clk_toggle_s1 <= cpu_clk_toggle;
            cpu_clk_toggle_s2 <= cpu_clk_toggle_s1;
        end
    end

    wire cpu_clk_rising = cpu_clk_toggle_s1 ^ cpu_clk_toggle_s2;

    always @(posedge sys_clk) begin
        if (z8k_start) begin
            bus_active <= 1'b0;
            cycle_count <= 32'd0;
            fetch_count <= 16'd0;
            prev_as_n <= 1'b1;
            counting <= 1'b1;
            cycle_timeout <= 1'b0;
            instr_cycle_count <= 32'd0;
        end else begin
            prev_as_n <= z8k_as_n_sync;

            if (as_falling && !bus_active)
                bus_active <= 1'b1;

            if (halt_detected)
                counting <= 1'b0;

            if (counting && !halt_detected && cpu_clk_rising)
                cycle_count <= cycle_count + 1'b1;

            if (counting && !halt_detected && opcode_fetch)
                fetch_count <= fetch_count + 1'b1;

            if (counting && (z8k_cycle_limit != 32'd0) && (cycle_count >= z8k_cycle_limit))
                cycle_timeout <= 1'b1;

            if (trace_active && cpu_clk_rising)
                instr_cycle_count <= instr_cycle_count + 1'b1;
        end
    end

    //------------------------------------------------------------------------
    // Trace Buffer
    //------------------------------------------------------------------------
    wire [9:0]  trace_rd_addr;
    wire [35:0] trace_rd_data;
    wire [9:0]  trace_wr_count;
    wire        trace_active;

    wire [15:0] trace_data = z8k_rw_n_sync ? data_to_cpu : z8k_wdata;

    trace_buffer_altera trace (
        .clk        (sys_clk),
        .rst_n      (sys_rst_n),
        .z8k_rst_n  (z8k_rst_n),
        .z8k_addr   (z8k_addr),
        .z8k_data   (trace_data),
        .z8k_as_n   (z8k_as_n_sync),
        .z8k_ds_n   (z8k_ds_n_sync),
        .z8k_rw_n   (z8k_rw_n_sync),
        .z8k_bw_n   (z8k_bw_n_sync),
        .z8k_mreq_n (z8k_mreq_n_sync),
        .z8k_st     (z8k_st),
        .rd_addr    (trace_rd_addr),
        .rd_data    (trace_rd_data),
        .wr_count   (trace_wr_count),
        .trace_active(trace_active)
    );

    //------------------------------------------------------------------------
    // Z80 Harness Controller
    //------------------------------------------------------------------------
    wire        z8k_mem_we;
    wire [14:0] z80_addr;
    wire [15:0] z8k_mem_wdata;
    wire [15:0] z8k_mem_rdata;

    // I/O port register signals (Z80 side)
    wire [3:0]  z80_io_reg_sel;
    wire [7:0]  z80_io_wbyte;
    wire [15:0] z80_io_rdata;
    wire        z80_io_wr_lo;
    wire        z80_io_wr_hi;
    wire [3:0]  z80_io_seq_reg_sel;
    wire [1:0]  z80_io_seq_slot_sel;
    wire [7:0]  z80_io_seq_wbyte;
    wire        z80_io_seq_wr_lo;
    wire        z80_io_seq_wr_hi;
    wire        z80_io_seq_clear;

    // I/O port register signals (Z8000 side)
    wire [15:0] z8k_io_rdata;

    z80_harness z80 (
        .clk            (sys_clk),
        .rst_n          (sys_rst_n),
        .uart_rx_data   (uart_rx_data),
        .uart_rx_valid  (uart_rx_valid),
        .uart_rx_ready  (uart_rx_ready),
        .uart_tx_data   (uart_tx_data),
        .uart_tx_valid  (uart_tx_valid),
        .uart_tx_ready  (uart_tx_ready),
        .z8k_rst_n      (z8k_rst_n),
        .z8k_halt_n     (z8k_halt_n),
        .z8k_st         (z8k_st),
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
        .io_seq_reg_sel (z80_io_seq_reg_sel),
        .io_seq_slot_sel(z80_io_seq_slot_sel),
        .io_seq_wbyte   (z80_io_seq_wbyte),
        .io_seq_wr_lo   (z80_io_seq_wr_lo),
        .io_seq_wr_hi   (z80_io_seq_wr_hi),
        .io_seq_clear   (z80_io_seq_clear),
        .z8k_instr_cycle_count(instr_cycle_count),
        .z80_alive      ()
    );

    //------------------------------------------------------------------------
    // Dual-Port BRAM (8KB)
    // Port A: Z80 harness (load/read test code)
    // Port B: Z8001 CPU (fetch/execute)
    //------------------------------------------------------------------------

    // Z8001 write logic - edge-detected to avoid trailing garbage
    // After real DS rises, the CPU stops driving data but z8k_ds_n_sync
    // stays low for 2 more clocks (synchronizer delay). Level-based write
    // enables would let the BRAM capture whatever garbage is on the floating
    // bus during those trailing cycles. Using DS falling edge ensures a
    // single-pulse write when data is guaranteed valid.
    wire z8k_ram_write = ram_sel && ~z8k_rw_n_sync && z8k_ds_falling;
    wire z8k_we_hi = z8k_ram_write && (z8k_bw_n_sync || ~z8k_addr[0]);
    wire z8k_we_lo = z8k_ram_write && (z8k_bw_n_sync ||  z8k_addr[0]);

    wire [15:0] z80_rd_data;
    wire [15:0] z8k_rd_data;

    // Z80 accesses to 0x2000-0x3FFF target the bootstrap master store instead
    // of the active CPU RAM. The CPU's Port B never drives z80_addr[13], so the
    // master is physically unreachable by the CPU (see boot_master.v).
    wire master_sel = z80_addr[13];

    ram16_altera bram (
        // Port A - Z80 harness (active CPU RAM only; master accesses excluded)
        .clka    (sys_clk),
        .wea_hi  (z8k_mem_we & ~master_sel),
        .wea_lo  (z8k_mem_we & ~master_sel),
        .addra   (z80_addr[12:0]),
        .dina    (z8k_mem_wdata),
        .douta   (z80_rd_data),
        // Port B - Z8001 CPU
        .clkb    (sys_clk),
        .web_hi  (z8k_we_hi),
        .web_lo  (z8k_we_lo),
        .addrb   ({sn_latched[0], z8k_addr[11:0]}),
        .dinb    (z8k_wdata),
        .doutb   (z8k_rd_data)
    );

    // Bootstrap master store (Z80-only, read-only to the CPU)
    wire [15:0] master_rd_data;
    boot_master boot_master_inst (
        .clk   (sys_clk),
        .we    (z8k_mem_we & master_sel),
        .waddr (z80_addr[11:1]),
        .din   (z8k_mem_wdata),
        .dout  (master_rd_data)
    );

    // Read mux: select registered once to match the 1-cycle BRAM read latency.
    reg master_sel_q;
    always @(posedge sys_clk) master_sel_q <= master_sel;
    assign z8k_mem_rdata = master_sel_q ? master_rd_data : z80_rd_data;

    //------------------------------------------------------------------------
    // I/O Port Registers
    //------------------------------------------------------------------------
    wire z8k_io_wr = io_port_match && ~z8k_rw_n_sync && z8k_ds_falling;
    wire z8k_io_rd = io_port_match &&  z8k_rw_n_sync && ~z8k_ds_n_sync;

    z8k_io_ports io_ports (
        .clk           (sys_clk),
        .rst_n         (sys_rst_n),
        // Z8000 bus side
        .z8k_reg_sel   (z8k_io_reg_sel),
        .z8k_wdata     (z8k_wdata),
        .z8k_rdata     (z8k_io_rdata),
        .z8k_wr        (z8k_io_wr),
        .z8k_rd        (z8k_io_rd),
        // z8001_bus_external exposes 1=word/0=byte for BRAM write enables;
        // z8k_io_ports expects the CPU B/W_n polarity: 0=word/1=byte.
        .z8k_bw_n      (~z8k_bw_n_sync),
        .z8k_addr_lsb  (z8k_addr[0]),
        // Z80 side
        .z80_reg_sel   (z80_io_reg_sel),
        .z80_wbyte     (z80_io_wbyte),
        .z80_rdata     (z80_io_rdata),
        .z80_wr_lo     (z80_io_wr_lo),
        .z80_wr_hi     (z80_io_wr_hi),
        .z80_seq_reg_sel   (z80_io_seq_reg_sel),
        .z80_seq_slot_sel  (z80_io_seq_slot_sel),
        .z80_seq_wbyte     (z80_io_seq_wbyte),
        .z80_seq_wr_lo     (z80_io_seq_wr_lo),
        .z80_seq_wr_hi     (z80_io_seq_wr_hi),
        .z80_seq_clear     (z80_io_seq_clear)
    );

    // Z8001 data bus mux
    assign data_to_cpu = ram_sel     ? z8k_rd_data :
                         io_port_match ? z8k_io_rdata :
                                         16'hFFFF;

    //------------------------------------------------------------------------
    // I/O LED Latch
    // Any Z8001 I/O write captures wdata; LED driven from bit 0
    //------------------------------------------------------------------------
    reg [15:0] io_led_reg;
    wire io_write = io_sel && ~z8k_rw_n_sync && z8k_ds_falling;

    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n)
            io_led_reg <= 16'h0000;
        else if (io_write)
            io_led_reg <= z8k_wdata;
    end

    assign driveLED = io_led_reg[0];

endmodule
