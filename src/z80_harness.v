// Z80-based Test Harness Controller
// Uses TV80 Z80 core to manage the Z8000 test harness via UART
//
// Memory Map (Z80):
//   0x0000-0x1FFF: RAM (8KB)
//
// I/O Ports (directly addressed when iorq_n=0):
//   0x00: UART data (R: read byte, W: send byte)
//   0x01: UART status (R: bit0=tx_ready, bit1=rx_valid)
//   0x10: Z8000 mem addr low
//   0x11: Z8000 mem addr high
//   0x12: Z8000 mem data low (from BRAM)
//   0x13: Z8000 mem data high
//   0x14: Z8000 control (W: bit0=reset_n, bit1=mem_write)
//   0x15: Z8000 status (R: bit0=halt_n, bit1=bus_active, bit2=timeout)
//   0x16-0x19: Cycle count (R, 32-bit little-endian)
//   0x1A-0x1B: Fetch count (R, 16-bit little-endian)
//   0x1C-0x1F: Cycle limit (W, 32-bit little-endian)
//   0x20-0x21: Trace read addr (R/W, 10-bit)
//   0x22-0x26: Trace data (R, 36-bit: addr[15:0], data[15:0], flags[3:0])
//   0x27-0x28: Trace write count (R, 10-bit)
//   0x29: Z8000 ST (R, 4-bit status type from CPU)
//   0x2A-0x2D: Instr cycle count (R, 32-bit little-endian, address-gated)
//   0x30-0x47: I/O port registers (12 regs, 2 bytes each: even=low, odd=high)
//   0x48-0xA7: I/O scripted-read FIFO slots (12 regs x 4 words)
//   0xA8: Clear all I/O scripted-read FIFO slots/counts (W)

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
    input  [3:0]  z8k_st,          // Z8000 status type (directly from CPU)

    // Z8000 memory interface (directly addressed to shared BRAM)
    output reg        z8k_mem_we,
    output reg [14:0] z80_addr,
    output reg [15:0] z8k_mem_wdata,
    input      [15:0] z8k_mem_rdata,

    // Z8000 instrumentation
    input         z8k_bus_active,    // AS_n has gone low since reset
    input  [31:0] z8k_cycle_count,   // Clock cycles since reset release
    input  [15:0] z8k_fetch_count,   // Opcode fetches since reset release

    // Cycle-based timeout
    output reg [31:0] z8k_cycle_limit,  // Cycle limit for timeout (0 = no limit)
    input         z8k_cycle_timeout,    // HIGH when cycle_count >= cycle_limit

    // Trace buffer interface
    output reg [9:0]  trace_rd_addr,    // Read address (0-1023)
    input      [35:0] trace_rd_data,    // Read data (36 bits)
    input      [9:0]  trace_wr_count,   // Number of entries captured

    // I/O port registers interface
    output [3:0]      io_port_reg_sel,  // Register index (0-11)
    output [7:0]      io_port_wbyte,    // Write data byte
    input  [15:0]     io_port_rdata,    // Read data (full word)
    output reg        io_port_wr_lo,    // Write low byte strobe
    output reg        io_port_wr_hi,    // Write high byte strobe

    // I/O scripted-read FIFO interface
    output [3:0]      io_seq_reg_sel,
    output [1:0]      io_seq_slot_sel,
    output [7:0]      io_seq_wbyte,
    output reg        io_seq_wr_lo,
    output reg        io_seq_wr_hi,
    output reg        io_seq_clear,

    // Instruction cycle counter (address-gated)
    input  [31:0]     z8k_instr_cycle_count,

    // Alive indicator
    output            z80_alive          // Toggles while Z80 firmware polls UART
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

// I/O port register decode (ports 0x30-0x47)
wire io_port_sel = (cpu_addr[7:0] >= 8'h30) && (cpu_addr[7:0] <= 8'h47);
wire [4:0] io_port_off = cpu_addr[4:0] - 5'h10; // (addr-0x30): 0x30[4:0]=0x10
assign io_port_reg_sel = io_port_off[4:1];       // (addr-0x30)/2 = reg index
wire   io_port_byte_hi = io_port_off[0];         // odd addr = high byte
assign io_port_wbyte = cpu_dout;

// I/O scripted-read FIFO decode (ports 0x48-0xA7, 12 regs x 4 words)
wire io_seq_sel = (cpu_addr[7:0] >= 8'h48) && (cpu_addr[7:0] <= 8'hA7);
wire [6:0] io_seq_off = cpu_addr[7:0] - 8'h48;
wire [5:0] io_seq_word = io_seq_off[6:1];
assign io_seq_reg_sel = io_seq_word[5:2];
assign io_seq_slot_sel = io_seq_word[1:0];
wire io_seq_byte_hi = io_seq_off[0];
assign io_seq_wbyte = cpu_dout;
wire io_seq_clear_sel = (cpu_addr[7:0] == 8'hA8);

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
        // Trace buffer (0x20-0x28)
        8'h20: io_dout = trace_rd_addr[7:0];              // Trace read addr low
        8'h21: io_dout = {6'b0, trace_rd_addr[9:8]};      // Trace read addr high
        8'h22: io_dout = trace_rd_data[7:0];              // Trace data byte 0
        8'h23: io_dout = trace_rd_data[15:8];             // Trace data byte 1
        8'h24: io_dout = trace_rd_data[23:16];            // Trace data byte 2
        8'h25: io_dout = trace_rd_data[31:24];            // Trace data byte 3
        8'h26: io_dout = {4'b0, trace_rd_data[35:32]};    // Trace data byte 4 (4 bits)
        8'h27: io_dout = trace_wr_count[7:0];             // Trace write count low
        8'h28: io_dout = {6'b0, trace_wr_count[9:8]};     // Trace write count high
        8'h29: io_dout = {4'b0, z8k_st};                  // Z8000 ST (status type)
        8'h2A: io_dout = z8k_instr_cycle_count[7:0];      // Instr cycle count byte 0
        8'h2B: io_dout = z8k_instr_cycle_count[15:8];     // Instr cycle count byte 1
        8'h2C: io_dout = z8k_instr_cycle_count[23:16];    // Instr cycle count byte 2
        8'h2D: io_dout = z8k_instr_cycle_count[31:24];    // Instr cycle count byte 3
        default: begin
            if (io_port_sel)
                io_dout = io_port_byte_hi ? io_port_rdata[15:8] : io_port_rdata[7:0];
        end
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
        z80_addr <= 15'h0000;
        z8k_mem_wdata <= 16'h0000;
        z8k_cycle_limit <= 32'h00000000;
        trace_rd_addr <= 10'h000;
        io_port_wr_lo <= 1'b0;
        io_port_wr_hi <= 1'b0;
        io_seq_wr_lo <= 1'b0;
        io_seq_wr_hi <= 1'b0;
        io_seq_clear <= 1'b0;
    end else begin
        // Defaults
        uart_tx_valid <= 1'b0;
        uart_rx_ready <= 1'b0;
        z8k_mem_we <= 1'b0;
        io_port_wr_lo <= 1'b0;
        io_port_wr_hi <= 1'b0;
        io_seq_wr_lo <= 1'b0;
        io_seq_wr_hi <= 1'b0;
        io_seq_clear <= 1'b0;

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
                        z80_addr <= z8k_addr_reg;
                        z8k_mem_wdata <= z8k_data_reg;
                    end
                end
                8'h1C: z8k_cycle_limit[7:0] <= cpu_dout;    // Cycle limit byte 0
                8'h1D: z8k_cycle_limit[15:8] <= cpu_dout;   // Cycle limit byte 1
                8'h1E: z8k_cycle_limit[23:16] <= cpu_dout;  // Cycle limit byte 2
                8'h1F: z8k_cycle_limit[31:24] <= cpu_dout;  // Cycle limit byte 3
                // Trace buffer read address
                8'h20: trace_rd_addr[7:0] <= cpu_dout;      // Trace read addr low
                8'h21: trace_rd_addr[9:8] <= cpu_dout[1:0]; // Trace read addr high
                default: begin
                    if (io_seq_clear_sel) begin
                        io_seq_clear <= 1'b1;
                    end else if (io_seq_sel) begin
                        if (io_seq_byte_hi)
                            io_seq_wr_hi <= 1'b1;
                        else
                            io_seq_wr_lo <= 1'b1;
                    end else if (io_port_sel) begin
                        if (io_port_byte_hi)
                            io_port_wr_hi <= 1'b1;
                        else
                            io_port_wr_lo <= 1'b1;
                    end
                end
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
        z80_addr <= z8k_addr_reg;
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
// Z80 Alive Indicator
// Counts UART status polls (port 0x01 reads).
// Bit 19 toggles ~every 500K polls = visible blink.
// ==============================================
reg [19:0] alive_cnt;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        alive_cnt <= 20'd0;
    else if (io_rd && cpu_addr[7:0] == 8'h01)
        alive_cnt <= alive_cnt + 1'b1;
end

assign z80_alive = alive_cnt[19];

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
