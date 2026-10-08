#include "StatsInfo.h"

statsInfo::statsInfo()
{
    if(statMapping.empty())
        init();
}
PESstat statsInfo::dummy = PESstat{};
std::map<QString,PESstat*> statsInfo::statMapping = std::map<QString,PESstat*>{};

#include "GameLayout.h"
size_t statsInfo::statCount = PES17_STAT_COUNT;
size_t statsInfo::playerEntrySize = 4784;
PESstat *statsInfo::stats = pes17Stats;
const GameLayout *statsInfo::locked = nullptr;

// The catalog is fixed by the first game attached or .sen opened, for the
// rest of the run (spec 5.2). Until then PES 2017's is active, as upstream.
bool statsInfo::select(const GameLayout &layout, bool *changed){
    if(changed) *changed = false;
    if(locked) return locked == &layout;
    locked = &layout;
    if(stats != layout.stats){
        stats = layout.stats;
        statCount = layout.statCount;
        playerEntrySize = layout.statEntrySize;
        init();
        if(changed) *changed = true;
    }
    return true;
}
