//============================================================================
// PLL Wrapper for Altera Cyclone IV
//
// Input:  50 MHz oscillator
// Output: 16 MHz system clock (c0)
//         4 MHz CPU clock (c1)
//
// Note: This is a placeholder. For actual synthesis, use Quartus MegaWizard
// to generate the ALTPLL megafunction with proper timing constraints.
// Replace this file with the generated pll.v from MegaWizard.
//============================================================================

module pll (
    input  wire inclk0,     // 50 MHz input
    output wire c0,         // 16 MHz output
    output wire c1,         // 4 MHz output
    output wire locked      // PLL locked indicator
);

`ifdef SIMULATION
    //------------------------------------------------------------------------
    // Simulation Model - Simple clock dividers
    //------------------------------------------------------------------------
    reg r_c0 = 0;
    reg r_c1 = 0;
    reg r_locked = 0;
    reg [7:0] lock_cnt = 0;

    // 50 MHz -> 16 MHz (divide by 3.125, approximate with toggle)
    // For simulation, just use simple dividers
    reg [1:0] div_c0 = 0;
    always @(posedge inclk0) begin
        if (div_c0 == 2'd2) begin
            div_c0 <= 0;
            r_c0 <= ~r_c0;
        end else begin
            div_c0 <= div_c0 + 1;
        end
    end

    // 16 MHz -> 4 MHz (divide by 4)
    reg [1:0] div_c1 = 0;
    always @(posedge r_c0) begin
        if (div_c1 == 2'd1) begin
            div_c1 <= 0;
            r_c1 <= ~r_c1;
        end else begin
            div_c1 <= div_c1 + 1;
        end
    end

    // Lock after some cycles
    always @(posedge inclk0) begin
        if (lock_cnt < 8'd255)
            lock_cnt <= lock_cnt + 1;
        r_locked <= (lock_cnt == 8'd255);
    end

    assign c0 = r_c0;
    assign c1 = r_c1;
    assign locked = r_locked;

`else
    //------------------------------------------------------------------------
    // Synthesis - Use ALTPLL megafunction
    //------------------------------------------------------------------------
    // Replace this with MegaWizard-generated ALTPLL instantiation
    // Example configuration:
    //   inclk0 = 50 MHz
    //   c0 = 16 MHz (multiply by 8, divide by 25)
    //   c1 = 4 MHz (multiply by 2, divide by 25)

    altpll #(
        .bandwidth_type("AUTO"),
        .clk0_divide_by(25),
        .clk0_duty_cycle(50),
        .clk0_multiply_by(8),
        .clk0_phase_shift("0"),
        .clk1_divide_by(25),
        .clk1_duty_cycle(50),
        .clk1_multiply_by(2),
        .clk1_phase_shift("0"),
        .compensate_clock("CLK0"),
        .inclk0_input_frequency(20000),  // 50 MHz = 20000 ps period
        .intended_device_family("Cyclone IV E"),
        .operation_mode("NORMAL"),
        .pll_type("AUTO"),
        .port_activeclock("PORT_UNUSED"),
        .port_areset("PORT_UNUSED"),
        .port_clkbad0("PORT_UNUSED"),
        .port_clkbad1("PORT_UNUSED"),
        .port_clkloss("PORT_UNUSED"),
        .port_clkswitch("PORT_UNUSED"),
        .port_configupdate("PORT_UNUSED"),
        .port_fbin("PORT_UNUSED"),
        .port_inclk0("PORT_USED"),
        .port_inclk1("PORT_UNUSED"),
        .port_locked("PORT_USED"),
        .port_pfdena("PORT_UNUSED"),
        .port_phasecounterselect("PORT_UNUSED"),
        .port_phasedone("PORT_UNUSED"),
        .port_phasestep("PORT_UNUSED"),
        .port_phaseupdown("PORT_UNUSED"),
        .port_pllena("PORT_UNUSED"),
        .port_scanaclr("PORT_UNUSED"),
        .port_scanclk("PORT_UNUSED"),
        .port_scanclkena("PORT_UNUSED"),
        .port_scandata("PORT_UNUSED"),
        .port_scandataout("PORT_UNUSED"),
        .port_scandone("PORT_UNUSED"),
        .port_scanread("PORT_UNUSED"),
        .port_scanwrite("PORT_UNUSED"),
        .port_clk0("PORT_USED"),
        .port_clk1("PORT_USED"),
        .port_clk2("PORT_UNUSED"),
        .port_clk3("PORT_UNUSED"),
        .port_clk4("PORT_UNUSED"),
        .port_clk5("PORT_UNUSED"),
        .self_reset_on_loss_lock("OFF"),
        .width_clock(5)
    ) pll_inst (
        .inclk({1'b0, inclk0}),
        .clk({3'b000, c1, c0}),
        .locked(locked),
        .activeclock(),
        .areset(1'b0),
        .clkbad(),
        .clkena({6{1'b1}}),
        .clkloss(),
        .clkswitch(1'b0),
        .configupdate(1'b0),
        .enable0(),
        .enable1(),
        .extclk(),
        .extclkena({4{1'b1}}),
        .fbin(1'b1),
        .fbmimicbidir(),
        .fbout(),
        .fref(),
        .icdrclk(),
        .pfdena(1'b1),
        .phasecounterselect({4{1'b1}}),
        .phasedone(),
        .phasestep(1'b1),
        .phaseupdown(1'b1),
        .pllena(1'b1),
        .scanaclr(1'b0),
        .scanclk(1'b0),
        .scanclkena(1'b1),
        .scandata(1'b0),
        .scandataout(),
        .scandone(),
        .scanread(1'b0),
        .scanwrite(1'b0),
        .sclkout0(),
        .sclkout1(),
        .vcooverrange(),
        .vcounderrange()
    );
`endif

endmodule
