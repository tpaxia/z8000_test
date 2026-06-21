// Global defines for all Gowin test-harness projects.
// Listed first in every .gprj so the macros are visible to the RTL that
// follows (same mechanism as z8001_defines.v -> `Z8001_MODE).

`ifndef GOWIN_DEFINES
`define GOWIN_DEFINES

// Map the microcode ROM into Gowin block RAM (BSRAM) via the portable
// inferred-ROM path in z8000_micro/rtl/microcode_rom.v, instead of ~3000 LUTs
// of combinational case logic. Enables the synchronous next-uPC wiring in
// z8000_cpu.v. See microcode_rom_z8001.mem / _z8002.mem for the init image.
`define BRAM_UCODE

`endif
