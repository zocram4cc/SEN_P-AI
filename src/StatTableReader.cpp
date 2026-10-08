#include "StatTableReader.h"

#include <stdio.h>
#include <tchar.h>
#include <stdint.h>
#include <ctype.h>
#include <algorithm>
#include <Windows.h>
#include <tlhelp32.h>
#include <QDebug>
#include "Common.h"
#include "GameLayout.h"
#include <vector>
#include <cstring>

#define STAT_MEM_STATE MEM_COMMIT
#define STAT_MEM_TYPE MEM_PRIVATE
#define STAT_MEM_PROTEC PAGE_READWRITE

#define teamIdOf(NUM) (NUM/100)
#define isSameTeam(A,B) (teamIdOf(A) == teamIdOf(B))

#define MAX_PLAYERS 32
static int8_t countTableEntries(HANDLE PES, uintptr_t addr, const GameLayout &L) {
    qDebug("Function Entered");
    uint32_t playerID = 0;
    uint32_t maybeID = 0;
    int entries = 0;
    while (entries <= MAX_PLAYERS) {
        if(!ReadProcessMemory(PES, (void*)addr, &maybeID, 4, NULL))
            dbgReturn(return -1);
        if(!(maybeID > L.playerIdMin && maybeID < L.playerIdMax))
            break;
        if(playerID > 0 && !isSameTeam(maybeID,playerID))
            break;
        if(playerID == 0)
            playerID = maybeID;
        entries++;
        addr += L.statEntrySize;
    }
    dbgReturn(return entries);
}



#define TEAM_MEM_STATE MEM_COMMIT
#define TEAM_MEM_TYPE MEM_PRIVATE
#define TEAM_MEM_PROTEC PAGE_READWRITE

static int8_t countTeamPlayerEntries(HANDLE PES, uintptr_t tableAddr, const GameLayout &L){
    qDebug("Function Entered");
    const TeamTableLayout &T = *L.teamTable;
    const size_t words = (T.teamIdOffset - T.pairsOffset) / 4 + 1;   // 66 on PES 2017
    std::vector<uint32_t> home(words), away(words);
    uint8_t count = 0;
    if(!ReadProcessMemory(PES, (void*)(tableAddr + T.pairsOffset), home.data(), words*4, NULL)) return -1;
    if(!ReadProcessMemory(PES, (void*)(tableAddr + T.sideStride + T.pairsOffset), away.data(), words*4, NULL)) return -1;
    for(int i = 0; i < 32; ++i)
        if((home[i*2] & 0xFFFF) == L.homePairMarker && teamIdOf(home[i*2 + 1]) == home[words-1]) count++;
    for(int i = 0; i < 32; ++i)
        if((away[i*2] & 0xFFFF) == L.awayPairMarker && teamIdOf(away[i*2 + 1]) == away[words-1]) count++;
    dbgReturn(return count);
}

static uint32_t readTeamId(const uint8_t *table, const GameLayout &L, bool away){
    const TeamTableLayout &T = *L.teamTable;
    uint32_t id;
    std::memcpy(&id, table + (away ? T.sideStride : 0) + T.teamIdOffset, 4);
    return id;
}

static teamInfo readTeam(const uint8_t *table, const GameLayout &L, bool away){
    const TeamTableLayout &T = *L.teamTable;
    const uint8_t *side = table + (away ? T.sideStride : 0);
    const uint8_t *players = table + (away ? T.awayPlayersOffset : T.playersOffset);
    teamInfo t;
    const char *name = (const char*)(side + T.teamNameOffset);
    t.name = QString::fromUtf8(name, (int)qstrnlen(name, (uint)T.teamNameMax));
    t.ID = readTeamId(table, L, away);
    t.nPlayers = 0;
    for(int i = 0; i < 32; ++i){
        int16_t valid;
        std::memcpy(&valid, side + T.pairsOffset + i*8, 2);
        if(valid != -1){
            const uint8_t *p = players + i*T.playerStride;
            const char *pname = (const char*)(p + T.playerNameOffset);
            uint32_t id; std::memcpy(&id, p + T.playerIdOffset, 4);
            t.player[t.nPlayers++] = {QString::fromUtf8(pname, (int)qstrnlen(pname, (uint)T.playerNameMax)),
                                      id, T.playerConditionOffset == (size_t)-1 ? (uint8_t)0 : p[T.playerConditionOffset]};
        }
    }
    return t;
}

bool StatTableReader::updateProcess(){
    qDebug("Function Entered");
    //Check if process is still opened
    DWORD exitCode = 0;
    if (GetExitCodeProcess(processHandle, &exitCode)) {
        if (exitCode != STILL_ACTIVE) {
            //Process was closed, close handle
            CloseHandle(processHandle);
            processHandle = NULL;
            basePtr = homePtr = awayPtr = teamDataPtr = nullptr;
            emit status_changed(QStringLiteral("SEN:P-AI noticed %1 close").arg(QString::fromWCharArray(_layout->processName)));
            emit table_lost();
            dbgReturn(return false);
        } else {
            dbgReturn(return true);
        }
    } else {
        emit status_changed(QStringLiteral("SEN:P-AI does not have access to Exit Code"));
        dbgReturn(return false);
    }
}

static DWORD findPid(const wchar_t *name){
    DWORD pid = 0;
    PROCESSENTRY32 entry; entry.dwSize = sizeof(PROCESSENTRY32);
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, NULL);
    //Loop through every available proccess and compare its name to the target name
    if (Process32First(snapshot, &entry) == TRUE)
        while (Process32Next(snapshot, &entry) == TRUE)
            if (_wcsicmp(entry.szExeFile, name) == 0) { pid = entry.th32ProcessID; break; }
    CloseHandle(snapshot);
    return pid;
}

bool StatTableReader::findProcess(){
    qDebug("Function Entered");
    QStringList names;
    for(const GameLayout *l : GameLayout::all()) names << QString::fromWCharArray(l->processName);
    emit action_changed(QStringLiteral("Searching for %1...").arg(names.join('/')));
    for(const GameLayout *candidate : GameLayout::all()){
        DWORD pesID = findPid(candidate->processName);
        if(pesID == 0) continue;
        QString exe = QString::fromWCharArray(candidate->processName);
        bool changed = false;
        if(!statsInfo::select(*candidate, &changed)){
            emit status_changed(QStringLiteral("This match is from %1; restart SEN:P-AI to open it.").arg(exe));
            dbgReturn(return false);
        }
        _layout = candidate;
        teamBuf[0].assign(_layout->teamTable->size, 0);
        teamBuf[1].assign(_layout->teamTable->size, 0);
        currTeamData = teamBuf[0].data(); prevTeamData = teamBuf[1].data();
        if(changed) emit catalog_changed();
        //open handle to process
        processHandle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,FALSE,pesID);
        if (processHandle == NULL) {
            emit status_changed(QStringLiteral("SEN:P-AI failed to open %1 with debug access\n").arg(exe));
            dbgReturn(return false);
        }
        emit status_changed(QStringLiteral("SEN:P-AI noticed %1!").arg(exe));
        dbgReturn(return true);
    }
    dbgReturn(return false);
}

bool StatTableReader::updateTeams(){
    qDebug("Function Entered");
    emit action_changed(QStringLiteral("Updating data"));
    if(ReadProcessMemory(processHandle, teamDataPtr, prevTeamData, _layout->teamTable->size, NULL)){ //Team Data read succeeds
        std::swap(currTeamData,prevTeamData);
        //If either team has changed
        if(readTeamId(currTeamData,*_layout,false) != readTeamId(prevTeamData,*_layout,false) || readTeamId(currTeamData,*_layout,true) != readTeamId(prevTeamData,*_layout,true)){
            teamInfo home = readTeam(currTeamData,*_layout,false);
            teamInfo away = readTeam(currTeamData,*_layout,true);

            emit status_changed(QStringLiteral("SEN:P-AI noticed new teams!"));
            emit teamsChanged(QDateTime::currentMSecsSinceEpoch(),home,away);
        } else { //If neither team has changed
            //go find what else changed
            for(size_t i = 0; i < _layout->teamTable->size; ++i){
                uint8_t currByte = currTeamData[i];
                uint8_t prevByte = prevTeamData[i];
                if(currByte != prevByte)
                    emit teamDataChanged(i,prevByte,currByte);
            }
        }//End If/Else either team has/hasn't changed

        //TODO insert some team data shit here
        dbgReturn(return true);
    } else { //Team data read fails
        teamDataPtr = nullptr;
        emit status_changed(QStringLiteral("SEN:P-AI lost track of teams"));
        emit teamData_lost();
        dbgReturn(return false);
    }
}

bool StatTableReader::findTeams(){
    qDebug("Function Entered");
    emit action_changed(QStringLiteral("Searching for Team Data table..."));
    MEMORY_BASIC_INFORMATION info;

    //Ask Windows for information on every block of memory in the proccess, starting at zero
    for(uintptr_t mappingAddr = 0;
        VirtualQueryEx(processHandle, (void*)mappingAddr, &info, sizeof(info)) > 0;
        mappingAddr = mappingAddr + info.RegionSize) {
        //If the properties of the memory block match what we're looking for
        if ((info.State & TEAM_MEM_STATE) && (info.Type & TEAM_MEM_TYPE) && (info.Protect & TEAM_MEM_PROTEC) && (_layout->teamRegionSize == 0 || info.RegionSize == _layout->teamRegionSize)) {
            //Check set memory offsets in the block and count how many Player IDs are found
            int8_t playerCount = countTeamPlayerEntries(processHandle, mappingAddr + _layout->teamTableOffset, *_layout);
            //If there are enough players to make two valid teams
            if(playerCount >= 22){
                teamDataPtr = (void*)(mappingAddr + _layout->teamTableOffset);
                //Do an initial read of the team data
                if(0 >= ReadProcessMemory(processHandle, teamDataPtr, currTeamData, _layout->teamTable->size, NULL))
                    ;//dbgReturn(return false);
                teamInfo home = readTeam(currTeamData,*_layout,false);
                teamInfo away = readTeam(currTeamData,*_layout,true);
                _homeID = home.ID;
                _awayID = away.ID;
                emit status_changed(QStringLiteral("SEN:P-AI noticed the teams!"));
                emit teamsChanged(QDateTime::currentMSecsSinceEpoch(),home,away);
                dbgReturn(return true);
            } //End if enough valid players
        }//End If matching memory block
    }//End For every memory block in the proccess
    dbgReturn(return false);
}

bool StatTableReader::updateStats(){
    qDebug("Function Entered");
    emit action_changed(QStringLiteral("Updating stats"));
    const size_t entrySize = _layout->statEntrySize;
    int awayRead, homeRead = ReadProcessMemory(processHandle, homePtr, prevData,                        _nHome*entrySize, NULL);
    if(homeRead)  awayRead = ReadProcessMemory(processHandle, awayPtr, prevData+_nHome*entrySize, _nAway*entrySize, NULL);
    if(homeRead && awayRead){ //Table read succeeds
        bool stillValid = true;
        for(int i = 0; i < _nHome + _nAway && stillValid; ++i){
            stillValid = stillValid && currData[i*entrySize] == prevData[i*entrySize];
        }
        if(stillValid){
            std::swap(currData,prevData);
            emit statTableUpdate(currData,prevData);
            dbgReturn(return true);
        }
    } //Table read fails or player ids changed
    basePtr = homePtr = awayPtr = nullptr;
    emit status_changed(QStringLiteral("SEN:P-AI lost track of stats"));
    emit table_lost();
    dbgReturn(return false);
}

bool StatTableReader::doStatsFound(uint8_t homeCount, uint8_t awayCount){
    qDebug("Function Entered");
    //If the number of valid players on each team is different than it was before, reallocate the player entries array and fix all the pointers
    const size_t entrySize = _layout->statEntrySize;
    if(homeCount != _nHome || awayCount != _nAway){
        currData = data = (uint8_t*)realloc(data,(homeCount+awayCount)*entrySize*2);
        prevData = currData + ((homeCount+awayCount)*entrySize);
        //fix all the pointers and counts
        _nHome = homeCount;
        _nAway = awayCount;
        _nPlayers = homeCount + awayCount;
    }
    //Do an initial update of the stats table

    int awayRead, homeRead = ReadProcessMemory(processHandle, homePtr, currData,                        _nHome*entrySize, NULL);
    if(homeRead)  awayRead = ReadProcessMemory(processHandle, awayPtr, currData+_nHome*entrySize, _nAway*entrySize, NULL);
    if(!(homeRead && awayRead))
        dbgReturn(return false);
    emit status_changed(QStringLiteral("SEN:P-AI noticed the stats!"));
    emit table_found(currData);
    dbgReturn(return true);

}

bool StatTableReader::findStats(){
    qDebug("Function Entered");
    emit action_changed(QStringLiteral("Searching for stats table..."));
    MEMORY_BASIC_INFORMATION info;

    //Ask Windows for information on every block of memory in the proccess, starting at zero
    for(uintptr_t mappingAddr = 0;
        VirtualQueryEx(processHandle, (void*)mappingAddr, &info, sizeof(info)) > 0;
        mappingAddr = mappingAddr + info.RegionSize) {
        //If the properties of the memory block match what we're looking for
        if ((info.State & STAT_MEM_STATE) && (info.Type & STAT_MEM_TYPE) && (info.Protect & STAT_MEM_PROTEC) && (_layout->statsRegionSize == 0 || info.RegionSize == _layout->statsRegionSize)) {
            //Check set memory offsets in the block and count how many Player IDs are found
            int8_t homeCount = countTableEntries(processHandle,(mappingAddr+_layout->homeStatsOffset),*_layout);
            int8_t awayCount = countTableEntries(processHandle,(mappingAddr+_layout->awayStatsOffset),*_layout);

            //If there are enough players to make two valid teams
            if (homeCount >= 11 && awayCount >= 11) {
                //Set target proccess pointers
                basePtr = (uint8_t*) mappingAddr;
                homePtr = (uint8_t*)(mappingAddr+_layout->homeStatsOffset);
                awayPtr = (uint8_t*)(mappingAddr+_layout->awayStatsOffset);

                dbgReturn(return doStatsFound(homeCount, awayCount));
            }//End If enough valid players
        }//End If matching memory block
    }//End For every memory block in the proccess
    dbgReturn(return false);
}



#include "emmintrin.h"
bool StatTableReader::bruteForceStats(){
    qDebug("Function Entered");
    MEMORY_BASIC_INFORMATION info;

    //Ask Windows for information on every block of memory in the proccess, starting at zero
    for(uintptr_t mappingAddr = 0;
        VirtualQueryEx(processHandle, (void*)mappingAddr, &info, sizeof(info)) > 0;
        mappingAddr = mappingAddr + info.RegionSize) {
        //If the properties of the memory block match what we're looking for
        if ((info.State & STAT_MEM_STATE) && (info.Type & STAT_MEM_TYPE) && (info.Protect & STAT_MEM_PROTEC) && (info.RegionSize > 0)){
            size_t regionSize = info.RegionSize;
            if(regionSize > searchSize){
                if(searchSize > 0)
                    _mm_free(searchSpace);
                searchSpace = (uint32_t*)_mm_malloc((searchSize = (uint32_t)regionSize),16);
                if(searchSpace == nullptr){
                    qDebug() << "Allocation failed";
                    dbgReturn(return false);
                }
            }
//            tryReadBlock(mappingAddr,(uint8_t*)searchSpace,regionSize);
            if(!ReadProcessMemory(processHandle,(void*)(mappingAddr),searchSpace,regionSize, NULL))
                continue;
            const __m128i* ptr = (const __m128i*)searchSpace;
            const uint32_t player = (_homeID*100)+1;
            const __m128i comp = _mm_set1_epi32(player);//Compare to the player ID of home team player 1
            const __m128i mask = _mm_set1_epi8(~0);
            const size_t numVectors = (regionSize)/16;
            //For every 128bit vector in the valid search area
            for(size_t i = 0; i < numVectors; i++){
                __m128i eq = _mm_cmpeq_epi32(_mm_load_si128(ptr+i),comp);
                if(_mm_movemask_epi8(eq) != 0){//If any elements matched
                    uint32_t lanes[4];
                    std::memcpy(lanes, &ptr[i], sizeof lanes);
                    int j = -1;
                    while(lanes[++j] != player);//check which element matched
                    uintptr_t homeAddr = mappingAddr + ((i*4)+j)*4;
                    uintptr_t awayAddr = homeAddr + _layout->awayStatsDiff;

                    uint8_t homeCount = countTableEntries(processHandle,homeAddr,*_layout);
                    uint8_t awayCount = countTableEntries(processHandle,awayAddr,*_layout);
                    //If there are enough players to make two valid teams
                    if (homeCount >= 11 && awayCount >= 11) {
                        //Set target proccess pointers
                        basePtr = (uint8_t*) mappingAddr;
                        homePtr = (uint8_t*) homeAddr;
                        awayPtr = (uint8_t*) awayAddr;

                        dbgReturn(return doStatsFound(homeCount, awayCount));
                    }//End If enough valid players
                }//End If any elements matched
            }//End for every 128bit vector
        }//End If matching memory block
    }//End For every memory block in the proccess
    dbgReturn(return false);
}


void StatTableReader::update(){
    qDebug("Function Entered");
    switch (status) {
    default:
    case None:
        if(findProcess()) status = Process;
        break;
    case Process:
        if(!updateProcess()) status = None;
        else if(findTeams()) status = Teams;
        break;
    case Teams:
        if(!updateTeams()) status = Process;
        else if(findStats()) status = Stats;
        break;
    case Stats:
        if(!updateStats()) status = Teams;
        break;
    case BruteForce:
        if(bruteForceStats()) status = Stats;
        else status = Teams;
        break;
    }
    butt->setEnabled(status == Teams);
    dbgReturn();
}


int StatTableReader::GetDebugPrivilege()
{
    qDebug("Function Entered");
    HANDLE hProcess=GetCurrentProcess();
    HANDLE hToken;

    if (!OpenProcessToken(hProcess, TOKEN_ADJUST_PRIVILEGES, &hToken))
        return FALSE;
    LUID luid;
    BOOL bRet=FALSE;

    if (LookupPrivilegeValue(NULL, SE_DEBUG_NAME, &luid))
    {
        TOKEN_PRIVILEGES tp;

        tp.PrivilegeCount=1;
        tp.Privileges[0].Luid=luid;
        tp.Privileges[0].Attributes=(TRUE) ? SE_PRIVILEGE_ENABLED: 0;
        //
        //  Enable the privilege or disable all privileges.
        //
        if (AdjustTokenPrivileges(hToken, FALSE, &tp, NULL, (PTOKEN_PRIVILEGES)NULL, (PDWORD)NULL))
        {
            //
            //  Check to see if you have proper access.
            //  You may get "ERROR_NOT_ALL_ASSIGNED".
            //
            bRet=(GetLastError() == ERROR_SUCCESS);
        }
    }

    CloseHandle(hToken);
    dbgReturn(return bRet);
}
