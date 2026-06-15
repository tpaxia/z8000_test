// True Dual-Port 16-bit RAM using Gowin DPB IP
// Port A: Z80 harness access (load/read test code)
// Port B: Z8000 CPU access (fetch/execute)
// Both ports can read and write independently.
//
// 32K bytes (16K words) with byte write enables.
// Uses 8x Gowin_DPB (4 banks x high/low byte, each 4Kx8).

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
                // Port A
                .clka   (clka),
                .ocea   (1'b1),
                .cea    (1'b1),
                .reseta (1'b0),
                .wrea   (wea_hi && bank_a == i[1:0]),
                .ada    (word_a),
                .dina   (dina[15:8]),
                .douta  (douta_hi[i*8 +: 8]),
                // Port B
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
                // Port A
                .clka   (clka),
                .ocea   (1'b1),
                .cea    (1'b1),
                .reseta (1'b0),
                .wrea   (wea_lo && bank_a == i[1:0]),
                .ada    (word_a),
                .dina   (dina[7:0]),
                .douta  (douta_lo[i*8 +: 8]),
                // Port B
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

endmodule
