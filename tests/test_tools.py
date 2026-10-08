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
