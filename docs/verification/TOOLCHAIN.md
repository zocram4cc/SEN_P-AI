# Toolchain

| Component | Version | Source |
|---|---|---|
| aqtinstall | 3.3.0 (PyPI upload 2025-06-02, >7 days before install on 2026-10-08) | `$AQT_VENV` |
| Qt | 5.15.2 `win64_mingw81` | `aqt install-qt windows desktop 5.15.2 win64_mingw81 -O $QT_WIN` |
| MinGW | 8.1.0 x86_64 posix-seh rev0 (`qt.tools.win64_mingw810`) | `aqt install-tool windows desktop tools_mingw qt.tools.win64_mingw810 -O $QT_WIN` |
| Wine | wine-11.19 (Staging), `/usr/bin/wine` | system |
| Win32 C tools | `x86_64-w64-mingw32-gcc` 16.2.0 | system |
| Python | `$RIG_VENV` (pytest, numpy, PyYAML already installed) | rig |

Build: `tools/build-win.sh` (Wine prefix `$BUILD_PREFIX`, separate from the game prefixes).

Build-script notes (toolchain, not source):

- `CONFIG+=c++14` is passed to qmake. The `.pro` says `c++11`, but `Match.cpp` uses generic lambdas; MSVC, upstream's compiler, defaults to C++14.
- `windeployqt` is replaced by an explicit copy of the Qt and MinGW runtime DLLs plus the `qwindows` and `qwindowsvistastyle` plugins: windeployqt classifies aqt's unstripped MinGW plugins as "debug" and refuses to deploy the platform plugin.

## Path placeholders used in these docs

Machine paths are written as variables; set them for your machine.

| Variable | Meaning |
|---|---|
| `$RIG` | the rig's working directory (rigbot, venvs, dumps) |
| `$RIGBOT` | the rigbot checkout; `tools/analyze/edit_names.py` and `hud_clock.py` read it from the environment |
| `$RIG_VENV` | rigbot's Python virtualenv |
| `$RIG_DOCS` | rig-side docs (the plan, spec and testbot scenario) |
| `$SENPAI`, `$SENPAI_BASELINE` | this checkout, and a worktree of tag `baseline-pes17` |
| `$QT_WIN`, `$AQT_VENV` | aqtinstall's output directory and its virtualenv; `tools/build-win.sh` requires `QT_WIN` |
| `$BUILD_PREFIX` | the Wine prefix used only for building (default `~/.local/share/wineprefixes/senpai-build`) |
| `$DUMPS` | scratch directory for memory dumps (never committed) |
| `$HEROIC_PREFIXES` | Heroic's Wine prefix root; games run in `default`, `default/Pro Evolution Soccer 2017`, `default/eFootball PES 2021` |
