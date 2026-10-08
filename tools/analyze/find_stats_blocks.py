#!/usr/bin/env python3
"""Runs of one team's player IDs (teamId*100+n) at a constant stride.
CLI: find_stats_blocks.py DUMP TEAM_ID [STRIDE]"""
import json
import sys
from collections import Counter

import numpy as np


def _hits(buf, team_id):
    words = np.frombuffer(buf[: len(buf) // 4 * 4], dtype="<u4")
    idx = np.nonzero((words // 100) == team_id)[0]
    return [int(i) * 4 for i in idx if 1 <= words[i] % 100 <= 99]


def runs(buf, team_id, stride=None, minimum=11):
    hits = _hits(buf, team_id)
    if stride is None:
        gaps = Counter(b - a for a, b in zip(hits, hits[1:]) if b > a)
        if not gaps:
            return []
        stride = gaps.most_common(1)[0][0]
    hit_set, out, seen = set(hits), [], set()
    for h in hits:
        if h in seen or (h - stride) in hit_set:
            continue
        n = 0
        while h + n * stride in hit_set:
            seen.add(h + n * stride)
            n += 1
        if n >= minimum:
            out.append((h, n, stride))
    return out


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    print(json.dumps(runs(data, int(sys.argv[2]), int(sys.argv[3], 0) if len(sys.argv) > 3 else None)))
