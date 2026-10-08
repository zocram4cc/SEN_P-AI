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
    assert "extern const size_t pes19StatCount = 2;" in text   # const alone has internal linkage

def test_main_compares_a_log_with_a_tap(tmp_path):
    ev = [{"type": "Event", "event": "Goal", "timestamp": 1, "gameMinute": 12.4, "team": "Home"}]
    tap = tmp_path / "tap.bin"
    tap.write_bytes(b"".join(struct.pack("<I", len(b := json.dumps(e, indent=4).encode())) + b for e in ev))
    assert diff_events.main([str(_log(tmp_path, ev)), str(tap), "--tap"]) == 0
    other = [dict(ev[0], team="Away")]
    tap.write_bytes(b"".join(struct.pack("<I", len(b := json.dumps(e).encode())) + b for e in other))
    assert diff_events.main([str(_log(tmp_path, ev)), str(tap)]) == 1

import align_catalog

P17 = [  # (offset, type, count, name, vis) - a toy PES 2017 catalog: id, 4 blocks, 2 tail bytes
    (0x00, "uint32", 1, "Player ID", "DontCare"),
    (0x04, "uint32", 9, "Goals Scored", "Important"),
    (0x28, "uint32", 9, "Own Goals Scored", "Unknown"),
    (0x4C, "uint32", 9, "Shots", "Normal"),
    (0x70, "uint32", 9, "Passes", "Normal"),
    (0x94, "sint8", 1, "First Minute on Pitch", "Normal"),
    (0x95, "uint8", 1, "?UNKNOWN 6", "Unknown"),
]

def _spec(anchors, blocks_end, entry_size, tail=None):
    return {"tag": "t", "entry_size": entry_size, "blocks_end": blocks_end,
            "anchors": {k: {"offset": v, "evidence": "e"} for k, v in anchors.items()},
            "tail": tail or {}}

def test_align_maps_equal_gaps_in_order_and_unequal_gaps_to_unknown():
    # new layout: Goals, Own Goals, Shots, 2 extra blocks, Passes -> gap Shots..Passes differs
    rows = align_catalog.align(P17, _spec({"Goals Scored": 0x04, "Shots": 0x4C, "Passes": 0xB8}, 0xDC, 0xE0))
    by = {r["name"]: r for r in rows}
    assert by["Own Goals Scored"]["offset"] == 0x28            # 1 block between, both sides
    assert [r["offset"] for r in rows if r["name"].startswith("?UNKNOWN")][:2] == [0x70, 0x94]
    assert by["First Minute on Pitch"]["offset"] == -1         # tail stat without a measurement is absent

def test_align_drops_pes17_names_from_an_unequal_gap():
    rows = align_catalog.align(P17, _spec({"Goals Scored": 0x04, "Passes": 0x94}, 0xB8, 0xBC))
    by = {r["name"]: r for r in rows}
    assert by["Own Goals Scored"]["offset"] == -1 and by["Shots"]["offset"] == -1

def test_align_covers_every_byte_exactly_once():
    tail = {"First Minute on Pitch": {"offset": 0x94, "type": "sint8", "count": 1, "evidence": "e"}}
    rows = align_catalog.align(P17, _spec({"Goals Scored": 0x04, "Passes": 0x70}, 0x94, 0xA0, tail))
    size = {"uint32": 4, "sint8": 1, "uint8": 1, "uint16": 2, "float32": 4}
    covered = sorted(b for r in rows if r["offset"] >= 0
                     for b in range(r["offset"], r["offset"] + size[r["type"]] * r["count"]))
    assert covered == list(range(0xA0))

def test_invariants_flag_made_above_attempts():
    rows = [{"name": "Passes", "offset": 4, "type": "uint32", "count": 9},
            {"name": "Passes Made", "offset": 40, "type": "uint32", "count": 9}]
    good = struct.pack("<I9I9I", 72101, 5, *[0] * 8, 4, *[0] * 8)
    bad = struct.pack("<I9I9I", 72102, 1, *[0] * 8, 3, *[0] * 8)
    assert align_catalog.invariants(rows, [good]) == []
    assert align_catalog.invariants(rows, [good, bad]) == [("Passes Made", "Passes", 72102, 3, 1)]

import accept

def test_accept_clock_check_ignores_hud_misreads_after_half_time():
    # HUD 0..44 one reading per "minute"; then 45; then a stoppage-time '90:00' OCR'd as '9:00'
    hud = [(1000 * m, m) for m in range(45)] + [(45000, 45), (99000, 9)]
    ev = [{"event": "Clock Updated", "timestamp": 1000 * m + 500, "gameMinute": float(m)} for m in range(45)]
    ev += [{"event": "Clock Updated", "timestamp": 99500, "gameMinute": 90.0}]
    fails, compared = accept.check(ev, ev, "", hud)
    assert compared == 45 and not [f for f in fails if f.startswith("clock")]
    ev[10]["gameMinute"] = 14.0                                   # a real first-half error still fails
    assert any(f.startswith("clock 14.0") for f in accept.check(ev, ev, "", hud)[0])
