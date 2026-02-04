// Gowin 16-bit RAM using Gowin_SP IP
// 8K bytes (4K words) with byte write enables
// Receives BYTE address, converts to word address internally
//
// Matches the working z8000_simple_monitor ram16 implementation

module ram16 (
    input         clk,
    input         we_hi,      // Write enable for high byte (D15-D8)
    input         we_lo,      // Write enable for low byte (D7-D0)
    input  [12:0] addr,       // 13-bit BYTE address (8K bytes = 4K words)
    input  [15:0] din,
    output [15:0] dout
);

    wire [7:0] dout_hi, dout_lo;

    // Convert byte address to word address, pad to 13 bits for Gowin_SP
    // addr[12:1] = word address (12 bits = 4K words)
    Gowin_SP ram_hi (
        .clk    (clk),
        .oce    (1'b1),
        .ce     (1'b1),
        .reset  (1'b0),
        .wre    (we_hi),
        .ad     ({1'b0, addr[12:1]}),  // Word address, padded to 13 bits
        .din    (din[15:8]),
        .dout   (dout_hi)
    );

    Gowin_SP ram_lo (
        .clk    (clk),
        .oce    (1'b1),
        .ce     (1'b1),
        .reset  (1'b0),
        .wre    (we_lo),
        .ad     ({1'b0, addr[12:1]}),  // Word address, padded to 13 bits
        .din    (din[7:0]),
        .dout   (dout_lo)
    );

    assign dout = {dout_hi, dout_lo};

endmodule
