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
    input         z8k_bw_n,       // 0=word, 1=byte
    input         z8k_addr_lsb,   // addr[0] for byte select: 0=high byte, 1=low byte

    // Z80 side
    input  [3:0]  z80_reg_sel,    // Register index 0-11
    input  [7:0]  z80_wbyte,
    output [15:0] z80_rdata,      // Full word, harness picks byte
    input         z80_wr_lo,      // Write low byte strobe
    input         z80_wr_hi       // Write high byte strobe
);

    reg [15:0] regs [0:11];

    integer i;

    // Z8000 read (combinational)
    assign z8k_rdata = regs[z8k_reg_sel];

    // Z80 read (combinational)
    assign z80_rdata = regs[z80_reg_sel];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 12; i = i + 1)
                regs[i] <= 16'h0000;
        end else begin
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
        end
    end

endmodule
