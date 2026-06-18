// Quartus Z80 firmware RAM.
// Implements the z80_fw_ram interface used by ../src/z80_harness.v.

`timescale 1ns / 1ps

module z80_fw_ram (
    input         clk,
    input  [12:0] addr,
    input  [7:0]  din,
    input         we,
    output [7:0]  dout
);

    altsyncram #(
        .operation_mode("SINGLE_PORT"),
        .width_a(8),
        .widthad_a(13),
        .outdata_reg_a("UNREGISTERED"),
        .init_file("z80_fw.mif"),
        .intended_device_family("Cyclone IV E")
    ) z80_ram (
        .clock0(clk),
        .address_a(addr),
        .data_a(din),
        .wren_a(we),
        .q_a(dout),
        // Unused ports
        .aclr0(1'b0),
        .aclr1(1'b0),
        .address_b(13'b0),
        .addressstall_a(1'b0),
        .addressstall_b(1'b0),
        .byteena_a(1'b1),
        .byteena_b(1'b1),
        .clock1(1'b1),
        .clocken0(1'b1),
        .clocken1(1'b1),
        .clocken2(1'b1),
        .clocken3(1'b1),
        .data_b(8'b0),
        .eccstatus(),
        .q_b(),
        .rden_a(1'b1),
        .rden_b(1'b1),
        .wren_b(1'b0)
    );

endmodule
