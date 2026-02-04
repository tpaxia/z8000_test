// Z8000 Instruction Test Harness Top Module
// Provides serial control interface for testing Z8000 instructions
//
// Target: Tang Nano 20K (GW2AR-18C)
// Clock: 27MHz system clock, ~4MHz CPU clock
// UART: 115200 baud, 8N1
//
// Memory Map:
//   0x0000-0x0005: Reset vectors (Reserved, FCW, PC)
//   0x0010-0x002F: Register setup block (R0-R15 initial values)
//   0x0030-0x0031: Initial FCW value (not used - bootstrap doesn't load FCW)
//   0x0040-0x007F: Bootstrap code (loads registers, jumps to test)
//   0x0080-0x009F: Register dump area (R0-R15 after test)
//   0x00A0-0x00A1: Final FCW value
//   0x00C0-0x010F: Dump routine (stores registers, HALTs)
//   0x0200-0x7FFF: Test code and data area
//
// Usage:
//   1. Write register initial values: WR 0 1234 (R0=0x1234)
//   2. Write test code: WM 0200 xxxx (instruction at 0x0200)
//   3. Write jump to dump: WM 0204 5E08, WM 0206 00C0
//   4. Execute: EX
//   5. Read results: RR 0 (read R0 result)

`timescale 1ns / 1ps

module test_harness_top (
    input         clk,       // 27MHz system clock
    input         rst,       // Active high reset
    input         uart_rx,   // UART receive pin
    output        uart_tx,   // UART transmit pin
    output        led,       // Heartbeat LED (flashing)
    output        led2,      // CPU in reset indicator
    output        led3,      // CPU running indicator
    output        led4       // CPU halted indicator
);

parameter CLK_FRE   = 27;
parameter UART_BAUD = 115200;

localparam ADDR_REG_SETUP  = 16'h0010;
localparam ADDR_FCW_SETUP  = 16'h0030;
localparam ADDR_BOOTSTRAP  = 16'h0040;
// Bootstrap has 16 LD + 1 JP = 34 words (68 bytes), ends at 0x0083
localparam ADDR_REG_DUMP   = 16'h0090;  // Moved to avoid overlap with bootstrap
localparam ADDR_FCW_DUMP   = 16'h00B0;
localparam ADDR_DUMP_ROUT  = 16'h00C0;
localparam ADDR_TEST_CODE  = 16'h0200;

wire rst_n = ~rst;

// ===========================================
// CPU Clock Generation - ~4MHz from 27MHz
// ===========================================
reg [2:0] clk_div;
reg       cpu_clk;
reg       toggle_sel;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        clk_div <= 3'd0;
        cpu_clk <= 1'b0;
        toggle_sel <= 1'b0;
    end else begin
        if ((toggle_sel && clk_div == 3'd3) || (!toggle_sel && clk_div == 3'd2)) begin
            clk_div <= 3'd0;
            cpu_clk <= ~cpu_clk;
            toggle_sel <= ~toggle_sel;
        end else begin
            clk_div <= clk_div + 1'b1;
        end
    end
end

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
// Z8000 CPU
// ===========================================
wire        cpu_as_n, cpu_ds_n, cpu_rw_n, cpu_mreq_n, cpu_bw_n;
wire [3:0]  cpu_st;
wire        cpu_busack_n, cpu_ns, cpu_halt_n;
wire        cpu_rst_n, cpu_busreq_n;

// LED indicators:
// led  = Heartbeat (flashing)
// led2 = CPU in reset (active when cpu_rst_n = 0)
// led3 = CPU running (active when out of reset and not halted)
// led4 = CPU halted (active when halt_n = 0)
assign led2 = ~cpu_rst_n;                      // On when CPU in reset
assign led3 = cpu_rst_n && cpu_halt_n;         // On when running
assign led4 = ~cpu_halt_n;                     // On when halted

wire [15:0] ad_bus;
reg  [15:0] data_to_cpu;

assign ad_bus = (cpu_rw_n && ~cpu_ds_n) ? data_to_cpu : 16'bz;

wire cpu_wait_n;  // Memory wait signal

z8000_cpu cpu (
    .clk        (cpu_clk),
    .rst_n      (cpu_rst_n),
    .ad         (ad_bus),
    .as_n       (cpu_as_n),
    .ds_n       (cpu_ds_n),
    .rw_n       (cpu_rw_n),
    .mreq_n     (cpu_mreq_n),
    .b_w_n      (cpu_bw_n),
    .st         (cpu_st),
    .wait_n     (cpu_wait_n),
    .busreq_n   (cpu_busreq_n),
    .busack_n   (cpu_busack_n),
    .nmi_n      (1'b1),
    .vi_n       (1'b1),
    .nvi_n      (1'b1),
    .n_s        (cpu_ns),
    .halt_n     (cpu_halt_n)
);

// ===========================================
// Address and Status Latch
// ===========================================
reg [15:0] latched_addr;
reg [3:0]  latched_st;

// Latch address on falling edge of AS_n (matches Z8000 bus timing)
always @(negedge cpu_as_n or negedge rst_n) begin
    if (!rst_n) begin
        latched_addr <= 16'h0000;
        latched_st <= 4'b0000;
    end else begin
        latched_addr <= ad_bus;
        latched_st <= cpu_st;
    end
end

// ===========================================
// I/O Ports
// ===========================================
// Port 0x00-0x01: Data register (word)
// Port 0x02-0x03: Control register (word)
// Port 0x10: Read returns 0xAA
// Port 0x11: Read returns 0x55
// Port 0x20-0x21: Special I/O data register (word)
reg [15:0] io_data_reg;
reg [15:0] io_ctrl_reg;
reg [15:0] sio_data_reg;

// I/O cycle detection - use cpu_st directly like z8000_micro testbench
wire is_io_cycle = (cpu_st == 4'b0010) || (cpu_st == 4'b0011);
wire is_sio_cycle = (cpu_st == 4'b0011);

// I/O read data
reg [15:0] io_rdata;
always @(*) begin
    case (latched_addr)
        16'h0000: io_rdata = io_data_reg;
        16'h0001: io_rdata = {8'h00, io_data_reg[7:0]};
        16'h0002: io_rdata = io_ctrl_reg;
        16'h0003: io_rdata = {8'h00, io_ctrl_reg[7:0]};
        16'h0010: io_rdata = 16'hAA00;  // Byte 0xAA in high lane (even addr)
        16'h0011: io_rdata = 16'h0055;  // Byte 0x55 in low lane (odd addr)
        16'h0020: io_rdata = sio_data_reg;
        16'h0021: io_rdata = {8'h00, sio_data_reg[7:0]};
        default:  io_rdata = 16'hDEAD;  // Unknown port
    endcase
end

// I/O write handling
wire io_write = is_io_cycle && ~cpu_rw_n && ~cpu_ds_n;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        io_data_reg <= 16'h1234;
        io_ctrl_reg <= 16'h0000;
        sio_data_reg <= 16'h5678;
    end else if (io_write) begin
        if (is_sio_cycle) begin
            // Special I/O write
            case (latched_addr)
                16'h0020: sio_data_reg <= ad_bus;
                16'h0021: sio_data_reg[7:0] <= ad_bus[7:0];
            endcase
        end else begin
            // Standard I/O write
            case (latched_addr)
                16'h0000: io_data_reg <= ad_bus;
                16'h0001: io_data_reg[7:0] <= ad_bus[7:0];
                16'h0002: io_ctrl_reg <= ad_bus;
                16'h0003: io_ctrl_reg[7:0] <= ad_bus[7:0];
            endcase
        end
    end
end

// ===========================================
// Memory - 16KB RAM (8K x 16-bit) using Block RAM
// Split into two byte-wide RAMs for byte write support
// Uses wait states for CPU reads (BRAM has 1-cycle latency)
// ===========================================
wire        harness_mem_we;
wire [14:0] harness_mem_addr;
wire [15:0] harness_mem_wdata;
wire        harness_mem_byte;

// Harness has memory access when CPU is in reset or has released bus
wire harness_active = ~cpu_rst_n || ~cpu_busack_n;

// Memory address selection: harness has priority when active
wire [12:0] mem_addr = harness_active ? harness_mem_addr[13:1] : latched_addr[13:1];

// CPU write signals
wire cpu_mem_write = ~cpu_mreq_n && ~cpu_rw_n && ~cpu_ds_n && !harness_active;
wire cpu_we_hi = cpu_mem_write && (cpu_bw_n || ~latched_addr[0]);
wire cpu_we_lo = cpu_mem_write && (cpu_bw_n || latched_addr[0]);

// Harness write signals
wire harness_we_hi = harness_mem_we && (!harness_mem_byte || !harness_mem_addr[0]);
wire harness_we_lo = harness_mem_we && (!harness_mem_byte || harness_mem_addr[0]);

// Combined write enables
wire we_hi = harness_we_hi || cpu_we_hi;
wire we_lo = harness_we_lo || cpu_we_lo;

// Write data selection
wire [7:0] wdata_hi = harness_mem_we ? harness_mem_wdata[7:0] : ad_bus[15:8];
wire [7:0] wdata_lo = harness_mem_we ? harness_mem_wdata[7:0] : ad_bus[7:0];
wire [7:0] harness_wdata_hi_word = harness_mem_wdata[15:8];
wire [7:0] wdata_hi_final = (harness_mem_we && !harness_mem_byte) ? harness_wdata_hi_word : wdata_hi;
wire [15:0] wdata_word = {wdata_hi_final, wdata_lo};
wire [1:0]  wr_be = {we_hi, we_lo};
wire        wr_en = we_hi || we_lo;

wire [15:0] mem_rdata;

`ifdef SIMULATION
// Behavioral model for simulation
reg [7:0] mem_hi [0:8191];
reg [7:0] mem_lo [0:8191];
reg [7:0] rdata_hi, rdata_lo;

always @(posedge clk) begin
    if (we_hi)
        mem_hi[mem_addr] <= wdata_hi_final;
    rdata_hi <= mem_hi[mem_addr];
end

always @(posedge clk) begin
    if (we_lo)
        mem_lo[mem_addr] <= wdata_lo;
    rdata_lo <= mem_lo[mem_addr];
end

assign mem_rdata = {rdata_hi, rdata_lo};

`else
// Gowin BRAM primitive for synthesis
gowin_dpb bram (
    .clk     (clk),
    .wr_en   (wr_en),
    .wr_addr (mem_addr),
    .wr_data (wdata_word),
    .wr_be   (wr_be),
    .rd_addr (mem_addr),
    .rd_data (mem_rdata)
);
`endif

wire [15:0] harness_mem_rdata = mem_rdata;

// ===========================================
// Wait State Generator for CPU Memory Reads
// BRAM has 1-cycle read latency, so we insert wait states
// Runs at system clock but synchronized to CPU signals
// ===========================================
reg mem_wait_n;
reg [2:0] wait_cnt;
reg mem_read_pending;

// Detect start of CPU memory read (falling edge of DS during read)
reg ds_n_prev;
always @(posedge clk) ds_n_prev <= cpu_ds_n;
wire cpu_read_start = ~cpu_mreq_n && cpu_rw_n && ~cpu_ds_n && ds_n_prev && !harness_active;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        mem_wait_n <= 1'b1;
        wait_cnt <= 3'd0;
        mem_read_pending <= 1'b0;
    end else begin
        if (cpu_read_start) begin
            // Start of CPU read - assert wait and start counter
            mem_wait_n <= 1'b0;
            wait_cnt <= 3'd7;  // Wait cycles for BRAM latency (system clocks)
            mem_read_pending <= 1'b1;
        end else if (mem_read_pending) begin
            if (wait_cnt > 0) begin
                wait_cnt <= wait_cnt - 1;
            end else begin
                // Done waiting - release wait
                mem_wait_n <= 1'b1;
                mem_read_pending <= 1'b0;
            end
        end else if (cpu_ds_n) begin
            // Reset when bus cycle ends
            mem_wait_n <= 1'b1;
        end
    end
end

// Connect wait signal to CPU (I/O doesn't need wait states)
assign cpu_wait_n = is_io_cycle ? 1'b1 : mem_wait_n;

always @(*) begin
    if (is_io_cycle)
        data_to_cpu = io_rdata;
    else if (~cpu_mreq_n && latched_addr[15] == 1'b0)
        data_to_cpu = mem_rdata;
    else
        data_to_cpu = 16'hFFFF;
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
// Controller
// ===========================================
test_harness_ctrl #(
    .ADDR_REG_SETUP(ADDR_REG_SETUP),
    .ADDR_FCW_SETUP(ADDR_FCW_SETUP),
    .ADDR_TEST_ADDR(16'h0032),
    .ADDR_REG_DUMP(ADDR_REG_DUMP),
    .ADDR_FCW_DUMP(ADDR_FCW_DUMP)
) ctrl (
    .clk(clk), .rst_n(rst_n),
    .uart_rx_data(uart_rx_data), .uart_rx_valid(uart_rx_valid),
    .uart_rx_ready(uart_rx_ready),
    .uart_tx_data(uart_tx_data), .uart_tx_valid(uart_tx_valid),
    .uart_tx_ready(uart_tx_ready),
    .cpu_rst_n(cpu_rst_n), .cpu_halt_n(cpu_halt_n),
    .cpu_busreq_n(cpu_busreq_n), .cpu_busack_n(cpu_busack_n),
    .mem_we(harness_mem_we), .mem_addr(harness_mem_addr),
    .mem_wdata(harness_mem_wdata), .mem_rdata(harness_mem_rdata),
    .mem_byte(harness_mem_byte)
);

// ===========================================
// ROM Initialization (for simulation)
// ===========================================
`ifdef SIMULATION
initial begin
    // Reset vectors
    mem_hi[0] = 8'h00; mem_lo[0] = 8'h00;  // 0x0000: Reserved
    mem_hi[1] = 8'h40; mem_lo[1] = 8'h00;  // 0x0002: FCW = System mode
    mem_hi[2] = 8'h00; mem_lo[2] = 8'h40;  // 0x0004: PC = bootstrap

    // Register setup defaults (0x0010-0x002F = words 8-23) - all zeros by default

    // FCW setup (word 24 = 0x0030)
    mem_hi[24] = 8'h40; mem_lo[24] = 8'h00;

    // Bootstrap at 0x0040 (word 32)
    // Load R0-R15 from setup area using LD Rd, @addr (opcode 0x610d)
    mem_hi[32] = 8'h61; mem_lo[32] = 8'h00;  mem_hi[33] = 8'h00; mem_lo[33] = 8'h10;  // LD R0, @0x0010
    mem_hi[34] = 8'h61; mem_lo[34] = 8'h01;  mem_hi[35] = 8'h00; mem_lo[35] = 8'h12;  // LD R1, @0x0012
    mem_hi[36] = 8'h61; mem_lo[36] = 8'h02;  mem_hi[37] = 8'h00; mem_lo[37] = 8'h14;  // LD R2, @0x0014
    mem_hi[38] = 8'h61; mem_lo[38] = 8'h03;  mem_hi[39] = 8'h00; mem_lo[39] = 8'h16;  // LD R3, @0x0016
    mem_hi[40] = 8'h61; mem_lo[40] = 8'h04;  mem_hi[41] = 8'h00; mem_lo[41] = 8'h18;  // LD R4, @0x0018
    mem_hi[42] = 8'h61; mem_lo[42] = 8'h05;  mem_hi[43] = 8'h00; mem_lo[43] = 8'h1A;  // LD R5, @0x001A
    mem_hi[44] = 8'h61; mem_lo[44] = 8'h06;  mem_hi[45] = 8'h00; mem_lo[45] = 8'h1C;  // LD R6, @0x001C
    mem_hi[46] = 8'h61; mem_lo[46] = 8'h07;  mem_hi[47] = 8'h00; mem_lo[47] = 8'h1E;  // LD R7, @0x001E
    mem_hi[48] = 8'h61; mem_lo[48] = 8'h08;  mem_hi[49] = 8'h00; mem_lo[49] = 8'h20;  // LD R8, @0x0020
    mem_hi[50] = 8'h61; mem_lo[50] = 8'h09;  mem_hi[51] = 8'h00; mem_lo[51] = 8'h22;  // LD R9, @0x0022
    mem_hi[52] = 8'h61; mem_lo[52] = 8'h0A;  mem_hi[53] = 8'h00; mem_lo[53] = 8'h24;  // LD R10, @0x0024
    mem_hi[54] = 8'h61; mem_lo[54] = 8'h0B;  mem_hi[55] = 8'h00; mem_lo[55] = 8'h26;  // LD R11, @0x0026
    mem_hi[56] = 8'h61; mem_lo[56] = 8'h0C;  mem_hi[57] = 8'h00; mem_lo[57] = 8'h28;  // LD R12, @0x0028
    mem_hi[58] = 8'h61; mem_lo[58] = 8'h0D;  mem_hi[59] = 8'h00; mem_lo[59] = 8'h2A;  // LD R13, @0x002A
    mem_hi[60] = 8'h61; mem_lo[60] = 8'h0E;  mem_hi[61] = 8'h00; mem_lo[61] = 8'h2C;  // LD R14, @0x002C
    mem_hi[62] = 8'h61; mem_lo[62] = 8'h0F;  mem_hi[63] = 8'h00; mem_lo[63] = 8'h2E;  // LD R15, @0x002E
    mem_hi[64] = 8'h5E; mem_lo[64] = 8'h08;  mem_hi[65] = 8'h02; mem_lo[65] = 8'h00;  // JP 0x0200 (test code)

    // Dump routine at 0x00C0 (word 96)
    // Store R0-R15 to dump area at 0x0090 using ST @addr, Rs (opcode 0x6F0s)
    mem_hi[96]  = 8'h6F; mem_lo[96]  = 8'h00;  mem_hi[97]  = 8'h00; mem_lo[97]  = 8'h90;  // ST @0x0090, R0
    mem_hi[98]  = 8'h6F; mem_lo[98]  = 8'h01;  mem_hi[99]  = 8'h00; mem_lo[99]  = 8'h92;  // ST @0x0092, R1
    mem_hi[100] = 8'h6F; mem_lo[100] = 8'h02;  mem_hi[101] = 8'h00; mem_lo[101] = 8'h94;  // ST @0x0094, R2
    mem_hi[102] = 8'h6F; mem_lo[102] = 8'h03;  mem_hi[103] = 8'h00; mem_lo[103] = 8'h96;  // ST @0x0096, R3
    mem_hi[104] = 8'h6F; mem_lo[104] = 8'h04;  mem_hi[105] = 8'h00; mem_lo[105] = 8'h98;  // ST @0x0098, R4
    mem_hi[106] = 8'h6F; mem_lo[106] = 8'h05;  mem_hi[107] = 8'h00; mem_lo[107] = 8'h9A;  // ST @0x009A, R5
    mem_hi[108] = 8'h6F; mem_lo[108] = 8'h06;  mem_hi[109] = 8'h00; mem_lo[109] = 8'h9C;  // ST @0x009C, R6
    mem_hi[110] = 8'h6F; mem_lo[110] = 8'h07;  mem_hi[111] = 8'h00; mem_lo[111] = 8'h9E;  // ST @0x009E, R7
    mem_hi[112] = 8'h6F; mem_lo[112] = 8'h08;  mem_hi[113] = 8'h00; mem_lo[113] = 8'hA0;  // ST @0x00A0, R8
    mem_hi[114] = 8'h6F; mem_lo[114] = 8'h09;  mem_hi[115] = 8'h00; mem_lo[115] = 8'hA2;  // ST @0x00A2, R9
    mem_hi[116] = 8'h6F; mem_lo[116] = 8'h0A;  mem_hi[117] = 8'h00; mem_lo[117] = 8'hA4;  // ST @0x00A4, R10
    mem_hi[118] = 8'h6F; mem_lo[118] = 8'h0B;  mem_hi[119] = 8'h00; mem_lo[119] = 8'hA6;  // ST @0x00A6, R11
    mem_hi[120] = 8'h6F; mem_lo[120] = 8'h0C;  mem_hi[121] = 8'h00; mem_lo[121] = 8'hA8;  // ST @0x00A8, R12
    mem_hi[122] = 8'h6F; mem_lo[122] = 8'h0D;  mem_hi[123] = 8'h00; mem_lo[123] = 8'hAA;  // ST @0x00AA, R13
    mem_hi[124] = 8'h6F; mem_lo[124] = 8'h0E;  mem_hi[125] = 8'h00; mem_lo[125] = 8'hAC;  // ST @0x00AC, R14
    mem_hi[126] = 8'h6F; mem_lo[126] = 8'h0F;  mem_hi[127] = 8'h00; mem_lo[127] = 8'hAE;  // ST @0x00AE, R15
    // Write "done" flag: LD R0, #0xDEAD; ST @0x00B0, R0; then HALT
    mem_hi[128] = 8'h21; mem_lo[128] = 8'h00;  mem_hi[129] = 8'hDE; mem_lo[129] = 8'hAD;  // LD R0, #0xDEAD
    mem_hi[130] = 8'h6F; mem_lo[130] = 8'h00;  mem_hi[131] = 8'h00; mem_lo[131] = 8'hB0;  // ST @0x00B0, R0
    mem_hi[132] = 8'h7A; mem_lo[132] = 8'h00;  // HALT

    // Default test code at 0x0200 (word 256)
    // Just jump to dump routine
    mem_hi[256] = 8'h5E; mem_lo[256] = 8'h08;  mem_hi[257] = 8'h00; mem_lo[257] = 8'hC0;  // JP 0x00C0
end
`endif

endmodule
