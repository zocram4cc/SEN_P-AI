#!/bin/bash
# Build SEN_P-AI.exe with Windows Qt 5.15.2 / MinGW 8.1 under Wine.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
QT=$QT_WIN/5.15.2/mingw81_64
MW=$QT_WIN/Tools/mingw810_64
export WINEPREFIX=${BUILD_PREFIX:-$BUILD_PREFIX}
export WINEDEBUG=-all
export WINEPATH="$(winepath -w "$QT/bin");$(winepath -w "$MW/bin")"
mkdir -p "$ROOT/build"
cd "$ROOT/build"
# MSVC (upstream's compiler) defaults to C++14; Match.cpp uses generic lambdas.
wine "$QT/bin/qmake.exe" "$(winepath -w "$ROOT/SEN_P-AI.pro")" -spec win32-g++ "CONFIG+=release c++14"
wine "$MW/bin/mingw32-make.exe" -j"$(nproc)"
# windeployqt skips aqt's unstripped MinGW plugins as "debug"; copy the runtime explicitly.
R="$ROOT/build/release"
mkdir -p "$R/platforms" "$R/styles"
cp -u "$QT"/bin/Qt5{Core,Gui,Network,Widgets}.dll "$MW"/bin/{libgcc_s_seh-1,libstdc++-6,libwinpthread-1}.dll "$R/"
cp -u "$QT/plugins/platforms/qwindows.dll" "$R/platforms/"
cp -u "$QT/plugins/styles/qwindowsvistastyle.dll" "$R/styles/"
echo "built: $ROOT/build/release/SEN_P-AI.exe"
