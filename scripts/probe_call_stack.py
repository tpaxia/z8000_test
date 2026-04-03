#!/usr/bin/env python3
"""Probe what the emulator pushes on the stack for segmented CALL/CALR/RET/SC tests.

Runs each test with VERIFY_MEM for the stack region to see
what words are actually written to the stack.

Usage: python -m scripts.probe_call_stack
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.emu_runner import EmuRunner
from tests.gen_segmented import generate_segmented_tests
from tests.gen_seg_systematic import generate_seg_systematic_tests
from tests.defs import TestCase

STACK_BASE = 0x0F00
# Probe 8 words below the stack pointer (0xEF0 - 0xEFE)
PROBE_ADDRS = list(range(STACK_BASE - 16, STACK_BASE, 2))


def make_sc_test():
    """Create an SC test for Z8001 segmented mode.

    ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001):
      0200: 2101 0800           ld r1,#0x800
      0204: 7d1d                ldctl psapoff,r1
      0206: 2101 8000           ld r1,#0x8000
      020a: 7d1c                ldctl psapseg,r1
      020c: 760e 8000 0f00      lda rr14,0x0f00
      0212: 2100 0000           ld r0,#0x0
      0216: 7f00                sc #0
      0218: 2100 dead           ld r0,#0xdead   (should NOT execute)
      021c: 5e08 00c0           jp t,0x00c0     (should NOT reach)

    Handler at 0x300:
      0300: 2100 55aa           ld r0,#0x55aa
      0304: 5e08 00c0           jp t,0x00c0

    PSA at PSAP(0x800)+0x18 = 0x818:
      0818: C000                new FCW (system + segmented)
      081a: 8000                new PCSEG (segment 0)
      081c: 0300                new PC offset (handler)

    SC stack frame (pushed to system stack at 0xF00):
      SP-2: PC offset
      SP-4: PCSEG
      SP-6: old FCW
      SP-8: identifier (SC instruction word)
    """
    return TestCase(
        name='seg_sc_basic',
        mnemonic='SC',
        description='SC #0: system call trap, verify stack frame',
        tags=['segmented', 'seg0', 'sc', 'trap'],
        instruction='SC #0',
        target='z8001-seg',
        code=[
            0x2101, 0x0800,             # LD R1, #0x0800
            0x7D1D,                     # LDCTL PSAP, R1
            0x2101, 0x8000,             # LD R1, #0x8000
            0x7D1C,                     # LDCTL PSAPSEG, R1
            0x760E, 0x8000, 0x0F00,     # LDA RR14, 0x0F00
            0x2100, 0x0000,             # LD R0, #0x0000
            0x7F00,                     # SC #0
            0x2100, 0xDEAD,             # LD R0, #0xDEAD (should not execute)
            0x5E08, 0x00C0,             # JP T, 0x00C0 (should not reach)
        ],
        regs={0: 0x0000, 1: 0x0000},
        fcw=0xC000,  # system mode + segmented
        memory={
            # Handler code at 0x300
            0x0300: 0x2100,  # LD R0, #0x55AA
            0x0302: 0x55AA,
            0x0304: 0x5E08,  # JP T, 0x00C0
            0x0306: 0x00C0,
            # PSA entry for System Call at PSAP+0x18 = 0x0818
            # Layout: reserved(+0), FCW(+2), PCSEG(+4), PC_off(+6)
            0x0818: 0x0000,  # Reserved
            0x081A: 0xC000,  # New FCW (system + segmented)
            0x081C: 0x8000,  # New PCSEG (segment 0)
            0x081E: 0x0300,  # New PC offset (handler)
        },
    )


def main():
    runner = EmuRunner(target="z8001-seg", verbose=True)
    runner.compile()

    # Collect all segmented CALL/CALR/RET tests
    all_tests = generate_segmented_tests() + generate_seg_systematic_tests()
    call_tests = [t for t in all_tests if any(
        tag in t.tags for tag in ['call', 'ret']
    )]

    # Add SC test
    sc_test = make_sc_test()
    call_tests.append(sc_test)

    print(f"Found {len(call_tests)} tests (CALL/CALR/RET + SC)")
    print(f"Probing stack addresses: {', '.join(f'0x{a:04X}' for a in PROBE_ADDRS)}")
    print("=" * 70)

    for tc in call_tests:
        # Inject probe addresses into expected_memory so the driver reads them back
        for addr in PROBE_ADDRS:
            if addr not in tc.expected_memory:
                tc.expected_memory[addr] = 0  # value doesn't matter, just need readback

        result = runner.run_test(tc)

        print(f"\n--- {tc.name} ({tc.mnemonic}) ---")
        print(f"  desc: {tc.description}")
        print(f"  FCW:  0x{result.actual_fcw:04X}")
        print(f"  R14:  0x{result.actual_regs.get(14, 0):04X}  R15: 0x{result.actual_regs.get(15, 0):04X}")
        print(f"  R0:   0x{result.actual_regs.get(0, 0):04X}")
        print(f"  exec: {result.exec_result}")
        print(f"  Stack memory:")
        for addr in PROBE_ADDRS:
            val = result.actual_memory.get(addr)
            if val is not None and val != 0:
                print(f"    [0x{addr:04X}] = 0x{val:04X}  <<")
            else:
                val_str = f"0x{val:04X}" if val is not None else "None"
                print(f"    [0x{addr:04X}] = {val_str}")

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
