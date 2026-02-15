"""Trace capture, storage, and comparison utilities."""

import json
import os


def save_traces(results, trace_dir):
    """Save traces from test results to JSON files.

    One file per test: trace_dir/test_name.json
    """
    os.makedirs(trace_dir, exist_ok=True)

    count = 0
    for r in results:
        if not r.trace:
            continue
        path = os.path.join(trace_dir, f"{r.test.name}.json")
        data = {
            "test": r.test.name,
            "mnemonic": r.test.mnemonic,
            "exec_result": r.exec_result,
            "cycle_count": r.cycle_count,
            "fetch_count": r.fetch_count,
            "instr_cycle_count": r.instr_cycle_count,
            "trace": _normalize_trace(r.trace),
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        count += 1

    return count


def load_traces(trace_dir):
    """Load all traces from a directory. Returns {test_name: trace_data}."""
    if not os.path.isdir(trace_dir):
        return {}

    traces = {}
    for name in os.listdir(trace_dir):
        if name.endswith('.json'):
            with open(os.path.join(trace_dir, name)) as f:
                data = json.load(f)
            traces[data["test"]] = data
    return traces


def compare_traces(results, ref_traces):
    """Compare test results against reference traces.

    Returns list of (test_name, diffs) tuples. diffs is empty if match.
    Each diff is a human-readable string.
    """
    comparisons = []

    for r in results:
        name = r.test.name
        if name not in ref_traces:
            comparisons.append((name, ["no reference trace"]))
            continue

        ref = ref_traces[name]
        diffs = _diff_trace(
            _normalize_trace(r.trace),
            ref["trace"],
            ref.get("target", "ref"),
        )
        comparisons.append((name, diffs))

    return comparisons


def _normalize_trace(trace):
    """Normalize trace entries to a consistent list-of-dicts format.

    Strips the index field (order is implicit) and ensures consistent keys.
    """
    normalized = []
    for entry in trace:
        if entry is None:
            continue
        normalized.append({
            "addr": entry.get("addr", 0),
            "data": entry.get("data", 0),
            "rw": entry.get("rw", "?"),
            "bw": entry.get("bw", "?"),
            "io": entry.get("io", "?"),
        })
    return normalized


def _diff_trace(actual, reference, ref_label):
    """Diff two normalized trace lists. Returns list of diff strings."""
    diffs = []

    if len(actual) != len(reference):
        diffs.append(
            f"length: got {len(actual)}, {ref_label} has {len(reference)}"
        )

    n = min(len(actual), len(reference))
    for i in range(n):
        a = actual[i]
        r = reference[i]

        mismatches = []
        for key in ("addr", "data", "rw", "bw", "io"):
            av = a.get(key)
            rv = r.get(key)
            if av != rv:
                if key in ("addr", "data"):
                    mismatches.append(
                        f"{key}=0x{av:04X} vs 0x{rv:04X}"
                    )
                else:
                    mismatches.append(f"{key}={av} vs {rv}")

        if mismatches:
            diffs.append(f"entry {i}: {', '.join(mismatches)}")

    # Report extra entries
    if len(actual) > n:
        for i in range(n, len(actual)):
            a = actual[i]
            diffs.append(
                f"entry {i}: extra (0x{a['addr']:04X} 0x{a['data']:04X} "
                f"{a['rw']} {a['bw']} {a['io']})"
            )
    if len(reference) > n:
        for i in range(n, len(reference)):
            r = reference[i]
            diffs.append(
                f"entry {i}: missing (ref: 0x{r['addr']:04X} 0x{r['data']:04X} "
                f"{r['rw']} {r['bw']} {r['io']})"
            )

    return diffs
