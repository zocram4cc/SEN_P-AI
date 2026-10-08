#ifndef STATSINFO_H
#define STATSINFO_H
#include <QString>
#include <map>
#include <stdint.h>
#include <math.h>

enum type:char {
    sint8, sint32, uint8, uint16, uint32, float32, uint32x9, uint32arr, validIndicator, cstring
};

union stat_value {
    float f;
    int32_t i;
    uint32_t u;

    stat_value(float F): f(F){}
    stat_value(int32_t I): i(I){}
    stat_value(uint32_t U): u(U){}
    stat_value(): u(0){}
};

struct PESstat {
    int visualIndex;
    ptrdiff_t offset;
    type statType;
    uint8_t count;
    QString name;
    bool shown;
    bool logged;
    //QString comment;

//    PESstat(int idx, ptrdiff_t _offset, type _type, uint8_t _count, const char *_name, bool _shown, bool _logged, const char *_comment = nullptr):
//        name(_name), comment(_comment), offset(_offset), visualIndex(idx), statType(_type), count(_count), shown(_shown), logged(_logged) {
//    }
    type getStatValueType() const{
        switch (statType) {
        case sint8:
        case sint32:
            return sint32;
        case uint8:
        case uint16:
        case uint32:
        case uint32x9:
        case uint32arr:
            return uint32;
        case float32:
        default:
            return float32;
        }
    }

    double getSegmentDouble(uint8_t *data, uint8_t segment = 0) const{
        if(offset < 0) return 0; //absent in this version: constant, so MatchReader never sees a change (NaN != NaN would)
        if(segment >= count) return std::nan("");
        switch (statType) {
#define CASE(VAL,TYPE) case VAL: return *(TYPE*)(data + offset + segment * sizeof(TYPE))
        CASE( sint8,  int8_t);
        CASE( uint8, uint8_t);
        CASE( uint16,uint16_t);
        CASE( uint32,uint32_t);
        CASE(float32,float);
#undef CASE
        default: return std::nan("");
        }
    }

    stat_value getSegmentValue(uint8_t *data, uint8_t segment = 0) const{
        if(offset < 0) return stat_value{};
        if(segment >= count) return stat_value{std::nanf("")};
        switch (statType) {
#define CASE(VAL,TYPE) case VAL: return stat_value{*(TYPE*)(data + offset + segment * sizeof(TYPE))}
        CASE( sint8,  int8_t);
        CASE( uint8, uint8_t);
        CASE( uint16,uint16_t);
        CASE( uint32,uint32_t);
        CASE(float32,float);
        default: return stat_value{std::nanf("")};
        }
    }

    double getValue(uint8_t *data) const{
        double result = 0;
        for(uint8_t i = 0; i < count; ++i)
            result += getSegmentDouble(data,i);
        return result;
    }

    bool getChanged(uint8_t *curr, uint8_t *prev) const{
        return getValue(curr) != getValue(prev);
    }

    bool getSegmentChanged(uint8_t *curr, uint8_t *prev, uint8_t segment, stat_value *out = nullptr) const{
        bool res = getSegmentDouble(curr,segment) != getSegmentDouble(prev,segment);
        if(res && out != nullptr)
            *out = getSegmentValue(curr,segment);
        return res;
    }
};

struct GameLayout;
#define PES17_STAT_COUNT 175
extern PESstat pes17Stats[];

class statsInfo
{
    static size_t statCount;
    static size_t playerEntrySize;
    static PESstat *stats;
    static PESstat dummy;
    static const GameLayout *locked;

    static std::map<QString,PESstat*> statMapping;
public:
    statsInfo();

    static bool select(const GameLayout &layout, bool *changed = nullptr);
    static const GameLayout* lockedLayout(){ return locked; }
    static void init(){
        qDebug("Function Entered");
        statMapping = std::map<QString,PESstat*>();
        for(int s = 0; s < statCount; ++s){
            statMapping.insert({stats[s].name,stats+s});
        }
    }

    static int getStatIndex(QString str){
        for(int i = 0; i < statCount; ++i){
            if(stats[i].name == str)
                return i;
        }
        return -1;
    }

    static PESstat& getStat(size_t i){
        if(i < statCount)
            return stats[i];
        else
            return dummy;
    }

    static PESstat& getStat(QString str){
        return *statMapping.at(str);
    }

    PESstat& operator[](size_t i){
        return getStat(i);
    }

    static size_t count() {
        return statCount;
    }

    static size_t entrySize(){
        return playerEntrySize;
    }
};

#endif // STATSINFO_H
