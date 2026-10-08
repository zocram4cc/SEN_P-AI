#!/usr/bin/env python3
"""A team's squad {playerId: name} from the game's EDIT file, via rigbot.
CLI: edit_names.py VERSION TEAM_NAME   (RIGBOT = the rigbot checkout; run with rigbot's Python)

Slots resolve exactly as rigbot.core.editfile.parse_squads does: by record ID
where the layout says so (pes17), else the cumulative squad grid."""
import json
import os
import sys

sys.path.insert(0, os.environ["RIGBOT"])
from rigbot.core import editfile as E  # noqa: E402


def squad(version, team_name):
    data = E.decrypt_edit(E.find_edit_file(version), version)["data"]
    layout = E.LAYOUTS[version]
    base, stride, name_off = layout["player_base"], layout["player_stride"], layout.get("name_off", 0)
    start, pids = E._squad_grid(data, layout)[E._team_ids(data, layout)[team_name]]
    if layout.get("index_by_id"):
        by_id = E._records_by_id(data, layout)
        slots = [(p, by_id[p]) for p in pids if p in by_id]
    else:
        slots = list(zip(pids, range(start, start + len(pids))))
    out = {}
    for pid, n in slots:
        at = base + n * stride + name_off
        out[pid] = E._COLOUR.sub("", data[at: at + 64].split(b"\0")[0].decode("utf-8", "ignore")).strip()
    return out


if __name__ == "__main__":
    print(json.dumps(squad(sys.argv[1], sys.argv[2]), ensure_ascii=False))
