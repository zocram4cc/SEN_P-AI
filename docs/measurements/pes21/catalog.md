# PES 2021 stat catalog (Task 12)

Inputs: stats-table dumps at `MATCH_FINISH` of M1 (1–0) and M2 (0–0 at 90:00), a third dump after M2's shoot-out (5–4), and the Team Stats, Player Ratings and Match Events pages of both (`oracle/`).

```
$ block_profile.py stats_ft.bin 505284 23 871444 23 8500 4 0x18E8 > profile.json        # 177 u32x9 blocks
$ align_catalog.py anchors.yaml --check <M1 dump>:505284:23:871444:23 <M2 dump>:505284:23:871444:23 > catalog.yaml
$ emit_catalog.py catalog.yaml > src/catalogs/Pes21Stats.cpp
```

Same shape as PES 2017 and PES 2019. There are 177 blocks (PES 2019: 168), so the tail starts at 0x18E8. Entry size 8500.

## Rule 1: anchors (`anchors.yaml`)

Blocks equal to PES 2019's for every anchor up to Interceptions: Goals 0, Assists 4, Shots 6, On Target 17, Passes 22, Made 23, Crosses 30, Tackles Won 50, Fouls 55, Free Kicks 61, Corners 63, Interceptions 78. The goalkeeper blocks moved by two: Shots Faced 131, On Target 132, Saves 133 (PES 2019: 129–131).

Unique in both matches except:

- Fouls: blocks 39 and 55 both fit (0,1)/(0,1).
- Interceptions: blocks 78 and 153 both fit.
- Passes Made: blocks 23 and 72 both fit.

Each takes PES 2019's position, which keeps PES 2017's order.

## Rule 2: alignment

The gaps up to Interceptions are the same as in PES 2019. That maps Own Goals Scored, Free kicks scored and Penalties scored; Low Passes … Lofted/High Passes Made; Clearances; and Fouls Offside, Yellow Cards and Red Cards in order. All other gaps differ from PES 2017 and become `?UNKNOWN`. 19 PES 2017 names are absent (the list is in `catalog.yaml`).

## Rule 3: invariants

One violation over both matches: **Saves 2 > Shots Faced On Target 1** for STALLMAN in M2. The game's own Team Stats page shows the same (/g/ Saves 2, /sp/ Shots on Target 1), so the invariant does not hold in PES 2021's data, and both anchors stay. Every other pair holds.

## Rule 4: segments

Segments 0–5 in both 90-minute matches. **After the shoot-out, segment 8 is set**: Goals Scored becomes 5–4 in segment 8, and Shots and Shots on Target also count the kicks. This matches MatchReader's `segment == 8` = penalties. Segments 6–7 (extra time) were not observed.

## Rule 5: tail

The same layout relative to the tail start as PES 2019:

- First/Last Minute on Pitch at +0/+1 (0x18E8/0x18E9);
- Current Playing Position at +0xC;
- Game Ticks Played ×13 at +0x10;
- Player Rating at +0x48;
- Realtime on Pitch at +0x27C.

Player Rating has an oracle here: it equals the Player Ratings page for 8 players of M1.

## Result

719 entries: 35 named with offsets, 19 absent, the rest `?UNKNOWN n`. All 16 mandatory names have offsets. Count 719 ≠ 175, ≠ 711.
