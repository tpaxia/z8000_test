#!/usr/bin/env python3
"""Generate hex file for Z80 firmware RAM initialization."""

import sys

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <firmware.bin> [output.hex]", file=sys.stderr)
        sys.exit(1)

    bin_file = sys.argv[1]
    hex_file = sys.argv[2] if len(sys.argv) > 2 else bin_file.replace('.bin', '.hex')

    with open(bin_file, 'rb') as f:
        data = f.read()

    # Generate hex file compatible with $readmemh
    with open(hex_file, 'w') as f:
        for byte in data:
            f.write(f'{byte:02X}\n')

    print(f"Generated {hex_file} ({len(data)} bytes)")

if __name__ == '__main__':
    main()
