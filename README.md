# SEN:P-AI
A program for extracting stats from PES17

This project is released under the GNU GPLv3. See LICENSE.txt for more details.

## This fork

Supported games: PES 2017 (`PES2017.exe`, behaviour identical to upstream 1.2.6) and PES 2019 (`PES2019.exe`). PES 2021 is being measured. The game is detected from the running process. The stat catalog is fixed by the first game attached or `.sen` opened in a run.

On Linux, run SEN:P-AI in the **game's** Wine prefix, so it shares the game's wineserver:

    WINEPREFIX="<the game's prefix>" wine build/release/SEN_P-AI.exe

Build (Windows Qt 5.15.2 / MinGW 8.1 under Wine, see `docs/verification/TOOLCHAIN.md`):

    QT_WIN=<aqtinstall output dir> tools/build-win.sh

Measurements and verification:

- `docs/measurements/pes17/calibration.md`: the analysers re-derive every PES 2017 constant
- `docs/measurements/pes19/layout.md`, `catalog.md`: PES 2019 memory layout and stat catalog
- `docs/verification/SUMMARY.md`: acceptance results; `QUESTIONS.md`: findings and deviations
- `tools/`: read-only discovery (`regions.c`, `analyze/`) and verification (`senpai_tap.c`, `diff_events.py`, `accept.py`)
