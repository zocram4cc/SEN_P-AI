import json, struct, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import diff_events, sen_sections

def _log(tmp, events):
    p = tmp / "log.txt"
    p.write_text("".join(json.dumps(e, indent=4) + "\n" for e in events))
    return p

def test_log_parses_concatenated_indented_json(tmp_path):
    ev = [{"type": "Event", "event": "Goal", "timestamp": 1, "gameMinute": 12.4},
          {"type": "Event", "event": "Clock Stopped", "timestamp": 2, "gameMinute": 12.5, "reason": "Goal"}]
    assert diff_events.load_log(_log(tmp_path, ev)) == ev

def test_tap_frames_are_length_prefixed(tmp_path):
    p = tmp_path / "tap.bin"
    frames = [{"event": "Stats Found"}, {"event": "Goal"}]
    p.write_bytes(b"".join(struct.pack("<I", len(b := json.dumps(f).encode())) + b for f in frames))
    assert diff_events.load_tap(p) == frames

def test_compare_ignores_timestamps_and_minute_fractions():
    a = [{"event": "Goal", "timestamp": 1, "gameMinute": 12.1, "team": "Home"}]
    b = [{"event": "Goal", "timestamp": 9, "gameMinute": 12.9, "team": "Home"}]
    assert diff_events.compare(a, b) == []

def test_compare_reports_a_different_scorer():
    a = [{"event": "Goal", "gameMinute": 12, "scorer": {"playerId": 72101}}]
    b = [{"event": "Goal", "gameMinute": 12, "scorer": {"playerId": 72102}}]
    assert diff_events.compare(a, b)

def test_compare_tolerates_two_extra_clock_stops_but_not_three():
    stop = {"event": "Clock Stopped", "gameMinute": 3}
    assert diff_events.compare([stop] * 5, [stop] * 3) == []
    assert diff_events.compare([stop] * 6, [stop] * 3)

def _sen(tmp, final):
    name = b"finalStats".ljust(24, b"\0")
    head = b"SEN:P-AI\0" + bytes([1, 2, 7]) + struct.pack("<HBBH", 175, 2, 10, 1)
    table_at = len(head)
    data_at = table_at + 32
    p = tmp / "m.sen"
    p.write_bytes(head + struct.pack("<II", len(final), data_at) + name + final)
    return p

def test_sen_section_reads_by_name(tmp_path):
    assert sen_sections.section(_sen(tmp_path, b"\x01\x02\x03"), "finalStats") == b"\x01\x02\x03"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "analyze"))
import find_stats_blocks, find_team_table, player_entries, block_profile, emit_catalog

def _u32(*vals):
    return b"".join(struct.pack("<I", v) for v in vals)

def test_stats_runs_find_a_strided_team_block():
    stride = 64
    buf = bytearray(4096)
    for k in range(14):                       # 14 players of team 721 at stride 64 from 0x100
        struct.pack_into("<I", buf, 0x100 + k * stride, 72101 + k)
    struct.pack_into("<I", buf, 0x900, 72150)  # a stray mention elsewhere
    assert find_stats_blocks.runs(bytes(buf), 721) == [(0x100, 14, 64)]

def test_team_pairs_found_with_marker_and_team_id():
    pairs = b"".join(_u32(0x0001FFFD, 72101 + k) for k in range(23)) + _u32(0xFFFFFFFF, 0) * 9
    buf = b"\0" * 64 + b"/g/\0".ljust(70, b"\0") + b"\0" * 10 + pairs + _u32(0, 721)
    found = find_team_table.pair_runs(buf, 721)
    assert found == [(64 + 80, 23, 0xFFFD)]
    assert find_team_table.team_name_offset(buf, 64 + 80, "/g/") == 64

def test_player_entries_stride_and_every_name_offset():
    stride, ids = 200, {72101: "TORVALDS", 72102: "STALLMAN"}
    buf = bytearray(1000)
    for k, (pid, name) in enumerate(ids.items()):
        struct.pack_into("<II", buf, 100 + k * stride + 40, pid, pid)   # ID, then a copy (PES 2017 commentaryID)
        buf[100 + k * stride + 52: 100 + k * stride + 52 + len(name)] = name.encode()
    assert player_entries.entries(bytes(buf), ids) == {"stride": 200, "name_minus_id": [8, 12], "first_name_at": 152}

def test_block_profile_sums_u32x9_blocks():
    row = _u32(72101) + _u32(*([0] * 8 + [1])) + _u32(*([2] + [0] * 8))
    prof = block_profile.blocks([row], [row], start=4, width=36)
    assert prof[0] == {"offset": 4, "home_sum": 1, "away_sum": 1, "segments_nonzero": [8]}
    assert prof[1]["home_sum"] == 2 and prof[1]["segments_nonzero"] == [0]

def test_emit_catalog_writes_pes_stat_rows(tmp_path):
    y = tmp_path / "c.yaml"
    y.write_text("tag: pes19\nentry_size: 8\nstats:\n"
                 "  - {name: Player ID, offset: 0x0, type: uint32, count: 1, vis: DontCare, evidence: e}\n"
                 "  - {name: Goals Scored, offset: -1, type: uint32, count: 9, vis: Important, evidence: absent}\n")
    text = emit_catalog.emit(y)
    assert '{  0, 0x0000, uint32,1,  L("Player ID"), DontCare},' in text
    assert '{  1, -1, uint32,9,  L("Goals Scored"), false, false},' in text
    assert "PESstat pes19Stats[2]" in text

def test_main_compares_a_log_with_a_tap(tmp_path):
    ev = [{"type": "Event", "event": "Goal", "timestamp": 1, "gameMinute": 12.4, "team": "Home"}]
    tap = tmp_path / "tap.bin"
    tap.write_bytes(b"".join(struct.pack("<I", len(b := json.dumps(e, indent=4).encode())) + b for e in ev))
    assert diff_events.main([str(_log(tmp_path, ev)), str(tap), "--tap"]) == 0
    other = [dict(ev[0], team="Away")]
    tap.write_bytes(b"".join(struct.pack("<I", len(b := json.dumps(e).encode())) + b for e in other))
    assert diff_events.main([str(_log(tmp_path, ev)), str(tap)]) == 1
