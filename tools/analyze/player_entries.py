#!/usr/bin/env python3
"""Per-player entries in the team table: where each name sits relative to its ID.
CLI: player_entries.py DUMP SQUAD_JSON   (SQUAD_JSON from edit_names.py)"""
import json
import struct
import sys
from collections import Counter


def entries(buf, ids_names, window=256):
    name_at = {}
    for pid, name in ids_names.items():
        at = buf.find(name.encode("utf-8") + b"\0")
        if at < 0:
            continue
        id_bytes = struct.pack("<I", int(pid))
        lo = max(0, at - window)
        idp = buf.rfind(id_bytes, lo, at)
        if idp >= 0:
            name_at[int(pid)] = (at, at - idp)
    positions = sorted(a for a, _ in name_at.values())
    stride = Counter(b - a for a, b in zip(positions, positions[1:])).most_common(1)[0][0]
    delta = Counter(d for _, d in name_at.values()).most_common(1)[0][0]
    return {"stride": stride, "name_minus_id": delta, "first_name_at": positions[0]}


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    print(json.dumps(entries(data, json.load(open(sys.argv[2])))))
