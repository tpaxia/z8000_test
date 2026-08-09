# Z8000 instruction test and comparison framework

This repository runs common Z8000 instruction tests against several independent
implementations:

- a physical Z8001 connected to a Quartus FPGA bus harness;
- the `z8000_micro` Verilog core, in simulation or on a Gowin/Quartus FPGA;
- the standalone `z8000_emu` C++ model; and
- MAME's Z8000 core through the `z8ktest01` and `z8ktest02` test machines.

Captures from the physical Z8001 are stored under `golden/` and are the reference
for the other backends.  The test definitions, bootstrap, memory observations,
I/O observations, undefined-result masks, and comparison code are shared, so a
test exercises the same instruction state on every target.

## Repository setup

Clone the repository with its three submodules:

```sh
git clone --recurse-submodules https://github.com/tpaxia/z8000_test.git
cd z8000_test
```

For an existing checkout:

```sh
git submodule update --init --recursive
```

The principal dependencies are:

- Python 3;
- `pyserial` for physical serial links (and the shared harness imported by the
  MAME runner);
- CMake and a C++17 compiler for `z8000_emu`;
- Icarus Verilog for the simulation backend;
- z88dk's `z88dk-z80asm` for the supervisor firmware;
- `z8k-coff-as`, `z8k-coff-ld`, and `z8k-coff-objcopy` for the bootstrap; and
- Gowin IDE or Quartus for the corresponding FPGA projects.

Install the Python serial dependency with:

```sh
python3 -m pip install pyserial
```

## The two test interfaces

There are two related command-line interfaces:

- `python3 -m tests` runs the declarative functional tests and checks their
  explicit expected values.
- `python3 -m tests.compare` runs the full differential suite and compares each
  result with a physical-Z8001 golden capture.  This is the main regression
  interface and includes the assembler-generated opcode-variant tests by
  default.

Use `--list` to see exactly which tests the current revision selects:

```sh
python3 -m tests --list --target z8002
python3 -m tests.compare --list --target z8002
python3 -m tests.compare --list --target z8001-seg
```

Both interfaces accept `--name`, `--mnemonic`, and a tag/category filter.  Run
either command with `--help` for the complete option list.

## Quick start: compare the standalone emulator

The emulator backend builds its CMake library and the harness driver
automatically on first use:

```sh
# Z8002/non-segmented execution against physical-Z8001 captures
python3 -m tests.compare --emu --target z8002

# Z8001 segmented execution against segmented captures
python3 -m tests.compare --emu --target z8001-seg
```

The golden directory follows the target automatically:

| Target | Tests selected | Default golden directory |
|---|---|---|
| `common` | target-independent tests | `golden/z8001` |
| `z8001` | common and Z8001 non-segmented tests | `golden/z8001` |
| `z8002` | common and Z8002 tests | `golden/z8001` |
| `z8001-seg` | segmented Z8001 tests | `golden/z8001-seg` |

Useful focused forms are:

```sh
python3 -m tests.compare --emu --name 'mame_*' -v
python3 -m tests.compare --emu --mnemonic DIVL -v
python3 -m tests.compare --emu --category opcode_coverage
python3 -m tests.compare --emu --no-opcode-coverage
python3 -m tests.compare --emu --recompile
```

Opcode-variant coverage is enabled by default.  `--no-opcode-coverage` is useful
for a shorter diagnostic run, but it is not the complete regression suite.

## Golden captures from the physical Z8001

The Quartus external-CPU harness is the reference target.  It uses a real
40-pin Zilog Z8001 and exposes the same ASCII supervisor protocol used by the
other hardware backends.  See [`quartus/README.md`](quartus/README.md) for the
board, level-shifter, pin, clock, and programming details.

Capture or refresh selected goldens with:

```sh
# Physical Z8001 in non-segmented mode
python3 -m tests.compare --capture --port /dev/cu.usbserial-XXXX \
    --target z8001

# Physical Z8001 in segmented mode
python3 -m tests.compare --capture --port /dev/cu.usbserial-XXXX \
    --target z8001-seg

# A focused recapture
python3 -m tests.compare --capture --port /dev/cu.usbserial-XXXX \
    --target z8001 --name 'mame_*'
```

`--golden-dir` can override the target-derived location.  Capturing overwrites
the selected JSON files, so inspect the resulting diff before committing them.

Each golden records the final register file and complete FCW, plus requested
memory and I/O observations.  `tests/golden_masks.json` documents fields whose
values are architecturally undefined.  Comparisons apply these masks by
default; use `--no-masks` to expose every raw difference.

The odd-stack-pointer PUSH/POP cases are presently disabled.  Real-silicon
captures conflict with the documented alignment behavior, and the tests remain
excluded while that discrepancy is unresolved.

## Verilog core

### Simulation

Run direct tests against `z8000_micro` with Icarus Verilog:

```sh
python3 -m tests --sim --target z8002
python3 -m tests.compare --sim --target z8002
python3 -m tests.compare --sim --target z8001-seg
```

Add `--recompile` after RTL changes.  The lower-level Make targets are:

```sh
make sim          # Z80 supervisor/command simulation
make sim-full     # direct BRAM simulation with the Z8000 core
make sim-compile  # compile the Python simulation backend
make wave         # open a generated VCD with GTKWave
```

### Gowin FPGA projects

| Project | Board | CPU mode |
|---|---|---|
| `z8002_test_harness.gprj` | Tang Nano 20K | Z8002 non-segmented |
| `z8001_seg_test_harness.gprj` | Tang Nano 20K | Z8001 segmented |
| `z8002_test_harness_primer20k.gprj` | Tang Primer 20K | Z8002 non-segmented |
| `z8001_seg_test_harness_primer20k.gprj` | Tang Primer 20K | Z8001 segmented |

Run a programmed board through its serial port:

```sh
python3 -m tests.compare --port /dev/cu.usbserial-XXXX --target z8002
python3 -m tests.compare --port /dev/cu.usbserial-XXXX --target z8001-seg
```

### Quartus projects

The `quartus/` directory contains three projects:

- `z8001_ext_test.qpf`: the physical-Z8001 golden-capture rig;
- `z8001_int_test.qpf`: the internal soft Z8001; and
- `z8002_int_test.qpf`: the internal soft Z8002.

`make firmware` rebuilds the shared Z80 supervisor firmware and the Quartus MIF
image.  `make ucode-mem` regenerates the Z8001 and Z8002 microcode memory images
from the `z8000_micro` submodule.

## MAME backend

The MAME runner uses `z8ktest01` for Z8001 and `z8ktest02` for Z8002.  These
machines reproduce the FPGA supervisor, shared BRAM, firmware, and UART protocol
inside MAME.  They are test-only machines and are not part of an ordinary
upstream MAME build; point the runner at a checkout containing
`src/mame/zilog/z8ktest.cpp`.

```sh
export Z8K_MAME_DIR=/path/to/mame

python3 -m tests.compare --mame --target z8002
python3 -m tests.compare --mame --target z8001-seg
```

Alternatively pass `--mame-dir /path/to/mame`.  The runner starts MAME itself,
uses a localhost socket for the emulated UART, and selects the appropriate test
machine from `--target`.

## Comparing two backends directly

`tests.crosscheck` compares the JSON output of two backend runs.  This exposes
cases where the implementations disagree even when both are being evaluated
against the same golden set:

```sh
python3 -m tests.compare --emu --target z8002 --save-json emu.json
python3 -m tests.compare --mame --target z8002 --save-json mame.json
python3 -m tests.crosscheck emu.json mame.json \
    --left-name z8000_emu --right-name MAME
```

The command exits nonzero if the two result sets diverge.

## DAB silicon sweep

`tests/gen_dab_sweep.py` covers all 2,048 DAB input combinations using eight
physical-CPU captures.  Decode the committed captures or compare them with
MAME's table using:

```sh
python3 -m tests.dab_table --golden-dir golden/z8001
python3 -m tests.dab_table --golden-dir golden/z8001 \
    --diff-header /path/to/mame/src/devices/cpu/z8000/z8000dab.h
python3 -m tests.dab_table --golden-dir golden/z8001 --flags
```

The decoded table is measured silicon behavior, not a table generated from an
emulator.

## Saving reports and traces

The differential runner can save machine-readable comparison results and bus
traces:

```sh
python3 -m tests.compare --emu --target z8002 \
    --save-json results/emu.json --save-traces traces/emu
```

For a physical-board functional-test report:

```sh
python3 scripts/gen_report.py --port /dev/cu.usbserial-XXXX \
    --target z8002 --output results/z8002
```

The bus trace records address, data, read/write, byte/word, memory/I/O, segment,
and status information where supported by the backend.

## Supervisor protocol and memory layout

The FPGA supervisor communicates at 115200 baud, 8N1.  The most useful commands
are:

| Command | Purpose |
|---|---|
| `INIT` | upload/initialize the Z8000 bootstrap |
| `EX` | reset, execute, and stop at HALT or timeout |
| `ST` / `RS` | read status / assert reset |
| `WRnxxxx` / `RRn` / `DA` | write, read, or dump registers |
| `WMaaaaxxxx` / `RMaaaa` | write or read a memory word |
| `CC` / `FC` | read cycle or instruction-fetch counts |
| `TC` / `TRnnn` | read trace count or a trace entry |
| `TOxxxxxxxx` | set the cycle timeout; zero disables it |

Commands contain no spaces and hexadecimal fields are written directly after
the command, for example `WM02008110`.

The bootstrap reserves the low memory area and places each test at `0x0200`:

| Address | Use |
|---|---|
| `0x0000` onward | reset/trap vectors and bootstrap state |
| `0x0010`-`0x002f` | initial R0-R15 values |
| `0x0090`-`0x00af` | dumped R0-R15 values |
| `0x00c0` onward | register-dump routine |
| `0x0200` onward | instruction under test |
| `0x0f00` onward | ordinary scratch area |

`test_harness.py` provides a small interactive client for manual protocol work:

```sh
python3 test_harness.py /dev/cu.usbserial-XXXX
python3 test_harness.py /dev/cu.usbserial-XXXX ST
```

## Source layout

- `tests/`: test definitions, generators, runners, comparison logic, masks,
  cross-checking, and DAB tooling;
- `golden/z8001/`: physical Z8001 non-segmented captures;
- `golden/z8001-seg/`: physical Z8001 segmented captures;
- `emu/`: bridge between the Python runner and `z8000_emu`;
- `src/`: shared supervisor firmware, bootstrap, BRAM, UART, trace, and FPGA
  harness logic;
- `quartus/`: physical and soft-CPU Quartus projects;
- `scripts/`: firmware/microcode conversion and report tools;
- `z8000_emu/`: standalone C++ emulator submodule;
- `z8000_micro/`: Verilog CPU submodule; and
- `tv80_official/`: Z80 supervisor-core submodule.

The large systematic generators contain assembler-verified opcode listings.
Do not hand-edit those listing comments: regenerate or validate instruction
encodings with the Z8000 assembler.

## License

This repository is licensed under the MIT License.  The submodules retain their
own licenses.
