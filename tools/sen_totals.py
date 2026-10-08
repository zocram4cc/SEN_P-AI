#!/usr/bin/env python3
"""Per-team totals of a .sen file's finalStats (layout: Match.cpp:488-536).

The catalog is picked by the file's stat count: PES 2017's from src/catalogs/Pes17Stats.cpp,
otherwise the docs/measurements/*/catalog.yaml with that many rows.
CLI: sen_totals.py MATCH.sen [STAT NAME ...]   (default: the Team Stats page's stats)"""
import struct
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "analyze"))
import sen_sections  # noqa: E402
import align_catalog  # noqa: E402

PAGE = ["Goals Scored", "Shots", "Shots on Target", "Fouls", "Fouls Offside", "Corner Kicks", "Free Kicks",
        "Passes", "Passes Made", "Crosses", "Interceptions", "Tackles Won", "Saves"]
CODE = {"sint8": "i", "sint32": "i", "float32": "f"}  # everything else is read as uint32 (PESstat::getStatValueType)


def catalog(stat_count):
    if stat_count == 175:
        return [(t, n) for _, t, _, n, _ in align_catalog.pes17_rows()]
    for path in sorted((ROOT / "docs" / "measurements").glob("*/catalog.yaml")):
        rows = yaml.safe_load(open(path))["stats"]
        if len(rows) == stat_count:
            return [(r["type"], r["name"]) for r in rows]
    raise LookupError(f"no catalog with {stat_count} stats")


def totals(path, names=PAGE):
    data = open(path, "rb").read()
    count, players = struct.unpack_from("<HB", data, 12)
    info = sen_sections.section(path, "matchInfo")
    n_home = info[32]
    final = sen_sections.section(path, "finalStats")
    out = {}
    for s, (typ, name) in enumerate(catalog(count)):
        vals = struct.unpack_from("<" + CODE.get(typ, "I") * players, final, s * players * 4)
        if name in names:
            out[name] = (sum(vals[:n_home]), sum(vals[n_home:]))
    return out


if __name__ == "__main__":
    for name, (h, a) in totals(sys.argv[1], sys.argv[2:] or PAGE).items():
        print(f"{name:20} {h:>8g} {a:>8g}")
