# PES 2017 parity, fork vs upstream (spec 7.1): PASS

- Date: 2026-10-08, 18:39–19:09 local.
- Builds, both under Wine in the PES 2017 prefix, each from its own working directory:
  - base: tag `baseline-pes17` (worktree `SEN_P-AI-baseline`);
  - fork: `755b12a` "refactor: per-version GameLayout and stat catalogs" (same `src/` as the later tool-only commits).
- Match: testbot scenario `docs/plans/senpai/scenario_subs_bestxi.yaml` match 2, `/g/` vs `/sp/`, final 2–3 (bot: `result: '/g/' vs '/sp/' score=(2, 3)`).

## Step 4 output

```
$ diff_events.py events-base.log events-fork.log; echo "events: $?"
events: 0
$ sen_sections.py match-base.sen match-fork.sen finalStats; echo "finalStats: $?"
identical
finalStats: 0
```

Both logs: `Teams Changed` 1, `Stats Found` 1, `Goal` 5, `Player Sub` 2, `Stats Lost` 1, `Clock Stopped` 28, `Clock Started` 27, `Clock Updated` 1443. Goals (both): 15' Home Green Is My Pepper, 40' Away TSUUUUUUUUUUUUUUUUU, 52' Home No Time For Love, 68' Away SO, IT HAPPENED AGAIN, 72' Away MESSI; bot: 15:41, 40:05, 52:52, 68:50, 72:08, same sides.

The whole `.sen` files first differ at byte 12, the PATCH version byte (6 vs 7, `Common.h`); timestamps differ after that.

## Clock vs HUD (the oracle used for spec 7.2)

`hud-clock.tsv` is `tools/analyze/hud_clock.py pes17` over the same match. Against the fork's log, every first-half `Clock Updated` with a HUD reading at most 3 s older: 49 compared, 0 outside ±1 minute, worst 1.

Evidence: `events-base.log`, `events-fork.log`, `match-base.sen`, `match-fork.sen`, `hud-clock.tsv`, `bot.log` (match 2 only).
