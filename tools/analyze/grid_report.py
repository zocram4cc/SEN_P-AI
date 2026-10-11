#!/usr/bin/env python3
"""The "Play Area Grid" (140 x u32 per stats entry) over seg_sampler.py samples.
CLI: grid_report.py VERSION SAMPLES.bin
Prints: whether every cell only ever grows (cumulative), how the grid total relates to the
player's ticks, and the final grid of each side's first entry and of each side's most
forward-placed player (by grid rows) as 14 rows of 10, so the orientation can be read off."""
import struct
import sys

VER, SAMPLES = sys.argv[1:3]
S, TAIL, GRID = {"pes17": (4784, 0xFE8, 0x1034), "pes21": (8500, 0x18E8, 0x1938)}[VER]
TICKS = TAIL + 0x10

samples = []
data, p = open(SAMPLES, "rb").read(), 0
while p < len(data):
    t, _, n = struct.unpack_from("<dQI", data, p)
    p += 20
    samples.append((t, data[p:p + n]))
    p += n


def entries(blob):
    for k in range(len(blob) // S):
        e = k * S
        pid = struct.unpack_from("<I", blob, e)[0]
        if pid:
            yield k, pid, struct.unpack_from("<140I", blob, e + GRID), struct.unpack_from("<13I", blob, e + TICKS)


shrinks, prev = 0, {}
for _, blob in samples:
    for k, pid, grid, _ in entries(blob):
        if k in prev:
            shrinks += sum(1 for a, b in zip(grid, prev[k]) if a < b)
        prev[k] = grid
print(f"samples {len(samples)}; cell decreases between consecutive samples: {shrinks}")

last = samples[-1][1]
for k, pid, grid, ticks in entries(last):
    if sum(ticks):
        print(f"{k:2} {pid} grid_total {sum(grid):7} ticks_total {sum(ticks):7} nonzero_cells {sum(1 for c in grid if c):3} ticks {list(ticks)}")
def show(k, pid, grid):
    print(f"entry {k} ({pid}): 14 rows x 10")
    for r in range(14):
        print(" ".join(f"{c:4}" for c in grid[r * 10:(r + 1) * 10]))


rows = lambda g: sum(r * sum(g[r * 10:(r + 1) * 10]) for r in range(14)) / max(1, sum(g))
for side in (0, 1):
    mine = [(k, pid, g) for k, pid, g, ticks in entries(last) if (k >= 23) == side and sum(ticks)]
    show(*mine[0])
    show(*max(mine, key=lambda e: rows(e[2])))
