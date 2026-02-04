// Behavioral 16-bit RAM for simulation
// 8K bytes (4K words) with byte write enables
// Receives BYTE address, converts to word address internally
//
// For synthesis, use the vendor-specific version:
//   ram16_gowin.v  - Gowin FPGA

module ram16 (
    input         clk,
    input         we_hi,      // Write enable for high byte (D15-D8)
    input         we_lo,      // Write enable for low byte (D7-D0)
    input  [12:0] addr,       // 13-bit BYTE address (8K bytes = 4K words)
    input  [15:0] din,
    output [15:0] dout
);

    // 4K words (8K bytes)
    reg [7:0] mem_hi [0:4095];
    reg [7:0] mem_lo [0:4095];
    reg [7:0] dout_hi, dout_lo;

    // Convert byte address to word address: addr[12:1]
    wire [11:0] word_addr = addr[12:1];

    always @(posedge clk) begin
        if (we_hi)
            mem_hi[word_addr] <= din[15:8];
        dout_hi <= mem_hi[word_addr];
    end

    always @(posedge clk) begin
        if (we_lo)
            mem_lo[word_addr] <= din[7:0];
        dout_lo <= mem_lo[word_addr];
    end

    assign dout = {dout_hi, dout_lo};

endmodule
