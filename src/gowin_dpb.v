// Gowin Dual-Port Block RAM wrapper
// 8K x 16-bit (16KB total) using SDPB primitives
// Port A: Write port (directly active)
// Port B: Read port (directly active)
//
// Pre-initialized with Z8000 test harness bootstrap and dump routines

module gowin_dpb (
    input         clk,

    // Write port
    input         wr_en,
    input  [12:0] wr_addr,
    input  [15:0] wr_data,
    input  [1:0]  wr_be,      // Byte enables: [1]=high byte, [0]=low byte

    // Read port
    input  [12:0] rd_addr,
    output [15:0] rd_data
);

// Use two 8-bit wide SDPBs for byte-write support

// High byte SDPB (even addresses)
wire [31:0] do_hi;
wire [7:0] rd_data_hi = do_hi[7:0];

SDPB #(
    .READ_MODE(0),           // 0 = bypass mode (no output register)
    .BIT_WIDTH_0(8),         // Write port width
    .BIT_WIDTH_1(8),         // Read port width
    .BLK_SEL_0(3'b000),
    .BLK_SEL_1(3'b000),
    .RESET_MODE("SYNC"),
    // Initialization for bootstrap and dump routines
    .INIT_RAM_00(256'h0000000000000040000000000000000000000000000000000000000000004000),
    .INIT_RAM_01(256'h0061006100610061006100610061006100610061006100610061006100610061),
    .INIT_RAM_02(256'h000000000000000000000000000000000000000000000000000000000000025E),
    .INIT_RAM_03(256'h006F006F006F006F006F006F006F006F006F006F006F006F006F006F006F006F),
    .INIT_RAM_04(256'h0000000000000000000000000000000000000000000000000000007A006FDE21),
    .INIT_RAM_05(256'h0),
    .INIT_RAM_06(256'h0),
    .INIT_RAM_07(256'h0),
    .INIT_RAM_08(256'h000000000000000000000000000000000000000000000000000000000000005E),
    .INIT_RAM_09(256'h0),
    .INIT_RAM_0A(256'h0),
    .INIT_RAM_0B(256'h0),
    .INIT_RAM_0C(256'h0),
    .INIT_RAM_0D(256'h0),
    .INIT_RAM_0E(256'h0),
    .INIT_RAM_0F(256'h0),
    .INIT_RAM_10(256'h0),
    .INIT_RAM_11(256'h0),
    .INIT_RAM_12(256'h0),
    .INIT_RAM_13(256'h0),
    .INIT_RAM_14(256'h0),
    .INIT_RAM_15(256'h0),
    .INIT_RAM_16(256'h0),
    .INIT_RAM_17(256'h0),
    .INIT_RAM_18(256'h0),
    .INIT_RAM_19(256'h0),
    .INIT_RAM_1A(256'h0),
    .INIT_RAM_1B(256'h0),
    .INIT_RAM_1C(256'h0),
    .INIT_RAM_1D(256'h0),
    .INIT_RAM_1E(256'h0),
    .INIT_RAM_1F(256'h0)
) bram_hi (
    .CLKA(clk),
    .CEA(wr_en & wr_be[1]),
    .RESETA(1'b0),
    .DI({{24{1'b0}}, wr_data[15:8]}),
    .ADA({wr_addr, 1'b0}),
    .BLKSELA(3'b000),

    .CLKB(clk),
    .CEB(1'b1),
    .RESETB(1'b0),
    .OCE(1'b1),
    .ADB({rd_addr, 1'b0}),
    .BLKSELB(3'b000),
    .DO(do_hi)
);

// Low byte SDPB (odd addresses)
wire [31:0] do_lo;
wire [7:0] rd_data_lo = do_lo[7:0];

SDPB #(
    .READ_MODE(0),           // 0 = bypass mode (no output register)
    .BIT_WIDTH_0(8),
    .BIT_WIDTH_1(8),
    .BLK_SEL_0(3'b000),
    .BLK_SEL_1(3'b000),
    .RESET_MODE("SYNC"),
    // Initialization for bootstrap and dump routines
    .INIT_RAM_00(256'h0000000000000000000000000000000000000000000000000000000000400000),
    .INIT_RAM_01(256'h2E0F2C0E2A0D280C260B240A220920081E071C061A0518041603140212011000),
    .INIT_RAM_02(256'h0000000000000000000000000000000000000000000000000000000000000008),
    .INIT_RAM_03(256'hAE0FAC0EAA0DA80CA60BA40AA209A0089E079C069A0598049603940292019000),
    .INIT_RAM_04(256'h00000000000000000000000000000000000000000000000000000000B000AD00),
    .INIT_RAM_05(256'h0),
    .INIT_RAM_06(256'h0),
    .INIT_RAM_07(256'h0),
    .INIT_RAM_08(256'h000000000000000000000000000000000000000000000000000000000000C008),
    .INIT_RAM_09(256'h0),
    .INIT_RAM_0A(256'h0),
    .INIT_RAM_0B(256'h0),
    .INIT_RAM_0C(256'h0),
    .INIT_RAM_0D(256'h0),
    .INIT_RAM_0E(256'h0),
    .INIT_RAM_0F(256'h0),
    .INIT_RAM_10(256'h0),
    .INIT_RAM_11(256'h0),
    .INIT_RAM_12(256'h0),
    .INIT_RAM_13(256'h0),
    .INIT_RAM_14(256'h0),
    .INIT_RAM_15(256'h0),
    .INIT_RAM_16(256'h0),
    .INIT_RAM_17(256'h0),
    .INIT_RAM_18(256'h0),
    .INIT_RAM_19(256'h0),
    .INIT_RAM_1A(256'h0),
    .INIT_RAM_1B(256'h0),
    .INIT_RAM_1C(256'h0),
    .INIT_RAM_1D(256'h0),
    .INIT_RAM_1E(256'h0),
    .INIT_RAM_1F(256'h0)
) bram_lo (
    .CLKA(clk),
    .CEA(wr_en & wr_be[0]),
    .RESETA(1'b0),
    .DI({{24{1'b0}}, wr_data[7:0]}),
    .ADA({wr_addr, 1'b0}),
    .BLKSELA(3'b000),

    .CLKB(clk),
    .CEB(1'b1),
    .RESETB(1'b0),
    .OCE(1'b1),
    .ADB({rd_addr, 1'b0}),
    .BLKSELB(3'b000),
    .DO(do_lo)
);

assign rd_data = {rd_data_hi, rd_data_lo};

endmodule
