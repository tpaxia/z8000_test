#!/usr/bin/env python3
"""Generate Gowin BRAM initialization values from assembled bootstrap binary"""

import sys

def load_binary(filename):
    """Load binary file into memory arrays"""
    with open(filename, 'rb') as f:
        data = f.read()

    # Create word array (16-bit big-endian)
    words = []
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            words.append((data[i] << 8) | data[i + 1])
        else:
            words.append(data[i] << 8)

    return words

def words_to_bytes(words):
    """Split words into high byte and low byte arrays"""
    mem_hi = []
    mem_lo = []
    for w in words:
        mem_hi.append((w >> 8) & 0xFF)
        mem_lo.append(w & 0xFF)
    return mem_hi, mem_lo

def format_init_ram(mem, start_addr, max_addr):
    """Generate INIT_RAM value for 32 bytes starting at start_addr"""
    # INIT_RAM format: 256'h<byte31><byte30>...<byte1><byte0>
    # where byte0 is at start_addr
    bytes_hex = ""
    for i in range(31, -1, -1):
        addr = start_addr + i
        if addr < len(mem) and addr <= max_addr:
            bytes_hex += f"{mem[addr]:02X}"
        else:
            bytes_hex += "00"
    return f"256'h{bytes_hex}"

def main():
    if len(sys.argv) < 2:
        print("Usage: gen_bram_init.py <bootstrap.bin>")
        sys.exit(1)

    words = load_binary(sys.argv[1])
    mem_hi, mem_lo = words_to_bytes(words)

    # Pad to at least 512 words (1KB) to cover all code
    while len(mem_hi) < 512:
        mem_hi.append(0)
        mem_lo.append(0)

    max_addr = len(mem_hi) - 1

    print("// Generated from bootstrap.bin")
    print("// High byte BRAM init (bram_hi)")
    for i in range(32):  # INIT_RAM_00 to INIT_RAM_1F
        val = format_init_ram(mem_hi, i * 32, max_addr)
        if val != "256'h" + "00" * 32:  # Only print non-zero
            print(f"    .INIT_RAM_{i:02X}({val}),")
        else:
            print(f"    .INIT_RAM_{i:02X}(256'h0),")

    print("\n// Low byte BRAM init (bram_lo)")
    for i in range(32):
        val = format_init_ram(mem_lo, i * 32, max_addr)
        if val != "256'h" + "00" * 32:
            print(f"    .INIT_RAM_{i:02X}({val}),")
        else:
            print(f"    .INIT_RAM_{i:02X}(256'h0),")

if __name__ == "__main__":
    main()
