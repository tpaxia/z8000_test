// Z8000 I/O Port Registers
// 12 x 16-bit registers, dual-access (Z8000 bus + Z80 harness)
//
// Z8000 side: active during test execution
//   Address decode by top module; this module receives pre-decoded reg_sel
//   Standard I/O (ST=0010): regs 0-5, Special I/O (ST=0100): regs 6-11
//   Word write: full 16-bit. Byte write: use bw_n and addr[0] for byte lane
//
// Z80 side: active when z8k_rst_n=0 (managed by top module)
//   Byte read/write via Z80 I/O ports 0x30-0x47
//   reg_index = (port_addr - 0x30) / 2, byte select = (port_addr - 0x30) & 1

`timescale 1ns / 1ps

module z8k_io_ports (
    input         clk,
    input         rst_n,
    // Z8000 bus side (directly driven by top module decode)
    input  [3:0]  z8k_reg_sel,    // Decoded register index 0-11
    input  [15:0] z8k_wdata,
    output [15:0] z8k_rdata,
    input         z8k_wr,         // Write strobe (active one clock)
    input         z8k_rd,         // Read active while Z8000 DS is asserted
    input         z8k_bw_n,       // 0=word, 1=byte
    input         z8k_addr_lsb,   // addr[0] for byte select: 0=high byte, 1=low byte

    // Z80 side
    input  [3:0]  z80_reg_sel,    // Register index 0-11
    input  [7:0]  z80_wbyte,
    output [15:0] z80_rdata,      // Full word, harness picks byte
    input         z80_wr_lo,      // Write low byte strobe
    input         z80_wr_hi,      // Write high byte strobe

    // Z80 scripted-read FIFO side: 4 words per I/O register.
    input  [3:0]  z80_seq_reg_sel,
    input  [1:0]  z80_seq_slot_sel,
    input  [7:0]  z80_seq_wbyte,
    input         z80_seq_wr_lo,
    input         z80_seq_wr_hi,
    input         z80_seq_clear
);

    reg [15:0] regs [0:11];
    reg [15:0] seq_regs [0:47];
    reg [2:0]  seq_count [0:11];
    reg [2:0]  seq_pos [0:11];
    reg        z8k_rd_prev;
    reg [3:0]  z8k_rd_reg_sel;

    wire       seq_active = (seq_count[z8k_reg_sel] != 3'd0);
    wire [2:0] seq_pos_raw = seq_pos[z8k_reg_sel];
    wire [2:0] seq_count_raw = seq_count[z8k_reg_sel];
    wire [1:0] seq_slot =
        (seq_pos_raw >= seq_count_raw) ? (seq_count_raw[1:0] - 2'd1) : seq_pos_raw[1:0];
    wire [5:0] z8k_seq_index = {z8k_reg_sel, 2'b00} + {4'd0, seq_slot};
    wire [5:0] z80_seq_index = {z80_seq_reg_sel, z80_seq_slot_sel};
    wire [15:0] z8k_read_value = seq_active ? seq_regs[z8k_seq_index] : regs[z8k_reg_sel];

    integer i;

    // Z8000 read (combinational)
    assign z8k_rdata = z8k_read_value;

    // Z80 read (combinational)
    assign z80_rdata = regs[z80_reg_sel];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 12; i = i + 1) begin
                regs[i] <= 16'h0000;
                seq_count[i] <= 3'd0;
                seq_pos[i] <= 3'd0;
            end
            for (i = 0; i < 48; i = i + 1)
                seq_regs[i] <= 16'h0000;
            z8k_rd_prev <= 1'b0;
            z8k_rd_reg_sel <= 4'd0;
        end else begin
            z8k_rd_prev <= z8k_rd;
            if (z8k_rd)
                z8k_rd_reg_sel <= z8k_reg_sel;

            if (z80_seq_clear) begin
                for (i = 0; i < 12; i = i + 1) begin
                    seq_count[i] <= 3'd0;
                    seq_pos[i] <= 3'd0;
                end
            end

            // Z8000 writes (during test execution, z8k_rst_n=1)
            if (z8k_wr) begin
                if (~z8k_bw_n) begin
                    // Word write
                    regs[z8k_reg_sel] <= z8k_wdata;
                end else begin
                    // Byte write
                    if (z8k_addr_lsb)
                        regs[z8k_reg_sel][7:0] <= z8k_wdata[7:0];   // Low byte
                    else
                        regs[z8k_reg_sel][15:8] <= z8k_wdata[15:8]; // High byte
                end
            end

            // Z80 writes (during setup/readback, z8k_rst_n=0)
            if (z80_wr_lo)
                regs[z80_reg_sel][7:0] <= z80_wbyte;
            if (z80_wr_hi)
                regs[z80_reg_sel][15:8] <= z80_wbyte;

            // Z80 scripted read FIFO writes. Writing any slot arms the sequence
            // through that slot and rewinds the read pointer.
            if (z80_seq_wr_lo) begin
                seq_regs[z80_seq_index][7:0] <= z80_seq_wbyte;
                if (seq_count[z80_seq_reg_sel] < ({1'b0, z80_seq_slot_sel} + 3'd1))
                    seq_count[z80_seq_reg_sel] <= {1'b0, z80_seq_slot_sel} + 3'd1;
                seq_pos[z80_seq_reg_sel] <= 3'd0;
            end
            if (z80_seq_wr_hi) begin
                seq_regs[z80_seq_index][15:8] <= z80_seq_wbyte;
                if (seq_count[z80_seq_reg_sel] < ({1'b0, z80_seq_slot_sel} + 3'd1))
                    seq_count[z80_seq_reg_sel] <= {1'b0, z80_seq_slot_sel} + 3'd1;
                seq_pos[z80_seq_reg_sel] <= 3'd0;
            end

            // Advance scripted reads once, after the Z8000 read cycle completes.
            if (z8k_rd_prev && !z8k_rd && (seq_count[z8k_rd_reg_sel] != 3'd0) &&
                seq_pos[z8k_rd_reg_sel] < seq_count[z8k_rd_reg_sel]) begin
                seq_pos[z8k_rd_reg_sel] <= seq_pos[z8k_rd_reg_sel] + 3'd1;
            end
        end
    end

endmodule
