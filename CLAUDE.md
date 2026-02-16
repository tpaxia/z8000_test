# Claude Code Instructions

Read `README.md` for project documentation (structure, build commands, memory map, serial protocol, etc.).

## General Rules

- Do ONLY what you are asked to do. Do not investigate, fix, or modify anything beyond the explicit request.
- When asked to run something, run it and report the result. Do not attempt to fix failures unless asked.
- When asked to explain something, explain it and stop. Do not start fixing it.
- Never assume the next step. Wait for instructions.

## Rules for Code Changes

- Do NOT hand-encode Z8000 instruction opcodes. Always verify encodings by assembling with `z8k-coff-as -z8002` and checking the output with `z8k-coff-objdump -d`. Never assume you know the encoding format — test it.
- Do NOT make speculative fixes. Diagnose first with tracing/evidence, then propose a targeted fix.
- Do NOT chain multiple untested changes. Make one change, test it, confirm the result before moving on.
- Do NOT modify clock domains, PLL configurations, or bus timing without explicit approval.
- Do NOT add/remove/rename module ports without explicit approval.
- Do NOT modify shared files (src/, z8000_micro/) when debugging a platform-specific issue (quartus/, gowin/).
- When debugging, prefer adding instrumentation (trace points, debug signals) over changing functional logic.
- Always revert failed changes before trying a different approach. Do not accumulate untested modifications.

## Protected Code

Do NOT modify the following without explicitly asking first:
- `quartus/z8001_bus_external.v`: `bus_as_active` logic and `buf_dir` assignment (M20FPGA bus buffer direction control)
- `z8000_micro/rtl/` - CPU core submodule (shared across all platforms)
- `quartus/pll.v` - PLL configuration (clock generation)
- `src/z8000_bus_fpga.v` - Gowin bus interface (working, reference implementation)
