#!/usr/bin/env python3
"""Read one named section out of a .sen file (layout: Match.cpp:463-481).

Usage: sen_sections.py A.sen B.sen SECTION   - exit 0 when the sections are byte-identical.
"""
import struct
import sys

HEAD = 9 + 3 + 2 + 1 + 1  # magic, version, statCount, players, matchLength


def section(path, name):
    data = open(path, "rb").read()
    if data[:9] != b"SEN:P-AI\0":
        raise ValueError(f"{path}: not a .sen file")
    (count,) = struct.unpack_from("<H", data, HEAD)
    for i in range(count):
        size, offset, raw = struct.unpack_from("<II24s", data, HEAD + 2 + i * 32)
        if raw.split(b"\0")[0].decode() == name:
            return data[offset:offset + size]
    raise KeyError(f"{path}: no section {name!r}")


def stat_count(path):
    return struct.unpack_from("<H", open(path, "rb").read(), 12)[0]


if __name__ == "__main__":
    a, b, name = sys.argv[1:4]
    same = section(a, name) == section(b, name)
    print("identical" if same else "DIFFERENT")
    sys.exit(0 if same else 1)
