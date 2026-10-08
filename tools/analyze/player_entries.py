#!/usr/bin/env python3
"""Per-player entries in the team table: where each name sits relative to its ID.
CLI: player_entries.py DUMP SQUAD_JSON   (SQUAD_JSON from edit_names.py)"""
import json
import struct
import sys
from collections import Counter


def entries(buf, ids_names, window=256):
    """name_minus_id lists every name-to-ID distance shared by all players found:
    an entry can hold its ID twice (PES 2017's commentaryID is a copy)."""
    found = {}
    for pid, name in ids_names.items():
        at = buf.find(name.encode("utf-8") + b"\0")
        if at < 0:
            continue
        id_bytes, lo, deltas = struct.pack("<I", int(pid)), max(0, at - window), set()
        idp = buf.rfind(id_bytes, lo, at)
        while idp >= 0:
            deltas.add(at - idp)
            idp = buf.rfind(id_bytes, lo, idp)
        if deltas:
            found[int(pid)] = (at, deltas)
    positions = sorted(a for a, _ in found.values())
    stride = Counter(b - a for a, b in zip(positions, positions[1:])).most_common(1)[0][0]
    common = sorted(set.intersection(*(d for _, d in found.values())))
    return {"stride": stride, "name_minus_id": common, "first_name_at": positions[0]}


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    print(json.dumps(entries(data, json.load(open(sys.argv[2])))))
