#!/usr/bin/env python3
"""Generate BRAM initialization files from bootstrap.bin.

Outputs:
  - bram_hi.hex / bram_lo.hex  : $readmemh files for simulation
  - bram_init.vh                : defparam INIT_RAM for Gowin DPB synthesis
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <bootstrap.bin> [output_dir]")
        sys.exit(1)

    bin_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(bin_path)

    with open(bin_path, 'rb') as f:
        data = f.read()

    # Pad to even length
    if len(data) % 2:
        data += b'\x00'

    num_words = len(data) // 2

    # Split into high/low byte arrays (word-addressed)
    hi_bytes = []
    lo_bytes = []
    for i in range(0, len(data), 2):
        hi_bytes.append(data[i])      # Big-endian: first byte = high
        lo_bytes.append(data[i + 1])  # Second byte = low

    # Pad to 4096 words
    while len(hi_bytes) < 4096:
        hi_bytes.append(0)
        lo_bytes.append(0)

    # ---- Generate simulation hex files ----
    # $readmemh format: one hex value per line, word-addressed
    hi_hex_path = os.path.join(out_dir, 'bram_hi.hex')
    lo_hex_path = os.path.join(out_dir, 'bram_lo.hex')

    with open(hi_hex_path, 'w') as f:
        for b in hi_bytes[:num_words]:
            f.write(f'{b:02X}\n')

    with open(lo_hex_path, 'w') as f:
        for b in lo_bytes[:num_words]:
            f.write(f'{b:02X}\n')

    print(f"Simulation: {hi_hex_path} ({num_words} words)")
    print(f"Simulation: {lo_hex_path} ({num_words} words)")

    # ---- Generate Gowin DPB INIT_RAM defparams ----
    # Each Gowin_DPB has two DPB primitives (4-bit each):
    #   dpb_inst_0 = low nibble [3:0]
    #   dpb_inst_1 = high nibble [7:4]
    #
    # INIT_RAM_xx: 256 bits = 64 nibbles, LSB = lowest address
    # Format: 64-char hex string, rightmost char = address 0

    def gen_init_params(byte_array, inst_prefix):
        """Generate INIT_RAM defparam lines for one Gowin_DPB instance."""
        lines = []
        lo_nibbles = [b & 0x0F for b in byte_array]
        hi_nibbles = [(b >> 4) & 0x0F for b in byte_array]

        for nibbles, inst_name in [(lo_nibbles, f'{inst_prefix}.dpb_inst_0'),
                                    (hi_nibbles, f'{inst_prefix}.dpb_inst_1')]:
            for ram_idx in range(64):  # INIT_RAM_00 to INIT_RAM_3F
                start = ram_idx * 64
                # Build 256-bit value: nibble at start goes to bits [3:0] (rightmost)
                val = 0
                for j in range(64):
                    addr = start + j
                    nib = nibbles[addr] if addr < len(nibbles) else 0
                    val |= (nib << (j * 4))
                lines.append(f'defparam {inst_name}.INIT_RAM_{ram_idx:02X} = 256\'h{val:064X};')
        return lines

    vh_path = os.path.join(out_dir, 'bram_init.vh')
    with open(vh_path, 'w') as f:
        f.write('// Auto-generated BRAM initialization from bootstrap.bin\n')
        f.write(f'// {num_words} words ({len(data)} bytes)\n')
        f.write('// Run: python3 scripts/gen_bram_init.py src/bootstrap.bin src\n\n')

        f.write('// High byte BRAM (ram_hi)\n')
        for line in gen_init_params(hi_bytes, 'ram_hi'):
            f.write(line + '\n')

        f.write('\n// Low byte BRAM (ram_lo)\n')
        for line in gen_init_params(lo_bytes, 'ram_lo'):
            f.write(line + '\n')

    print(f"Synthesis:  {vh_path} (4 x 64 INIT_RAM params)")

if __name__ == '__main__':
    main()
