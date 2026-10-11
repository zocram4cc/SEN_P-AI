#!/usr/bin/env python3
"""Read-only: dump both stats blocks every 3 s while a match runs (needs WINEPREFIX of the game).
CLI: seg_sampler.py VERSION BOTLOG AFTER_PATTERN OUT.bin
Each record: <d epoch><Q region base><I length> + home block + away block (23 entries each).
Starts at the first MATCH_ONGOING after AFTER_PATTERN in rigbot's log, stops after MATCH_FINISH."""
import os
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VER, LOG, AFTER, OUT = sys.argv[1:5]
EXE, RSIZE, H, A, S = {"pes17": ("PES2017.exe", 0x90000, 0x35010, 0x5DE40, 4784),
                       "pes19": ("PES2019.exe", 0x190000, 0x7B5A4, 0xD18EC, 8176),
                       "pes21": ("PES2021.exe", 0x190000, 0x7B5C4, 0xD4C14, 8500)}[VER]
REG = str(Path(__file__).resolve().parents[1] / "regions.exe")
ENV = dict(os.environ, WINEDEBUG="-all")
TMP = os.path.join(tempfile.gettempdir(), "seg_sampler.bin")


def tail():
    text = open(LOG, errors="replace").read()
    return text[text.index(AFTER):] if AFTER in text else ""


def wine(*args):
    return subprocess.run(["wine", REG, EXE, *args], env=ENV, capture_output=True, text=True)


while "entering state MATCH_ONGOING" not in tail():
    time.sleep(2)
base = None
while base is None:  # the region holding /g/'s first player ID (72101) with the stats region's size
    rows = [line.split() for line in wine("scan", "72101").stdout.splitlines()]
    base = next((int(r[1], 16) for r in rows if len(r) > 2 and int(r[2], 16) == RSIZE), None)
    time.sleep(2)
print(f"base {base:x}", flush=True)
finished = 0
with open(OUT, "ab") as out:
    while finished < 2:
        if "entering state MATCH_FINISH" in tail():
            finished += 1
        t = time.time()
        if wine("dump", f"{base + H:x}", str(A - H + 23 * S), TMP).returncode == 0:
            d = open(TMP, "rb").read()
            blob = d[:23 * S] + d[A - H:A - H + 23 * S]
            out.write(struct.pack("<dQI", t, base, len(blob)) + blob)
            out.flush()
        time.sleep(3)
print("done", flush=True)
