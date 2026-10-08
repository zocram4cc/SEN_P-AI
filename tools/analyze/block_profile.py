#!/usr/bin/env python3
"""Per-block team sums of u32 x9 stat blocks across one side's entries.
CLI: block_profile.py STATS_DUMP HOME_AT HOME_N AWAY_AT AWAY_N ENTRY_SIZE [START] [END]"""
import json
import struct
import sys


def blocks(home_rows, away_rows, start=4, width=36, end=None):
    end = end if end is not None else min(len(r) for r in home_rows + away_rows)
    out = []
    for off in range(start, end - width + 1, width):
        def col(rows):
            return [struct.unpack_from("<9I", r, off) for r in rows]
        h, a = col(home_rows), col(away_rows)
        nonzero = sorted({s for row in h + a for s, v in enumerate(row) if v})
        out.append({"offset": off, "home_sum": sum(map(sum, h)),
                    "away_sum": sum(map(sum, a)), "segments_nonzero": nonzero})
    return out


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    h_at, h_n, a_at, a_n, size = (int(x, 0) for x in sys.argv[2:7])
    start = int(sys.argv[7], 0) if len(sys.argv) > 7 else 4
    end = int(sys.argv[8], 0) if len(sys.argv) > 8 else None
    rows = lambda at, n: [data[at + k * size: at + (k + 1) * size] for k in range(n)]
    print(json.dumps(blocks(rows(h_at, h_n), rows(a_at, a_n), start, 36, end), indent=1))
