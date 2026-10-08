# Questions and deviations for the owner

## Source edits beyond the spec's three portability edits (spec 2.2)

The spec allows exactly three MinGW portability edits plus the `clock_updated` declaration. Building and running needed four more. None changes behaviour on a build where upstream already worked:

1. `src/Match.cpp`: `#include <cstring>` (MSVC pulled it in transitively for `std::strncpy`/`std::strncmp`).
2. `src/Match.cpp:558,577`: `f.get<uint32_t>()` becomes `f.template get<uint32_t>()`. `f` has a dependent type; MSVC accepts the missing `template` keyword, GCC cannot parse it and has no flag to allow it.
3. `src/main.cpp:24-28`: the debug message handler did `std::strchr(context.function,'(')-1` unconditionally. Messages emitted inside the release Qt DLLs carry no context (`function == NULL`), so any Qt-internal warning crashed the handler. Under Wine, Qt warns `EnableNonClientDpiScaling() failed` inside `WM_NCCREATE`; the crash there made `CreateWindowEx` fail and the main window never appeared. The handler now treats a missing function name as empty; such messages are logged as `...(line   0 of )`. Messages with a function name are formatted exactly as before.
4. `src/StatTableReader.cpp` `findPid`: upstream called `Process32First` and then compared only the entries from `Process32Next`, so the first snapshot entry was never checked. On Windows that entry is always `[System Process]` (pid 0). Under Wine, the game launched first in a fresh wineserver is pid 32 and is the first entry (seen live: PES 2019, `tools`-side probe listing `32 [PES2019.exe]` first), so SEN:P-AI never found it. The loop now compares the first entry too; on Windows nothing changes.

Cosmetic, left as upstream: with GCC's `__PRETTY_FUNCTION__`, constructors have no return type before the name, so the debug log prints e.g. `tatTableReader::StatTableReader` (first character dropped). The format code is upstream's and unchanged.

## Plan assumptions that did not hold on the rig

- `/sp/`'s team ID is 750 in the PES 2017 EDIT and 749 in PES 2019 and PES 2021 (`tools/analyze/edit_names.py`), not 794.
- SEN:P-AI status texts go to the UI only; the debug log does not mirror them. Status was checked with window screenshots.
- The testbot log has no `last_clock` lines and logs substitutions at their *scheduled* minute ("sub at 15'"); the game applies a sub at the next stoppage. Neither is a ±1-minute oracle for `Player Sub` or `Clock Updated`. `tools/analyze/hud_clock.py` records the HUD clock (OCR through rigbot's own clock region) with wall timestamps instead.
- `diff_events.py` as planned applied `--tap` to both inputs, so log-vs-tap comparison (Task 3 Step 5) crashed; it now detects each file's format.
- `edit_names.py` as planned resolved squads by record ID for every version; that is only valid for PES 2017. It now uses the same resolution as `rigbot.core.editfile.parse_squads`.

## Spec 7.2 "sub minute ±1" conflicts with the 1:1 algorithm

Upstream's clock estimate can jump ahead at a substitution made during a stoppage. PES 2017 parity match (`pes17-parity/`): at 18:50:36 `Clock Stopped` 25.12 (Corner kick); at 18:50:54 `Player Sub` and `Clock Updated` 27.91 while the HUD read 25:05 before and 25:07 after; at 18:51:08 `Clock Stopped` 28.88 with the HUD at 25:51. The upstream build and the fork produce the same events (parity holds), so `tools/accept.py` reports `sub minute 27.9 vs HUD 25..25` for **upstream itself**. Since spec 4.4 forbids changing the algorithm, a sub minute outside ±1 is reported as this finding when the same pattern (clock jump at the sub, during a stoppage) is visible in the events; it is not a porting error. Owner: confirm, or relax 7.2 for subs.

## Absent stats read as 0, not NaN (spec 4.5 vs 4.4)

Spec 4.5 says a stat with offset -1 reads as NaN. With MatchReader unchanged (spec 4.4) that breaks the match: `collectStatChanges` tests `curr != prev`, which is always true for NaN, so every absent stat would log 9 changes per player per tick, and its segment search (`for(segment = 8; ... getSegmentDouble(...) == 0; --segment)`) never matches NaN, leaving segment 8 = penalties, so the clock would read `BENULDIES`. `PESstat::getSegmentDouble`/`getSegmentValue` therefore return 0 for offset -1: constant, never a change, written as 0 to `.sen`. Absent stats are `shown = false, logged = false`. PES 2017 has no absent stats, so its behaviour is unchanged.

## PES 2019 findings (data differences, algorithm unchanged)

- **Tick rate.** At Match Time 10 min, PES 2019 counts ≈356 ticks per game minute (PES 2017: 320 = 10 × 32). MatchReader's own ±32 correction settles at 352, so the `.sen` header stores match length 11. Measured in `measurements/pes19/layout.md`.
- **40 squad slots.** The team table has 40 player pairs and 40 player entries per side (PES 2017: 32). SEN:P-AI keeps reading 32, as upstream (`MAX_PLAYERS`, `teamInfo::player[32]`); a squad above 32 players would be truncated.
- **Condition byte** at entry+207 holds `0x10 | ordinal` (0 purple … 4 red) instead of PES 2017's 0x00–0x80. It is read raw; nothing uses it.
- **Player Rating** is very likely the float at entry+0x17EC (PES 2017's relative position; 7.0 for a two-goal scorer). The rig's bot never opens the Player Ratings page on PES 2019, so by the catalog rules it is absent. Owner: open that page once (or allow the structural evidence) to enable it.

## Wine X11 abort

The PES 2019 acceptance instance exited during the following match with `X Error of failed request: BadWindow (invalid Window parameter)`, `X_UnmapWindow`: Xlib's default handler ending the process inside Wine's X11 driver. Its debug log stops mid-tick. Observed once in about 4 h of runtime across instances. If it recurs, running SEN:P-AI with Wine's Wayland driver is the first thing to try.

## The "mode" of Last Minute on Pitch is a max

`MatchReader::calcUpdateTime` (`MatchReader.cpp:285-293`) calls `std::max_element` over an `unordered_map<int,int>` of minute → count. `pair` compares the key first, so it returns the largest minute, not the most common one. With 24 bench entries at −1 and 22 players on the pitch, a real mode would be −1, so the max is what makes the clock work. Left as upstream (spec 4.4).
