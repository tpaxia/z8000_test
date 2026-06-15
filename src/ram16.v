// True Dual-Port 16-bit RAM
// Port A: Z80 harness access (load/read test code)
// Port B: Z8000 CPU access (fetch/execute)
// Both ports can read and write independently - no muxing needed.
//
// 32K bytes (16K words) with byte write enables.
// Receives BYTE addresses, converts to word address internally.
//
// Simulation: behavioral dual-port model
// Synthesis:  Gowin_DPB (4Kx8 true dual-port BRAM) x8

module ram16 (
    // Port A (Z80 harness)
    input         clka,
    input         wea_hi,      // Write enable high byte
    input         wea_lo,      // Write enable low byte
    input  [14:0] addra,       // 15-bit BYTE address
    input  [15:0] dina,
    output [15:0] douta,
    // Port B (Z8000 CPU)
    input         clkb,
    input         web_hi,      // Write enable high byte
    input         web_lo,      // Write enable low byte
    input  [14:0] addrb,       // 15-bit BYTE address
    input  [15:0] dinb,
    output [15:0] doutb
);

    // Word addresses (14-bit, 16K words)
    wire [13:0] addra_w = addra[14:1];
    wire [13:0] addrb_w = addrb[14:1];

`ifdef SIMULATION
    // Behavioral dual-port model
    reg [7:0] mem_hi [0:16383];
    reg [7:0] mem_lo [0:16383];

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

    // Memory starts zeroed; bootstrap is loaded at runtime by Z80 INIT command.
    // For sim-full, the testbench writes needed data directly.

`else
    wire [1:0] bank_a = addra[14:13];
    wire [1:0] bank_b = addrb[14:13];
    wire [11:0] word_a = addra[12:1];
    wire [11:0] word_b = addrb[12:1];

    reg [1:0] bank_a_q;
    reg [1:0] bank_b_q;
    always @(posedge clka) bank_a_q <= bank_a;
    always @(posedge clkb) bank_b_q <= bank_b;

    wire [31:0] douta_hi;
    wire [31:0] douta_lo;
    wire [31:0] doutb_hi;
    wire [31:0] doutb_lo;

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : ram_bank
            Gowin_DPB ram_hi (
                .clka   (clka),
                .ocea   (1'b1),
                .cea    (1'b1),
                .reseta (1'b0),
                .wrea   (wea_hi && bank_a == i[1:0]),
                .ada    (word_a),
                .dina   (dina[15:8]),
                .douta  (douta_hi[i*8 +: 8]),
                .clkb   (clkb),
                .oceb   (1'b1),
                .ceb    (1'b1),
                .resetb (1'b0),
                .wreb   (web_hi && bank_b == i[1:0]),
                .adb    (word_b),
                .dinb   (dinb[15:8]),
                .doutb  (doutb_hi[i*8 +: 8])
            );

            Gowin_DPB ram_lo (
                .clka   (clka),
                .ocea   (1'b1),
                .cea    (1'b1),
                .reseta (1'b0),
                .wrea   (wea_lo && bank_a == i[1:0]),
                .ada    (word_a),
                .dina   (dina[7:0]),
                .douta  (douta_lo[i*8 +: 8]),
                .clkb   (clkb),
                .oceb   (1'b1),
                .ceb    (1'b1),
                .resetb (1'b0),
                .wreb   (web_lo && bank_b == i[1:0]),
                .adb    (word_b),
                .dinb   (dinb[7:0]),
                .doutb  (doutb_lo[i*8 +: 8])
            );
        end
    endgenerate

    function [7:0] bank_mux;
        input [31:0] data;
        input [1:0] bank;
        begin
            case (bank)
                2'd0: bank_mux = data[7:0];
                2'd1: bank_mux = data[15:8];
                2'd2: bank_mux = data[23:16];
                default: bank_mux = data[31:24];
            endcase
        end
    endfunction

    assign douta = {bank_mux(douta_hi, bank_a_q), bank_mux(douta_lo, bank_a_q)};
    assign doutb = {bank_mux(doutb_hi, bank_b_q), bank_mux(doutb_lo, bank_b_q)};

`endif

endmodule
