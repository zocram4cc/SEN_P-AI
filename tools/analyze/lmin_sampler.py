"""Read-only: sample every player's First/Last Minute on Pitch once a second (PES 2019 layout).
python lmin_sampler.py BOTLOG AFTER_PATTERN SECONDS OUT.tsv   (WINEPREFIX = the game's prefix)"""
import collections, struct, subprocess, sys, time, os
LOG, AFTER, SECS, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
ENV = dict(os.environ, WINEDEBUG="-all")
REG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "regions.exe")
while True:
    text = open(LOG, errors="replace").read()
    if AFTER in text and "entering state MATCH_ONGOING" in text[text.index(AFTER):]:
        break
    time.sleep(2)
time.sleep(10)
hits = subprocess.run(["wine", REG, "PES2019.exe", "scan", "72101"], env=ENV, capture_output=True, text=True).stdout
base = next(int(l.split()[1], 16) for l in hits.splitlines() if l.split()[2] == "190000")
H, A, S = 0x7B5A4, 0xD18EC, 8176
end = time.time() + SECS
with open(OUT, "w") as f:
    while time.time() < end:
        rows = []
        for off in (H, A):
            subprocess.run(["wine", REG, "PES2019.exe", "dump", f"{base + off:x}", str(23 * S), "/tmp/lmin.bin"], env=ENV, capture_output=True)
            d = open("/tmp/lmin.bin", "rb").read()
            rows += [struct.unpack_from("<bb", d, k * S + 0x17A4) for k in range(23)]
        lm = [l for fm, l in rows]
        mode = collections.Counter(lm).most_common(1)[0][0]
        odd = [(k, fm, l) for k, (fm, l) in enumerate(rows) if l != mode and fm >= 0]
        f.write(f"{int(time.time()*1000)}\tmax={max(lm)}\tmode={mode}\t{odd}\n"); f.flush()
        time.sleep(1)
