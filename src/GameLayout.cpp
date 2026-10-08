#include "GameLayout.h"
#include "TeamDataTable.h"
#include "StatsInfo.h"
#include <cstddef>

static_assert(offsetof(teamDataTable, homeData.players) == 0x0F8, "PES17 home pairs");
static_assert(offsetof(teamDataTable, awayData) + offsetof(teamDataTable, homeData.players) == 0x618, "PES17 away pairs");
static_assert((offsetof(teamDataTable, homeData.teamID) - offsetof(teamDataTable, homeData.players)) / 4 == 65, "PES17 team id word");

static const TeamTableLayout PES2017_TEAM_TABLE = {
    sizeof(teamDataTable),
    offsetof(teamDataTable, awayData),
    offsetof(teamDataTable, homeData.teamName), 70,
    offsetof(teamDataTable, homeData.players),
    offsetof(teamDataTable, homeData.teamID),
    offsetof(teamDataTable, homePlayers),
    offsetof(teamDataTable, awayPlayers),
    sizeof(teamDataTable::playerEntry),
    offsetof(teamDataTable::playerEntry, playerName), 46,
    offsetof(teamDataTable::playerEntry, playerID),
    offsetof(teamDataTable::playerEntry, playerCondition),
};

const GameLayout PES2017_LAYOUT = {
    L"PES2017.exe", "PES2017",
    393216, 0x538B4, 0xFFFD, 0xFFFE, &PES2017_TEAM_TABLE,
    589824, 0x35010, 0x5DE40, 0x28E30,
    4784, 70099, 90300,
    pes17Stats, PES17_STAT_COUNT,
};

const std::vector<const GameLayout*>& GameLayout::all() {
    static const std::vector<const GameLayout*> layouts = { &PES2017_LAYOUT };
    return layouts;
}

const GameLayout* GameLayout::byStatCount(size_t n) {
    for (const GameLayout *l : all()) if (l->statCount == n) return l;
    return nullptr;
}
