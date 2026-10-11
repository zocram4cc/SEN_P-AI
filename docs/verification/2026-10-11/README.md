# Fresh launches of PES 2019 and PES 2021 (2026-10-11)

One testbot match per version, `/g/` vs `/sp/`, Match Time 10, extra time and penalties on, each in a new game launch (not the session the layouts were measured in). Alongside SEN:P-AI 1.3.0 (`eeeada2`): `tools/analyze/seg_sampler.py` dumped both stats blocks every 3 s (read-only, `regions.exe dump`), `tools/analyze/hud_clock.py` read the HUD clock, and the full-time pages were captured from OBS. Results: PES 2019 0–3, PES 2021 3–1, so neither went to extra time.

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

## Consequence for the PES 2019 layout

`PES2019_LAYOUT.teamTableOffset` is valid only for the launch it was measured in. A reader has to locate the table by its pairs (`find_team_table.py`'s signature: 0xFFFD/0xFFFE markers with one team's player IDs) inside the 0x50000 region. Not fixed in this commit.

## Executables

The installs launched by rigbot through Heroic (SHA-256, FileVersion):

- `PES2017.exe` `4cd49eacd6edd1391eadca1e18bb8ba7092eef8447b928ebf82be381aa93a330` 1.0.0.0
- `PES2019.exe` `06e980f0a8138b7cc8255c8100b93a33414ba7f309e74fc5368c80a23b4965a5` 1.6.9.2
- `PES2021.exe` `d5faee3ba913463d373d320871e32ce9bc4d6db9b7ea22e53340dd4607e6ee76` 1.1.9.3

The same executables ran the 2026-10-08 measurements and acceptance matches (none was modified since).
