# PES 2021 layout measurement (Task 10)

- Date: 2026-10-08. Prefix `$HEROIC_PREFIXES/default/eFootball PES 2021`, `/usr/bin/wine`. All tools read-only.
- Testbot scenario `scenario_subs_bestxi.yaml` with `best_xi: false` (rigbot's best-XI step fails on PES 2021 today: `confirm_back_on_pre_game_bar`), `/g/` 721 vs `/sp/` 749.
  - Pre-game of the 21:27 attempt: team table.
  - M1: kick-off 22:01:56, final 1–0; subs GIMI for PERRO CACA 30', NGUBU for GIMI 67'.
  - M2: kick-off 22:22:48, 0–0, 5–4 on penalties.
- `export WINEDEBUG=-all WINEPREFIX=...`; tool output lines end in CRLF (strip `\r`).

## Team table (pre-game 21:28)

```
$ regions.exe PES2021.exe scan 72101          # and 74901
      4 7ffffd300000 50000
      3 45770000 1880000
      1 7fd70000 270000
      1 1eac0000 20000
$ find_team_table.py pre_7ffffd300000.bin 721 /g/   -> [{"pairs_at": 220148, "count": 23, "marker": "0xfffd", "name_at": 219820}]
$ find_team_table.py pre_7ffffd300000.bin 749 /sp/  -> [{"pairs_at": 221828, "count": 23, "marker": "0xfffe", "name_at": 221500}]
  (none in 45770000 or 7fd70000)
$ player_entries.py ... g.json   -> {"stride": 392, "name_minus_id": [4, 8], "first_name_at": 224432}
$ player_entries.py ... sp.json  -> {"stride": 392, "name_minus_id": [4, 8], "first_name_at": 240112}
```

- As in PES 2019: 40 pairs per side, then a `validPair`, then `teamID` at name+652; 40 player entries per side. Entries are 392 bytes. The previous entry's `01000000 15000000` trailer ends at name−60, so an entry starts at name−60: ID at +52, its copy at +56, name at +60, print name at +121.
- Condition: oracle = the Team Sheet arrows (`oracle/team-sheet.jpg`): the 12 bench players plus STALLMAN, BOTNET, LOUIS ROSSMANN, TECHTUBERS and NO TIME FOR LOVE. Searching name−300…name+336 over every 3-bit field: 17/17 at name+271, shift 0; next best 7/17. Values 0x11–0x14 (`0x10 | ordinal`, as PES 2019).
- M2 pre-game: the same base 7ffffd300000 and the same pair, name and entry offsets.

## Stats table (M1, 22:02)

```
$ for every hit region < 256 MiB: dump; find_stats_blocks 721; 749
7f6b0000 190000 g=[[505284, 23, 8500]] sp=[[871444, 23, 8500]]
(other regions: strides 4, 8, 36, 60, 72, 160, 1008 - not per-player tables of this shape)
```

Stats table: region 0x190000; home 0x7B5C4, away 0xD4C14, stride 8500, away − home 0x59650. M2: base 7f7a0000, same offsets and stride. Both region sizes held in both matches and are recorded.

## Tick rate

Match Time 10 min (`oracle/m1-settings.jpg`). Game Ticks Played: 33376 for full-match players at full time, 370.8 per minute including stoppage (PES 2019: about 356 in play; PES 2017: 320). Finding only; MatchReader corrects it at run time.

Dumps deleted after this task.
