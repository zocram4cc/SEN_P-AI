# PES 2019 stat catalog (Task 12)

Inputs: full-time dumps of the stats table at `MATCH_FINISH` of M1 (19:49, /g/ 3–4 /sp/) and M2 (20:16, 0–3), and the Team Stats and Match Events pages captured by `ftcapture.sh` (`oracle/`).

```
$ block_profile.py ft1/stats_ft.bin 505252 23 858348 23 8176 4 0x17A4 > profile1.json   # 168 u32x9 blocks
$ block_profile.py ft2/stats_ft.bin 505252 23 858348 23 8176 4 0x17A4 > profile2.json
$ align_catalog.py anchors.yaml --check ft1/stats_ft.bin:505252:23:858348:23 ft2/stats_ft.bin:505252:23:858348:23 > catalog.yaml
$ emit_catalog.py catalog.yaml > src/catalogs/Pes19Stats.cpp
```

The entry has the PES 2017 shape: u32 player ID, then u32×9 blocks from 0x4, then a tail. There are 168 blocks (PES 2017: 113), so the tail starts at 0x17A4 (PES 2017: 0xFE8). Entry size 8176 (PES 2017: 4784).

## Rule 1: anchors

Each anchor is the only block whose (home, away) sums equal the oracle in **both** matches (`anchors.yaml` lists the numbers):

| Stat | PES 2017 block | PES 2019 block | Offset |
|---|---|---|---|
| Goals Scored | 0 | 0 | 0x0004 (also per player = Match Events scorers) |
| Assists | 4 | 4 | 0x0094 (per player = Match Events assists) |
| Shots | 5 | 6 | 0x00DC |
| Shots on Target | 10 | 17 | 0x0268 |
| Passes | 13 | 22 | 0x031C |
| Passes Made | 14 | 23 | 0x0340 (0x0A24 also fits; 0x0340 is adjacent to Passes as in PES 2017) |
| Crosses | 21 | 30 | 0x043C |
| Tackles Won | 38 | 50 | 0x070C (the page's "Tackles" is Tackles Won, PES 2017 calibration) |
| Fouls | 43 | 55 | 0x07C0 |
| Free Kicks | 49 | 61 | 0x0898 |
| Corner Kicks | 51 | 63 | 0x08E0 |
| Interceptions | 62 | 78 | 0x0AFC |
| Shots Faced | 109 | 129 | 0x1228 (= opponent's Shots) |
| Shots Faced On Target | 110 | 130 | 0x124C (= opponent's On Target) |
| Saves | 111 | 131 | 0x1270 |

The Team Stats page shows "Fouls (Offside)" with offsides 0–0 in both matches, which fits 39 blocks; Offside is placed by rule 2 instead.

## Rule 2: alignment between anchors

| Between | PES 2017 blocks | PES 2019 blocks | Result |
|---|---|---|---|
| Goals Scored – Assists | 3 | 3 | Own Goals Scored, Free kicks scored, Penalties scored in order |
| Assists – Shots | 0 | 1 | 1 unknown |
| Shots – Shots on Target | 4 | 10 | unknowns; Headers, Shots (Strong Foot), Shots (Weak Foot) absent |
| Shots on Target – Passes | 2 | 4 | unknowns; Free kicks shot, Penalty kicks shot absent |
| Passes Made – Crosses | 6 | 6 | Low Passes … Lofted/High Passes Made in order |
| Crosses – Tackles Won | 16 | 19 | unknowns; Crosses Made, Ground/Aerial Passes (Made), Low/Chipped Thru Balls (Made), Tackles absent |
| Tackles Won – Fouls | 4 | 4 | ?UNKNOWN 40–42, Clearances in order |
| Fouls – Free Kicks | 5 | 5 | Fouls Offside, Yellow Cards, Red Cards, ?48, ?49 in order |
| Free Kicks – Corner Kicks | 1 | 1 | in order |
| Corner Kicks – Interceptions | 10 | 14 | unknowns; Touches absent |
| Interceptions – Shots Faced | 46 | 50 | unknowns |
| after Saves | 1 | 36 | unknowns |

Plausibility of the in-order mappings: Yellow Cards (0x0808) is (0, 1) in M1 and (0, 0) in M2; Red Cards and Own Goals Scored are 0 in both, consistent with no red cards and no own goals on the Match Events pages.

## Rule 3: invariants

`align_catalog.py --check` over all 46 entries of both matches: no violations (Passes Made ≤ Passes, Low Passes Made ≤ Low Passes, Through Balls Made ≤ Through Balls, Lofted/High Passes Made ≤ Lofted/High Passes, Tackles Won and Crosses have no mapped partner, Shots on Target ≤ Shots, Saves ≤ Shots Faced On Target ≤ Shots Faced).

## Rule 4: segments

Non-zero segments in both 90-minute matches: 0–5. Segments 6–8 not observed (extra time is off in the scenario; no forced draw available).

## Rule 5: tail

| Field | Offset | Evidence |
|---|---|---|
| First Minute on Pitch (sint8) | 0x17A4 | −1 bench, 0 starters; subs 22/42/71 (M1) and 21/36/66 (M2) = Match Events minutes |
| Last Minute on Pitch (sint8) | 0x17A5 | the current minute (16 at HUD 16:17) for everyone on the pitch; the sub-off minute for those replaced |
| Current Playing Position (uint32) | 0x17B0 | GK 0, RB 3, CMF 5, LMF 6, RMF 7, AMF 8, CF 12 = formation; 13 on the bench |
| Game Ticks Played (uint32×13) | 0x17B4 | 13 per-position counters (Stallman: GK slot; Torvalds, APOLOGIZE: CB slot); frozen while paused; 0x17E8 is a different field |
| Realtime (sec) on Pitch (uint32) | 0x1A20 | starters 612–615 s; APOLOGIZE 146 (off 22'), Thinkpad 277 (off 42'), WOBBIE 469 (on 22') |

Absent for lack of a clear oracle:

- **Player Rating:** float at 0x17EC holds plausible ratings (Terry A. Davis 7.0 with two goals). The bot never opens a Player Ratings page on PES 2019, so it stays absent; see QUESTIONS.
- **Stamina:** reads 0 at PES 2017's relative position.
- **Distance Dribbled, Play Area Grid:** no oracle.

Every other tail byte is `?UNKNOWN`: u32 words, plus two u8 flags around the sint8 pair.

## Result

711 entries: 34 named with offsets, 20 PES 2017 names absent (offset −1), and the rest `?UNKNOWN n`. All 16 mandatory names have offsets. Count 711 ≠ 175.
