#!/usr/bin/env python3
"""HUD clock oracle: OCR the in-game clock off OBS once a second.

Prints "epoch_ms<TAB>M:SS" whenever the reading changes, so SEN:P-AI event
timestamps (ms since epoch) can be compared with the on-screen clock.
Uses rigbot's own clock region and parse_clock; never sends input.
CLI: hud_clock.py VERSION   (run with $RIG_VENV/bin/python)"""
import asyncio
import sys
import time
from pathlib import Path

RIGBOT = Path("$RIGBOT")
sys.path.insert(0, str(RIGBOT))
import easyocr  # noqa: E402
from obswebsocket import obsws  # noqa: E402
from rigbot.core.frame import Frame  # noqa: E402
from rigbot.core.sources import ObsScreenshotSource  # noqa: E402
from rigbot.core.vision import Vision, parse_clock  # noqa: E402
from rigbot.spec.loader import load_all  # noqa: E402


async def main(version):
    spec = load_all(RIGBOT / "rigbot" / "versions")[version]
    vision = Vision(easyocr.Reader(["en"], gpu=True, verbose=False), spec.corrections)
    ws = obsws("localhost", 4455, "")
    ws.connect()
    source, last, seq = ObsScreenshotSource(ws, "rigbot"), None, 0
    try:
        while True:
            seq += 1
            frame = Frame(source.get_frame(), seq, time.time())
            clock = parse_clock(await vision.text(frame, spec.ocr_regions["clock"]))
            if clock and clock != last:
                print(f"{int(frame.captured_at * 1000)}\t{clock}", flush=True)
                last = clock
            await asyncio.sleep(max(0.0, 1.0 - (time.time() - frame.captured_at)))
    finally:
        ws.disconnect()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
