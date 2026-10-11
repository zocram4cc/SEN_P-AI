# SEN:P-AI
A program for extracting stats from PES17

This project is released under the GNU GPLv3. See LICENSE.txt for more details.

## This fork

Supported games: PES 2017 (`PES2017.exe`, behaviour identical to upstream 1.2.6), PES 2019 (`PES2019.exe`) and PES 2021 (`PES2021.exe`). The game is detected from the running process. The stat catalog is fixed by the first game attached or `.sen` opened in a run.

On Linux, run SEN:P-AI in the **game's** Wine prefix, so it shares the game's wineserver:

    WINEPREFIX="<the game's prefix>" wine build/release/SEN_P-AI.exe

Build (Windows Qt 5.15.2 / MinGW 8.1 under Wine, see `docs/verification/TOOLCHAIN.md`):

    QT_WIN=<aqtinstall output dir> tools/build-win.sh

Rigdio: Settings → **Rigdio URL** (e.g. `http://localhost:31338`; empty = off) sends match events to Rigdio's local API (the zocram4cc/rigdio fork):

| SEN:P-AI event | Rigdio call |
|---|---|
| Goal | `POST /api/goal {side, scorer}` (the scorer's goalhorn) |
| Own Goal | `POST /api/goal {side}` for the other side, and `POST /api/event {event: "owngoal", player, minute}` |
| Card | `POST /api/event {event: "yellow"/"red", player, minute}` |
| Player Sub | `POST /api/event {event: "sub", player, minute}` (the player coming on) |
| Clock Stopped (not a goal or half end) | `POST /api/chant {}` with the **Chant at a stoppage** chance |
| Teams Changed | `POST /api/load {home, away}`, only with **Load team exports** ticked |

Teams Changed fires when the teams are picked in the menus, before the anthems. Anthems and the victory anthem have no cue in memory; play those from Rigdio. `--no-rigdio` on the command line turns the option off for that run; rigbot passes it because it drives Rigdio itself.

Measurements and verification:

- `docs/measurements/pes17/calibration.md`: the analysers re-derive every PES 2017 constant
- `docs/measurements/pes19/`, `docs/measurements/pes21/`: `layout.md`, `catalog.md` - memory layout and stat catalog per version
- `docs/verification/SUMMARY.md`: acceptance results; `QUESTIONS.md`: findings and deviations
- `tools/`: read-only discovery (`regions.c`, `analyze/`) and verification (`senpai_tap.c`, `diff_events.py`, `accept.py`)
