// Generic/simulation Z80 firmware RAM.
// Implements the z80_fw_ram interface used by z80_harness.v.

`timescale 1ns / 1ps

module z80_fw_ram (
    input         clk,
    input  [12:0] addr,
    input  [7:0]  din,
    input         we,
    output reg [7:0] dout
);

    reg [7:0] ram [0:8191];

    always @(posedge clk) begin
        if (we)
            ram[addr] <= din;
        dout <= ram[addr];
    end

    initial begin
        $readmemh("z80_fw.hex", ram);
    end

endmodule
