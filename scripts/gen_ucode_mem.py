#!/usr/bin/env python3
"""Generate microcode ROM $readmemh init images for the inferred-BSRAM build.

The Gowin test-harness projects (and the BRAM_UCODE simulation build) map the
microcode ROM into block RAM via an inferred `reg` array initialised with
$readmemb (see z8000_micro/rtl/microcode_rom.v). This emits a dense, 4096-line
binary image (one 54-bit microinstruction per line) for each CPU mode, derived
from the committed combinational microcode source so the BRAM contents are
provably identical to the simulation/golden-validated case ROM. Binary (not
hex) because 54 is not a multiple of 4 -- a hex image would be 56 bits/line and
Gowin flags a width mismatch (EX2526).

$readmemb resolves a bare filename differently per tool: iverilog looks in the
simulation cwd (the repo root), while GowinSynthesis looks in the directory of
the source .v that contains the $readmemh (here z8000_micro/rtl/, beside
microcode_rom.v). So -- exactly like z80_fw.hex, which this project keeps in
both ./ and src/ -- each image is written to BOTH locations with a bare name:

  * z8000_micro/rtl/microcode_rom_z800{1,2}.mem  -> Gowin synthesis
  * microcode_rom_z800{1,2}.mem (repo root)      -> iverilog simulation

Undefined addresses default to 0 (NOP), matching the case ROM's
`default: uinst = 0`.

Usage: scripts/gen_ucode_mem.py   (run from the repo root)
"""

import re
import sys
from pathlib import Path

DEPTH = 4096
ENTRY_RE = re.compile(r"12'h([0-9A-Fa-f]+):\s*uinst\s*=\s*54'h([0-9A-Fa-f]+)")


def build_image(v_path: Path) -> list:
    image = [0] * DEPTH
    for line in v_path.read_text().splitlines():
        m = ENTRY_RE.search(line)
        if m:
            image[int(m.group(1), 16)] = int(m.group(2), 16)
    return image


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    rtl = root / "z8000_micro" / "rtl"
    for mode in ("z8001", "z8002"):
        src = rtl / f"microcode_rom_{mode}.v"
        if not src.exists():
            print(f"error: missing {src}", file=sys.stderr)
            return 1
        image = build_image(src)
        # 54-bit binary per line ($readmemb): 54 is not a multiple of 4, so a
        # hex image would be 56 bits wide and Gowin flags a width mismatch.
        text = "\n".join(f"{w:054b}" for w in image) + "\n"
        # rtl/ copy -> Gowin (source-dir relative); root copy -> iverilog (cwd).
        for out in (rtl / f"microcode_rom_{mode}.mem",
                    root / f"microcode_rom_{mode}.mem"):
            out.write_text(text)
        print(f"wrote microcode_rom_{mode}.mem to ./ and z8000_micro/rtl/ "
              f"({sum(1 for w in image if w)} defined / {DEPTH})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
