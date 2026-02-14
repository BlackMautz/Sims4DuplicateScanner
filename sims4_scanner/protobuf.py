# -*- coding: utf-8 -*-
"""Gemeinsamer Protobuf-Parser für Tray, Savegame und Portrait-Dateien.

Vereinheitlicht die Varint-Dekodierung und Feld-Extraktion, die vorher
in tray.py, savegame.py und tray_portraits.py dupliziert waren.
"""

from __future__ import annotations

import struct
from collections import defaultdict


def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Dekodiert einen Protobuf-Varint ab Position pos.

    Returns:
        (value, new_pos)
    """
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            break
        shift += 7
        if shift > 63:
            break
    return result, pos


def parse_pb(data: bytes, max_depth: int = 3, depth: int = 0) -> dict[int, list]:
    """Parst Protobuf-Felder (vereinfacht).

    Gibt {field_num: [(wire_type_str, value), ...]} zurück.
    wire_type_str: "varint", "fixed64", "bytes", "fixed32"

    Args:
        data: Rohbytes zum Parsen
        max_depth: Maximale Rekursionstiefe (für savegame.py Kompatibilität)
        depth: Aktuelle Tiefe
    """
    fields: dict[int, list] = defaultdict(list) if max_depth > 1 else {}
    if depth >= max_depth or len(data) < 2:
        return fields

    pos = 0
    dlen = len(data)

    while pos < dlen - 1:
        try:
            tag, new_pos = decode_varint(data, pos)
            if tag == 0 or new_pos >= dlen:
                pos = new_pos if new_pos > pos else pos + 1
                continue

            field_num = tag >> 3
            wire_type = tag & 0x07

            if field_num > 5000 or field_num == 0:
                pos += 1
                continue

            if wire_type == 0:  # Varint
                value, pos = decode_varint(data, new_pos)
                if isinstance(fields, defaultdict):
                    fields[field_num].append(("varint", value))
                else:
                    fields.setdefault(field_num, []).append(("varint", value))
            elif wire_type == 1:  # Fixed64
                if new_pos + 8 <= dlen:
                    value = struct.unpack_from("<Q", data, new_pos)[0]
                    pos = new_pos + 8
                    if isinstance(fields, defaultdict):
                        fields[field_num].append(("fixed64", value))
                    else:
                        fields.setdefault(field_num, []).append(("fixed64", value))
                else:
                    pos = new_pos + 1
            elif wire_type == 2:  # Length-delimited
                length, pos2 = decode_varint(data, new_pos)
                if 0 < length < 10_000_000 and pos2 + length <= dlen:
                    if isinstance(fields, defaultdict):
                        fields[field_num].append(("bytes", data[pos2:pos2 + length]))
                    else:
                        fields.setdefault(field_num, []).append(("bytes", data[pos2:pos2 + length]))
                    pos = pos2 + length
                else:
                    pos = new_pos + 1
            elif wire_type == 5:  # Fixed32
                if new_pos + 4 <= dlen:
                    value = struct.unpack_from("<I", data, new_pos)[0]
                    pos = new_pos + 4
                    if isinstance(fields, defaultdict):
                        fields[field_num].append(("fixed32", value))
                    else:
                        fields.setdefault(field_num, []).append(("fixed32", value))
                else:
                    pos = new_pos + 1
            else:
                pos = new_pos + 1
        except Exception:
            pos += 1

    return fields


# ── Convenience-Helfer ───────────────────────────────────────────

def pb_string(fields: dict, field_num: int) -> str:
    """Holt einen UTF-8-String aus einem Protobuf-Feld."""
    for vtype, val in fields.get(field_num, []):
        if vtype == "bytes":
            try:
                text = val.decode("utf-8")
                if text.isprintable():
                    return text
            except Exception:
                pass
    return ""


def pb_varint(fields: dict, field_num: int) -> int | None:
    """Holt einen Varint-Wert aus einem Protobuf-Feld."""
    for vtype, val in fields.get(field_num, []):
        if vtype == "varint":
            return val
    return None


def pb_fixed64(fields: dict, field_num: int) -> int | None:
    """Holt einen Fixed64-Wert aus einem Protobuf-Feld."""
    for vtype, val in fields.get(field_num, []):
        if vtype == "fixed64":
            return val
    return None
