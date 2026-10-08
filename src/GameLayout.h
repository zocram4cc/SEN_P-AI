#ifndef GAMELAYOUT_H
#define GAMELAYOUT_H
#include <cstddef>
#include <cstdint>
#include <vector>
struct PESstat;

// Where the team data table keeps the fields SEN:P-AI reads. Offsets from
// the table start unless noted. PES 2017's are offsetof() of teamDataTable.
struct TeamTableLayout {
    size_t size;               // bytes read each tick
    size_t sideStride;         // homeData -> awayData
    size_t teamNameOffset;     // within a side
    size_t teamNameMax;        // 70
    size_t pairsOffset;        // players[32] {validPair, uint32 id} within a side
    size_t teamIdOffset;       // teamID within a side
    size_t playersOffset;      // homePlayers[0]
    size_t awayPlayersOffset;  // awayPlayers[0]
    size_t playerStride;       // sizeof(playerEntry)
    size_t playerNameOffset;   // within playerEntry
    size_t playerNameMax;      // 46
    size_t playerIdOffset;     // within playerEntry
    size_t playerConditionOffset; // within playerEntry
};

struct GameLayout {
    const wchar_t *processName;
    const char *tag;
    // team data table
    size_t teamRegionSize;     // 0 = any size
    size_t teamTableOffset;
    uint16_t homePairMarker, awayPairMarker;
    const TeamTableLayout *teamTable;
    // stats table
    size_t statsRegionSize;    // 0 = any size
    size_t homeStatsOffset, awayStatsOffset, awayStatsDiff;
    size_t statEntrySize;
    uint32_t playerIdMin, playerIdMax;   // both exclusive
    // catalog
    PESstat *stats;
    size_t statCount;

    static const std::vector<const GameLayout*>& all();
    static const GameLayout* byStatCount(size_t n);
};

extern const GameLayout PES2017_LAYOUT;
#endif // GAMELAYOUT_H
