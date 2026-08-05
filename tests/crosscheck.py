"""Cross-check two backends against each other, test by test.

Comparing each backend against golden separately answers "is this one
right". It does not answer "do these two agree", which is the louder
signal: two independently maintained implementations of the same core
disagreeing on a single test localises a defect immediately, where a pass
rate only tells you something is wrong somewhere.

Feed it the --save-json output of two runs over the same golden set:

    python -m tests.compare --emu  --golden-dir golden/z8001 --save-json emu.json
    python -m tests.compare --mame --golden-dir golden/z8001 --save-json mame.json
    python -m tests.crosscheck emu.json mame.json

Exit status is 1 if the two disagree anywhere, so it can gate a commit.
"""

from __future__ import annotations

import argparse
import json
import sys


def load(path):
    """Read a --save-json comparison file into {test: {field: (ref, dut)}}."""
    with open(path) as fh:
        rows = json.load(fh)
    out = {}
    for r in rows:
        diffs = {}
        for d in r.get("diffs", []):
            if d.get("masked"):
                continue
            diffs[d["field"]] = (d.get("ref"), d.get("dut"))
        out[r["test"]] = diffs
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Cross-check two backend runs against each other")
    ap.add_argument("left", help="--save-json output from the first backend")
    ap.add_argument("right", help="--save-json output from the second backend")
    ap.add_argument("--left-name", default=None)
    ap.add_argument("--right-name", default=None)
    ap.add_argument("--limit", type=int, default=40,
                    help="max divergences to print (0 = all)")
    args = ap.parse_args()

    lname = args.left_name or args.left
    rname = args.right_name or args.right
    left, right = load(args.left), load(args.right)

    only_left = sorted(set(left) - set(right))
    only_right = sorted(set(right) - set(left))
    shared = sorted(set(left) & set(right))

    print(f"{lname}: {len(left)} tests")
    print(f"{rname}: {len(right)} tests")
    if only_left:
        print(f"  only in {lname}: {len(only_left)}  e.g. {only_left[:3]}")
    if only_right:
        print(f"  only in {rname}: {len(only_right)}  e.g. {only_right[:3]}")

    # A test where both backends agree - including agreeing on being wrong -
    # is not a divergence. Only differing behaviour is.
    diverged = [t for t in shared if left[t] != right[t]]

    print()
    print(f"Cross-check over {len(shared)} shared tests: "
          f"{len(shared) - len(diverged)} agree, {len(diverged)} diverge")

    if diverged:
        print()
        shown = diverged if args.limit == 0 else diverged[:args.limit]
        for t in shown:
            print(f"  {t}")
            for field in sorted(set(left[t]) | set(right[t])):
                lv = left[t].get(field)
                rv = right[t].get(field)
                if lv == rv:
                    continue
                fmt = lambda v: "matches golden" if v is None else \
                    f"ref={v[0]} dut={v[1]}"
                print(f"      {field:<14s} {lname}: {fmt(lv)}")
                print(f"      {'':<14s} {rname}: {fmt(rv)}")
        if len(shown) < len(diverged):
            print(f"  ... {len(diverged) - len(shown)} more (use --limit 0)")

    return 1 if diverged else 0


if __name__ == "__main__":
    sys.exit(main())
