# Makefile for Z8001 External Test Harness (Quartus)
#
# Targets:
#   make firmware  - Build Z80 firmware and generate MIF file
#   make clean     - Clean generated files

# Tools
Z80ASM = z80asm
PYTHON = python3

# Paths
SRC_DIR = ../src
SCRIPTS_DIR = ../scripts

# Files
Z80_FW_ASM = $(SRC_DIR)/z80_fw.asm
Z80_FW_BIN = z80_fw.bin
Z80_FW_HEX = z80_fw.hex
Z80_FW_MIF = z80_fw.mif

.PHONY: all firmware clean

all: firmware

# Build Z80 firmware and generate MIF
firmware: $(Z80_FW_MIF)

$(Z80_FW_MIF): $(Z80_FW_HEX)
	$(PYTHON) gen_mif.py $(Z80_FW_HEX) $(Z80_FW_MIF) 8192 8

$(Z80_FW_HEX): $(Z80_FW_BIN)
	$(PYTHON) $(SCRIPTS_DIR)/gen_fw_hex.py $(Z80_FW_BIN) $(Z80_FW_HEX)

$(Z80_FW_BIN): $(Z80_FW_ASM)
	$(Z80ASM) -b -o $(Z80_FW_BIN) $(Z80_FW_ASM)

# Alternative: copy hex from main project if already built
copy-hex:
	@if exist $(SRC_DIR)\z80_fw.hex copy $(SRC_DIR)\z80_fw.hex $(Z80_FW_HEX)
	$(PYTHON) gen_mif.py $(Z80_FW_HEX) $(Z80_FW_MIF) 8192 8

clean:
	-del /Q $(Z80_FW_BIN) $(Z80_FW_HEX) $(Z80_FW_MIF) 2>nul

# Help
help:
	@echo Targets:
	@echo   make firmware  - Build Z80 firmware and generate MIF file
	@echo   make copy-hex  - Copy hex from main project and generate MIF
	@echo   make clean     - Clean generated files
