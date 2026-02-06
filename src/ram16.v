// True Dual-Port 16-bit RAM
// Port A: Z80 harness access (load/read test code)
// Port B: Z8000 CPU access (fetch/execute)
// Both ports can read and write independently - no muxing needed.
//
// 8K bytes (4K words) with byte write enables.
// Receives BYTE addresses, converts to word address internally.
//
// Simulation: behavioral dual-port model
// Synthesis:  Gowin_DPB (4Kx8 true dual-port BRAM) x2

module ram16 (
    // Port A (Z80 harness)
    input         clka,
    input         wea_hi,      // Write enable high byte
    input         wea_lo,      // Write enable low byte
    input  [12:0] addra,       // 13-bit BYTE address
    input  [15:0] dina,
    output [15:0] douta,
    // Port B (Z8000 CPU)
    input         clkb,
    input         web_hi,      // Write enable high byte
    input         web_lo,      // Write enable low byte
    input  [12:0] addrb,       // 13-bit BYTE address
    input  [15:0] dinb,
    output [15:0] doutb
);

    // Word addresses (12-bit, 4K words)
    wire [11:0] addra_w = addra[12:1];
    wire [11:0] addrb_w = addrb[12:1];

`ifdef SIMULATION
    // Behavioral dual-port model
    reg [7:0] mem_hi [0:4095];
    reg [7:0] mem_lo [0:4095];

    // Port A
    reg [7:0] douta_hi, douta_lo;
    always @(posedge clka) begin
        if (wea_hi) mem_hi[addra_w] <= dina[15:8];
        if (wea_lo) mem_lo[addra_w] <= dina[7:0];
        douta_hi <= mem_hi[addra_w];
        douta_lo <= mem_lo[addra_w];
    end
    assign douta = {douta_hi, douta_lo};

    // Port B
    reg [7:0] doutb_hi, doutb_lo;
    always @(posedge clkb) begin
        if (web_hi) mem_hi[addrb_w] <= dinb[15:8];
        if (web_lo) mem_lo[addrb_w] <= dinb[7:0];
        doutb_hi <= mem_hi[addrb_w];
        doutb_lo <= mem_lo[addrb_w];
    end
    assign doutb = {doutb_hi, doutb_lo};

    // Bootstrap initialization
    initial begin
        $readmemh("bram_hi.hex", mem_hi);
        $readmemh("bram_lo.hex", mem_lo);
    end

`else
    // Gowin DPB: two 4Kx8 true dual-port BRAMs (high byte + low byte)
    wire [7:0] douta_hi, douta_lo;
    wire [7:0] doutb_hi, doutb_lo;

    Gowin_DPB ram_hi (
        // Port A
        .clka   (clka),
        .ocea   (1'b1),
        .cea    (1'b1),
        .reseta (1'b0),
        .wrea   (wea_hi),
        .ada    (addra_w),
        .dina   (dina[15:8]),
        .douta  (douta_hi),
        // Port B
        .clkb   (clkb),
        .oceb   (1'b1),
        .ceb    (1'b1),
        .resetb (1'b0),
        .wreb   (web_hi),
        .adb    (addrb_w),
        .dinb   (dinb[15:8]),
        .doutb  (doutb_hi)
    );

    Gowin_DPB ram_lo (
        // Port A
        .clka   (clka),
        .ocea   (1'b1),
        .cea    (1'b1),
        .reseta (1'b0),
        .wrea   (wea_lo),
        .ada    (addra_w),
        .dina   (dina[7:0]),
        .douta  (douta_lo),
        // Port B
        .clkb   (clkb),
        .oceb   (1'b1),
        .ceb    (1'b1),
        .resetb (1'b0),
        .wreb   (web_lo),
        .adb    (addrb_w),
        .dinb   (dinb[7:0]),
        .doutb  (doutb_lo)
    );

    assign douta = {douta_hi, douta_lo};
    assign doutb = {doutb_hi, doutb_lo};

`endif

endmodule
