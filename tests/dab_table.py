"""Decode the DAB sweep captures into a table, diff it, and emit C.

The sweep captures (tests/gen_dab_sweep.py) store one word per table entry:
    (result byte << 8) | (FCW & 0xFF)
Eight captures - one per (C, H, DA) combination - cover all 2048 entries.

This module reassembles them into MAME's z8000dab.h index space

    idx = value | (C ? 0x100 : 0) | (H ? 0x200 : 0) | (DA ? 0x400 : 0)
    entry = (carry_out ? 0x100 : 0) | result_byte

and can diff the measured table against MAME's generated one or emit a
drop-in replacement.

    python -m tests.dab_table --golden-dir golden/z8001
    python -m tests.dab_table --golden-dir golden/z8001 --diff-header \
        ~/Projects/mame_latest/mame/src/devices/cpu/z8000/z8000dab.h
    python -m tests.dab_table --golden-dir golden/z8001 --emit-header > z8000dab.h

Flags beyond carry are captured too; --flags reports every entry whose
Z/S/V/DA/H differ from what MAME's DAB handler computes (CLR_CZS then Z and S
from the result byte, V/DA/H preserved from the input).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

from .flags import FLAG_BITS
from .gen_dab_sweep import COMBINATIONS, SWEEP_COUNT, result_addr, sweep_name

CF = 0x100
HF = 0x200
DF = 0x400
TABLE_SIZE = 0x800


def table_index(value, c, h, da):
    return value | (CF if c else 0) | (HF if h else 0) | (DF if da else 0)


def load_sweep(golden_dir):
    """Read the 8 sweep captures -> {idx: (result_byte, out_fcw_low)}.

    Raises FileNotFoundError if a capture is missing, KeyError if a capture is
    missing observed words.
    """
    entries = {}
    for suffix, da, c, h in COMBINATIONS:
        name = sweep_name(suffix)
        path = os.path.join(golden_dir, f'{name}.json')
        with open(path) as fh:
            data = json.load(fh)
        memory = {int(k): v for k, v in data.get('memory', {}).items()}
        for value in range(SWEEP_COUNT):
            addr = result_addr(value)
            if addr not in memory:
                raise KeyError(f'{name}: no observation for 0x{addr:04X}')
            word = memory[addr]
            entries[table_index(value, c, h, da)] = (
                (word >> 8) & 0xFF, word & 0xFF)
    return entries


def measured_table(entries):
    """Collapse to MAME's (carry << 8) | result encoding."""
    table = [None] * TABLE_SIZE
    carry_bit = 1 << FLAG_BITS['C']
    for idx, (result, out_fcw) in entries.items():
        table[idx] = ((CF if out_fcw & carry_bit else 0) | result)
    return table


def parse_header(path):
    """Parse MAME's z8000dab.h into a 2048-entry list."""
    with open(path) as fh:
        text = fh.read()
    body = text[text.index('{'):]
    values = [int(m, 16) for m in re.findall(r'0x([0-9a-fA-F]+)', body)]
    if len(values) != TABLE_SIZE:
        raise ValueError(
            f'{path}: parsed {len(values)} entries, expected {TABLE_SIZE}')
    return values


def describe(idx):
    kind = 'sub' if idx & DF else 'add'
    return (f'{kind} val=0x{idx & 0xFF:02X} '
            f'C={1 if idx & CF else 0} H={1 if idx & HF else 0}')


def fmt_entry(entry):
    if entry is None:
        return '  ----'
    return f'0x{entry & 0xFF:02X}/C{1 if entry & CF else 0}'


def expected_flags(idx, result):
    """Flags MAME's DAB handler produces: CLR_CZS, then Z/S from the result.

    V, DA and H are not touched by DAB, so they carry through from the input.
    """
    flags = 0
    if not result:
        flags |= 1 << FLAG_BITS['Z']
    elif result & 0x80:
        flags |= 1 << FLAG_BITS['S']
    if idx & DF:
        flags |= 1 << FLAG_BITS['DA']
    if idx & HF:
        flags |= 1 << FLAG_BITS['H']
    return flags


def flag_names(value):
    return ' '.join(f'{n}={(value >> b) & 1}'
                    for n, b in sorted(FLAG_BITS.items(),
                                       key=lambda kv: -kv[1]))


def emit_header(table):
    lines = [
        '// license:BSD-3-Clause',
        '// copyright-holders:Juergen Buchmueller,Ernesto Corvi',
        '/************************************************',
        ' * Result table for Z8000 DAB instruction',
        ' *',
        ' * Measured, not derived: decoded from the dab_sweep_* captures',
        ' * (tests/gen_dab_sweep.py). When those come from golden/z8001 this',
        ' * is real Z8001 silicon - do not regenerate from makedab.cpp.',
        ' *',
        ' * bits    description',
        ' * ----------------------------------------------',
        ' * 0..7    destination value',
        ' * 8       carry flag before',
        ' * 9       half carry flag before',
        ' * 10      D flag (0 add/adc, 1 sub/sbc)',
        ' *',
        ' * result  description',
        ' * ----------------------------------------------',
        ' * 0..7    result value',
        ' * 8       carry flag after',
        ' ************************************************/',
        '',
        'static const uint16_t Z8000_dab[0x800] = {',
    ]
    for base in range(0, TABLE_SIZE, 8):
        row = ','.join(f'0x{(table[i] or 0):03x}' for i in range(base, base + 8))
        lines.append(f'\t{row},')
    lines.append('};')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Decode the silicon DAB table from sweep captures')
    parser.add_argument('--golden-dir', default='golden/z8001',
                        help='directory holding the dab_sweep_* captures')
    parser.add_argument('--diff-header', metavar='PATH',
                        help="diff against MAME's z8000dab.h")
    parser.add_argument('--emit-header', action='store_true',
                        help='print a measured z8000dab.h to stdout')
    parser.add_argument('--flags', action='store_true',
                        help='report entries whose Z/S/V/DA/H differ from '
                             "MAME's DAB handler")
    parser.add_argument('--limit', type=int, default=40,
                        help='max differing entries to print (0 = all)')
    args = parser.parse_args()

    try:
        entries = load_sweep(args.golden_dir)
    except FileNotFoundError as exc:
        print(f'Missing sweep capture: {exc.filename}', file=sys.stderr)
        print('Capture first:', file=sys.stderr)
        print('  python -m tests.compare --capture --port /dev/ttyUSB0 '
              f"--target z8001 --golden-dir {args.golden_dir} "
              "--name 'dab_sweep_*'", file=sys.stderr)
        sys.exit(1)

    table = measured_table(entries)

    if args.emit_header:
        print(emit_header(table))
        return

    print(f'Decoded {len(entries)} of {TABLE_SIZE} DAB entries '
          f'from {args.golden_dir}/')

    if args.diff_header:
        mame = parse_header(args.diff_header)
        diffs = [i for i in range(TABLE_SIZE) if table[i] != mame[i]]
        print(f'\nvs {args.diff_header}: '
              f'{TABLE_SIZE - len(diffs)} match, {len(diffs)} differ')
        by_class = {}
        for idx in diffs:
            key = (bool(idx & DF), bool(idx & CF), bool(idx & HF))
            by_class.setdefault(key, []).append(idx)
        for (da, c, h), idxs in sorted(by_class.items()):
            kind = 'sub' if da else 'add'
            print(f'  {kind} C={int(c)} H={int(h)}: {len(idxs)} entries')
        if diffs:
            print()
            shown = diffs if args.limit == 0 else diffs[:args.limit]
            for idx in shown:
                print(f'  {describe(idx):<28s} '
                      f'captured={fmt_entry(table[idx])}  '
                      f'mame={fmt_entry(mame[idx])}')
            if len(shown) < len(diffs):
                print(f'  ... {len(diffs) - len(shown)} more '
                      f'(use --limit 0)')

    if args.flags:
        odd = []
        for idx, (result, out_fcw) in sorted(entries.items()):
            want = expected_flags(idx, result)
            got = out_fcw & 0xFC
            if (got & ~(1 << FLAG_BITS['C'])) != want:
                odd.append((idx, result, got, want))
        print(f'\nNon-carry flag check: {len(entries) - len(odd)} as MAME '
              f'computes them, {len(odd)} differ')
        shown = odd if args.limit == 0 else odd[:args.limit]
        for idx, result, got, want in shown:
            print(f'  {describe(idx):<28s} result=0x{result:02X}')
            print(f'      captured {flag_names(got)}')
            print(f'      mame     {flag_names(want)}')
        if len(shown) < len(odd):
            print(f'  ... {len(odd) - len(shown)} more (use --limit 0)')


if __name__ == '__main__':
    main()
