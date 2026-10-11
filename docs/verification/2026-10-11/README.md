# Fresh launches of PES 2017, PES 2019 and PES 2021 (2026-10-11)

One testbot match per version (PES 2017 added the same night), `/g/` vs `/sp/`, Match Time 10, extra time and penalties on, each in a new game launch (not the session the layouts were measured in). Alongside SEN:P-AI 1.3.0 (`eeeada2`): `tools/analyze/seg_sampler.py` dumped both stats blocks every 3 s (read-only, `regions.exe dump`), `tools/analyze/hud_clock.py` read the HUD clock, and the full-time pages were captured from OBS. Results: PES 2017 0–2, PES 2019 0–3, PES 2021 3–1, so none went to extra time.

## Results

| Check | PES 2019 | PES 2021 |
|---|---|---|
| Team table offset in its 0x50000 region | **moved**: home pairs at 230008 (measured 2026-10-08: 207720), away 231524 (209236); table start 0x38168 instead of `GameLayout.cpp`'s 0x32A58. Side stride 1516, markers and IDs unchanged | unchanged: pairs at 220148 / 221828, as measured, though the region's base differs |
| SEN:P-AI attaches | **no**: stays in the Teams state for the whole match (its fixed-offset read finds no table), so no events and no `.sen` | yes: teams, stats and events as in `../pes21/` |
| Stats blocks at the measured offsets | yes (0x7B5A4 / 0xD18EC, player IDs 72101… / 74901…) | yes (0x7B5C4 / 0xD4C14) |
| u32 before each stats entry's player ID | 0xFFFD on every home entry, 0xFFFE on every away entry | same |
| Player Rating (tail +0x48) vs the Player Ratings page | entry+0x17EC equals the page for all 22 players (`ratings.tsv`, `pes19-ratings.jpg`) | entry+0x1930 equals the page for all 22 players (`ratings.tsv`, `pes21-ratings.jpg`) |
| 9-bucket counters vs the HUD clock | 15-minute periods: 0 = 0–15, 1 = 15–30, 2 = 30–45 and first-half stoppage (passes at the HUD's 45:59 and 46:29), 3 = 45–60, 4 = 60–75, 5 = 75–90 and stoppage (`pes19-buckets.txt`) | the same boundaries (`pes21-buckets.txt`) |
| Buckets 6–7 (extra time) | not observed | not observed |

`*-buckets.txt` is `seg_report.py` over the samples: one line per 3 s sample where a counter changed, with the latest HUD reading and its age; each bucket's first line marks the boundary to within one sample. The raw samples (127 MB per match) are not committed; `seg_sampler.py` reproduces them.

## Heatmap grids ("Play Area Grid", 140 × u32)

`tools/analyze/grid_report.py` over the same samples (`pes17-grid.txt`, `pes21-grid.txt`):

| | PES 2017 (entry+0x1034) | PES 2021 (entry+0x1938) |
|---|---|---|
| Populates, cumulative | yes; no cell decreased in 327 samples | yes; no cell decreased in 364 samples |
| Shape | 14 rows × 10, row-major, all 140 values are cells | 14 rows × 10, row-major, but the 140th position is not a cell; value 140 = sum of the others (±1 in flight), a sample count |
| Rows | row 0 at the player's own goal, both sides, both halves: both goalkeepers stay in rows 0–2 all match (checked mid-second-half and at full time) | same |
| Rate | ≈630 per full-match player (one per ≈48 ticks) | ≈1270 (one per ≈27 ticks) |
| Column 0's touchline | not determined | not determined |

## PES 2017: the unofficial fork's pointer chain

`tools/analyze/chain17.py` follows the fork's PES 2017 profile (`root = *(0x400000 + 0x21A9E68)`; readiness `*(*(root + 0x124) + 0x1168)`; stats base `*(root + 0x2890) + 0x317FC`, home entry `+0x3804`) and compares it with the scan. In the pre-game menu the root is 0 (`pes17-chain-pregame.txt`); 60 s into the match the readiness flag is 1 (the profile says 0 = live) and `*(root + 0x2890)` is 0x8000, so the derived home entry 0x3D000 holds no player while the scan finds the home block at 0x66505010 (`pes17-chain-live.txt`). The profile does not hold on this executable.

PES 2017's buckets match PES 2019's and 2021's (`pes17-buckets.txt`). SEN:P-AI found teams and stats at the layout's fixed offsets on PES 2017 with the `locateTeamTable` build.

## The PES 2019 team table, fixed

`PES2019_LAYOUT.teamTableOffset` holds only for the launch it was measured in. Over five launches of PES 2019 the table started at 0x32A58 (2026-10-08), 0x38168, 0x2B5B8, 0x2F218 and 0x2F388 inside its 0x50000 region, with the same layout each time. `StatTableReader`'s `locateTeamTable` now tries the layout's offset first (where PES 2017 and PES 2021 have kept it in every launch seen) and otherwise searches the region for the table's signature: a home pair {0xFFFD, a player of the team at `teamIdOffset`} at slot 0, confirmed by the two-team count `countTeamPlayerEntries` already used.

Verified on the rebuilt exe, each in a fresh launch:

| Launch | Teams | Table at | Result |
|---|---|---|---|
| testbot | /g/ vs /sp/ | 0x2B5B8 | Teams Changed (pre-game) |
| testbot, attached mid-match | /g/ vs /sp/ | 0x2F218 | Teams Changed, Stats Found, Clock Updated |
| betting rotation | /lgbt/ (730) vs /int/ (733) | 0x2F388 | Teams Changed, Stats Found, Clock Started/Stopped/Updated |

## Executables

The installs launched by rigbot through Heroic (SHA-256, FileVersion):

- `PES2017.exe` `4cd49eacd6edd1391eadca1e18bb8ba7092eef8447b928ebf82be381aa93a330` 1.0.0.0
- `PES2019.exe` `06e980f0a8138b7cc8255c8100b93a33414ba7f309e74fc5368c80a23b4965a5` 1.6.9.2
- `PES2021.exe` `d5faee3ba913463d373d320871e32ce9bc4d6db9b7ea22e53340dd4607e6ee76` 1.1.9.3

The same executables ran the 2026-10-08 measurements and acceptance matches (none was modified since).
