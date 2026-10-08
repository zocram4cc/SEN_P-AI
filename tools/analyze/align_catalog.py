#!/usr/bin/env python3
"""Anchors YAML -> catalog YAML, by the rules of the plan's Task 12.

- Rule 2: anchors pin PES 2017 u32x9 blocks to new blocks. Between two anchors, equal
  block counts map in order (names included); otherwise every new block there is
  ?UNKNOWN and the PES 2017 names there are absent (offset -1).
- Rule 5: tail fields are only the measured ones listed under `tail`; every other tail
  byte is ?UNKNOWN, u32 words where a whole aligned word is free, else u8 flags.
- Rule 3: `invariants` checks every "X Made" <= "X" pair per player in raw entries.

CLI: align_catalog.py ANCHORS_YAML [--check DUMP:HOME_AT:HOME_N:AWAY_AT:AWAY_N ...] > catalog.yaml
"""
import re
import struct
import sys
from pathlib import Path

import yaml

PES17_CPP = Path(__file__).resolve().parents[2] / "src" / "catalogs" / "Pes17Stats.cpp"
SIZE = {"sint8": 1, "uint8": 1, "uint16": 2, "uint32": 4, "float32": 4}
PAIRS = [("Passes Made", "Passes"), ("Low Passes Made", "Low Passes"), ("Through Balls Made", "Through Balls"),
         ("Lofted/High Passes Made", "Lofted/High Passes"), ("Crosses Made", "Crosses"),
         ("Ground Passes Made", "Ground Passes"), ("Aerial Passes Made", "Aerial Passes"),
         ("Low Thru Balls Made", "Low Thru Balls"), ("Chipped Thru Balls Made", "Chipped Thru Balls"),
         ("Tackles Won", "Tackles"), ("Shots on Target", "Shots"),
         ("Shots Faced On Target", "Shots Faced"), ("Saves", "Shots Faced On Target")]


def pes17_rows(path=PES17_CPP):
    """(offset, type, count, name, vis) for every PES 2017 catalog row."""
    pat = re.compile(r'\{\s*\d+,\s*0x([0-9A-F]+),\s*(\w+)\s*,(\d+),\s*L\("([^"]+)"\),\s*(\w+)\}')
    return [(int(o, 16), t, int(c), n, v) for o, t, c, n, v in pat.findall(Path(path).read_text())]


def align(p17, spec):
    blocks_end, entry = spec["blocks_end"], spec["entry_size"]
    if (blocks_end - 4) % 36:
        raise ValueError("blocks_end must be 4 + 36k")
    n_new = (blocks_end - 4) // 36
    p17_blocks = [r for r in p17 if r[1] == "uint32" and r[2] == 9]
    by_name = {r[3]: k for k, r in enumerate(p17_blocks)}
    pins = sorted((by_name[n], (a["offset"] - 4) // 36, n) for n, a in spec["anchors"].items())
    for (p, q, _), (p2, q2, n2) in zip(pins, pins[1:]):
        if not (p < p2 and q < q2):
            raise ValueError(f"anchors out of order at {n2}")
    rows, absent, new_name = [], [], {}
    pin_at = {q: (p, n) for p, q, n in pins}
    for (p, q, n0), (p2, q2, n1) in zip([(-1, -1, "start")] + pins, pins + [(len(p17_blocks), n_new, "end")]):
        same = (p2 - p) == (q2 - q)
        for k in range(1, q2 - q):
            src = p17_blocks[p + k] if same else None
            new_name[q + k] = (src[3], src[4], f"rule 2: in order between {n0} and {n1}") if src else \
                (None, "Unknown", f"rule 2: {q2 - q - 1} blocks between {n0} and {n1} vs PES 2017 {p2 - p - 1}")
        if not same:
            absent += [r for r in p17_blocks[p + 1:p2] if not r[3].startswith("?")]
    rows.append({"name": "Player ID", "offset": 0, "type": "uint32", "count": 1, "vis": "DontCare",
                 "evidence": "u32 player ID at entry start (find_stats_blocks run)"})
    for q in range(n_new):
        if q in pin_at:
            name = pin_at[q][1]
            vis, ev = p17_blocks[by_name[name]][4], spec["anchors"][name]["evidence"]
        else:
            name, vis, ev = new_name[q]
        rows.append({"name": name, "offset": 4 + 36 * q, "type": "uint32", "count": 9, "vis": vis, "evidence": ev})
    tail = sorted(({"name": n, **t} for n, t in spec.get("tail", {}).items()), key=lambda r: r["offset"])
    p17_vis = {r[3]: r[4] for r in p17}
    taken = set()
    for t in tail:
        span = range(t["offset"], t["offset"] + SIZE[t["type"]] * t["count"])
        if taken & set(span) or span.start < blocks_end or span.stop > entry:
            raise ValueError(f"tail field {t['name']} overlaps or is out of the tail")
        taken |= set(span)
    i, cells = blocks_end, []
    while i < entry:
        if i in taken:
            i += 1
            continue
        if i % 4 == 0 and i + 4 <= entry and not taken & set(range(i, i + 4)):
            cells.append((i, "uint32"))
            i += 4
        else:
            cells.append((i, "uint8"))
            i += 1
    merged = sorted([(t["offset"], t) for t in tail] + [(o, {"name": None, "offset": o, "type": ty, "count": 1})
                                                         for o, ty in cells], key=lambda x: x[0])
    for _, t in merged:
        if t["name"]:
            rows.append({"name": t["name"], "offset": t["offset"], "type": t["type"], "count": t["count"],
                         "vis": p17_vis.get(t["name"], "Unknown"), "evidence": t["evidence"]})
        else:
            rows.append({"name": None, "offset": t["offset"], "type": t["type"], "count": 1, "vis": "Unknown",
                         "evidence": "rule 5: tail byte without a measured meaning"})
    named = {r["name"] for r in rows if r["name"]}
    absent += [r for r in p17 if r[3] not in named and not r[3].startswith("?") and r[2] != 9]
    for r in absent:
        if r[3] not in named:
            rows.append({"name": r[3], "offset": -1, "type": r[1], "count": r[2], "vis": r[4],
                         "evidence": "absent: not found in this version (spec 4.5)"})
            named.add(r[3])
    for k, r in enumerate(rows):
        if r["name"] is None:
            r["name"] = f"?UNKNOWN {k}" + (" FLAG" if r["type"] == "uint8" else "")
    return rows


def invariants(rows, entries):
    """Rule 3 violations as (made, plain, player_id, made_value, plain_value)."""
    at = {r["name"]: r for r in rows if r["offset"] >= 0 and r["type"] == "uint32" and r["count"] == 9}
    out = []
    for e in entries:
        pid = struct.unpack_from("<I", e, 0)[0]
        for made, plain in PAIRS:
            if made in at and plain in at:
                m = sum(struct.unpack_from("<9I", e, at[made]["offset"]))
                p = sum(struct.unpack_from("<9I", e, at[plain]["offset"]))
                if m > p:
                    out.append((made, plain, pid, m, p))
    return out


def main(argv):
    spec = yaml.safe_load(open(argv[0]))
    rows = align(pes17_rows(), spec)
    entries = []
    for arg in argv[argv.index("--check") + 1:] if "--check" in argv else []:
        path, *nums = arg.split(":")
        h_at, h_n, a_at, a_n = (int(x, 0) for x in nums)
        data = open(path, "rb").read()
        es = spec["entry_size"]
        entries += [data[h_at + k * es:h_at + (k + 1) * es] for k in range(h_n)]
        entries += [data[a_at + k * es:a_at + (k + 1) * es] for k in range(a_n)]
    bad = invariants(rows, entries)
    for b in bad:
        print("rule 3 violation:", b, file=sys.stderr)
    yaml.safe_dump({"tag": spec["tag"], "entry_size": spec["entry_size"], "stats": rows},
                   sys.stdout, sort_keys=False, width=200)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
