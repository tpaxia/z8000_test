# Z8000 Test Harness Makefile
# Target: Tang Nano 20K

# Paths
SRC_DIR = src
TV80_DIR = tv80_official/rtl/core
Z8K_RTL_DIR = z8000_micro/rtl

# TV80 Z80 core sources
TV80_SRCS = \
	$(TV80_DIR)/tv80_alu.v \
	$(TV80_DIR)/tv80_mcode.v \
	$(TV80_DIR)/tv80_reg.v \
	$(TV80_DIR)/tv80_core.v \
	$(TV80_DIR)/tv80s.v

# Z80 harness sources
Z80_HARNESS_SRCS = \
	$(SRC_DIR)/z80_harness.v \
	$(SRC_DIR)/z8000_test_harness_top.v \
	$(SRC_DIR)/z8000_bus_fpga.v \
	$(SRC_DIR)/uart_tx.v \
	$(SRC_DIR)/uart_rx.v \
	$(SRC_DIR)/ram16.v \
	$(SRC_DIR)/trace_buffer.v \
	$(SRC_DIR)/z8k_io_ports.v

# Z8000 sources
Z8K_SRCS = \
	$(Z8K_RTL_DIR)/z8000_cpu.v \
	$(Z8K_RTL_DIR)/microcode_rom.v \
	$(Z8K_RTL_DIR)/decode_rom.v

# Include paths
VERILOG_INCS = -I$(Z8K_RTL_DIR) -I$(TV80_DIR)

# Firmware
Z88DK ?= C:/Program Files (x86)/z88dk
Z80ASM = "$(Z88DK)/bin/z88dk-z80asm"
Z80_FW_SRC = $(SRC_DIR)/z80_fw.asm
Z80_FW_BIN = $(SRC_DIR)/z80_fw.bin
Z80_FW_HEX = $(SRC_DIR)/z80_fw.hex
BOOTSTRAP_BODY_INC = $(SRC_DIR)/bootstrap_body.inc
BOOTSTRAP_BIN = $(SRC_DIR)/bootstrap.bin

# Default target
.PHONY: all
all: help

.PHONY: help
help:
	@echo "Z8000 Instruction Test Harness"
	@echo ""
	@echo "Firmware:"
	@echo "  firmware   - Assemble Z80 firmware (z80_fw.asm -> z80_fw.bin/hex)"
	@echo "  fw-verilog - Print Verilog RAM init code (for manual inclusion)"
	@echo ""
	@echo "Simulation:"
	@echo "  sim        - Run Z80 harness simulation (6 command tests)"
	@echo "  sim-full   - Run full system simulation with Z8000 CPU"
	@echo "  wave       - Open waveform viewer (gtkwave)"
	@echo ""
	@echo "Build:"
	@echo "  clean      - Remove all generated files"
	@echo ""
	@echo "FPGA (requires Gowin IDE):"
	@echo "  synth      - Show project file info"
	@echo ""
	@echo "Project files:"
	@echo "  z8000_test_harness.gprj - Z80-based harness"

#
# Z80 Firmware
#
.PHONY: firmware
firmware: $(Z80_FW_BIN) $(Z80_FW_HEX)

$(Z80_FW_BIN): $(Z80_FW_SRC) $(BOOTSTRAP_BODY_INC)
	@echo "Assembling Z80 firmware..."
	cd $(SRC_DIR) && $(Z80ASM) -b -o=z80_fw.bin z80_fw.asm
	@echo "Firmware size: $$(wc -c < $(Z80_FW_BIN)) bytes"

$(Z80_FW_HEX): $(Z80_FW_BIN)
	@echo "Generating hex file for RAM init..."
	python3 scripts/gen_fw_hex.py $(Z80_FW_BIN) $(Z80_FW_HEX)

# Generate Verilog RAM initialization (for manual inclusion)
.PHONY: fw-verilog
fw-verilog: $(Z80_FW_BIN)
	@echo "Verilog RAM initialization:"
	@echo ""
	@python3 -c " \
with open('$(Z80_FW_BIN)', 'rb') as f: \
    data = f.read(); \
print('// Z80 firmware - %d bytes' % len(data)); \
print('// Auto-generated from z80_fw.asm'); \
for i in range(0, len(data), 8): \
    chunk = data[i:i+8]; \
    line = '    '; \
    for j, b in enumerate(chunk): \
        line += 'ram[%d]=8\\'h%02x; ' % (i+j, b); \
    print(line.rstrip()); \
"

#
# Z80 Harness Simulation (without Z8000 - tests harness only)
#
.PHONY: sim
sim: firmware $(SRC_DIR)/z8000_test_harness_tb.v $(SRC_DIR)/z80_harness.v $(TV80_SRCS)
	cp $(Z80_FW_HEX) z80_fw.hex
	iverilog -g2012 -DSIMULATION $(VERILOG_INCS) -o z8000_test_harness_tb.vvp \
		$(SRC_DIR)/z8000_test_harness_tb.v \
		$(SRC_DIR)/z80_harness.v \
		$(SRC_DIR)/uart_tx.v \
		$(SRC_DIR)/uart_rx.v \
		$(TV80_SRCS)
	vvp z8000_test_harness_tb.vvp

# Full system simulation with Z8000 (direct BRAM test, no UART)
.PHONY: sim-full
sim-full: $(SRC_DIR)/z8000_full_tb.v $(Z8K_SRCS)
	iverilog -g2012 -DSIMULATION $(VERILOG_INCS) -o z8000_full_tb.vvp \
		$(SRC_DIR)/z8000_full_tb.v \
		$(SRC_DIR)/ram16.v \
		$(Z8K_SRCS)
	vvp z8000_full_tb.vvp


#
# Waveform Viewer
#
.PHONY: wave
wave:
	@if [ -f z8000_harness.vcd ]; then \
		gtkwave z8000_harness.vcd &; \
	elif [ -f test_harness.vcd ]; then \
		gtkwave test_harness.vcd &; \
	else \
		echo "No VCD file found. Run 'make sim' first."; \
	fi

#
# Bootstrap (Z8000 test code)
#
.PHONY: bootstrap
bootstrap: $(SRC_DIR)/bootstrap.bin $(BOOTSTRAP_INC)

$(SRC_DIR)/bootstrap.bin: $(SRC_DIR)/bootstrap.s
	cd $(SRC_DIR) && z8k-coff-as -z8002 -als bootstrap.s -o bootstrap.o > bootstrap.lst
	cd $(SRC_DIR) && z8k-coff-ld -Ttext 0x0000 bootstrap.o -o bootstrap.elf
	cd $(SRC_DIR) && z8k-coff-objcopy -O binary bootstrap.elf bootstrap.bin
	@echo "Bootstrap binary generated: $(SRC_DIR)/bootstrap.bin"
	@echo "Listing file: $(SRC_DIR)/bootstrap.lst"

$(BOOTSTRAP_BODY_INC): $(BOOTSTRAP_BIN)
	python3 scripts/gen_bootstrap_inc.py $(BOOTSTRAP_BIN) $(BOOTSTRAP_BODY_INC) --skip 8

#
# Clean
#
.PHONY: clean
clean:
	rm -f *.vvp *.vcd z80_fw.hex
	rm -f $(SRC_DIR)/z80_fw.bin $(SRC_DIR)/z80_fw.hex
	rm -f $(SRC_DIR)/bootstrap.bin $(SRC_DIR)/bootstrap.o $(SRC_DIR)/bootstrap.elf
	rm -f $(SRC_DIR)/bootstrap.lst $(SRC_DIR)/bootstrap_body.inc
	rm -f $(SRC_DIR)/*.vvp $(SRC_DIR)/*.vcd
	rm -rf impl

#
# FPGA synthesis (requires Gowin IDE)
#
.PHONY: synth
synth:
	@echo "Open Gowin IDE with project file:"
	@echo "  z8000_test_harness.gprj"
