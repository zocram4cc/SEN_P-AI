#!/usr/bin/env python3
"""Spec 7.2 checks: accept.py EVENTS_LOG TAP BOT_LOG HUD_TSV

HUD_TSV is tools/analyze/hud_clock.py output ("epoch_ms<TAB>M:SS"). The bot logs
substitutions at their scheduled minute, so sub and clock minutes are judged
against the HUD clock instead (docs/verification/QUESTIONS.md)."""
import bisect
import re
import sys
from difflib import SequenceMatcher

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import diff_events  # noqa: E402


def hud_minute(hud, ts, max_age_ms):
    """Minute on the HUD at wall time ts (ms): the last reading at most max_age_ms old."""
    i = bisect.bisect_right([t for t, _ in hud], ts) - 1
    return hud[i][1] if i >= 0 and ts - hud[i][0] <= max_age_ms else None


def hud_bracket(hud, ts):
    """HUD minutes of the last reading before ts and the first after it (the HUD is
    hidden during the stoppage in which a substitution happens)."""
    i = bisect.bisect_right([t for t, _ in hud], ts)
    return (hud[i - 1][1] if i > 0 else None), (hud[i][1] if i < len(hud) else None)


def check(ev, tap, bot, hud):
    fails = []
    if "Stats Found" not in [e["event"] for e in ev]:
        fails.append("no Stats Found")
    goals = [e for e in ev if e["event"] == "Goal"]
    bot_goals = re.findall(r"goal: (home|away) scored at (\d+):\d+", bot)
    if len(goals) != len(bot_goals):
        fails.append(f"goals: senpai {len(goals)} bot {len(bot_goals)}")
    for g, (side, minute) in zip(goals, bot_goals):
        if g["team"].lower() != side or abs(int(g["gameMinute"]) - int(minute)) > 1:
            fails.append(f"goal mismatch {g['team']} {g['gameMinute']} vs {side} {minute}")
    scorers = re.findall(r"goal: scorer (.+?) \(", bot)
    for g, name in zip(goals, scorers):
        if g["scorer"]["name"].lower() != name.lower():
            fails.append(f"scorer {g['scorer']['name']!r} vs bot {name!r}")
    subs = [e for e in ev if e["event"] == "Player Sub" and e["gameMinute"] > 0]
    bot_subs = [re.sub(r"^\d+\s+", "", s).strip().lower() for s in re.findall(r"sub at \d+': .+? -> (.+)", bot)]
    if len(subs) != len(bot_subs):
        fails.append(f"subs: senpai {len(subs)} bot {len(bot_subs)}")
    for s, came_on in zip(subs, bot_subs):
        name = s["playerIn"]["name"].lower()
        if came_on not in name and SequenceMatcher(None, came_on, name).ratio() < 0.5:   # bot names are OCR
            fails.append(f"sub playerIn {s['playerIn']['name']!r} vs bot {came_on!r}")
        before, after = hud_bracket(hud, s["timestamp"])
        known = [m for m in (before, after) if m is not None]
        if not known or not min(known) - 1 <= int(s["gameMinute"]) <= max(known) + 1:
            fails.append(f"sub minute {s['gameMinute']:.1f} vs HUD {before}..{after}")
    clock = [e["event"] for e in ev if e["event"] in ("Clock Stopped", "Clock Started")]
    if any(a == b == "Clock Stopped" for a, b in zip(clock, clock[1:])):
        fails.append("two consecutive Clock Stopped")
    compared = 0
    # First half = before the HUD reaches 45' straight after 43'/44'. OCR misreads ("7:42" as
    # "71:42"; stoppage "90:00 +0:32" as "9:00") do not follow that sequence.
    start = min(e["timestamp"] for e in ev if "timestamp" in e)
    clip = [(t, m) for t, m in hud if t >= start]
    half_time = next((t for (_, p), (t, m) in zip(clip, clip[1:]) if m == 45 and p in (43, 44)), float("inf"))
    for e in ev:
        if e["event"] != "Clock Updated" or e["timestamp"] >= half_time:
            continue
        m = hud_minute(hud, e["timestamp"], 3000)
        if m is None or m >= 45:
            continue
        compared += 1
        if abs(int(e["gameMinute"]) - m) > 1:
            fails.append(f"clock {e['gameMinute']:.1f} vs HUD {m}")
    if compared < 10:
        fails.append(f"only {compared} first-half Clock Updated events had a HUD reading")
    result = re.search(r"score=\((\d+), (\d+)\)", bot)
    own = lambda team: sum(1 for e in ev if e["event"] == "Own Goal" and e["team"] == team)
    home = sum(1 for g in goals if g["team"] == "Home") + own("Away")
    away = sum(1 for g in goals if g["team"] == "Away") + own("Home")
    if result and (home, away) != (int(result[1]), int(result[2])):
        fails.append(f"score {home}-{away} vs full time {result[1]}-{result[2]}")
    if diff_events.compare(ev, tap):
        fails.append("pipe and log differ")
    return fails, compared


if __name__ == "__main__":
    ev = diff_events.load(sys.argv[1])
    tap = diff_events.load(sys.argv[2])
    bot = open(sys.argv[3], encoding="utf-8", errors="replace").read()
    hud = [(int(t), int(c.split(":")[0])) for t, c in (line.split() for line in open(sys.argv[4]))]
    fails, compared = check(ev, tap, bot, hud)
    print("\n".join(fails) or f"accept: all checks pass ({compared} first-half clock readings)")
    sys.exit(1 if fails else 0)
