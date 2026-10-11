#!/usr/bin/env python3
"""Read-only check of the unofficial fork's PES17 pointer chains (match_tracker testing.md).
chain17.py (WINEPREFIX = the game's)  -> module base, readiness flag, chain-derived home entry vs the scan's."""
import os, struct, subprocess, tempfile
from pathlib import Path
ENV = dict(os.environ, WINEDEBUG="-all")
REG = str(Path(__file__).resolve().parents[1] / "regions.exe")
TMP = os.path.join(tempfile.gettempdir(), "chain17.bin")

def run(*a):
    return subprocess.run(["wine", REG, "PES2017.exe", *a], env=ENV, capture_output=True, text=True).stdout

def u32(addr):
    subprocess.run(["wine", REG, "PES2017.exe", "dump", f"{addr:x}", "4", TMP], env=ENV, capture_output=True)
    return struct.unpack("<I", open(TMP, "rb").read())[0]

# module base: first MEM_IMAGE region (type 0x1000000) at the usual 32-bit image base
regions = [l.split("\t") for l in run("list").splitlines()]
image = sorted(int(b, 16) for b, s, st, ty, pr in regions if int(ty, 16) == 0x1000000)
mod = 0x400000 if 0x400000 in image else image[0]
root = u32(mod + 0x21A9E68)
container = u32(root + 0x124)
flag = u32(container + 0x1168)
sub = u32(root + 0x2890)
home = sub + 0x317FC + 0x3804
scan = [l.split() for l in run("scan", "72101", str(0x90000)).splitlines()]
print(f"module {mod:x} root {root:x} container {container:x} flag {flag} sub {sub:x}")
print(f"chain home entry {home:x}; scan hits {[(h[0], h[1]) for h in scan]}")
for h in scan:
    if int(h[0], 16) == home:
        print("MATCH: chain home entry == scan hit")
print(f"id at chain home entry: {u32(home)}")
