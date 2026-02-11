#!/usr/bin/env python3
"""Convert Z8000 bootstrap.bin to Z80 assembly include file.

Generates a .inc file with:
- DW statements with 16-bit words (big-endian)
- bootstrap_body_len: number of words

Use --skip N to skip the first N 16-bit words (e.g. --skip 8 to skip
reset vectors that are defined inline with IFDEF in the firmware source).
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Convert Z8000 bootstrap binary to Z80 assembly include')
    parser.add_argument('input', help='Input binary file')
    parser.add_argument('output', help='Output .inc file')
    parser.add_argument('--skip', type=int, default=0,
                        help='Skip first N 16-bit words')
    args = parser.parse_args()

    with open(args.input, 'rb') as f:
        data = f.read()

    # Pad to even length if needed
    if len(data) % 2:
        data += b'\x00'

    # Convert to 16-bit words (big-endian, as Z8000 stores them)
    words = []
    for i in range(0, len(data), 2):
        word = (data[i] << 8) | data[i+1]
        words.append(word)

    # Skip first N words
    skip = args.skip
    skipped_words = words[:skip]
    words = words[skip:]

    # Find last non-zero word to trim trailing zeros
    last_nonzero = len(words) - 1
    while last_nonzero > 0 and words[last_nonzero] == 0:
        last_nonzero -= 1
    words = words[:last_nonzero + 1]

    with open(args.output, 'w') as f:
        f.write("; Z8000 Bootstrap Body - Auto-generated from bootstrap.bin\n")
        f.write("; Do not edit - run 'make bootstrap' to regenerate\n")
        f.write(";\n")
        if skip:
            f.write(f"; Skipped first {skip} words ({skip*2} bytes) - defined inline in firmware\n")
            f.write(";\n")
        f.write(f"; Size: {len(words)} words ({len(words)*2} bytes)\n")
        f.write(";\n\n")

        f.write(f"bootstrap_body_len: equ {len(words)}\n\n")

        # Write 8 words per line
        for i in range(0, len(words), 8):
            chunk = words[i:i+8]
            hex_vals = ', '.join(f'0x{w:04X}' for w in chunk)
            addr = (skip + i) * 2  # Address in original binary
            f.write(f"        dw {hex_vals}  ; 0x{addr:04X}\n")

    print(f"Generated {args.output} ({len(words)} words, {len(words)*2} bytes, skip={skip})")


if __name__ == '__main__':
    main()
