//============================================================================
// Bootstrap master store (Z80-only) - shared by all test harnesses
//
// Holds the pristine bootstrap image uploaded once by the Z80 harness. The
// Z8001 CPU bus is never connected here, so it is physically read-only to the
// CPU: no test (however buggy) can corrupt it. The Z80 INIT routine copies
// this master into the active CPU RAM (0x0000) before every test, so each test
// starts from a clean bootstrap.
//
// Selected on the harness side by z80_addr[13] (the 0x2000 line), which the
// CPU's Port B never drives. The existing harness/firmware shadow addresses
// (0x3000 image, 0x3FFE word count) land here unchanged.
//
// 2048 x 16 (4KB), word-granular writes (the harness uploads whole words).
// 1-cycle registered read latency to match ram16_altera Port A.
//============================================================================

module boot_master (
    input             clk,
    input             we,        // z8k_mem_we & master-select
    input      [10:0] waddr,     // z80_addr[11:1]  (2048 words)
    input      [15:0] din,
    output reg [15:0] dout
);

    reg [15:0] mem [0:2047];

    always @(posedge clk) begin
        if (we) mem[waddr] <= din;
        dout <= mem[waddr];
    end

endmodule
