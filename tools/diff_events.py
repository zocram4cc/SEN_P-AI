#!/usr/bin/env python3
"""SEN:P-AI parity check (spec section 7, item 1).

Usage: diff_events.py A B   A/B: event-log files or senpai_tap frames, each detected
by its first byte (a log starts with '{'; a flag such as --tap is accepted and ignored).
Exit 0 when (a) the non-clock events match in every field but timestamp, with
minutes truncated, and (b) Clock Stopped counts differ by at most 2.
"""
import json
import sys

CORE = {"Teams Changed", "Stats Found", "Stats Lost", "Goal", "Own Goal",
        "Card", "Player Sub"}


def load_log(path):
    text = open(path, encoding="utf-8").read()
    decoder, i, out = json.JSONDecoder(), 0, []
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return out
        obj, i = decoder.raw_decode(text, i)
        out.append(obj)


def load_tap(path):
    data, i, out = open(path, "rb").read(), 0, []
    while i < len(data):
        n = int.from_bytes(data[i:i + 4], "little")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def _norm(event):
    out = {k: v for k, v in event.items() if k != "timestamp"}
    for key in ("gameMinute", "injuryMinute"):
        v = out.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[key] = int(v)
    return out


def compare(a, b, stop_tolerance=2):
    problems = []
    core_a = [_norm(e) for e in a if e.get("event") in CORE]
    core_b = [_norm(e) for e in b if e.get("event") in CORE]
    for i, (x, y) in enumerate(zip(core_a, core_b)):
        if x != y:
            problems.append(f"event {i} differs:\n  A {x}\n  B {y}")
            break
    if len(core_a) != len(core_b):
        problems.append(f"event counts differ: A {len(core_a)} B {len(core_b)}")
    stops_a = sum(e.get("event") == "Clock Stopped" for e in a)
    stops_b = sum(e.get("event") == "Clock Stopped" for e in b)
    if abs(stops_a - stops_b) > stop_tolerance:
        problems.append(f"Clock Stopped counts differ: A {stops_a} B {stops_b}")
    return problems


def load(path):
    head = open(path, "rb").read(64).lstrip()
    return load_log(path) if head.startswith(b"{") else load_tap(path)


def main(argv):
    paths = [p for p in argv if not p.startswith("--")]
    problems = compare(load(paths[0]), load(paths[1]))
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
