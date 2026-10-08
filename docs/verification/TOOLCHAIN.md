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
