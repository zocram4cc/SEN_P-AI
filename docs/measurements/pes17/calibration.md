# Analyser calibration on PES 2017 (Task 9)

- Date: 2026-10-08, live match 18:46–19:09 local. Testbot scenario match 2, `/g/` (721) vs `/sp/` (750), final 2–3.
- Prefix: `$HEROIC_PREFIXES/default/Pro Evolution Soccer 2017`. All tools read-only (`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`).
- `T=$SENPAI/tools`, run under `WINEPREFIX=$P17 WINEDEBUG=-all`.

## Step 2: regions and the stats table (after kick-off, 18:46)

```
$ wine $T/regions.exe PES2017.exe list > regions.tsv      # 2530 regions
$ wine $T/regions.exe PES2017.exe scan 72101 > hits.tsv   # 35 hits
$ awk '{print $2, $3}' hits.tsv | sort | uniq -c | sort -rn | head
      3 650b0000 60000
      3 63c20000 ff0000
      3 62c30000 ff0000
      3 171f0000 30000
      3 14e50000 20000
      2 664d0000 90000
      ...
$ wine $T/regions.exe PES2017.exe dump 664d0000 0x90000 r_664d0000.bin
$ find_stats_blocks.py r_664d0000.bin 721   ->  [[217104, 23, 4784]]
$ find_stats_blocks.py r_664d0000.bin 750   ->  [[384576, 23, 4784]]
```

| Constant | Expected | Measured |
|---|---|---|
| `statsRegionSize` | 589824 (0x90000) | 0x90000 |
| `homeStatsOffset` | 0x35010 | 217104 = 0x35010 |
| `awayStatsOffset` | 0x5DE40 | 384576 = 0x5DE40 |
| `awayStatsDiff` | 0x28E30 | 167472 = 0x28E30 |
| `statEntrySize` | 4784 | 4784 |

## Step 3: team table

```
$ wine $T/regions.exe PES2017.exe dump 650b0000 0x60000 r_650b0000.bin
$ find_team_table.py r_650b0000.bin 721 /g/   -> [{"pairs_at": 342444, "count": 23, "marker": "0xfffd", "name_at": 342200}]
$ find_team_table.py r_650b0000.bin 750 /sp/  -> [{"pairs_at": 343756, "count": 23, "marker": "0xfffe", "name_at": 343512}]
$ edit_names.py pes17 /g/ > g.json; edit_names.py pes17 /sp/ > sp.json
$ player_entries.py r_650b0000.bin g.json     -> {"stride": 232, "name_minus_id": [4, 8], "first_name_at": 346140}
$ player_entries.py r_650b0000.bin sp.json    -> {"stride": 232, "name_minus_id": [4, 8], "first_name_at": 353564}
```

Struct values from `x86_64-w64-mingw32-g++ -I src` (`teamDataTable`): `sizeof` 18736, `awayData` 0x520, `teamName` 0x4, `players` 0xF8, `teamID` 0x1FC, `homePlayers` 0xF30, `awayPlayers` 0x2C30; `playerEntry` 232 bytes, `playerID` 48, `playerName` 56, `playerCondition` 30.

| Constant | Expected | Measured |
|---|---|---|
| `teamRegionSize` | 393216 (0x60000) | 0x60000 |
| home pairs | 0x538B4 + 0x0F8 = 342444 | 342444, marker 0xFFFD |
| away pairs | 0x538B4 + 0x618 = 343756 | 343756, marker 0xFFFE |
| team name | 0x538B4 + 4 = 342200 | 342200 (both sides, +0x520 for away) |
| player stride | 232 | 232 |
| name − ID | 8 | [4, 8]: the entry stores the ID twice (`playerID` at +48, `commentaryID` at +52 equals it). The analyser now lists every common distance. |
| first home name | 0x538B4 + 0xF30 + 56 = 346140 | 346140 |
| first away name | 0x538B4 + 0x2C30 + 56 = 353564 | 353564 |
| condition byte | +30, top 3 bits | +30: 0x8E, 0x41, 0x40 for the first three /g/ players (red, green, green) |

## Step 4: catalog anchors at full time (19:09:09)

`ftcapture.sh` dumped the stats region at `MATCH_FINISH` and saved OBS frames of the full-time pages (Team Stats, Player Ratings, Match Events).

```
$ block_profile.py stats_ft.bin 0x35010 23 0x5DE40 23 4784 4 0x0FE8 > profile.json
```

| Stat (PES 2017 offset) | Team Stats page | Block sums (home, away) | |
|---|---|---|---|
| Goals Scored (0x0004) | 2–3 | (2, 3) | OK |
| Shots (0x00B8) | 13, 13 | (13, 13) | OK |
| Shots on Target (0x016C) | (5), (8) | (5, 8) | OK |
| Fouls (0x0610) | 0, 1 | (0, 1) | OK |
| Fouls Offside (0x0634) | (0), (1) | (0, 1) | OK |
| Corner Kicks (0x0730) | 1, 3 | (1, 3) | OK |
| Free Kicks (0x06E8) | 1, 0 | (1, 0) | OK |
| Crosses (0x02F8) | 12, 8 | (12, 8) | OK |
| Interceptions (0x08BC) | 16, 10 | (16, 10) | OK |
| Saves (0x0FA0) | 4, 4 | (4, 4) | OK |
| Passes Made / Passes (0x01FC / 0x01D8) | "Passes Completed (%)" 81%, 75% | 81%, 75% | OK; the page shows a ratio, not a count |
| Tackles (0x0538) | "Tackles" 5, 5 | (13, 18) | **the page's "Tackles" is Tackles Won** (0x055C) = (5, 5) |

- Segments in use: 0–5 (no extra time played).
- Player Rating (0x1030, float32): equals the Player Ratings page for all 9 visible /g/ players (6.0, 5.5, 6.0, 5.5, 5.5, 6.5, 6.0, 6.0, 7.0).
- First/Last Minute on Pitch (0x0FE8/0x0FE9, sint8): starters 0 / 90.
- Game Ticks Played (0x0FF8, uint32×13): max 30593, only segment 0 used; 339.9 per minute over 90 minutes including stoppage time, consistent with 320 per minute (`matchLength` 10 × 32).

## Consequences for Task 12 (oracle mapping)

- "Tackles" on the Team Stats page anchors **Tackles Won**, not Tackles.
- "Passes Completed (%)" anchors the ratio Passes Made / Passes, not either count.
- On the Team Stats page "Fouls (Offside)" and "Shots (On Target)" carry the second stat in brackets.

Dumps deleted after this step.
