//============================================================================
// Dual-Port RAM for Altera/Intel FPGAs
//
// Same interface as ram16.v from the Gowin project.
// Uses altsyncram megafunction to implement true dual-port RAM.
//
// Port A: Z80 harness (load/read test code)
// Port B: Z8001 CPU (fetch/execute)
//
// 8K bytes (4K words) with byte write enables.
// Receives BYTE addresses, converts to word address internally.
//============================================================================

module ram16_altera (
    // Port A (Z80 harness)
    input         clka,
    input         wea_hi,      // Write enable high byte
    input         wea_lo,      // Write enable low byte
    input  [12:0] addra,       // 13-bit BYTE address
    input  [15:0] dina,
    output [15:0] douta,
    // Port B (Z8001 CPU)
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
    //------------------------------------------------------------------------
    // Simulation - Behavioral dual-port model
    //------------------------------------------------------------------------
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
    //------------------------------------------------------------------------
    // Synthesis - MegaWizard-generated dual-port RAM (two 4Kx8 instances)
    //------------------------------------------------------------------------
    wire [7:0] douta_hi, douta_lo;
    wire [7:0] doutb_hi, doutb_lo;

    // High byte RAM (MegaWizard-generated)
    ram_hi ram_hi_inst (
        .clock      (clka),
        .address_a  (addra_w),
        .data_a     (dina[15:8]),
        .wren_a     (wea_hi),
        .q_a        (douta_hi),
        .address_b  (addrb_w),
        .data_b     (dinb[15:8]),
        .wren_b     (web_hi),
        .q_b        (doutb_hi)
    );

    // Low byte RAM (MegaWizard-generated)
    ram_lo ram_lo_inst (
        .clock      (clka),
        .address_a  (addra_w),
        .data_a     (dina[7:0]),
        .wren_a     (wea_lo),
        .q_a        (douta_lo),
        .address_b  (addrb_w),
        .data_b     (dinb[7:0]),
        .wren_b     (web_lo),
        .q_b        (doutb_lo)
    );

    assign douta = {douta_hi, douta_lo};
    assign doutb = {doutb_hi, doutb_lo};
`endif

endmodule
