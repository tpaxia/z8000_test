// Z80-based Test Harness Controller
// Uses TV80 Z80 core to manage the Z8000 test harness via UART
//
// Memory Map (Z80):
//   0x0000-0x1FFF: RAM (8KB)
//
// I/O Ports (active accent accent when iorq_n=0, directly accent addressed):
//   0x00: UART data (R: read byte, W: send byte)
//   0x01: UART status (R: bit0=tx_ready, bit1=rx_valid)
//   0x10: Z8000 mem addr low
//   0x11: Z8000 mem addr high
//   0x12: Z8000 mem data low (directly addressed to BRAM)
//   0x13: Z8000 mem data high
//   0x14: Z8000 control (W: bit0=reset_n)
//   0x15: Z8000 status (R: bit0=halt_n)

`timescale 1ns / 1ps

module z80_harness (
    input         clk,
    input         rst_n,

    // UART
    input  [7:0]  uart_rx_data,
    input         uart_rx_valid,
    output reg    uart_rx_ready,
    output reg [7:0] uart_tx_data,
    output reg    uart_tx_valid,
    input         uart_tx_ready,

    // Z8000 control
    output reg    z8k_rst_n,
    input         z8k_halt_n,

    // Z8000 memory interface (directly addressed to shared BRAM)
    output reg        z8k_mem_we,
    output reg [14:0] z8k_mem_addr,
    output reg [15:0] z8k_mem_wdata,
    input      [15:0] z8k_mem_rdata,

    // Z8000 instrumentation
    input         z8k_bus_active,    // AS_n has gone low since reset
    input  [31:0] z8k_cycle_count,   // Clock cycles since reset release
    input  [15:0] z8k_fetch_count,   // Opcode fetches since reset release

    // Cycle-based timeout
    output reg [31:0] z8k_cycle_limit,  // Cycle limit for timeout (0 = no limit)
    input         z8k_cycle_timeout     // HIGH when cycle_count >= cycle_limit
);

// ==============================================
// TV80 CPU
// ==============================================
wire        cpu_m1_n, cpu_mreq_n, cpu_iorq_n, cpu_rd_n, cpu_wr_n;
wire        cpu_rfsh_n, cpu_halt_n, cpu_busak_n;
wire [15:0] cpu_addr;
wire [7:0]  cpu_dout;
reg  [7:0]  cpu_din;

tv80s #(
    .Mode(0),       // Z80 mode
    .T2Write(1),
    .IOWait(1)
) cpu (
    .clk      (clk),
    .reset_n  (rst_n),
    .wait_n   (1'b1),
    .int_n    (1'b1),
    .nmi_n    (1'b1),
    .busrq_n  (1'b1),
    .m1_n     (cpu_m1_n),
    .mreq_n   (cpu_mreq_n),
    .iorq_n   (cpu_iorq_n),
    .rd_n     (cpu_rd_n),
    .wr_n     (cpu_wr_n),
    .rfsh_n   (cpu_rfsh_n),
    .halt_n   (cpu_halt_n),
    .busak_n  (cpu_busak_n),
    .A        (cpu_addr),
    .di       (cpu_din),
    .dout     (cpu_dout)
);

// ==============================================
// Z80 RAM (8KB)
// ==============================================
reg [7:0] ram [0:8191];
reg [7:0] ram_dout;

wire ram_cs = ~cpu_mreq_n && (cpu_addr[15:13] == 3'b000); // 0x0000-0x1FFF
wire ram_we = ram_cs && ~cpu_wr_n;
wire ram_rd = ram_cs && ~cpu_rd_n;

always @(posedge clk) begin
    if (ram_we)
        ram[cpu_addr[12:0]] <= cpu_dout;
    ram_dout <= ram[cpu_addr[12:0]];
end

// ==============================================
// I/O Decoding
// ==============================================
wire io_cs = ~cpu_iorq_n && cpu_m1_n; // M1 high = not interrupt ack
wire io_rd = io_cs && ~cpu_rd_n;
wire io_wr = io_cs && ~cpu_wr_n;

// I/O registers
reg [7:0] io_dout;
reg [14:0] z8k_addr_reg;
reg [15:0] z8k_data_reg;
reg        mem_read_pending;
reg [1:0]  mem_read_wait;

// UART RX consumed flag
reg uart_rx_consumed;

// I/O Read
always @(*) begin
    io_dout = 8'hFF;
    case (cpu_addr[7:0])
        8'h00: io_dout = uart_rx_data;                    // UART data
        8'h01: io_dout = {6'b0, uart_rx_valid, uart_tx_ready}; // UART status
        8'h10: io_dout = z8k_addr_reg[7:0];               // Addr low
        8'h11: io_dout = {1'b0, z8k_addr_reg[14:8]};      // Addr high
        8'h12: io_dout = z8k_mem_rdata[7:0];              // Data low (from BRAM)
        8'h13: io_dout = z8k_mem_rdata[15:8];             // Data high
        8'h14: io_dout = {7'b0, z8k_rst_n};               // Z8000 control (read rst_n)
        8'h15: io_dout = {5'b0, z8k_cycle_timeout, z8k_bus_active, z8k_halt_n}; // Z8000 status
        8'h16: io_dout = z8k_cycle_count[7:0];            // Cycle count byte 0
        8'h17: io_dout = z8k_cycle_count[15:8];           // Cycle count byte 1
        8'h18: io_dout = z8k_cycle_count[23:16];          // Cycle count byte 2
        8'h19: io_dout = z8k_cycle_count[31:24];          // Cycle count byte 3
        8'h1A: io_dout = z8k_fetch_count[7:0];            // Fetch count byte 0
        8'h1B: io_dout = z8k_fetch_count[15:8];           // Fetch count byte 1
    endcase
end

// I/O Write and Control
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        uart_tx_data <= 8'h00;
        uart_tx_valid <= 1'b0;
        uart_rx_ready <= 1'b0;
        uart_rx_consumed <= 1'b0;
        z8k_rst_n <= 1'b0;
        z8k_addr_reg <= 15'h0000;
        z8k_data_reg <= 16'h0000;
        z8k_mem_we <= 1'b0;
        z8k_mem_addr <= 15'h0000;
        z8k_mem_wdata <= 16'h0000;
        z8k_cycle_limit <= 32'h00000000;
    end else begin
        // Defaults
        uart_tx_valid <= 1'b0;
        uart_rx_ready <= 1'b0;
        z8k_mem_we <= 1'b0;

        // Clear consumed flag when rx_valid goes low
        if (!uart_rx_valid)
            uart_rx_consumed <= 1'b0;

        if (io_wr) begin
            case (cpu_addr[7:0])
                8'h00: begin // UART TX
                    uart_tx_data <= cpu_dout;
                    uart_tx_valid <= 1'b1;
                end
                8'h10: z8k_addr_reg[7:0] <= cpu_dout;
                8'h11: z8k_addr_reg[14:8] <= cpu_dout[6:0];
                8'h12: z8k_data_reg[7:0] <= cpu_dout;
                8'h13: z8k_data_reg[15:8] <= cpu_dout;
                8'h14: begin // Control
                    z8k_rst_n <= cpu_dout[0];
                    if (cpu_dout[1]) begin // Write to Z8000 mem
                        z8k_mem_we <= 1'b1;
                        z8k_mem_addr <= z8k_addr_reg;
                        z8k_mem_wdata <= z8k_data_reg;
                    end
                end
                8'h1C: z8k_cycle_limit[7:0] <= cpu_dout;    // Cycle limit byte 0
                8'h1D: z8k_cycle_limit[15:8] <= cpu_dout;   // Cycle limit byte 1
                8'h1E: z8k_cycle_limit[23:16] <= cpu_dout;  // Cycle limit byte 2
                8'h1F: z8k_cycle_limit[31:24] <= cpu_dout;  // Cycle limit byte 3
            endcase
        end

        if (io_rd) begin
            case (cpu_addr[7:0])
                8'h00: begin // UART RX - acknowledge byte
                    if (uart_rx_valid && !uart_rx_consumed) begin
                        uart_rx_ready <= 1'b1;
                        uart_rx_consumed <= 1'b1;
                    end
                end
            endcase
        end

        // Keep Z8000 memory address updated for reads
        z8k_mem_addr <= z8k_addr_reg;
    end
end

// ==============================================
// CPU Data Input Mux
// ==============================================
always @(*) begin
    if (ram_rd)
        cpu_din = ram_dout;
    else if (io_rd)
        cpu_din = io_dout;
    else
        cpu_din = 8'hFF;
end

// ==============================================
// RAM Initialization
// ==============================================
// Z80 Firmware: 770 bytes
// Commands: ST, RS, EX, WRnxxxx, RRn, WMaaaaxxxx, RMaaaa, DA, MT
// Generated from z80_fw.asm - run 'make firmware' to rebuild
initial begin
    $readmemh("z80_fw.hex", ram);
end

endmodule
