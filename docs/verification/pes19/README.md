# PES 2019 acceptance (spec 7.2): PASS with one upstream finding

- Date: 2026-10-08. Build `pes19-pes21` at `75a7e1f` (same `src/` as `0110c2e`). Prefix `$HEROIC_PREFIXES/default`, `/usr/bin/wine`.
- Match: testbot scenario `docs/plans/senpai/scenario_subs_bestxi.yaml`, rig match 4 of the session, `/g/` vs `/sp/`. SEN:P-AI, `senpai_tap.exe` and `tools/analyze/hud_clock.py` ran from PRE_GAME (20:40:42) to after full time (21:10:18). Final 2–1 (bot: `result: '/g/' vs '/sp/' score=(2, 1)`).
- This match was not used for any measurement (the layout and catalog came from matches 1 and 2), so it is an out-of-sample check.

## `tools/accept.py events.log tap.bin bot.log hud-clock.tsv`

```
sub minute 35.5 vs HUD 31..32
clock 38.7 vs HUD 35
```

Every other check passes: Stats Found reached without brute force; goals 3 = bot 3, sides, minutes ±1 and scorers equal (Botnet 27.97' / bot 28:36, Install Gentoo 50.73' / 51:27, PUNISHED MESSI 59.66' / 60:30); score 2–1; 3 subs with the bot's players in; no two consecutive Clock Stopped (27 stopped, 26 started); pipe and log identical (`diff_events.py events.log tap.bin` exit 0).

The two failures are the upstream clock jump at a substitution (`../QUESTIONS.md`), on the same pattern as upstream on PES 2017: at 20:57:45 Clock Stopped 32.24 (HUD 31:58); at 20:57:55 Player Sub and Clock Updated 35.47 (HUD 31:58); at 20:58:12 Clock Updated 34.2 (HUD 33:57); at 20:58:39 Clock Started/Updated 38.69 (HUD 35:01); at 20:58:52 37.18 (HUD 36:55); back within ±1 by 20:59:02. A read-only sampler over the next match (`lmin-m5.tsv`, 1 Hz, all 46 entries) shows the stats table's largest Last Minute on Pitch, which is what MatchReader's "mode" computes (`std::max_element` over a `map<int,int>` compares keys first), rising one minute at a time through both substitutions. The jump is therefore in MatchReader's time estimate or a sub-second transient, not in the stored minutes.

## Remaining 7.2 items (by hand)

| Item | Result |
|---|---|
| `Teams Changed` names vs EDIT (`edit_names.py pes19 /g/`, `/sp/`) | /g/ 721 and /sp/ 749, 23 players each; IDs and names equal as sets and per ID |
| Final score vs full-time screen | 2–1 = `oracle-teamstats.jpg` |
| Sub minutes vs Match Events page (`oracle-events*.jpg`) | EXPOSED 19.14 / 19', MY BOY JLINGZ... 69 / 69', iTODDLERS BTFO 35.47 / 33' (the jump above); card PERRO CACA 19.14 / 19' |
| Grid totals (`tools/sen_totals.py match.sen`) vs Team Stats page | Shots 7/5, On Target 4/4, Fouls 0/4, Offside 0/1, Corners 1/2, Free Kicks 4/0, Passes 173/91, Made 157/78, Crosses 9/1, Interceptions 6/2, Tackles (Won) 1/2, Saves 2/2: all equal |
| First-half clock vs HUD | every Clock Updated with a HUD reading ≤3 s old within ±1, except the 38.7 vs 35 above |
| `.sen` reopens in the same build | opened through Open in a fresh instance with no game running (build prefix): `grid-reopened.png` shows the same tab score, clock 90+1:17, grid rows and event log as the live instance (`grid-live.png`) |
| Catalog lock (spec 5.2) | the same instance, now on the PES 2019 catalog, refuses a PES 2017 `.sen` with "This match is from PES2017.exe; restart SEN:P-AI to open it." (`catalog-lock-message.png`) |
| Brute force (7.3) | `../brute-force/pes19-*`: with `statsRegionSize` forced to 1, "Try Harder" in the Teams state gives "SEN:P-AI noticed the stats!" |

## Notes

- The acceptance instance later exited during the next match (21:17:32) with `X Error of failed request: BadWindow ... X_UnmapWindow`, an abort in Wine's X11 driver; its debug log ends mid-tick with no warning. Recorded in `../QUESTIONS.md`.
- Event logs and `.sen` written by the PES 2019 build: Player Sub events carry no `playerOut`, as in the PES 2017 baseline.

Evidence: `events.log`, `tap.bin`, `match.sen`, `bot.log`, `hud-clock.tsv`, screenshots.
