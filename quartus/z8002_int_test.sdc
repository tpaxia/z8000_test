# Timing Constraints for Z8002 Internal Test Harness

# Input clock (50 MHz oscillator)
create_clock -name clk_50mhz -period 20.000 [get_ports clk]

# PLL-generated clocks (auto-derived by Quartus from ALTPLL)
# clk_16mhz: 16 MHz system clock (c0)
# clk_4mhz:  4 MHz external clock only (c1) - not used for internal CPU
derive_pll_clocks
derive_clock_uncertainty

# Derived 4MHz CPU clock (register divider from 16MHz)
create_generated_clock -name z8k_cpu_clk \
    -source [get_pins {pll_inst|pll_inst|auto_generated|pll1|clk[0]}] \
    -divide_by 4 \
    [get_registers {z8k_cpu_clk}]

# UART is asynchronous - false path
set_false_path -from [get_ports urxd1]
set_false_path -to [get_ports utxd1]

# Reset is asynchronous
set_false_path -from [get_ports n_reset]

# LED is slow - false path
set_false_path -to [get_ports driveLED]

# External Z8001 pins - all false paths (CPU in reset, buffers disabled)
set_false_path -to [get_ports {freset fclk fbreq fwait fnvi fvi fnmi}]
set_false_path -to [get_ports {fbuscs fbusrd}]
set_false_path -to [get_ports {n_sRamCS0 n_sRamCS1 n_sRamOE n_sRamWE}]
set_false_path -from [get_ports {fas fds fbw fmreq frw}]
set_false_path -from [get_ports {fst[*] fsn[*] sramData[*]}]
