# PES 2021 acceptance (spec 7.2): PASS with the upstream substitution finding

- Date: 2026-10-08. Build `pes19-pes21` at `2518131`. Prefix `$HEROIC_PREFIXES/default/eFootball PES 2021`.
- Match: testbot scenario with `best_xi: false` (rigbot's best-XI step fails on PES 2021 at the time of testing), rig match 4 of the session, `/g/` vs `/sp/`. SEN:P-AI, `senpai_tap.exe` and `hud_clock.py` ran from PRE_GAME (23:08:45) to after full time (23:30:00). Final 1–0. This match was not used for measurement.
- `events.log` and `tap.bin` are cut at this match's `Stats Lost`; the instance kept running into the next match.

## `tools/accept.py events.log tap.bin bot.log hud-clock.tsv`

```
sub minute 36.0 vs HUD 32..32
clock 36.0 vs HUD 32
```

Everything else passes:

- Stats Found was reached without brute force.
- The goal matches the bot: TERRY A. DAVIS, 75.16 vs 75:20.
- The score is 1–0.
- There are 3 Player Sub events, with the bot's players coming on.
- No two Clock Stopped events are consecutive.
- First-half clock: every Clock Updated is within ±1 of the HUD, except the jump above.
- Pipe and log are identical.

The two failures are the upstream clock jump at a substitution made during a stoppage (`../QUESTIONS.md`); the same check fails on the upstream build on PES 2017.

## By hand

| Item | Result |
|---|---|
| `Teams Changed` vs EDIT (`edit_names.py pes21 /g/`, `/sp/`) | /g/ 721 and /sp/ 749, 23 players each, IDs and names identical |
| Score vs full time | 1–0 = `oracle-p2.jpg` |
| Events vs Match Events page (`oracle-p4.jpg`) | NGUBU 31.1 / 31', WOBBIE 74 / 74', goal TERRY A. DAVIS 75.2 / 76'; >A FUCKING CHEESE GRATER 36.0 / 33' (the jump) |
| Grid totals (`sen_totals.py match.sen`) vs Team Stats | Shots 6/2, On Target 4/1, Fouls 0/1, Offside 0/0, Corners 1/1, Free Kicks 0/0, Passes 139/108, Made 123/84, Crosses 3/4, Interceptions 17/9, Tackles (Won) 1/3, Saves 1/2: all equal |
| `.sen` reopens | in a fresh instance with no game (build prefix): `grid-reopened.png` shows 1–0, 90+2:36, the grid and the event log |
| Catalog lock | the same instance, locked to PES 2021, refuses a PES 2019 `.sen` (`catalog-lock-message.png`) |
| Brute force (7.3) | `../brute-force/pes21-*` |
| Penalties | M2 of the measurements went to a shoot-out: shoot-out goals land in segment 8, MatchReader's penalties rule (`../../measurements/pes21/catalog.md`) |

## Oracle note

`hud_clock.py` misreads some frames ("7:42" as "71:42"; stoppage "90:00 +0:32" as "9:00"). `accept.py` treats as first half only the readings before the HUD reaches 45' straight after 43'/44'.
