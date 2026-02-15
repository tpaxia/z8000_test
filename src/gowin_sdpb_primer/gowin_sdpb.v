//Copyright (C)2014-2025 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: IP file
//Tool Version: V1.9.11.03 Education
//Part Number: GW2A-LV18PG256C8/I7
//Device: GW2A-18
//Device Version: C
//Created Time: Sun Feb 15 09:50:10 2026

module Gowin_SDPB (dout, clka, cea, reseta, clkb, ceb, resetb, oce, ada, din, adb);

output [35:0] dout;
input clka;
input cea;
input reseta;
input clkb;
input ceb;
input resetb;
input oce;
input [9:0] ada;
input [35:0] din;
input [9:0] adb;

wire [17:0] sdpx9b_inst_0_dout_w;
wire [17:0] sdpx9b_inst_1_dout_w;
wire gw_vcc;
wire gw_gnd;

assign gw_vcc = 1'b1;
assign gw_gnd = 1'b0;

SDPX9B sdpx9b_inst_0 (
    .DO({sdpx9b_inst_0_dout_w[17:0],dout[17:0]}),
    .CLKA(clka),
    .CEA(cea),
    .RESETA(reseta),
    .CLKB(clkb),
    .CEB(ceb),
    .RESETB(resetb),
    .OCE(oce),
    .BLKSELA({gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELB({gw_gnd,gw_gnd,gw_gnd}),
    .ADA({ada[9:0],gw_gnd,gw_gnd,gw_vcc,gw_vcc}),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[17:0]}),
    .ADB({adb[9:0],gw_gnd,gw_gnd,gw_gnd,gw_gnd})
);

defparam sdpx9b_inst_0.READ_MODE = 1'b1;
defparam sdpx9b_inst_0.BIT_WIDTH_0 = 18;
defparam sdpx9b_inst_0.BIT_WIDTH_1 = 18;
defparam sdpx9b_inst_0.BLK_SEL_0 = 3'b000;
defparam sdpx9b_inst_0.BLK_SEL_1 = 3'b000;
defparam sdpx9b_inst_0.RESET_MODE = "SYNC";

SDPX9B sdpx9b_inst_1 (
    .DO({sdpx9b_inst_1_dout_w[17:0],dout[35:18]}),
    .CLKA(clka),
    .CEA(cea),
    .RESETA(reseta),
    .CLKB(clkb),
    .CEB(ceb),
    .RESETB(resetb),
    .OCE(oce),
    .BLKSELA({gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELB({gw_gnd,gw_gnd,gw_gnd}),
    .ADA({ada[9:0],gw_gnd,gw_gnd,gw_vcc,gw_vcc}),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[35:18]}),
    .ADB({adb[9:0],gw_gnd,gw_gnd,gw_gnd,gw_gnd})
);

defparam sdpx9b_inst_1.READ_MODE = 1'b1;
defparam sdpx9b_inst_1.BIT_WIDTH_0 = 18;
defparam sdpx9b_inst_1.BIT_WIDTH_1 = 18;
defparam sdpx9b_inst_1.BLK_SEL_0 = 3'b000;
defparam sdpx9b_inst_1.BLK_SEL_1 = 3'b000;
defparam sdpx9b_inst_1.RESET_MODE = "SYNC";

endmodule //Gowin_SDPB
