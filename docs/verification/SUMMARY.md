# Verification summary (spec section 7)

| Criterion | Evidence | Result |
|---|---|---|
| 7.1 PES 2017 parity, fork vs upstream | `pes17-parity/README.md` (refactor build), `pes17-parity-final/README.md` (final build `2518131`) | PASS both: `diff_events.py` exit 0, `finalStats` byte-identical; final run even has identical clock-event counts |
| 7.1 Phase 0 Wine gate (upstream on PES 2017) | `pes17-baseline/README.md` | PASS |
| 7.2 PES 2019 acceptance | `pes19/README.md` | PASS except the clock readings around one substitution, which upstream shows on PES 2017 too (QUESTIONS: "sub minute ±1") |
| 7.2 PES 2021 acceptance | `pes21/README.md` | PASS, same single exception; run with the scenario's `best_xi: false` because rigbot's PES 2021 best-XI step was failing |
| 7.3 Brute force | `brute-force/pes17-*`, `pes19-*`, `pes21-*` | PASS on all three |
| 7.4 Reproducible discovery | `../measurements/pes19/`, `../measurements/pes21/` (`layout.md`, `catalog.md`, `anchors.yaml`, `layout.yaml`); evidence comments in `src/GameLayout.cpp` and the generated catalogs | PASS: every offset was the same in two matches per version (one game launch) |
| Fresh launch (2026-10-11) | `2026-10-11/README.md` | PES 2021 PASS. PES 2019: the team table moved inside its region in each new launch, so the fixed-offset reader never attached; **fixed** by a signature search over the region, verified in three more launches (testbot and betting teams); stats offsets held |
| 7.5 Read-only | `grep -rn "WriteProcessMemory\|VirtualProtectEx\|PROCESS_VM_WRITE\|PROCESS_ALL_ACCESS" src tools` → nothing (exit 1); both `OpenProcess` calls (`src/StatTableReader.cpp`, `tools/regions.c`) use `PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ`; the built exes import no write/inject API; under Wine a write through such a handle is refused with error 5 (access denied) | PASS |

## Findings for the owner

Details in `QUESTIONS.md`.

- **Segments.** The nine buckets are 15-minute periods of the game clock (0 = 0–15 … 5 = 75–90; each half's stoppage time stays in its last bucket), measured against the HUD on PES 2019 and PES 2021 (`2026-10-11/`). A PES 2021 shoot-out writes segment 8 (MatchReader's penalties rule). Segments 6–7 (extra time) were not observed.
- **PES 2019 team table offset varies by launch** (0x32A58 on 2026-10-08; 0x38168, 0x2B5B8, 0x2F218, 0x2F388 on 2026-10-11); `locateTeamTable` finds it by signature. PES 2021's held across two launches.
- **Player Rating** is at tail +0x48 on both versions and equals the Player Ratings page for all 22 players of a 2026-10-11 match on each (PES 2019 entry+0x17EC, still absent from `Pes19Stats.cpp`).
- **Tick rate.** At Match Time 10: PES 2017 320 ticks per game minute, PES 2019 ≈356, PES 2021 ≈371 (including stoppage). MatchReader's own ±32 correction absorbs it; `.sen` stores the corrected match length.
- **Absent stats.** PES 2019: 20 PES 2017 names absent, among them Player Rating (very likely entry+0x17EC, but no ratings-page oracle on that rig run). PES 2021: 19 absent; Player Rating is mapped from the Player Ratings page. Both lack Stamina, Tackles, Touches and the Ground/Aerial/Low/Chipped pass families. Absent stats read as a constant 0, not NaN.
- **Rule 3 does not hold in PES 2021's data:** Saves can exceed Shots Faced On Target, and the game's own Team Stats page shows the same.
- **Condition byte.** PES 2019 and PES 2021 store `0x10 | ordinal` (PES 2017: top 3 bits). Read raw; unused by any output.
- **Region sizes** were stable across two matches each: team 0x50000 and stats 0x190000 on both PES 2019 and PES 2021. Entry sizes: 4784 / 8176 / 8500.
- **Catalogs:** 175 / 711 / 719 entries. The 16 mandatory names are mapped in all three.
- **40 squad slots** in PES 2019 and PES 2021 team tables; the reader keeps upstream's 32.
- **Source edits beyond the spec's three:** `Match.cpp` (include, `template` keyword), `main.cpp` (null-safe log handler), `findPid` (first snapshot entry).
- **Upstream behaviours left as is:** the clock jump at substitutions; "mode" of Last Minute on Pitch is really the max.
- **Wine:** one X11 `BadWindow` abort in about 4 h of runtime.
