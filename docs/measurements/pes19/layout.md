# PES 2019 layout measurement (Task 10)

- Date: 2026-10-08. Prefix `$HEROIC_PREFIXES/default`, `/usr/bin/wine`. All tools read-only.
- Matches (testbot `docs/plans/senpai/scenario_subs_bestxi.yaml`, `/g/` 721 vs `/sp/` 749):
  - M1: kick-off 19:26:41, final 3–4; subs WOBBIE for APOLOGIZE 22', Techtubers for Thinkpad 42', EL VAR SINSON for NGUBU 71'.
  - M2: kick-off 19:55:47, final 0–3.
- `T=$SENPAI/tools`, `export WINEDEBUG=-all WINEPREFIX=$HEROIC_PREFIXES/default`.
- Wine's text-mode stdout ends tool lines with CRLF; strip `\r` before matching fields with awk.

## Team table (M1 pre-game, 19:21)

```
$ wine $T/regions.exe PES2019.exe scan 72101 > hits-pre.tsv
      4 2d1c0000 50000
      3 60d80000 1490000
      2 7f590000 290000
      1 2af80000 20000
$ find_team_table.py pre_2d1c0000.bin 721 /g/   -> [{"pairs_at": 207720, "count": 23, "marker": "0xfffd", "name_at": 207452}]
$ find_team_table.py pre_2d1c0000.bin 749 /sp/  -> [{"pairs_at": 209236, "count": 23, "marker": "0xfffe", "name_at": 208968}]
  (no pair runs in 60d80000 or 7f590000)
$ edit_names.py pes19 /g/ > g.json; edit_names.py pes19 /sp/ > sp.json
$ player_entries.py pre_2d1c0000.bin g.json   -> {"stride": 256, "name_minus_id": [4, 8], "first_name_at": 211724}
$ player_entries.py pre_2d1c0000.bin sp.json  -> {"stride": 256, "name_minus_id": [4, 8], "first_name_at": 221964}
```

- No `u32` team ID within 64 bytes after 32 pairs: the pair array has **40** slots (`ffff0000 00000000` invalid pairs continue), then a 4-byte `validPair`, then `teamID` (721 / 749) at name+592. The player-entry arrays are 40 × 256 bytes per side (away names start 10240 bytes after home names). The EDIT file's squad table also has 40 slots. SEN:P-AI reads 32 slots, as upstream; squads here have 23.
- Entry boundary: each entry starts at name−56. The 8 bytes before that are `01000000 15000000`, PES 2017's two trailing words of the previous entry. Within an entry: `validPair` (FFFD/FFFE) at +44, `playerID` at +48, the ID again at +52, name (46 bytes) at +56, print name at +102.
- Team name: 70 bytes NUL-padded, scoreboard code at +70 (`G`), as PES 2017.
- Condition byte: oracle = the Team Sheet arrows at pre-game (`oracle/m1-team-sheet.jpg`): blue Stallman, SICP, i use arch btw, iTODDLERS BTFO, *BSD, AMD-chan; orange Install Gentoo, >A fucking cheese grater, Mommy Lisa, Thinkpad, Green Is My Pepper; purple CS Grad; green the rest. Searching every byte from name−200 to name+200, every 3-bit field, both directions:

```
(23 matches, rel name +151, shift 0, ascending)   next best: 17
```

  The byte at entry+207 holds 0x10 | ordinal (0 purple … 4 red), unlike PES 2017's 0x00–0x80 in the top bits. `playerInfo.condition` is not used by any output.

## Stats table (M1 live, 19:27)

```
$ wine $T/regions.exe PES2019.exe scan 72101 > hits.tsv; ... scan 74901 > hits-sp.tsv
$ for r in 45bc0000:0x1490000 64560000:0x290000 618e0000:0x520000 7f320000:0x190000 33770000:0x20000; do dump; find_stats_blocks 721; 749; done
== 45bc0000 0x1490000: g []  sp []
== 64560000 0x290000: g []  sp []
== 618e0000 0x520000: g [[124, 11, 112]]  sp [[1356, 11, 112]]
== 7f320000 0x190000: g [[505252, 23, 8176]]  sp [[858348, 23, 8176]]
== 33770000 0x20000: g [[126336, 23, 8]]  sp [[126704, 23, 8]]
```

The stats table is the region where both teams run 23 entries at the same stride: 0x190000, home 0x7B5A4, away 0xD18EC, stride 8176 (0x1FF0, the lead), away − home 0x56348 (the lead; 43.19 entries, so the two sides are separate arrays).

## Second match (Step 6)

```
M2 pre-game: team pairs in 2d1c0000 (0x50000) again; pairs_at 207720 / 209236, name_at 207452 / 208968, players 211724 / 221964, stride 256
M2 kick-off 19:55:47 + 20 s: stats region 7f690000 size 0x190000; find_stats_blocks 721 [[505252, 23, 8176]], 749 [[858348, 23, 8176]]
```

Every offset within its region is the same in both matches. Region sizes 0x50000 and 0x190000 are the same in both matches, so both are recorded (the stats base moved, which is expected).

## ID bounds

`playerIdMin 70099`, `playerIdMax 91100` (spec 6). `/g/` 72101–72123 and `/sp/` 74901–74923 lie inside.

## Tick rate (rule 5, spec 4.4)

Match Time is 10 min (`oracle/match-settings.jpg`). Game Ticks Played: 5833 at HUD 16:17 (358/min) and 14916 for Thinkpad off at 42' (355/min), against PES 2017's 320 (= 10 × 32). MatchReader corrects ticks-per-minute in ±32 steps towards the stats-table minute (`MatchReader.cpp:340-355`), so it settles at 352 and stores `matchLength` 11 (written to `.sen`). Finding, no change: see `../../verification/QUESTIONS.md`.

Dumps deleted after this task.
