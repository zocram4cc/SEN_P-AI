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

extern PESstat pes19Stats[]; extern const size_t pes19StatCount, pes19EntrySize;
// docs/measurements/pes19/layout.yaml, measured 2026-10-08 on two testbot matches /g/ vs /sp/
// (19:26 3-4 and 19:55 0-3) with tools/regions.exe + tools/analyze; evidence per value there.
static const TeamTableLayout PES2019_TEAM_TABLE = {
    /*size*/ 22652,              // awayPlayersOffset + 32 * playerStride
    /*sideStride*/ 1516,         // away pairs 209236 - home pairs 207720
    /*teamNameOffset*/ 4, /*teamNameMax*/ 70,
    /*pairsOffset*/ 272,         // 40 pairs per side (PES 2017: 32); the reader uses the first 32
    /*teamIdOffset*/ 596,        // after 40 pairs and a validPair
    /*playersOffset*/ 4220,      // first home name 211724 - 56 - table start 207448
    /*awayPlayersOffset*/ 14460, // first away name 221964 - 56 - table start
    /*playerStride*/ 256,
    /*playerNameOffset*/ 56, /*playerNameMax*/ 46,
    /*playerIdOffset*/ 48,       // player_entries name_minus_id [4, 8]
    /*playerConditionOffset*/ 207, // condition ordinal 0-4 in the low bits (PES 2017: 0x00-0x80); 23/23 = Team Sheet arrows
};
const GameLayout PES2019_LAYOUT = {
    L"PES2019.exe", "PES2019",
    0x50000, 0x32A58, 0xFFFD, 0xFFFE, &PES2019_TEAM_TABLE, // team region: same base and offset in both matches
    0x190000, 0x7B5A4, 0xD18EC, 0x56348,                  // find_stats_blocks: [505252, 23, 8176] / [858348, 23, 8176], both matches
    pes19EntrySize, 70099, 91100,                          // spec 6: EDIT IDs 70101-91023
    pes19Stats, pes19StatCount,                            // src/catalogs/Pes19Stats.cpp from docs/measurements/pes19/catalog.yaml
};

const std::vector<const GameLayout*>& GameLayout::all() {
    static const std::vector<const GameLayout*> layouts = { &PES2017_LAYOUT, &PES2019_LAYOUT };
    return layouts;
}

const GameLayout* GameLayout::byStatCount(size_t n) {
    for (const GameLayout *l : all()) if (l->statCount == n) return l;
    return nullptr;
}
