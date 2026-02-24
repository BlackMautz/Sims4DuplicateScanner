# -*- coding: utf-8 -*-
"""Tray-Analyse: Erkennt welche CC/Mods von gespeicherten Sims, Häusern und Räumen verwendet werden."""

from __future__ import annotations

import os
import struct as _struct
import time
import concurrent.futures
from pathlib import Path
from collections import defaultdict

from .dbpf import read_dbpf_resource_keys
from .protobuf import decode_varint


# ── Protobuf-Hilfsfunktionen (nutzt shared protobuf.py) ─────────

_decode_varint = decode_varint


def _scan_protobuf_instances(data: bytes) -> set:
    """Scannt Protobuf-Daten rekursiv nach großen Varint/Fixed64-Werten (Instance-IDs)."""
    instances = set()
    _scan_pb_recursive(data, instances, 0)
    return instances


def _scan_pb_recursive(data: bytes, instances: set, depth: int):
    """Rekursiver Protobuf-Scanner für Instance-IDs."""
    if depth > 8 or len(data) < 2:
        return
    pos = 0
    while pos < len(data) - 1:
        try:
            tag, pos2 = _decode_varint(data, pos)
            if tag == 0:
                pos = pos2
                continue
            field_num = tag >> 3
            wire_type = tag & 0x07
            if field_num > 500 or field_num == 0:
                pos += 1
                continue

            if wire_type == 0:  # Varint
                value, pos = _decode_varint(data, pos2)
                if value >= 0x100000000:  # > 32 Bit → wahrscheinlich Instance-ID
                    instances.add(value)
            elif wire_type == 1:  # Fixed64
                if pos2 + 8 > len(data):
                    break
                value = _struct.unpack_from('<Q', data, pos2)[0]
                pos = pos2 + 8
                if value > 0:
                    instances.add(value)
            elif wire_type == 2:  # Length-delimited (verschachteltes Protobuf)
                length, pos3 = _decode_varint(data, pos2)
                if length < 0 or length > len(data) - pos3:
                    pos += 1
                    continue
                blob = data[pos3:pos3 + length]
                pos = pos3 + length
                _scan_pb_recursive(blob, instances, depth + 1)
            elif wire_type == 5:  # Fixed32
                if pos2 + 4 > len(data):
                    break
                pos = pos2 + 4
            else:
                pos += 1
        except Exception:
            pos += 1


# ── Trayitem-Parser ─────────────────────────────────────────────

TRAY_TYPE_NAMES = {1: "Haushalt", 2: "Grundstück", 3: "Raum"}


def parse_trayitem(filepath: str | Path) -> dict | None:
    """Parst eine .trayitem-Datei und extrahiert Metadaten.

    Returns:
        dict mit Feldern: instance_id, type, type_name, name, description,
        creator_name, creator_hash, oder None bei Fehler.
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        if len(data) < 16:
            return None
    except Exception:
        return None

    # 8-Byte Header überspringen, dann Protobuf parsen
    pos = 8
    result = {
        'instance_id': 0,
        'type': 0,
        'type_name': 'Unbekannt',
        'name': '',
        'description': '',
        'creator_name': '',
        'creator_hash': 0,
    }

    while pos < len(data):
        try:
            tag, pos2 = _decode_varint(data, pos)
            if tag == 0:
                pos = pos2
                continue
            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                value, pos = _decode_varint(data, pos2)
                if field_num == 1:
                    result['instance_id'] = value
                elif field_num == 2:
                    result['type'] = value
                    result['type_name'] = TRAY_TYPE_NAMES.get(value, 'Unbekannt')
                elif field_num == 6:
                    result['creator_hash'] = value
            elif wire_type == 1:  # Fixed64
                pos = pos2 + 8
            elif wire_type == 2:  # Length-delimited
                length, pos3 = _decode_varint(data, pos2)
                if length < 0 or length > len(data) - pos3:
                    break
                blob = data[pos3:pos3 + length]
                pos = pos3 + length
                if field_num == 4:
                    try:
                        result['name'] = blob.decode('utf-8')
                    except Exception:
                        result['name'] = blob.decode('latin-1', errors='replace')
                elif field_num == 5:
                    try:
                        result['description'] = blob.decode('utf-8')[:200]
                    except Exception:
                        result['description'] = ''
                elif field_num == 7:
                    try:
                        result['creator_name'] = blob.decode('utf-8')
                    except Exception:
                        result['creator_name'] = ''
            elif wire_type == 5:  # Fixed32
                pos = pos2 + 4
            else:
                break
        except Exception:
            break

    return result if result['instance_id'] != 0 else None


# ── Tray-Ordner-Analyse ─────────────────────────────────────────

def _group_tray_files(tray_dir: str | Path) -> dict:
    """Gruppiert alle Tray-Dateien nach Instance-ID.

    Returns:
        dict: instance_hex -> {'trayitem': path, 'binaries': [paths], 'types': set}
    """
    tray_dir = Path(tray_dir)
    if not tray_dir.is_dir():
        return {}

    groups = {}  # instance_hex -> info

    for fn in os.listdir(tray_dir):
        if '!' not in fn or '.' not in fn:
            continue
        parts = fn.split('!')
        if len(parts) != 2:
            continue

        instance_hex = parts[1].rsplit('.', 1)[0]  # z.B. 0x000015720ea50381
        ext = fn.rsplit('.', 1)[-1].lower()
        fp = tray_dir / fn

        if instance_hex not in groups:
            groups[instance_hex] = {'trayitem': None, 'binaries': [], 'types': set()}

        if ext == 'trayitem' and parts[0] in ('0x00000001', '0x00000002', '0x00000003'):
            # Haupttrayitem (Prefix 01=Haushalt, 02=Grundstück, 03=Raum)
            existing = groups[instance_hex]['trayitem']
            if existing is None or parts[0] < str(existing.name).split('!')[0]:
                groups[instance_hex]['trayitem'] = fp
        elif ext in ('householdbinary', 'hhi', 'blueprint', 'bpi', 'sgi', 'room', 'rmi'):
            groups[instance_hex]['binaries'].append(fp)
            groups[instance_hex]['types'].add(ext)

    return groups


def _extract_instances_from_binary(filepath: Path) -> set:
    """Extrahiert Instance-IDs aus einer Tray-Binärdatei via Protobuf-Scan."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        if len(data) < 8:
            return set()
        # Header überspringen (4–12 Bytes je nach Typ)
        ext = filepath.suffix.lower().lstrip('.')
        if ext == 'householdbinary':
            skip = 12  # version(4) + size(4) + padding(4)
        elif ext in ('hhi', 'bpi', 'rmi'):
            skip = 4   # size-header
        elif ext == 'blueprint':
            skip = 12
        elif ext == 'sgi':
            skip = 4
        elif ext == 'room':
            skip = 4
        else:
            skip = 4
        return _scan_protobuf_instances(data[skip:])
    except Exception:
        return set()


# ── Mod-Instance-Index ───────────────────────────────────────────

def build_mod_instance_index(mod_dirs: list[Path], progress_cb=None) -> dict:
    """Baut einen Index: Instance-ID → set(mod_pfade).

    Verwendet einen Disk-Cache (mtime+size pro .package) um bei Wiederholungen
    das erneute Lesen aller DBPF-Dateien zu vermeiden.

    Args:
        mod_dirs: Liste von Mod-Verzeichnissen zum Scannen
        progress_cb: Optional callback(current, total, filename)

    Returns:
        dict: instance_id (int) → set von Dateipfaden
    """
    from .config import load_tray_cache, save_tray_cache

    index = defaultdict(set)
    pkg_files = []

    for mod_dir in mod_dirs:
        if not mod_dir.is_dir():
            continue
        for root, dirs, files in os.walk(mod_dir):
            for fn in files:
                if fn.lower().endswith('.package'):
                    pkg_files.append(Path(root) / fn)

    # Disk-Cache laden: {Pfad: {mt, sz, keys: [(t,g,i), ...]}}
    tray_disk_cache = load_tray_cache()
    cached_entries = tray_disk_cache.get("mod_index_entries", {})
    new_entries = {}
    cache_hits = 0

    total = len(pkg_files)
    print(f"[TRAY] Mod-Index: {total} .package Dateien werden gelesen...", flush=True)
    t0 = time.time()

    # ── Phase 1: Cache-Hits sofort verarbeiten, Cache-Misses sammeln ──
    cache_miss_files = []  # (index, pkg_path, stat) für paralleles Lesen
    for i, pkg_path in enumerate(pkg_files):
        pkg_str = str(pkg_path)
        try:
            st = pkg_path.stat()
            cached = cached_entries.get(pkg_str)
            if cached and abs(cached.get('mt', 0) - st.st_mtime) < 0.01 and cached.get('sz', -1) == st.st_size:
                # Cache-Hit: sofort verarbeiten
                inst_ids = cached.get('ids') or cached.get('keys')
                cache_hits += 1
                if inst_ids:
                    for item in inst_ids:
                        if isinstance(item, (list, tuple)) and len(item) >= 3:
                            index[item[2]].add(pkg_str)
                        else:
                            index[item].add(pkg_str)
                    new_entries[pkg_str] = {
                        'mt': st.st_mtime,
                        'sz': st.st_size,
                        'ids': inst_ids if not isinstance(inst_ids[0], (list, tuple)) else list({x[2] for x in inst_ids}),
                    }
                else:
                    new_entries[pkg_str] = {'mt': st.st_mtime, 'sz': st.st_size, 'ids': []}
            else:
                cache_miss_files.append((i, pkg_path, st))
        except Exception:
            pass
        if progress_cb and (i % 200 == 0 or i == total - 1):
            progress_cb(i + 1, total, pkg_path.name)

    print(f"[TRAY] {cache_hits} Cache-Hits, {len(cache_miss_files)} Cache-Misses → parallel lesen...", flush=True)

    # ── Phase 2: Cache-Misses parallel lesen (I/O-bound) ──
    def _read_pkg(args):
        _i, _path, _st = args
        try:
            raw_keys = read_dbpf_resource_keys(_path)
            if raw_keys:
                ids = list({k[2] for k in raw_keys})
            else:
                ids = []
            return (str(_path), _st.st_mtime, _st.st_size, ids)
        except Exception:
            return (str(_path), _st.st_mtime, _st.st_size, [])

    if cache_miss_files:
        workers = min(6, len(cache_miss_files))  # Nicht zu viele für Disk-I/O
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            _miss_done = 0
            for result_tuple in pool.map(_read_pkg, cache_miss_files):
                _miss_done += 1
                pkg_str, mt, sz, inst_ids = result_tuple
                if inst_ids:
                    for item in inst_ids:
                        if isinstance(item, (list, tuple)) and len(item) >= 3:
                            index[item[2]].add(pkg_str)
                        else:
                            index[item].add(pkg_str)
                    new_entries[pkg_str] = {'mt': mt, 'sz': sz, 'ids': inst_ids}
                else:
                    new_entries[pkg_str] = {'mt': mt, 'sz': sz, 'ids': []}
                if _miss_done % 200 == 0:
                    print(f"[TRAY] Cache-Miss: {_miss_done}/{len(cache_miss_files)} gelesen...", flush=True)

    # Cache auf Disk speichern (nur Instance-IDs, nicht volle Keys)
    elapsed = time.time() - t0
    print(f"[TRAY] Index fertig: {total} Dateien in {elapsed:.1f}s ({cache_hits} aus Cache)", flush=True)
    print("[TRAY] Cache wird gespeichert...", flush=True)
    tray_disk_cache["mod_index_entries"] = new_entries
    save_tray_cache(tray_disk_cache)
    print("[TRAY] Cache gespeichert.", flush=True)

    return dict(index)


# ── Hauptanalyse ─────────────────────────────────────────────────

def analyze_tray(tray_dir: str | Path,
                 mod_instance_index: dict,
                 progress_cb=None) -> dict:
    """Analysiert den Tray-Ordner und findet CC-Abhängigkeiten.

    Args:
        tray_dir: Pfad zum Sims 4 Tray-Ordner
        mod_instance_index: Instance-ID → set(mod_pfade) Index
        progress_cb: Optional callback(current, total, name)

    Returns:
        dict mit:
            items: Liste von Tray-Einträgen mit Mod-Referenzen
            mod_usage: dict mod_pfad → set(item_names)
            summary: Zusammenfassung
    """
    tray_dir = Path(tray_dir)
    if not tray_dir.is_dir():
        return {'items': [], 'mod_usage': {}, 'summary': _empty_summary()}

    # Phase 1: Tray-Dateien gruppieren
    file_groups = _group_tray_files(tray_dir)

    # Phase 2: Trayitems parsen + Binärdateien scannen
    items = []
    mod_usage = defaultdict(set)  # mod_pfad → set(item_namen)
    total = len(file_groups)
    processed = 0

    for instance_hex, group_info in file_groups.items():
        trayitem_path = group_info.get('trayitem')
        if not trayitem_path:
            continue

        # Metadaten parsen
        meta = parse_trayitem(trayitem_path)
        if not meta:
            continue

        # Instance-IDs aus allen zugehörigen Binärdateien extrahieren
        all_instances = set()
        for bin_path in group_info['binaries']:
            instances = _extract_instances_from_binary(bin_path)
            all_instances.update(instances)

        # Cross-Reference mit Mod-Index
        used_mods = {}  # mod_pfad → anzahl_matches
        for inst_id in all_instances:
            if inst_id in mod_instance_index:
                for mod_path in mod_instance_index[inst_id]:
                    used_mods[mod_path] = used_mods.get(mod_path, 0) + 1

        # Mod-Usage-Map aktualisieren
        item_name = meta.get('name', 'Unbekannt')
        for mod_path in used_mods:
            mod_usage[mod_path].add(item_name)

        # Item-Objekt erstellen
        item = {
            'instance_id': instance_hex,
            'type': meta['type'],
            'type_name': meta['type_name'],
            'name': item_name,
            'creator': meta.get('creator_name', ''),
            'description': meta.get('description', '')[:100],
            'binary_count': len(group_info['binaries']),
            'instance_count': len(all_instances),
            'cc_count': len(used_mods),
            'used_mods': [
                {
                    'path': mp,
                    'name': Path(mp).name,
                    'matches': cnt,
                }
                for mp, cnt in sorted(used_mods.items(),
                                      key=lambda x: -x[1])
            ],
        }
        items.append(item)

        processed += 1
        if progress_cb and (processed % 20 == 0 or processed == total):
            progress_cb(processed, total, item_name)

    # Sortieren: zuerst nach Typ, dann nach Name
    items.sort(key=lambda x: (x['type'], x['name'].lower()))

    # Mod-Usage-Map in serialisierbare Form
    mod_usage_final = {}
    for mod_path, item_names in sorted(mod_usage.items()):
        mod_usage_final[mod_path] = {
            'name': Path(mod_path).name,
            'used_by': sorted(item_names),
            'used_count': len(item_names),
        }

    summary = {
        'total_items': len(items),
        'households': sum(1 for i in items if i['type'] == 1),
        'lots': sum(1 for i in items if i['type'] == 2),
        'rooms': sum(1 for i in items if i['type'] == 3),
        'items_with_cc': sum(1 for i in items if i['cc_count'] > 0),
        'total_mods_used': len(mod_usage_final),
        'max_cc_item': max((i['name'] for i in items if i['cc_count'] > 0),
                          default=''),
        'max_cc_count': max((i['cc_count'] for i in items), default=0),
    }

    return {
        'items': items,
        'mod_usage': mod_usage_final,
        'summary': summary,
    }


def _empty_summary() -> dict:
    return {
        'total_items': 0, 'households': 0, 'lots': 0, 'rooms': 0,
        'items_with_cc': 0, 'total_mods_used': 0,
        'max_cc_item': '', 'max_cc_count': 0,
    }


# ── Schnellprüfung: Wird ein Mod verwendet? ─────────────────────

def check_mod_in_use(mod_path: str | Path,
                     tray_dir: str | Path,
                     mod_instance_index: dict | None = None) -> list[str]:
    """Prüft ob ein Mod von Tray-Items verwendet wird.

    Args:
        mod_path: Pfad zur .package Mod-Datei
        tray_dir: Pfad zum Tray-Ordner
        mod_instance_index: Optional vorberechneter Index

    Returns:
        Liste von Tray-Item-Namen die den Mod verwenden
    """
    mod_path = Path(mod_path)
    if not mod_path.is_file():
        return []

    # Instance-IDs des Mods auslesen
    keys = read_dbpf_resource_keys(mod_path)
    if not keys:
        return []
    mod_instances = {inst for _t, _g, inst in keys}

    # Tray-Dateien scannen
    tray_dir = Path(tray_dir)
    if not tray_dir.is_dir():
        return []

    file_groups = _group_tray_files(tray_dir)
    used_by = []

    for instance_hex, group_info in file_groups.items():
        trayitem_path = group_info.get('trayitem')
        if not trayitem_path:
            continue

        # Binärdateien scannen
        for bin_path in group_info['binaries']:
            tray_instances = _extract_instances_from_binary(bin_path)
            overlap = mod_instances & tray_instances
            if overlap:
                meta = parse_trayitem(trayitem_path)
                if meta:
                    used_by.append(meta.get('name', 'Unbekannt'))
                break

    return sorted(set(used_by))
