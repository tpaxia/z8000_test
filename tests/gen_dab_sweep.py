"""Exhaustive DAB table capture from silicon.

The Z8000 DAB correction table is indexed by
(destination byte, C, H, DA) -> (result byte, C out): 2048 entries. MAME
derives it with a generator (makedab.cpp) rather than measuring it, and both
the pre-fix and post-fix generators are known to disagree with the real Z8001
in at least one class (see golden mame_dab_sub_half_borrow_wrap: silicon gives
0x9F/C=1, both MAME tables give 0xFF).

This module sweeps the whole table in 8 captures - one per (C, H, DA)
combination - by running a 256-iteration loop on the CPU under test:

    loop:
        ldb   rh2,rh7     ; value under test (0x00..0xFF)
        ldctl fcw,r1      ; install this combination's C/H/DA
        dab   rh2
        ldctl r3,fcw      ; capture result flags (LDCTL affects no flags,
        ldb   rh6,rh2     ;  so this MUST be the instruction right after DAB)
        ldb   rl6,rl3
        ld    @r5,r6      ; store (result << 8) | (FCW & 0xFF)
        inc   r5,#2
        incb  rh7,#1
        djnz  r4,loop

Each entry records the full low FCW byte, not just carry, so the capture also
pins DAB's Z/S/V/DA/H outputs over the entire input domain.

NON-SEGMENTED ONLY. `LDCTL FCW,Rn` rewrites the whole FCW; in segmented mode
it would clear the SEG bit and break the dump routine (the same reason
sys_ldctl_write_fcw is in gen_seg_systematic._SKIP_TESTS). DAB behaviour does
not depend on segmentation, so nothing is lost.

Capture:
    python -m tests.compare --capture --port /dev/ttyUSB0 --target z8001 \
        --golden-dir golden/z8001 --name 'dab_sweep_*'

Decode / diff / emit a C table:
    python -m tests.dab_table --golden-dir golden/z8001

Usage:
    from tests.gen_dab_sweep import generate_dab_sweep_tests
    tests = generate_dab_sweep_tests()
"""

from .defs import TestCase
from .flags import FCW_SYS, flag_mask

# Results buffer: 256 words at 0x0600-0x07FF (the free SRC/DST scratch window,
# well inside the lower 4KB that non-segmented mode can address).
RESULT_BASE = 0x0600
SWEEP_COUNT = 256

# Register allocation for the sweep loop.
REG_FCW_IN = 1     # FCW to install before each DAB
REG_WORK = 2       # RH2 = value under test / result
REG_FCW_OUT = 3    # captured FCW
REG_LOOP = 4       # iteration counter
REG_PTR = 5        # store pointer
REG_PACK = 6       # (result << 8) | flags
REG_VALUE = 7      # RH7 = value counter

# ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002, linked at .text=0x200)
#   200: a072            ldb     rh2,rh7
#   202: 7d1a            ldctl   fcw,r1
#   204: b020            dab     rh2
#   206: 7d32            ldctl   r3,fcw
#   208: a026            ldb     rh6,rh2
#   20a: a0be            ldb     rl6,rl3
#   20c: 2f56            ld      @r5,r6
#   20e: a951            inc     r5,#0x2
#   210: a870            incb    rh7,#0x1
#   212: f48a            djnz    r4,0x200
SWEEP_CODE = [
    0xA072,
    0x7D1A,
    0xB020,
    0x7D32,
    0xA026,
    0xA0BE,
    0x2F56,
    0xA951,
    0xA870,
    0xF48A,
]

# (name suffix, DA, C, H) - DA=0 is the add/adc half of the table, DA=1 sub/sbc.
COMBINATIONS = [
    ('add_c0h0', 0, 0, 0),
    ('add_c0h1', 0, 0, 1),
    ('add_c1h0', 0, 1, 0),
    ('add_c1h1', 0, 1, 1),
    ('sub_c0h0', 1, 0, 0),
    ('sub_c0h1', 1, 0, 1),
    ('sub_c1h0', 1, 1, 0),
    ('sub_c1h1', 1, 1, 1),
]


def sweep_name(suffix):
    return f'dab_sweep_{suffix}'


def input_fcw(da, c, h):
    """FCW installed by LDCTL before each DAB (system mode + the inputs)."""
    fcw = FCW_SYS
    if c:
        fcw |= flag_mask('C')
    if h:
        fcw |= flag_mask('H')
    if da:
        fcw |= flag_mask('DA')
    return fcw


def result_addr(value):
    """Address of the result word for destination byte `value`."""
    return RESULT_BASE + value * 2


def generate_dab_sweep_tests():
    """One test per (C, H, DA) combination, each sweeping all 256 values."""
    tests = []
    observe = [result_addr(v) for v in range(SWEEP_COUNT)]

    for suffix, da, c, h in COMBINATIONS:
        tests.append(TestCase(
            name=sweep_name(suffix),
            mnemonic='DAB',
            description=(
                f'DAB sweep over all 256 destination bytes with '
                f'DA={da} C={c} H={h}'
            ),
            tags=['dab', 'byte', 'sweep', 'table'],
            target='common',
            code=list(SWEEP_CODE),
            regs={
                REG_FCW_IN: input_fcw(da, c, h),
                REG_WORK: 0x0000,
                REG_FCW_OUT: 0x0000,
                REG_LOOP: SWEEP_COUNT,
                REG_PTR: RESULT_BASE,
                REG_PACK: 0x0000,
                REG_VALUE: 0x0000,
            },
            fcw=FCW_SYS,
            # Every result word is written by the loop, so no preload is
            # needed - an unwritten entry would show as a diff, not as noise.
            observe_memory=observe,
        ))

    return tests
