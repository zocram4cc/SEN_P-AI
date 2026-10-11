"""seg_report.py VERSION SAMPLES.bin HUD.tsv -> one line per sample where a 9-bucket counter or ticks changed:
time, HUD clock, per-bucket deltas of Passes and Goals (summed over both sides), the 13 tick counters' total delta."""
import struct, sys, bisect
VER, SAMPLES, HUD = sys.argv[1:4]
S, PASSES, TAIL = {"pes17": (4784, 0x1D8, 0xFE8), "pes19": (8176, 0x31C, 0x17A4), "pes21": (8500, 0x31C, 0x18E8)}[VER]
TICKS = TAIL + 0x10
hud = [(int(l.split("\t")[0]) / 1000, l.split("\t")[1].strip()) for l in open(HUD) if "\t" in l]
hud_t = [t for t, _ in hud]

def clock(t):
    i = bisect.bisect_right(hud_t, t) - 1
    return f"{hud[i][1]}@{t - hud[i][0]:.0f}s" if i >= 0 else "-"

def sums(blob, off, n):
    out = [0] * n
    for k in range(46):
        e = k * S
        if struct.unpack_from("<I", blob, e)[0] == 0:
            continue
        for b, v in enumerate(struct.unpack_from(f"<{n}I", blob, e + off)):
            out[b] += v
    return out

prev = None
data = open(SAMPLES, "rb").read()
p = 0
while p < len(data):
    t, base, n = struct.unpack_from("<dQI", data, p); p += 20
    blob = data[p:p + n]; p += n
    cur = (sums(blob, PASSES, 9), sums(blob, 0x4, 9), sums(blob, TICKS, 13))
    if prev and cur != prev:
        d = [[a - b for a, b in zip(x, y)] for x, y in zip(cur, prev)]
        nz = lambda v: {i: x for i, x in enumerate(v) if x}
        print(f"{t:.0f} {clock(t):>14} passes{nz(d[0])} goals{nz(d[1])} ticks{nz(d[2])}")
    prev = cur
print("final passes", prev[0], "goals", prev[1], "ticks", prev[2])
