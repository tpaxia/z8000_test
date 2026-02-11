# Timing Constraints for Z8001 External Test Harness

# Input clock (50 MHz oscillator)
create_clock -name clk_50mhz -period 20.000 [get_ports clk_50mhz]

# PLL-generated clocks (will be auto-derived by Quartus)
# clk_16mhz: 16 MHz system clock
# clk_4mhz:  4 MHz Z8001 CPU clock

# Z8001 CPU clock output (directly driven accent accent)
create_generated_clock -name z8k_clk -source [get_pins {pll_inst|*}] -divide_by 4 [get_ports z8k_clk]

# External Z8001 interface timing
# AS_n and DS_n are inputs from the CPU
set_input_delay -clock z8k_clk -max 15.0 [get_ports {z8k_as_n z8k_ds_n z8k_mreq_n z8k_rw_n z8k_bw_n}]
set_input_delay -clock z8k_clk -min 5.0 [get_ports {z8k_as_n z8k_ds_n z8k_mreq_n z8k_rw_n z8k_bw_n}]

# Status and segment inputs
set_input_delay -clock z8k_clk -max 15.0 [get_ports {z8k_st[*] z8k_sn[*]}]
set_input_delay -clock z8k_clk -min 5.0 [get_ports {z8k_st[*] z8k_sn[*]}]

# Bidirectional AD bus
set_input_delay -clock z8k_clk -max 20.0 [get_ports {z8k_ad[*]}]
set_input_delay -clock z8k_clk -min 5.0 [get_ports {z8k_ad[*]}]
set_output_delay -clock z8k_clk -max 10.0 [get_ports {z8k_ad[*]}]
set_output_delay -clock z8k_clk -min 2.0 [get_ports {z8k_ad[*]}]

# Bus buffer control
set_output_delay -clock z8k_clk -max 5.0 [get_ports {bus_buf_oe_n bus_buf_dir}]
set_output_delay -clock z8k_clk -min 1.0 [get_ports {bus_buf_oe_n bus_buf_dir}]

# UART is asynchronous - false path
set_false_path -from [get_ports uart_rx]
set_false_path -to [get_ports uart_tx]

# Reset is asynchronous
set_false_path -from [get_ports rst_n]

# LEDs are slow - false path
set_false_path -to [get_ports {led[*]}]
