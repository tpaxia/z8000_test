// Test ROM for Z8000 - reset vector and HALT
// Combinational output for proper timing

module test_rom (
    input         clk,
    input  [9:0]  addr,      // Word address
    output reg [15:0] data
);

always @(*) begin
    case (addr)
        10'h000: data = 16'h0000;  // 0x0000 - unused
        10'h001: data = 16'h4000;  // 0x0002 - FCW (System mode)
        10'h002: data = 16'h0040;  // 0x0004 - PC
        10'h020: data = 16'h7A00;  // 0x0040 - HALT
        default: data = 16'h8D00;  // NOP
    endcase
end

endmodule
