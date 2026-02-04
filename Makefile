# Z8000 Test Harness Makefile
# Target: Tang Nano 20K

# Paths
Z8K_MICRO = ../z8000_micro
SRC_DIR = src

# Verilog sources
VERILOG_SRCS = \
	$(SRC_DIR)/test_harness_top.v \
	$(SRC_DIR)/test_harness_ctrl.v \
	$(SRC_DIR)/uart_tx.v \
	$(SRC_DIR)/uart_rx.v \
	$(Z8K_MICRO)/z8000_cpu.v \
	$(Z8K_MICRO)/uasm/output/microcode_rom.v \
	$(Z8K_MICRO)/uasm/output/decode_rom.v

# Include paths
VERILOG_INCS = -I$(Z8K_MICRO)

# Simulation
SIM_TOP = test_harness_tb
SIM_OUT = test_harness.vcd

# Default target
.PHONY: all
all: help

.PHONY: help
help:
	@echo "Z8000 Instruction Test Harness"
	@echo ""
	@echo "Targets:"
	@echo "  sim      - Run simulation"
	@echo "  wave     - Open waveform viewer"
	@echo "  clean    - Clean build artifacts"
	@echo ""
	@echo "FPGA targets (requires Gowin toolchain):"
	@echo "  synth    - Synthesize design"
	@echo "  impl     - Implement design"
	@echo "  program  - Program FPGA"

# Simulation
.PHONY: sim
sim: $(SRC_DIR)/test_harness_tb.v $(VERILOG_SRCS)
	iverilog -g2012 -DSIMULATION $(VERILOG_INCS) -o test_harness_tb.vvp \
		$(SRC_DIR)/test_harness_tb.v $(VERILOG_SRCS)
	vvp test_harness_tb.vvp

# Open waveform
.PHONY: wave
wave: $(SIM_OUT)
	gtkwave $(SIM_OUT) &

# Build bootstrap binary from assembly
.PHONY: bootstrap
bootstrap: $(SRC_DIR)/bootstrap.bin

$(SRC_DIR)/bootstrap.bin: $(SRC_DIR)/bootstrap.s
	cd $(SRC_DIR) && z8k-coff-as -z8002 bootstrap.s -o bootstrap.o
	cd $(SRC_DIR) && z8k-coff-ld -Ttext 0x0000 bootstrap.o -o bootstrap.elf
	cd $(SRC_DIR) && z8k-coff-objcopy -O binary bootstrap.elf bootstrap.bin
	@echo "Bootstrap binary generated: $(SRC_DIR)/bootstrap.bin"

# Clean
.PHONY: clean
clean:
	rm -f *.vvp *.vcd
	rm -f $(SRC_DIR)/*.o $(SRC_DIR)/*.elf $(SRC_DIR)/*.bin
	rm -rf impl

# Test specific instruction
# Usage: make test INSTR="ADD R1, R2"
.PHONY: test
test:
	@echo "TODO: Interactive test mode"

# FPGA synthesis (requires Gowin IDE)
.PHONY: synth
synth:
	@echo "Run Gowin IDE for synthesis"
	@echo "Project file: instructions.gprj"

.PHONY: impl
impl:
	@echo "Run Gowin IDE for implementation"

.PHONY: program
program:
	@echo "Run Gowin Programmer"
