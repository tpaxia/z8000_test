// Gowin Block RAM wrapper using SP (Single Port) primitives
// 8K x 16-bit (16KB total) using eight 8-bit SP instances
// 4 SP blocks per byte bank, selected by addr[12:11]
//
// Based on Gowin IP Core Generator output

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

`ifdef SIMULATION
// Simulation model - simple reg arrays (8K words)
reg [7:0] mem_hi [0:8191];
reg [7:0] mem_lo [0:8191];
reg [7:0] rd_data_hi, rd_data_lo;
integer init_i;

wire [12:0] addr = wr_en ? wr_addr[12:0] : rd_addr[12:0];

// Initialize to zeros
initial begin
    for (init_i = 0; init_i < 8192; init_i = init_i + 1) begin
        mem_hi[init_i] = 8'h00;
        mem_lo[init_i] = 8'h00;
    end
    // Load initialization data (matching INIT_RAM content)
    mem_hi[0] = 8'h00; mem_lo[0] = 8'h00;
    mem_hi[1] = 8'h40; mem_lo[1] = 8'h00;
    mem_hi[2] = 8'h00; mem_lo[2] = 8'h40;
end

always @(posedge clk) begin
    if (wr_en) begin
        if (wr_be[1]) mem_hi[addr] <= wr_data[15:8];
        if (wr_be[0]) mem_lo[addr] <= wr_data[7:0];
    end
    rd_data_hi <= mem_hi[addr];
    rd_data_lo <= mem_lo[addr];
end

assign rd_data = {rd_data_hi, rd_data_lo};

`else
// Gowin SP primitives for synthesis
// 4 blocks per bank, selected by addr[12:11]

wire [12:0] addr = wr_en ? wr_addr[12:0] : rd_addr[12:0];
wire [2:0] blk_sel = {1'b0, addr[12:11]};
wire gw_gnd = 1'b0;

// High byte outputs from each block
wire [7:0] rd_data_hi_0, rd_data_hi_1, rd_data_hi_2, rd_data_hi_3;
wire [23:0] sp_hi_dout_unused_0, sp_hi_dout_unused_1, sp_hi_dout_unused_2, sp_hi_dout_unused_3;

// Low byte outputs from each block
wire [7:0] rd_data_lo_0, rd_data_lo_1, rd_data_lo_2, rd_data_lo_3;
wire [23:0] sp_lo_dout_unused_0, sp_lo_dout_unused_1, sp_lo_dout_unused_2, sp_lo_dout_unused_3;

// Mux outputs based on registered block select
reg [1:0] blk_sel_r;
always @(posedge clk) blk_sel_r <= addr[12:11];

wire [7:0] rd_data_hi = (blk_sel_r == 2'd0) ? rd_data_hi_0 :
                        (blk_sel_r == 2'd1) ? rd_data_hi_1 :
                        (blk_sel_r == 2'd2) ? rd_data_hi_2 : rd_data_hi_3;
wire [7:0] rd_data_lo = (blk_sel_r == 2'd0) ? rd_data_lo_0 :
                        (blk_sel_r == 2'd1) ? rd_data_lo_1 :
                        (blk_sel_r == 2'd2) ? rd_data_lo_2 : rd_data_lo_3;

//=============================================================================
// High byte block 0 (addresses 0x0000-0x07FF)
//=============================================================================
SP sp_hi_0 (
    .DO({sp_hi_dout_unused_0, rd_data_hi_0}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[1]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[15:8]})
);
defparam sp_hi_0.READ_MODE = 1'b0;
defparam sp_hi_0.WRITE_MODE = 2'b00;
defparam sp_hi_0.BIT_WIDTH = 8;
defparam sp_hi_0.BLK_SEL = 3'b000;
defparam sp_hi_0.RESET_MODE = "SYNC";
defparam sp_hi_0.INIT_RAM_00 = 256'h0000000000000000000000000000000000000000000000000000000000004000;
defparam sp_hi_0.INIT_RAM_01 = 256'h0061006100610061006100610061006100610061006100610061006100610061;
defparam sp_hi_0.INIT_RAM_02 = 256'h000000000000000000000000000000000000000000000000000000000000025E;
defparam sp_hi_0.INIT_RAM_03 = 256'h006F006F006F006F006F006F006F006F006F006F006F006F006F006F006F006F;
defparam sp_hi_0.INIT_RAM_04 = 256'h0000000000000000000000000000000000000000000000000000007A006FDE21;
defparam sp_hi_0.INIT_RAM_05 = 256'h0;
defparam sp_hi_0.INIT_RAM_06 = 256'h0;
defparam sp_hi_0.INIT_RAM_07 = 256'h0;
defparam sp_hi_0.INIT_RAM_08 = 256'h0;
defparam sp_hi_0.INIT_RAM_09 = 256'h0;
defparam sp_hi_0.INIT_RAM_0A = 256'h0;
defparam sp_hi_0.INIT_RAM_0B = 256'h0;
defparam sp_hi_0.INIT_RAM_0C = 256'h0;
defparam sp_hi_0.INIT_RAM_0D = 256'h0;
defparam sp_hi_0.INIT_RAM_0E = 256'h0;
defparam sp_hi_0.INIT_RAM_0F = 256'h0;
defparam sp_hi_0.INIT_RAM_10 = 256'h0;
defparam sp_hi_0.INIT_RAM_11 = 256'h0;
defparam sp_hi_0.INIT_RAM_12 = 256'h0;
defparam sp_hi_0.INIT_RAM_13 = 256'h0;
defparam sp_hi_0.INIT_RAM_14 = 256'h0;
defparam sp_hi_0.INIT_RAM_15 = 256'h0;
defparam sp_hi_0.INIT_RAM_16 = 256'h0;
defparam sp_hi_0.INIT_RAM_17 = 256'h0;
defparam sp_hi_0.INIT_RAM_18 = 256'h0;
defparam sp_hi_0.INIT_RAM_19 = 256'h0;
defparam sp_hi_0.INIT_RAM_1A = 256'h0;
defparam sp_hi_0.INIT_RAM_1B = 256'h0;
defparam sp_hi_0.INIT_RAM_1C = 256'h0;
defparam sp_hi_0.INIT_RAM_1D = 256'h0;
defparam sp_hi_0.INIT_RAM_1E = 256'h0;
defparam sp_hi_0.INIT_RAM_1F = 256'h0;
defparam sp_hi_0.INIT_RAM_20 = 256'h0;
defparam sp_hi_0.INIT_RAM_21 = 256'h0;
defparam sp_hi_0.INIT_RAM_22 = 256'h0;
defparam sp_hi_0.INIT_RAM_23 = 256'h0;
defparam sp_hi_0.INIT_RAM_24 = 256'h0;
defparam sp_hi_0.INIT_RAM_25 = 256'h0;
defparam sp_hi_0.INIT_RAM_26 = 256'h0;
defparam sp_hi_0.INIT_RAM_27 = 256'h0;
defparam sp_hi_0.INIT_RAM_28 = 256'h0;
defparam sp_hi_0.INIT_RAM_29 = 256'h0;
defparam sp_hi_0.INIT_RAM_2A = 256'h0;
defparam sp_hi_0.INIT_RAM_2B = 256'h0;
defparam sp_hi_0.INIT_RAM_2C = 256'h0;
defparam sp_hi_0.INIT_RAM_2D = 256'h0;
defparam sp_hi_0.INIT_RAM_2E = 256'h0;
defparam sp_hi_0.INIT_RAM_2F = 256'h0;
defparam sp_hi_0.INIT_RAM_30 = 256'h0;
defparam sp_hi_0.INIT_RAM_31 = 256'h0;
defparam sp_hi_0.INIT_RAM_32 = 256'h0;
defparam sp_hi_0.INIT_RAM_33 = 256'h0;
defparam sp_hi_0.INIT_RAM_34 = 256'h0;
defparam sp_hi_0.INIT_RAM_35 = 256'h0;
defparam sp_hi_0.INIT_RAM_36 = 256'h0;
defparam sp_hi_0.INIT_RAM_37 = 256'h0;
defparam sp_hi_0.INIT_RAM_38 = 256'h0;
defparam sp_hi_0.INIT_RAM_39 = 256'h0;
defparam sp_hi_0.INIT_RAM_3A = 256'h0;
defparam sp_hi_0.INIT_RAM_3B = 256'h0;
defparam sp_hi_0.INIT_RAM_3C = 256'h0;
defparam sp_hi_0.INIT_RAM_3D = 256'h0;
defparam sp_hi_0.INIT_RAM_3E = 256'h0;
defparam sp_hi_0.INIT_RAM_3F = 256'h0;

//=============================================================================
// High byte block 1 (addresses 0x0800-0x0FFF)
//=============================================================================
SP sp_hi_1 (
    .DO({sp_hi_dout_unused_1, rd_data_hi_1}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[1]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[15:8]})
);
defparam sp_hi_1.READ_MODE = 1'b0;
defparam sp_hi_1.WRITE_MODE = 2'b00;
defparam sp_hi_1.BIT_WIDTH = 8;
defparam sp_hi_1.BLK_SEL = 3'b001;
defparam sp_hi_1.RESET_MODE = "SYNC";
defparam sp_hi_1.INIT_RAM_00 = 256'h0;
defparam sp_hi_1.INIT_RAM_01 = 256'h0;
defparam sp_hi_1.INIT_RAM_02 = 256'h0;
defparam sp_hi_1.INIT_RAM_03 = 256'h0;
defparam sp_hi_1.INIT_RAM_04 = 256'h0;
defparam sp_hi_1.INIT_RAM_05 = 256'h0;
defparam sp_hi_1.INIT_RAM_06 = 256'h0;
defparam sp_hi_1.INIT_RAM_07 = 256'h0;
defparam sp_hi_1.INIT_RAM_08 = 256'h0;
defparam sp_hi_1.INIT_RAM_09 = 256'h0;
defparam sp_hi_1.INIT_RAM_0A = 256'h0;
defparam sp_hi_1.INIT_RAM_0B = 256'h0;
defparam sp_hi_1.INIT_RAM_0C = 256'h0;
defparam sp_hi_1.INIT_RAM_0D = 256'h0;
defparam sp_hi_1.INIT_RAM_0E = 256'h0;
defparam sp_hi_1.INIT_RAM_0F = 256'h0;
defparam sp_hi_1.INIT_RAM_10 = 256'h0;
defparam sp_hi_1.INIT_RAM_11 = 256'h0;
defparam sp_hi_1.INIT_RAM_12 = 256'h0;
defparam sp_hi_1.INIT_RAM_13 = 256'h0;
defparam sp_hi_1.INIT_RAM_14 = 256'h0;
defparam sp_hi_1.INIT_RAM_15 = 256'h0;
defparam sp_hi_1.INIT_RAM_16 = 256'h0;
defparam sp_hi_1.INIT_RAM_17 = 256'h0;
defparam sp_hi_1.INIT_RAM_18 = 256'h0;
defparam sp_hi_1.INIT_RAM_19 = 256'h0;
defparam sp_hi_1.INIT_RAM_1A = 256'h0;
defparam sp_hi_1.INIT_RAM_1B = 256'h0;
defparam sp_hi_1.INIT_RAM_1C = 256'h0;
defparam sp_hi_1.INIT_RAM_1D = 256'h0;
defparam sp_hi_1.INIT_RAM_1E = 256'h0;
defparam sp_hi_1.INIT_RAM_1F = 256'h0;
defparam sp_hi_1.INIT_RAM_20 = 256'h0;
defparam sp_hi_1.INIT_RAM_21 = 256'h0;
defparam sp_hi_1.INIT_RAM_22 = 256'h0;
defparam sp_hi_1.INIT_RAM_23 = 256'h0;
defparam sp_hi_1.INIT_RAM_24 = 256'h0;
defparam sp_hi_1.INIT_RAM_25 = 256'h0;
defparam sp_hi_1.INIT_RAM_26 = 256'h0;
defparam sp_hi_1.INIT_RAM_27 = 256'h0;
defparam sp_hi_1.INIT_RAM_28 = 256'h0;
defparam sp_hi_1.INIT_RAM_29 = 256'h0;
defparam sp_hi_1.INIT_RAM_2A = 256'h0;
defparam sp_hi_1.INIT_RAM_2B = 256'h0;
defparam sp_hi_1.INIT_RAM_2C = 256'h0;
defparam sp_hi_1.INIT_RAM_2D = 256'h0;
defparam sp_hi_1.INIT_RAM_2E = 256'h0;
defparam sp_hi_1.INIT_RAM_2F = 256'h0;
defparam sp_hi_1.INIT_RAM_30 = 256'h0;
defparam sp_hi_1.INIT_RAM_31 = 256'h0;
defparam sp_hi_1.INIT_RAM_32 = 256'h0;
defparam sp_hi_1.INIT_RAM_33 = 256'h0;
defparam sp_hi_1.INIT_RAM_34 = 256'h0;
defparam sp_hi_1.INIT_RAM_35 = 256'h0;
defparam sp_hi_1.INIT_RAM_36 = 256'h0;
defparam sp_hi_1.INIT_RAM_37 = 256'h0;
defparam sp_hi_1.INIT_RAM_38 = 256'h0;
defparam sp_hi_1.INIT_RAM_39 = 256'h0;
defparam sp_hi_1.INIT_RAM_3A = 256'h0;
defparam sp_hi_1.INIT_RAM_3B = 256'h0;
defparam sp_hi_1.INIT_RAM_3C = 256'h0;
defparam sp_hi_1.INIT_RAM_3D = 256'h0;
defparam sp_hi_1.INIT_RAM_3E = 256'h0;
defparam sp_hi_1.INIT_RAM_3F = 256'h0;

//=============================================================================
// High byte block 2 (addresses 0x1000-0x17FF)
//=============================================================================
SP sp_hi_2 (
    .DO({sp_hi_dout_unused_2, rd_data_hi_2}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[1]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[15:8]})
);
defparam sp_hi_2.READ_MODE = 1'b0;
defparam sp_hi_2.WRITE_MODE = 2'b00;
defparam sp_hi_2.BIT_WIDTH = 8;
defparam sp_hi_2.BLK_SEL = 3'b010;
defparam sp_hi_2.RESET_MODE = "SYNC";
defparam sp_hi_2.INIT_RAM_00 = 256'h0;
defparam sp_hi_2.INIT_RAM_01 = 256'h0;
defparam sp_hi_2.INIT_RAM_02 = 256'h0;
defparam sp_hi_2.INIT_RAM_03 = 256'h0;
defparam sp_hi_2.INIT_RAM_04 = 256'h0;
defparam sp_hi_2.INIT_RAM_05 = 256'h0;
defparam sp_hi_2.INIT_RAM_06 = 256'h0;
defparam sp_hi_2.INIT_RAM_07 = 256'h0;
defparam sp_hi_2.INIT_RAM_08 = 256'h0;
defparam sp_hi_2.INIT_RAM_09 = 256'h0;
defparam sp_hi_2.INIT_RAM_0A = 256'h0;
defparam sp_hi_2.INIT_RAM_0B = 256'h0;
defparam sp_hi_2.INIT_RAM_0C = 256'h0;
defparam sp_hi_2.INIT_RAM_0D = 256'h0;
defparam sp_hi_2.INIT_RAM_0E = 256'h0;
defparam sp_hi_2.INIT_RAM_0F = 256'h0;
defparam sp_hi_2.INIT_RAM_10 = 256'h0;
defparam sp_hi_2.INIT_RAM_11 = 256'h0;
defparam sp_hi_2.INIT_RAM_12 = 256'h0;
defparam sp_hi_2.INIT_RAM_13 = 256'h0;
defparam sp_hi_2.INIT_RAM_14 = 256'h0;
defparam sp_hi_2.INIT_RAM_15 = 256'h0;
defparam sp_hi_2.INIT_RAM_16 = 256'h0;
defparam sp_hi_2.INIT_RAM_17 = 256'h0;
defparam sp_hi_2.INIT_RAM_18 = 256'h0;
defparam sp_hi_2.INIT_RAM_19 = 256'h0;
defparam sp_hi_2.INIT_RAM_1A = 256'h0;
defparam sp_hi_2.INIT_RAM_1B = 256'h0;
defparam sp_hi_2.INIT_RAM_1C = 256'h0;
defparam sp_hi_2.INIT_RAM_1D = 256'h0;
defparam sp_hi_2.INIT_RAM_1E = 256'h0;
defparam sp_hi_2.INIT_RAM_1F = 256'h0;
defparam sp_hi_2.INIT_RAM_20 = 256'h0;
defparam sp_hi_2.INIT_RAM_21 = 256'h0;
defparam sp_hi_2.INIT_RAM_22 = 256'h0;
defparam sp_hi_2.INIT_RAM_23 = 256'h0;
defparam sp_hi_2.INIT_RAM_24 = 256'h0;
defparam sp_hi_2.INIT_RAM_25 = 256'h0;
defparam sp_hi_2.INIT_RAM_26 = 256'h0;
defparam sp_hi_2.INIT_RAM_27 = 256'h0;
defparam sp_hi_2.INIT_RAM_28 = 256'h0;
defparam sp_hi_2.INIT_RAM_29 = 256'h0;
defparam sp_hi_2.INIT_RAM_2A = 256'h0;
defparam sp_hi_2.INIT_RAM_2B = 256'h0;
defparam sp_hi_2.INIT_RAM_2C = 256'h0;
defparam sp_hi_2.INIT_RAM_2D = 256'h0;
defparam sp_hi_2.INIT_RAM_2E = 256'h0;
defparam sp_hi_2.INIT_RAM_2F = 256'h0;
defparam sp_hi_2.INIT_RAM_30 = 256'h0;
defparam sp_hi_2.INIT_RAM_31 = 256'h0;
defparam sp_hi_2.INIT_RAM_32 = 256'h0;
defparam sp_hi_2.INIT_RAM_33 = 256'h0;
defparam sp_hi_2.INIT_RAM_34 = 256'h0;
defparam sp_hi_2.INIT_RAM_35 = 256'h0;
defparam sp_hi_2.INIT_RAM_36 = 256'h0;
defparam sp_hi_2.INIT_RAM_37 = 256'h0;
defparam sp_hi_2.INIT_RAM_38 = 256'h0;
defparam sp_hi_2.INIT_RAM_39 = 256'h0;
defparam sp_hi_2.INIT_RAM_3A = 256'h0;
defparam sp_hi_2.INIT_RAM_3B = 256'h0;
defparam sp_hi_2.INIT_RAM_3C = 256'h0;
defparam sp_hi_2.INIT_RAM_3D = 256'h0;
defparam sp_hi_2.INIT_RAM_3E = 256'h0;
defparam sp_hi_2.INIT_RAM_3F = 256'h0;

//=============================================================================
// High byte block 3 (addresses 0x1800-0x1FFF)
//=============================================================================
SP sp_hi_3 (
    .DO({sp_hi_dout_unused_3, rd_data_hi_3}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[1]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[15:8]})
);
defparam sp_hi_3.READ_MODE = 1'b0;
defparam sp_hi_3.WRITE_MODE = 2'b00;
defparam sp_hi_3.BIT_WIDTH = 8;
defparam sp_hi_3.BLK_SEL = 3'b011;
defparam sp_hi_3.RESET_MODE = "SYNC";
defparam sp_hi_3.INIT_RAM_00 = 256'h0;
defparam sp_hi_3.INIT_RAM_01 = 256'h0;
defparam sp_hi_3.INIT_RAM_02 = 256'h0;
defparam sp_hi_3.INIT_RAM_03 = 256'h0;
defparam sp_hi_3.INIT_RAM_04 = 256'h0;
defparam sp_hi_3.INIT_RAM_05 = 256'h0;
defparam sp_hi_3.INIT_RAM_06 = 256'h0;
defparam sp_hi_3.INIT_RAM_07 = 256'h0;
defparam sp_hi_3.INIT_RAM_08 = 256'h0;
defparam sp_hi_3.INIT_RAM_09 = 256'h0;
defparam sp_hi_3.INIT_RAM_0A = 256'h0;
defparam sp_hi_3.INIT_RAM_0B = 256'h0;
defparam sp_hi_3.INIT_RAM_0C = 256'h0;
defparam sp_hi_3.INIT_RAM_0D = 256'h0;
defparam sp_hi_3.INIT_RAM_0E = 256'h0;
defparam sp_hi_3.INIT_RAM_0F = 256'h0;
defparam sp_hi_3.INIT_RAM_10 = 256'h0;
defparam sp_hi_3.INIT_RAM_11 = 256'h0;
defparam sp_hi_3.INIT_RAM_12 = 256'h0;
defparam sp_hi_3.INIT_RAM_13 = 256'h0;
defparam sp_hi_3.INIT_RAM_14 = 256'h0;
defparam sp_hi_3.INIT_RAM_15 = 256'h0;
defparam sp_hi_3.INIT_RAM_16 = 256'h0;
defparam sp_hi_3.INIT_RAM_17 = 256'h0;
defparam sp_hi_3.INIT_RAM_18 = 256'h0;
defparam sp_hi_3.INIT_RAM_19 = 256'h0;
defparam sp_hi_3.INIT_RAM_1A = 256'h0;
defparam sp_hi_3.INIT_RAM_1B = 256'h0;
defparam sp_hi_3.INIT_RAM_1C = 256'h0;
defparam sp_hi_3.INIT_RAM_1D = 256'h0;
defparam sp_hi_3.INIT_RAM_1E = 256'h0;
defparam sp_hi_3.INIT_RAM_1F = 256'h0;
defparam sp_hi_3.INIT_RAM_20 = 256'h0;
defparam sp_hi_3.INIT_RAM_21 = 256'h0;
defparam sp_hi_3.INIT_RAM_22 = 256'h0;
defparam sp_hi_3.INIT_RAM_23 = 256'h0;
defparam sp_hi_3.INIT_RAM_24 = 256'h0;
defparam sp_hi_3.INIT_RAM_25 = 256'h0;
defparam sp_hi_3.INIT_RAM_26 = 256'h0;
defparam sp_hi_3.INIT_RAM_27 = 256'h0;
defparam sp_hi_3.INIT_RAM_28 = 256'h0;
defparam sp_hi_3.INIT_RAM_29 = 256'h0;
defparam sp_hi_3.INIT_RAM_2A = 256'h0;
defparam sp_hi_3.INIT_RAM_2B = 256'h0;
defparam sp_hi_3.INIT_RAM_2C = 256'h0;
defparam sp_hi_3.INIT_RAM_2D = 256'h0;
defparam sp_hi_3.INIT_RAM_2E = 256'h0;
defparam sp_hi_3.INIT_RAM_2F = 256'h0;
defparam sp_hi_3.INIT_RAM_30 = 256'h0;
defparam sp_hi_3.INIT_RAM_31 = 256'h0;
defparam sp_hi_3.INIT_RAM_32 = 256'h0;
defparam sp_hi_3.INIT_RAM_33 = 256'h0;
defparam sp_hi_3.INIT_RAM_34 = 256'h0;
defparam sp_hi_3.INIT_RAM_35 = 256'h0;
defparam sp_hi_3.INIT_RAM_36 = 256'h0;
defparam sp_hi_3.INIT_RAM_37 = 256'h0;
defparam sp_hi_3.INIT_RAM_38 = 256'h0;
defparam sp_hi_3.INIT_RAM_39 = 256'h0;
defparam sp_hi_3.INIT_RAM_3A = 256'h0;
defparam sp_hi_3.INIT_RAM_3B = 256'h0;
defparam sp_hi_3.INIT_RAM_3C = 256'h0;
defparam sp_hi_3.INIT_RAM_3D = 256'h0;
defparam sp_hi_3.INIT_RAM_3E = 256'h0;
defparam sp_hi_3.INIT_RAM_3F = 256'h0;

//=============================================================================
// Low byte block 0 (addresses 0x0000-0x07FF)
//=============================================================================
SP sp_lo_0 (
    .DO({sp_lo_dout_unused_0, rd_data_lo_0}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[0]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[7:0]})
);
defparam sp_lo_0.READ_MODE = 1'b0;
defparam sp_lo_0.WRITE_MODE = 2'b00;
defparam sp_lo_0.BIT_WIDTH = 8;
defparam sp_lo_0.BLK_SEL = 3'b000;
defparam sp_lo_0.RESET_MODE = "SYNC";
defparam sp_lo_0.INIT_RAM_00 = 256'h0000000000000000000000000000000000000000000000000000000000400000;
defparam sp_lo_0.INIT_RAM_01 = 256'h2E0F2C0E2A0D280C260B240A220920081E071C061A0518041603140212011000;
defparam sp_lo_0.INIT_RAM_02 = 256'h0000000000000000000000000000000000000000000000000000000000000008;
defparam sp_lo_0.INIT_RAM_03 = 256'hAE0FAC0EAA0DA80CA60BA40AA209A0089E079C069A0598049603940292019000;
defparam sp_lo_0.INIT_RAM_04 = 256'h00000000000000000000000000000000000000000000000000000000B000AD00;
defparam sp_lo_0.INIT_RAM_05 = 256'h0;
defparam sp_lo_0.INIT_RAM_06 = 256'h0;
defparam sp_lo_0.INIT_RAM_07 = 256'h0;
defparam sp_lo_0.INIT_RAM_08 = 256'h0;
defparam sp_lo_0.INIT_RAM_09 = 256'h0;
defparam sp_lo_0.INIT_RAM_0A = 256'h0;
defparam sp_lo_0.INIT_RAM_0B = 256'h0;
defparam sp_lo_0.INIT_RAM_0C = 256'h0;
defparam sp_lo_0.INIT_RAM_0D = 256'h0;
defparam sp_lo_0.INIT_RAM_0E = 256'h0;
defparam sp_lo_0.INIT_RAM_0F = 256'h0;
defparam sp_lo_0.INIT_RAM_10 = 256'h0;
defparam sp_lo_0.INIT_RAM_11 = 256'h0;
defparam sp_lo_0.INIT_RAM_12 = 256'h0;
defparam sp_lo_0.INIT_RAM_13 = 256'h0;
defparam sp_lo_0.INIT_RAM_14 = 256'h0;
defparam sp_lo_0.INIT_RAM_15 = 256'h0;
defparam sp_lo_0.INIT_RAM_16 = 256'h0;
defparam sp_lo_0.INIT_RAM_17 = 256'h0;
defparam sp_lo_0.INIT_RAM_18 = 256'h0;
defparam sp_lo_0.INIT_RAM_19 = 256'h0;
defparam sp_lo_0.INIT_RAM_1A = 256'h0;
defparam sp_lo_0.INIT_RAM_1B = 256'h0;
defparam sp_lo_0.INIT_RAM_1C = 256'h0;
defparam sp_lo_0.INIT_RAM_1D = 256'h0;
defparam sp_lo_0.INIT_RAM_1E = 256'h0;
defparam sp_lo_0.INIT_RAM_1F = 256'h0;
defparam sp_lo_0.INIT_RAM_20 = 256'h0;
defparam sp_lo_0.INIT_RAM_21 = 256'h0;
defparam sp_lo_0.INIT_RAM_22 = 256'h0;
defparam sp_lo_0.INIT_RAM_23 = 256'h0;
defparam sp_lo_0.INIT_RAM_24 = 256'h0;
defparam sp_lo_0.INIT_RAM_25 = 256'h0;
defparam sp_lo_0.INIT_RAM_26 = 256'h0;
defparam sp_lo_0.INIT_RAM_27 = 256'h0;
defparam sp_lo_0.INIT_RAM_28 = 256'h0;
defparam sp_lo_0.INIT_RAM_29 = 256'h0;
defparam sp_lo_0.INIT_RAM_2A = 256'h0;
defparam sp_lo_0.INIT_RAM_2B = 256'h0;
defparam sp_lo_0.INIT_RAM_2C = 256'h0;
defparam sp_lo_0.INIT_RAM_2D = 256'h0;
defparam sp_lo_0.INIT_RAM_2E = 256'h0;
defparam sp_lo_0.INIT_RAM_2F = 256'h0;
defparam sp_lo_0.INIT_RAM_30 = 256'h0;
defparam sp_lo_0.INIT_RAM_31 = 256'h0;
defparam sp_lo_0.INIT_RAM_32 = 256'h0;
defparam sp_lo_0.INIT_RAM_33 = 256'h0;
defparam sp_lo_0.INIT_RAM_34 = 256'h0;
defparam sp_lo_0.INIT_RAM_35 = 256'h0;
defparam sp_lo_0.INIT_RAM_36 = 256'h0;
defparam sp_lo_0.INIT_RAM_37 = 256'h0;
defparam sp_lo_0.INIT_RAM_38 = 256'h0;
defparam sp_lo_0.INIT_RAM_39 = 256'h0;
defparam sp_lo_0.INIT_RAM_3A = 256'h0;
defparam sp_lo_0.INIT_RAM_3B = 256'h0;
defparam sp_lo_0.INIT_RAM_3C = 256'h0;
defparam sp_lo_0.INIT_RAM_3D = 256'h0;
defparam sp_lo_0.INIT_RAM_3E = 256'h0;
defparam sp_lo_0.INIT_RAM_3F = 256'h0;

//=============================================================================
// Low byte block 1 (addresses 0x0800-0x0FFF)
//=============================================================================
SP sp_lo_1 (
    .DO({sp_lo_dout_unused_1, rd_data_lo_1}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[0]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[7:0]})
);
defparam sp_lo_1.READ_MODE = 1'b0;
defparam sp_lo_1.WRITE_MODE = 2'b00;
defparam sp_lo_1.BIT_WIDTH = 8;
defparam sp_lo_1.BLK_SEL = 3'b001;
defparam sp_lo_1.RESET_MODE = "SYNC";
defparam sp_lo_1.INIT_RAM_00 = 256'h0;
defparam sp_lo_1.INIT_RAM_01 = 256'h0;
defparam sp_lo_1.INIT_RAM_02 = 256'h0;
defparam sp_lo_1.INIT_RAM_03 = 256'h0;
defparam sp_lo_1.INIT_RAM_04 = 256'h0;
defparam sp_lo_1.INIT_RAM_05 = 256'h0;
defparam sp_lo_1.INIT_RAM_06 = 256'h0;
defparam sp_lo_1.INIT_RAM_07 = 256'h0;
defparam sp_lo_1.INIT_RAM_08 = 256'h0;
defparam sp_lo_1.INIT_RAM_09 = 256'h0;
defparam sp_lo_1.INIT_RAM_0A = 256'h0;
defparam sp_lo_1.INIT_RAM_0B = 256'h0;
defparam sp_lo_1.INIT_RAM_0C = 256'h0;
defparam sp_lo_1.INIT_RAM_0D = 256'h0;
defparam sp_lo_1.INIT_RAM_0E = 256'h0;
defparam sp_lo_1.INIT_RAM_0F = 256'h0;
defparam sp_lo_1.INIT_RAM_10 = 256'h0;
defparam sp_lo_1.INIT_RAM_11 = 256'h0;
defparam sp_lo_1.INIT_RAM_12 = 256'h0;
defparam sp_lo_1.INIT_RAM_13 = 256'h0;
defparam sp_lo_1.INIT_RAM_14 = 256'h0;
defparam sp_lo_1.INIT_RAM_15 = 256'h0;
defparam sp_lo_1.INIT_RAM_16 = 256'h0;
defparam sp_lo_1.INIT_RAM_17 = 256'h0;
defparam sp_lo_1.INIT_RAM_18 = 256'h0;
defparam sp_lo_1.INIT_RAM_19 = 256'h0;
defparam sp_lo_1.INIT_RAM_1A = 256'h0;
defparam sp_lo_1.INIT_RAM_1B = 256'h0;
defparam sp_lo_1.INIT_RAM_1C = 256'h0;
defparam sp_lo_1.INIT_RAM_1D = 256'h0;
defparam sp_lo_1.INIT_RAM_1E = 256'h0;
defparam sp_lo_1.INIT_RAM_1F = 256'h0;
defparam sp_lo_1.INIT_RAM_20 = 256'h0;
defparam sp_lo_1.INIT_RAM_21 = 256'h0;
defparam sp_lo_1.INIT_RAM_22 = 256'h0;
defparam sp_lo_1.INIT_RAM_23 = 256'h0;
defparam sp_lo_1.INIT_RAM_24 = 256'h0;
defparam sp_lo_1.INIT_RAM_25 = 256'h0;
defparam sp_lo_1.INIT_RAM_26 = 256'h0;
defparam sp_lo_1.INIT_RAM_27 = 256'h0;
defparam sp_lo_1.INIT_RAM_28 = 256'h0;
defparam sp_lo_1.INIT_RAM_29 = 256'h0;
defparam sp_lo_1.INIT_RAM_2A = 256'h0;
defparam sp_lo_1.INIT_RAM_2B = 256'h0;
defparam sp_lo_1.INIT_RAM_2C = 256'h0;
defparam sp_lo_1.INIT_RAM_2D = 256'h0;
defparam sp_lo_1.INIT_RAM_2E = 256'h0;
defparam sp_lo_1.INIT_RAM_2F = 256'h0;
defparam sp_lo_1.INIT_RAM_30 = 256'h0;
defparam sp_lo_1.INIT_RAM_31 = 256'h0;
defparam sp_lo_1.INIT_RAM_32 = 256'h0;
defparam sp_lo_1.INIT_RAM_33 = 256'h0;
defparam sp_lo_1.INIT_RAM_34 = 256'h0;
defparam sp_lo_1.INIT_RAM_35 = 256'h0;
defparam sp_lo_1.INIT_RAM_36 = 256'h0;
defparam sp_lo_1.INIT_RAM_37 = 256'h0;
defparam sp_lo_1.INIT_RAM_38 = 256'h0;
defparam sp_lo_1.INIT_RAM_39 = 256'h0;
defparam sp_lo_1.INIT_RAM_3A = 256'h0;
defparam sp_lo_1.INIT_RAM_3B = 256'h0;
defparam sp_lo_1.INIT_RAM_3C = 256'h0;
defparam sp_lo_1.INIT_RAM_3D = 256'h0;
defparam sp_lo_1.INIT_RAM_3E = 256'h0;
defparam sp_lo_1.INIT_RAM_3F = 256'h0;

//=============================================================================
// Low byte block 2 (addresses 0x1000-0x17FF)
//=============================================================================
SP sp_lo_2 (
    .DO({sp_lo_dout_unused_2, rd_data_lo_2}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[0]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[7:0]})
);
defparam sp_lo_2.READ_MODE = 1'b0;
defparam sp_lo_2.WRITE_MODE = 2'b00;
defparam sp_lo_2.BIT_WIDTH = 8;
defparam sp_lo_2.BLK_SEL = 3'b010;
defparam sp_lo_2.RESET_MODE = "SYNC";
defparam sp_lo_2.INIT_RAM_00 = 256'h0;
defparam sp_lo_2.INIT_RAM_01 = 256'h0;
defparam sp_lo_2.INIT_RAM_02 = 256'h0;
defparam sp_lo_2.INIT_RAM_03 = 256'h0;
defparam sp_lo_2.INIT_RAM_04 = 256'h0;
defparam sp_lo_2.INIT_RAM_05 = 256'h0;
defparam sp_lo_2.INIT_RAM_06 = 256'h0;
defparam sp_lo_2.INIT_RAM_07 = 256'h0;
defparam sp_lo_2.INIT_RAM_08 = 256'h0;
defparam sp_lo_2.INIT_RAM_09 = 256'h0;
defparam sp_lo_2.INIT_RAM_0A = 256'h0;
defparam sp_lo_2.INIT_RAM_0B = 256'h0;
defparam sp_lo_2.INIT_RAM_0C = 256'h0;
defparam sp_lo_2.INIT_RAM_0D = 256'h0;
defparam sp_lo_2.INIT_RAM_0E = 256'h0;
defparam sp_lo_2.INIT_RAM_0F = 256'h0;
defparam sp_lo_2.INIT_RAM_10 = 256'h0;
defparam sp_lo_2.INIT_RAM_11 = 256'h0;
defparam sp_lo_2.INIT_RAM_12 = 256'h0;
defparam sp_lo_2.INIT_RAM_13 = 256'h0;
defparam sp_lo_2.INIT_RAM_14 = 256'h0;
defparam sp_lo_2.INIT_RAM_15 = 256'h0;
defparam sp_lo_2.INIT_RAM_16 = 256'h0;
defparam sp_lo_2.INIT_RAM_17 = 256'h0;
defparam sp_lo_2.INIT_RAM_18 = 256'h0;
defparam sp_lo_2.INIT_RAM_19 = 256'h0;
defparam sp_lo_2.INIT_RAM_1A = 256'h0;
defparam sp_lo_2.INIT_RAM_1B = 256'h0;
defparam sp_lo_2.INIT_RAM_1C = 256'h0;
defparam sp_lo_2.INIT_RAM_1D = 256'h0;
defparam sp_lo_2.INIT_RAM_1E = 256'h0;
defparam sp_lo_2.INIT_RAM_1F = 256'h0;
defparam sp_lo_2.INIT_RAM_20 = 256'h0;
defparam sp_lo_2.INIT_RAM_21 = 256'h0;
defparam sp_lo_2.INIT_RAM_22 = 256'h0;
defparam sp_lo_2.INIT_RAM_23 = 256'h0;
defparam sp_lo_2.INIT_RAM_24 = 256'h0;
defparam sp_lo_2.INIT_RAM_25 = 256'h0;
defparam sp_lo_2.INIT_RAM_26 = 256'h0;
defparam sp_lo_2.INIT_RAM_27 = 256'h0;
defparam sp_lo_2.INIT_RAM_28 = 256'h0;
defparam sp_lo_2.INIT_RAM_29 = 256'h0;
defparam sp_lo_2.INIT_RAM_2A = 256'h0;
defparam sp_lo_2.INIT_RAM_2B = 256'h0;
defparam sp_lo_2.INIT_RAM_2C = 256'h0;
defparam sp_lo_2.INIT_RAM_2D = 256'h0;
defparam sp_lo_2.INIT_RAM_2E = 256'h0;
defparam sp_lo_2.INIT_RAM_2F = 256'h0;
defparam sp_lo_2.INIT_RAM_30 = 256'h0;
defparam sp_lo_2.INIT_RAM_31 = 256'h0;
defparam sp_lo_2.INIT_RAM_32 = 256'h0;
defparam sp_lo_2.INIT_RAM_33 = 256'h0;
defparam sp_lo_2.INIT_RAM_34 = 256'h0;
defparam sp_lo_2.INIT_RAM_35 = 256'h0;
defparam sp_lo_2.INIT_RAM_36 = 256'h0;
defparam sp_lo_2.INIT_RAM_37 = 256'h0;
defparam sp_lo_2.INIT_RAM_38 = 256'h0;
defparam sp_lo_2.INIT_RAM_39 = 256'h0;
defparam sp_lo_2.INIT_RAM_3A = 256'h0;
defparam sp_lo_2.INIT_RAM_3B = 256'h0;
defparam sp_lo_2.INIT_RAM_3C = 256'h0;
defparam sp_lo_2.INIT_RAM_3D = 256'h0;
defparam sp_lo_2.INIT_RAM_3E = 256'h0;
defparam sp_lo_2.INIT_RAM_3F = 256'h0;

//=============================================================================
// Low byte block 3 (addresses 0x1800-0x1FFF)
//=============================================================================
SP sp_lo_3 (
    .DO({sp_lo_dout_unused_3, rd_data_lo_3}),
    .CLK(clk),
    .OCE(1'b1),
    .CE(1'b1),
    .RESET(1'b0),
    .WRE(wr_en & wr_be[0]),
    .BLKSEL(blk_sel),
    .AD({addr[10:0], gw_gnd, gw_gnd, gw_gnd}),
    .DI({24'b0, wr_data[7:0]})
);
defparam sp_lo_3.READ_MODE = 1'b0;
defparam sp_lo_3.WRITE_MODE = 2'b00;
defparam sp_lo_3.BIT_WIDTH = 8;
defparam sp_lo_3.BLK_SEL = 3'b011;
defparam sp_lo_3.RESET_MODE = "SYNC";
defparam sp_lo_3.INIT_RAM_00 = 256'h0;
defparam sp_lo_3.INIT_RAM_01 = 256'h0;
defparam sp_lo_3.INIT_RAM_02 = 256'h0;
defparam sp_lo_3.INIT_RAM_03 = 256'h0;
defparam sp_lo_3.INIT_RAM_04 = 256'h0;
defparam sp_lo_3.INIT_RAM_05 = 256'h0;
defparam sp_lo_3.INIT_RAM_06 = 256'h0;
defparam sp_lo_3.INIT_RAM_07 = 256'h0;
defparam sp_lo_3.INIT_RAM_08 = 256'h0;
defparam sp_lo_3.INIT_RAM_09 = 256'h0;
defparam sp_lo_3.INIT_RAM_0A = 256'h0;
defparam sp_lo_3.INIT_RAM_0B = 256'h0;
defparam sp_lo_3.INIT_RAM_0C = 256'h0;
defparam sp_lo_3.INIT_RAM_0D = 256'h0;
defparam sp_lo_3.INIT_RAM_0E = 256'h0;
defparam sp_lo_3.INIT_RAM_0F = 256'h0;
defparam sp_lo_3.INIT_RAM_10 = 256'h0;
defparam sp_lo_3.INIT_RAM_11 = 256'h0;
defparam sp_lo_3.INIT_RAM_12 = 256'h0;
defparam sp_lo_3.INIT_RAM_13 = 256'h0;
defparam sp_lo_3.INIT_RAM_14 = 256'h0;
defparam sp_lo_3.INIT_RAM_15 = 256'h0;
defparam sp_lo_3.INIT_RAM_16 = 256'h0;
defparam sp_lo_3.INIT_RAM_17 = 256'h0;
defparam sp_lo_3.INIT_RAM_18 = 256'h0;
defparam sp_lo_3.INIT_RAM_19 = 256'h0;
defparam sp_lo_3.INIT_RAM_1A = 256'h0;
defparam sp_lo_3.INIT_RAM_1B = 256'h0;
defparam sp_lo_3.INIT_RAM_1C = 256'h0;
defparam sp_lo_3.INIT_RAM_1D = 256'h0;
defparam sp_lo_3.INIT_RAM_1E = 256'h0;
defparam sp_lo_3.INIT_RAM_1F = 256'h0;
defparam sp_lo_3.INIT_RAM_20 = 256'h0;
defparam sp_lo_3.INIT_RAM_21 = 256'h0;
defparam sp_lo_3.INIT_RAM_22 = 256'h0;
defparam sp_lo_3.INIT_RAM_23 = 256'h0;
defparam sp_lo_3.INIT_RAM_24 = 256'h0;
defparam sp_lo_3.INIT_RAM_25 = 256'h0;
defparam sp_lo_3.INIT_RAM_26 = 256'h0;
defparam sp_lo_3.INIT_RAM_27 = 256'h0;
defparam sp_lo_3.INIT_RAM_28 = 256'h0;
defparam sp_lo_3.INIT_RAM_29 = 256'h0;
defparam sp_lo_3.INIT_RAM_2A = 256'h0;
defparam sp_lo_3.INIT_RAM_2B = 256'h0;
defparam sp_lo_3.INIT_RAM_2C = 256'h0;
defparam sp_lo_3.INIT_RAM_2D = 256'h0;
defparam sp_lo_3.INIT_RAM_2E = 256'h0;
defparam sp_lo_3.INIT_RAM_2F = 256'h0;
defparam sp_lo_3.INIT_RAM_30 = 256'h0;
defparam sp_lo_3.INIT_RAM_31 = 256'h0;
defparam sp_lo_3.INIT_RAM_32 = 256'h0;
defparam sp_lo_3.INIT_RAM_33 = 256'h0;
defparam sp_lo_3.INIT_RAM_34 = 256'h0;
defparam sp_lo_3.INIT_RAM_35 = 256'h0;
defparam sp_lo_3.INIT_RAM_36 = 256'h0;
defparam sp_lo_3.INIT_RAM_37 = 256'h0;
defparam sp_lo_3.INIT_RAM_38 = 256'h0;
defparam sp_lo_3.INIT_RAM_39 = 256'h0;
defparam sp_lo_3.INIT_RAM_3A = 256'h0;
defparam sp_lo_3.INIT_RAM_3B = 256'h0;
defparam sp_lo_3.INIT_RAM_3C = 256'h0;
defparam sp_lo_3.INIT_RAM_3D = 256'h0;
defparam sp_lo_3.INIT_RAM_3E = 256'h0;
defparam sp_lo_3.INIT_RAM_3F = 256'h0;

assign rd_data = {rd_data_hi, rd_data_lo};

`endif

endmodule
