#!/usr/bin/env python3
"""The team table's player pairs {u16 marker, u16 index, u32 playerId} (TeamDataTable.h).
CLI: find_team_table.py DUMP TEAM_ID TEAM_NAME"""
import json
import struct
import sys


def pair_runs(buf, team_id, markers=(0xFFFD, 0xFFFE), minimum=11):
    out, i, end = [], 0, len(buf) - 8
    while i <= end:
        m, pid = struct.unpack_from("<II", buf, i)
        if (m & 0xFFFF) in markers and pid // 100 == team_id:
            start, n = i, 0
            while i <= end:
                m2, p2 = struct.unpack_from("<II", buf, i)
                if (m2 & 0xFFFF) != (m & 0xFFFF) or p2 // 100 != team_id:
                    break
                n, i = n + 1, i + 8
            if n >= minimum:
                out.append((start, n, m & 0xFFFF))
            continue
        i += 4
    return out


def team_name_offset(buf, pairs_at, name, window=1024):
    needle = name.encode("utf-8") + b"\0"
    at = buf.rfind(needle, max(0, pairs_at - window), pairs_at)
    return at if at >= 0 else None


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    found = pair_runs(data, int(sys.argv[2]))
    print(json.dumps([{"pairs_at": a, "count": n, "marker": hex(m),
                       "name_at": team_name_offset(data, a, sys.argv[3])} for a, n, m in found]))
