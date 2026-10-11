#ifndef COMMON_H
#define COMMON_H
//Version
#define MAJOR 1
#define MINOR 3
#define PATCH 0

#include "Match.h"
#include "PipeServer.h"
#include "SettingsDialog.h"
#include "StatSelectionDialog.h"
#include "StatsInfo.h"
#include "StatTableReader.h"
#include "TeamDataTable.h"
#include <QDebug>
#include <QString>

#define dbgReturn(...) do{ qDebug("Function returned"); __VA_ARGS__; }while(false)

// Rigdio's own default (webserver_host:webserver_port).
#define RIGDIO_DEFAULT_URL "http://127.0.0.1:31338"

#endif // COMMON_H
