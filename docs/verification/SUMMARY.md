# Verification summary (spec section 7)

| Criterion | Evidence | Result |
|---|---|---|
| 7.1 PES 2017 parity, fork vs upstream | `pes17-parity/README.md` | PASS: `diff_events.py` exit 0, `finalStats` byte-identical |
| 7.1 Phase 0 Wine gate (upstream on PES 2017) | `pes17-baseline/README.md` | PASS |
| 7.2 PES 2019 acceptance | `pes19/README.md` | PASS except two clock readings around one substitution; upstream shows the same on PES 2017 (QUESTIONS: "sub minute ±1") |
| 7.2 PES 2021 acceptance | none yet | PENDING: team table located (40 slots, 392-byte entries, condition at entry+331); stats table and catalog need live matches, blocked while rigbot's PES 2021 testbot is being fixed |
| 7.3 Brute force | `brute-force/pes17-*`, `brute-force/pes19-*` | PASS on PES 2017 and PES 2019; PES 2021 pending |
| 7.4 Reproducible discovery | `../measurements/pes19/layout.md`, `catalog.md`, `anchors.yaml`; evidence comments in `src/GameLayout.cpp` and `src/catalogs/Pes19Stats.cpp` | PASS for PES 2019 (two matches, same offsets) |
| 7.5 Read-only | `grep -rn "WriteProcessMemory\|VirtualProtectEx\|PROCESS_VM_WRITE\|PROCESS_ALL_ACCESS" src tools` → nothing (exit 1); both `OpenProcess` calls use `PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ` | PASS |

The parity re-run on the final build (plan Task 14 step 2) is pending with PES 2021: the final build adds the PES 2019 layout to the search list, and the `findPid` first-entry fix.

## Findings for the owner

Details in `QUESTIONS.md`.

- **Segments.** PES 2019 uses segments 0–5 in 90-minute matches, as PES 2017; segments 6–8 were not observed (extra time off).
- **Tick rate.** PES 2019 counts ≈356 ticks per game minute at Match Time 10 (PES 2017: 320). MatchReader's own correction settles at 352 and stores match length 11 in `.sen`.
- **Absent stats.** PES 2019 has 20 PES 2017 names absent, among them Player Rating (very likely at entry+0x17EC, but no ratings page oracle), Stamina, Tackles, Touches, and the Ground/Aerial/Low/Chipped pass families. Absent stats read as a constant 0, not NaN.
- **Condition byte.** PES 2019 and PES 2021 store `0x10 | ordinal` (PES 2017: top 3 bits). Read raw; unused by any output.
- **Region sizes.** Stable across two matches each: PES 2019 team 0x50000 and stats 0x190000; PES 2021 team 0x50000.
- **40 squad slots** in PES 2019 and PES 2021 team tables; the reader keeps upstream's 32.
- **Source edits beyond the spec's three:** `Match.cpp` (include, `template` keyword), `main.cpp` (null-safe log handler), `findPid` (first snapshot entry).
- **Upstream behaviours left as is:** the clock jump at substitutions; "mode" of Last Minute on Pitch is really the max.
- **Wine:** one X11 `BadWindow` abort in about 4 h of runtime.
