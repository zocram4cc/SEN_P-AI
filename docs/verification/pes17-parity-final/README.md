# PES 2017 parity on the final build (plan Task 14 step 2): PASS

- Date: 2026-10-08/09, 23:37–00:09 local. PES 2017 prefix, `/usr/bin/wine`.
- Builds, side by side, each from its own working directory:
  - base: tag `baseline-pes17`;
  - fork: `2518131`, the last source change. It has all three layouts, so the status text reads "Searching for PES2017.exe/PES2019.exe/PES2021.exe...", and includes the `findPid` first-entry fix.
- Match: original testbot scenario (`best_xi: true`), `/g/` vs `/sp/`, final 2–3 (bot: `result: '/g/' vs '/sp/' score=(2, 3)`).

```
$ diff_events.py events-base.log events-fork.log; echo "events: $?"
events: 0
$ sen_sections.py match-base.sen match-fork.sen finalStats; echo "finalStats: $?"
identical
finalStats: 0
```

Both logs: `Teams Changed` 1, `Stats Found` 1, `Goal` 5, `Card` 1, `Player Sub` 3, `Stats Lost` 1, `Clock Stopped` 29, `Clock Started` 28, `Clock Updated` 2225: the same counts, including the clock events.

`accept.py events-fork.log events-fork.log bot.log hud-clock.tsv` reports only the upstream substitution clock jump (`sub minute 22.6 vs HUD 20..20`, `39.2 vs 35..35`). The base build's events are identical, so upstream does the same.
