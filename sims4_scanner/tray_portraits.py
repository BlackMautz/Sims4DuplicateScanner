# -*- coding: utf-8 -*-
"""Tray-Porträts: Entschlüsselt SGI-Dateien und verknüpft Sim-Namen mit Porträtbildern.

Die .householdbinary-Dateien im Tray-Ordner enthalten Sim-Daten als Protobuf:
    f1 (bytes) → Haupt-Blob
      f1.f6 (bytes) → Sim-Daten-Blob (pro Sim ein Eintrag)
        f1.f6.f1 (fixed64) → Tray-Sim-ID (= SGI Instance-ID)
        f1.f6.f5 (string) → Vorname
        f1.f6.f6 (string) → Nachname

SGI-Dateiname: 0x{type:08X}!0x{tray_sim_id:016x}.sgi
    Type = Position im Haushalt (0x13=Sim0, 0x23=Sim1, 0x33=Sim2, ...)
    Jeder Sim hat genau EIN SGI mit seinem eigenen Type-Prefix.

SGI-Format:
    24-Byte Header + XOR-verschlüsselte JPEG-Payload
    XOR-Key: 41 25 E6 CD 47 BA B2 1A
"""

from __future__ import annotations

import os
import struct

from .protobuf import parse_pb, pb_string, pb_fixed64


# XOR-Schlüssel für SGI/HHI-Entschlüsselung
_XOR_KEY = bytes.fromhex("4125e6cd47bab21a")


def _decrypt_sgi(filepath: str) -> bytes | None:
    """Entschlüsselt eine SGI-Datei und gibt JPEG-Bytes zurück."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) < 32:
            return None
        payload = data[24:]
        key = _XOR_KEY
        klen = len(key)  # 8

        # Schnelle 8-Byte-Block-XOR statt Byte-für-Byte
        result = bytearray(len(payload))
        key_int = int.from_bytes(key, 'little')
        # Hauptteil: 8 Bytes auf einmal XOR-en
        full_blocks = len(payload) // klen
        for i in range(full_blocks):
            off = i * klen
            block = int.from_bytes(payload[off:off + klen], 'little')
            result[off:off + klen] = (block ^ key_int).to_bytes(klen, 'little')
        # Rest-Bytes (0-7)
        remainder = full_blocks * klen
        for i in range(remainder, len(payload)):
            result[i] = payload[i] ^ key[i % klen]
        return bytes(result)
    except Exception:
        return None


# Lokale Aliase für den bestehenden Code
_pb_parse = parse_pb
_pb_string = pb_string
_pb_fixed64 = pb_fixed64


# ── Sim-Daten aus Householdbinary extrahieren ────────────────────

def _extract_sims_from_householdbinary(filepath: str, include_hh_info: bool = False):
    """Parst eine .householdbinary und gibt [(first, last, tray_sim_id), ...] zurück.

    Struktur: top.f1 (Haupt-Blob) → f1.f6 (Sim-Einträge, je ein bytes-Feld)
              Sim-Eintrag: f1=tray_sim_id(fixed64), f5=Vorname(str), f6=Nachname(str)
    
    Args:
        filepath: Pfad zur .householdbinary
        include_hh_info: Wenn True, gibt (sims, hh_name, creator) zurück
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except Exception:
        return ([], "", "") if include_hh_info else []

    # Householdbinary hat einen 16-Byte-Header (Version, Größen, Reserved)
    # Protobuf-Daten beginnen ab Offset 16
    if len(data) < 20:
        return ([], "", "") if include_hh_info else []
    pb_data = data[16:]

    sims: list[tuple[str, str, int]] = []
    hh_name = ""
    creator = ""
    top = _pb_parse(pb_data)

    for t1, blob1 in top.get(1, []):
        if t1 != "bytes" or len(blob1) < 20:
            continue
        sub1 = _pb_parse(blob1)

        # Haushaltsdaten (Name, Creator) — gleicher Blob, kein zweites Lesen!
        if include_hh_info and not hh_name:
            hh_name = _pb_string(sub1, 3)
            creator = _pb_string(sub1, 15)

        for t6, blob6 in sub1.get(6, []):
            if t6 != "bytes" or len(blob6) < 10:
                continue
            sim_fields = _pb_parse(blob6)
            first = _pb_string(sim_fields, 5)
            last = _pb_string(sim_fields, 6)
            tray_id = _pb_fixed64(sim_fields, 1)
            if first and first != '.' and tray_id:
                sims.append((first, last if last and last != '.' else '', tray_id))

    if include_hh_info:
        return sims, hh_name, creator
    return sims


# ── Portrait-Index aufbauen ──────────────────────────────────────

def build_portrait_index(tray_dir: str) -> tuple:
    """Baut Index: 'Vorname Nachname' → Pfad zur SGI-Datei.

    Jeder Sim im Haushalt bekommt einen eigenen Type-Prefix:
        Sim 0 → 0x00000013, Sim 1 → 0x00000023, Sim 2 → 0x00000033, ...
    
    1. Sammelt ALLE SGI-Dateinamen → {instance_id_lower: sgi_path}
    2. Parst jede .householdbinary → Sim-Namen + Tray-IDs
    3. Sucht SGI per Instance-ID (unabhängig vom Type-Prefix)
    4. Gibt (portrait_dict, tray_households) zurück

    Returns:
        tuple: (dict[str, str], list) — ({full_name: sgi_path}, tray_households)
    """
    if not tray_dir or not os.path.isdir(tray_dir):
        return {}, []

    # Instance-ID (lowercase hex, z.B. "0x0571160a04335212") → SGI-Pfad
    sgi_by_instance: dict[str, str] = {}
    hh_files: list[str] = []

    for entry in os.scandir(tray_dir):
        if not entry.is_file():
            continue
        if entry.name.endswith(".sgi") and "!" in entry.name:
            # Dateiname: 0x{type}!0x{instance}.sgi → Instance extrahieren
            parts = entry.name.split("!", 1)
            if len(parts) == 2:
                instance_id = parts[1].replace(".sgi", "").lower()
                sgi_by_instance[instance_id] = entry.path
        elif entry.name.endswith(".householdbinary"):
            hh_files.append(entry.path)

    if not sgi_by_instance:
        return {}

    result: dict[str, str] = {}
    # Zusätzlich: Tray-Haushalte sammeln für Rename-Matching
    # Liste von [(tray_name, sgi_path), ...] pro Haushalt
    _tray_households: list[list[tuple[str, str]]] = []

    for hh_path in hh_files:
        sims = _extract_sims_from_householdbinary(hh_path)
        hh_members: list[tuple[str, str]] = []
        for first_name, last_name, tray_sim_id in sims:
            instance_key = f"0x{tray_sim_id:016x}"
            sgi_path = sgi_by_instance.get(instance_key)
            if sgi_path:
                full_name = f"{first_name} {last_name}".strip()
                hh_members.append((full_name, sgi_path))
                if full_name and full_name not in result:
                    result[full_name] = sgi_path
        if hh_members:
            _tray_households.append(hh_members)

    return result, _tray_households


def match_renamed_sims(portrait_index: dict[str, str],
                       tray_households: list,
                       savegame_households: dict[str, list[str]]) -> dict[str, str]:
    """Matcht umbenannte Sims über Haushalt-Zugehörigkeit.

    Wenn in einem Savegame-Haushalt einige Sims per Name ein Portrait haben,
    aber andere nicht, versucht diese Funktion die übrigen SGI-Portraits
    aus dem passenden Tray-Haushalt zuzuordnen.

    Args:
        portrait_index: Index von build_portrait_index()
        tray_households: Tray-Haushalte von build_portrait_index()
        savegame_households: {household_name: [full_name, ...]}

    Returns:
        Zusätzliche Zuordnungen {savegame_name: sgi_path}
    """
    if not tray_households or not isinstance(tray_households, list):
        return {}

    extra: dict[str, str] = {}

    for hh_name, save_members in savegame_households.items():
        # Welche Savegame-Sims haben schon ein Portrait?
        matched_save = {n for n in save_members if n in portrait_index}
        unmatched_save = [n for n in save_members if n not in portrait_index]
        if not unmatched_save:
            continue  # Alle haben schon Portraits

        # Finde den Tray-Haushalt mit den meisten Namens-Treffern
        best_tray_hh = None
        best_score = 0
        for tray_hh in tray_households:
            tray_names = {name for name, _ in tray_hh}
            overlap = matched_save & tray_names
            if len(overlap) > best_score:
                best_score = len(overlap)
                best_tray_hh = tray_hh

        if not best_tray_hh or best_score == 0:
            continue  # Kein Tray-Haushalt passt

        # Welche Tray-Sims wurden noch nicht zugeordnet?
        tray_matched_names = {name for name, _ in best_tray_hh if name in matched_save}
        tray_unmatched = [(name, path) for name, path in best_tray_hh
                          if name not in tray_matched_names]

        # Wenn genau gleich viele übrig sind → 1:1 zuordnen (nach Position)
        if len(tray_unmatched) == len(unmatched_save):
            for save_name, (_, sgi_path) in zip(unmatched_save, tray_unmatched):
                extra[save_name] = sgi_path
        elif len(tray_unmatched) == 1 and len(unmatched_save) >= 1:
            # Nur 1 Tray-Sim übrig → dem ersten unmatched zuordnen
            extra[unmatched_save[0]] = tray_unmatched[0][1]

    return extra


def get_portrait_jpeg(portrait_index: dict[str, str], sim_name: str) -> bytes | None:
    """Gibt entschlüsselte JPEG-Bytes für einen Sim zurück (nach Name).

    Args:
        portrait_index: Index von build_portrait_index()
        sim_name: Voller Sim-Name ('Vorname Nachname')
    """
    sgi_path = portrait_index.get(sim_name)
    if not sgi_path or not os.path.isfile(sgi_path):
        return None
    return _decrypt_sgi(sgi_path)


# ── Bibliothek-Index: Alle Tray-Haushalte mit Sims ──────────────

def build_library_index(tray_dir: str) -> list[dict]:
    """Baut einen Index aller Tray-Haushalte mit ihren Sims und Portraits.

    Rückgabe: Liste von Haushalts-Dicts:
        {
            "name": "Haushaltsname",
            "creator": "Gallery-Creator" oder "",
            "filename": "0x...householdbinary",
            "sims": [
                {"full_name": "Vorname Nachname", "has_portrait": True/False},
                ...
            ]
        }
    """
    if not tray_dir or not os.path.isdir(tray_dir):
        return []

    # SGI-Dateien sammeln
    sgi_by_instance: dict[str, str] = {}
    hh_files: list[str] = []

    for entry in os.scandir(tray_dir):
        if not entry.is_file():
            continue
        if entry.name.endswith(".sgi") and "!" in entry.name:
            parts = entry.name.split("!", 1)
            if len(parts) == 2:
                instance_id = parts[1].replace(".sgi", "").lower()
                sgi_by_instance[instance_id] = entry.path
        elif entry.name.endswith(".householdbinary"):
            hh_files.append(entry.path)

    households: list[dict] = []

    for hh_path in hh_files:
        # Sims + Haushaltsinfo in einem einzigen File-Read
        sims_data, hh_name, creator = _extract_sims_from_householdbinary(hh_path, include_hh_info=True)
        if not sims_data:
            continue

        sims_list = []
        for first_name, last_name, tray_sim_id in sims_data:
            full_name = f"{first_name} {last_name}".strip()
            instance_key = f"0x{tray_sim_id:016x}"
            has_portrait = instance_key in sgi_by_instance
            sims_list.append({
                "full_name": full_name,
                "has_portrait": has_portrait,
            })

        households.append({
            "name": hh_name or os.path.basename(hh_path),
            "creator": creator,
            "filename": os.path.basename(hh_path),
            "sim_count": len(sims_list),
            "sims": sims_list,
            "file_id": os.path.basename(hh_path).split("!")[1].split(".")[0] if "!" in os.path.basename(hh_path) else os.path.basename(hh_path),
        })

    # Eindeutige Namen für Duplikate erstellen
    name_counts = {}
    for hh in households:
        base_name = hh["name"]
        if base_name in name_counts:
            name_counts[base_name] += 1
            hh["display_name"] = f"{base_name} #{name_counts[base_name]}"
        else:
            name_counts[base_name] = 1
            hh["display_name"] = base_name

    households.sort(key=lambda h: h["display_name"].lower())
    return households
