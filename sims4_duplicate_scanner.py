# -*- coding: utf-8 -*-
"""
Sims4 Duplikate Scanner + Web-UI (localhost)

Findet und entfernt doppelte Mod-Dateien mit:
- Batch-Duplikat-Löschen/Quarantäne (Checkboxen)
- Automatische ZIP-Backups vor dem Scan
- Detailliertes Aktions-Log mit CSV-Export
- Web-basierte Verwaltungs-UI

Hinweis: Standard-Empfehlung ist Quarantäne (sicherer), aber Löschen geht auch.
"""

from __future__ import annotations

import os
import re
import threading
import hashlib
import time
import json
import shutil
import secrets
import socket
import webbrowser
import zipfile
import zlib
import base64
import ctypes
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
SCANNER_VERSION = "2.3.0"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1470190485824868544/eDQYj0eHWK8EbeIeiuDdAWirjWZLWtYHDPHE6YuhhkVLfoGdiXaxfP2fOYX_3f9r4rKe"

# ---- Persistente Einstellungen (Ordner/Optionen merken) ----
def _default_config_path() -> Path:
    # Windows: %APPDATA%\Sims4DupeScanner\config.json
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / "sims4_duplicate_scanner_config.json"
    return Path.home() / ".sims4_duplicate_scanner_config.json"


CONFIG_PATH = _default_config_path()

# ---- DBPF-Analyse-Cache (Kategorien zwischenspeichern) ----
def _default_deep_cache_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / "dbpf_deep_cache.json"
    return Path.home() / ".sims4_dbpf_deep_cache.json"

_DEEP_CACHE_PATH = _default_deep_cache_path()


def load_deep_cache() -> dict:
    """Lädt den DBPF-Analyse-Cache von Disk. Gibt dict {path: {mt, sz, deep}} zurück."""
    try:
        if _DEEP_CACHE_PATH.exists():
            data = json.loads(_DEEP_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("version") == 1:
                return data.get("entries", {})
    except Exception:
        pass
    return {}


def save_deep_cache(entries: dict) -> None:
    """Speichert den DBPF-Analyse-Cache auf Disk."""
    try:
        _DEEP_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "entries": entries}
        _DEEP_CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8",
        )
    except Exception:
        pass


def _cache_entry_valid(entry: dict, path: Path) -> bool:
    """Prüft ob ein Cache-Eintrag noch aktuell ist (gleiche mtime + Größe)."""
    try:
        st = path.stat()
        return (abs(entry.get('mt', 0) - st.st_mtime) < 0.01
                and entry.get('sz', -1) == st.st_size)
    except Exception:
        return False


def _analyze_with_cache(path: Path, deep_cache: dict | None):
    """Führt analyze_package_deep aus mit Cache-Unterstützung.

    Gibt (info_dict, all_keys) oder None zurück.
    Wenn nur info_dict aus dem Cache kommt, wird all_keys=None.
    """
    ps = str(path)
    if deep_cache is not None and ps in deep_cache:
        ce = deep_cache[ps]
        if _cache_entry_valid(ce, path):
            return (ce['deep'], None)  # aus Cache, keine all_keys
    # Nicht gecached → frisch analysieren
    result = analyze_package_deep(path)
    if result and deep_cache is not None:
        try:
            st = path.stat()
            deep_cache[ps] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': result[0]}
        except Exception:
            pass
    return result


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Im Notfall nicht crashen, nur nicht speichern
        pass
# -----------------------------------------------------------


def normalize_exts(ext_text: str) -> set[str]:
    ext_text = (ext_text or "").strip()
    if ext_text == "" or ext_text == "*":
        return set()  # empty = allow all
    exts = {e.strip().lower() for e in ext_text.split(",") if e.strip()}
    return {e if e.startswith(".") else f".{e}" for e in exts}


def normalize_ignore_dirs(ignore_text: str) -> set[str]:
    ignore_text = (ignore_text or "").strip()
    return {d.strip().lower() for d in ignore_text.split(",") if d.strip()}


def safe_stat(p: Path):
    try:
        st = p.stat()
        return st.st_size, st.st_mtime
    except Exception:
        return None, None


def human_size(n: int | None) -> str:
    if n is None:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.2f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return f"{n} B"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def best_root_index(path: Path, roots: list[Path]) -> int | None:
    # Try both original and resolved paths to handle junctions/symlinks
    candidates = set()
    candidates.add(str(path).lower())
    try:
        candidates.add(str(path.resolve()).lower())
    except Exception:
        pass

    best_i = None
    best_len = -1
    for i, r in enumerate(roots):
        root_candidates = set()
        root_candidates.add(str(r).lower())
        try:
            root_candidates.add(str(r.resolve()).lower())
        except Exception:
            pass

        for ps in candidates:
            for rs in root_candidates:
                if ps.startswith(rs) and len(rs) > best_len:
                    best_i = i
                    best_len = len(rs)
    return best_i


def is_under_any_root(path: Path, roots: list[Path]) -> bool:
    """Security: allow actions only inside chosen roots.
    Handles junctions/symlinks by checking both original and resolved paths."""
    # Collect all path variants (original + resolved)
    path_variants = set()
    path_variants.add(str(path).lower().rstrip("\\/"))
    try:
        path_variants.add(str(path.resolve()).lower().rstrip("\\/"))
    except Exception:
        pass

    if not path_variants:
        return False

    for r in roots:
        root_variants = set()
        root_variants.add(str(r).lower().rstrip("\\/"))
        try:
            root_variants.add(str(r.resolve()).lower().rstrip("\\/"))
        except Exception:
            pass

        for ps in path_variants:
            for rs in root_variants:
                if ps == rs:
                    return True
                if ps.startswith(rs + os.sep):
                    return True
    return False


def ensure_unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suf = dest.suffix
    parent = dest.parent
    for i in range(1, 10000):
        cand = parent / f"{stem}__dup{i}{suf}"
        if not cand.exists():
            return cand
    return parent / f"{stem}__dup{int(time.time())}{suf}"


# ---- Ähnliche Dateinamen: Normalisierung ----

_VERSION_RE = re.compile(
    r'[_\- ]+'            # PFLICHT-Trenner (mindestens einer)
    r'(?:'
    r'v\d+[\._]?\d*[a-z]?'               # v-Prefix: v185, v1.5, v185e
    r'|\d{3,}[a-z]?'                     # 3+ Ziffern ohne v: 185, 185e, 2024
    r'|\d+\.\d+(?:\.\d+)*[a-z]?'         # Semver ohne v: 1.5, 1.5.3
    r')'
    r'(?:[_\- ]*(?:patch|fix|update|hotfix)\d*)?',  # optionale Suffixe
    re.IGNORECASE,
)

_COPY_RE = re.compile(
    r'[_\- ]*(?:'
    r'\(\d+\)'            # (1), (2)
    r'|copy'              # Copy
    r'|kopie'             # Kopie (deutsch)
    r'|- copy'            # - Copy
    r'|_old'              # _old
    r'|_backup'           # _backup
    r'|_bak'              # _bak
    r'|_original'         # _original
    r'|_new'              # _new
    r'|_neu'              # _neu
    r')',
    re.IGNORECASE,
)

_EXTRA_STRIP_RE = re.compile(r'[_\- ]+$')  # Trailing separators


def normalize_mod_name(filename: str) -> str:
    """Normalisiert einen Mod-Dateinamen für Ähnlichkeitsvergleich.
    
    Entfernt: Versionsnummern, (1)-Kopien, _old/_backup, Sonderzeichen.
    'WickedWhims_v185e.package' → 'wickedwhims'
    'MyMod (1).package' → 'mymod'
    'cool_mod_v3_backup.ts4script' → 'cool_mod'
    """
    # Extension entfernen
    name = Path(filename).stem.lower()
    
    # Copy/Backup-Suffixe entfernen (vor Version, können mehrfach vorkommen)
    for _ in range(3):
        name = _COPY_RE.sub('', name)
    
    # Versionsnummern entfernen (von rechts, können mehrfach sein)
    for _ in range(3):
        name = _VERSION_RE.sub('', name, count=1)
    
    # Trailing separators
    name = _EXTRA_STRIP_RE.sub('', name)
    
    # Leer? Dann lieber den Original-Stem zurückgeben
    if not name.strip():
        name = Path(filename).stem.lower()
    
    return name.strip()


import struct as _struct

# Bekannte DBPF Resource Types (TS4)
_RESOURCE_TYPE_NAMES = {
    0x034AEECB: "CAS Part",
    0x00B2D882: "Object Definition",
    0x545AC67A: "Buff Tuning",
    0x03B33DDF: "Trait Tuning",
    0xE882D22F: "Object Tuning",
    0x339BC0E4: "Interaction Tuning",
    0x0C772E27: "Lot Tuning",
    0xCB5FDDC7: "Action Tuning",
    0xC0DB5AE7: "Instance Tuning",
    0x6017E896: "Sim Data",
    0x220557DA: "Sim Info",
    0xD382BF57: "Texture (LRLE)",
    0x00000000: "Null",
    0x736884F1: "Region Tuning",
    0xE5105066: "Recipe Tuning",
    0x7FB6AD72: "Aspiration Tuning",
    0x0904DF10: "Career Tuning",
    0x8B18FF6E: "Walkby Tuning",
    0x6A4ABC1C: "Situation Tuning",
    # --- Erweiterte Typen für Tiefenanalyse ---
    0x015A1849: "Mesh (GEOM)",
    0x01D10F34: "Blend Geometry",
    0x0166038C: "NameMap",
    0x3C1AF1F2: "Thumbnail",
    0x2F7D0004: "DST Image",
    0x00AE6C67: "Bone Delta",
    0x062C8204: "Hotspot Control",
    0x025ED6F4: "Sim Outfit",
    0xD3044521: "Color List",
    0x0355E0A6: "Footprint",
    0xB61DE6B4: "Region Sort",
    0xF1EDBD86: "Slot Tuning",
}

def _res_type_name(type_id: int) -> str:
    return _RESOURCE_TYPE_NAMES.get(type_id, f"0x{type_id:08X}")


def read_dbpf_resource_keys(path: Path) -> list[tuple[int, int, int]] | None:
    """Liest Resource Keys (Type, Group, Instance) aus einer DBPF v2 .package-Datei.
    
    Returns: Liste von (type, group, instance) Tupeln, oder None bei Fehler.
    """
    try:
        with open(path, 'rb') as f:
            header = f.read(96)
            if len(header) < 96 or header[:4] != b'DBPF':
                return None
            major = _struct.unpack_from('<I', header, 4)[0]
            if major != 2:
                return None

            entry_count = _struct.unpack_from('<I', header, 36)[0]
            index_size = _struct.unpack_from('<I', header, 44)[0]
            index_offset = _struct.unpack_from('<Q', header, 64)[0]

            if entry_count == 0:
                return []
            if index_offset == 0 or index_size < 4:
                return []

            f.seek(index_offset)
            index_data = f.read(index_size)
            if len(index_data) < index_size:
                return None

        pos = 0
        flags = _struct.unpack_from('<I', index_data, pos)[0]
        pos += 4

        # Konstante Werte für gesetzte Flag-Bits: Type, Group, InstanceHi, InstanceLo
        const_vals = [None, None, None, None]
        for i in range(4):
            if flags & (1 << i):
                if pos + 4 > len(index_data):
                    return None
                const_vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                pos += 4

        # Per-Entry-Größe berechnen
        header_bytes = pos
        remaining = index_size - header_bytes
        if entry_count > 0 and remaining > 0:
            entry_size = remaining // entry_count
        else:
            return []

        key_field_count = sum(1 for v in const_vals if v is None)
        key_bytes = key_field_count * 4
        skip_bytes = entry_size - key_bytes
        if skip_bytes < 0:
            return None

        keys = []
        for _ in range(entry_count):
            vals = list(const_vals)
            for i in range(4):
                if vals[i] is None:
                    if pos + 4 > len(index_data):
                        break
                    vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                    pos += 4
            if None in vals:
                break
            rtype, group, ihi, ilo = vals
            instance = (ihi << 32) | ilo
            keys.append((rtype, group, instance))
            pos += skip_bytes

        return keys
    except Exception:
        return None


def check_package_integrity(path: Path) -> str:
    """Prüft die DBPF-Integrität einer .package-Datei.
    
    Returns:
        'ok'            - Datei ist eine gültige DBPF v2 Datei
        'empty'         - Datei ist leer (0 Bytes)
        'too_small'     - Datei kleiner als 96 Bytes (DBPF-Header)
        'no_dbpf'       - Kein DBPF-Magic-Header gefunden
        'wrong_version' - DBPF v1 (TS2/TS3) statt v2 (TS4)
        'unreadable'    - Datei konnte nicht gelesen werden
    """
    try:
        size = path.stat().st_size
        if size == 0:
            return 'empty'
        if size < 96:
            return 'too_small'
        with open(path, 'rb') as f:
            header = f.read(96)
        if len(header) < 96:
            return 'too_small'
        # Magic: "DBPF" (0x44 0x42 0x50 0x46)
        if header[:4] != b'DBPF':
            return 'no_dbpf'
        # Major Version (uint32 LE at offset 4): 2 = TS4
        major = _struct.unpack_from('<I', header, 4)[0]
        if major != 2:
            return 'wrong_version'
        return 'ok'
    except (PermissionError, OSError):
        return 'unreadable'


def extract_version(filename: str) -> str:
    """Versucht eine Versionsnummer aus dem Dateinamen zu extrahieren."""
    stem = Path(filename).stem
    # Suche nach v185e, v1.5, _v3, etc.
    m = re.search(r'[_\- ]v(\d+(?:[\._]\d+)*[a-z]?)', stem, re.IGNORECASE)
    if m:
        return 'v' + m.group(1)
    # Semver ohne v: _1.5.3, _185e (mind. 3 Ziffern oder Punkt)
    m = re.search(r'[_\- ](\d+\.\d+(?:\.\d+)*[a-z]?)', stem, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'[_\- ](\d{3,}[a-z]?)', stem, re.IGNORECASE)
    if m:
        return m.group(1)
    # Suche nach (1), (2) etc.
    m = re.search(r'\((\d+)\)', stem)
    if m:
        return f"({m.group(1)})"
    return ""


# ---- Tiefenanalyse .package (Stufe 1-5) ----

def read_dbpf_entries(path: Path) -> list[dict] | None:
    """Liest den vollständigen DBPF v2 Index mit Offsets, Größen und Kompression.

    Returns: Liste von Dicts {type, group, instance, offset, comp_size, uncomp_size, compression}
    """
    try:
        with open(path, 'rb') as f:
            header = f.read(96)
            if len(header) < 96 or header[:4] != b'DBPF':
                return None
            major = _struct.unpack_from('<I', header, 4)[0]
            if major != 2:
                return None
            entry_count = _struct.unpack_from('<I', header, 36)[0]
            index_size = _struct.unpack_from('<I', header, 44)[0]
            index_offset = _struct.unpack_from('<Q', header, 64)[0]
            if entry_count == 0 or index_offset == 0 or index_size < 4:
                return []
            f.seek(index_offset)
            index_data = f.read(index_size)
            if len(index_data) < index_size:
                return None

        pos = 0
        flags = _struct.unpack_from('<I', index_data, pos)[0]
        pos += 4
        const_vals = [None, None, None, None]
        for i in range(4):
            if flags & (1 << i):
                if pos + 4 > len(index_data):
                    return None
                const_vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                pos += 4
        header_bytes = pos
        remaining = index_size - header_bytes
        if entry_count > 0 and remaining > 0:
            entry_size = remaining // entry_count
        else:
            return []
        key_field_count = sum(1 for v in const_vals if v is None)
        key_bytes = key_field_count * 4
        meta_bytes = entry_size - key_bytes

        entries = []
        for _ in range(entry_count):
            vals = list(const_vals)
            for i in range(4):
                if vals[i] is None:
                    if pos + 4 > len(index_data):
                        break
                    vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                    pos += 4
            if None in vals:
                break
            rtype, group, ihi, ilo = vals
            instance = (ihi << 32) | ilo
            offset = comp_size = uncomp_size = 0
            compression = 0
            if meta_bytes >= 16 and pos + meta_bytes <= len(index_data):
                offset = _struct.unpack_from('<I', index_data, pos)[0]
                file_size_raw = _struct.unpack_from('<I', index_data, pos + 4)[0]
                uncomp_size = _struct.unpack_from('<I', index_data, pos + 8)[0]
                compression = _struct.unpack_from('<H', index_data, pos + 12)[0]
                comp_size = file_size_raw & 0x7FFFFFFF
            pos += meta_bytes
            entries.append({
                'type': rtype, 'group': group, 'instance': instance,
                'offset': offset, 'comp_size': comp_size,
                'uncomp_size': uncomp_size, 'compression': compression,
            })
        return entries
    except Exception:
        return None


def _read_resource_data(path: Path, entry: dict) -> bytes | None:
    """Liest und dekomprimiert eine einzelne Ressource aus einer .package-Datei."""
    try:
        size_to_read = entry.get('comp_size') or entry.get('uncomp_size') or 0
        if size_to_read <= 0 or entry.get('offset', 0) <= 0:
            return None
        with open(path, 'rb') as f:
            f.seek(entry['offset'])
            raw = f.read(size_to_read)
        if not raw:
            return None
        comp = entry.get('compression', 0)
        if comp == 0x5A42:  # ZLIB
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return raw
        elif comp == 0xFFFF:  # Intern — oft ZLIB
            try:
                return zlib.decompress(raw)
            except Exception:
                return None
        return raw  # 0x0000 = unkomprimiert
    except Exception:
        return None


# ---- DDS → PNG Konvertierung (für Objekt-Thumbnails) ----
def _dds_to_png(dds_data: bytes, max_dim: int = 128) -> bytes | None:
    """Dekodiert DDS-Textur (DXT1/DXT5/unkomprimiert) und liefert PNG-Bytes.

    Unterstützt die häufigsten Sims 4 DDS-Formate.
    Gibt None zurück wenn Format nicht unterstützt oder Fehler.
    """
    try:
        if len(dds_data) < 128 or dds_data[:4] != b'DDS ':
            return None
        # DDS Header parsen (ab Offset 4)
        height = _struct.unpack_from('<I', dds_data, 12)[0]
        width = _struct.unpack_from('<I', dds_data, 16)[0]
        pf_flags = _struct.unpack_from('<I', dds_data, 80)[0]
        pf_fourcc = dds_data[84:88]
        pf_rgbbitcount = _struct.unpack_from('<I', dds_data, 88)[0]
        pf_rmask = _struct.unpack_from('<I', dds_data, 92)[0]
        pf_gmask = _struct.unpack_from('<I', dds_data, 96)[0]
        pf_bmask = _struct.unpack_from('<I', dds_data, 100)[0]
        pf_amask = _struct.unpack_from('<I', dds_data, 104)[0]

        if width < 8 or height < 8 or width > 2048 or height > 2048:
            return None  # Zu klein (<8px) oder zu groß (>2048px)

        pixel_data = dds_data[128:]
        rgba = None

        if pf_flags & 0x4:  # DDPF_FOURCC
            if pf_fourcc in (b'DXT1', b'DST1'):
                rgba = _decode_dxt1(pixel_data, width, height)
            elif pf_fourcc in (b'DXT5', b'DST5'):
                rgba = _decode_dxt5(pixel_data, width, height)
        elif pf_flags & 0x40:  # DDPF_RGB
            if pf_rgbbitcount == 32:
                rgba = _decode_rgba(pixel_data, width, height, pf_rmask, pf_gmask, pf_bmask, pf_amask)
            elif pf_rgbbitcount == 24:
                rgba = _decode_rgb24(pixel_data, width, height)

        if not rgba:
            return None

        # Downscale wenn zu groß
        if width > max_dim or height > max_dim:
            rgba, width, height = _downscale_rgba(rgba, width, height, max_dim)

        # RGBA → PNG
        return _rgba_to_png(rgba, width, height)
    except Exception:
        return None


def _decode_dxt1(data: bytes, w: int, h: int) -> bytearray | None:
    """DXT1 (BC1) Dekodierung → RGBA."""
    bw, bh = (w + 3) // 4, (h + 3) // 4
    needed = bw * bh * 8
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    pos = 0
    for by in range(bh):
        for bx in range(bw):
            c0 = _struct.unpack_from('<H', data, pos)[0]
            c1 = _struct.unpack_from('<H', data, pos + 2)[0]
            bits = _struct.unpack_from('<I', data, pos + 4)[0]
            pos += 8
            r0, g0, b0 = (c0 >> 11) << 3, ((c0 >> 5) & 63) << 2, (c0 & 31) << 3
            r1, g1, b1 = (c1 >> 11) << 3, ((c1 >> 5) & 63) << 2, (c1 & 31) << 3
            colors = [(r0, g0, b0, 255), (r1, g1, b1, 255)]
            if c0 > c1:
                colors.append(((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3, 255))
                colors.append(((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3, 255))
            else:
                colors.append(((r0+r1)//2, (g0+g1)//2, (b0+b1)//2, 255))
                colors.append((0, 0, 0, 0))
            for py in range(4):
                for px in range(4):
                    x, y = bx*4+px, by*4+py
                    if x < w and y < h:
                        idx = (bits >> (2*(py*4+px))) & 3
                        c = colors[idx]
                        p = (y*w+x)*4
                        out[p:p+4] = bytes(c)
    return out


def _decode_dxt5(data: bytes, w: int, h: int) -> bytearray | None:
    """DXT5 (BC3) Dekodierung → RGBA."""
    bw, bh = (w + 3) // 4, (h + 3) // 4
    needed = bw * bh * 16
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    pos = 0
    for by in range(bh):
        for bx in range(bw):
            # Alpha block (8 bytes)
            a0 = data[pos]; a1 = data[pos+1]
            abits = int.from_bytes(data[pos+2:pos+8], 'little')
            pos += 8
            alphas = [a0, a1]
            if a0 > a1:
                for i in range(6):
                    alphas.append(((6-i)*a0 + (1+i)*a1) // 7)
            else:
                for i in range(4):
                    alphas.append(((4-i)*a0 + (1+i)*a1) // 5)
                alphas.extend([0, 255])
            # Color block (8 bytes)
            c0 = _struct.unpack_from('<H', data, pos)[0]
            c1 = _struct.unpack_from('<H', data, pos+2)[0]
            bits = _struct.unpack_from('<I', data, pos+4)[0]
            pos += 8
            r0, g0, b0 = (c0 >> 11) << 3, ((c0 >> 5) & 63) << 2, (c0 & 31) << 3
            r1, g1, b1 = (c1 >> 11) << 3, ((c1 >> 5) & 63) << 2, (c1 & 31) << 3
            colors = [(r0, g0, b0), (r1, g1, b1),
                      ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3),
                      ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3)]
            for py in range(4):
                for px in range(4):
                    x, y = bx*4+px, by*4+py
                    if x < w and y < h:
                        ci = (bits >> (2*(py*4+px))) & 3
                        ai = (abits >> (3*(py*4+px))) & 7
                        r, g, b = colors[ci]
                        a = alphas[ai]
                        p = (y*w+x)*4
                        out[p:p+4] = bytes((r, g, b, a))
    return out


def _decode_rgba(data: bytes, w: int, h: int, rm: int, gm: int, bm: int, am: int) -> bytearray | None:
    """Unkomprimiert 32-Bit RGBA/BGRA → RGBA."""
    needed = w * h * 4
    if len(data) < needed:
        return None
    # Bitshift aus Maske berechnen
    def _shift(mask):
        if mask == 0: return 0, 0
        s = 0
        while mask and not (mask & 1): mask >>= 1; s += 1
        return s, mask
    rs, _ = _shift(rm); gs, _ = _shift(gm); bs, _ = _shift(bm); as_, _ = _shift(am)
    out = bytearray(needed)
    for i in range(w * h):
        px = _struct.unpack_from('<I', data, i*4)[0]
        out[i*4]   = (px >> rs) & 0xFF
        out[i*4+1] = (px >> gs) & 0xFF
        out[i*4+2] = (px >> bs) & 0xFF
        out[i*4+3] = ((px >> as_) & 0xFF) if am else 255
    return out


def _decode_rgb24(data: bytes, w: int, h: int) -> bytearray | None:
    """Unkomprimiert 24-Bit BGR → RGBA."""
    needed = w * h * 3
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    for i in range(w * h):
        b, g, r = data[i*3], data[i*3+1], data[i*3+2]
        out[i*4:i*4+4] = bytes((r, g, b, 255))
    return out


def _downscale_rgba(rgba: bytearray, w: int, h: int, max_dim: int):
    """Einfaches Downscaling via Pixel-Skipping (nearest neighbor)."""
    scale = max(w, h) / max_dim
    nw, nh = max(1, int(w / scale)), max(1, int(h / scale))
    out = bytearray(nw * nh * 4)
    for ny in range(nh):
        for nx in range(nw):
            sx = min(int(nx * scale), w - 1)
            sy = min(int(ny * scale), h - 1)
            sp = (sy * w + sx) * 4
            dp = (ny * nw + nx) * 4
            out[dp:dp+4] = rgba[sp:sp+4]
    return out, nw, nh


def _rgba_to_png(rgba: bytearray, w: int, h: int) -> bytes:
    """RGBA-Pixel → PNG-Datei (unkomprimiert, Filtertyp 0)."""
    import io
    def _crc32(data):
        return zlib.crc32(data) & 0xFFFFFFFF

    raw_rows = bytearray()
    stride = w * 4
    for y in range(h):
        raw_rows.append(0)  # Filter: None
        raw_rows.extend(rgba[y*stride:(y+1)*stride])

    compressed = zlib.compress(bytes(raw_rows), 6)

    buf = io.BytesIO()
    # PNG Signature
    buf.write(b'\x89PNG\r\n\x1a\n')
    # IHDR
    ihdr_data = _struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)  # 8bit RGBA
    ihdr_chunk = b'IHDR' + ihdr_data
    buf.write(_struct.pack('>I', len(ihdr_data)))
    buf.write(ihdr_chunk)
    buf.write(_struct.pack('>I', _crc32(ihdr_chunk)))
    # IDAT
    idat_chunk = b'IDAT' + compressed
    buf.write(_struct.pack('>I', len(compressed)))
    buf.write(idat_chunk)
    buf.write(_struct.pack('>I', _crc32(idat_chunk)))
    # IEND
    iend_chunk = b'IEND'
    buf.write(_struct.pack('>I', 0))
    buf.write(iend_chunk)
    buf.write(_struct.pack('>I', _crc32(iend_chunk)))

    return buf.getvalue()


# TS4 CAS Body Types
_CAS_BODY_TYPES = {
    1: "Oberteil", 2: "Ganzkörper", 3: "Unterteil", 4: "Schuhe",
    5: "Hut", 6: "Brille", 7: "Halskette", 8: "Armband",
    9: "Ohrringe", 10: "Ring", 11: "Handschuhe", 12: "Socken",
    13: "Strumpfhose", 14: "Haarfarbe", 15: "Make-Up", 16: "Lidschatten",
    17: "Lippenstift", 18: "Wimpern", 19: "Gesichtsbehaarung",
    20: "Oberteil-Accessoire", 21: "Brustbehaarung", 22: "Tattoo",
    24: "Haare", 25: "Gesichts-Overlay", 26: "Kopf", 27: "Körper",
    28: "Ohrläppchen", 29: "Zähne", 30: "Fingernägel", 31: "Fußnägel",
}

_TUNING_TYPES = {
    0x545AC67A, 0x03B33DDF, 0xE882D22F, 0x339BC0E4, 0x0C772E27,
    0xCB5FDDC7, 0xC0DB5AE7, 0x736884F1, 0xE5105066, 0x7FB6AD72,
    0x0904DF10, 0x8B18FF6E, 0x6A4ABC1C,
}


def analyze_package_deep(path: Path):
    """Tiefenanalyse einer .package-Datei.

    Returns: (info_dict, all_keys_set) oder None bei Fehler.
    info_dict: total_resources, type_breakdown, category,
               cas_body_types, tuning_names, thumbnail_b64
    """
    if path.suffix.lower() != '.package':
        return None
    entries = read_dbpf_entries(path)
    if entries is None:
        return None

    # Typ-Aufschlüsselung
    type_counts = defaultdict(int)
    for e in entries:
        type_counts[_res_type_name(e['type'])] += 1

    # Kategorie ableiten
    cas_count = sum(1 for e in entries if e['type'] == 0x034AEECB)
    mesh_count = sum(1 for e in entries if e['type'] in (0x015A1849, 0x01D10F34))
    texture_count = sum(1 for e in entries if e['type'] in (0xD382BF57, 0x2F7D0004))
    tuning_count = sum(1 for e in entries if e['type'] in _TUNING_TYPES)

    if cas_count > 0:
        category = "CAS"  # wird nach Body-Type-Erkennung verfeinert
    elif mesh_count > 0 and tuning_count > 0:
        category = "Objekt/Möbel"
    elif tuning_count > 5:
        category = "Gameplay-Mod (Tuning)"
    elif mesh_count > 0:
        category = "Mesh/Build-Mod"
    elif texture_count > 0:
        category = "Textur/Override"
    else:
        category = "Sonstiges"

    all_keys = set((e['type'], e['group'], e['instance']) for e in entries)

    result = {
        'total_resources': len(entries),
        'type_breakdown': dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        'category': category,
        'cas_body_types': [],
        'tuning_names': [],
        'thumbnail_b64': None,
    }

    # ---- Stufe 3: Thumbnail suchen (PNG/JPEG/DDS) ----
    # Bekannte Thumbnail-Typen: CAS-Thumbnails + Objekt-Thumbnails
    _THUMB_TYPES = (0x3C1AF1F2, 0xC8A5E01A, 0x3C2A8647, 0x5B282D45, 0xCD9DE247, 0x0580A2B4, 0x0580A2B6)
    thumb_entries = [e for e in entries if e['type'] in _THUMB_TYPES]
    for te in thumb_entries[:5]:
        data = _read_resource_data(path, te)
        if data and len(data) > 8:
            if data[:4] == b'\x89PNG':
                result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(data).decode()
                break
            elif data[:2] == b'\xff\xd8':
                result['thumbnail_b64'] = 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
                break

    # Fallback 1: PNG/JPEG in beliebigen Ressourcen suchen (< 200KB)
    if not result['thumbnail_b64']:
        for e in entries:
            usz = e.get('uncomp_size', 0) or e.get('comp_size', 0)
            if usz > 200_000 or e['type'] in _THUMB_TYPES:
                continue
            data = _read_resource_data(path, e)
            if data and len(data) > 8:
                if data[:4] == b'\x89PNG':
                    result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(data).decode()
                    break
                elif data[:2] == b'\xff\xd8':
                    result['thumbnail_b64'] = 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
                    break

    # Fallback 2: DDS-Textur dekodieren (0x00B2D882 = häufig bei Objekten/Möbeln)
    if not result['thumbnail_b64']:
        dds_entries = [e for e in entries if e['type'] == 0x00B2D882]
        # Bevorzuge mittelgroße DDS (64-256px = gute Thumbnails), überspringe winzige 4x4
        dds_entries.sort(key=lambda e: abs((e.get('uncomp_size', 0) or e.get('comp_size', 0)) - 16000))
        for de in dds_entries[:3]:
            data = _read_resource_data(path, de)
            if data and len(data) > 128 and data[:4] == b'DDS ':
                png_data = _dds_to_png(data, max_dim=128)
                if png_data:
                    result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(png_data).decode()
                    break

    # ---- Stufe 4: CAS Parts Body Type (Best-Effort) ----
    cas_entries = [e for e in entries if e['type'] == 0x034AEECB]
    body_types = set()
    cas_part_names = []
    for ce in cas_entries[:20]:
        data = _read_resource_data(path, ce)
        if not data or len(data) < 20:
            continue
        try:
            version = _struct.unpack_from('<I', data, 0)[0]
            if not (18 <= version <= 55):
                continue
            num_presets = _struct.unpack_from('<I', data, 8)[0]
            pos = 12
            # Presets überspringen
            for _ in range(min(num_presets, 100)):
                if pos + 12 > len(data):
                    break
                pos += 8  # presetId (uint64)
                xml_size = _struct.unpack_from('<I', data, pos)[0]
                pos += 4 + xml_size
            if pos >= len(data) - 2:
                continue
            # partName (1 Byte Länge + Zeichen, oft UTF-16LE kodiert)
            name_len = data[pos]
            name_bytes = data[pos + 1:pos + 1 + name_len]
            pos += 1 + name_len
            # Name dekodieren (UTF-16LE oder ASCII)
            part_name = ''
            if name_len >= 2 and name_bytes[1:2] == b'\x00':
                try:
                    part_name = name_bytes.decode('utf-16-le', errors='ignore')
                except Exception:
                    part_name = name_bytes.decode('ascii', errors='ignore')
            else:
                part_name = name_bytes.decode('ascii', errors='ignore')
            if part_name and len(cas_part_names) < 5:
                cas_part_names.append(part_name)
        except Exception:
            pass

    # Body-Type-Erkennung über CAS-Part-interne Namen und Dateiname
    # EA CAS Part Namenskonvention: {creator}_{ageGender}{BodyPart}_{mesh}_{variant}
    # ageGender-Prefix: y=YoungAdult, c=Child, t=Teen, p=Toddler, e=Elder
    # gender: f=Female, m=Male, u=Unisex
    # BodyPart: Hair_, Top_, Body_, Bottom_, Shoe, Hat_, Acc_, Makeup, etc.
    _AGE = r'[ycpte][fmu]'
    _NAME_TO_BODY = [
        # HAARE (24) — CAS-intern: yfHair_, ymHair_ etc. / Dateiname: hair, hairstyle
        (re.compile(rf'(?:{_AGE})?Hair_|hair(?:style)?|wig', re.I), 24),
        # HAARFARBE (14) — CAS-intern: HairColor
        (re.compile(r'(?:haircolor|hair_color|recolor.*hair)', re.I), 14),
        # OBERTEIL (1) — CAS-intern: yfTop_ / Dateiname: top, shirt, sweater etc.
        (re.compile(rf'(?:{_AGE})?Top_|(?:shirt|hoodie|jacket|blouse|sweater|tshirt|vest|coat|tank|cardigan|tee(?:_)|polo|crop(?:top|_)|blazer|pullover|parka)', re.I), 1),
        # GANZKÖRPER (2) — CAS-intern: yfBody_ / Dateiname: dress, gown, jumpsuit etc.
        (re.compile(rf'(?:{_AGE})?Body_|(?:fullbody|full_body|dress|gown|jumpsuit|romper|onesie|bodysuit|chemise|lingerie|swimsuit|bikini|bathrobe|pajama|pyjama|nightgown|costume)', re.I), 2),
        # UNTERTEIL (3) — CAS-intern: yfBottom_ / Dateiname: pants, skirt, jeans etc.
        (re.compile(rf'(?:{_AGE})?Bottom_|(?:pant|jean|skirt|shorts|trouser|legging|underwear(?!_set))', re.I), 3),
        # SCHUHE (4) — CAS-intern: yfShoe / Dateiname: shoes, boots, sandals etc.
        (re.compile(rf'(?:{_AGE})?Shoe|(?:boot|sandal|sneaker|heel|slipper|loafer|flats?(?:_)|stiletto|platform|clog|mule|moccasin)', re.I), 4),
        # HUT (5) — CAS-intern: yfHat_, Acc_Hat / Dateiname: hat, beanie, cap etc.
        (re.compile(rf'(?:{_AGE})?Hat_|Acc_Hat|(?:beanie|(?:^|_)cap(?:_|$)|crown|headband|headwear|turban|beret|tiara|helmet|hood(?:_|$))', re.I), 5),
        # BRILLE (6) — CAS-intern: Acc_Glass / Dateiname: glasses, sunglasses etc.
        (re.compile(r'Acc_Glass|(?:glasses|sunglasses|spectacles|eyewear|monocle)', re.I), 6),
        # HALSKETTE (7) — CAS-intern: Acc_Neck / Dateiname: necklace, choker etc.
        (re.compile(r'Acc_Neck|(?:necklace|choker|pendant|collar(?:_|$)|chain(?:_neck))', re.I), 7),
        # ARMBAND (8) — CAS-intern: Acc_Wrist, Acc_Bracelet / Dateiname: bracelet etc.
        (re.compile(r'Acc_Wrist|Acc_Bracelet|(?:bracelet|bangle|wristband|cuff(?:_|$))', re.I), 8),
        # OHRRINGE (9) — CAS-intern: Acc_Ear / Dateiname: earring etc.
        (re.compile(r'Acc_Ear|(?:earring|ear_ring|ear(?:Drop|Round|Pentagon|Stud|Hoop|Dangle|Clip|Cuff|Wrap|Plug))', re.I), 9),
        # RING (10) — CAS-intern: Acc_Ring / Dateiname: ring
        (re.compile(r'Acc_Ring|(?:(?:^|_)ring(?:_|$))', re.I), 10),
        # HANDSCHUHE (11) — CAS-intern: Acc_Glove / Dateiname: gloves etc.
        (re.compile(r'Acc_Glove|(?:glove|mitten)', re.I), 11),
        # SOCKEN (12) — CAS-intern: yfSock / Dateiname: socks etc.
        (re.compile(rf'(?:{_AGE})?Sock|sock', re.I), 12),
        # STRUMPFHOSE (13) — Dateiname: tights, stockings etc.
        (re.compile(r'(?:tight|stocking|pantyhose|legwear)', re.I), 13),
        # MAKE-UP (15) — CAS-intern: yuMakeup, Facepaint / Dateiname: makeup, blush etc.
        (re.compile(r'Makeup|MakeUp|Make_Up|Facepaint|(?:blush|bronzer|contour|face_paint|highlight(?:er)?)', re.I), 15),
        # LIDSCHATTEN (16) — Dateiname: eyeshadow etc.
        (re.compile(r'(?:eyeshadow|eye_shadow)', re.I), 16),
        # LIPPENSTIFT (17) — Dateiname: lipstick, lipcolor etc.
        (re.compile(r'(?:lipstick|lip_stick|lip(?:_)?color|lipgloss|lip_gloss)', re.I), 17),
        # WIMPERN (18) — Dateiname: eyelash, eyeliner etc.
        (re.compile(r'(?:eyelash|eyeliner|lashes)', re.I), 18),
        # GESICHTSBEHAARUNG (19) — Dateiname: beard, mustache etc.
        (re.compile(r'(?:beard|facial_hair|facialhair|mustache|goatee|stubble|sideburn)', re.I), 19),
        # OBERTEIL-ACCESSOIRE (20) — CAS-intern: Acc_Top
        (re.compile(r'Acc_Top|(?:scarf|shawl|cape|poncho)', re.I), 20),
        # TATTOO (22) — Dateiname: tattoo
        (re.compile(r'tattoo', re.I), 22),
        # SKIN/OVERLAY (25) — Dateiname: skin, skindetail, freckle etc.
        (re.compile(r'(?:skin(?:tone|detail|overlay|blend)?|freckle|mole|birthmark|wrinkle|scar|blemish|dimple)', re.I), 25),
        # FINGERNÄGEL (30) — Dateiname: nails, manicure etc.
        (re.compile(r'(?:nail(?:s|polish)?|fingernail|manicure)', re.I), 30),
        # FUSSNÄGEL (31) — Dateiname: toenails, pedicure etc.
        (re.compile(r'(?:toenail|pedicure)', re.I), 31),
        # AUGENBRAUEN (extra — als Make-Up 15 einsortiert)
        (re.compile(r'(?:eyebrow|brow(?:s|_))', re.I), 15),
    ]
    file_stem = path.stem
    all_name_sources = cas_part_names + [file_stem]
    for src_name in all_name_sources:
        if not src_name:
            continue
        for pat, bt_id in _NAME_TO_BODY:
            if pat.search(src_name):
                body_types.add(bt_id)
                break  # nur erste Übereinstimmung pro Name

    result['cas_body_types'] = [_CAS_BODY_TYPES.get(bt, f"Typ {bt}") for bt in sorted(body_types)]

    # ---- Stufe 5: Tuning XML Names ----
    tuning_entries = [e for e in entries if e['type'] in _TUNING_TYPES]
    names = []
    for te in tuning_entries[:20]:
        data = _read_resource_data(path, te)
        if not data or len(data) < 10:
            continue
        try:
            text = data.decode('utf-8', errors='ignore')
            m = re.search(r'\bn="([^"]+)"', text[:500])
            if m:
                names.append(m.group(1))
        except Exception:
            pass
    result['tuning_names'] = names[:10]

    # ---- Kategorie verfeinern basierend auf Body Types ----
    if result['category'] == 'CAS' and body_types:
        _HAIR_TYPES = {14, 24}  # Haarfarbe, Haare
        _CLOTHING_TYPES = {1, 2, 3, 4, 5, 11, 12, 13}  # Oberteil..Strumpfhose
        _MAKEUP_TYPES = {15, 16, 17, 18, 19, 25, 26, 27}  # Make-Up..Körper
        _ACCESSOIRE_TYPES = {6, 7, 8, 9, 10, 20, 22, 28, 29, 30, 31}  # Brille..Fußnägel
        if body_types & _HAIR_TYPES:
            result['category'] = 'CAS (Haare 💇)'
        elif body_types & _CLOTHING_TYPES:
            result['category'] = 'CAS (Kleidung 👚)'
        elif body_types & _MAKEUP_TYPES:
            result['category'] = 'CAS (Make-Up 💄)'
        elif body_types & _ACCESSOIRE_TYPES:
            result['category'] = 'CAS (Accessoire 💍)'
        else:
            result['category'] = 'CAS (Kleidung/Haare/Make-Up)'
    elif result['category'] == 'CAS':
        result['category'] = 'CAS (Kleidung/Haare/Make-Up)'

    return result, all_keys


# ---- Addon-Erkennung ----
_ADDON_KEYWORDS = re.compile(
    r'(?:^|[_\-\s!.])'
    r'(?:addon|add-on|add_on|extension|patch|fix|hotfix|override|compat|compatibility|compat_patch)'
    r'(?:[_\-\s!.]|$)',
    re.IGNORECASE,
)

def _is_addon_pair(path_a: str, path_b: str) -> bool:
    """Prüft ob zwei Packages eine Addon-Beziehung haben.
    
    True wenn:
    - Einer der Dateinamen ein Addon-Keyword enthält UND
    - der Basis-Name (ohne Addon-Keyword) im anderen Dateinamen vorkommt
    ODER beide den gleichen Autor-Prefix teilen UND im gleichen Ordner liegen.
    """
    name_a = Path(path_a).stem.lower()
    name_b = Path(path_b).stem.lower()
    dir_a = str(Path(path_a).parent).lower()
    dir_b = str(Path(path_b).parent).lower()
    
    # Check: Hat einer ein Addon-Keyword?
    a_has_kw = bool(_ADDON_KEYWORDS.search(name_a))
    b_has_kw = bool(_ADDON_KEYWORDS.search(name_b))
    
    if a_has_kw or b_has_kw:
        # Addon-Name sollte den Base-Namen enthalten
        if a_has_kw:
            base_clean = _ADDON_KEYWORDS.sub('', name_a).strip('_- !.')
            if base_clean and base_clean in name_b:
                return True
        if b_has_kw:
            base_clean = _ADDON_KEYWORDS.sub('', name_b).strip('_- !.')
            if base_clean and base_clean in name_a:
                return True
    
    # Check: Gleicher Ordner + einer enthält den anderen als Prefix
    if dir_a == dir_b:
        # Normalisiere für Prefix-Vergleich
        norm_a = normalize_mod_name(Path(path_a).name)
        norm_b = normalize_mod_name(Path(path_b).name)
        if norm_a and norm_b and norm_a != norm_b:
            if norm_a.startswith(norm_b) or norm_b.startswith(norm_a):
                # Zusätzlich: der längere Name enthält ein Addon-artiges Suffix
                longer = name_a if len(name_a) > len(name_b) else name_b
                shorter = name_b if len(name_a) > len(name_b) else name_a
                extra = longer.replace(shorter, '', 1).strip('_- !.')
                if extra:  # Es gibt einen Zusatz → wahrscheinlich Addon
                    return True
    
    return False


def scan_duplicates(
    roots: list[Path],
    exts: set[str],
    ignore_dirs: set[str],
    do_name: bool,
    do_content: bool,
    do_conflicts: bool = False,
    progress_cb=None,
):
    """
    progress_cb(phase, cur, total, msg)
    phases: collect, name, hashing_init, hashing, finalize
    """
    def emit(phase, cur, total, msg):
        if progress_cb:
            progress_cb(phase, cur, total, msg)

    files: list[Path] = []

    emit("collect", 0, None, "Sammle Dateien…")
    count = 0
    last_emit = time.time()
    visited_inodes = set()  # Track visited files by inode (resolves symlinks/junctions)

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out ignored directories and symlinks/junctions
            filtered_dirs = []
            for d in dirnames:
                if d.lower() in ignore_dirs:
                    continue
                dir_path = Path(dirpath) / d
                try:
                    # Symlinks überspringen
                    if dir_path.is_symlink():
                        continue
                    # Windows Junctions erkennen (ReparsePoint-Attribut)
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(dir_path))
                    if attrs != -1 and (attrs & 0x400):  # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
                        continue
                except Exception:
                    pass
                filtered_dirs.append(d)
            dirnames[:] = filtered_dirs

            for fn in filenames:
                p = Path(dirpath) / fn
                try:
                    if not p.is_file():
                        continue
                    if p.is_symlink():
                        continue
                    
                    # Get the real file path (resolves symlinks/junctions)
                    try:
                        real_p = p.resolve()
                        stat_info = real_p.stat()
                        # Use inode (Windows: file_index) to track unique files
                        inode = (stat_info.st_ino, stat_info.st_dev)
                        if inode in visited_inodes:
                            continue
                        visited_inodes.add(inode)
                    except Exception:
                        pass
                    
                    if exts and p.suffix.lower() not in exts:
                        continue
                    files.append(p)
                    count += 1
                    now = time.time()
                    if now - last_emit > 0.15:
                        emit("collect", count, None, f"Sammle Dateien… ({count})")
                        last_emit = now
                except Exception:
                    pass

    emit("collect", count, None, f"Dateien gesammelt: {count}")

    name_dupes = {}
    if do_name:
        emit("name", None, None, "Prüfe Duplikate nach Dateiname…")
        by_name = defaultdict(list)
        for p in files:
            by_name[p.name.lower()].append(p)
        name_dupes = {k: v for k, v in by_name.items() if len(v) > 1}
        emit("name", None, None, f"Name-Gruppen: {len(name_dupes)}")

    content_dupes = {}
    if do_content:
        emit("hashing_init", 0, 0, "Bereite Hash-Prüfung vor…")
        by_size = defaultdict(list)
        for p in files:
            try:
                by_size[p.stat().st_size].append(p)
            except Exception:
                pass

        candidates = []
        for _, group in by_size.items():
            if len(group) > 1:
                candidates.extend(group)

        total = len(candidates)
        emit("hashing_init", 0, total, f"Hashing-Kandidaten: {total}")

        if total > 0:
            by_hash = defaultdict(list)
            done = 0
            last_emit = time.time()
            for p in candidates:
                try:
                    digest = file_sha256(p)
                    by_hash[digest].append(p)
                except Exception:
                    pass
                done += 1
                now = time.time()
                if now - last_emit > 0.08 or done == total:
                    emit("hashing", done, total, f"Hashing… ({done}/{total})\n{p}")
                    last_emit = now

            content_dupes = {d: ps for d, ps in by_hash.items() if len(ps) > 1}

        emit("finalize", None, None, f"Inhalt-Gruppen: {len(content_dupes)}")

    # Ähnliche Dateinamen finden (normalisierter Name)
    similar_dupes = {}
    if do_name:
        emit("finalize", None, None, "Prüfe ähnliche Dateinamen…")
        by_normalized = defaultdict(list)
        for p in files:
            norm = normalize_mod_name(p.name)
            by_normalized[norm].append(p)
        # Nur Gruppen mit 2+ Dateien, die NICHT schon exakt gleich heißen
        for norm_key, paths in by_normalized.items():
            if len(paths) < 2:
                continue
            # Prüfe ob alle den gleichen echten Namen haben → dann ist es ein exakter Duplikat, kein ähnlicher
            real_names = set(p.name.lower() for p in paths)
            if len(real_names) == 1:
                continue  # Alle heißen gleich → schon in name_dupes
            # Prüfe ob sich die Dateien NUR in der Extension unterscheiden (.package vs .ts4script)
            # → Das sind zusammengehörige Mod-Dateien, keine Duplikate!
            real_stems = set(p.stem.lower() for p in paths)
            if len(real_stems) == 1:
                continue  # Gleicher Name, nur andere Endung → gehört zusammen
            similar_dupes[norm_key] = paths
        emit("finalize", None, None, f"Ähnliche Gruppen: {len(similar_dupes)}")

        # Name-Gruppen entfernen, deren Dateien komplett in einer Ähnlich-Gruppe enthalten sind
        # → Die Ähnlich-Gruppe zeigt es mit Cluster-Ansicht besser
        if similar_dupes and name_dupes:
            similar_paths_all = set()
            for paths in similar_dupes.values():
                for p in paths:
                    similar_paths_all.add(str(p).lower())
            redundant_keys = []
            for name_key, name_paths in name_dupes.items():
                if all(str(p).lower() in similar_paths_all for p in name_paths):
                    redundant_keys.append(name_key)
            for k in redundant_keys:
                del name_dupes[k]
            if redundant_keys:
                emit("finalize", None, None,
                     f"Name-Gruppen: {len(redundant_keys)} in Ähnlich-Gruppen aufgegangen → {len(name_dupes)} verbleibend")

    # Korrupte .package-Dateien erkennen (DBPF-Header-Check)
    corrupt_files = []
    emit("integrity", 0, None, "Prüfe .package-Integrität…")
    pkg_files = [p for p in files if p.suffix.lower() == '.package']
    checked = 0
    last_emit = time.time()
    for p in pkg_files:
        status = check_package_integrity(p)
        if status != 'ok':
            corrupt_files.append((p, status))
        checked += 1
        now = time.time()
        if now - last_emit > 0.1:
            emit("integrity", checked, len(pkg_files), f"Integritäts-Check… ({checked}/{len(pkg_files)})")
            last_emit = now
    emit("integrity", len(pkg_files), len(pkg_files), f"Korrupte Dateien: {len(corrupt_files)}")

    # Doppelte Mod-IDs / Ressource-Konflikte    
    conflicts = []
    addon_pairs = []
    if do_conflicts:
        emit("conflicts", 0, len(pkg_files), "Lese DBPF-Index für Konflikt-Analyse…")
        # Resource Key → [Path, ...]
        key_to_pkgs = defaultdict(list)
        done_c = 0
        last_emit = time.time()
        for p in pkg_files:
            rkeys = read_dbpf_resource_keys(p)
            if rkeys:
                seen_in_file = set()  # Dups innerhalb einer Datei ignorieren
                for rk in rkeys:
                    if rk not in seen_in_file:
                        seen_in_file.add(rk)
                        key_to_pkgs[rk].append(p)
            done_c += 1
            now = time.time()
            if now - last_emit > 0.1:
                emit("conflicts", done_c, len(pkg_files), f"DBPF-Index lesen… ({done_c}/{len(pkg_files)})")
                last_emit = now

        emit("conflicts", len(pkg_files), len(pkg_files), "Suche Konflikte…")

        # Finde Keys die in 2+ verschiedenen Packages vorkommen
        shared_keys = {k: paths for k, paths in key_to_pkgs.items() if len(paths) > 1}

        # Gruppiere nach Package-Paar/-Gruppe
        # pair_key = frozenset der Pfade → Liste der geteilten keys
        pair_map = defaultdict(list)  # frozenset(str(path),...) → [(type, group, instance), ...]
        for rk, paths in shared_keys.items():
            pk = frozenset(str(p) for p in paths)
            pair_map[pk].append(rk)

        # In Conflict-Objekte umwandeln + Addon-Erkennung
        for path_set, rkeys in pair_map.items():
            # Anzahl überlappender Keys und häufigste Typen
            type_counter = defaultdict(int)
            for rt, rg, ri in rkeys:
                type_counter[_res_type_name(rt)] += 1
            top_types = sorted(type_counter.items(), key=lambda x: -x[1])[:5]
            paths_sorted = sorted(path_set)
            entry = {
                'paths': paths_sorted,
                'shared_count': len(rkeys),
                'top_types': top_types,
            }
            # Addon-Check (nur bei 2er-Paaren)
            if len(paths_sorted) == 2 and _is_addon_pair(paths_sorted[0], paths_sorted[1]):
                addon_pairs.append(entry)
            else:
                conflicts.append(entry)
        conflicts.sort(key=lambda c: -c['shared_count'])
        addon_pairs.sort(key=lambda c: -c['shared_count'])
        emit("conflicts", len(pkg_files), len(pkg_files),
             f"Konflikte: {len(conflicts)} Gruppen, {len(addon_pairs)} Addon-Paare")

    return files, name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs


_CORRUPT_LABELS = {
    'empty': ('Leer', 'Datei ist 0 Bytes groß'),
    'too_small': ('Zu klein', 'Datei hat weniger als 96 Bytes (kein gültiger DBPF-Header)'),
    'no_dbpf': ('Kein DBPF', 'Datei hat keinen gültigen DBPF-Magic-Header — möglicherweise beschädigt oder falsches Format'),
    'wrong_version': ('Falsche Version', 'DBPF v1 (TS2/TS3) statt v2 (TS4) — falsches Spiel?'),
    'unreadable': ('Nicht lesbar', 'Datei konnte nicht gelesen werden (Berechtigung/Zugriff)'),
}


def _read_curseforge_data(mods_dir: str = "", cf_manifest_path: str = "") -> dict:
    """Liest CurseForge/Overwolf-Manifest und gibt ein Dict {normalisierter_pfad: info} zurück."""
    result = {}
    try:
        if cf_manifest_path and Path(cf_manifest_path).exists():
            manifest_path = Path(cf_manifest_path)
        else:
            manifest_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json"
        if not manifest_path.exists():
            return result
        raw = manifest_path.read_text(encoding="utf-8", errors="ignore")
        # BOM / Steuerzeichen entfernen
        raw = raw.lstrip('\ufeff\x00')
        # Manchmal beginnt die Datei mit einer hex-ID vor dem JSON
        idx = raw.find('[')
        if idx > 0:
            raw = raw[idx:]
        instances = json.loads(raw)
        # Sims 4 = gameTypeID 78062
        for inst in instances:
            if not isinstance(inst, dict):
                continue
            if inst.get("gameTypeID") != 78062:
                continue
            for addon in inst.get("installedAddons", []):
                try:
                    if not isinstance(addon, dict):
                        continue
                    mod_name = addon.get("name", "")
                    author = addon.get("primaryAuthor", "")
                    url = addon.get("webSiteURL", "") or ""
                    thumb = addon.get("thumbnailUrl", "") or ""
                    installed_file = addon.get("installedFile") or {}
                    latest_file = addon.get("latestFile") or {}
                    installed_id = installed_file.get("id", 0) if isinstance(installed_file, dict) else 0
                    latest_id = latest_file.get("id", 0) if isinstance(latest_file, dict) else 0
                    has_update = installed_id != latest_id and latest_id > 0
                    game_ver = ""
                    if isinstance(installed_file, dict):
                        gvs = installed_file.get("gameVersion") or []
                        if gvs and isinstance(gvs, list):
                            game_ver = str(gvs[0])
                    latest_game_ver = ""
                    if isinstance(latest_file, dict):
                        lgvs = latest_file.get("gameVersion") or []
                        if lgvs and isinstance(lgvs, list):
                            latest_game_ver = str(lgvs[0])
                    date_installed = addon.get("dateInstalled", "") or ""
                    date_updated = addon.get("dateUpdated", "") or ""
                    info = {
                        "name": mod_name,
                        "author": author,
                        "url": url,
                        "thumbnail": thumb,
                        "has_update": has_update,
                        "installed_version": game_ver,
                        "latest_version": latest_game_ver,
                        "latest_file_name": (latest_file.get("fileName", "") or "") if isinstance(latest_file, dict) else "",
                        "download_url": (latest_file.get("downloadUrl", "") or "") if isinstance(latest_file, dict) else "",
                        "date_installed": date_installed[:10] if date_installed else "",
                        "date_updated": date_updated[:10] if date_updated else "",
                    }
                    for fp in addon.get("filePaths", []):
                        if fp:
                            norm = os.path.normcase(os.path.normpath(fp))
                            result[norm] = info
                except Exception:
                    continue
    except Exception as ex:
        print(f"[CURSEFORGE] Fehler beim Lesen: {ex}", flush=True)
    return result


def _read_game_version(sims4_dir: str) -> dict | None:
    """Liest die Spielversion und das Patch-Datum aus GameVersion.txt."""
    if not sims4_dir:
        return None
    gv = Path(sims4_dir) / "GameVersion.txt"
    if not gv.exists():
        return None
    try:
        text = gv.read_text(encoding='utf-8', errors='ignore').strip()
        # Version-String bereinigen (BOM / Steuerzeichen entfernen)
        version = ''.join(c for c in text if c.isprintable() or c == '.')
        mtime = gv.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        return {
            'version': version,
            'patch_date': dt.strftime('%Y-%m-%d %H:%M'),
            'patch_ts': mtime,
        }
    except Exception:
        return None


class Dataset:
    def __init__(self, roots: list[Path], sims4_dir: str = ""):
        self.roots = roots
        self.sims4_dir = sims4_dir
        self.game_info = _read_game_version(sims4_dir)
        self.groups = []
        self.corrupt = []  # list of {file_obj, status, label, hint}
        self.conflicts = []  # list of conflict dicts
        self.addon_pairs = []  # list of addon-pair dicts (erwartete Konflikte)
        self.all_scanned_files: list[Path] = []  # ALLE gescannten Dateien
        self.non_mod_files: list[dict] = []  # Nicht-Mod-Dateien (txt, png, etc.)
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def collect_non_mod_files(self):
        """Sammelt alle Nicht-Mod-Dateien (txt, png, mp4, html, etc.) aus den Mod-Ordnern."""
        mod_exts = {".package", ".ts4script", ".zip", ".7z", ".rar"}
        ignore_dirs = {"__macosx", ".git", "__pycache__"}
        non_mod = []
        by_ext: dict[str, list] = {}  # ext -> list of file info
        for root in self.roots:
            if not root.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                filtered = []
                for d in dirnames:
                    if d.lower() in ignore_dirs:
                        continue
                    dp = Path(dirpath) / d
                    try:
                        if dp.is_symlink():
                            continue
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(dp))
                        if attrs != -1 and (attrs & 0x400):
                            continue
                    except Exception:
                        pass
                    filtered.append(d)
                dirnames[:] = filtered
                for fn in filenames:
                    p = Path(dirpath) / fn
                    try:
                        if not p.is_file() or p.is_symlink():
                            continue
                        ext = p.suffix.lower()
                        if ext in mod_exts:
                            continue
                        size, mtime = safe_stat(p)
                        idx = best_root_index(p, self.roots)
                        rel_str = ""
                        mod_folder = ""
                        try:
                            if idx is not None:
                                rel = p.resolve().relative_to(self.roots[idx].resolve())
                                rel_str = str(rel)
                                mod_folder = rel.parts[0] if len(rel.parts) > 1 else "(Mods-Root)"
                            else:
                                rel_str = p.name
                                mod_folder = p.parent.name
                        except Exception:
                            rel_str = p.name
                            mod_folder = p.parent.name
                        dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S") if mtime else "?"
                        obj = {
                            "path": str(p),
                            "name": p.name,
                            "rel": rel_str,
                            "ext": ext if ext else "(keine)",
                            "mod_folder": mod_folder,
                            "size": size,
                            "size_h": human_size(size),
                            "mtime": dt,
                        }
                        non_mod.append(obj)
                        by_ext.setdefault(ext if ext else "(keine)", []).append(obj)
                    except Exception:
                        pass
        # Sortiert nach Extension und dann Name
        non_mod.sort(key=lambda f: (f["ext"], f["name"].lower()))
        self.non_mod_files = non_mod
        self._non_mod_by_ext = sorted(by_ext.items(), key=lambda x: -len(x[1]))

    def _file_obj(self, p: Path) -> dict:
        size, mtime = safe_stat(p)
        idx = best_root_index(p, self.roots)
        label = f"Ordner {idx + 1}" if idx is not None else "Unbekannt"
        dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S") if mtime else "?"

        rel_str = ""
        mod_folder = ""
        try:
            if idx is not None:
                rel = p.resolve().relative_to(self.roots[idx].resolve())
                rel_str = str(rel)
                mod_folder = rel.parts[0] if len(rel.parts) > 1 else "(Mods-Root)"
            else:
                rel_str = p.name
                mod_folder = p.parent.name
        except Exception:
            rel_str = p.name
            mod_folder = p.parent.name

        return {
            "path": str(p),
            "rel": rel_str,
            "mod_folder": mod_folder,
            "root_label": label,
            "root_index": (idx + 1) if idx is not None else None,
            "size": size,
            "size_h": human_size(size),
            "mtime": dt,
            "exists": p.exists(),
        }

    def build_from_scan(self, name_dupes: dict[str, list[Path]], content_dupes: dict[str, list[Path]], similar_dupes: dict[str, list[Path]] = None, corrupt_files: list = None, conflicts: list = None, addon_pairs: list = None):
        groups = []

        for filename, paths in name_dupes.items():
            files = [self._file_obj(p) for p in sorted(paths, key=lambda x: str(x).lower())]
            groups.append({
                "type": "name",
                "key": filename,
                "key_short": filename,
                "size_each": None,
                "files": files,
            })

        for digest, paths in content_dupes.items():
            paths_sorted = sorted(paths, key=lambda x: str(x).lower())
            size0, _ = safe_stat(paths_sorted[0])
            files = [self._file_obj(p) for p in paths_sorted]
            groups.append({
                "type": "content",
                "key": digest,
                "key_short": digest[:12] + "…",
                "size_each": size0,
                "files": files,
            })

        # Ähnliche Dateinamen (z.B. verschiedene Versionen)
        if similar_dupes:
            for norm_key, paths in similar_dupes.items():
                paths_sorted = sorted(paths, key=lambda x: str(x).lower())
                files = []
                for p in paths_sorted:
                    fobj = self._file_obj(p)
                    fobj["version"] = extract_version(p.name)
                    # Hash für Cluster-Bildung
                    try:
                        fobj["hash"] = file_sha256(p)
                    except Exception:
                        fobj["hash"] = None
                    files.append(fobj)
                groups.append({
                    "type": "similar",
                    "key": norm_key,
                    "key_short": norm_key,
                    "size_each": None,
                    "files": files,
                })

        def score(g):
            count = len(g["files"])
            size_each = g["size_each"] or 0
            return (count, count * size_each)

        groups.sort(key=score, reverse=True)
        self.groups = groups

        # Korrupte Dateien verarbeiten
        self.corrupt = []
        if corrupt_files:
            for p, status in corrupt_files:
                fobj = self._file_obj(p)
                label, hint = _CORRUPT_LABELS.get(status, (status, ''))
                self.corrupt.append({
                    **fobj,
                    'status': status,
                    'status_label': label,
                    'status_hint': hint,
                })

        # Konflikte verarbeiten
        self.conflicts = []
        if conflicts:
            for c in conflicts:
                file_objs = []
                for ps in c['paths']:
                    p = Path(ps)
                    file_objs.append(self._file_obj(p))
                self.conflicts.append({
                    'files': file_objs,
                    'shared_count': c['shared_count'],
                    'top_types': c['top_types'],
                })

        # Addon-Paare verarbeiten
        self.addon_pairs = []
        if addon_pairs:
            for c in addon_pairs:
                file_objs = []
                for ps in c['paths']:
                    p = Path(ps)
                    file_objs.append(self._file_obj(p))
                self.addon_pairs.append({
                    'files': file_objs,
                    'shared_count': c['shared_count'],
                    'top_types': c['top_types'],
                })

    def enrich_groups(self, progress_cb=None, deep_cache=None):
        """Tiefenanalyse für ALLE Gruppen: Thumbnails, Kategorie, Body-Types, Key-Überlappung."""
        if not self.groups:
            return

        # Für Content-Gruppen reicht 1 Datei (identisch), Rest bekommt Kopie
        total_files = 0
        for g in self.groups:
            if g['type'] == 'content':
                total_files += 1  # nur 1 Datei analysieren
            else:
                total_files += len(g['files'])
        done = 0

        for g in self.groups:
            file_keys = {}  # path → set of resource keys

            if g['type'] == 'content':
                # Inhaltlich identisch → nur 1 Datei analysieren, Rest bekommt Kopie
                first_deep = None
                for f in g['files']:
                    p = Path(f['path'])
                    if p.suffix.lower() != '.package':
                        continue
                    deep = _analyze_with_cache(p, deep_cache)
                    if deep:
                        first_deep = deep[0]
                        if deep[1] is not None:
                            file_keys[f['path']] = deep[1]
                    break
                if first_deep:
                    for f in g['files']:
                        f['deep'] = first_deep
                done += 1
                if progress_cb and done % 3 == 0:
                    progress_cb("deep", done, total_files,
                                f"Tiefenanalyse… ({done}/{total_files})")
            else:
                # Name/Similar: jede Datei einzeln analysieren
                for f in g['files']:
                    p = Path(f['path'])
                    if p.suffix.lower() != '.package':
                        done += 1
                        continue
                    # Für similar-Gruppen brauchen wir all_keys für Überlappung
                    if g['type'] == 'similar':
                        deep = analyze_package_deep(p)
                        # Trotzdem in Cache speichern
                        if deep and deep_cache is not None:
                            try:
                                st = p.stat()
                                deep_cache[str(p)] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': deep[0]}
                            except Exception:
                                pass
                    else:
                        deep = _analyze_with_cache(p, deep_cache)
                    if deep:
                        info = deep[0]
                        keys = deep[1]
                        if keys is not None:
                            file_keys[f['path']] = keys
                        f['deep'] = info
                    done += 1
                    if progress_cb and done % 3 == 0:
                        progress_cb("deep", done, total_files,
                                    f"Tiefenanalyse… ({done}/{total_files})")

            # Key-Überlappung nur für similar-Gruppen
            if g['type'] == 'similar' and len(file_keys) >= 2:
                all_keys_union = set()
                for ks in file_keys.values():
                    all_keys_union |= ks
                shared = set.intersection(*file_keys.values())
                total = len(all_keys_union)
                overlap_pct = len(shared) / total * 100 if total > 0 else 0

                if overlap_pct >= 80:
                    rec = "update"
                    rec_text = "Wahrscheinlich ein Update — behalte nur die neueste Version"
                    rec_color = "#f59e0b"
                elif overlap_pct >= 30:
                    rec = "unclear"
                    rec_text = "Teilweise überlappend — manuell prüfen"
                    rec_color = "#8b5cf6"
                else:
                    rec = "different"
                    rec_text = "Verschiedene Items — wahrscheinlich beide behalten"
                    rec_color = "#22c55e"

                g['deep_comparison'] = {
                    'overlap_pct': round(overlap_pct, 1),
                    'shared_keys': len(shared),
                    'total_keys': total,
                    'recommendation': rec,
                    'recommendation_text': rec_text,
                    'recommendation_color': rec_color,
                }

            # Gemeinsame Kategorie der Gruppe bestimmen (für Header-Badge)
            cats = [f.get('deep', {}).get('category', '') for f in g['files'] if f.get('deep')]
            if cats:
                from collections import Counter
                common_cat = Counter(cats).most_common(1)[0][0]
                g['group_category'] = common_cat

        if progress_cb:
            progress_cb("deep", total_files, total_files, "Tiefenanalyse abgeschlossen")

    # ------------------------------------------------------------------
    # Auto-Kategorisierung: Tiefenanalyse für ALLE gescannten Dateien
    # ------------------------------------------------------------------
    def enrich_all_files(self, progress_cb=None, deep_cache=None):
        """Kategorisiert ALLE gescannten .package-Dateien (nicht nur Problemdateien)."""
        if not self.all_scanned_files:
            return
        if not hasattr(self, '_all_deep'):
            self._all_deep = {}
        # Bereits analysierte Pfade sammeln (aus enrich_groups)
        analyzed = set(self._all_deep.keys())
        for g in self.groups:
            for f in g.get('files', []):
                d = f.get('deep')
                if d:
                    ps = f['path']
                    analyzed.add(ps)
                    self._all_deep[ps] = d
        for c in self.corrupt:
            d = c.get('deep')
            if d:
                analyzed.add(c.get('path', ''))
        for coll in (self.conflicts, self.addon_pairs):
            for entry in coll:
                for f in entry.get('files', []):
                    d = f.get('deep')
                    if d:
                        ps = f.get('path', '')
                        analyzed.add(ps)
                        self._all_deep[ps] = d
        # Noch nicht analysierte .package-Dateien
        todo = [p for p in self.all_scanned_files
                if str(p) not in analyzed and p.suffix.lower() == '.package']
        if not todo:
            if progress_cb:
                progress_cb("categorize", 0, 0, "Alle Dateien bereits kategorisiert")
            return
        total = len(todo)
        cached_count = 0
        for i, p in enumerate(todo):
            ps = str(p)
            try:
                # Cache prüfen
                if deep_cache is not None and ps in deep_cache:
                    ce = deep_cache[ps]
                    if _cache_entry_valid(ce, p):
                        self._all_deep[ps] = ce['deep']
                        cached_count += 1
                        if progress_cb and ((i + 1) % 50 == 0 or i + 1 == total):
                            progress_cb("categorize", i + 1, total,
                                        f"Kategorisiere… ({i + 1}/{total}, {cached_count} aus Cache)")
                        continue
                # Nicht im Cache → frisch analysieren
                result = analyze_package_deep(p)
                if result:
                    self._all_deep[ps] = result[0]
                    # In Cache speichern
                    if deep_cache is not None:
                        try:
                            st = p.stat()
                            deep_cache[ps] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': result[0]}
                        except Exception:
                            pass
            except Exception:
                pass
            if progress_cb and ((i + 1) % 20 == 0 or i + 1 == total):
                progress_cb("categorize", i + 1, total,
                            f"Kategorisiere… ({i + 1}/{total}, {cached_count} aus Cache)")
        if progress_cb:
            progress_cb("categorize", total, total,
                        f"Kategorisierung abgeschlossen ({cached_count}/{total} aus Cache)")

    # ------------------------------------------------------------------
    # Mod-Abhängigkeits-Erkennung
    # ------------------------------------------------------------------
    def detect_dependencies(self):
        """Erkennt Abhängigkeiten und Zusammengehörigkeit zwischen Mod-Dateien."""
        if not self.all_scanned_files:
            self.dependencies = []
            return
        # --- 1. Script+Package-Paare (gleicher Stem) ---
        by_stem = defaultdict(list)
        for p in self.all_scanned_files:
            by_stem[p.stem.lower()].append(p)
        pairs = []
        for stem, paths in by_stem.items():
            exts = set(p.suffix.lower() for p in paths)
            if '.package' in exts and '.ts4script' in exts:
                pkgs = [p for p in paths if p.suffix.lower() == '.package']
                scripts = [p for p in paths if p.suffix.lower() == '.ts4script']
                pairs.append({
                    'type': 'script_pair',
                    'label': 'Script + Package',
                    'hint': 'Diese Dateien gehören zusammen — bitte BEIDE behalten oder BEIDE entfernen!',
                    'icon': '🔗',
                    'files': [str(p) for p in sorted(pkgs + scripts)],
                    'stem': stem,
                })
        # --- 2. Namens-basierte Abhängigkeiten ---
        _DEP_RE = re.compile(
            r'(?:^|[_\-.\s])'
            r'(?:requires?|needs?|depends?(?:_?on)?|patch[_\-]?for|addon[_\-]?for|based[_\-]?on|extension[_\-]?for)'
            r'[_\-.\s]+'
            r'(.+)',
            re.IGNORECASE,
        )
        name_deps = []
        all_stems = {p.stem.lower(): p for p in self.all_scanned_files}
        for p in self.all_scanned_files:
            m = _DEP_RE.search(p.stem)
            if m:
                dep_name = normalize_mod_name(m.group(1))
                # Suche die Basis-Mod
                candidates = []
                for other_stem, other_p in all_stems.items():
                    if other_p == p:
                        continue
                    if dep_name and dep_name in normalize_mod_name(other_stem):
                        candidates.append(other_p)
                if candidates:
                    name_deps.append({
                        'type': 'name_dependency',
                        'label': 'Benötigt Basis-Mod',
                        'hint': f'"{p.name}" scheint einen anderen Mod zu benötigen.',
                        'icon': '📎',
                        'files': [str(p)] + [str(c) for c in candidates[:3]],
                        'stem': p.stem.lower(),
                    })
        # --- 3. Mod-Familien (gleicher Prefix, 3+ Dateien) ---
        prefix_groups = defaultdict(list)
        for p in self.all_scanned_files:
            parts = re.split(r'[_\-\s]+', p.stem.lower())
            if len(parts) >= 2:
                prefix = parts[0]
                if len(prefix) >= 3:
                    prefix_groups[prefix].append(p)
        families = []
        for prefix, members in prefix_groups.items():
            if len(members) >= 3:
                families.append({
                    'type': 'mod_family',
                    'label': f'Mod-Familie „{prefix}"',
                    'hint': f'{len(members)} Dateien mit dem Prefix „{prefix}" — gehören vermutlich zusammen.',
                    'icon': '👨‍👩‍👧‍👦',
                    'files': [str(p) for p in sorted(members)],
                    'stem': prefix,
                    'count': len(members),
                })
        families.sort(key=lambda f: -f['count'])
        self.dependencies = pairs + name_deps + families[:20]

    def remove_file(self, file_path: str):
        target = (file_path or "").strip().lower()
        for g in list(self.groups):
            g["files"] = [f for f in g["files"] if str(f.get("path", "")).strip().lower() != target]
            if len(g["files"]) < 2:
                self.groups.remove(g)

    def to_json(self) -> dict:
        wasted = 0
        for g in self.groups:
            if g["type"] == "content" and g["size_each"] is not None and len(g["files"]) > 1:
                wasted += g["size_each"] * (len(g["files"]) - 1)

        # --- Statistiken: Alle Dateien sammeln (dedupliziert) ---
        seen_paths_stats = set()
        all_unique_files = []
        for g in self.groups:
            for f in g.get('files', []):
                if f['path'] not in seen_paths_stats:
                    seen_paths_stats.add(f['path'])
                    all_unique_files.append(f)
        for c in self.corrupt:
            p = c.get('path', '')
            if p and p not in seen_paths_stats:
                seen_paths_stats.add(p)
                all_unique_files.append(c)
        for conf in self.conflicts:
            for f in conf.get('files', []):
                p = f.get('path', '')
                if p and p not in seen_paths_stats:
                    seen_paths_stats.add(p)
                    all_unique_files.append(f)
        for ap in self.addon_pairs:
            for f in ap.get('files', []):
                p = f.get('path', '')
                if p and p not in seen_paths_stats:
                    seen_paths_stats.add(p)
                    all_unique_files.append(f)

        total_size = sum(f.get('size', 0) for f in all_unique_files)

        # Kategorie-Zählung wird NACH all_files_list-Aufbau berechnet (s.u.)

        # Ordner-Größen (pro mod_folder)
        folder_sizes = {}
        folder_counts = {}
        for f in all_unique_files:
            mf = f.get('mod_folder', '(Mods-Root)')
            folder_sizes[mf] = folder_sizes.get(mf, 0) + f.get('size', 0)
            folder_counts[mf] = folder_counts.get(mf, 0) + 1

        # Top 10 größte Dateien
        sorted_by_size = sorted(all_unique_files, key=lambda f: -(f.get('size', 0)))
        top10 = []
        for f in sorted_by_size[:10]:
            top10.append({
                'path': f.get('path', ''),
                'rel': f.get('rel', ''),
                'mod_folder': f.get('mod_folder', ''),
                'size': f.get('size', 0),
                'size_h': f.get('size_h', '?'),
            })

        # Top 10 größte Ordner
        sorted_folders = sorted(folder_sizes.items(), key=lambda x: -x[1])
        top10_folders = [{'name': n, 'size': s, 'size_h': human_size(s), 'count': folder_counts.get(n, 0)} for n, s in sorted_folders[:10]]

        # Veraltete Mods sammeln (vor letztem Patch geändert)
        outdated = []
        if self.game_info:
            patch_ts = self.game_info['patch_ts']
            # Alle Dateien aus allen Gruppen sammeln
            seen_paths = set()
            all_files = []
            for g in self.groups:
                for f in g.get('files', []):
                    if f['path'] not in seen_paths:
                        seen_paths.add(f['path'])
                        all_files.append(f)
            # Auch korrupte Dateien, Konflikte etc.
            for c in self.corrupt:
                p = c.get('path', '')
                if p and p not in seen_paths:
                    seen_paths.add(p)
                    all_files.append(c)
            # Dateien nach mtime filtern
            for f in all_files:
                mt_str = f.get('mtime', '?')
                if mt_str == '?':
                    continue
                try:
                    mt = datetime.strptime(mt_str, '%Y-%m-%d %H:%M:%S').timestamp()
                except Exception:
                    continue
                if mt < patch_ts:
                    days_old = int((patch_ts - mt) / 86400)
                    f_copy = dict(f)
                    f_copy['days_before_patch'] = days_old
                    # Risiko-Einstufung
                    p_lower = f.get('path', '').lower()
                    if p_lower.endswith('.ts4script'):
                        f_copy['risk'] = 'hoch'
                        f_copy['risk_reason'] = 'Script-Mod — bricht häufig nach Patches'
                    else:
                        # Tiefenanalyse-Kategorie nutzen (falls vorhanden)
                        deep = f.get('deep', {})
                        cat = deep.get('category', '') if isinstance(deep, dict) else ''
                        if 'Tuning' in cat or 'Gameplay' in cat:
                            f_copy['risk'] = 'mittel'
                            f_copy['risk_reason'] = 'Tuning-Mod — kann nach Patches Probleme machen'
                        elif 'CAS' in cat:
                            f_copy['risk'] = 'niedrig'
                            f_copy['risk_reason'] = 'CAS/CC — bricht selten nach Patches'
                        elif 'Objekt' in cat:
                            f_copy['risk'] = 'niedrig'
                            f_copy['risk_reason'] = 'Objekt/Möbel — bricht selten'
                        else:
                            f_copy['risk'] = 'unbekannt'
                            f_copy['risk_reason'] = 'Typ nicht erkannt'
                    outdated.append(f_copy)
            outdated.sort(key=lambda x: (-{'hoch':3,'mittel':2,'niedrig':1}.get(x.get('risk',''),0), -x.get('days_before_patch',0)))

        # --- ALLE gescannten Dateien als file_obj aufbereiten ---
        all_files_list = []
        _deep_map = getattr(self, '_all_deep', {})
        if self.all_scanned_files:
            seen_all = set()
            # Zuerst die bereits aufbereiteten Dateien aus Problemkategorien nutzen
            existing_objs = {}  # path -> file_obj
            for f in all_unique_files:
                existing_objs[f.get('path', '')] = f
            for p in self.all_scanned_files:
                ps = str(p)
                if ps in seen_all:
                    continue
                seen_all.add(ps)
                if ps in existing_objs:
                    obj = existing_objs[ps]
                else:
                    obj = self._file_obj(p)
                # Deep-Daten aus enrich_all_files anfügen (falls vorhanden und noch nicht da)
                if not obj.get('deep') and ps in _deep_map:
                    obj['deep'] = _deep_map[ps]
                all_files_list.append(obj)

        total_scanned = len(all_files_list) if all_files_list else len(all_unique_files)

        # Kategorie-Zählung aus deep analysis (nutze all_files_list für vollständige Abdeckung)
        cat_source = all_files_list if all_files_list else all_unique_files
        cat_counts = {}
        for f in cat_source:
            deep = f.get('deep', {})
            cat = deep.get('category', '') if isinstance(deep, dict) else ''
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            else:
                cat_counts['Unbekannt'] = cat_counts.get('Unbekannt', 0) + 1
        cat_counts_sorted = sorted(cat_counts.items(), key=lambda x: -x[1])

        # Abhängigkeiten
        deps = getattr(self, 'dependencies', [])

        return {
            "created_at": self.created_at,
            "roots": [{"label": f"Ordner {i+1}", "path": str(r)} for i, r in enumerate(self.roots)],
            "game_info": self.game_info,
            "summary": {
                "groups_name": sum(1 for g in self.groups if g["type"] == "name"),
                "groups_content": sum(1 for g in self.groups if g["type"] == "content"),
                "groups_similar": sum(1 for g in self.groups if g["type"] == "similar"),
                "corrupt_count": len(self.corrupt),
                "conflict_count": len(self.conflicts),
                "addon_count": len(self.addon_pairs),
                "outdated_count": len(outdated),
                "dependency_count": len(deps),
                "entries_total": sum(len(g["files"]) for g in self.groups),
                "total_files": total_scanned,
                "problem_files": len(all_unique_files),
                "total_size": total_size,
                "total_size_h": human_size(total_size),
                "wasted_bytes_est": wasted,
                "wasted_h": human_size(wasted),
                "non_mod_count": len(self.non_mod_files),
            },
            "stats": {
                "category_counts": cat_counts_sorted,
                "top10_biggest": top10,
                "top10_folders": top10_folders,
            },
            "groups": self.groups,
            "corrupt": self.corrupt,
            "conflicts": self.conflicts,
            "addon_pairs": self.addon_pairs,
            "outdated": outdated,
            "dependencies": deps,
            "all_files": all_files_list,
            "non_mod_files": self.non_mod_files,
            "non_mod_by_ext": getattr(self, '_non_mod_by_ext', []),
        }


# ---- Sims 4 Fehlerlog-Analyse (menschenlesbar) ----

import traceback as _tb

def find_sims4_userdir(scan_roots: list[Path] = None) -> Path | None:
    """Versucht das Sims 4 Benutzerverzeichnis automatisch zu finden.
    Durchsucht: Scan-Roots, alle bekannten Standard-Pfade, alle Benutzerordner."""
    
    candidates = []
    
    # 1. Aus den Scan-Roots ableiten (falls vorhanden)
    if scan_roots:
        for r in scan_roots:
            p = r
            for _ in range(6):
                if (p / "GameVersion.txt").exists() or (p / "Options.ini").exists():
                    return p
                if p.parent == p:
                    break
                p = p.parent
            # Auch resolved version prüfen (für Junctions)
            try:
                r_resolved = r.resolve()
                p = r_resolved
                for _ in range(6):
                    if (p / "GameVersion.txt").exists() or (p / "Options.ini").exists():
                        return p
                    if p.parent == p:
                        break
                    p = p.parent
            except Exception:
                pass
    
    # 2. Standard-Pfade prüfen (Deutsch + Englisch + verschiedene Laufwerke)
    userprofile = os.environ.get("USERPROFILE", str(Path.home()))
    
    # Verschiedene "Documents" Ordner (auch OneDrive-Umleitungen)
    doc_paths = set()
    doc_paths.add(Path(userprofile) / "Documents")
    doc_paths.add(Path(userprofile) / "Dokumente")
    doc_paths.add(Path(userprofile) / "OneDrive" / "Documents")
    doc_paths.add(Path(userprofile) / "OneDrive" / "Dokumente")
    
    # Windows Known Folder für Dokumente
    try:
        import ctypes.wintypes
        CSIDL_PERSONAL = 5
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
        if buf.value:
            doc_paths.add(Path(buf.value))
    except Exception:
        pass
    
    # Sims 4 Ordnernamen (verschiedene Sprachen)
    sims4_names = ["Die Sims 4", "The Sims 4", "Les Sims 4", "Los Sims 4"]
    
    for doc in doc_paths:
        for name in sims4_names:
            candidate = doc / "Electronic Arts" / name
            if candidate.exists() and (candidate / "Options.ini").exists():
                return candidate
            # Auch ohne Options.ini akzeptieren wenn Mods-Ordner existiert
            if candidate.exists() and (candidate / "Mods").exists():
                candidates.append(candidate)
    
    # 3. Laufwerke C und D schnell prüfen (keine Netzlaufwerke!)
    for drive_letter in "CD":
        drive = Path(f"{drive_letter}:\\")
        try:
            if not drive.is_dir():
                continue
        except Exception:
            continue
        for name in sims4_names:
            candidate = drive / "Electronic Arts" / name
            try:
                if candidate.exists() and ((candidate / "Options.ini").exists() or (candidate / "Mods").exists()):
                    candidates.append(candidate)
            except Exception:
                continue
    
    # Ersten Kandidaten zurückgeben
    if candidates:
        return candidates[0]
    
    return None


def parse_sims4_errors(sims4_dir: Path) -> list[dict]:
    """Liest alle relevanten Fehlerlogs und gibt verständliche Erklärungen zurück."""
    errors = []

    # Bekannte Fehler-Muster mit Erklärungen
    PATTERNS = [
        {
            "regex": r"ImportError.*No module named '([^']+)'",
            "titel": "Fehlende Mod-Abhängigkeit",
            "erklaerung": "Ein Mod versucht ein anderes Modul zu laden, das nicht installiert ist: '{1}'.",
            "loesung": "Prüfe ob der Mod alle benötigten Dateien hat. Eventuell fehlt ein Zusatz-Mod oder eine Bibliothek.",
            "schwere": "hoch",
        },
        {
            "regex": r"AttributeError.*'(\w+)' object has no attribute '(\w+)'",
            "titel": "Veralteter oder kaputter Mod",
            "erklaerung": "Ein Mod versucht eine Funktion zu nutzen, die es nicht gibt: '{1}' hat kein '{2}'.",
            "loesung": "Aktualisiere den betroffenen Mod oder entferne ihn. Häufig nach einem Spiel-Update.",
            "schwere": "hoch",
        },
        {
            "regex": r"KeyError:\s*(\S+)",
            "titel": "Fehlende Daten / Schlüssel nicht gefunden",
            "erklaerung": "Ein Mod sucht nach Daten die nicht existieren (Schlüssel: {1}).",
            "loesung": "Meistens ein veralteter Mod oder fehlende Animations-/CC-Dateien. Mod aktualisieren.",
            "schwere": "mittel",
        },
        {
            "regex": r"TypeError.*argument.*'(\w+)'.*'(\w+)'",
            "titel": "Falscher Datentyp",
            "erklaerung": "Ein Mod übergibt den falschen Datentyp: erwartet '{1}', bekommen '{2}'.",
            "loesung": "Mod ist nicht kompatibel mit der aktuellen Spielversion. Update suchen.",
            "schwere": "hoch",
        },
        {
            "regex": r"FileNotFoundError.*'([^']+)'",
            "titel": "Datei nicht gefunden",
            "erklaerung": "Eine Datei wurde nicht gefunden: '{1}'.",
            "loesung": "Die Datei wurde gelöscht oder verschoben. Mod neu installieren.",
            "schwere": "mittel",
        },
        {
            "regex": r"Error #1009.*?Cannot access a property or method of a null object.*?(\w+)/(\w+)",
            "titel": "UI-Fehler (Flash/ActionScript)",
            "erklaerung": "Die Benutzeroberfläche hat einen Fehler in {1}/{2}.",
            "loesung": "Kann von UI-Mods wie 'UI Cheats Extension' kommen, oder ein EA Base-Game Bug sein. UI-Mod aktualisieren oder im EA-Forum nachschauen.",
            "schwere": "mittel",
        },
        {
            "regex": r"Error #1009",
            "titel": "UI-Fehler (Flash/ActionScript)",
            "erklaerung": "Die Benutzeroberfläche versucht auf etwas zuzugreifen, das nicht existiert.",
            "loesung": "Häufig ein EA Base-Game Bug oder ein Problem mit UI-Mods. Cache löschen (localthumbcache.package) kann helfen.",
            "schwere": "mittel",
        },
        {
            "regex": r"ModuleNotFoundError.*No module named '([^']+)'",
            "titel": "Python-Modul fehlt",
            "erklaerung": "Das Python-Modul '{1}' wurde nicht gefunden.",
            "loesung": "Ein Mod benötigt eine Bibliothek die fehlt. Entweder den Mod aktualisieren oder die fehlende Datei nachinstallieren.",
            "schwere": "hoch",
        },
        {
            "regex": r"Exception.*?version.*?mismatch|incompatible.*?version",
            "titel": "Versions-Konflikt",
            "erklaerung": "Zwei Mods oder ein Mod und das Spiel haben inkompatible Versionen.",
            "loesung": "Alle Mods auf die neueste Version aktualisieren.",
            "schwere": "hoch",
        },
        {
            "regex": r"NameError.*name '(\w+)' is not defined",
            "titel": "Unbekannter Name",
            "erklaerung": "Ein Mod verwendet '{1}', aber das ist nicht definiert.",
            "loesung": "Mod ist beschädigt oder veraltet. Neu herunterladen.",
            "schwere": "hoch",
        },
    ]

    # WickedWhims-spezifische Muster
    WW_PATTERNS = [
        {
            "regex": r"KeyError.*_cache_sex_posture_animation_data",
            "titel": "WickedWhims: Kaputte Animation",
            "erklaerung": "Eine WickedWhims-Animation ist veraltet oder beschädigt.",
            "loesung": "Benutze Sims 4 Studio → 'Find Resource' mit der angegebenen Resource-ID um die kaputte Animation zu finden und zu entfernen.",
            "schwere": "niedrig",
        },
        {
            "regex": r"WickedWhims.*outdated.*broken",
            "titel": "WickedWhims: Veraltete/Kaputte Mods erkannt",
            "erklaerung": "WickedWhims hat veraltete oder kaputte Animations-Mods erkannt.",
            "loesung": "Die genannten Resource-IDs in Sims 4 Studio suchen und die betroffenen Dateien entfernen oder aktualisieren.",
            "schwere": "mittel",
        },
    ]

    # MCCC-spezifische Muster
    MCCC_PATTERNS = [
        {
            "regex": r"mc_cmd_center.*failed to load|MCCC.*load.*fail",
            "titel": "MCCC: Laden fehlgeschlagen",
            "erklaerung": "MC Command Center konnte nicht korrekt geladen werden.",
            "loesung": "MCCC komplett neu installieren. Alle mc_*.ts4script und mc_*.package Dateien ersetzen.",
            "schwere": "hoch",
        },
    ]

    ALL_PATTERNS = PATTERNS + WW_PATTERNS + MCCC_PATTERNS

    # Log-Dateien sammeln — NUR die jeweils neueste Version pro Typ
    log_files = []

    def newest_file(pattern: str) -> Path | None:
        """Gibt die neueste Datei zurück die dem Pattern entspricht."""
        files = list(sims4_dir.glob(pattern))
        if not files:
            return None
        # Sortiere nach Änderungsdatum, neueste zuerst
        files.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
        return files[0]

    # lastException — nur die neueste
    newest = newest_file("lastException*.txt")
    if newest:
        log_files.append(("Python-Fehler", newest))

    # lastUIException — nur die neueste
    newest = newest_file("lastUIException*.txt")
    if newest:
        log_files.append(("UI-Fehler", newest))

    # WickedWhims Exception — nur die neueste
    newest = newest_file("WickedWhims*Exception*.txt")
    if newest:
        log_files.append(("WickedWhims-Fehler", newest))

    # Mod-Logs — nur die neueste pro Mod-Name
    mod_logs = sims4_dir / "mod_logs"
    if mod_logs.exists():
        seen_mod_names = set()
        mod_log_files = sorted(mod_logs.glob("*.txt"),
                               key=lambda f: f.stat().st_mtime if f.exists() else 0,
                               reverse=True)
        for f in mod_log_files:
            # Gruppiere nach Mod-Name (ohne Version/Datum)
            base = re.sub(r'_?\d+[\._]\d+.*$', '', f.stem).lower()
            if base not in seen_mod_names:
                seen_mod_names.add(base)
                log_files.append(("Mod-Log", f))

    seen_keys = set()  # Duplikate vermeiden

    for kategorie, log_path in log_files:
        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if not content.strip():
            continue

        # Große Dateien kürzen — Regex auf Megabyte-Dateien ist viel zu langsam
        content_full = content
        if len(content) > 100_000:
            content = content[:100_000]

        # Datum aus Datei extrahieren
        try:
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
        except Exception:
            mtime = "unbekannt"

        # Betroffene Mod-Dateien aus dem Traceback extrahieren (nur erste 200 Zeilen)
        mod_files_found = set()
        for i, line in enumerate(content.splitlines()):
            if i >= 200:
                break
            # Suche nach .ts4script oder .package Referenzen
            ts4_matches = re.findall(r'[\w\-\.]+\.ts4script', line, re.IGNORECASE)
            mod_files_found.update(ts4_matches)
            pkg_matches = re.findall(r'[\w\-\.]+\.package', line, re.IGNORECASE)
            mod_files_found.update(pkg_matches)

        matched = False
        for pat in ALL_PATTERNS:
            m = re.search(pat["regex"], content, re.IGNORECASE)
            if m:
                groups = m.groups()
                erklaerung = pat["erklaerung"]
                for i, g in enumerate(groups, 1):
                    erklaerung = erklaerung.replace(f"{{{i}}}", str(g))

                # Dedup-Key
                key = f"{pat['titel']}|{erklaerung}|{log_path.name}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                errors.append({
                    "kategorie": kategorie,
                    "datei": log_path.name,
                    "datum": mtime,
                    "titel": pat["titel"],
                    "erklaerung": erklaerung,
                    "loesung": pat["loesung"],
                    "schwere": pat["schwere"],
                    "betroffene_mods": sorted(mod_files_found) if mod_files_found else [],
                    "raw_snippet": content[:500].strip(),
                })
                matched = True

        # Wenn kein Muster passt, trotzdem als "Unbekannter Fehler" anzeigen
        if not matched and ("error" in content.lower() or "exception" in content.lower()):
            # Ersten sinnvollen Fehler-Text extrahieren
            first_error = ""
            for line in content.splitlines():
                line_stripped = line.strip()
                if any(kw in line_stripped.lower() for kw in ["error", "exception", "traceback"]):
                    first_error = line_stripped[:200]
                    break

            key = f"unbekannt|{log_path.name}|{first_error[:80]}"
            if key not in seen_keys:
                seen_keys.add(key)
                errors.append({
                    "kategorie": kategorie,
                    "datei": log_path.name,
                    "datum": mtime,
                    "titel": "Sonstiger Fehler",
                    "erklaerung": first_error if first_error else "Ein Fehler wurde erkannt, aber konnte nicht automatisch klassifiziert werden.",
                    "loesung": "Schau dir die Log-Datei genauer an oder frage in der Sims 4 Community.",
                    "schwere": "unbekannt",
                    "betroffene_mods": sorted(mod_files_found) if mod_files_found else [],
                    "raw_snippet": content[:500].strip(),
                })

    # Nach Schwere sortieren
    schwere_order = {"hoch": 0, "mittel": 1, "niedrig": 2, "unbekannt": 3}
    errors.sort(key=lambda e: schwere_order.get(e["schwere"], 99))

    return errors


# ---- History / Snapshots ----

def _history_dir() -> Path:
    """History-Ordner im selben Verzeichnis wie das Programm."""
    d = Path(__file__).resolve().parent / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_json(name: str, data: dict) -> Path:
    """Speichert JSON mit Zeitstempel im history-Ordner."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    p = _history_dir() / f"{name}_{ts}.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return p


def _load_latest(prefix: str) -> dict | None:
    """Lädt den letzten Snapshot mit gegebenem Prefix."""
    hdir = _history_dir()
    files = sorted(hdir.glob(f"{prefix}_*.json"), reverse=True)
    if not files:
        return None
    try:
        with files[0].open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_all_history(prefix: str, max_count: int = 20) -> list[dict]:
    """Lädt alle History-Einträge (nur Metadaten, nicht die vollen Daten)."""
    hdir = _history_dir()
    files = sorted(hdir.glob(f"{prefix}_*.json"), reverse=True)[:max_count]
    results = []
    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Nur Metadaten zurückgeben (nicht alles)
            meta = {k: v for k, v in data.items() if k != "details" and k != "mods"}
            meta["_file"] = fp.name
            results.append(meta)
        except Exception:
            pass
    return results


# -- Custom Creators (persistent) --

_CUSTOM_CREATORS_FILE = Path(__file__).parent / "custom_creators.json"

def _load_custom_creators() -> dict:
    """Lade benutzerdefinierte Creator-Zuordnungen aus JSON-Datei."""
    try:
        if _CUSTOM_CREATORS_FILE.exists():
            with _CUSTOM_CREATORS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[CREATORS] Fehler beim Laden: {ex}", flush=True)
    return {}

def _save_custom_creators(creators: dict):
    """Speichere benutzerdefinierte Creator-Zuordnungen."""
    try:
        with _CUSTOM_CREATORS_FILE.open("w", encoding="utf-8") as f:
            json.dump(creators, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[CREATORS] Fehler beim Speichern: {ex}", flush=True)


# -- Mod-Notizen (persistent) --

_MOD_NOTES_FILE = Path(__file__).parent / "mod_notes.json"

def _load_mod_notes() -> dict:
    """Lade Mod-Notizen aus JSON-Datei."""
    try:
        if _MOD_NOTES_FILE.exists():
            with _MOD_NOTES_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[NOTES] Fehler beim Laden: {ex}", flush=True)
    return {}

def _save_mod_notes(notes: dict):
    """Speichere Mod-Notizen."""
    try:
        with _MOD_NOTES_FILE.open("w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[NOTES] Fehler beim Speichern: {ex}", flush=True)


# -- Mod-Tags (persistent) --

_MOD_TAGS_FILE = Path(__file__).parent / "mod_tags.json"

def _load_mod_tags() -> dict:
    """Lade Mod-Tags aus JSON-Datei."""
    try:
        if _MOD_TAGS_FILE.exists():
            with _MOD_TAGS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[TAGS] Fehler beim Laden: {ex}", flush=True)
    return {}

def _save_mod_tags(tags: dict):
    """Speichere Mod-Tags."""
    try:
        with _MOD_TAGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[TAGS] Fehler beim Speichern: {ex}", flush=True)


# -- 1) Scan-History speichern --

def save_scan_history(files_count: int, name_dupes: dict, content_dupes: dict, roots: list[Path]):
    """Speichert Scan-Ergebnis als History-Eintrag."""
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dateien_gesamt": files_count,
        "duplikate_name_gruppen": len(name_dupes),
        "duplikate_name_dateien": sum(len(v) for v in name_dupes.values()),
        "duplikate_inhalt_gruppen": len(content_dupes),
        "duplikate_inhalt_dateien": sum(len(v) for v in content_dupes.values()),
        "scan_ordner": [str(r) for r in roots],
        "details": {
            "name_keys": list(name_dupes.keys())[:200],
            "content_keys": [k[:16] for k in list(content_dupes.keys())[:200]],
        },
    }
    p = _save_json("scan", data)
    print(f"[HISTORY] Scan gespeichert: {p}", flush=True)
    return data


# -- 2) Fehler-Snapshot speichern & vergleichen --

def save_error_snapshot(errors: list[dict]) -> dict:
    """Speichert Fehler-Snapshot und vergleicht mit dem letzten."""
    # Lade vorherigen Snapshot
    prev = _load_latest("errors")
    prev_keys = set()
    if prev and "error_keys" in prev:
        prev_keys = set(prev["error_keys"])

    # Aktuelle Fehler-Keys erstellen
    current_keys = set()
    for e in errors:
        key = f"{e.get('titel','')}|{e.get('datei','')}|{e.get('erklaerung','')[:80]}"
        current_keys.add(key)
        # NEU/BEKANNT markieren
        if key in prev_keys:
            e["status"] = "bekannt"
        else:
            e["status"] = "neu"

    # Entfernte Fehler (waren vorher da, jetzt nicht mehr)
    removed_keys = prev_keys - current_keys

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fehler_gesamt": len(errors),
        "fehler_neu": sum(1 for e in errors if e.get("status") == "neu"),
        "fehler_bekannt": sum(1 for e in errors if e.get("status") == "bekannt"),
        "fehler_behoben": len(removed_keys),
        "error_keys": list(current_keys),
    }

    _save_json("errors", data)
    print(f"[HISTORY] Fehler-Snapshot: {data['fehler_gesamt']} Fehler ({data['fehler_neu']} neu, {data['fehler_bekannt']} bekannt, {data['fehler_behoben']} behoben)", flush=True)
    return data


# -- 3) Mod-Snapshot speichern & vergleichen --

def save_mod_snapshot(files: list[Path], roots: list[Path]) -> dict:
    """Speichert Mod-Inventar und vergleicht mit dem letzten Snapshot."""
    # NUR echte Mod-Dateien zählen (.package + .ts4script)
    MOD_EXTS = {".package", ".ts4script"}
    mod_files = [p for p in files if p.suffix.lower() in MOD_EXTS]

    # Duplikate durch Junctions vermeiden: nur eindeutige resolved-Pfade
    seen_resolved = set()
    unique_mod_files = []
    for p in mod_files:
        try:
            resolved = str(p.resolve()).lower()
        except Exception:
            resolved = str(p).lower()
        if resolved not in seen_resolved:
            seen_resolved.add(resolved)
            unique_mod_files.append(p)

    # Lade vorherigen Snapshot
    prev = _load_latest("mods")
    prev_mods = {}
    if prev and "mods" in prev:
        prev_mods = {m["name"].lower(): m for m in prev["mods"]}

    # Aktuelles Inventar erstellen (Name als Key, nicht Pfad — Junction-safe)
    current_mods = []
    for p in unique_mod_files:
        try:
            st = p.stat()
            mod_info = {
                "path": str(p),
                "name": p.name,
                "size": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "folder": p.parent.name,
            }
            current_mods.append(mod_info)
        except Exception:
            pass

    current_names = {m["name"].lower() for m in current_mods}
    prev_names = set(prev_mods.keys())

    # Änderungen berechnen (nach Name, nicht Pfad)
    neue = current_names - prev_names
    entfernt = prev_names - current_names
    geaendert = set()
    for m in current_mods:
        key = m["name"].lower()
        prev_m = prev_mods.get(key)
        if prev_m and (prev_m.get("size") != m["size"] or prev_m.get("mtime") != m["mtime"]):
            geaendert.add(key)

    changes = {
        "neue_mods": sorted([n for n in neue])[:100],
        "entfernte_mods": sorted([n for n in entfernt])[:100],
        "geaenderte_mods": sorted([n for n in geaendert])[:100],
    }

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mods_gesamt": len(current_mods),
        "mods_package": sum(1 for m in current_mods if m["name"].lower().endswith(".package")),
        "mods_script": sum(1 for m in current_mods if m["name"].lower().endswith(".ts4script")),
        "groesse_gesamt": sum(m["size"] for m in current_mods),
        "groesse_gesamt_h": human_size(sum(m["size"] for m in current_mods)),
        "neue": len(neue),
        "entfernt": len(entfernt),
        "geaendert": len(geaendert),
        "changes": changes,
        "mods": current_mods,  # Vollständige Liste für nächsten Vergleich
    }

    p = _save_json("mods", data)
    print(f"[HISTORY] Mod-Snapshot: {data['mods_gesamt']} Mods | +{len(neue)} neu, -{len(entfernt)} entfernt, ~{len(geaendert)} geändert | {p}", flush=True)
    return data


# -----------------------------------------------------------


# ---- Auto-Watcher: Erkennt Dateiänderungen im Mods-Ordner ----
class ModFolderWatcher:
    """Überwacht Mod-Ordner auf Änderungen (hinzugefügt/gelöscht/geändert).

    Pollt alle ``interval`` Sekunden und löst bei Änderungen ein Callback aus.
    Verwendet einen Debounce: erst ``debounce`` Sekunden nach der *letzten*
    Änderung wird der Callback aufgerufen (verhindert Spam bei Batch-Kopieren).
    """

    _EXTS = {".package", ".ts4script"}

    def __init__(self, roots: list[Path], on_change, interval: float = 5.0, debounce: float = 4.0):
        self.roots = roots
        self.on_change = on_change
        self.interval = interval
        self.debounce = debounce
        self._snapshot: dict[str, tuple[float, int]] = {}  # path → (mtime, size)
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_change_time: float | None = None
        self._pending_changes: list[str] = []
        self.last_event: str = ""  # Letzte Änderungs-Nachricht für Web-UI
        self.last_event_time: float = 0

    def _build_snapshot(self) -> dict[str, tuple[float, int]]:
        snap = {}
        ignore_dirs = {"__macosx", ".git", "__pycache__"}
        for root in self.roots:
            if not root.exists():
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    # Filter: Junctions, Symlinks, ignorierte Ordner
                    filtered = []
                    for d in dirnames:
                        if d.lower() in ignore_dirs:
                            continue
                        dp = Path(dirpath) / d
                        try:
                            if dp.is_symlink():
                                continue
                            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(dp))
                            if attrs != -1 and (attrs & 0x400):
                                continue
                        except Exception:
                            pass
                        filtered.append(d)
                    dirnames[:] = filtered

                    for fn in filenames:
                        p = Path(dirpath) / fn
                        try:
                            if not p.is_file() or p.is_symlink():
                                continue
                            if p.suffix.lower() not in self._EXTS:
                                continue
                            st = p.stat()
                            snap[str(p)] = (st.st_mtime, st.st_size)
                        except Exception:
                            pass
            except Exception:
                pass
        return snap

    def _diff(self, old: dict, new: dict) -> list[str]:
        changes = []
        for p in new:
            if p not in old:
                changes.append(f"+ {Path(p).name}")
            elif new[p] != old[p]:
                changes.append(f"~ {Path(p).name}")
        for p in old:
            if p not in new:
                changes.append(f"- {Path(p).name}")
        return changes

    def _poll_loop(self):
        # Initialen Snapshot aufbauen
        self._snapshot = self._build_snapshot()
        print(f"[WATCHER] Gestartet — {len(self._snapshot)} Dateien überwacht", flush=True)

        while self._running:
            time.sleep(self.interval)
            if not self._running:
                break
            try:
                new_snap = self._build_snapshot()
                changes = self._diff(self._snapshot, new_snap)
                if changes:
                    self._snapshot = new_snap
                    self._pending_changes = changes
                    self._last_change_time = time.time()
                    summary = ", ".join(changes[:5])
                    if len(changes) > 5:
                        summary += f" (+{len(changes) - 5} weitere)"
                    self.last_event = f"{len(changes)} Änderung(en): {summary}"
                    self.last_event_time = time.time()
                    print(f"[WATCHER] {self.last_event}", flush=True)

                # Debounce: Wenn Änderungen pending sind und genug Zeit vergangen
                if (self._last_change_time is not None
                        and time.time() - self._last_change_time >= self.debounce
                        and self._pending_changes):
                    pending = self._pending_changes
                    self._pending_changes = []
                    self._last_change_time = None
                    print(f"[WATCHER] Debounce abgelaufen — starte Auto-Rescan ({len(pending)} Änderungen)", flush=True)
                    try:
                        self.on_change(pending)
                    except Exception as ex:
                        print(f"[WATCHER] Callback-Fehler: {ex}", flush=True)
            except Exception as ex:
                print(f"[WATCHER] Poll-Fehler: {ex}", flush=True)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="ModWatcher")
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread = None
        print("[WATCHER] Gestoppt", flush=True)


class LocalServer:
    def __init__(self, dataset: Dataset, quarantine_dir: Path, sims4_dir: str = "", cf_path: str = ""):
        self.dataset = dataset
        self.quarantine_dir = quarantine_dir
        self.sims4_dir = sims4_dir
        self.cf_path = cf_path
        self.token = secrets.token_urlsafe(24)
        self.port = None
        self.httpd = None
        self.log_file = self.quarantine_dir / "_sims4_actions.log.txt"
        self.scan_history = {}
        self.mod_snapshot = {}
        # Shared progress state for live progress bar
        self._progress = {"active": False, "phase": "", "cur": 0, "total": 0, "msg": "", "done": False, "error": ""}
        self._watcher: ModFolderWatcher | None = None
        self._auto_rescan_msg = ""  # Letzte Auto-Rescan Nachricht
        self._auto_rescan_time: float = 0

    def _start_watcher(self):
        """Startet den Datei-Watcher für automatische Rescans."""
        roots = self.dataset.roots if self.dataset else []
        if not roots:
            return

        def on_change(changes: list[str]):
            # Nur Rescan starten wenn kein Scan läuft
            if self._progress.get("active"):
                print("[WATCHER] Scan läuft bereits — Auto-Rescan übersprungen", flush=True)
                return
            self._auto_rescan_msg = f"🔄 Änderungen erkannt ({len(changes)}), starte Auto-Rescan…"
            self._auto_rescan_time = time.time()
            self._trigger_rescan()

        self._watcher = ModFolderWatcher(roots, on_change=on_change, interval=5.0, debounce=4.0)
        self._watcher.start()

    def _trigger_rescan(self):
        """Interner Rescan (gleiche Logik wie der Web-Rescan)."""
        server_ref = self

        def rescan_auto():
            try:
                server_ref._progress.update({"active": True, "phase": "collect", "cur": 0, "total": 0, "msg": "Auto-Rescan…", "done": False, "error": ""})
                def progress_cb(phase, cur, total, msg):
                    server_ref._progress.update({"phase": phase, "cur": cur or 0, "total": total or 0, "msg": msg or ""})

                roots = server_ref.dataset.roots
                exts = {".package", ".ts4script", ".zip", ".7z", ".rar"}
                ignore_dirs = {"__macosx", ".git", "__pycache__"}
                sims4_dir = server_ref.sims4_dir

                files, name_d, content_d, similar_d, corrupt, conflicts, addon_pairs = scan_duplicates(
                    roots=roots, exts=exts, ignore_dirs=ignore_dirs,
                    do_name=True, do_content=True, do_conflicts=True,
                    progress_cb=progress_cb,
                )
                ds = Dataset(roots, sims4_dir=sims4_dir)
                ds.all_scanned_files = files
                ds.build_from_scan(name_d, content_d, similar_d, corrupt, conflicts, addon_pairs)

                deep_cache = load_deep_cache()
                server_ref._progress.update({"phase": "deep", "cur": 0, "total": 0, "msg": "Tiefenanalyse…"})
                ds.enrich_groups(progress_cb=progress_cb, deep_cache=deep_cache)
                ds.enrich_all_files(progress_cb=progress_cb, deep_cache=deep_cache)
                ds.detect_dependencies()
                ds.collect_non_mod_files()
                save_deep_cache(deep_cache)

                try:
                    server_ref.scan_history = save_scan_history(len(files), name_d, content_d, roots)
                    server_ref.mod_snapshot = save_mod_snapshot(files, roots)
                except Exception:
                    pass

                server_ref.dataset = ds
                server_ref._auto_rescan_msg = f"✅ Auto-Rescan fertig — {len(files)} Dateien"
                server_ref._auto_rescan_time = time.time()
                server_ref._progress.update({"active": False, "done": True, "phase": "done", "msg": f"Auto-Rescan fertig! {len(files)} Dateien."})
                # Watcher-Snapshot aktualisieren damit kein erneuter Trigger
                if server_ref._watcher and server_ref._watcher._running:
                    server_ref._watcher._snapshot = server_ref._watcher._build_snapshot()
                print(f"[WATCHER] Auto-Rescan abgeschlossen: {len(files)} Dateien", flush=True)
            except Exception as ex:
                server_ref._progress.update({"active": False, "done": False, "error": str(ex), "phase": "error", "msg": str(ex)})
                print(f"[WATCHER] Auto-Rescan Fehler: {ex}", flush=True)

        threading.Thread(target=rescan_auto, daemon=True, name="AutoRescan").start()

    def _pick_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _append_log(self, line: str):
        try:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{ts}] {line}\n")
        except Exception:
            pass

    def _log_action(self, action: str, path: str, size: int | None = None, status: str = "OK", note: str = ""):
        """Strukturiertes Logging mit Dateigrößen und Status."""
        try:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            size_str = human_size(size) if size else "?"
            
            # Einfache Text-Log
            msg = f"[{ts}] {action:15} | Size: {size_str:12} | {path}"
            if note:
                msg += f" | Note: {note}"
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(msg + "\n")
            
            # Strukturiertes JSON-Log
            csv_file = self.quarantine_dir / "_sims4_actions.csv"
            import csv
            file_exists = csv_file.exists()
            with csv_file.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Timestamp", "Action", "Size (Bytes)", "Size (Human)", "Path", "Status", "Note"])
                writer.writerow([ts, action, size or "", size_str, path, status, note])
        except Exception:
            pass

    def start(self):
        from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
        from urllib.parse import urlparse, parse_qs

        self.port = self._pick_free_port()
        token = self.token
        dataset = self.dataset
        quarantine_dir = self.quarantine_dir
        append_log = self._append_log
        server_ref = self

        quarantine_dir.mkdir(parents=True, exist_ok=True)
        append_log(f"SERVER START {self.port}")

        HTML_PAGE = self._build_html_page()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _send(self, status: int, content: bytes, ctype="text/html; charset=utf-8"):
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)

            def _json(self, status: int, obj: dict):
                self._send(status, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

            def _read_json(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except Exception:
                    length = 0
                data = self.rfile.read(length) if length > 0 else b"{}"
                try:
                    return json.loads(data.decode("utf-8"))
                except Exception:
                    return {}

            def do_GET(self):
                u = urlparse(self.path)

                if u.path == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()
                    return

                if u.path == "/":
                    self._send(200, HTML_PAGE.encode("utf-8"))
                    return

                if u.path == "/api/data":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    d = server_ref.dataset.to_json()
                    cfg = load_config()
                    d["ignored_groups"] = cfg.get("ignored_groups", [])
                    self._json(200, {"ok": True, "data": d})
                    return

                if u.path == "/api/errors":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        sims_dir_str = server_ref.sims4_dir
                        sims_dir = Path(sims_dir_str) if sims_dir_str else None
                        if sims_dir and sims_dir.is_dir():
                            print(f"[ERRORS] Sims4 Dir: {sims_dir}", flush=True)
                            errs = parse_sims4_errors(sims_dir)
                            # Fehler-Snapshot speichern & NEU/BEKANNT markieren
                            err_snap = save_error_snapshot(errs)
                            print(f"[ERRORS] {len(errs)} Fehler gefunden ({err_snap.get('fehler_neu',0)} neu, {err_snap.get('fehler_bekannt',0)} bekannt, {err_snap.get('fehler_behoben',0)} behoben)", flush=True)
                            self._json(200, {"ok": True, "sims4_dir": str(sims_dir), "errors": errs, "snapshot": err_snap})
                        else:
                            print("[ERRORS] Kein g\u00fcltiges Sims4 Dir angegeben", flush=True)
                            self._json(200, {"ok": True, "sims4_dir": None, "errors": [], "note": "Kein g\u00fcltiges Sims 4 Verzeichnis angegeben. Bitte in der GUI einstellen."})
                    except Exception as ex:
                        print(f"[ERRORS][CRASH] {type(ex).__name__}: {ex}", flush=True)
                        import traceback; traceback.print_exc()
                        self._json(500, {"ok": False, "error": f"Fehler bei Analyse: {type(ex).__name__}: {ex}"})
                    return

                if u.path == "/api/history":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        scan_hist = _load_all_history("scan", 20)
                        mod_snap = getattr(server_ref, "mod_snapshot", {})
                        self._json(200, {
                            "ok": True,
                            "scan_history": scan_hist,
                            "mod_snapshot": {
                                "mods_gesamt": mod_snap.get("mods_gesamt", 0),
                                "mods_package": mod_snap.get("mods_package", 0),
                                "mods_script": mod_snap.get("mods_script", 0),
                                "groesse_gesamt_h": mod_snap.get("groesse_gesamt_h", "?"),
                                "neue": mod_snap.get("neue", 0),
                                "entfernt": mod_snap.get("entfernt", 0),
                                "geaendert": mod_snap.get("geaendert", 0),
                                "changes": mod_snap.get("changes", {}),
                                "timestamp": mod_snap.get("timestamp", ""),
                            },
                        })
                    except Exception as ex:
                        print(f"[HISTORY][CRASH] {type(ex).__name__}: {ex}", flush=True)
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/quarantine":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        # Alle Quarantäne-Ordner finden (dupe_quarantine_*)
                        q_parent = quarantine_dir.parent
                        q_dirs = sorted(q_parent.glob("dupe_quarantine_*"), reverse=True)
                        q_files = []
                        total_size = 0
                        for qd in q_dirs:
                            if not qd.is_dir():
                                continue
                            for fp in qd.rglob("*"):
                                if fp.is_file() and not fp.name.startswith("_sims4_"):
                                    sz = fp.stat().st_size
                                    total_size += sz
                                    mt = datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                                    q_files.append({
                                        'path': str(fp),
                                        'name': fp.name,
                                        'q_dir': qd.name,
                                        'size': sz,
                                        'size_h': human_size(sz),
                                        'mtime': mt,
                                    })
                        self._json(200, {
                            "ok": True,
                            "files": q_files,
                            "total_count": len(q_files),
                            "total_size_h": human_size(total_size),
                            "q_dirs": [str(d) for d in q_dirs if d.is_dir()],
                        })
                    except Exception as ex:
                        print(f"[QUARANTINE_LIST][ERR] {ex}", flush=True)
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/progress":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    self._json(200, dict(server_ref._progress))
                    return

                if u.path == "/api/watcher":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    w = server_ref._watcher
                    watcher_info = {
                        "active": w is not None and w._running if w else False,
                        "files_watched": len(w._snapshot) if w else 0,
                        "last_event": w.last_event if w else "",
                        "last_event_time": w.last_event_time if w else 0,
                        "auto_rescan_msg": server_ref._auto_rescan_msg,
                        "auto_rescan_time": server_ref._auto_rescan_time,
                    }
                    self._json(200, watcher_info)
                    return

                if u.path == "/api/creators":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        creators = _load_custom_creators()
                        self._json(200, {"ok": True, "creators": creators})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/notes":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        notes = _load_mod_notes()
                        self._json(200, {"ok": True, "notes": notes})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/tags":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        tags = _load_mod_tags()
                        self._json(200, {"ok": True, "tags": tags})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/curseforge":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        cf_data = _read_curseforge_data(cf_manifest_path=server_ref.cf_path)
                        self._json(200, {"ok": True, "curseforge": cf_data})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/mod_export":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    try:
                        ds = server_ref.dataset
                        notes = _load_mod_notes()
                        tags = _load_mod_tags()
                        lines = ["Name;Pfad;Ordner;Größe;Geändert;Creator;Tags;Notiz"]
                        if ds:
                            data = ds.to_json()
                            seen = set()
                            all_files = []
                            for g in data.get('groups', []):
                                for f in g.get('files', []):
                                    if f['path'] not in seen:
                                        seen.add(f['path'])
                                        all_files.append(f)
                            for c in data.get('corrupt', []):
                                p = c.get('path', '')
                                if p and p not in seen:
                                    seen.add(p)
                                    all_files.append(c)
                            for conf in data.get('conflicts', []):
                                for f in conf.get('files', []):
                                    p = f.get('path', '')
                                    if p and p not in seen:
                                        seen.add(p)
                                        all_files.append(f)
                            for ap in data.get('addon_pairs', []):
                                for f in ap.get('files', []):
                                    p = f.get('path', '')
                                    if p and p not in seen:
                                        seen.add(p)
                                        all_files.append(f)
                            all_files.sort(key=lambda f: f.get('path', ''))
                            for f in all_files:
                                fpath = f.get('path', '')
                                fname = Path(fpath).name
                                mfolder = f.get('mod_folder', '')
                                sz = f.get('size_h', '')
                                mt = f.get('mtime', '')
                                deep = f.get('deep', {})
                                cat = deep.get('category', '') if isinstance(deep, dict) else ''
                                ftags = ', '.join(tags.get(fpath, []))
                                fnote = notes.get(fpath, '').replace(';', ',')
                                # Clean semicolons
                                lines.append(f"{fname};{fpath};{mfolder};{sz};{mt};{cat};{ftags};{fnote}")
                        csv_data = '\n'.join(lines)
                        self._send(200, csv_data.encode('utf-8-sig'), 'text/csv; charset=utf-8')
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/tutorial":
                    qs = parse_qs(u.query)
                    if qs.get("token", [""])[0] != token:
                        self._json(403, {"ok": False, "error": "bad token"})
                        return
                    seen = getattr(server_ref, 'app_ref', None)
                    tutorial_seen = getattr(seen, '_tutorial_seen', False) if seen else False
                    self._json(200, {"ok": True, "tutorial_seen": tutorial_seen})
                    return

                self._send(404, b"not found", "text/plain; charset=utf-8")

            def do_POST(self):
                u = urlparse(self.path)
                if u.path != "/api/action":
                    self._json(404, {"ok": False, "error": "not found"})
                    return

                payload = self._read_json()
                if payload.get("token") != token:
                    self._json(403, {"ok": False, "error": "bad token"})
                    return

                action = payload.get("action")
                raw_path = payload.get("path", "")
                p = Path(raw_path)

                # Creator verwalten
                if action in ("add_creator", "edit_creator"):
                    try:
                        key = payload.get("key", "").strip().lower()
                        cname = payload.get("cname", "").strip()
                        curl = payload.get("curl", "").strip()
                        cicon = payload.get("cicon", "").strip() or "🔗"
                        if not key or not cname:
                            self._json(400, {"ok": False, "error": "key und name erforderlich"})
                            return
                        creators = _load_custom_creators()
                        creators[key] = {"name": cname, "url": curl, "icon": cicon}
                        _save_custom_creators(creators)
                        verb = "Edited" if action == "edit_creator" else "Added"
                        self._json(200, {"ok": True, "added": key})
                        print(f"[CREATOR] {verb}: {key} -> {cname} ({curl})", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "delete_creator":
                    try:
                        key = payload.get("key", "").strip().lower()
                        if not key:
                            self._json(400, {"ok": False, "error": "key erforderlich"})
                            return
                        creators = _load_custom_creators()
                        if key in creators:
                            del creators[key]
                            _save_custom_creators(creators)
                        self._json(200, {"ok": True, "deleted": key})
                        print(f"[CREATOR] Deleted: {key}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                # Mod-Notizen verwalten
                if action == "save_note":
                    try:
                        fpath = payload.get("path", "").strip()
                        note_text = payload.get("note", "").strip()
                        if not fpath:
                            self._json(400, {"ok": False, "error": "path erforderlich"})
                            return
                        notes = _load_mod_notes()
                        if note_text:
                            notes[fpath] = note_text
                        elif fpath in notes:
                            del notes[fpath]
                        _save_mod_notes(notes)
                        self._json(200, {"ok": True, "path": fpath})
                        print(f"[NOTE] Saved for: {Path(fpath).name}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                # Mod-Tags verwalten
                if action == "add_tag":
                    try:
                        fpath = payload.get("path", "").strip()
                        tag = payload.get("tag", "").strip()
                        if not fpath or not tag:
                            self._json(400, {"ok": False, "error": "path und tag erforderlich"})
                            return
                        tags = _load_mod_tags()
                        if fpath not in tags:
                            tags[fpath] = []
                        if tag not in tags[fpath]:
                            tags[fpath].append(tag)
                        _save_mod_tags(tags)
                        self._json(200, {"ok": True, "path": fpath, "tags": tags[fpath]})
                        print(f"[TAG] Added '{tag}' to: {Path(fpath).name}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "remove_tag":
                    try:
                        fpath = payload.get("path", "").strip()
                        tag = payload.get("tag", "").strip()
                        if not fpath or not tag:
                            self._json(400, {"ok": False, "error": "path und tag erforderlich"})
                            return
                        tags = _load_mod_tags()
                        if fpath in tags and tag in tags[fpath]:
                            tags[fpath].remove(tag)
                            if not tags[fpath]:
                                del tags[fpath]
                        _save_mod_tags(tags)
                        self._json(200, {"ok": True, "path": fpath, "tags": tags.get(fpath, [])})
                        print(f"[TAG] Removed '{tag}' from: {Path(fpath).name}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                # ---- Mod-Import-Manager ----
                if action == "import_upload":
                    # Upload einer einzelnen Datei per Drag&Drop / Dateiauswahl
                    # relative_path = Unterordner-Pfad um Ordnerstruktur 1:1 zu übernehmen
                    try:
                        import base64 as _b64
                        filename = payload.get("filename", "").strip()
                        filedata_b64 = payload.get("filedata", "")
                        subfolder = payload.get("subfolder", "").strip()
                        relative_path = payload.get("relative_path", "").strip().replace("\\", "/")
                        # Sicherheit: keine .. im relativen Pfad
                        if ".." in relative_path:
                            self._json(400, {"ok": False, "error": "Ungültiger Pfad"})
                            return
                        if not filename:
                            self._json(400, {"ok": False, "error": "Kein Dateiname"})
                            return
                        file_bytes = _b64.b64decode(filedata_b64)
                        # Temp-Datei schreiben
                        import tempfile as _tf
                        tmp_dir = Path(_tf.gettempdir()) / "sims4_import"
                        tmp_dir.mkdir(parents=True, exist_ok=True)
                        tmp_path = tmp_dir / filename
                        tmp_path.write_bytes(file_bytes)
                        src_name = filename.lower()
                        src_hash = file_sha256(tmp_path)
                        src_size = len(file_bytes)
                        matches = []
                        # Mod-Dateien: gegen gescannte Dateien prüfen
                        mod_exts = {".package", ".ts4script"}
                        ext = Path(filename).suffix.lower()
                        if ext in mod_exts:
                            existing_files = server_ref.dataset.all_scanned_files if server_ref.dataset else []
                            for ep in existing_files:
                                if not ep.exists():
                                    continue
                                ep_name = ep.name.lower()
                                if ep_name == src_name:
                                    ep_hash = file_sha256(ep)
                                    ep_size, _ = safe_stat(ep)
                                    if ep_hash == src_hash:
                                        matches.append({"path": str(ep), "relation": "identical"})
                                    else:
                                        matches.append({"path": str(ep), "relation": "update", "existing_size": ep_size, "existing_size_h": human_size(ep_size)})
                        else:
                            # Sonstige Dateien: prüfe ob Ziel schon existiert
                            roots = server_ref.dataset.roots if server_ref.dataset else []
                            if roots:
                                check_dir = roots[0]
                                if subfolder:
                                    check_dir = check_dir / subfolder
                                if relative_path:
                                    check_dir = check_dir / relative_path
                                dest_check = check_dir / filename
                                if dest_check.exists():
                                    ep_hash = file_sha256(dest_check)
                                    ep_size, _ = safe_stat(dest_check)
                                    if ep_hash == src_hash:
                                        matches.append({"path": str(dest_check), "relation": "identical"})
                                    else:
                                        matches.append({"path": str(dest_check), "relation": "update", "existing_size": ep_size, "existing_size_h": human_size(ep_size)})
                        if not matches:
                            # Neue Datei — direkt importieren, Ordnerstruktur beibehalten
                            roots = server_ref.dataset.roots if server_ref.dataset else []
                            if not roots:
                                self._json(400, {"ok": False, "error": "Kein Mod-Ordner konfiguriert"})
                                return
                            target_dir = roots[0]
                            if subfolder:
                                target_dir = target_dir / subfolder
                            if relative_path:
                                target_dir = target_dir / relative_path
                            target_dir.mkdir(parents=True, exist_ok=True)
                            dest = target_dir / filename
                            import shutil as _sh
                            _sh.copy2(str(tmp_path), str(dest))
                            self._json(200, {"ok": True, "status": "new", "imported": True, "dest": str(dest), "size_h": human_size(src_size), "relative_path": relative_path})
                            print(f"[IMPORT_UPLOAD] NEW: {filename} -> {dest}", flush=True)
                            append_log(f"IMPORT_UPLOAD NEW {filename} -> {dest}")
                        elif all(m["relation"] == "identical" for m in matches):
                            # Identisch — übersprungen
                            self._json(200, {"ok": True, "status": "identical", "imported": False, "matches": matches})
                            print(f"[IMPORT_UPLOAD] IDENTICAL: {filename}", flush=True)
                        else:
                            # Update oder ähnlich — zur Bestätigung zurückgeben
                            self._json(200, {"ok": True, "status": "update", "imported": False, "matches": matches, "tmp_path": str(tmp_path), "size_h": human_size(src_size)})
                            print(f"[IMPORT_UPLOAD] UPDATE: {filename} ({len(matches)} match(es))", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_upload_confirm":
                    # Bestätigung eines Upload-Updates (überschreibe vorhandene)
                    try:
                        import shutil as _sh
                        tmp_path = Path(payload.get("tmp_path", ""))
                        replace_path = Path(payload.get("replace_path", ""))
                        if not tmp_path.exists():
                            self._json(400, {"ok": False, "error": "Temp-Datei nicht mehr vorhanden"})
                            return
                        _sh.copy2(str(tmp_path), str(replace_path))
                        self._json(200, {"ok": True, "replaced": True, "dest": str(replace_path)})
                        print(f"[IMPORT_UPLOAD] REPLACED: {tmp_path.name} -> {replace_path}", flush=True)
                        append_log(f"IMPORT_UPLOAD REPLACE {tmp_path.name} -> {replace_path}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_scan":
                    # Scanne einen Quell-Ordner nach importierbaren Mod-Dateien
                    try:
                        source_dir = Path(payload.get("source", "").strip())
                        if not source_dir.exists() or not source_dir.is_dir():
                            self._json(400, {"ok": False, "error": f"Ordner nicht gefunden: {source_dir}"})
                            return
                        mod_exts = {".package", ".ts4script"}
                        found_files = []
                        for fp in source_dir.rglob("*"):
                            if fp.is_file() and fp.suffix.lower() in mod_exts:
                                sz, mt = safe_stat(fp)
                                found_files.append({
                                    "path": str(fp),
                                    "name": fp.name,
                                    "size": sz,
                                    "size_h": human_size(sz),
                                    "mtime": datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S") if mt else "?",
                                })
                        self._json(200, {"ok": True, "files": found_files, "count": len(found_files)})
                        print(f"[IMPORT] Scan: {source_dir} -> {len(found_files)} Dateien", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_check":
                    # Prüfe eine Datei gegen vorhandene Mods (Name + Hash)
                    try:
                        source_path = Path(payload.get("source_path", "").strip())
                        if not source_path.exists() or not source_path.is_file():
                            self._json(400, {"ok": False, "error": "Datei nicht gefunden"})
                            return

                        src_name = source_path.name.lower()
                        src_hash = file_sha256(source_path)
                        src_size, _ = safe_stat(source_path)

                        # Gegen alle gescannten Dateien prüfen
                        matches = []
                        existing_files = server_ref.dataset.all_scanned_files if server_ref.dataset else []
                        for ep in existing_files:
                            if not ep.exists():
                                continue
                            ep_name = ep.name.lower()
                            match_type = None
                            # Exakter Hash-Match = identische Datei
                            try:
                                ep_hash = file_sha256(ep)
                                if ep_hash == src_hash:
                                    match_type = "identical"
                            except Exception:
                                ep_hash = ""

                            # Gleicher Dateiname = mögliches Update
                            if not match_type and ep_name == src_name:
                                match_type = "same_name"

                            # Ähnlicher Name (ohne Versionsnummern)
                            if not match_type:
                                import re as _re
                                def _strip_version(n):
                                    n = _re.sub(r'[_\-\s]?v?\d+(\.\d+)*[a-z]?$', '', Path(n).stem, flags=_re.IGNORECASE)
                                    return n.lower().strip()
                                if _strip_version(src_name) == _strip_version(ep_name) and _strip_version(src_name):
                                    match_type = "similar_name"

                            if match_type:
                                ep_sz, ep_mt = safe_stat(ep)
                                matches.append({
                                    "path": str(ep),
                                    "name": ep.name,
                                    "size": ep_sz,
                                    "size_h": human_size(ep_sz),
                                    "match_type": match_type,
                                })

                        # Status bestimmen
                        if any(m["match_type"] == "identical" for m in matches):
                            status = "identical"  # Exakt gleich — überspringen
                        elif any(m["match_type"] == "same_name" for m in matches):
                            status = "update"  # Gleicher Name, anderer Inhalt — Update
                        elif any(m["match_type"] == "similar_name" for m in matches):
                            status = "similar"  # Ähnlicher Name — mögliches Update
                        else:
                            status = "new"  # Komplett neu

                        self._json(200, {
                            "ok": True,
                            "source": str(source_path),
                            "hash": src_hash,
                            "status": status,
                            "matches": matches,
                        })
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_execute":
                    # Führe den Import aus: Kopiere Datei in Mods-Ordner
                    try:
                        source_path = Path(payload.get("source_path", "").strip())
                        subfolder = payload.get("subfolder", "").strip()
                        mode = payload.get("mode", "copy")  # copy, update
                        replace_path = payload.get("replace_path", "").strip()  # Bei update: welche Datei ersetzen

                        if not source_path.exists() or not source_path.is_file():
                            self._json(400, {"ok": False, "error": "Quelldatei nicht gefunden"})
                            return

                        target_root = server_ref.dataset.roots[0] if server_ref.dataset and server_ref.dataset.roots else None
                        if not target_root:
                            self._json(400, {"ok": False, "error": "Kein Mods-Ordner bekannt"})
                            return

                        if mode == "update" and replace_path:
                            # Vorhandene Datei überschreiben
                            dest = Path(replace_path)
                            if not dest.parent.exists():
                                dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(source_path), str(dest))
                            print(f"[IMPORT] UPDATE: {source_path.name} -> {dest}", flush=True)
                            append_log(f"IMPORT_UPDATE {source_path} -> {dest}")
                        else:
                            # Neue Datei kopieren
                            if subfolder:
                                dest_dir = target_root / subfolder
                            else:
                                dest_dir = target_root
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest = dest_dir / source_path.name
                            dest = ensure_unique_path(dest)
                            shutil.copy2(str(source_path), str(dest))
                            print(f"[IMPORT] COPY: {source_path.name} -> {dest}", flush=True)
                            append_log(f"IMPORT_COPY {source_path} -> {dest}")

                        sz, _ = safe_stat(dest)
                        self._json(200, {"ok": True, "dest": str(dest), "size_h": human_size(sz), "mode": mode})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[IMPORT][ERR] {ex}", flush=True)
                    return

                # Rescan-Aktion — startet neuen Scan im Hintergrund
                if action == "rescan":
                    if server_ref._progress.get("active"):
                        self._json(200, {"ok": False, "error": "scan already running"})
                        return
                    def rescan_worker():
                        try:
                            server_ref._progress.update({"active": True, "phase": "collect", "cur": 0, "total": 0, "msg": "Starte Scan…", "done": False, "error": ""})
                            def progress_cb(phase, cur, total, msg):
                                server_ref._progress.update({"phase": phase, "cur": cur or 0, "total": total or 0, "msg": msg or ""})

                            roots = server_ref.dataset.roots
                            exts = {".package", ".ts4script", ".zip", ".7z", ".rar"}
                            ignore_dirs = {"__macosx", ".git", "__pycache__"}
                            sims4_dir = server_ref.sims4_dir

                            files, name_d, content_d, similar_d, corrupt, conflicts, addon_pairs = scan_duplicates(
                                roots=roots, exts=exts, ignore_dirs=ignore_dirs,
                                do_name=True, do_content=True, do_conflicts=True,
                                progress_cb=progress_cb,
                            )
                            ds = Dataset(roots, sims4_dir=sims4_dir)
                            ds.all_scanned_files = files
                            ds.build_from_scan(name_d, content_d, similar_d, corrupt, conflicts, addon_pairs)

                            # DBPF-Cache laden
                            deep_cache = load_deep_cache()

                            server_ref._progress.update({"phase": "deep", "cur": 0, "total": 0, "msg": "Tiefenanalyse…"})
                            ds.enrich_groups(progress_cb=progress_cb, deep_cache=deep_cache)

                            # Auto-Kategorisierung + Abhängigkeiten
                            ds.enrich_all_files(progress_cb=progress_cb, deep_cache=deep_cache)
                            ds.detect_dependencies()
                            ds.collect_non_mod_files()

                            # DBPF-Cache speichern
                            save_deep_cache(deep_cache)

                            try:
                                server_ref.scan_history = save_scan_history(len(files), name_d, content_d, roots)
                                server_ref.mod_snapshot = save_mod_snapshot(files, roots)
                            except Exception:
                                pass

                            # Dataset austauschen (thread-safe genug für unseren Zweck)
                            server_ref.dataset = ds

                            server_ref._progress.update({"active": False, "done": True, "phase": "done", "msg": f"Fertig! {len(files)} Dateien gescannt."})
                            # Watcher-Snapshot aktualisieren
                            if server_ref._watcher and server_ref._watcher._running:
                                server_ref._watcher._snapshot = server_ref._watcher._build_snapshot()
                        except Exception as ex:
                            server_ref._progress.update({"active": False, "done": False, "error": str(ex), "phase": "error", "msg": str(ex)})
                    threading.Thread(target=rescan_worker, daemon=True).start()
                    self._json(200, {"ok": True, "started": True})
                    return

                # Restore-Aktion erlaubt Quarantäne-Pfade
                if action in ("restore", "delete_q"):
                    # Prüfe ob Datei in einem Quarantäne-Ordner liegt
                    q_parent = quarantine_dir.parent
                    try:
                        p.resolve().relative_to(q_parent.resolve())
                        is_q = any(part.startswith("dupe_quarantine_") for part in p.parts)
                    except ValueError:
                        is_q = False
                    if not is_q:
                        self._json(400, {"ok": False, "error": "path not in quarantine"})
                        return
                elif action in ("ignore_group", "unignore_group", "import_upload", "import_upload_confirm", "mark_tutorial_seen", "send_bug_report"):
                    pass  # Diese Aktionen brauchen keinen Dateipfad
                elif not is_under_any_root(p, server_ref.dataset.roots):
                    self._json(400, {"ok": False, "error": "path not allowed (not under selected roots)"})
                    print(f"[BLOCKED] {action} -> {p}", flush=True)
                    append_log(f"BLOCKED {action} {p}")
                    return

                if action == "open_folder":
                    try:
                        import subprocess
                        subprocess.run(["explorer", "/select,", str(p)], check=False)
                        self._json(200, {"ok": True})
                        print(f"[OPEN_FOLDER] {p}", flush=True)
                        append_log(f"OPEN_FOLDER {p}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[OPEN_FOLDER][ERR] {p} :: {ex}", flush=True)
                        append_log(f"OPEN_FOLDER_ERR {p} :: {ex}")
                    return

                if action == "quarantine":
                    try:
                        if not p.exists() or not p.is_file():
                            server_ref.dataset.remove_file(str(p))
                            self._json(200, {"ok": True, "moved": False, "note": "file missing (removed from list)"})
                            print(f"[QUARANTINE][MISSING] {p}", flush=True)
                            self._log_action("QUARANTINE", str(p), None, "MISSING", "file missing")
                            return

                        size, _ = safe_stat(p)
                        idx = best_root_index(p, server_ref.dataset.roots)
                        label = f"Ordner{idx+1}" if idx is not None else "Unbekannt"

                        if idx is not None:
                            rel = p.resolve().relative_to(server_ref.dataset.roots[idx].resolve())
                            dest = quarantine_dir / label / rel
                        else:
                            dest = quarantine_dir / label / p.name

                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest = ensure_unique_path(dest)

                        shutil.move(str(p), str(dest))
                        server_ref.dataset.remove_file(str(p))
                        self._json(200, {"ok": True, "moved": True, "to": str(dest), "path": str(p)})
                        print(f"[QUARANTINE] OK: {p} -> {dest}", flush=True)
                        self._log_action("QUARANTINE", str(p), size, "OK", f"moved to {dest}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[QUARANTINE][ERR] {p} :: {ex}", flush=True)
                        self._log_action("QUARANTINE", str(p), None, "ERROR", str(ex))
                    return

                if action == "delete":
                    try:
                        if not p.exists():
                            server_ref.dataset.remove_file(str(p))
                            self._json(200, {"ok": True, "deleted": False, "note": "file missing (removed from list)", "path": str(p)})
                            print(f"[DELETE][MISSING] {p}", flush=True)
                            self._log_action("DELETE", str(p), None, "MISSING", "file missing")
                            return
                        if not p.is_file():
                            self._json(400, {"ok": False, "error": "not a file"})
                            print(f"[DELETE][NOT_FILE] {p}", flush=True)
                            self._log_action("DELETE", str(p), None, "ERROR", "not a file")
                            return
                        size, _ = safe_stat(p)
                        p.unlink()
                        server_ref.dataset.remove_file(str(p))
                        self._json(200, {"ok": True, "deleted": True, "path": str(p)})
                        print(f"[DELETE] OK: {p}", flush=True)
                        self._log_action("DELETE", str(p), size, "OK", "")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[DELETE][ERR] {p} :: {ex}", flush=True)
                        self._log_action("DELETE", str(p), None, "ERROR", str(ex))
                    return

                if action == "restore":
                    # Datei aus Quarantäne zurück in den Mods-Ordner verschieben
                    try:
                        if not p.exists() or not p.is_file():
                            self._json(200, {"ok": True, "restored": False, "note": "file missing"})
                            return
                        size, _ = safe_stat(p)
                        # Zielordner = erster Scan-Root (Mods-Ordner)
                        target_root = server_ref.dataset.roots[0] if server_ref.dataset.roots else None
                        if not target_root:
                            self._json(400, {"ok": False, "error": "Kein Mod-Ordner bekannt"})
                            return
                        # Versuche relative Struktur zu rekonstruieren
                        try:
                            # Quarantäne-Struktur: quarantine_dir / OrdnerX / rel_path
                            rel_parts = p.relative_to(quarantine_dir.parent).parts
                            # Überspringe: dupe_quarantine_XXX / OrdnerX
                            if len(rel_parts) > 2:
                                rel_path = Path(*rel_parts[2:])
                                dest = target_root / rel_path
                            else:
                                dest = target_root / p.name
                        except ValueError:
                            dest = target_root / p.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest = ensure_unique_path(dest)
                        shutil.move(str(p), str(dest))
                        self._json(200, {"ok": True, "restored": True, "to": str(dest), "path": str(p)})
                        print(f"[RESTORE] OK: {p} -> {dest}", flush=True)
                        server_ref._log_action("RESTORE", str(p), size, "OK", f"restored to {dest}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[RESTORE][ERR] {p} :: {ex}", flush=True)
                        server_ref._log_action("RESTORE", str(p), None, "ERROR", str(ex))
                    return

                if action == "delete_q":
                    # Datei endgültig aus Quarantäne löschen
                    try:
                        if not p.exists() or not p.is_file():
                            self._json(200, {"ok": True, "deleted": False, "note": "file missing"})
                            return
                        size, _ = safe_stat(p)
                        p.unlink()
                        self._json(200, {"ok": True, "deleted": True, "path": str(p)})
                        print(f"[DELETE_Q] OK: {p}", flush=True)
                        server_ref._log_action("DELETE_Q", str(p), size, "OK", "permanently deleted from quarantine")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[DELETE_Q][ERR] {p} :: {ex}", flush=True)
                        server_ref._log_action("DELETE_Q", str(p), None, "ERROR", str(ex))
                    return

                if action == "ignore_group":
                    try:
                        group_key = payload.get("group_key", "")
                        group_type = payload.get("group_type", "")
                        if not group_key or not group_type:
                            self._json(400, {"ok": False, "error": "group_key und group_type erforderlich"})
                            return
                        entry = f"{group_type}::{group_key}"
                        cfg = load_config()
                        ignored = cfg.get("ignored_groups", [])
                        if entry not in ignored:
                            ignored.append(entry)
                        cfg["ignored_groups"] = ignored
                        save_config(cfg)
                        self._json(200, {"ok": True, "ignored": True, "entry": entry})
                        print(f"[IGNORE_GROUP] {entry}", flush=True)
                        append_log(f"IGNORE_GROUP {entry}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "unignore_group":
                    try:
                        group_key = payload.get("group_key", "")
                        group_type = payload.get("group_type", "")
                        if not group_key or not group_type:
                            self._json(400, {"ok": False, "error": "group_key und group_type erforderlich"})
                            return
                        entry = f"{group_type}::{group_key}"
                        cfg = load_config()
                        ignored = cfg.get("ignored_groups", [])
                        if entry in ignored:
                            ignored.remove(entry)
                        cfg["ignored_groups"] = ignored
                        save_config(cfg)
                        self._json(200, {"ok": True, "unignored": True, "entry": entry})
                        print(f"[UNIGNORE_GROUP] {entry}", flush=True)
                        append_log(f"UNIGNORE_GROUP {entry}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "mark_tutorial_seen":
                    try:
                        app = getattr(server_ref, 'app_ref', None)
                        if app:
                            app._tutorial_seen = True
                            app._save_config_now()
                        self._json(200, {"ok": True})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "send_bug_report":
                    try:
                        import urllib.request as _urlreq
                        import platform as _plat
                        category = payload.get("category", "").strip()
                        symptoms = payload.get("symptoms", [])
                        description = payload.get("description", "").strip()

                        if not category:
                            self._json(400, {"ok": False, "error": "Bitte wähle eine Kategorie"})
                            return
                        if not symptoms and not description:
                            self._json(400, {"ok": False, "error": "Bitte wähle Symptome oder beschreibe das Problem"})
                            return

                        # Kategorie-Labels
                        cat_labels = {
                            'crash': '💥 Absturz / Einfrieren',
                            'scan': '🔍 Scan-Problem',
                            'display': '🖥️ Anzeige-Fehler',
                            'action': '⚡ Aktion funktioniert nicht',
                            'import': '📥 Import-Problem',
                            'curseforge': '🔥 CurseForge-Problem',
                            'performance': '🐢 Performance-Problem',
                            'other': '❓ Sonstiges'
                        }
                        cat_label = cat_labels.get(category, category)

                        # Symptome als Text
                        symptom_text = ', '.join(symptoms) if symptoms else 'Keine ausgewählt'

                        # Beschreibung
                        desc_text = description if description else 'Keine Beschreibung'

                        # Sammle System-Infos
                        sys_info = f"Windows {_plat.version()} | Python {_plat.python_version()} | Scanner v{SCANNER_VERSION}"

                        # GameVersion.txt auslesen
                        game_ver = "Nicht gefunden"
                        sims4_path = Path(server_ref.sims4_dir) if server_ref.sims4_dir else None
                        if sims4_path and sims4_path.exists():
                            gv_file = sims4_path / "GameVersion.txt"
                            if gv_file.exists():
                                try:
                                    game_ver = gv_file.read_text(encoding='utf-8', errors='replace').strip()[:200]
                                except Exception:
                                    game_ver = "Nicht lesbar"

                        # Sammle Scan-Daten
                        scan_summary = "Kein Scan vorhanden"
                        mod_type_stats = "Keine Daten"
                        ds = server_ref.dataset
                        if ds:
                            d = ds.to_json()
                            s = d.get('summary', {})
                            scan_summary = (
                                f"Dateien: {s.get('total_files', '?')} | "
                                f"Duplikate: Name {s.get('groups_name', 0)} / Inhalt {s.get('groups_content', 0)} / Ähnlich {s.get('groups_similar', 0)} | "
                                f"Korrupt: {s.get('corrupt_count', 0)} | Konflikte: {s.get('conflict_count', 0)}"
                            )
                            # Mod-Typ Statistik — ALLE Dateien im Mod-Ordner zählen
                            try:
                                type_counts = {}
                                if ds and ds.roots:
                                    for root in ds.roots:
                                        root_path = Path(root)
                                        if root_path.exists():
                                            for fp in root_path.rglob('*'):
                                                if fp.is_file():
                                                    ext = fp.suffix.lower()
                                                    if ext:
                                                        type_counts[ext] = type_counts.get(ext, 0) + 1
                                if type_counts:
                                    mod_type_stats = ' | '.join(f"{ext}: {cnt}" for ext, cnt in sorted(type_counts.items(), key=lambda x: -x[1]))
                            except Exception:
                                mod_type_stats = "Fehler beim Zählen"

                        # Sammle Mod-Ordner
                        mod_folders = "Keine"
                        if ds and ds.roots:
                            mod_folders = ', '.join(str(r) for r in ds.roots)

                        # ── Alle Exception-Dateien sammeln (VOLL für .txt) ──
                        import re as _re
                        all_exc_files_data = []
                        all_ui_exc_files_data = []
                        last_exc_short = "Keine lastException gefunden"
                        last_ui_exc_short = "Keine lastUIException gefunden"
                        last_exc_full = ""
                        last_ui_exc_full = ""
                        error_messages = []  # Extrahierte Fehlermeldungen
                        broken_mods = []    # Verdächtige Mods

                        if sims4_path and sims4_path.exists():
                            # ALLE lastException Dateien
                            exc_files = sorted(sims4_path.glob("lastException*.txt"),
                                               key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
                            for ef in exc_files[:5]:  # Max 5 neueste
                                try:
                                    content = ef.read_text(encoding='utf-8', errors='replace')
                                    all_exc_files_data.append((ef.name, content))
                                    # XML parsen für bessere Analyse
                                    # Fehlermeldung extrahieren
                                    desync_match = _re.search(r'<desyncdata>(.*?)</desyncdata>', content, _re.DOTALL)
                                    if desync_match:
                                        raw = desync_match.group(1).replace('&#13;&#10;', '\n').replace('&#10;', '\n').replace('&#13;', '\n')
                                        # Erste Zeile = Haupt-Fehlermeldung
                                        first_line = raw.strip().split('\n')[0][:300]
                                        if first_line and first_line not in error_messages:
                                            error_messages.append(first_line)
                                    # BetterExceptions Advice
                                    advice_match = _re.search(r'<Advice>(.*?)</Advice>', content)
                                    if advice_match:
                                        advice = advice_match.group(1).strip()
                                        if advice and advice not in error_messages:
                                            error_messages.append(f"[BE] {advice}")
                                    # Mod-Namen aus categoryid
                                    cat_match = _re.search(r'<categoryid>(.*?)</categoryid>', content)
                                    if cat_match:
                                        cat_val = cat_match.group(1).strip()
                                        if cat_val and cat_val not in ('', 'Unknown'):
                                            broken_mods.append(cat_val)
                                    # Mod-Namen aus Fehlertexten
                                    mod_hits = _re.findall(r'([a-zA-Z_]{3,}(?:mods?|interactions?|script|cheats?|overhaul)[a-zA-Z0-9_]*)', content, _re.IGNORECASE)
                                    mod_hits += _re.findall(r'(?:TypeError|Error):\s*(\w+?)[\s(]', content)
                                    for m in mod_hits:
                                        if len(m) > 5 and m.lower() not in ('module', 'import', 'error', 'false', 'string', 'version', 'typeerror', 'script'):
                                            if m not in broken_mods:
                                                broken_mods.append(m)
                                except Exception:
                                    all_exc_files_data.append((ef.name, "NICHT LESBAR"))
                            if exc_files:
                                try:
                                    c = exc_files[0].read_text(encoding='utf-8', errors='replace')
                                    last_exc_short = f"**{exc_files[0].name}**\n```\n{c[:1500]}\n```"
                                    last_exc_full = c
                                except Exception:
                                    last_exc_short = f"Datei: {exc_files[0].name} (nicht lesbar)"

                            # ALLE lastUIException Dateien
                            ui_exc_files = sorted(sims4_path.glob("lastUIException*.txt"),
                                               key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
                            for uf in ui_exc_files[:5]:
                                try:
                                    content = uf.read_text(encoding='utf-8', errors='replace')
                                    all_ui_exc_files_data.append((uf.name, content))
                                    desync_match = _re.search(r'<desyncdata>(.*?)</desyncdata>', content, _re.DOTALL)
                                    if desync_match:
                                        raw = desync_match.group(1).replace('&#13;&#10;', '\n').replace('&#10;', '\n')
                                        first_line = raw.strip().split('\n')[0][:300]
                                        if first_line and first_line not in error_messages:
                                            error_messages.append(first_line)
                                    cat_match = _re.search(r'<categoryid>(.*?)</categoryid>', content)
                                    if cat_match:
                                        cat_val = cat_match.group(1).strip()
                                        if cat_val and cat_val not in ('', 'Unknown') and cat_val not in broken_mods:
                                            broken_mods.append(cat_val)
                                except Exception:
                                    all_ui_exc_files_data.append((uf.name, "NICHT LESBAR"))
                            if ui_exc_files:
                                try:
                                    c = ui_exc_files[0].read_text(encoding='utf-8', errors='replace')
                                    last_ui_exc_short = f"**{ui_exc_files[0].name}**\n```\n{c[:1000]}\n```"
                                    last_ui_exc_full = c
                                except Exception:
                                    last_ui_exc_short = f"Datei: {ui_exc_files[0].name} (nicht lesbar)"

                        # Scanner-Log einlesen (VOLL + gekürzt)
                        scanner_log_short = "Kein Log vorhanden"
                        scanner_log_full = ""
                        if server_ref.log_file and server_ref.log_file.exists():
                            try:
                                scanner_log_full = server_ref.log_file.read_text(encoding='utf-8', errors='replace')
                                lines = scanner_log_full.splitlines()
                                scanner_log_short = '\n'.join(lines[-30:])
                            except Exception:
                                scanner_log_short = "Log nicht lesbar"

                        # Duplikat-Details für Report
                        duplicate_details = ""
                        conflict_details = ""
                        corrupt_details = ""
                        if ds:
                            d_full = ds.to_json()
                            groups = d_full.get('groups', [])
                            # Duplikate auflisten
                            dup_lines = []
                            for g in groups:
                                gtype = g.get('type', '')
                                files = g.get('files', [])
                                if len(files) > 1:
                                    dup_lines.append(f"\n--- {gtype.upper()} Gruppe ---")
                                    for fi in files:
                                        dup_lines.append(f"  {fi.get('path', '?')} ({fi.get('size_hr', '?')})")
                            duplicate_details = '\n'.join(dup_lines) if dup_lines else "Keine Duplikate"

                            # Konflikte
                            conflicts = d_full.get('conflicts', [])
                            conf_lines = []
                            for c in conflicts[:50]:  # Max 50
                                c_files = c.get('files', [])
                                res_name = c.get('resource', '?')
                                conf_lines.append(f"\n  Ressource: {res_name}")
                                for cf in c_files:
                                    conf_lines.append(f"    {cf.get('path', '?')}")
                            conflict_details = '\n'.join(conf_lines) if conf_lines else "Keine Konflikte"

                            # Korrupte Dateien
                            corrupts = d_full.get('corrupt', [])
                            if corrupts:
                                corrupt_details = '\n'.join(f"  {c.get('path', '?')} — {c.get('error', '?')}" for c in corrupts)
                            else:
                                corrupt_details = "Keine korrupten Dateien"

                        # Mod-Logs (z.B. Sims4CommunityLib Logs)
                        mod_log_data = ""
                        if sims4_path and sims4_path.exists():
                            mod_log_dir = sims4_path / "mod_logs"
                            if mod_log_dir.exists():
                                try:
                                    log_files = sorted(mod_log_dir.glob("*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
                                    for lf in log_files[:3]:
                                        try:
                                            lc = lf.read_text(encoding='utf-8', errors='replace')[-2000:]
                                            mod_log_data += f"\n\n--- {lf.name} (letzte 2000 Zeichen) ---\n{lc}"
                                        except Exception:
                                            mod_log_data += f"\n--- {lf.name}: NICHT LESBAR ---"
                                except Exception:
                                    mod_log_data = "mod_logs Ordner nicht lesbar"

                        # ── Auto-Analyse ──────────────────────────────
                        severity = "🟢 Gering"
                        hints = []
                        verdict = ""

                        has_exc = len(all_exc_files_data) > 0
                        has_ui_exc = len(all_ui_exc_files_data) > 0

                        # Deduplizierte Mod-Liste (max 10)
                        broken_mods = list(dict.fromkeys(broken_mods))[:10]

                        # Scan-Daten prüfen
                        has_corrupt = False
                        has_dupes = False
                        has_conflicts = False
                        dupe_count = 0
                        conflict_count = 0
                        corrupt_count = 0
                        if ds:
                            d2 = ds.to_json()
                            s2 = d2.get('summary', {})
                            corrupt_count = s2.get('corrupt_count', 0)
                            conflict_count = s2.get('conflict_count', 0)
                            dupe_count = s2.get('groups_name', 0) + s2.get('groups_content', 0) + s2.get('groups_similar', 0)
                            has_corrupt = corrupt_count > 0
                            has_dupes = dupe_count > 0
                            has_conflicts = conflict_count > 0

                        # Schweregrad bestimmen
                        critical_cats = ('crash', 'scan')
                        critical_symptoms = ('Absturz', 'Einfrieren', 'wird nicht gestartet', 'Scan startet nicht')
                        has_critical_symptom = any(s in symptom_text for s in critical_symptoms)

                        if category in critical_cats and (has_exc or has_critical_symptom):
                            severity = "🔴 Kritisch"
                        elif has_corrupt or (has_exc and category in critical_cats):
                            severity = "🔴 Kritisch"
                        elif has_exc or has_conflicts or category == 'performance':
                            severity = "🟡 Mittel"
                        else:
                            severity = "🟢 Gering"

                        # Hinweise sammeln
                        if has_corrupt:
                            hints.append(f"⛔ {corrupt_count} korrupte Datei(en) gefunden — echtes Problem!")
                        if has_exc and broken_mods:
                            hints.append(f"🔥 Fehlerhafte Mods/Quellen: {', '.join(broken_mods[:5])}")
                        elif has_exc:
                            hints.append("⚠️ Exception vorhanden — wahrscheinlich Mod-Konflikt")
                        if has_ui_exc:
                            hints.append("⚠️ UI-Exception vorhanden — möglicherweise UI-Mod-Problem")
                        if error_messages:
                            for em in error_messages[:3]:
                                hints.append(f"💬 {em[:200]}")
                        if has_conflicts:
                            hints.append(f"⚡ {conflict_count} Mod-Konflikte erkannt")
                        if has_dupes and dupe_count > 10:
                            hints.append(f"📦 {dupe_count} Duplikat-Gruppen — User braucht Hilfe beim Aufräumen")
                        elif has_dupes:
                            hints.append(f"📦 {dupe_count} Duplikat-Gruppen vorhanden")
                        if len(all_exc_files_data) > 1:
                            hints.append(f"📄 {len(all_exc_files_data)} Exception-Dateien gefunden (siehe .txt)")
                        if len(all_ui_exc_files_data) > 1:
                            hints.append(f"📄 {len(all_ui_exc_files_data)} UI-Exception-Dateien gefunden (siehe .txt)")
                        if not has_exc and not has_ui_exc and not has_corrupt and not has_conflicts:
                            hints.append("✅ Keine Fehler in Logs — alles sauber")
                        if len(description) < 10 and not symptoms:
                            hints.append("🤷 Sehr wenig Info vom User — evtl. verwirrt")

                        # Gesamturteil
                        if has_corrupt or (has_exc and broken_mods):
                            verdict = "🔴 **Echtes Problem** — Es gibt konkrete Fehler. Mod-Konflikte oder korrupte Dateien."
                        elif has_exc or has_ui_exc:
                            verdict = "🟡 **Wahrscheinlich echtes Problem** — Exceptions vorhanden, aber Ursache unklar."
                        elif has_conflicts and conflict_count > 20:
                            verdict = "🟡 **Mod-Chaos** — Viele Konflikte. User braucht Hilfe beim Sortieren."
                        elif not has_exc and not has_ui_exc and not has_corrupt and category == 'other':
                            verdict = "🟢 **Vermutlich User-Fehler** — Keine Fehler gefunden. User versteht vermutlich etwas nicht."
                        elif not has_exc and not has_ui_exc and not has_corrupt:
                            verdict = "🟡 **Unklar** — Keine Exceptions, aber User meldet Problem. Nachfragen empfohlen."
                        else:
                            verdict = "🟡 **Manuell prüfen** — Automatische Analyse kann Ursache nicht sicher bestimmen."

                        hints_text = '\n'.join(hints) if hints else 'Keine besonderen Auffälligkeiten'

                        # ── HTML Report-Datei ──────────────────────────────
                        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        import html as _html

                        def _h(text):
                            """HTML-escape helper"""
                            return _html.escape(str(text))

                        sev_color = '#4caf50' if severity.startswith('🟢') else ('#ff9800' if severity.startswith('🟡') else '#f44336')
                        sev_bg = '#e8f5e9' if severity.startswith('🟢') else ('#fff3e0' if severity.startswith('🟡') else '#ffebee')

                        html_parts = []
                        html_parts.append(f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>Bug Report — {_h(report_time)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:#1a1a2e;color:#e0e0e0;padding:20px;line-height:1.5}}
.container{{max-width:1100px;margin:0 auto}}
h1{{color:#ff6b6b;text-align:center;padding:20px 0;font-size:1.8em;border-bottom:2px solid #ff6b6b}}
h2{{color:#61dafb;margin:20px 0 10px;padding:10px;background:#16213e;border-radius:8px;cursor:pointer;user-select:none}}
h2:hover{{background:#1a2744}}
h2::before{{content:'▼ ';font-size:0.8em}}
.section{{background:#16213e;border-radius:8px;padding:15px;margin-bottom:15px}}
.collapsed .section{{display:none}}
.collapsed h2::before{{content:'▶ '}}
.info-grid{{display:grid;grid-template-columns:180px 1fr;gap:8px 15px;padding:10px}}
.info-label{{color:#61dafb;font-weight:600}}
.info-value{{color:#e0e0e0}}
.severity-box{{background:{sev_bg};color:{sev_color};border:2px solid {sev_color};border-radius:10px;padding:15px;text-align:center;font-size:1.3em;font-weight:700;margin:10px 0}}
.verdict-box{{background:#1e1e3a;border-left:4px solid {sev_color};padding:12px 15px;margin:10px 0;border-radius:0 8px 8px 0;font-size:1.05em}}
.hint{{padding:5px 10px;margin:3px 0;background:#1e1e3a;border-radius:5px}}
.mod-tag{{display:inline-block;background:#ff6b6b22;color:#ff6b6b;border:1px solid #ff6b6b55;padding:3px 10px;border-radius:15px;margin:3px;font-size:0.9em}}
.error-msg{{background:#2d1b1b;border-left:3px solid #ff6b6b;padding:8px 12px;margin:5px 0;border-radius:0 5px 5px 0;font-family:monospace;font-size:0.85em;word-break:break-all}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}
th{{background:#0d1b2a;color:#61dafb;padding:8px 12px;text-align:left;border-bottom:2px solid #61dafb33}}
td{{padding:6px 12px;border-bottom:1px solid #ffffff11}}
tr:hover td{{background:#ffffff08}}
.corrupt-row td{{color:#ff6b6b}}
pre{{background:#0d1117;color:#c9d1d9;padding:12px;border-radius:8px;overflow-x:auto;font-size:0.82em;max-height:400px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}}
.mod-list{{max-height:500px;overflow-y:auto}}
.mod-list table td:first-child{{max-width:600px;overflow:hidden;text-overflow:ellipsis}}
.size-col{{text-align:right;white-space:nowrap;color:#888}}
.stats-bar{{display:flex;gap:15px;flex-wrap:wrap;margin:10px 0}}
.stat-card{{background:#1e1e3a;padding:10px 18px;border-radius:8px;text-align:center;min-width:100px}}
.stat-num{{font-size:1.5em;font-weight:700;color:#61dafb}}
.stat-label{{font-size:0.8em;color:#888}}
.footer{{text-align:center;color:#666;padding:20px;font-size:0.8em;border-top:1px solid #333;margin-top:30px}}
</style>
<script>
function toggle(el){{el.parentElement.classList.toggle('collapsed')}}
</script>
</head>
<body>
<div class="container">
<h1>🐛 Bug Report — Sims 4 Duplikate Scanner</h1>
<p style="text-align:center;color:#888;margin:10px 0">Erstellt: {_h(report_time)} | Scanner v{_h(SCANNER_VERSION)}</p>
''')

                        # ── Übersicht ──
                        html_parts.append(f'''
<div><h2 onclick="toggle(this)">📋 Übersicht</h2>
<div class="section">
<div class="info-grid">
<span class="info-label">Kategorie</span><span class="info-value">{_h(cat_label)}</span>
<span class="info-label">Symptome</span><span class="info-value">{_h(symptom_text)}</span>
<span class="info-label">Beschreibung</span><span class="info-value">{_h(desc_text)}</span>
<span class="info-label">System</span><span class="info-value">{_h(sys_info)}</span>
<span class="info-label">Spielversion</span><span class="info-value">{_h(game_ver)}</span>
<span class="info-label">Mod-Ordner</span><span class="info-value">{_h(mod_folders)}</span>
<span class="info-label">Mod-Typen</span><span class="info-value">{_h(mod_type_stats)}</span>
</div>
<div class="stats-bar">
<div class="stat-card"><div class="stat-num">{s.get('total_files','?') if ds else '?'}</div><div class="stat-label">Dateien</div></div>
<div class="stat-card"><div class="stat-num">{dupe_count}</div><div class="stat-label">Duplikate</div></div>
<div class="stat-card"><div class="stat-num">{corrupt_count}</div><div class="stat-label">Korrupt</div></div>
<div class="stat-card"><div class="stat-num">{conflict_count}</div><div class="stat-label">Konflikte</div></div>
</div>
</div></div>
''')

                        # ── Auto-Analyse ──
                        hints_html = ''.join(f'<div class="hint">{_h(h)}</div>' for h in hints)
                        mods_html = ''.join(f'<span class="mod-tag">{_h(m)}</span>' for m in broken_mods) if broken_mods else '<span style="color:#888">Keine erkannt</span>'
                        errors_html = ''.join(f'<div class="error-msg">{_h(e)}</div>' for e in error_messages) if error_messages else '<span style="color:#888">Keine</span>'

                        # verdict ohne Markdown-Formatierung
                        verdict_clean = verdict.replace('**', '')

                        html_parts.append(f'''
<div><h2 onclick="toggle(this)">🤖 Auto-Analyse</h2>
<div class="section">
<div class="severity-box">{_h(severity)}</div>
<div class="verdict-box">{_h(verdict_clean)}</div>
<h3 style="color:#aaa;margin:15px 0 5px">📋 Hinweise</h3>
{hints_html}
<h3 style="color:#aaa;margin:15px 0 5px">🔥 Verdächtige Mods</h3>
{mods_html}
<h3 style="color:#aaa;margin:15px 0 5px">💬 Fehlermeldungen</h3>
{errors_html}
</div></div>
''')

                        # ── Korrupte Dateien ──
                        if has_corrupt and ds:
                            corrupts = d_full.get('corrupt', [])
                            corrupt_rows = ''.join(f'<tr class="corrupt-row"><td>{_h(c.get("path","?"))}</td><td>{_h(c.get("error","?"))}</td></tr>' for c in corrupts)
                            html_parts.append(f'''
<div><h2 onclick="toggle(this)">⛔ Korrupte Dateien ({corrupt_count})</h2>
<div class="section">
<table><tr><th>Datei</th><th>Fehler</th></tr>{corrupt_rows}</table>
</div></div>
''')

                        # ── Duplikate ──
                        if has_dupes and ds:
                            dup_html = ''
                            for g in d_full.get('groups', []):
                                files = g.get('files', [])
                                if len(files) > 1:
                                    gtype = g.get('type', '').upper()
                                    rows = ''.join(f'<tr><td>{_h(fi.get("path","?"))}</td><td class="size-col">{_h(fi.get("size_hr","?"))}</td></tr>' for fi in files)
                                    dup_html += f'<h4 style="color:#61dafb;margin:10px 0 5px">{_h(gtype)} Gruppe</h4><table><tr><th>Datei</th><th>Größe</th></tr>{rows}</table>'
                            html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📦 Duplikate ({dupe_count} Gruppen)</h2>
<div class="section">{dup_html}</div></div>
''')

                        # ── Mod-Konflikte ──
                        if has_conflicts and ds:
                            conflicts = d_full.get('conflicts', [])
                            conf_html = ''
                            for c_item in conflicts[:80]:
                                c_files = c_item.get('files', [])
                                res_name = c_item.get('resource', '?')
                                rows = ''.join(f'<tr><td>{_h(cf.get("path","?"))}</td></tr>' for cf in c_files)
                                conf_html += f'<h4 style="color:#ff9800;margin:10px 0 5px">Ressource: {_h(res_name)}</h4><table><tr><th>Datei</th></tr>{rows}</table>'
                            html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">⚡ Mod-Konflikte ({conflict_count})</h2>
<div class="section">{conf_html}</div></div>
''')

                        # ── Exceptions ──
                        for i, (fname, fcontent) in enumerate(all_exc_files_data):
                            html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">⚠️ lastException #{i+1}: {_h(fname)}</h2>
<div class="section"><pre>{_h(fcontent)}</pre></div></div>
''')
                        for i, (fname, fcontent) in enumerate(all_ui_exc_files_data):
                            html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">🖥️ lastUIException #{i+1}: {_h(fname)}</h2>
<div class="section"><pre>{_h(fcontent)}</pre></div></div>
''')

                        # ── Mod-Logs ──
                        if mod_log_data:
                            html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📋 Mod-Logs</h2>
<div class="section"><pre>{_h(mod_log_data)}</pre></div></div>
''')

                        # ── Komplette Mod-Liste ──
                        mod_list_html = ''
                        total_mod_count = 0
                        if ds and ds.roots:
                            for root in ds.roots:
                                root_path = Path(root)
                                mod_list_html += f'<h4 style="color:#61dafb;margin:10px 0 5px">📂 {_h(str(root_path))}</h4>'
                                if root_path.exists():
                                    mod_list_html += '<table><tr><th>Datei</th><th style="text-align:right">Größe</th></tr>'
                                    mod_files = sorted(root_path.rglob('*'))
                                    for mf in mod_files:
                                        if mf.is_file():
                                            total_mod_count += 1
                                            try:
                                                rel = mf.relative_to(root_path)
                                                size = mf.stat().st_size
                                                if size >= 1048576:
                                                    size_str = f"{size / 1048576:.1f} MB"
                                                elif size >= 1024:
                                                    size_str = f"{size / 1024:.1f} KB"
                                                else:
                                                    size_str = f"{size} B"
                                                mod_list_html += f'<tr><td>{_h(str(rel))}</td><td class="size-col">{size_str}</td></tr>'
                                            except Exception:
                                                mod_list_html += f'<tr><td>{_h(mf.name)}</td><td class="size-col">?</td></tr>'
                                    mod_list_html += '</table>'
                                else:
                                    mod_list_html += '<p style="color:#888">(Ordner nicht erreichbar)</p>'

                        html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📁 Alle Mods ({total_mod_count} Dateien)</h2>
<div class="section"><div class="mod-list">{mod_list_html}</div></div></div>
''')

                        # ── Scanner-Log ──
                        html_parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📋 Scanner-Log</h2>
<div class="section"><pre>{_h(scanner_log_full) if scanner_log_full else 'Kein Log vorhanden'}</pre></div></div>
''')

                        # Footer
                        html_parts.append(f'''
<div class="footer">Scanner v{_h(SCANNER_VERSION)} | Report erstellt {_h(report_time)}</div>
</div></body></html>''')

                        report_html = ''.join(html_parts)
                        report_bytes = report_html.encode('utf-8')

                        # ── Discord Embeds (Kurzübersicht) ──────────────────
                        embed1 = {
                            "title": "\U0001f41b Bug Report — Sims 4 Duplikate Scanner",
                            "color": 0xFF4444,
                            "fields": [
                                {"name": "📋 Kategorie", "value": cat_label, "inline": True},
                                {"name": "🎮 Spielversion", "value": game_ver[:200], "inline": True},
                                {"name": "🔎 Symptome", "value": symptom_text[:1024], "inline": False},
                                {"name": "📝 Beschreibung", "value": desc_text[:1024], "inline": False},
                                {"name": "💻 System", "value": sys_info, "inline": False},
                                {"name": "📊 Scan-Ergebnis", "value": scan_summary[:1024], "inline": False},
                                {"name": "📁 Mod-Typen", "value": mod_type_stats[:1024], "inline": False},
                                {"name": "📂 Mod-Ordner", "value": mod_folders[:1024], "inline": False},
                            ],
                            "footer": {"text": f"Scanner v{SCANNER_VERSION} | {report_time} | 📎 Details in .html Anhang"}
                        }
                        embed2 = {
                            "title": "🤖 Auto-Analyse",
                            "color": 0x4488FF if severity.startswith("🟢") else (0xFFAA00 if severity.startswith("🟡") else 0xFF0000),
                            "fields": [
                                {"name": "📊 Schweregrad", "value": severity, "inline": True},
                                {"name": "🏷️ Kategorie", "value": cat_label, "inline": True},
                                {"name": "🎯 Urteil", "value": verdict, "inline": False},
                                {"name": "📋 Hinweise", "value": hints_text[:1024], "inline": False},
                            ]
                        }
                        if broken_mods:
                            embed2["fields"].append({"name": "🔥 Verdächtige Mods", "value": ', '.join(broken_mods[:5])[:1024], "inline": False})
                        if error_messages:
                            err_preview = '\n'.join(f"• {e[:150]}" for e in error_messages[:3])
                            embed2["fields"].append({"name": "💬 Fehlermeldungen", "value": err_preview[:1024], "inline": False})

                        # ── Multipart senden (Embeds + .txt Datei) ──────────
                        import uuid as _uuid
                        boundary = f"----BugReport{_uuid.uuid4().hex}"
                        body_parts = []

                        # payload_json Part
                        webhook_payload = {
                            "embeds": [embed1, embed2],
                            "username": "Sims4 Scanner Bug Bot"
                        }
                        body_parts.append(f'--{boundary}\r\n')
                        body_parts.append('Content-Disposition: form-data; name="payload_json"\r\n')
                        body_parts.append('Content-Type: application/json\r\n\r\n')
                        body_parts.append(json.dumps(webhook_payload))
                        body_parts.append('\r\n')

                        # File Part
                        report_filename = f"bugreport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        body_parts.append(f'--{boundary}\r\n')
                        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{report_filename}"\r\n')
                        body_parts.append('Content-Type: text/html; charset=utf-8\r\n\r\n')

                        body_bytes = ''.join(body_parts).encode('utf-8') + report_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

                        req = _urlreq.Request(
                            DISCORD_WEBHOOK_URL,
                            data=body_bytes,
                            headers={
                                'Content-Type': f'multipart/form-data; boundary={boundary}',
                                'User-Agent': 'Sims4Scanner'
                            },
                            method='POST'
                        )
                        _urlreq.urlopen(req, timeout=15)
                        self._json(200, {"ok": True})
                        print(f"[BUG_REPORT] Sent to Discord with .txt — {cat_label} ({len(report_bytes)} bytes)", flush=True)
                        append_log(f"BUG_REPORT sent ({category}, {len(report_bytes)} bytes)")
                    except Exception as ex:
                        print(f"[BUG_REPORT] Error: {ex}", flush=True)
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                self._json(404, {"ok": False, "error": "unknown action"})
                print(f"[UNKNOWN_ACTION] {action} -> {p}", flush=True)
                append_log(f"UNKNOWN_ACTION {action} {p}")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        # File-Watcher starten
        self._start_watcher()

    def stop(self):
        try:
            if self._watcher:
                self._watcher.stop()
                self._watcher = None
        except Exception:
            pass
        try:
            if self.httpd:
                self.httpd.shutdown()
                self._append_log("SERVER STOP")
        except Exception:
            pass

    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def _build_html_page(self) -> str:
        html = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sims4 Duplicate Scanner – Web UI</title>
<style>
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#0f1115; color:#e7e7e7; margin:16px; }
  h1 { margin:0 0 8px 0; }
  .muted { color:#b6b6b6; }
  .box { background:#151926; border:1px solid #232a3a; border-radius:14px; padding:14px; margin:12px 0; }
  code { color:#d7d7ff; }
  .topgrid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
  @media (max-width: 900px) { .topgrid { grid-template-columns: 1fr; } }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; background:#232a3a; margin-left:8px; font-size:12px; }
  .search { width:100%; padding:10px 12px; border-radius:10px; border:1px solid #232a3a; background:#0f1422; color:#e7e7e7; }
  details.grp { border:1px solid #232a3a; border-radius:14px; padding:10px 12px; margin:10px 0; }
  details.grp.color-0 { background:#141a28; border-left:4px solid #4a7fff; }
  details.grp.color-1 { background:#1a1428; border-left:4px solid #a855f7; }
  details.grp.color-2 { background:#14281a; border-left:4px solid #22c55e; }
  details.grp.color-3 { background:#281a14; border-left:4px solid #f97316; }
  details.grp.color-4 { background:#28141a; border-left:4px solid #ef4444; }
  details.grp.color-5 { background:#142828; border-left:4px solid #06b6d4; }
  details.grp.grp-ignored { opacity:0.55; }
  details.grp.grp-ignored > summary { font-style:italic; }
  #import-dropzone:hover { border-color:#2563eb !important; background:#1e293b !important; }
  #import-dropzone.drag-active { border-color:#22c55e !important; background:#0f2a1a !important; }
  summary { cursor:pointer; }
  summary::-webkit-details-marker { display:none; }
  .files { margin-top:10px; display:flex; flex-direction:column; gap:10px; }
  .file { background:#0f1422; border:1px solid #1f2738; border-radius:12px; padding:10px; }
  .row1 { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .tag { display:inline-block; padding:2px 8px; border-radius:999px; background:#2d3a55; font-size:12px; }
  .size { color:#cfd6ff; font-size:12px; }
  .date { color:#a8ffcf; font-size:12px; }
  .btn { border:1px solid #2a3350; background:#11182b; color:#e7e7e7; padding:6px 10px; border-radius:10px; cursor:pointer; font-size:13px; }
  .btn:hover { filter:brightness(1.1); }
  .btn-danger { border-color:#6b2b2b; background:#2b1111; }
  .btn-ok { border-color:#2b6b3b; background:#112b1a; }
  .btn-ghost { border-color:#2a3350; background:transparent; }
  .flex { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .hr { height:1px; background:#232a3a; margin:10px 0; }
  .notice { background:#1a2238; border:1px solid #2b3553; padding:10px; border-radius:12px; }
  .subhead { margin-top:8px; padding:8px 10px; border-radius:10px; background:#101729; border:1px dashed #2a3350; color:#cfd6ff; }
  .pathline { word-break: break-all; }
  .small { font-size:12px; }
  #last { padding:10px 12px; border-radius:12px; background:#101729; border:1px solid #232a3a; }
  #log { width:100%; min-height:120px; max-height:260px; overflow:auto; padding:10px; border-radius:12px; background:#0f1422; border:1px solid #232a3a; color:#e7e7e7; white-space:pre; }
  #batchbar { position:sticky; top:50px; z-index:5; }
  #section-nav { position:sticky; top:0; z-index:10; background:#0f172a; border-bottom:1px solid #334155; padding:6px 16px; display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin:0 -20px; padding-left:20px; padding-right:20px; }
  #section-nav .nav-btn { background:#1e293b; border:1px solid #334155; color:#94a3b8; padding:4px 12px; border-radius:6px; font-size:12px; cursor:pointer; transition:all 0.15s; display:inline-flex; align-items:center; gap:4px; white-space:nowrap; }
  #section-nav .nav-btn:hover { background:#334155; color:#e2e8f0; border-color:#4b5563; }
  #section-nav .nav-btn .nav-badge { background:#6366f1; color:#fff; font-size:10px; padding:1px 6px; border-radius:10px; font-weight:bold; min-width:14px; text-align:center; }
  #section-nav .nav-btn.nav-hidden { display:none; }
  #section-nav .nav-label { color:#64748b; font-size:11px; font-weight:bold; margin-right:4px; }
  .help-toggle { background:#1e293b; border:1px solid #334155; color:#94a3b8; padding:6px 14px; border-radius:8px; cursor:pointer; font-size:13px; transition:all 0.2s; }
  .help-toggle:hover { background:#334155; color:#e2e8f0; }
  .help-panel { display:none; background:#0f172a; border:1px solid #334155; border-radius:12px; padding:20px; margin-top:10px; }
  .help-panel.open { display:block; }
  .help-step { display:flex; gap:12px; margin-bottom:14px; align-items:flex-start; }
  .help-num { background:#6366f1; color:#fff; min-width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:13px; flex-shrink:0; }
  .help-text { color:#cbd5e1; font-size:13px; line-height:1.5; }
  .help-text b { color:#e2e8f0; }
  .legend-grid { display:grid; grid-template-columns:auto 1fr; gap:6px 14px; font-size:12px; margin-top:10px; }
  .legend-icon { text-align:center; min-width:80px; }
  .info-hint { background:#172554; border:1px solid #1e40af; border-radius:8px; padding:10px 14px; margin-bottom:12px; font-size:12px; color:#93c5fd; }

  /* ---- Tutorial Overlay ---- */
  #tutorial-overlay { display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(4px); justify-content:center; align-items:center; }
  #tutorial-overlay.active { display:flex; }
  #tutorial-card { background:linear-gradient(145deg,#0f172a,#1e1b4b); border:1px solid #4f46e5; border-radius:20px; padding:36px 40px 28px; max-width:600px; width:92vw; box-shadow:0 20px 60px rgba(0,0,0,0.6); position:relative; animation:tutorialIn 0.35s ease-out; }
  @keyframes tutorialIn { from { opacity:0; transform:translateY(30px) scale(0.95); } to { opacity:1; transform:translateY(0) scale(1); } }
  #tutorial-card .tut-header { text-align:center; margin-bottom:20px; }
  #tutorial-card .tut-icon { font-size:48px; margin-bottom:8px; display:block; }
  #tutorial-card .tut-title { font-size:22px; font-weight:bold; color:#e2e8f0; margin-bottom:4px; }
  #tutorial-card .tut-body { color:#cbd5e1; font-size:14px; line-height:1.7; min-height:100px; }
  #tutorial-card .tut-body b { color:#a5b4fc; }
  #tutorial-card .tut-body ul { margin:8px 0 0 18px; padding:0; }
  #tutorial-card .tut-body li { margin-bottom:4px; }
  .tut-footer { display:flex; justify-content:space-between; align-items:center; margin-top:24px; gap:12px; flex-wrap:wrap; }
  .tut-dots { display:flex; gap:6px; justify-content:center; flex:1; }
  .tut-dot { width:10px; height:10px; border-radius:50%; background:#334155; transition:all 0.2s; cursor:pointer; }
  .tut-dot.active { background:#6366f1; transform:scale(1.3); }
  .tut-dot.done { background:#4f46e5; }
  .tut-btn { border:1px solid #4f46e5; background:#1e1b4b; color:#c7d2fe; padding:8px 20px; border-radius:10px; cursor:pointer; font-size:13px; transition:all 0.15s; white-space:nowrap; }
  .tut-btn:hover { background:#312e81; color:#e0e7ff; }
  .tut-btn-primary { background:#6366f1; color:#fff; border-color:#6366f1; font-weight:bold; }
  .tut-btn-primary:hover { background:#818cf8; }
  .tut-btn-skip { background:transparent; border-color:#334155; color:#64748b; font-size:12px; }
  .tut-btn-skip:hover { color:#94a3b8; border-color:#475569; }
  .tut-check { display:flex; align-items:center; gap:8px; margin-top:16px; justify-content:center; }
  .tut-check label { color:#64748b; font-size:12px; cursor:pointer; }
  .tut-check input { accent-color:#6366f1; }

  /* Plumbob CSS Animation */
  .plumbob-container { position:relative; width:54px; height:70px; margin:0 auto 12px; }
  .plumbob { width:54px; height:70px; animation: plumbobFloat 3s ease-in-out infinite, plumbobGlow 2s ease-in-out infinite alternate; filter: drop-shadow(0 0 12px rgba(99,230,130,0.5)); }
  @keyframes plumbobFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    25% { transform: translateY(-8px) rotate(2deg); }
    50% { transform: translateY(-4px) rotate(0deg); }
    75% { transform: translateY(-10px) rotate(-2deg); }
  }
  @keyframes plumbobGlow {
    0% { filter: drop-shadow(0 0 8px rgba(99,230,130,0.3)); }
    100% { filter: drop-shadow(0 0 20px rgba(99,230,130,0.7)); }
  }
  .nav-btn-tutorial { background:linear-gradient(135deg,#312e81,#1e1b4b) !important; border-color:#6366f1 !important; color:#c7d2fe !important; }
  .nav-btn-tutorial:hover { background:linear-gradient(135deg,#3730a3,#312e81) !important; color:#e0e7ff !important; }
  .nav-btn-bug { background:linear-gradient(135deg,#7f1d1d,#1e1b4b) !important; border-color:#dc2626 !important; color:#fca5a5 !important; }
  .nav-btn-bug:hover { background:linear-gradient(135deg,#991b1b,#312e81) !important; color:#fecaca !important; }

  /* Bug Report Modal */
  #bugreport-overlay { display:none; position:fixed; inset:0; z-index:10000; background:rgba(0,0,0,0.75); backdrop-filter:blur(4px); justify-content:center; align-items:center; }
  #bugreport-overlay.active { display:flex; }
  #bugreport-card { background:linear-gradient(145deg,#0f172a,#1c1017); border:1px solid #dc2626; border-radius:20px; padding:32px 36px 24px; max-width:620px; width:94vw; box-shadow:0 20px 60px rgba(0,0,0,0.6); animation:tutorialIn 0.35s ease-out; max-height:90vh; overflow-y:auto; }
  #bugreport-card h2 { margin:0 0 6px; font-size:20px; color:#fca5a5; }
  #bugreport-card .bug-sub { color:#94a3b8; font-size:13px; margin-bottom:16px; }
  #bugreport-card textarea { width:100%; min-height:80px; background:#0f1422; border:1px solid #334155; border-radius:10px; color:#e7e7e7; padding:12px; font-size:13px; resize:vertical; font-family:inherit; }
  #bugreport-card textarea:focus { outline:none; border-color:#dc2626; }
  #bugreport-card .bug-info { background:#172554; border:1px solid #1e40af; border-radius:8px; padding:10px 14px; margin:12px 0; font-size:12px; color:#93c5fd; }
  #bugreport-card .bug-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:16px; }
  #bugreport-card .bug-status { margin-top:12px; padding:10px; border-radius:8px; font-size:13px; display:none; }
  #bugreport-card .bug-status.success { display:block; background:#052e16; border:1px solid #16a34a; color:#86efac; }
  #bugreport-card .bug-status.error { display:block; background:#2b1111; border:1px solid #dc2626; color:#fca5a5; }
  #bugreport-card label { color:#cbd5e1; font-size:13px; font-weight:bold; display:block; margin-bottom:4px; }
  #bugreport-card select { width:100%; background:#0f1422; border:1px solid #334155; border-radius:10px; color:#e7e7e7; padding:10px 12px; font-size:13px; font-family:inherit; appearance:auto; }
  #bugreport-card select:focus { outline:none; border-color:#dc2626; }
  .bug-field { margin-bottom:14px; }
  .bug-checks { display:grid; grid-template-columns:1fr 1fr; gap:6px 16px; margin-top:6px; }
  .bug-checks label { font-weight:normal; display:flex; align-items:center; gap:6px; cursor:pointer; font-size:12px; color:#94a3b8; }
  .bug-checks input { accent-color:#dc2626; }

  #back-to-top { position:fixed; bottom:24px; right:24px; z-index:99; background:#6366f1; color:#fff; border:none; border-radius:50%; width:44px; height:44px; font-size:20px; cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.4); transition:opacity 0.2s, transform 0.2s; opacity:0; pointer-events:none; transform:translateY(10px); }
  #back-to-top.visible { opacity:1; pointer-events:auto; transform:translateY(0); }
  #back-to-top:hover { background:#818cf8; transform:translateY(-2px); }
  @keyframes pulse { 0% { margin-left:0; } 100% { margin-left:70%; } }
  .selbox { transform: scale(1.15); margin-right:8px; }
  .busy { opacity:0.65; pointer-events:none; }
  .err-card { border-radius:12px; padding:12px; margin:8px 0; }
  .err-card.hoch { background:#2b1111; border:1px solid #6b2b2b; border-left:4px solid #ef4444; }
  .err-card.mittel { background:#2b2211; border:1px solid #6b5b2b; border-left:4px solid #f59e0b; }
  .err-card.niedrig { background:#112b1a; border:1px solid #2b6b3b; border-left:4px solid #22c55e; }
  .err-card.unbekannt { background:#151926; border:1px solid #232a3a; border-left:4px solid #64748b; }
  .err-title { font-weight:bold; font-size:15px; }
  .err-schwere { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; text-transform:uppercase; }
  .err-schwere.hoch { background:#7f1d1d; color:#fca5a5; }
  .err-schwere.mittel { background:#78350f; color:#fde68a; }
  .err-schwere.niedrig { background:#14532d; color:#86efac; }
  .err-schwere.unbekannt { background:#334155; color:#cbd5e1; }
  .err-explain { margin:6px 0; color:#d1d5db; }
  .corrupt-card { border-radius:10px; padding:10px 14px; margin:6px 0; background:#2b1111; border:1px solid #6b2b2b; border-left:4px solid #ef4444; display:flex; justify-content:space-between; align-items:center; }
  .corrupt-card.warn { background:#2b2211; border-color:#6b5b2b; border-left-color:#f59e0b; }
  .corrupt-status { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; }
  .corrupt-status.empty { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.too_small { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.no_dbpf { background:#7f1d1d; color:#fca5a5; }
  .corrupt-status.wrong_version { background:#78350f; color:#fde68a; }
  .corrupt-status.unreadable { background:#334155; color:#cbd5e1; }
  .conflict-card { border-radius:10px; padding:12px 14px; margin:8px 0; background:#1a1a2e; border:1px solid #3a3a5e; border-left:4px solid #8b5cf6; }
  .conflict-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#4c1d95; color:#c4b5fd; }
  .conflict-types { margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; }
  .conflict-type-pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; background:#1e293b; color:#94a3b8; }
  .addon-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#065f46; color:#6ee7b7; }
  .addon-ok { display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:bold; background:#14532d; color:#86efac; }
  .err-solution { margin:6px 0; padding:8px 10px; background:#0f1422; border-radius:8px; border-left:3px solid #4a7fff; }
  .err-meta { display:flex; gap:12px; flex-wrap:wrap; font-size:12px; color:#9ca3af; margin-top:6px; }
  .err-mods { margin-top:6px; }
  .err-mod-tag { display:inline-block; padding:1px 8px; border-radius:6px; background:#1e293b; color:#93c5fd; font-size:11px; margin:2px; }
  .err-raw { margin-top:8px; }
  .err-raw summary { cursor:pointer; color:#6b7280; font-size:12px; }
  .err-raw pre { font-size:11px; color:#9ca3af; white-space:pre-wrap; word-break:break-all; max-height:200px; overflow:auto; background:#0a0e17; padding:8px; border-radius:8px; margin-top:4px; }

  /* Status-Badges NEU/BEKANNT */
  .err-status { display:inline-block; padding:1px 8px; border-radius:999px; font-size:10px; font-weight:bold; text-transform:uppercase; margin-left:8px; }
  .err-status.neu { background:#1e3a5f; color:#60a5fa; }
  .err-status.bekannt { background:#334155; color:#94a3b8; }

  /* History-Tabelle */
  .hist-table { width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }
  .hist-table th { text-align:left; padding:8px 10px; border-bottom:2px solid #334155; color:#94a3b8; font-weight:600; }
  .hist-table td { padding:6px 10px; border-bottom:1px solid #1e293b; }
  .hist-table tr:hover { background:#111827; }

  /* Mod-Inventar Stats */
  .mod-stats { display:flex; gap:16px; flex-wrap:wrap; margin:8px 0; }
  .mod-stat { padding:10px 16px; border-radius:10px; background:#111827; border:1px solid #1e293b; text-align:center; min-width:120px; }
  .mod-stat .val { font-size:22px; font-weight:bold; color:#e2e8f0; }
  .mod-stat .lbl { font-size:11px; color:#94a3b8; margin-top:2px; }

  /* Änderungs-Tags */
  .change-tag { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11px; margin:2px; }
  .change-tag.neu { background:#14532d; color:#86efac; }
  .change-tag.entfernt { background:#7f1d1d; color:#fca5a5; }
  .change-tag.geaendert { background:#78350f; color:#fde68a; }

  /* Per-File Ansicht */
  .view-toggle { display:flex; gap:4px; background:#151926; border-radius:10px; padding:3px; border:1px solid #232a3a; }
  .view-toggle button { padding:6px 14px; border-radius:8px; border:none; background:transparent; color:#b6b6b6; cursor:pointer; font-size:13px; font-weight:600; transition:all 0.15s; }
  .view-toggle button.active { background:#2d3a55; color:#e7e7e7; }
  .view-toggle button:hover:not(.active) { color:#e7e7e7; }
  .pf-card { background:#151926; border:1px solid #232a3a; border-radius:14px; padding:14px; margin:10px 0; }
  .pf-card .pf-header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
  .pf-card .pf-name { font-weight:bold; font-size:15px; word-break:break-all; }
  .pf-card .pf-meta { display:flex; gap:8px; flex-wrap:wrap; align-items:center; font-size:12px; }
  .pf-section { margin-top:10px; padding:10px 12px; border-radius:10px; border-left:4px solid; }
  .pf-section.pf-name-dupe { background:#141a28; border-color:#4a7fff; }
  .pf-section.pf-content-dupe { background:#1a1428; border-color:#a855f7; }
  .pf-section.pf-similar-dupe { background:#142828; border-color:#06b6d4; }
  .pf-section.pf-corrupt { background:#2b1111; border-color:#ef4444; }
  .pf-section.pf-addon { background:#0f2922; border-color:#22c55e; }
  .pf-section.pf-conflict { background:#1a1a2e; border-color:#8b5cf6; }
  .pf-section-title { font-weight:bold; font-size:13px; margin-bottom:6px; }
  .pf-partner { font-size:12px; color:#94a3b8; margin:2px 0; }
  .pf-partner code { font-size:11px; }
  #perfile-view { display:none; }

  /* Mod-Notizen */
  .note-area { margin-top:8px; }
  .note-display { display:flex; align-items:flex-start; gap:8px; padding:6px 10px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; font-size:12px; color:#fde68a; cursor:pointer; }
  .note-display:hover { background:#111827; }
  .note-input { width:100%; padding:8px 10px; background:#0f1115; border:1px solid #334155; border-radius:8px; color:#e7e7e7; font-size:12px; resize:vertical; min-height:36px; box-sizing:border-box; font-family:inherit; }
  .note-btn { font-size:11px; padding:3px 10px; border-radius:6px; cursor:pointer; border:1px solid #334155; background:#1e293b; color:#94a3b8; }
  .note-btn:hover { background:#334155; color:#e2e8f0; }
  .note-btn-save { background:#112b1a; border-color:#2b6b3b; color:#86efac; }

  /* Mod-Tags */
  .mod-tags-area { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; align-items:center; }
  .mod-tag-pill { display:inline-flex; align-items:center; gap:3px; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; cursor:default; }
  .mod-tag-pill .tag-remove { cursor:pointer; opacity:0.6; margin-left:2px; font-size:10px; }
  .mod-tag-pill .tag-remove:hover { opacity:1; }
  .tag-add-btn { display:inline-flex; align-items:center; padding:2px 6px; border-radius:999px; font-size:11px; background:#1e293b; border:1px dashed #334155; color:#94a3b8; cursor:pointer; }
  .tag-add-btn:hover { background:#334155; color:#e2e8f0; }
  .tag-menu { position:absolute; background:#1e293b; border:1px solid #334155; border-radius:8px; padding:6px; z-index:20; display:flex; flex-wrap:wrap; gap:4px; max-width:260px; box-shadow:0 8px 24px rgba(0,0,0,0.4); }
  .tag-menu-item { padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; cursor:pointer; border:none; }
  .tag-menu-item:hover { filter:brightness(1.3); }

  /* Verlaufs-Diagramm */
  .chart-container { position:relative; width:100%; height:220px; margin-top:12px; background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:12px; box-sizing:border-box; }
  .chart-container canvas { width:100% !important; height:100% !important; }

  /* Dashboard / Ampel */
  .dashboard { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin:12px 0; }
  .dash-card { border-radius:14px; padding:16px; border:1px solid; cursor:pointer; transition:all 0.2s; position:relative; overflow:hidden; }
  .dash-card:hover { transform:translateY(-2px); filter:brightness(1.15); }
  .dash-card .dash-icon { font-size:28px; margin-bottom:6px; }
  .dash-card .dash-count { font-size:32px; font-weight:800; margin-bottom:2px; }
  .dash-card .dash-label { font-size:14px; font-weight:600; margin-bottom:4px; }
  .dash-card .dash-desc { font-size:12px; opacity:0.8; line-height:1.4; }
  .dash-card .dash-action { display:inline-block; margin-top:8px; padding:4px 12px; border-radius:6px; font-size:11px; font-weight:600; background:rgba(255,255,255,0.1); }
  .dash-card.dash-critical { background:linear-gradient(135deg,#1a0505,#2b1111); border-color:#6b2b2b; }
  .dash-card.dash-critical .dash-count { color:#f87171; }
  .dash-card.dash-warn { background:linear-gradient(135deg,#1a1005,#2b2211); border-color:#6b5b2b; }
  .dash-card.dash-warn .dash-count { color:#fbbf24; }
  .dash-card.dash-info { background:linear-gradient(135deg,#050d1a,#111a2b); border-color:#2b3a6b; }
  .dash-card.dash-info .dash-count { color:#60a5fa; }
  .dash-card.dash-ok { background:linear-gradient(135deg,#051a0d,#112b1a); border-color:#2b6b3b; }
  .dash-card.dash-ok .dash-count { color:#4ade80; }
  .dash-card.dash-hidden { display:none; }
  .dash-header { margin:16px 0 8px; }
  .dash-header h2 { margin:0 0 4px; font-size:20px; }
  .dash-header p { margin:0; }
  #section-nav .nav-sep { width:1px; height:20px; background:#334155; margin:0 4px; flex-shrink:0; }

  /* ---- Lightbox / Bildvorschau ---- */
  #lightbox-overlay {
    display:none; position:fixed; inset:0; z-index:10000;
    background:rgba(0,0,0,0.92); backdrop-filter:blur(8px);
    justify-content:center; align-items:center; cursor:zoom-out;
    flex-direction:column; padding:20px;
  }
  #lightbox-overlay.active { display:flex; }
  #lightbox-overlay .lb-single {
    max-width:90vw; max-height:90vh; border-radius:12px;
    border:2px solid #475569; box-shadow:0 0 60px rgba(0,0,0,0.7);
    object-fit:contain; cursor:default;
    animation: lbFadeIn 0.2s ease;
  }
  @keyframes lbFadeIn { from{opacity:0;transform:scale(0.85)} to{opacity:1;transform:scale(1)} }
  #lightbox-close {
    position:fixed; top:18px; right:24px; z-index:10001;
    font-size:32px; color:#fff; background:rgba(0,0,0,0.5); border:none;
    border-radius:50%; width:44px; height:44px; cursor:pointer;
    display:none; align-items:center; justify-content:center; line-height:1;
  }
  #lightbox-close:hover { background:rgba(255,255,255,0.15); }
  #lightbox-overlay.active ~ #lightbox-close { display:flex; }
  .thumb-clickable { cursor:zoom-in; transition:transform 0.15s, box-shadow 0.15s; }
  .thumb-clickable:hover { transform:scale(1.12); box-shadow:0 0 12px rgba(96,165,250,0.5); }

  /* Gallery / Vergleichsansicht */
  #lightbox-overlay .lb-gallery {
    display:flex; flex-wrap:wrap; gap:18px; justify-content:center;
    align-items:flex-start; max-width:95vw; max-height:88vh;
    overflow-y:auto; padding:10px; cursor:default;
  }
  #lightbox-overlay .lb-gallery::-webkit-scrollbar { width:6px; }
  #lightbox-overlay .lb-gallery::-webkit-scrollbar-thumb { background:#475569; border-radius:3px; }
  .lb-gallery-card {
    background:#1e293b; border:2px solid #334155; border-radius:12px;
    padding:12px; text-align:center; min-width:180px; max-width:320px;
    flex:1 1 220px; animation: lbFadeIn 0.25s ease;
    transition: border-color 0.2s;
  }
  .lb-gallery-card:hover { border-color:#60a5fa; }
  .lb-gallery-card img {
    max-width:280px; max-height:280px; border-radius:8px;
    object-fit:contain; background:#0f172a;
    border:1px solid #475569; margin-bottom:8px;
  }
  .lb-gallery-card .lb-label {
    color:#e2e8f0; font-size:12px; word-break:break-all;
    margin-top:6px; line-height:1.3;
  }
  .lb-gallery-card .lb-meta {
    color:#94a3b8; font-size:11px; margin-top:4px;
  }
  .lb-gallery-title {
    color:#e2e8f0; font-size:18px; font-weight:600;
    margin-bottom:12px; text-align:center; width:100%;
  }
  .lb-gallery-hint {
    color:#64748b; font-size:12px; text-align:center;
    width:100%; margin-top:8px;
  }
</style>
</head>
<body>
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px;">
  <div>
    <h1 style="margin:0;">🎮 Sims 4 Mod-Scanner</h1>
    <p class="muted" style="margin:4px 0 0;">Dein Werkzeug zum Aufräumen — findet Duplikate, Konflikte, kaputte Dateien &amp; mehr.</p>
  </div>
</div>

<!-- Dashboard -->
<div class="dash-header" id="dash-header">
  <h2>📋 Auf einen Blick</h2>
  <p class="muted small">Das hat der Scanner bei deinen Mods gefunden. Klicke auf eine Karte um direkt dorthin zu springen.</p>
</div>
<div class="dashboard" id="dashboard">
  <div class="dash-card dash-critical dash-hidden" id="dash-corrupt" onclick="document.getElementById('corrupt-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">💀</div>
    <div class="dash-count" id="dash-corrupt-count">0</div>
    <div class="dash-label">Korrupte Dateien</div>
    <div class="dash-desc">Beschädigte .package-Dateien die Fehler im Spiel verursachen. <b>Sofort entfernen!</b></div>
    <span class="dash-action">Jetzt anschauen →</span>
  </div>
  <div class="dash-card dash-warn" id="dash-dupes" onclick="document.getElementById('view-header').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">📂</div>
    <div class="dash-count" id="dash-dupes-count">0</div>
    <div class="dash-label">Duplikate</div>
    <div class="dash-desc">Doppelte oder sehr ähnliche Mod-Dateien. Aufräumen spart Speicher &amp; verhindert Probleme.</div>
    <span class="dash-action">Aufräumen →</span>
  </div>
  <div class="dash-card dash-warn dash-hidden" id="dash-conflicts" onclick="document.getElementById('conflict-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">⚔️</div>
    <div class="dash-count" id="dash-conflicts-count">0</div>
    <div class="dash-label">Konflikte</div>
    <div class="dash-desc">Mods die sich gegenseitig überschreiben — nur einer kann funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-outdated" onclick="document.getElementById('outdated-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">⏰</div>
    <div class="dash-count" id="dash-outdated-count">0</div>
    <div class="dash-label">Veraltete Mods</div>
    <div class="dash-desc">Vor dem letzten Spiel-Patch erstellt — könnten nicht mehr funktionieren.</div>
    <span class="dash-action">Prüfen →</span>
  </div>
  <div class="dash-card dash-ok dash-hidden" id="dash-addons" onclick="document.getElementById('addon-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">🧩</div>
    <div class="dash-count" id="dash-addons-count">0</div>
    <div class="dash-label">Addons erkannt</div>
    <div class="dash-desc">Erweiterungen die zusammengehören — <b>kein Handlungsbedarf!</b></div>
    <span class="dash-action">Details →</span>
  </div>
  <div class="dash-card dash-info dash-hidden" id="dash-nonmod" onclick="document.getElementById('nonmod-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">📄</div>
    <div class="dash-count" id="dash-nonmod-count">0</div>
    <div class="dash-label">Sonstige Dateien</div>
    <div class="dash-desc">Nicht-Mod-Dateien (txt, png, html…) im Mods-Ordner — können aufgeräumt werden.</div>
    <span class="dash-action">Anzeigen →</span>
  </div>
  <div class="dash-card dash-ok" id="dash-total" onclick="document.getElementById('stats-section').scrollIntoView({behavior:'smooth'})">
    <div class="dash-icon">📦</div>
    <div class="dash-count" id="dash-total-count">…</div>
    <div class="dash-label">Mods gescannt</div>
    <div class="dash-desc">Deine gesamte Mod-Sammlung wurde analysiert.</div>
    <span class="dash-action">Statistik →</span>
  </div>
</div>

<div class="box" style="margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:15px;font-weight:bold;">📖 Erste Schritte — So funktioniert der Scanner</span>
    <button class="help-toggle" id="help-toggle" onclick="document.getElementById('help-panel').classList.toggle('open'); this.textContent = document.getElementById('help-panel').classList.contains('open') ? '▲ Hilfe zuklappen' : '▼ Hilfe aufklappen';">▲ Hilfe zuklappen</button>
  </div>
  <div class="help-panel open" id="help-panel">
    <div style="margin-bottom:16px;">
      <p class="muted" style="margin:0 0 10px;"><b>Keine Sorge, es ist einfacher als es aussieht!</b> Hier die wichtigsten Schritte:</p>
      <div class="help-step">
        <span class="help-num">1</span>
        <div class="help-text">Der Scanner hat deine Mods bereits gescannt. Scrolle nach unten zu <b>"Duplikat-Gruppen"</b> — dort siehst du welche Dateien doppelt oder ähnlich sind.</div>
      </div>
      <div class="help-step">
        <span class="help-num">2</span>
        <div class="help-text">Jede Gruppe zeigt dir zusammengehörige Dateien. Setze ein <b>Häkchen ☑️</b> bei den Dateien, die du <b>nicht mehr brauchst</b> (z.B. die ältere Version oder das Duplikat).</div>
      </div>
      <div class="help-step">
        <span class="help-num">3</span>
        <div class="help-text">Klicke oben auf <b>📦 Markierte in Quarantäne</b>. Die Dateien werden in einen sicheren Ordner verschoben — <b>nichts wird gelöscht!</b> Du kannst sie jederzeit wiederherstellen.</div>
      </div>
      <div class="help-step">
        <span class="help-num">4</span>
        <div class="help-text">Starte das Spiel und teste ob alles funktioniert. Wenn ja, kannst du die Quarantäne-Dateien später endgültig löschen. Wenn nicht, einfach zurückverschieben.</div>
      </div>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🎨 Was bedeuten die Farben und Icons?</p>
    <div class="legend-grid">
      <span class="legend-icon"><span class="pill" style="background:#4c1d95;color:#c4b5fd;">📦 Inhalt-Duplikat</span></span>
      <span class="muted"><b>Dateien sind zu 100% identisch</b> — eine davon ist überflüssig und kann sicher entfernt werden.</span>
      <span class="legend-icon"><span class="pill" style="background:#1e3a5f;color:#60a5fa;">📛 Name-Duplikat</span></span>
      <span class="muted">Gleicher Dateiname in verschiedenen Ordnern — <b>Inhalt prüfen!</b> Könnte unterschiedlich sein.</span>
      <span class="legend-icon"><span class="pill" style="background:#134e4a;color:#5eead4;">🔤 Ähnlicher Name</span></span>
      <span class="muted">Sehr ähnliche Dateinamen — wahrscheinlich verschiedene <b>Versionen</b> desselben Mods. Die ältere entfernen!</span>
      <span class="legend-icon">💀 Korrupt</span>
      <span class="muted">Datei ist <b>beschädigt</b> oder leer — verursacht Fehler im Spiel. Bitte löschen oder neu herunterladen!</span>
      <span class="legend-icon">🔀 Konflikt</span>
      <span class="muted">Zwei Mods überschreiben sich gegenseitig — <b>nur einer funktioniert</b>. Behalte den neueren.</span>
      <span class="legend-icon">🧩 Addon</span>
      <span class="muted"><b>Kein Problem!</b> Dieser Mod ist eine Erweiterung für einen anderen — beide behalten.</span>
      <span class="legend-icon">⏰ Veraltet</span>
      <span class="muted">Mod wurde <b>vor dem letzten Spiel-Update</b> erstellt — könnte nicht mehr funktionieren.</span>
    </div>

    <div class="hr"></div>
    <p style="font-weight:bold;font-size:13px;margin:12px 0 8px;color:#e2e8f0;">🛡️ Sicherheits-Tipps</p>
    <div class="muted" style="font-size:12px;line-height:1.6;">
      ✅ Immer zuerst <b>Quarantäne</b> nutzen statt direkt zu löschen<br>
      ✅ Nach dem Aufräumen das Spiel <b>testen</b> bevor du Quarantäne-Dateien endgültig löschst<br>
      ✅ Im Zweifel: <b>lieber behalten!</b> — doppelte CAS-Teile (Haare, Kleidung) sind harmlos<br>
      ⚠️ <b>Script-Mods</b> (.ts4script) sind nach Patches am problematischsten — bei Problemen zuerst die deaktivieren<br>
      ⚠️ <b>Konflikte</b> bei Tuning-Mods können zu Abstürzen führen — da konsequent aufräumen
    </div>
  </div>
</div>

<!-- Globale Suche -->
<div class="box" style="background:linear-gradient(135deg,#0f172a 60%,#1e1b4b);border:1px solid #4f46e5;position:sticky;top:0;z-index:100;">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <span style="font-size:20px;">🔍</span>
    <input class="search" id="global-search" placeholder="Globale Suche — durchsucht ALLE Mods, Duplikate, Konflikte, Notizen, Tags, CurseForge…" style="flex:1;min-width:200px;font-size:14px;padding:12px 16px;border:1px solid #4f46e5;">
    <span id="global-search-count" class="muted small"></span>
    <button class="btn btn-ghost" onclick="document.getElementById('global-search').value=''; globalSearch();" style="font-size:11px;">✖ Leeren</button>
  </div>
  <div id="global-search-results" style="display:none;margin-top:12px;max-height:70vh;overflow-y:auto;"></div>
</div>

<div id="section-nav">
  <span class="nav-label">Probleme:</span>
  <button class="nav-btn" onclick="document.getElementById('view-header').scrollIntoView({behavior:'smooth'})" id="nav-groups">📂 Duplikate <span class="nav-badge" id="nav-badge-groups">0</span></button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('corrupt-section').scrollIntoView({behavior:'smooth'})" id="nav-corrupt">💀 Korrupte <span class="nav-badge" id="nav-badge-corrupt">0</span></button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('conflict-section').scrollIntoView({behavior:'smooth'})" id="nav-conflict">⚔️ Konflikte <span class="nav-badge" id="nav-badge-conflict">0</span></button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('outdated-section').scrollIntoView({behavior:'smooth'})" id="nav-outdated">⏰ Veraltet <span class="nav-badge" id="nav-badge-outdated">0</span></button>
  <div class="nav-sep"></div>
  <span class="nav-label">Info:</span>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('addon-section').scrollIntoView({behavior:'smooth'})" id="nav-addon">🧩 Addons <span class="nav-badge" id="nav-badge-addon">0</span></button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('deps-section').scrollIntoView({behavior:'smooth'})" id="nav-deps">🔗 Abhängigkeiten <span class="nav-badge" id="nav-badge-deps">0</span></button>
  <button class="nav-btn" onclick="document.getElementById('error-section').scrollIntoView({behavior:'smooth'})" id="nav-errors">🔍 Fehler</button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('nonmod-section').scrollIntoView({behavior:'smooth'})" id="nav-nonmod">📄 Sonstige <span class="nav-badge" id="nav-badge-nonmod">0</span></button>
  <div class="nav-sep"></div>
  <button class="nav-btn" onclick="document.getElementById('import-section').scrollIntoView({behavior:'smooth'})" id="nav-import" style="background:linear-gradient(135deg,#1e3a5f,#0f172a);border:1px solid #2563eb;">📥 Import</button>
  <div class="nav-sep"></div>
  <span class="nav-label">Werkzeuge:</span>
  <button class="nav-btn" onclick="document.getElementById('batchbar').scrollIntoView({behavior:'smooth'})">🎛️ Aktionen</button>
  <button class="nav-btn" onclick="document.getElementById('stats-section').scrollIntoView({behavior:'smooth'})" id="nav-stats">📊 Statistik</button>
  <button class="nav-btn" onclick="document.getElementById('creators-section').scrollIntoView({behavior:'smooth'})" id="nav-creators">🔗 Creator</button>
  <button class="nav-btn" onclick="document.getElementById('allmods-section').scrollIntoView({behavior:'smooth'})" id="nav-allmods">🏷️ Alle Mods</button>
  <button class="nav-btn nav-hidden" onclick="document.getElementById('quarantine-section').scrollIntoView({behavior:'smooth'})" id="nav-quarantine">📦 Quarantäne <span class="nav-badge" id="nav-badge-quarantine">0</span></button>
  <button class="nav-btn" onclick="document.getElementById('history-section').scrollIntoView({behavior:'smooth'})" id="nav-history">📚 Verlauf</button>
  <div class="nav-sep"></div>
  <button class="nav-btn nav-btn-tutorial" onclick="startTutorial()" title="Tutorial nochmal anzeigen">❓ Tutorial</button>
  <button class="nav-btn nav-btn-bug" onclick="openBugReport()" title="Bug melden">🐛 Bug melden</button>
</div>

<!-- Bug Report Modal -->
<div id="bugreport-overlay">
  <div id="bugreport-card">
    <h2>🐛 Bug melden</h2>
    <div class="bug-sub">Dein Bericht wird automatisch mit System-Infos, Scan-Daten und Fehlerlogs an den Entwickler gesendet.</div>

    <div class="bug-field">
      <label>📋 Was für ein Problem hast du?</label>
      <select id="bug-category">
        <option value="">— Bitte auswählen —</option>
        <option value="crash">💥 Scanner stürzt ab / friert ein</option>
        <option value="scan">🔍 Scan funktioniert nicht richtig</option>
        <option value="display">🖥️ Anzeige-Fehler (Seite sieht kaputt aus)</option>
        <option value="action">⚡ Aktion funktioniert nicht (Quarantäne, Löschen etc.)</option>
        <option value="import">📥 Import funktioniert nicht</option>
        <option value="curseforge">🔥 CurseForge-Integration Problem</option>
        <option value="performance">🐢 Scanner ist sehr langsam</option>
        <option value="other">❓ Sonstiges</option>
      </select>
    </div>

    <div class="bug-field">
      <label>🔎 Was ist passiert? (Wähle alles aus was zutrifft)</label>
      <div class="bug-checks">
        <label><input type="checkbox" class="bug-symptom" value="Fehlermeldung angezeigt"> Fehlermeldung angezeigt</label>
        <label><input type="checkbox" class="bug-symptom" value="Seite lädt nicht"> Seite lädt nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Daten fehlen / sind falsch"> Daten fehlen / falsch</label>
        <label><input type="checkbox" class="bug-symptom" value="Button reagiert nicht"> Button reagiert nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Scanner hängt / keine Reaktion"> Scanner hängt</label>
        <label><input type="checkbox" class="bug-symptom" value="Spiel startet danach nicht"> Spiel startet danach nicht</label>
        <label><input type="checkbox" class="bug-symptom" value="Dateien verschwunden"> Dateien verschwunden</label>
        <label><input type="checkbox" class="bug-symptom" value="Sonstiges Problem"> Sonstiges</label>
      </div>
    </div>

    <div class="bug-field">
      <label>📝 Beschreibe das Problem kurz (optional aber hilfreich)</label>
      <textarea id="bug-description" placeholder="Z.B.: Ich habe auf Quarantäne geklickt aber nichts ist passiert…"></textarea>
    </div>

    <div class="bug-info">📎 <b>Folgende Infos werden automatisch mitgesendet:</b> System-Info, Scanner-Version, Spielversion, Scan-Ergebnis, Mod-Ordner, Mod-Statistik nach Typ, lastException.txt, lastUIException.txt, Scanner-Log</div>
    <div id="bug-status" class="bug-status"></div>
    <div class="bug-footer">
      <button class="tut-btn tut-btn-skip" onclick="closeBugReport()">Abbrechen</button>
      <button class="tut-btn tut-btn-primary" id="bug-send-btn" onclick="sendBugReport()" style="background:#dc2626;border-color:#dc2626;">🐛 Absenden</button>
    </div>
  </div>
</div>

<div class="box notice">
  <b>🛡️ Sicherheitshinweis:</b> Nutze immer <b>📦 Quarantäne</b> statt Löschen! Quarantäne = Dateien werden nur verschoben, du kannst sie jederzeit zurückholen. <b>🗑 Löschen</b> ist endgültig und nicht rückgängig zu machen!
</div>

<div class="box" id="import-section" style="border:1px solid #2563eb;background:linear-gradient(135deg,#0f172a 60%,#1e1b4b);">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📥 Mod-Import-Manager</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Ziehe <b>Dateien oder ganze Ordner</b> hierher (z.B. direkt aus einer entpackten RAR/ZIP). <b>Alles</b> wird 1:1 übernommen — Ordnerstruktur, Configs, Scripts, alles! Bei <b>bereits vorhandenen Dateien</b> wirst du gefragt.</div>

  <div id="import-dropzone" style="margin:12px 0;padding:28px 20px;border:2px dashed #334155;border-radius:12px;text-align:center;cursor:pointer;transition:all 0.2s;background:#0f1422;">
    <div style="font-size:32px;margin-bottom:6px;">📂</div>
    <div style="color:#94a3b8;font-size:14px;"><b>Mod-Dateien oder Ordner hierher ziehen</b></div>
    <div class="muted small" style="margin-top:4px;">oder klicke hier um Dateien auszuwählen</div>
    <input type="file" id="import-file-input" multiple style="display:none;">
    <input type="file" id="import-folder-input" webkitdirectory style="display:none;">
    <div style="margin-top:8px;"><button class="btn btn-ghost" id="btn-import-folder-select" style="padding:4px 14px;font-size:12px;" onclick="event.stopPropagation(); document.getElementById('import-folder-input').click();">📁 Ordner auswählen</button></div>
  </div>

  <div style="margin:12px 0; display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
    <input type="text" id="import-source" placeholder="Oder: ganzen Quell-Ordner angeben (z.B. C:\\Users\\Name\\Downloads)" style="flex:1; min-width:300px; padding:8px 12px; background:#0f1115; border:1px solid #334155; border-radius:6px; color:#e7e7e7; font-size:14px;">
    <button class="btn btn-ok" id="btn-import-scan" title="Scannt den Quell-Ordner und importiert alle Dateien">🔍 Ordner scannen</button>
  </div>

  <div id="import-target-row" style="margin:8px 0 12px; display:none;">
    <label class="muted small">Ziel-Unterordner im Mods-Ordner (optional):</label>
    <input type="text" id="import-target-subfolder" placeholder="(direkt in Mods-Ordner)" style="width:300px; padding:6px 10px; background:#0f1115; border:1px solid #334155; border-radius:6px; color:#e7e7e7; font-size:13px; margin-left:8px;">
  </div>

  <div id="import-status" class="muted small" style="margin:4px 0;"></div>

  <div id="import-actions" style="display:none; margin:8px 0; gap:8px; display:none;">
    <button class="btn btn-ok" id="btn-import-all-update" title="Alle Updates übernehmen (überschreibt vorhandene)">🔄 Alle Updates übernehmen</button>
    <button class="btn btn-ghost" id="btn-import-clear">✖ Liste leeren</button>
  </div>

  <div id="import-results" style="margin-top:8px;"></div>
</div>

<div id="last" class="muted">Letzte Aktion: –</div>
<div id="watcher-banner" style="display:none;padding:8px 16px;margin:4px 0;border-radius:8px;background:linear-gradient(90deg,#1e3a5f,#1e293b);border:1px solid #334155;color:#94a3b8;font-size:0.95em;display:flex;align-items:center;gap:8px;" class="muted small">
  <span id="watcher-dot" style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;animation:watcherPulse 2s ease-in-out infinite;"></span>
  <span>👁️ Datei-Watcher aktiv — <span id="watcher-files">0</span> Dateien überwacht</span>
  <span id="watcher-event" style="margin-left:auto;opacity:0.7;"></span>
</div>
<style>
@keyframes watcherPulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
</style>

<div class="box" id="batchbar">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>📋 Sammel-Aktionen</b>
      <span class="pill" id="selcount">0 ausgewählt</span><br>
      <span class="muted small">Hier kannst du alle Dateien, bei denen du ein <b>Häkchen ☑️</b> gesetzt hast, auf einmal verarbeiten.</span><br>
      <span class="muted small" style="opacity:0.6;">Log-Datei: <code id="logfile"></code></span>
    </div>
    <div class="flex">
      <button class="btn btn-ok" id="btn_q_sel" title="SICHER: Verschiebt alle markierten Dateien in einen Quarantäne-Ordner. Du kannst sie jederzeit wiederherstellen!">📦 In Quarantäne verschieben</button>
      <button class="btn btn-danger" id="btn_d_sel" title="ACHTUNG: Löscht alle markierten Dateien ENDGÜLTIG vom PC! Nicht rückgängig machbar!">🗑 Endgültig löschen</button>
      <button class="btn btn-ghost" id="btn_clear_sel" title="Entfernt alle Häkchen — keine Dateien werden verändert">✖ Auswahl leeren</button>
      <button class="btn btn-ghost" id="reload" title="Scannt alle Mod-Ordner komplett neu — kann bei vielen Mods ein paar Minuten dauern">↻ Neu scannen</button>
      <button class="btn btn-ghost" id="btn_save_html" title="Speichert eine Kopie dieser Seite als HTML-Datei auf dem Desktop — praktisch zum Teilen oder Archivieren">📄 Bericht speichern</button>
    </div>
  </div>
  <div class="hr"></div>
  <div id="batchstatus" class="muted small">Bereit.</div>
</div>

<div class="box">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>Aktionen-Log</b> <span class="pill">wird im Browser gespeichert</span>
      <span class="muted small" style="margin-left:4px;">Alle Quarantäne/Lösch-Aktionen werden hier protokolliert</span>
    </div>
    <div class="flex">
      <button class="btn btn-ghost" id="log_copy">📋 Log kopieren</button>
      <button class="btn btn-ghost" id="log_csv">💾 CSV exportieren</button>
      <button class="btn btn-danger" id="log_clear">🧹 Log leeren</button>
    </div>
  </div>
  <div style="margin-top:10px;" id="log"></div>
</div>

<div class="topgrid">
  <div class="box">
    <h3>🔍 Suche & Filter</h3>
    <p class="muted small" style="margin:0 0 8px;">Filtere die Ergebnisse oder suche nach bestimmten Mod-Namen.</p>
    <input class="search" id="q" placeholder="Mod-Name eingeben… z.B. wicked, mccc, littlemssam">
    <div class="flex" style="margin-top:10px;">
      <label title="Dateien mit exakt gleichem Namen in verschiedenen Ordnern"><input type="checkbox" id="f_name" checked> 📛 Name-Duplikate</label>
      <label title="Dateien die Byte-für-Byte identisch sind (egal wie sie heißen)"><input type="checkbox" id="f_content" checked> 📦 Inhalt-Duplikate</label>
      <label title="Dateien mit sehr ähnlichem Namen (z.B. verschiedene Versionen)"><input type="checkbox" id="f_similar" checked> 🔤 Ähnliche Namen</label>
      <label title="Gruppiert Dateien nach ihrem Unterordner"><input type="checkbox" id="g_mod" checked> 📁 nach Unterordner gruppieren</label>
      <label title="Zeigt den kompletten Dateipfad statt nur den Dateinamen"><input type="checkbox" id="show_full" checked> 📂 voller Pfad</label>
      <label title="Bei Sammel-Aktionen (Rest in Quarantäne etc.) wird bevorzugt eine Datei aus dem Haupt-Mod-Ordner behalten">
        <input type="checkbox" id="keep_ord1" checked> ⭐ Haupt-Ordner bevorzugen
      </label>
      <label title="Zeigt auch Gruppen an, die du als 'Ist korrekt' markiert hast"><input type="checkbox" id="f_show_ignored"> 👁 Ignorierte anzeigen</label>
    </div>
    <div class="hr"></div>
    <div id="summary" class="muted">Lade…</div>
  </div>

  <div class="box">
    <h3>📁 Gescannte Ordner</h3>
    <ul id="roots" class="muted" style="margin:0; padding-left:18px;"></ul>
    <div class="hr"></div>
    <div class="muted small">ℹ️ <b>Inhalt-Duplikat</b> = Dateien sind zu 100% identisch (sicher löschbar).<br><b>Name-Duplikat</b> = Gleicher Name, aber Inhalt könnte unterschiedlich sein (erst prüfen!).</div>
  </div>
</div>

<div class="box" id="view-header">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2 id="view-title">📂 Duplikat-Gruppen</h2>
    <div class="view-toggle" id="view-toggle">
      <button class="active" data-view="groups" title="Zeigt zusammengehörige Dateien als Gruppen">📂 Gruppen-Ansicht</button>
      <button data-view="perfile" title="Zeigt alle Infos pro einzelner Datei auf einer Karte">📋 Pro Datei</button>
    </div>
  </div>
  <div class="info-hint" style="margin-top:8px;">💡 <b>So funktioniert es:</b> Jede Gruppe zeigt Dateien die zusammengehören (z.B. Duplikate). Setze ein <b>Häkchen ☑️</b> bei der Datei, die du <b>nicht brauchst</b>, und nutze dann oben <b>📦 Quarantäne</b>. Die Buttons <b>"🗑 Rest in Quarantäne"</b> helfen dir: sie markieren automatisch alle außer der besten Datei.</div>
</div>

<div id="groups-view">
<div class="box">
  <div id="groups">Lade…</div>
</div>
</div>

<div id="perfile-view">
<div class="box">
  <div style="background:#1a2238; border:1px solid #2b3553; border-radius:12px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#e2e8f0;">📋 Pro-Datei-Ansicht — Was ist das?</p>
    <p class="muted" style="margin:0 0 8px;">Hier siehst du <b>jede Datei einzeln</b> mit allen Infos auf einen Blick. Kein Hin- und Herscrollen zwischen verschiedenen Sektionen mehr!</p>
    <div style="display:grid; grid-template-columns:auto 1fr; gap:6px 12px; font-size:12px; margin-top:8px;">
      <span class="corrupt-status no_dbpf" style="text-align:center;">⚠️ Korrupt</span>
      <span class="muted">Datei ist beschädigt oder hat falsches Format — kann Fehler im Spiel verursachen</span>
      <span class="conflict-badge" style="text-align:center;">🔀 Konflikt</span>
      <span class="muted">Teilt sich IDs mit anderen Mods — eins überschreibt das andere, nur eins funktioniert</span>
      <span class="addon-badge" style="text-align:center;">🧩 Addon</span>
      <span class="muted">Ergänzt einen anderen Mod — <b>OK, beide behalten!</b></span>
      <span class="pill" style="background:#4c1d95;color:#c4b5fd; text-align:center;">Inhalt-Duplikat</span>
      <span class="muted">Exakt gleicher Inhalt wie eine andere Datei — eine davon ist überflüssig</span>
      <span class="pill" style="background:#1e3a5f;color:#60a5fa; text-align:center;">Name-Duplikat</span>
      <span class="muted">Gleicher Dateiname in verschiedenen Ordnern</span>
      <span class="pill" style="background:#134e4a;color:#5eead4; text-align:center;">Ähnlich</span>
      <span class="muted">Sehr ähnlicher Name — könnte eine alte/neue Version sein</span>
    </div>
    <p class="muted small" style="margin:10px 0 0;">💡 Tipp: Dateien mit den meisten Auffälligkeiten stehen ganz oben. Nutze die Suche um eine bestimmte Datei zu finden.</p>
  </div>
  <input class="search" id="pf-search" placeholder="Datei suchen… z.B. wicked, littlemssam, asketo">
  <div id="perfile-summary" class="muted" style="margin-top:8px;"></div>
  <div id="perfile-list" style="margin-top:12px;"></div>
</div>
</div>

<div class="box" id="corrupt-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>⚠️ Korrupte / Verdächtige .package-Dateien</h2>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese .package-Dateien sind beschädigt oder haben ein ungültiges Format. Sie verursachen möglicherweise Fehler im Spiel. <b>Empfehlung:</b> Lösche sie oder lade sie neu vom Ersteller herunter.</div>
  <div id="corrupt-summary" class="muted"></div>
  <div id="corrupt-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="addon-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🧩 Addon-Beziehungen (erwartet)</h2>
  </div>
  <div style="background:#0f2922; border:1px solid #065f46; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#6ee7b7;">✅ Alles OK — das hier sind keine Probleme!</p>
    <p class="muted" style="margin:0 0 6px;">Diese Packages teilen sich <b>absichtlich</b> Ressource-IDs. Das passiert, wenn ein <b>Addon/Erweiterung</b> einen bestehenden Mod ergänzt oder anpasst.</p>
    <p class="muted" style="margin:0 0 6px;">Beispiel: <i>LittleMsSam_DressCodeLotTrait<b>!_Addon_LotChallenge</b>.package</i> erweitert den Basis-Mod <i>LittleMsSam_DressCodeLotTrait.package</i>.</p>
    <p class="muted" style="margin:0 0 6px;">👉 <b>Beide behalten!</b> Addon + Basis-Mod gehören zusammen. Wenn du eins löschst, funktioniert das andere nicht mehr richtig.</p>
    <p class="muted small" style="margin:0;">Tipp: Falls ein Addon nach einem Update Probleme macht, prüfe ob <b>beide</b> (Addon + Basis) auf dem gleichen Stand sind.</p>
  </div>
  <div id="addon-summary" class="muted"></div>
  <div id="addon-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="conflict-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔀 Ressource-Konflikte (Doppelte Mod-IDs)</h2>
  </div>
  <div style="background:#1e1b2e; border:1px solid #3a3a5e; border-radius:10px; padding:14px; margin-bottom:14px;">
    <p style="margin:0 0 8px; font-size:14px; font-weight:bold; color:#c4b5fd;">💡 Was bedeutet das?</p>
    <p class="muted" style="margin:0 0 6px;">Jede Mod-Datei (.package) enthält <b>Ressourcen</b> mit eindeutigen IDs — z.B. Haare, Kleidung, Objekte oder Gameplay-Änderungen.</p>
    <p class="muted" style="margin:0 0 6px;">Wenn <b>zwei Packages die gleichen IDs</b> haben, überschreibt eins das andere. Das heißt: <b>nur eins funktioniert</b>, das andere wird vom Spiel ignoriert!</p>
    <p class="muted" style="margin:0 0 6px;">👉 <b>Was tun?</b> Meistens sind es alte/neue Versionen desselben Mods. Behalte die <b>neuere</b> (schau aufs Datum) und verschiebe die andere in Quarantäne.</p>
    <p class="muted small" style="margin:0;">Tipp: Bei <b>CAS Part</b>-Konflikten (Haare, Kleidung, Make-up) sieht man nur eine Variante im Spiel. Bei <b>Tuning</b>-Konflikten (Gameplay) kann es zu Fehlern oder Abstürzen kommen.</p>
  </div>
  <div id="conflict-summary" class="muted"></div>
  <div id="conflict-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="outdated-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>⏰ Veraltete Mods</h2>
    <span class="muted small" id="outdated-game-ver"></span>
  </div>
  <div style="padding:10px 14px;background:#1e293b;border-radius:8px;margin-bottom:10px;">
    <p class="muted" style="margin:0 0 6px;">Diese Mods wurden <b>vor dem letzten Spiel-Patch</b> zuletzt geändert. Sie könnten nach dem Update nicht mehr funktionieren.</p>
    <p class="muted" style="margin:0 0 6px;">⚠️ <b>Hohes Risiko:</b> Script-Mods (.ts4script) — brechen fast immer nach Patches.</p>
    <p class="muted" style="margin:0 0 6px;">⚡ <b>Mittleres Risiko:</b> Tuning/Gameplay-Mods — können nach Patches Fehler verursachen.</p>
    <p class="muted small" style="margin:0;">✅ <b>Niedriges Risiko:</b> CAS/CC und Objekte — brechen selten, meistens nur bei großen Updates.</p>
  </div>
  <div style="margin-bottom:8px;">
    <label class="muted small"><input type="checkbox" id="outdated-filter-high" checked> ⚠️ Hohes Risiko</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="outdated-filter-mid" checked> ⚡ Mittleres Risiko</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="outdated-filter-low"> ✅ Niedriges Risiko</label>
  </div>
  <div id="outdated-summary" class="muted"></div>
  <div id="outdated-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="deps-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔗 Mod-Abhängigkeiten</h2>
    <span class="muted small" id="deps-summary"></span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du, welche Mods <b>zusammengehören</b>. Script+Package-Paare sollten immer gemeinsam behalten oder entfernt werden. Mod-Familien (viele Dateien mit gleichem Prefix) gehören vermutlich zum selben Mod.</div>
  <div style="margin-bottom:8px;">
    <label class="muted small"><input type="checkbox" id="deps-filter-pairs" checked> 🔗 Script-Paare</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-namedeps" checked> 📎 Namens-Abhängigkeiten</label>
    <label class="muted small" style="margin-left:12px;"><input type="checkbox" id="deps-filter-families" checked> 👨‍👩‍👧‍👦 Mod-Familien</label>
  </div>
  <div id="deps-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="error-section">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔍 Fehler-Analyse</h2>
    <button class="btn btn-ghost" id="btn_reload_errors">↻ Fehler neu laden</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier werden die Fehlerlogs deines Spiels (lastException.txt, lastUIException.txt) automatisch ausgelesen und verständlich erklärt. So findest du heraus, welcher Mod ein Problem verursacht hat.</div>
  <div id="error-summary" class="muted">Lade Fehler…</div>
  <div id="error-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="history-section">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📊 Verlauf &amp; Mod-Inventar</h2>
    <button class="btn btn-ghost" id="btn_reload_history">↻ Aktualisieren</button>
  </div>

  <div class="info-hint">💡 <b>Was ist das?</b> Der Verlauf zeigt dir wieviele Mods du installiert hast und was sich seit dem letzten Scan geändert hat (neue Mods, gelöschte Mods, Updates). So behältst du den Überblick.</div>
  <div id="mod-snapshot" style="margin-bottom:16px;">
    <h3 style="margin:12px 0 8px;">📦 Mod-Inventar</h3>
    <div id="mod-snapshot-content" class="muted">Lade…</div>
  </div>

  <div id="mod-changes" style="margin-bottom:16px; display:none;">
    <h3 style="margin:12px 0 8px;">🔄 Änderungen seit letztem Scan</h3>
    <div id="mod-changes-content"></div>
  </div>

  <div id="scan-history">
    <h3 style="margin:12px 0 8px;">📈 Scan-Verlauf</h3>
    <div id="scan-history-content" class="muted">Lade…</div>
  </div>

  <div id="history-chart-area" style="display:none; margin-top:16px;">
    <h3 style="margin:0 0 8px; font-size:14px;">📊 Verlaufs-Diagramm</h3>
    <div class="chart-container">
      <canvas id="history-chart"></canvas>
    </div>
  </div>
</div>

<!-- Live-Fortschrittsbalken -->
<div class="box" id="progress-section" style="display:none;">
  <h2>🔄 Scan läuft…</h2>
  <div id="progress-phase" class="muted" style="margin-bottom:8px;">Starte…</div>
  <div style="background:#23293a; border-radius:8px; height:28px; overflow:hidden; position:relative; margin-bottom:8px;">
    <div id="progress-bar" style="height:100%; background:linear-gradient(90deg,#6366f1,#a78bfa); width:0%; transition:width 0.3s ease; border-radius:8px; display:flex; align-items:center; justify-content:center;">
      <span id="progress-pct" style="color:#fff; font-size:12px; font-weight:600; text-shadow:0 1px 2px rgba(0,0,0,0.5);"></span>
    </div>
  </div>
  <div id="progress-detail" class="muted" style="font-size:12px;"></div>
</div>

<div class="box" id="all-ok-banner" style="display:none; text-align:center; padding:30px;">
  <div style="font-size:48px; margin-bottom:12px;">✅</div>
  <h2 style="color:#4ade80; margin:0 0 8px;">Alles sieht gut aus!</h2>
  <p class="muted" style="max-width:500px;margin:0 auto;">Keine Duplikate, keine korrupten Dateien, keine Konflikte gefunden. Deine Mod-Sammlung ist aufgeräumt!</p>
</div>

<div class="box" id="stats-section">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📊 Mod-Statistiken</h2>
    <button class="btn btn-ghost" id="btn_export_modlist" title="Exportiere komplette Mod-Liste als CSV-Datei">📥 Mod-Liste exportieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Eine Übersicht über deine gesamte Mod-Sammlung: Wie viele Mods du hast, welche Kategorien, welche Ordner am größten sind und welche Dateien am meisten Platz brauchen.</div>
  <div id="stats-overview" class="muted">Lade…</div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:12px;">
    <div>
      <h3 style="margin:0 0 8px; font-size:14px;">🎨 Mod-Kategorien</h3>
      <div id="stats-categories"></div>
    </div>
    <div>
      <h3 style="margin:0 0 8px; font-size:14px;">📁 Größte Ordner</h3>
      <div id="stats-folders"></div>
    </div>
  </div>
  <div style="margin-top:16px;">
    <h3 style="margin:0 0 8px; font-size:14px;">📀 Top 10 größte Mods</h3>
    <div id="stats-biggest"></div>
  </div>
</div>

<div class="box" id="creators-section">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🔗 Mod-Creator & Download-Links</h2>
    <button class="btn btn-ghost" id="btn_toggle_creator_form" title="Neuen Creator/Download-Link hinzufügen">➕ Creator hinzufügen</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier kannst du eigene Creator-Links hinterlegen. Wenn ein Dateiname ein bestimmtes Muster enthält (z.B. <code>wickedwhims</code>), wird automatisch ein klickbarer Badge angezeigt. So findest du schnell die Download-Seite für Updates!</div>

  <div id="creator-form-box" style="display:none; margin:12px 0; padding:14px; background:#1a1d2e; border:1px solid #334155; border-radius:10px;">
    <h3 style="margin:0 0 10px; font-size:14px;" id="creator-form-title">➕ Neuen Creator hinzufügen</h3>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
      <div>
        <label style="font-size:12px; color:#9ca3af;">Dateiname-Muster <span style="color:#f87171;">*</span></label>
        <input type="text" id="cr_key" placeholder="z.B. wickedwhims, mccc, littlemssam" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
        <div style="font-size:11px;color:#6b7280;margin-top:2px;">Wird im Dateinamen gesucht (Kleinbuchstaben)</div>
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Creator-Name <span style="color:#f87171;">*</span></label>
        <input type="text" id="cr_name" placeholder="z.B. TURBODRIVER" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Download/Website-URL</label>
        <input type="text" id="cr_url" placeholder="https://example.com" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
      <div>
        <label style="font-size:12px; color:#9ca3af;">Icon/Emoji</label>
        <input type="text" id="cr_icon" placeholder="🔗" maxlength="4" style="width:100%;padding:8px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:13px;box-sizing:border-box;">
      </div>
    </div>
    <div class="flex" style="margin-top:10px; gap:8px;">
      <button class="btn btn-ok" id="btn_save_creator">💾 Speichern</button>
      <button class="btn btn-ghost" id="btn_cancel_creator">Abbrechen</button>
      <input type="hidden" id="cr_edit_mode" value="">
    </div>
  </div>

  <div id="creators-list" style="margin-top:12px;"></div>
</div>

<div class="box" id="allmods-section">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>🏷️ Alle Mods — Tags &amp; Notizen</h2>
    <div class="flex" style="gap:6px;">
      <select id="allmods-cat-filter" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;">
        <option value="">Alle Kategorien</option>
      </select>
      <select id="allmods-tag-filter" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;">
        <option value="">Alle Tags</option>
        <option value="__tagged">🏷️ Nur getaggte</option>
        <option value="__untagged">Ohne Tags</option>
        <option value="__noted">📝 Mit Notiz</option>
      </select>
      <input type="text" id="allmods-search" placeholder="🔍 Mod suchen…" style="padding:6px 10px;background:#0f1115;border:1px solid #334155;border-radius:6px;color:#e7e7e7;font-size:12px;width:220px;">
    </div>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du <b>alle gescannten Mods</b> auf einen Blick. Du kannst jeder Datei Tags und Notizen zuweisen, um deine Mod-Sammlung zu organisieren. Nutze die Suche und Filter oben rechts.</div>
  <div id="allmods-summary" class="muted" style="margin:8px 0;">Warte auf Scan…</div>
  <div id="allmods-list" style="margin-top:8px;"></div>
  <div id="allmods-loadmore" style="text-align:center;margin-top:12px;display:none;">
    <button class="btn btn-ghost" id="btn_allmods_more">⬇️ Mehr laden…</button>
  </div>
</div>

<div class="box" id="nonmod-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📄 Sonstige Dateien im Mods-Ordner</h2>
    <span class="muted" id="nonmod-summary">Warte auf Scan…</span>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Diese Dateien liegen in deinem Mods-Ordner, sind aber <b>keine Mods</b> (.package/.ts4script). Das Spiel ignoriert sie — sie stören nicht, nehmen aber Platz weg. Typisch: Readmes, Vorschau-Bilder, alte Archive.</div>
  <div id="nonmod-list" style="margin-top:8px;"></div>
</div>

<div class="box" id="quarantine-section" style="display:none;">
  <div class="flex" style="justify-content:space-between; align-items:center;">
    <h2>📦 Quarantäne-Manager</h2>
    <button class="btn btn-ghost" id="btn_reload_quarantine">↻ Aktualisieren</button>
  </div>
  <div class="info-hint">💡 <b>Was ist das?</b> Hier siehst du alle Dateien, die du in Quarantäne verschoben hast. Du kannst sie einzeln <b>zurückholen</b> (zurück in den Mods-Ordner) oder <b>endgültig löschen</b>.</div>
  <div id="quarantine-summary" class="muted">Lade…</div>
  <div id="quarantine-list" style="margin-top:12px;"></div>
</div>

<script>
const TOKEN = __TOKEN__;
const LOGFILE = __LOGFILE__;
document.getElementById('logfile').textContent = LOGFILE;

const LOG_KEY = 'dupe_actionlog_v2';
let logEntries = [];
try { logEntries = JSON.parse(localStorage.getItem(LOG_KEY) || '[]'); } catch(e) { logEntries = []; }

const selected = new Set();

function esc(s) {
  return String(s ?? '')
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'","&#39;");
}

function renderLog() {
  document.getElementById('log').textContent = logEntries.join('\\n');
}
renderLog();

function addLog(line) {
  const ts = new Date().toLocaleString();
  logEntries.unshift(`[${ts}] ${line}`);
  if (logEntries.length > 500) logEntries = logEntries.slice(0, 500);
  localStorage.setItem(LOG_KEY, JSON.stringify(logEntries));
  renderLog();
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch (e) {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta);
    ta.select(); document.execCommand('copy'); ta.remove();
  }
}

document.getElementById('log_copy').addEventListener('click', async () => {
  await copyText(logEntries.join('\\n'));
  addLog('LOG COPIED');
});

document.getElementById('log_csv').addEventListener('click', async () => {
  // Create CSV from log entries
  const csv = logEntries.map(line => {
    // Escape CSV fields properly
    return '"' + line.replace(/"/g, '""') + '"';
  }).join('\\n');
  
  // Add header
  const csvWithHeader = '"Timestamp | Action | Info"\\n' + csv;
  
  // Create download
  const blob = new Blob([csvWithHeader], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `dupe_actions_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  addLog('CSV EXPORTED');
});

document.getElementById('log_clear').addEventListener('click', () => {
  if (!confirm('Log wirklich leeren?')) return;
  logEntries = [];
  localStorage.setItem(LOG_KEY, JSON.stringify(logEntries));
  renderLog();
});

function setLast(text) {
  document.getElementById('last').textContent = 'Letzte Aktion: ' + text;
}

function setBatchStatus(text) {
  document.getElementById('batchstatus').textContent = text;
}

function updateSelCount() {
  document.getElementById('selcount').textContent = `${selected.size} ausgewählt`;
}

async function loadData() {
  const r = await fetch('/api/data?token=' + encodeURIComponent(TOKEN));
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || 'unknown');
  return j.data;
}

async function postAction(action, path, extra={}) {
  const res = await fetch('/api/action', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ token: TOKEN, action, path, ...extra })
  });
  const j = await res.json();
  if (!j.ok) throw new Error(j.error || 'unknown');
  return j;
}

function matchesFilters(text, term) {
  term = term.trim().toLowerCase();
  if (!term) return true;
  return text.toLowerCase().includes(term);
}

function humanSize(bytes) {
  const units = ['B','KB','MB','GB','TB'];
  let x = Number(bytes);
  let i = 0;
  while (x >= 1024 && i < units.length-1) { x /= 1024; i++; }
  return i === 0 ? `${Math.round(x)} B` : `${x.toFixed(2)} ${units[i]}`;
}

function uniqueCount(arr) { return new Set(arr).size; }

// Cluster-Rendering: Gruppiert Dateien innerhalb einer Ähnlich-Gruppe nach identischem Inhalt (Hash)
function renderClusters(files, gi) {
  // Gruppiere nach Hash
  const byHash = new Map();
  const noHash = [];
  for (const f of files) {
    if (f.hash) {
      if (!byHash.has(f.hash)) byHash.set(f.hash, []);
      byHash.get(f.hash).push(f);
    } else {
      noHash.push(f);
    }
  }

  // Trenne: Cluster (2+ mit gleichem Hash) vs Einzigartige
  const clusters = [];
  const unique = [...noHash];
  for (const [hash, group] of byHash) {
    if (group.length >= 2) {
      clusters.push(group);
    } else {
      unique.push(group[0]);
    }
  }

  // Wenn keine Cluster gefunden → keine Sub-Gruppierung nötig
  if (clusters.length === 0) return null;

  let html = '';
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

  for (let ci = 0; ci < clusters.length; ci++) {
    const cluster = clusters[ci];
    const letter = letters[ci] || (ci + 1);
    const size = cluster[0].size_h || '?';
    html += `<div style="margin:8px 0 4px 0;padding:8px 12px;background:#0a2010;border:1px solid #22c55e40;border-left:3px solid #22c55e;border-radius:8px;">
      <div style="font-size:13px;font-weight:bold;color:#86efac;margin-bottom:4px;">
        🔗 Cluster ${esc(String(letter))} — ${cluster.length}× identisch (je ${esc(size)})
        <span class="pill" style="background:#14532d;color:#86efac;font-size:11px;">Behalte 1, lösche ${cluster.length - 1}</span>
      </div>
      ${cluster.map(f => renderFileRow(f, gi)).join('')}
    </div>`;
  }

  if (unique.length > 0) {
    html += `<div style="margin:8px 0 4px 0;padding:8px 12px;background:#1e1b4b40;border:1px solid #8b5cf640;border-left:3px solid #8b5cf6;border-radius:8px;">
      <div style="font-size:13px;font-weight:bold;color:#c4b5fd;margin-bottom:4px;">
        ✨ Einzigartig — ${unique.length} Datei(en)
        <span class="pill" style="background:#312e81;color:#c4b5fd;font-size:11px;">Manuell prüfen</span>
      </div>
      ${unique.map(f => renderFileRow(f, gi)).join('')}
    </div>`;
  }

  return html;
}

function fmtGroupHeader(g) {
  const t = g.type === 'name' ? 'Name' : g.type === 'similar' ? 'Ähnlich' : 'Inhalt';
  const count = g.files.length;
  const per = g.size_each ? ('je ~ ' + humanSize(g.size_each)) : '';
  const folders = uniqueCount(g.files.map(f => f.mod_folder || '(Mods-Root)'));

  // Bei ähnlichen Gruppen: Versions-Info anzeigen
  let versionHint = '';
  let deepHint = '';
  if (g.type === 'similar') {
    const versions = g.files.map(f => f.version || '').filter(v => v);
    if (versions.length > 0) {
      versionHint = `<span class="pill" style="background:#1e3a5f;color:#60a5fa;">Versionen: ${versions.map(v => esc(v)).join(', ')}</span>`;
    }
    // Deep comparison badge
    if (g.deep_comparison) {
      const dc = g.deep_comparison;
      const icon = dc.recommendation === 'update' ? '⬆️' : dc.recommendation === 'different' ? '✅' : '❓';
      deepHint = `<span class="pill" style="background:${dc.recommendation_color}20;color:${dc.recommendation_color};border:1px solid ${dc.recommendation_color};">
        ${icon} ${dc.overlap_pct}% Überlappung</span>`;
    }
  }

  // Kategorie-Badge aus Gruppen-Info
  let catBadge = '';
  if (g.group_category) {
    let cs = 'background:#1e293b;color:#94a3b8;';
    const gc = g.group_category;
    if (gc.includes('Haare')) cs = 'background:#7c3aed33;color:#c084fc;border:1px solid #7c3aed;font-weight:bold;';
    else if (gc.includes('Make-Up')) cs = 'background:#ec489922;color:#f472b6;border:1px solid #ec4899;';
    else if (gc.includes('Accessoire')) cs = 'background:#f59e0b22;color:#fbbf24;border:1px solid #f59e0b;';
    else if (gc.includes('Kleidung')) cs = 'background:#06b6d422;color:#22d3ee;border:1px solid #06b6d4;';
    catBadge = `<span class="pill" style="${cs}font-size:11px;">${esc(gc)}</span>`;
  }

  return `<span><b>${esc(g.key_short)}</b>
    <span class="pill" style="${g.type === 'similar' ? 'background:#1e3a5f;color:#60a5fa;' : ''}">${t}</span>
    <span class="pill">${count} Dateien</span>
    <span class="pill">${folders} Ordner</span>
    ${per ? `<span class="pill">${esc(per)}</span>` : ''}
    ${catBadge}
    ${versionHint}
    ${deepHint}
  </span>`;
}

function removeRowsForPath(path) {
  document.querySelectorAll('button[data-path]').forEach(btn => {
    if (btn.dataset.path === path) {
      const fileDiv = btn.closest('.file');
      if (fileDiv) fileDiv.remove();
    }
  });
  // also unselect checkbox
  document.querySelectorAll('input.sel[data-path]').forEach(cb => {
    if (cb.dataset.path === path) cb.checked = false;
  });
  selected.delete(path);
  updateSelCount();
}

function preferKeepPath(files) {
  // Prefer Ordner 1 if enabled, otherwise first.
  const preferOrd1 = document.getElementById('keep_ord1').checked;
  if (!files || files.length === 0) return null;
  if (preferOrd1) {
    const inOrd1 = files.find(f => f.root_index === 1);
    if (inOrd1) return inOrd1.path;
  }
  return files[0].path;
}

function renderDeepInfo(f, gi) {
  if (!f.deep) return '';
  const d = f.deep;

  // Thumbnail
  const thumb = d.thumbnail_b64
    ? `<img src="${d.thumbnail_b64}" class="thumb-clickable" onclick="openCompareGallery(${gi})" style="max-width:72px;max-height:72px;border-radius:6px;border:1px solid #444;margin-right:12px;float:left;background:#1e293b;" title="🖼️ Klicken um alle Bilder der Gruppe zu vergleichen" />`
    : '';

  // Kategorie mit dynamischer Farbe
  let catStyle = 'background:#1e3a5f;color:#60a5fa';
  if (d.category && d.category.includes('Haare')) catStyle = 'background:#7c3aed22;color:#c084fc;border:1px solid #7c3aed';
  else if (d.category && d.category.includes('Make-Up')) catStyle = 'background:#ec489922;color:#f472b6;border:1px solid #ec4899';
  else if (d.category && d.category.includes('Accessoire')) catStyle = 'background:#f59e0b22;color:#fbbf24;border:1px solid #f59e0b';
  else if (d.category && d.category.includes('Kleidung')) catStyle = 'background:#06b6d422;color:#22d3ee;border:1px solid #06b6d4';
  const cat = d.category
    ? `<span class="pill" style="${catStyle};font-size:11px;" title="Automatisch erkannte Mod-Kategorie">${esc(d.category)}</span>`
    : '';

  // Resource count
  const resCount = `<span class="pill" style="background:#1e293b;font-size:11px;" title="Anzahl der Ressourcen in dieser .package">📦 ${d.total_resources} Ressourcen</span>`;

  // Type breakdown pills (top 5)
  const types = Object.entries(d.type_breakdown || {}).slice(0, 5)
    .map(([k, v]) => `<span class="pill" style="background:#1e293b;font-size:11px;" title="Ressource-Typ: ${esc(k)}">${esc(k)}: ${v}</span>`).join(' ');

  // CAS body types mit Kategorie-Farben
  const _btStyle = (b) => {
    const hair = ['Haare','Haarfarbe'];
    const cloth = ['Oberteil','Ganzkörper','Unterteil','Schuhe','Socken','Strumpfhose','Handschuhe'];
    const makeup = ['Make-Up','Lidschatten','Lippenstift','Wimpern','Gesichtsbehaarung','Gesichts-Overlay','Kopf','Körper'];
    const acc = ['Hut','Brille','Halskette','Armband','Ohrringe','Ring','Oberteil-Accessoire','Tattoo','Ohrläppchen','Zähne','Fingernägel','Fußnägel'];
    if (hair.includes(b)) return {bg:'#7c3aed33',fg:'#c084fc',bd:'#7c3aed',icon:'💇 '};
    if (cloth.includes(b)) return {bg:'#0e7490aa',fg:'#67e8f9',bd:'#06b6d4',icon:'👚 '};
    if (makeup.includes(b)) return {bg:'#9d174daa',fg:'#f9a8d4',bd:'#ec4899',icon:'💄 '};
    if (acc.includes(b)) return {bg:'#92400eaa',fg:'#fcd34d',bd:'#f59e0b',icon:'💍 '};
    return {bg:'#4a1942',fg:'#f0abfc',bd:'#7c3aed',icon:''};
  };
  const cas = d.cas_body_types && d.cas_body_types.length
    ? `<div style="margin-top:4px;">👗 <span style="color:#f0abfc;font-size:12px;">Body: ${d.cas_body_types.map(b => {
        const s = _btStyle(b);
        return `<span class="pill" style="background:${s.bg};color:${s.fg};border:1px solid ${s.bd};font-size:11px;font-weight:bold;">${s.icon}${esc(b)}</span>`;
      }).join(' ')}</span></div>`
    : '';

  // Tuning names
  const tuning = d.tuning_names && d.tuning_names.length
    ? `<div style="margin-top:4px;">📝 <span style="font-size:11px;color:#94a3b8;">Tuning: </span>${d.tuning_names.slice(0, 5).map(n => `<code style="font-size:11px;background:#1e293b;padding:1px 5px;border-radius:4px;">${esc(n)}</code>`).join(' ')}</div>`
    : '';

  return `
  <div class="deep-info" style="margin-top:8px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;font-size:12px;">
    ${thumb}
    <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
      ${cat} ${resCount}
    </div>
    <div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:3px;">${types}</div>
    ${cas}
    ${tuning}
    <div style="clear:both;"></div>
  </div>`;
}

function renderFileRow(f, gi) {
  const exists = f.exists ? '' : ' <span class="pill">fehlt</span>';
  const showFull = document.getElementById('show_full').checked;

  const rel = f.rel && f.rel !== f.path ? f.rel : f.path;
  const mainLine = rel ? rel : f.path;
  const fullLine = (rel && showFull)
    ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
    : '';

  // Creator badge
  const fname = (f.path || '').split(/[\\/]/).pop();
  const creator = detectCreator(fname);
  const creatorBadge = creator
    ? `<a href="${esc(creator.url)}" target="_blank" rel="noopener" class="pill" style="background:#312e81;color:#a5b4fc;text-decoration:none;cursor:pointer;" title="Mod von ${esc(creator.name)} — Klicken für Website">${creator.icon} ${esc(creator.name)}</a>`
    : '';
  const cfBadge = renderCurseForgeUI(f.path);

  const btns = `
    <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
    <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
    <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
    <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
  `;

  const checked = selected.has(f.path) ? 'checked' : '';

  return `
  <div class="file" data-gi="${gi}">
    <div class="row1">
      <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" data-gi="${gi}" ${checked}>
      <span class="tag">${esc(f.root_label)}</span>
      <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
      <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
      ${creatorBadge}
      ${cfBadge}
      ${exists}
    </div>
    <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
    ${fullLine}
    ${renderDeepInfo(f, gi)}
    ${renderTagsUI(f.path)}
    <div class="flex" style="margin-top:10px;">${btns}</div>
  </div>`;
}

function groupByModFolder(files) {
  const map = new Map();
  for (const f of files) {
    const k = (f.mod_folder || '(Mods-Root)').trim() || '(Mods-Root)';
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(f);
  }
  return Array.from(map.entries()).sort((a,b)=> a[0].localeCompare(b[0]));
}

function isGroupIgnored(g, data) {
  const ignored = data.ignored_groups || [];
  const entry = g.type + '::' + g.key;
  return ignored.includes(entry);
}

function renderGroups(data) {
  const term = document.getElementById('q').value.trim().toLowerCase();
  const showName = document.getElementById('f_name').checked;
  const showContent = document.getElementById('f_content').checked;
  const showSimilar = document.getElementById('f_similar').checked;
  const showIgnored = document.getElementById('f_show_ignored').checked;
  const groupMod = document.getElementById('g_mod').checked;

  const out = [];
  for (let gi = 0; gi < data.groups.length; gi++) {
    const g = data.groups[gi];

    if (g.type === 'name' && !showName) continue;
    if (g.type === 'content' && !showContent) continue;
    if (g.type === 'similar' && !showSimilar) continue;

    const ignored = isGroupIgnored(g, data);
    if (ignored && !showIgnored) continue;

    const hay = (g.type + ' ' + g.key + ' ' + g.key_short + ' ' + g.files.map(x => x.path).join(' '));
    if (!matchesFilters(hay, term)) continue;

    const keepPath = preferKeepPath(g.files);
    const keepHint = keepPath ? `<span class="pill">behalte: ${esc(keepPath.split(/[\\/]/).pop())}</span>` : '';

    let inner = '';
    // Ähnlich-Gruppen: Cluster-Darstellung (identische Dateien sub-gruppieren)
    if (g.type === 'similar' && !groupMod) {
      const clusterHtml = renderClusters(g.files, gi);
      if (clusterHtml) {
        inner = clusterHtml;
      } else {
        inner = g.files.map(f => renderFileRow(f, gi)).join('');
      }
    } else if (groupMod) {
      const grouped = groupByModFolder(g.files);
      for (const [mod, files] of grouped) {
        const roots = [...new Set(files.map(f => f.root_label))].join(', ');
        inner += `<div class="subhead">📦 ${esc(roots)} / ${esc(mod)} <span class="pill">${files.length} Datei(en)</span></div>`;
        inner += files.map(f => renderFileRow(f, gi)).join('');
      }
    } else {
      inner = g.files.map(f => renderFileRow(f, gi)).join('');
    }

    const tools = `
      <div class="flex" style="margin:8px 0 2px 0;">
        <button class="btn" style="background:#1e293b;color:#c084fc;border:1px solid #7c3aed;" onclick="openCompareGallery(${gi})" title="Zeigt alle Vorschaubilder dieser Gruppe nebeneinander zum Vergleichen">🖼️ Bilder vergleichen</button>
        <button class="btn btn-ghost" data-gact="select_all" data-gi="${gi}" title="Setzt bei allen Dateien dieser Gruppe ein Häkchen">✅ Alle markieren</button>
        <button class="btn btn-ghost" data-gact="select_rest" data-gi="${gi}" title="Markiert alle außer der empfohlenen Datei">✅ Rest markieren (1 behalten)</button>
        <button class="btn btn-ok" data-gact="quarantine_rest" data-gi="${gi}" title="Verschiebt alle bis auf die beste Datei sicher in Quarantäne">📦 Rest in Quarantäne</button>
        <button class="btn btn-danger" data-gact="delete_rest" data-gi="${gi}" title="Löscht alle bis auf die beste — kann nicht rückgängig gemacht werden!">🗑 Rest löschen</button>
        ${ignored
          ? `<button class="btn" style="background:#065f46;color:#6ee7b7;border:1px solid #059669;" data-gact="unignore_group" data-gi="${gi}" data-gkey="${esc(g.key)}" data-gtype="${esc(g.type)}" title="Diese Gruppe wird wieder als potentielles Problem gezählt">↩️ Wieder melden</button>`
          : `<button class="btn" style="background:#1e3a5f;color:#60a5fa;border:1px solid #2563eb;" data-gact="ignore_group" data-gi="${gi}" data-gkey="${esc(g.key)}" data-gtype="${esc(g.type)}" title="Markiert diese Gruppe als 'Ist korrekt' — wird nicht mehr als Problem gezählt">✅ Ist korrekt</button>`
        }
        ${keepHint}
      </div>
    `;

    // Deep comparison bar for similar groups
    let deepCompBar = '';
    if (g.type === 'similar' && g.deep_comparison) {
      const dc = g.deep_comparison;
      const icon = dc.recommendation === 'update' ? '⬆️' : dc.recommendation === 'different' ? '✅' : '❓';
      const recClass = dc.recommendation === 'update' ? 'background:#451a03;border-color:#f59e0b;'
        : dc.recommendation === 'different' ? 'background:#052e16;border-color:#22c55e;'
        : 'background:#1e1b4b;border-color:#8b5cf6;';
      deepCompBar = `
      <div style="margin:8px 0;padding:10px 14px;${recClass}border:1px solid;border-radius:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
          <span style="font-size:22px;font-weight:bold;color:${dc.recommendation_color};">${dc.overlap_pct}%</span>
          <span style="color:#9ca3af;font-size:13px;">Überlappung der Resource-Keys (${dc.shared_keys} von ${dc.total_keys} geteilt)</span>
        </div>
        <div style="background:#334155;border-radius:4px;height:8px;overflow:hidden;">
          <div style="background:${dc.recommendation_color};width:${Math.min(dc.overlap_pct,100)}%;height:100%;border-radius:4px;transition:width 0.5s;"></div>
        </div>
        <div style="margin-top:8px;color:${dc.recommendation_color};font-weight:bold;font-size:13px;">
          ${icon} ${esc(dc.recommendation_text)}
        </div>
        <div style="margin-top:4px;color:#9ca3af;font-size:11px;">
          ${dc.recommendation === 'update'
            ? '💡 Die Dateien teilen die meisten Resource-Keys → es handelt sich um dasselbe Item in verschiedenen Versionen.'
            : dc.recommendation === 'different'
            ? '💡 Die Dateien teilen kaum Resource-Keys → es sind verschiedene Items (z.B. verschiedene Kleidungsstücke).'
            : '💡 Teilweise Überlappung — könnte ein Update mit geändertem Inhalt sein, oder ähnliche aber verschiedene Items.'}
        </div>
      </div>`;
    }

    const colorClass = 'color-' + (gi % 6);
    const ignoredClass = ignored ? ' grp-ignored' : '';
    const ignoredBadge = ignored ? '<span class="pill" style="background:#065f46;color:#6ee7b7;border:1px solid #059669;margin-left:6px;">✅ Ignoriert</span>' : '';
    out.push(`<details class="grp ${colorClass}${ignoredClass}">
      <summary>${fmtGroupHeader(g)}${ignoredBadge}</summary>
      <div class="files">${tools}${deepCompBar}${inner}</div>
    </details>`);
  }
  return out.length ? out.join('') : '<p class="muted">Keine Treffer (Filter/Suche?).</p>';
}

function renderSummary(data) {
  const s = data.summary;
  const corruptInfo = s.corrupt_count ? `<br>⚠️ Korrupte .package-Dateien: <b style="color:#ef4444;">${s.corrupt_count}</b>` : '';
  const conflictInfo = s.conflict_count ? `<br>🔀 Ressource-Konflikte: <b style="color:#8b5cf6;">${s.conflict_count}</b> Gruppen` : '';
  const addonInfo = s.addon_count ? `<br>🧩 Addon-Beziehungen: <b style="color:#6ee7b7;">${s.addon_count}</b> (OK — erwartet)` : '';
  const outdatedInfo = s.outdated_count ? `<br>⏰ Vor letztem Patch geändert: <b style="color:#fbbf24;">${s.outdated_count}</b> Mods` : '';
  const ignoredGrp = countIgnoredGroups(data);
  const ignoredLabel = ignoredGrp ? ` <span style="color:#6ee7b7;">(${ignoredGrp} ignoriert)</span>` : '';
  return `
    Erstellt: <b>${esc(data.created_at)}</b><br>
    Gruppen: <b>${s.groups_name}</b> Name / <b>${s.groups_content}</b> Inhalt / <b>${s.groups_similar || 0}</b> Ähnlich${ignoredLabel}<br>
    Einträge: <b>${s.entries_total}</b><br>
    Verschwendeter Speicher (identische Duplikate): <b>${esc(s.wasted_h)}</b>
    ${corruptInfo}
    ${conflictInfo}
    ${addonInfo}
    ${outdatedInfo}
  `;
}

function renderRoots(data) {
  return data.roots.map(r => `<li><b>${esc(r.label)}:</b> <code>${esc(r.path)}</code></li>`).join('');
}

function renderCorrupt(data) {
  const section = document.getElementById('corrupt-section');
  const list = data.corrupt || [];
  if (list.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  // Zusammenfassung nach Status
  const byStatus = {};
  for (const c of list) {
    byStatus[c.status_label] = (byStatus[c.status_label] || 0) + 1;
  }
  const summaryParts = Object.entries(byStatus).map(([k,v]) => `<b>${v}</b> ${esc(k)}`).join(', ');
  document.getElementById('corrupt-summary').innerHTML = `${list.length} Datei(en) gefunden: ${summaryParts}`;

  const cards = list.map(c => {
    const isWarn = c.status === 'wrong_version';
    const checked = selected.has(c.path) ? 'checked' : '';
    return `<div class="corrupt-card${isWarn ? ' warn' : ''}">
      <div>
        <input class="sel selbox" type="checkbox" data-path="${esc(c.path)}" ${checked} style="margin-right:8px;">
        <span class="corrupt-status ${esc(c.status)}">${esc(c.status_label)}</span>
        <span style="margin-left:8px; font-weight:bold;">${esc(c.rel || c.path)}</span>
        <span class="muted small" style="margin-left:8px;">${esc(c.size_h)} | ${esc(c.mtime)}</span>
        <div class="muted small" style="margin-top:4px;">${esc(c.status_hint)}</div>
        ${renderTagsUI(c.path)}
      </div>
      <div>
        <button class="btn btn-danger" style="font-size:12px;" onclick="doQuarantine('${esc(c.path).replace(/'/g,"\\'")}')">📦 Quarantäne</button>
      </div>
    </div>`;
  }).join('');
  document.getElementById('corrupt-list').innerHTML = cards;
}

function renderAddons(data) {
  const section = document.getElementById('addon-section');
  const list = data.addon_pairs || [];
  if (list.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  document.getElementById('addon-summary').innerHTML =
    `<span class="addon-ok">✅ ${list.length} Addon-Paar(e)</span> erkannt — diese gehören zusammen und sind kein Problem.`;

  const cards = list.map((c, i) => {
    const colorClass = 'color-' + (i % 6);

    const fileRows = c.files.map(f => {
      const showFull = document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';
      return `<div class="file" style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label)}</span>
          <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:4px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${renderTagsUI(f.path)}
        <div class="flex" style="margin-top:8px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    const typePills = c.top_types.map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    return `<details class="grp ${colorClass}" style="margin-bottom:8px;">
      <summary style="cursor:pointer;">
        <span class="addon-badge">${c.shared_count} geteilte Keys</span>
        <span class="addon-ok">✅ Addon</span>
        <span class="muted small" style="margin-left:8px;">${c.files.map(f => esc((f.rel||f.path).split(/[\\\\/]/).pop())).join(' ↔ ')}</span>
      </summary>
      <div style="margin-top:8px;">
        <div class="conflict-types" style="margin-bottom:8px;">Geteilte Typen: ${typePills}</div>
        <div class="muted small" style="margin-bottom:8px; color:#6ee7b7;">👍 Diese Dateien gehören zusammen — beide behalten!</div>
        ${fileRows}
      </div>
    </details>`;
  }).join('');
  document.getElementById('addon-list').innerHTML = cards;
}

function renderConflicts(data) {
  const section = document.getElementById('conflict-section');
  const list = data.conflicts || [];
  if (list.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  document.getElementById('conflict-summary').innerHTML =
    `<b>${list.length}</b> Konflikt-Gruppe(n) gefunden.`;

  const cards = list.map((c, i) => {
    const colorClass = 'color-' + (i % 6);

    // Prüfe ob Dateinamen ähnlich sind (gleicher Creator/Mod-Prefix)
    const fnames = c.files.map(f => (f.rel||f.path).split(/[\\\\/]/).pop().replace(/\.[^.]+$/, '').toLowerCase());
    let commonPrefix = fnames[0] || '';
    for (let fi = 1; fi < fnames.length; fi++) {
      let j = 0;
      while (j < commonPrefix.length && j < fnames[fi].length && commonPrefix[j] === fnames[fi][j]) j++;
      commonPrefix = commonPrefix.substring(0, j);
    }
    commonPrefix = commonPrefix.replace(/[_\-\s!.+]+$/, '');
    const namesRelated = commonPrefix.length >= 5;

    const relatedHint = namesRelated
      ? `<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px 12px; margin-bottom:10px;">
          <span style="color:#60a5fa; font-weight:bold;">ℹ️ Hinweis:</span>
          <span class="muted"> Diese Dateien haben sehr ähnliche Namen (<b>${esc(commonPrefix)}…</b>) und gehören wahrscheinlich zusammen (z.B. verschiedene Teile desselben Mods). In dem Fall ist der Konflikt normal und gewollt — beide behalten!</span>
        </div>`
      : '';

    const fileRows = c.files.map(f => {
      const showFull = document.getElementById('show_full').checked;
      const rel = f.rel && f.rel !== f.path ? f.rel : '';
      const mainLine = rel ? rel : f.path;
      const fullLine = (rel && showFull)
        ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
        : '';
      const checked = selected.has(f.path) ? 'checked' : '';
      return `<div class="file" style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div class="row1">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="tag">${esc(f.root_label)}</span>
          <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
          <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
        </div>
        <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
        ${fullLine}
        ${renderTagsUI(f.path)}
        <div class="flex" style="margin-top:10px;">
          <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
          <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
          <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
          <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
        </div>
      </div>`;
    }).join('');

    const typePills = c.top_types.map(([name, count]) =>
      `<span class="conflict-type-pill">${esc(name)}: ${count}</span>`
    ).join('');

    // Empfehlung: neueste behalten
    let newest = c.files[0];
    for (const f of c.files) {
      if (f.mtime > newest.mtime) newest = f;
    }
    const keepName = (newest.rel || newest.path).split(/[\\\\/]/).pop();

    return `<details class="grp ${colorClass}" style="margin-bottom:8px;">
      <summary style="cursor:pointer;">
        <span class="conflict-badge">${c.shared_count} geteilte Keys</span>
        <span class="pill">${c.files.length} Packages</span>
        <span class="muted small" style="margin-left:8px;">${c.files.map(f => esc((f.rel||f.path).split(/[\\\\/]/).pop())).join(' ↔ ')}</span>
      </summary>
      <div style="margin-top:8px;">
        <div class="conflict-types" style="margin-bottom:8px;">Häufigste Typen: ${typePills}</div>
        ${relatedHint}
        <div class="muted small" style="margin-bottom:8px;">💡 Empfehlung: <b>${esc(keepName)}</b> behalten (neuster Stand: ${esc(newest.mtime)})</div>
        <div class="flex" style="margin-bottom:8px;">
          <button class="btn btn-ok" data-conflict-rest="${i}">📦 Rest in Quarantäne (neueste behalten)</button>
        </div>
        ${fileRows}
      </div>
    </details>`;
  }).join('');
  document.getElementById('conflict-list').innerHTML = cards;

  // Event-Delegation für "Rest in Quarantäne"-Buttons
  document.getElementById('conflict-list').querySelectorAll('[data-conflict-rest]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const ci = parseInt(e.target.dataset.conflictRest);
      const c = list[ci];
      if (!c) return;
      let newest = c.files[0];
      for (const f of c.files) { if (f.mtime > newest.mtime) newest = f; }
      const rest = c.files.filter(f => f.path !== newest.path);
      const keepFile = (newest.rel||newest.path).split(/[\\\\/]/).pop();
      const removeFiles = rest.map(f=>(f.rel||f.path).split(/[\\\\/]/).pop()).join('\\n');
      if (!confirm('📦 ' + rest.length + ' Datei(en) in Quarantäne verschieben?\\n\\nBehalte: ' + keepFile + '\\n\\nEntferne:\\n' + removeFiles)) return;
      for (const f of rest) {
        await doQuarantine(f.path);
      }
    });
  });
}

// ---- Per-File Ansicht ----
function buildPerFileMap(data) {
  // Sammle ALLE Findings pro Dateipfad
  const map = new Map(); // path -> { file, findings: [] }

  function ensure(f) {
    if (!map.has(f.path)) {
      map.set(f.path, { file: f, findings: [] });
    }
    return map.get(f.path);
  }

  // Gruppen (Name/Inhalt/Ähnlich)
  for (const g of (data.groups || [])) {
    const typeLabel = g.type === 'name' ? 'Name-Duplikat' : g.type === 'content' ? 'Inhalt-Duplikat' : 'Ähnlicher Name';
    const typeClass = g.type === 'name' ? 'pf-name-dupe' : g.type === 'content' ? 'pf-content-dupe' : 'pf-similar-dupe';
    const partners = g.files.map(f => f.path);
    for (const f of g.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'group',
        type: g.type,
        typeLabel,
        typeClass,
        key: g.key_short,
        sizeEach: g.size_each,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: g.files.filter(x => x.path !== f.path),
      });
    }
  }

  // Korrupte
  for (const c of (data.corrupt || [])) {
    const entry = ensure(c);
    entry.findings.push({
      category: 'corrupt',
      typeLabel: 'Korrupt',
      typeClass: 'pf-corrupt',
      statusLabel: c.status_label,
      statusHint: c.status_hint,
      status: c.status,
    });
  }

  // Addon-Paare
  for (const a of (data.addon_pairs || [])) {
    const partners = a.files.map(f => f.path);
    for (const f of a.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'addon',
        typeLabel: 'Addon-Beziehung',
        typeClass: 'pf-addon',
        sharedCount: a.shared_count,
        topTypes: a.top_types,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: a.files.filter(x => x.path !== f.path),
      });
    }
  }

  // Konflikte
  for (const c of (data.conflicts || [])) {
    const partners = c.files.map(f => f.path);
    for (const f of c.files) {
      const entry = ensure(f);
      entry.findings.push({
        category: 'conflict',
        typeLabel: 'Ressource-Konflikt',
        typeClass: 'pf-conflict',
        sharedCount: c.shared_count,
        topTypes: c.top_types,
        partners: partners.filter(p => p !== f.path),
        partnerFiles: c.files.filter(x => x.path !== f.path),
      });
    }
  }

  return map;
}

function countIgnoredGroups(data) {
  const ignored = data.ignored_groups || [];
  let count = 0;
  for (const g of (data.groups || [])) {
    if (ignored.includes(g.type + '::' + g.key)) count++;
  }
  return count;
}

function updateNavBadges(data) {
  const s = data.summary || {};
  const ignoredCount = countIgnoredGroups(data);
  const groups = (s.groups_name||0) + (s.groups_content||0) + (s.groups_similar||0) - ignoredCount;
  const corrupt = s.corrupt_count || 0;
  const addon = s.addon_count || 0;
  const conflict = s.conflict_count || 0;
  const outdated = s.outdated_count || 0;
  const deps = s.dependency_count || 0;

  document.getElementById('nav-badge-groups').textContent = groups;
  document.getElementById('nav-badge-corrupt').textContent = corrupt;
  document.getElementById('nav-badge-addon').textContent = addon;
  document.getElementById('nav-badge-conflict').textContent = conflict;
  document.getElementById('nav-badge-outdated').textContent = outdated;
  document.getElementById('nav-badge-deps').textContent = deps;

  document.getElementById('nav-corrupt').classList.toggle('nav-hidden', corrupt === 0);
  document.getElementById('nav-addon').classList.toggle('nav-hidden', addon === 0);
  document.getElementById('nav-conflict').classList.toggle('nav-hidden', conflict === 0);
  document.getElementById('nav-outdated').classList.toggle('nav-hidden', outdated === 0);
  document.getElementById('nav-deps').classList.toggle('nav-hidden', deps === 0);

  // --- Dashboard-Karten aktualisieren ---
  const totalFiles = s.total_files || 0;
  const wastedMB = s.wasted_h || '';

  // Korrupte
  document.getElementById('dash-corrupt-count').textContent = corrupt;
  document.getElementById('dash-corrupt').classList.toggle('dash-hidden', corrupt === 0);

  // Duplikate
  document.getElementById('dash-dupes-count').textContent = groups;
  const dupeDesc = document.querySelector('#dash-dupes .dash-desc');
  if (groups === 0 && ignoredCount === 0) {
    dupeDesc.innerHTML = '<b style="color:#4ade80;">✅ Keine Duplikate gefunden!</b> Alles sauber.';
    document.getElementById('dash-dupes').className = 'dash-card dash-ok';
  } else if (groups === 0 && ignoredCount > 0) {
    dupeDesc.innerHTML = '<b style="color:#4ade80;">✅ Alle ' + ignoredCount + ' Gruppen als korrekt markiert.</b>';
    document.getElementById('dash-dupes').className = 'dash-card dash-ok';
  } else {
    const ignoredHint = ignoredCount > 0 ? ' <span style="color:#6ee7b7;">(' + ignoredCount + ' ignoriert)</span>' : '';
    dupeDesc.innerHTML = 'Doppelte oder sehr ähnliche Mod-Dateien.' + (wastedMB ? ' <b>' + esc(wastedMB) + ' verschwendet.</b>' : '') + ignoredHint + ' Aufräumen empfohlen.';
  }

  // Konflikte
  document.getElementById('dash-conflicts-count').textContent = conflict;
  document.getElementById('dash-conflicts').classList.toggle('dash-hidden', conflict === 0);

  // Veraltet
  document.getElementById('dash-outdated-count').textContent = outdated;
  document.getElementById('dash-outdated').classList.toggle('dash-hidden', outdated === 0);

  // Addons
  document.getElementById('dash-addons-count').textContent = addon;
  document.getElementById('dash-addons').classList.toggle('dash-hidden', addon === 0);

  // Sonstige Dateien
  const nonmod = s.non_mod_count || 0;
  document.getElementById('nav-badge-nonmod').textContent = nonmod;
  document.getElementById('nav-nonmod').classList.toggle('nav-hidden', nonmod === 0);
  document.getElementById('dash-nonmod-count').textContent = nonmod;
  document.getElementById('dash-nonmod').classList.toggle('dash-hidden', nonmod === 0);

  // Gesamt
  document.getElementById('dash-total-count').textContent = totalFiles;
}

// ---- Sonstige Dateien (Nicht-Mod-Dateien) ----
function renderNonModFiles(data) {
  const nonmod = data.non_mod_files || [];
  const byExt = data.non_mod_by_ext || [];
  const section = document.getElementById('nonmod-section');
  const list = document.getElementById('nonmod-list');
  const summary = document.getElementById('nonmod-summary');
  if (!nonmod.length) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';
  const totalSize = nonmod.reduce((a, f) => a + (f.size || 0), 0);
  summary.innerHTML = `<b>${nonmod.length}</b> Dateien — ${humanSize(totalSize)} belegt`;
  let html = '';
  // Gruppiert nach Dateityp
  const extIcons = {'.txt':'📝', '.png':'🖼️', '.jpg':'🖼️', '.jpeg':'🖼️', '.gif':'🖼️', '.bmp':'🖼️',
    '.html':'🌐', '.htm':'🌐', '.log':'📋', '.cfg':'⚙️', '.ini':'⚙️', '.json':'📊', '.xml':'📊',
    '.dat':'💾', '.tmbin':'🔧', '.tmcatalog':'🔧', '.mp4':'🎬', '.avi':'🎬', '.mov':'🎬',
    '.mp3':'🎵', '.wav':'🎵', '.pdf':'📕', '.doc':'📕', '.docx':'📕', '.zip':'📦', '.7z':'📦', '.rar':'📦'};
  const extLabels = {'.txt':'Text-Dateien', '.png':'PNG-Bilder', '.jpg':'JPEG-Bilder', '.html':'HTML-Dateien',
    '.htm':'HTML-Dateien', '.log':'Log-Dateien', '.cfg':'Konfiguration', '.ini':'Einstellungen',
    '.json':'JSON-Daten', '.xml':'XML-Daten', '.dat':'Datendateien', '.tmbin':'TurboDriver-Daten',
    '.tmcatalog':'TurboDriver-Katalog', '.mp4':'Videos', '.gif':'GIF-Bilder', '.pdf':'PDF-Dokumente',
    '.7z':'Archive', '.rar':'Archive', '.zip':'Archive'};
  for (const [ext, files] of byExt) {
    const icon = extIcons[ext] || '📄';
    const label = extLabels[ext] || (ext ? ext.toUpperCase().substring(1) + '-Dateien' : 'Ohne Endung');
    const extSize = files.reduce((a, f) => a + (f.size || 0), 0);
    html += `<details style="margin-bottom:6px;"><summary style="cursor:pointer;padding:6px 10px;background:#1e293b;border-radius:6px;border:1px solid #334155;font-size:13px;">`;
    html += `${icon} <b>${esc(label)}</b> <span class="muted">(${files.length} Dateien, ${humanSize(extSize)})</span></summary>`;
    html += `<div style="padding:6px 0 6px 16px;">`;
    for (const f of files) {
      html += `<div style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px;border-bottom:1px solid #1e293b;">`;
      html += `<span style="flex:1;word-break:break-all;" title="${esc(f.path)}">${esc(f.rel || f.name)}</span>`;
      html += `<span class="muted" style="flex-shrink:0;">${esc(f.mod_folder)}</span>`;
      html += `<span class="muted" style="flex-shrink:0;width:70px;text-align:right;">${esc(f.size_h)}</span>`;
      html += `</div>`;
    }
    html += `</div></details>`;
  }
  list.innerHTML = html;
}

// ---- Bekannte Mod-Ersteller ----
const KNOWN_CREATORS = {
  'wickedwhims': {name: 'TURBODRIVER', url: 'https://wickedwhimsmod.com/', icon: '🔞'},
  'wonderfulwhims': {name: 'TURBODRIVER', url: 'https://wonderfulwhims.com/', icon: '💕'},
  'mccc': {name: 'Deaderpool', url: 'https://deaderpool-mccc.com/downloads.html', icon: '🎮'},
  'mc_cmd': {name: 'Deaderpool (MCCC)', url: 'https://deaderpool-mccc.com/downloads.html', icon: '🎮'},
  'littlemssam': {name: 'LittleMsSam', url: 'https://lms-mods.com/', icon: '🌸'},
  'basemental': {name: 'Basemental', url: 'https://basementalcc.com/', icon: '💊'},
  'kawaiistacie': {name: 'KawaiiStacie', url: 'https://www.patreon.com/kawaiistacie', icon: '🌈'},
  'sacrificial': {name: 'Sacrificial', url: 'https://sacrificialmods.com/', icon: '🔪'},
  'kuttoe': {name: 'Kuttoe', url: '', icon: '🏠'},
  'zerbu': {name: 'Zerbu', url: 'https://zerbu.tumblr.com/', icon: '🏗️'},
  'tmex': {name: 'TwistedMexi', url: 'https://twistedmexi.com/', icon: '🔧'},
  'twistedmexi': {name: 'TwistedMexi', url: 'https://twistedmexi.com/', icon: '🔧'},
  'simrealist': {name: 'SimRealist', url: 'https://simrealist.itch.io/', icon: '🏥'},
  'lumpinou': {name: 'Lumpinou', url: 'https://lumpinoumods.com/', icon: '💝'},
  'coldsims': {name: 'ColdSims', url: '', icon: '❄️'},
  'ravasheen': {name: 'Ravasheen', url: 'https://ravasheen.com/', icon: '✨'},
  'ilkavelle': {name: 'IlkaVelle', url: '', icon: '🎨'},
  'simscommunitylib': {name: 'Sims4CommunityLib', url: 'https://github.com/ColonolNutty/Sims4CommunityLibrary', icon: '📚'},
  's4cl': {name: 'Sims4CommunityLib', url: 'https://github.com/ColonolNutty/Sims4CommunityLibrary', icon: '📚'},
  'bienchen': {name: 'Bienchen', url: '', icon: '🐝'},
  'scarletredesign': {name: 'ScarletReDesign', url: '', icon: '🎨'},
  'helaene': {name: 'Helaene', url: '', icon: '✂️'},
  'aretha': {name: 'Aretha', url: '', icon: '👗'},
  'adeepindigo': {name: 'ADeepIndigo', url: '', icon: '🎨'},
  'kiara': {name: 'Kiara Zurk', url: '', icon: '💇'},
  'simpledimples': {name: 'SimpleDimples', url: '', icon: '👶'},
  'arethabee': {name: 'Aretha', url: '', icon: '👗'},
};

// Custom creators (from server, merged at runtime)
let CUSTOM_CREATORS = {};

// CurseForge-Daten (from Overwolf manifest)
let CURSEFORGE_DATA = {};  // normpath -> {name, author, url, has_update, ...}
let _CF_CACHE = {};  // fast lookup cache: short-key -> info

// Vorberechnete Such-Indizes (werden bei Datenänderung neu gebaut)
let _CATEGORY_INDEX = {};   // path -> ['📛 Name-Duplikat', ...]
let _SEARCH_HAY_CACHE = {}; // path -> lowercase haystack string
let _SEARCH_INDEX_DIRTY = true;

// Mod-Notizen & Tags (from server, persistent)
let MOD_NOTES = {};
let MOD_TAGS = {};
const AVAILABLE_TAGS = [
  {name: 'Wichtig', color: '#dc2626', bg: '#7f1d1d'},
  {name: 'Favorit', color: '#f59e0b', bg: '#78350f'},
  {name: 'Testen', color: '#3b82f6', bg: '#1e3a5f'},
  {name: 'CAS/CC', color: '#ec4899', bg: '#831843'},
  {name: 'Build/Buy', color: '#8b5cf6', bg: '#4c1d95'},
  {name: 'Gameplay', color: '#10b981', bg: '#065f46'},
  {name: 'Veraltet', color: '#f97316', bg: '#9a3412'},
  {name: 'Behalten', color: '#22c55e', bg: '#14532d'},
  {name: 'Entfernen', color: '#ef4444', bg: '#7f1d1d'},
  {name: 'Script', color: '#06b6d4', bg: '#164e63'},
];

function detectCreator(filename) {
  const lower = (filename || '').toLowerCase();
  // Custom creators have priority
  for (const [key, info] of Object.entries(CUSTOM_CREATORS)) {
    if (lower.includes(key)) return {...info, custom: true, key};
  }
  for (const [key, info] of Object.entries(KNOWN_CREATORS)) {
    if (lower.includes(key)) return {...info, custom: false, key};
  }
  return null;
}

// ---- Creator-Verwaltung ----
async function loadCreators() {
  try {
    const r = await fetch('/api/creators?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) CUSTOM_CREATORS = j.creators || {};
  } catch(e) { console.error('[CREATORS]', e); }
  renderCreatorsList();
}

async function loadNotes() {
  try {
    const r = await fetch('/api/notes?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) MOD_NOTES = j.notes || {};
  } catch(e) { console.error('[NOTES]', e); }
}

async function loadTags() {
  try {
    const r = await fetch('/api/tags?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) MOD_TAGS = j.tags || {};
  } catch(e) { console.error('[TAGS]', e); }
}

async function loadCurseForge() {
  try {
    const r = await fetch('/api/curseforge?token=' + TOKEN);
    const j = await r.json();
    if (j.ok) {
      CURSEFORGE_DATA = j.curseforge || {};
      _buildCFCache();
      _SEARCH_INDEX_DIRTY = true;
    }
  } catch(e) { console.error('[CURSEFORGE]', e); }
}

// Baut den CurseForge-Cache (einmal nach loadCurseForge)
function _buildCFCache() {
  _CF_CACHE = {};
  for (const [k, v] of Object.entries(CURSEFORGE_DATA)) {
    _CF_CACHE[k] = v;  // full norm path
    // Kurzschlüssel: letzte 2 Pfad-Teile
    const parts = k.split('\\');
    if (parts.length >= 2) {
      _CF_CACHE[parts.slice(-2).join('\\')] = v;
    }
    // Nur Dateiname als letzter Fallback
    if (parts.length >= 1) {
      const fn = parts[parts.length - 1];
      if (!_CF_CACHE[fn]) _CF_CACHE[fn] = v;  // first-wins für Dateinamen
    }
  }
}

function getCurseForgeInfo(filePath) {
  if (!filePath || !CURSEFORGE_DATA) return null;
  const norm = filePath.replace(/\//g, '\\').toLowerCase();
  // O(1) Lookup: Vollpfad
  if (_CF_CACHE[norm]) return _CF_CACHE[norm];
  // O(1) Lookup: letzte 2 Teile
  const parts = norm.split('\\');
  if (parts.length >= 2) {
    const short = parts.slice(-2).join('\\');
    if (_CF_CACHE[short]) return _CF_CACHE[short];
  }
  // O(1) Lookup: nur Dateiname
  if (parts.length >= 1 && _CF_CACHE[parts[parts.length - 1]]) {
    return _CF_CACHE[parts[parts.length - 1]];
  }
  return null;
}

function renderCurseForgeUI(filePath) {
  const cf = getCurseForgeInfo(filePath);
  if (!cf) return '';
  let badge = `<a href="${esc(cf.url)}" target="_blank" rel="noopener" class="pill" style="background:#f16436;color:#fff;text-decoration:none;cursor:pointer;font-size:10px;" title="Installiert über CurseForge\nMod: ${esc(cf.name)}\nAutor: ${esc(cf.author)}">🔥 CurseForge</a>`;
  if (cf.has_update) {
    badge += ` <span class="pill" style="background:#065f46;color:#22c55e;font-size:10px;cursor:pointer;" title="Update verfügbar!\nNeue Version: ${esc(cf.latest_version || '?')}\nDatei: ${esc(cf.latest_file_name || '?')}" onclick="if(confirm('Update für ${esc(cf.name).replace(/'/g, '\\\'')} öffnen?')) window.open('${esc(cf.url)}', '_blank')">⬆️ Update</span>`;
  }
  return badge;
}

async function saveNote(path, note) {
  try {
    await postAction('save_note', path, {note});
    MOD_NOTES[path] = note;
    if (!note) delete MOD_NOTES[path];
  } catch(e) { console.error('[SAVE_NOTE]', e); }
}

async function addTag(path, tag) {
  try {
    const res = await postAction('add_tag', path, {tag});
    MOD_TAGS[path] = res.tags || [];
  } catch(e) { console.error('[ADD_TAG]', e); }
}

async function removeTag(path, tag) {
  try {
    const res = await postAction('remove_tag', path, {tag});
    MOD_TAGS[path] = res.tags || [];
    if (MOD_TAGS[path].length === 0) delete MOD_TAGS[path];
  } catch(e) { console.error('[REMOVE_TAG]', e); }
}

function renderNotesUI(path) {
  const note = MOD_NOTES[path] || '';
  const hasNote = !!note;
  const safePath = btoa(unescape(encodeURIComponent(path)));
  return `<div class="note-area" data-note-path="${esc(path)}" data-note-b64="${safePath}">
    ${hasNote
      ? `<div class="note-display" onclick="this.style.display='none'; this.nextElementSibling.style.display='block'; this.nextElementSibling.querySelector('textarea').focus();" title="Klicken zum Bearbeiten">
          <span>📝</span><span>${esc(note)}</span>
        </div>
        <div style="display:none;">
          <textarea class="note-input" placeholder="Notiz schreiben…">${esc(note)}</textarea>
          <div class="flex" style="margin-top:4px; gap:4px;">
            <button class="note-btn note-btn-save" data-note-action="save">💾 Speichern</button>
            <button class="note-btn" data-note-action="delete">🗑</button>
            <button class="note-btn" data-note-action="cancel">Abbrechen</button>
          </div>
        </div>`
      : `<button class="note-btn" data-note-action="open" title="Notiz hinzufügen" style="font-size:11px;">📝 Notiz</button>`
    }
  </div>`;
}

function renderTagsUI(path) {
  const fileTags = MOD_TAGS[path] || [];
  const safePath = btoa(unescape(encodeURIComponent(path)));
  let html = '<div class="mod-tags-area" data-tags-path="' + esc(path) + '" data-tags-b64="' + safePath + '">';
  for (const t of fileTags) {
    const def = AVAILABLE_TAGS.find(at => at.name === t) || {color:'#94a3b8', bg:'#334155'};
    html += `<span class="mod-tag-pill" style="background:${def.bg};color:${def.color};">${esc(t)}<span class="tag-remove" data-tag-remove="${esc(t)}">✕</span></span>`;
  }
  html += `<span class="tag-add-btn" data-tag-add="1" title="Tag hinzufügen">🏷️ +</span>`;
  html += '</div>';
  return html;
}

function b64ToPath(b64) {
  return decodeURIComponent(escape(atob(b64)));
}

// Tag-Menü
let _tagMenuEl = null;
function showTagMenu(evt, path) {
  evt.stopPropagation();
  closeTagMenu();
  const existing = MOD_TAGS[path] || [];
  const available = AVAILABLE_TAGS.filter(t => !existing.includes(t.name));
  if (available.length === 0) return;

  const menu = document.createElement('div');
  menu.className = 'tag-menu';
  menu.style.position = 'fixed';
  menu.style.left = evt.clientX + 'px';
  menu.style.top = evt.clientY + 'px';
  for (const t of available) {
    const btn = document.createElement('button');
    btn.className = 'tag-menu-item';
    btn.style.background = t.bg;
    btn.style.color = t.color;
    btn.textContent = t.name;
    btn.onclick = async (e) => {
      e.stopPropagation();
      closeTagMenu();
      await addTag(path, t.name);
      // Re-render tags for this path
      const area = document.querySelector('[data-tags-path="' + CSS.escape(path) + '"]');
      if (area) area.outerHTML = renderTagsUI(path);
    };
    menu.appendChild(btn);
  }
  document.body.appendChild(menu);
  _tagMenuEl = menu;
  // Reposition if off screen
  setTimeout(() => {
    const r = menu.getBoundingClientRect();
    if (r.right > window.innerWidth) menu.style.left = (window.innerWidth - r.width - 8) + 'px';
    if (r.bottom > window.innerHeight) menu.style.top = (window.innerHeight - r.height - 8) + 'px';
  }, 0);
}
function closeTagMenu() {
  if (_tagMenuEl) { _tagMenuEl.remove(); _tagMenuEl = null; }
}
document.addEventListener('click', closeTagMenu);

// Event delegation for tags
document.addEventListener('click', async (ev) => {
  // Tag remove
  const removeBtn = ev.target.closest('[data-tag-remove]');
  if (removeBtn) {
    ev.stopPropagation();
    const area = removeBtn.closest('.mod-tags-area');
    const path = b64ToPath(area.dataset.tagsB64);
    const tag = removeBtn.dataset.tagRemove;
    await removeTag(path, tag);
    area.outerHTML = renderTagsUI(path);
    return;
  }
  // Tag add
  const addBtn = ev.target.closest('[data-tag-add]');
  if (addBtn) {
    const area = addBtn.closest('.mod-tags-area');
    const path = b64ToPath(area.dataset.tagsB64);
    showTagMenu(ev, path);
    return;
  }
  // Note actions
  const noteBtn = ev.target.closest('[data-note-action]');
  if (noteBtn) {
    const action = noteBtn.dataset.noteAction;
    const area = noteBtn.closest('.note-area');
    const path = b64ToPath(area.dataset.noteB64);
    if (action === 'open') {
      area.innerHTML = `
        <textarea class="note-input" placeholder="Notiz schreiben…"></textarea>
        <div class="flex" style="margin-top:4px; gap:4px;">
          <button class="note-btn note-btn-save" data-note-action="save">💾 Speichern</button>
          <button class="note-btn" data-note-action="cancel">Abbrechen</button>
        </div>`;
      area.querySelector('textarea').focus();
    } else if (action === 'save') {
      const ta = area.querySelector('textarea');
      const text = ta.value.trim();
      await saveNote(path, text);
      area.outerHTML = renderNotesUI(path);
    } else if (action === 'delete') {
      await saveNote(path, '');
      area.outerHTML = renderNotesUI(path);
    } else if (action === 'cancel') {
      area.outerHTML = renderNotesUI(path);
    }
    return;
  }
});

function renderCreatorsList() {
  const el = document.getElementById('creators-list');
  const all = {};
  // Built-in first, then custom (custom override if same key)
  for (const [k,v] of Object.entries(KNOWN_CREATORS)) all[k] = {...v, custom: false};
  for (const [k,v] of Object.entries(CUSTOM_CREATORS)) all[k] = {...v, custom: true};

  const sorted = Object.entries(all).sort((a,b) => a[1].name.localeCompare(b[1].name));
  const customCount = Object.keys(CUSTOM_CREATORS).length;
  const totalCount = sorted.length;

  let html = `<div style="margin-bottom:10px;" class="muted">${totalCount} Creator gespeichert (${customCount} eigene, ${totalCount - customCount} vorinstalliert)</div>`;
  html += '<div style="display:flex; flex-wrap:wrap; gap:6px;">';
  for (const [key, info] of sorted) {
    const urlPart = info.url
      ? `<a href="${esc(info.url)}" target="_blank" rel="noopener" style="color:#a5b4fc;text-decoration:underline;font-size:11px; margin-left:4px;" title="${esc(info.url)}">🔗</a>`
      : '';
    const editBtn = `<button class="btn-x" data-edit-creator="${esc(key)}" data-cr-name="${esc(info.name)}" data-cr-url="${esc(info.url||'')}" data-cr-icon="${esc(info.icon||'')}" data-cr-custom="${info.custom}" title="Creator bearbeiten" style="margin-left:2px;background:none;border:none;color:#facc15;cursor:pointer;font-size:12px;padding:0 2px;">✏️</button>`;
    const isOverride = info.custom && KNOWN_CREATORS.hasOwnProperty(key);
    let delBtn = '';
    if (info.custom && !isOverride) {
      delBtn = `<button class="btn-x" data-del-creator="${esc(key)}" title="Eigenen Creator-Link entfernen" style="margin-left:2px;background:none;border:none;color:#f87171;cursor:pointer;font-size:12px;padding:0 2px;">✕</button>`;
    } else if (isOverride) {
      delBtn = `<button class="btn-x" data-del-creator="${esc(key)}" title="Auf Original zurücksetzen" style="margin-left:2px;background:none;border:none;color:#38bdf8;cursor:pointer;font-size:12px;padding:0 2px;">↩️</button>`;
    }
    const bg = info.custom ? '#312e81' : '#1e293b';
    const border = info.custom ? '#6366f1' : '#334155';
    html += `<div style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:${bg};border:1px solid ${border};border-radius:16px;font-size:12px;" title="Muster: ${esc(key)}${info.url ? '\\nURL: ' + esc(info.url) : ''}">
      <span>${info.icon || '🔗'}</span>
      <span style="font-weight:600;">${esc(info.name)}</span>
      <code style="color:#6b7280;font-size:10px;">${esc(key)}</code>
      ${urlPart}${editBtn}${delBtn}
    </div>`;
  }
  html += '</div>';
  el.innerHTML = html;
}

// Form handlers
function openCreatorForm(editKey, name, url, icon) {
  const box = document.getElementById('creator-form-box');
  const title = document.getElementById('creator-form-title');
  const keyInput = document.getElementById('cr_key');
  const editMode = document.getElementById('cr_edit_mode');
  if (editKey) {
    title.textContent = '✏️ Creator bearbeiten: ' + editKey;
    keyInput.value = editKey;
    keyInput.readOnly = true;
    keyInput.style.opacity = '0.6';
    document.getElementById('cr_name').value = name || '';
    document.getElementById('cr_url').value = url || '';
    document.getElementById('cr_icon').value = icon || '';
    editMode.value = editKey;
  } else {
    title.textContent = '➕ Neuen Creator hinzufügen';
    keyInput.value = '';
    keyInput.readOnly = false;
    keyInput.style.opacity = '1';
    document.getElementById('cr_name').value = '';
    document.getElementById('cr_url').value = '';
    document.getElementById('cr_icon').value = '';
    editMode.value = '';
  }
  box.style.display = '';
  box.scrollIntoView({behavior:'smooth', block:'nearest'});
}

document.getElementById('btn_toggle_creator_form').addEventListener('click', () => {
  const box = document.getElementById('creator-form-box');
  if (box.style.display !== 'none') { box.style.display = 'none'; return; }
  openCreatorForm(null);
});
document.getElementById('btn_cancel_creator').addEventListener('click', () => {
  document.getElementById('creator-form-box').style.display = 'none';
});
document.getElementById('btn_save_creator').addEventListener('click', async () => {
  const key = document.getElementById('cr_key').value.trim().toLowerCase();
  const cname = document.getElementById('cr_name').value.trim();
  const curl = document.getElementById('cr_url').value.trim();
  const cicon = document.getElementById('cr_icon').value.trim() || '🔗';
  const editMode = document.getElementById('cr_edit_mode').value;
  if (!key || !cname) { alert('Bitte Muster und Creator-Name ausfüllen!'); return; }
  const act = editMode ? 'edit_creator' : 'add_creator';
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: act, key, cname, curl, cicon})
    });
    const j = await r.json();
    if (j.ok) {
      document.getElementById('cr_key').value = '';
      document.getElementById('cr_key').readOnly = false;
      document.getElementById('cr_key').style.opacity = '1';
      document.getElementById('cr_name').value = '';
      document.getElementById('cr_url').value = '';
      document.getElementById('cr_icon').value = '';
      document.getElementById('cr_edit_mode').value = '';
      document.getElementById('creator-form-box').style.display = 'none';
      await loadCreators();
      // Refresh file cards to show new badges
      if (window.__DATA) {
        document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
      }
    } else { alert('Fehler: ' + (j.error || 'unbekannt')); }
  } catch(e) { alert('Fehler: ' + e.message); }
});

// Edit creator (event delegation)
document.addEventListener('click', (ev) => {
  const btn = ev.target.closest('[data-edit-creator]');
  if (!btn) return;
  const key = btn.dataset.editCreator;
  const name = btn.dataset.crName;
  const url = btn.dataset.crUrl;
  const icon = btn.dataset.crIcon;
  openCreatorForm(key, name, url, icon);
});

// Delete custom creator (event delegation)
document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('[data-del-creator]');
  if (!btn) return;
  const key = btn.dataset.delCreator;
  const isOverride = KNOWN_CREATORS.hasOwnProperty(key);
  const msg = isOverride
    ? `"${key}" auf den vorinstallierten Original-Wert zurücksetzen?`
    : `Creator-Link "${key}" wirklich entfernen?`;
  if (!confirm(msg)) return;
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'delete_creator', key})
    });
    const j = await r.json();
    if (j.ok) {
      await loadCreators();
      if (window.__DATA) {
        document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
      }
    }
  } catch(e) { alert('Fehler: ' + e.message); }
});

// ---- Such-Index aufbauen (einmal nach Datenänderung) ----
function _buildSearchIndex(data) {
  if (!data) return;
  // 1. Kategorie-Index: path -> [Kategorie-Labels]
  _CATEGORY_INDEX = {};
  for (const g of (data.groups||[])) {
    const label = g.type === 'name' ? '📛 Name-Duplikat' : g.type === 'content' ? '📦 Inhalt-Duplikat' : '🔤 Ähnlich';
    for (const gf of (g.files||[])) {
      if (!_CATEGORY_INDEX[gf.path]) _CATEGORY_INDEX[gf.path] = [];
      _CATEGORY_INDEX[gf.path].push(label);
    }
  }
  for (const c of (data.corrupt||[])) {
    if (!_CATEGORY_INDEX[c.path]) _CATEGORY_INDEX[c.path] = [];
    _CATEGORY_INDEX[c.path].push('💀 Korrupt');
  }
  for (const conf of (data.conflicts||[])) {
    for (const cf2 of (conf.files||[])) {
      if (!_CATEGORY_INDEX[cf2.path]) _CATEGORY_INDEX[cf2.path] = [];
      _CATEGORY_INDEX[cf2.path].push('⚔️ Konflikt');
    }
  }
  for (const ap of (data.addon_pairs||[])) {
    for (const af of (ap.files||[])) {
      if (!_CATEGORY_INDEX[af.path]) _CATEGORY_INDEX[af.path] = [];
      _CATEGORY_INDEX[af.path].push('🧩 Addon');
    }
  }
  // 2. Haystack-Cache: path -> suchbarer String
  _SEARCH_HAY_CACHE = {};
  const allFiles = collectAllUniqueFiles(data);
  for (const f of allFiles) {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop().toLowerCase();
    const ftags = MOD_TAGS[fpath] || [];
    const fnote = MOD_NOTES[fpath] || '';
    const cfInfo = getCurseForgeInfo(fpath);
    _SEARCH_HAY_CACHE[fpath] = (fname + ' ' + (f.rel||'') + ' ' + (f.mod_folder||'') + ' ' + ftags.join(' ') + ' ' + fnote + ' ' + (cfInfo ? cfInfo.name + ' ' + cfInfo.author : '')).toLowerCase();
  }
  _SEARCH_INDEX_DIRTY = false;
}

// ---- Globale Suche ----
let _globalSearchTimer = null;
document.getElementById('global-search').addEventListener('input', function() {
  clearTimeout(_globalSearchTimer);
  _globalSearchTimer = setTimeout(globalSearch, 300);
});
document.getElementById('global-search').addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { this.value = ''; globalSearch(); }
});

function globalSearch() {
  const term = (document.getElementById('global-search').value || '').trim().toLowerCase();
  const resultsDiv = document.getElementById('global-search-results');
  const countSpan = document.getElementById('global-search-count');

  if (!term || term.length < 2) {
    resultsDiv.style.display = 'none';
    resultsDiv.innerHTML = '';
    countSpan.textContent = '';
    return;
  }

  const data = window.__DATA;
  if (!data) { countSpan.textContent = 'Kein Scan geladen'; return; }

  // Index bei Bedarf einmal aufbauen
  if (_SEARCH_INDEX_DIRTY) _buildSearchIndex(data);

  const results = [];
  const MAX = 100;
  const allFiles = collectAllUniqueFiles(data);

  for (const f of allFiles) {
    if (results.length >= MAX) break;
    const fpath = f.path || '';
    // O(1) Haystack-Lookup statt Neuberechnung
    const hay = _SEARCH_HAY_CACHE[fpath] || '';
    if (!hay.includes(term)) continue;
    // O(1) Kategorie-Lookup statt verschachtelte Schleifen
    const cats = _CATEGORY_INDEX[fpath] || ['✅ OK'];
    results.push({file: f, categories: cats, cfInfo: getCurseForgeInfo(fpath)});
  }

  countSpan.textContent = results.length >= MAX ? `${MAX}+ Treffer` : `${results.length} Treffer`;

  if (results.length === 0) {
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="muted" style="padding:12px;">Keine Treffer gefunden.</div>';
    return;
  }

  const html = results.map(r => {
    const f = r.file;
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop();
    const creator = detectCreator(fname);
    const creatorBadge = creator ? `<span class="pill" style="background:#312e81;color:#a5b4fc;font-size:10px;">${creator.icon} ${esc(creator.name)}</span>` : '';
    const cfBadge = r.cfInfo ? renderCurseForgeUI(fpath) : '';
    const catBadges = r.categories.map(c => `<span class="pill" style="font-size:10px;">${c}</span>`).join('');
    const tagBadges = (MOD_TAGS[fpath]||[]).map(t => {
      const td = AVAILABLE_TAGS.find(x => x.name === t);
      return td ? `<span class="pill" style="background:${td.bg};color:${td.color};font-size:10px;">${t}</span>` : '';
    }).join('');
    const note = MOD_NOTES[fpath];
    const noteSnippet = note ? `<span class="muted small" style="margin-left:8px;">📝 ${esc(note.substring(0,60))}${note.length>60?'…':''}</span>` : '';

    return `<div style="padding:8px 12px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;margin-bottom:4px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-weight:bold;font-size:12px;max-width:35%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(fpath)}">${esc(fname)}</span>
      <span class="muted small">${esc(f.size_h||'?')}</span>
      ${catBadges}
      ${creatorBadge}
      ${cfBadge}
      ${tagBadges}
      ${noteSnippet}
      <span class="muted small" style="margin-left:auto;">${esc(f.mod_folder||'')}</span>
      <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;" data-act="open_folder" data-path="${esc(fpath)}">📂</button>
      <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;" data-act="copy" data-path="${esc(fpath)}">📋</button>
    </div>`;
  }).join('');

  resultsDiv.style.display = 'block';
  resultsDiv.innerHTML = html;
}

// Initial load
loadCreators();
loadNotes();
loadTags();
loadCurseForge();

// ---- Tutorial System ----
const TUTORIAL_STEPS = [
  {
    icon: '🎮',
    title: 'Willkommen beim Sims 4 Duplikate Scanner!',
    body: `<b>Schön, dass du da bist!</b> Dieses Tool hilft dir, deine Mods-Sammlung sauber und organisiert zu halten.<br><br>
    In diesem kurzen Tutorial zeigen wir dir alle wichtigen Funktionen.<br><br>
    <b>💡 Tipp:</b> Du kannst das Tutorial jederzeit über den <b>❓ Tutorial</b>-Button in der Navigationsleiste erneut starten.`
  },
  {
    icon: '🧭',
    title: 'Die Navigationsleiste',
    body: `Oben findest du die <b>Navigationsleiste</b> mit allen Bereichen:<br>
    <ul>
      <li><b>📂 Duplikate</b> — Gefundene doppelte Mod-Dateien</li>
      <li><b>💀 Korrupte</b> — Beschädigte Dateien die Probleme verursachen</li>
      <li><b>⚔️ Konflikte</b> — Mods die sich gegenseitig überschreiben</li>
      <li><b>⏰ Veraltet</b> — Mods die nicht mehr aktuell sind</li>
    </ul>
    Die Badges zeigen die <b>Anzahl</b> der gefundenen Probleme an. Abschnitte ohne Funde werden automatisch ausgeblendet.`
  },
  {
    icon: '🔍',
    title: 'Duplikate verstehen',
    body: `Der Scanner findet drei Arten von Duplikaten:<br>
    <ul>
      <li><b>📝 Name</b> — Gleicher Dateiname in verschiedenen Ordnern</li>
      <li><b>📦 Inhalt</b> — Identischer Dateiinhalt (exakte Kopien)</li>
      <li><b>🔎 Ähnlich</b> — Dateien mit ähnlichem Inhalt (z.B. verschiedene Versionen)</li>
    </ul>
    Jede Gruppe zeigt alle betroffenen Dateien mit <b>Pfad, Größe und Änderungsdatum</b>.`
  },
  {
    icon: '📦',
    title: 'DBPF-Tiefenanalyse',
    body: `Der Scanner kann <b>.package-Dateien</b> lesen und analysieren — das Sims 4 Dateiformat.<br><br>
    Die Tiefenanalyse erkennt automatisch:
    <ul>
      <li><b>Kategorie</b> — CAS, Objekte, Tuning, Skript usw.</li>
      <li><b>Vorschaubilder</b> — Thumbnails direkt aus der Datei</li>
      <li><b>Interne Ressourcen</b> — Was genau in der Datei steckt</li>
    </ul>
    So siehst du auf einen Blick, was jede Mod-Datei enthält!`
  },
  {
    icon: '🖼️',
    title: 'Thumbnails & Bildvergleich',
    body: `Bei Duplikat-Gruppen mit Vorschaubildern erscheint ein <b>🖼️ Vergleichen</b>-Button.<br><br>
    Damit öffnest du eine <b>Galerie</b> mit allen Bildern nebeneinander — perfekt um zu entscheiden, welche Version du behalten willst!<br><br>
    <b>💡 Klicke</b> auf ein Bild zum Vergrößern. Mit <b>ESC</b> schließt du die Ansicht wieder.`
  },
  {
    icon: '⚡',
    title: 'Aktionen & Quarantäne',
    body: `Für jede Datei stehen dir Aktionen zur Verfügung:<br>
    <ul>
      <li><b>📦 Quarantäne</b> — Verschiebt die Datei sicher (rückgängig machbar!)</li>
      <li><b>🗑️ Löschen</b> — Löscht die Datei endgültig</li>
      <li><b>📂 Öffnen</b> — Zeigt den Ordner im Explorer</li>
    </ul>
    <b>🛡️ Tipp:</b> Nutze immer Quarantäne statt Löschen! Du kannst Dateien jederzeit wiederherstellen.`
  },
  {
    icon: '🎛️',
    title: 'Batch-Aktionen',
    body: `Im Bereich <b>🎛️ Aktionen</b> findest du praktische Werkzeuge:<br>
    <ul>
      <li><b>Alle Duplikate markieren</b> — Schnell eine Seite auswählen</li>
      <li><b>Batch-Quarantäne</b> — Alle markierten auf einmal verschieben</li>
      <li><b>🔄 Rescan</b> — Erneut scannen nach Änderungen</li>
      <li><b>📥 Export</b> — Mod-Liste als CSV exportieren</li>
    </ul>
    Über die <b>Checkboxen</b> bei jeder Datei kannst du auswählen, was passieren soll.`
  },
  {
    icon: '🔎',
    title: 'Globale Suche',
    body: `Die <b>Globale Suche</b> ganz oben durchsucht <b>ALLES</b> auf einmal:<br>
    <ul>
      <li>Dateinamen und Pfade</li>
      <li>Notizen und Tags</li>
      <li>Creator-Informationen</li>
      <li>CurseForge-Daten</li>
    </ul>
    Einfach eintippen — die Ergebnisse erscheinen sofort!`
  },
  {
    icon: '🏷️',
    title: 'Notizen & Tags',
    body: `Du kannst zu jeder Mod <b>persönliche Notizen</b> und <b>Tags</b> hinzufügen:<br><br>
    <b>📝 Notizen</b> — Freitext, z.B. "Funktioniert super mit XY Mod"<br>
    <b>🏷️ Tags</b> — Kategorie-Labels wie "Favorit", "Testen", "Behalten"<br><br>
    Alles wird gespeichert und überlebt Rescans! Nutze Tags um deine Mods zu organisieren.`
  },
  {
    icon: '🔥',
    title: 'CurseForge Integration',
    body: `Wenn du den <b>CurseForge App</b> nutzt, kann der Scanner deine installierten Mods abgleichen.<br><br>
    Die Integration zeigt dir:
    <ul>
      <li><b>Installierte Mods</b> vs. lokale Dateien</li>
      <li><b>Versionsinfos</b> und Update-Status</li>
      <li><b>Autor & Beschreibung</b> aus CurseForge</li>
    </ul>
    Der Pfad wird automatisch erkannt, kann aber in den Einstellungen angepasst werden.`
  },
  {
    icon: '📜',
    title: 'Scan-Historie & Snapshots',
    body: `Im Bereich <b>📚 Verlauf</b> findest du:<br><br>
    <b>📸 Mod-Snapshot</b> — Ein Foto deiner Mod-Sammlung bei jedem Scan<br>
    <b>📋 Scan-Historie</b> — Alle durchgeführten Aktionen (Quarantäne, Löschen usw.)<br><br>
    So kannst du nachvollziehen, was sich geändert hat und welche Aktionen du durchgeführt hast.`
  },
  {
    icon: '🎉',
    title: 'Fertig! Viel Spaß!',
    body: `Du kennst jetzt alle <b>wichtigen Funktionen</b>!<br><br>
    <b>Noch ein paar Tipps:</b>
    <ul>
      <li>Der <b>🔄 Auto-Watcher</b> erkennt Änderungen automatisch</li>
      <li>Erstelle <b>Creator-Verknüpfungen</b> für deine Lieblings-Modder</li>
      <li>Nutze den <b>📥 Import-Manager</b> für neue Mods</li>
      <li>Schau regelmäßig nach <b>⚔️ Konflikten</b></li>
    </ul>
    <b>🎮 Happy Simming!</b>`
  }
];

let tutorialStep = 0;

function renderTutorialStep() {
  const step = TUTORIAL_STEPS[tutorialStep];
  document.getElementById('tut-step-icon').textContent = step.icon;
  document.getElementById('tut-step-title').textContent = step.title;
  document.getElementById('tut-step-body').innerHTML = step.body;

  // Dots
  const dotsEl = document.getElementById('tut-dots');
  dotsEl.innerHTML = TUTORIAL_STEPS.map((_, i) =>
    `<div class="tut-dot ${i === tutorialStep ? 'active' : (i < tutorialStep ? 'done' : '')}" onclick="tutorialGoTo(${i})"></div>`
  ).join('');

  // Buttons
  document.getElementById('tut-btn-prev').style.display = tutorialStep === 0 ? 'none' : '';
  const isLast = tutorialStep === TUTORIAL_STEPS.length - 1;
  document.getElementById('tut-btn-next').textContent = isLast ? '✅ Fertig!' : 'Weiter →';
  document.getElementById('tut-btn-skip').style.display = isLast ? 'none' : '';
}

function startTutorial() {
  tutorialStep = 0;
  renderTutorialStep();
  document.getElementById('tutorial-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeTutorial() {
  document.getElementById('tutorial-overlay').classList.remove('active');
  document.body.style.overflow = '';
  if (document.getElementById('tut-dont-show').checked) {
    markTutorialSeen();
  }
}

function tutorialNext() {
  if (tutorialStep < TUTORIAL_STEPS.length - 1) {
    tutorialStep++;
    renderTutorialStep();
  } else {
    closeTutorial();
  }
}

function tutorialPrev() {
  if (tutorialStep > 0) {
    tutorialStep--;
    renderTutorialStep();
  }
}

function tutorialGoTo(i) {
  tutorialStep = i;
  renderTutorialStep();
}

async function markTutorialSeen() {
  try {
    await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ token: TOKEN, action: 'mark_tutorial_seen' })
    });
  } catch(e) { console.warn('Tutorial-Status konnte nicht gespeichert werden', e); }
}

async function checkTutorialOnStart() {
  try {
    const r = await fetch('/api/tutorial?token=' + encodeURIComponent(TOKEN));
    const d = await r.json();
    if (d.ok && !d.tutorial_seen) {
      startTutorial();
    }
  } catch(e) { console.warn('Tutorial-Check fehlgeschlagen', e); }
}

// Tutorial-Keyboard Navigation
document.addEventListener('keydown', function(e) {
  const overlay = document.getElementById('tutorial-overlay');
  if (!overlay.classList.contains('active')) return;
  if (e.key === 'ArrowRight' || e.key === 'Enter') { e.preventDefault(); tutorialNext(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); tutorialPrev(); }
  if (e.key === 'Escape') { e.preventDefault(); closeTutorial(); }
});

// Check on page load
checkTutorialOnStart();

// ---- Bug Report ----
function openBugReport() {
  document.getElementById('bug-category').value = '';
  document.getElementById('bug-description').value = '';
  document.querySelectorAll('.bug-symptom').forEach(cb => cb.checked = false);
  document.getElementById('bug-status').className = 'bug-status';
  document.getElementById('bug-status').textContent = '';
  document.getElementById('bug-send-btn').disabled = false;
  document.getElementById('bug-send-btn').textContent = '🐛 Absenden';
  document.getElementById('bugreport-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeBugReport() {
  document.getElementById('bugreport-overlay').classList.remove('active');
  document.body.style.overflow = '';
}

async function sendBugReport() {
  const category = document.getElementById('bug-category').value;
  const desc = document.getElementById('bug-description').value.trim();
  const symptoms = [];
  document.querySelectorAll('.bug-symptom:checked').forEach(cb => symptoms.push(cb.value));

  if (!category) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '⚠️ Bitte wähle eine Kategorie aus!';
    return;
  }
  if (symptoms.length === 0 && !desc) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '⚠️ Bitte wähle mindestens ein Symptom oder beschreibe das Problem!';
    return;
  }
  const btn = document.getElementById('bug-send-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Wird gesendet…';
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ token: TOKEN, action: 'send_bug_report', category: category, symptoms: symptoms, description: desc })
    });
    const d = await r.json();
    if (d.ok) {
      document.getElementById('bug-status').className = 'bug-status success';
      document.getElementById('bug-status').textContent = '✅ Bug-Report wurde erfolgreich gesendet! Danke für deine Hilfe!';
      setTimeout(() => closeBugReport(), 3000);
    } else {
      document.getElementById('bug-status').className = 'bug-status error';
      document.getElementById('bug-status').textContent = '❌ Fehler: ' + (d.error || 'Unbekannt');
      btn.disabled = false;
      btn.textContent = '🐛 Absenden';
    }
  } catch(e) {
    document.getElementById('bug-status').className = 'bug-status error';
    document.getElementById('bug-status').textContent = '❌ Verbindungsfehler: ' + e.message;
    btn.disabled = false;
    btn.textContent = '🐛 Absenden';
  }
}

// Bug Report Keyboard
document.addEventListener('keydown', function(e) {
  const ov = document.getElementById('bugreport-overlay');
  if (!ov.classList.contains('active')) return;
  if (e.key === 'Escape') { e.preventDefault(); closeBugReport(); }
});

// ---- Alles OK Banner ----
function checkAllOK(data) {
  const s = data.summary || {};
  const groups = (s.groups_name||0) + (s.groups_content||0) + (s.groups_similar||0);
  const hasProblems = groups > 0 || s.corrupt_count > 0 || s.conflict_count > 0;
  document.getElementById('all-ok-banner').style.display = hasProblems ? 'none' : '';
}

// ---- Abhängigkeiten ----
function renderDependencies(data) {
  const section = document.getElementById('deps-section');
  const deps = data.dependencies || [];
  if (deps.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  const showPairs = document.getElementById('deps-filter-pairs').checked;
  const showNameDeps = document.getElementById('deps-filter-namedeps').checked;
  const showFamilies = document.getElementById('deps-filter-families').checked;

  const filtered = deps.filter(d => {
    if (d.type === 'script_pair') return showPairs;
    if (d.type === 'name_dependency') return showNameDeps;
    if (d.type === 'mod_family') return showFamilies;
    return true;
  });

  document.getElementById('deps-summary').textContent =
    `${deps.length} Beziehungen erkannt (${filtered.length} angezeigt)`;

  const html = filtered.map((d, i) => {
    const typeColors = {
      'script_pair': '#3b82f6',
      'name_dependency': '#f59e0b',
      'mod_family': '#8b5cf6',
    };
    const color = typeColors[d.type] || '#64748b';
    const filesHtml = (d.files || []).map(fp => {
      const name = fp.split(/[\\\\/]/).pop();
      const ext = name.split('.').pop().toLowerCase();
      const extBadge = ext === 'ts4script'
        ? '<span style="background:#7f1d1d;color:#fca5a5;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:4px;">Script</span>'
        : ext === 'package'
          ? '<span style="background:#1e3a5f;color:#93c5fd;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:4px;">Package</span>'
          : '';
      return `<div style="padding:4px 8px;background:#0f172a;border-radius:4px;margin:2px 0;font-size:12px;display:flex;align-items:center;gap:6px;">
        <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(fp)}">${esc(name)}</span>${extBadge}
        <button class="btn btn-ghost" style="font-size:10px;padding:2px 6px;margin-left:auto;" data-act="open_folder" data-path="${esc(fp)}">📂</button>
      </div>`;
    }).join('');
    const countInfo = d.count ? ` (${d.count} Dateien)` : ` (${d.files.length} Dateien)`;
    return `<details class="grp color-${i % 6}" style="margin-bottom:6px;">
      <summary style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-size:16px;">${d.icon}</span>
        <b style="font-size:13px;">${esc(d.label)}${countInfo}</b>
        <span style="background:${color};color:#fff;padding:1px 8px;border-radius:10px;font-size:10px;">${d.type === 'script_pair' ? 'Script+Package' : d.type === 'name_dependency' ? 'Abhängigkeit' : 'Familie'}</span>
      </summary>
      <div style="margin-top:8px;padding:6px 10px;background:#111827;border-radius:8px;">
        <p class="muted small" style="margin:0 0 6px;">${esc(d.hint)}</p>
        ${filesHtml}
      </div>
    </details>`;
  }).join('');

  document.getElementById('deps-list').innerHTML = html || '<div class="muted">Keine Abhängigkeiten gefunden.</div>';
}

// Event listeners for dependency filters
['deps-filter-pairs', 'deps-filter-namedeps', 'deps-filter-families'].forEach(id => {
  document.getElementById(id).addEventListener('change', () => {
    if (window.__DATA) renderDependencies(window.__DATA);
  });
});

// ---- Statistik-Dashboard ----
function renderStats(data) {
  const s = data.summary || {};
  const stats = data.stats || {};

  // Übersicht
  const overviewHtml = `
    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:8px;">
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#6366f1;">${s.total_files || 0}</div>
        <div class="muted small">Dateien gesamt</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#22c55e;">${esc(s.total_size_h || '?')}</div>
        <div class="muted small">Gesamtgröße</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#f59e0b;">${esc(s.wasted_h || '0 B')}</div>
        <div class="muted small">Verschwendet (Duplikate)</div>
      </div>
      <div style="background:#1e293b; border-radius:10px; padding:14px; text-align:center;">
        <div style="font-size:28px; font-weight:bold; color:#ef4444;">${s.corrupt_count || 0}</div>
        <div class="muted small">Korrupte Dateien</div>
      </div>
    </div>`;
  document.getElementById('stats-overview').innerHTML = overviewHtml;

  // Kategorie-Balken
  const cats = stats.category_counts || [];
  const catMax = cats.length > 0 ? cats[0][1] : 1;
  const catColors = {
    'CAS (Haare 💇)':'#a855f7', 'CAS (Kleidung 👚)':'#06b6d4', 'CAS (Make-Up 💄)':'#ec4899',
    'CAS (Accessoire 💍)':'#f59e0b', 'CAS (Kleidung/Haare/Make-Up)':'#8b5cf6',
    'Objekt/Möbel':'#22c55e', 'Gameplay-Mod (Tuning)':'#ef4444', 'Mesh/Build-Mod':'#14b8a6',
    'Textur/Override':'#f97316', 'Sonstiges':'#64748b', 'Unbekannt':'#475569',
  };
  const catHtml = cats.map(([name, count]) => {
    const pct = Math.round(count / catMax * 100);
    const color = catColors[name] || '#6366f1';
    return `<div style="margin-bottom:4px; display:flex; align-items:center; gap:8px;">
      <div style="min-width:180px; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(name)}</div>
      <div style="flex:1; background:#0f172a; border-radius:4px; height:18px; overflow:hidden;">
        <div style="width:${pct}%; background:${color}; height:100%; border-radius:4px; min-width:2px;"></div>
      </div>
      <div style="min-width:40px; text-align:right; font-size:12px; color:#94a3b8;">${count}</div>
    </div>`;
  }).join('');
  document.getElementById('stats-categories').innerHTML = catHtml || '<span class="muted small">Keine Daten</span>';

  // Top 10 Ordner
  const folders = stats.top10_folders || [];
  const folderMax = folders.length > 0 ? folders[0].size : 1;
  const folderHtml = folders.map(f => {
    const pct = Math.round(f.size / folderMax * 100);
    return `<div style="margin-bottom:4px; display:flex; align-items:center; gap:8px;">
      <div style="min-width:180px; font-size:12px; color:#cbd5e1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${esc(f.name)}">📁 ${esc(f.name)}</div>
      <div style="flex:1; background:#0f172a; border-radius:4px; height:18px; overflow:hidden;">
        <div style="width:${pct}%; background:#3b82f6; height:100%; border-radius:4px; min-width:2px;"></div>
      </div>
      <div style="min-width:80px; text-align:right; font-size:11px; color:#94a3b8;">${esc(f.size_h)} (${f.count})</div>
    </div>`;
  }).join('');
  document.getElementById('stats-folders').innerHTML = folderHtml || '<span class="muted small">Keine Daten</span>';

  // Top 10 größte Dateien
  const biggest = stats.top10_biggest || [];
  const bigHtml = biggest.map((f, i) => {
    const name = (f.rel || f.path || '').split(/[\\\\/]/).pop();
    const creator = detectCreator(name);
    const creatorBadge = creator ? `<span style="background:#1e3a5f;color:#60a5fa;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:4px;" title="Mod-Ersteller: ${esc(creator.name)}">${creator.icon} ${esc(creator.name)}</span>` : '';
    return `<div style="display:flex;align-items:center;gap:10px;padding:6px 10px;background:#0f172a;border:1px solid #1e293b;border-radius:6px;margin-bottom:4px;">
      <span style="color:#64748b;font-weight:bold;min-width:20px;">#${i+1}</span>
      <div style="flex:1;min-width:0;">
        <div style="font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(name)}${creatorBadge}</div>
        <div class="muted" style="font-size:11px;">${esc(f.mod_folder)} | ${esc(f.size_h)}</div>
      </div>
      <div style="font-weight:bold;color:#f59e0b;font-size:13px;">${esc(f.size_h)}</div>
    </div>`;
  }).join('');
  document.getElementById('stats-biggest').innerHTML = bigHtml || '<span class="muted small">Keine Daten</span>';
}

// ---- Quarantäne-Manager ----
async function loadQuarantine() {
  try {
    const resp = await fetch('/api/quarantine?token=' + TOKEN);
    const json = await resp.json();
    if (!json.ok) throw new Error(json.error);
    renderQuarantine(json);
  } catch(e) {
    document.getElementById('quarantine-summary').innerHTML = '<span style="color:#ef4444;">Fehler: ' + esc(e.message) + '</span>';
  }
}

function renderQuarantine(qdata) {
  const files = qdata.files || [];
  const section = document.getElementById('quarantine-section');

  if (files.length === 0) {
    section.style.display = 'none';
    document.getElementById('nav-quarantine').classList.add('nav-hidden');
    return;
  }
  section.style.display = '';
  document.getElementById('nav-quarantine').classList.remove('nav-hidden');
  document.getElementById('nav-badge-quarantine').textContent = files.length;

  document.getElementById('quarantine-summary').innerHTML =
    `<b>${files.length}</b> Dateien in Quarantäne | Gesamtgröße: <b>${esc(qdata.total_size_h)}</b>`;

  const cards = files.map(f => {
    const creator = detectCreator(f.name);
    const creatorBadge = creator ? ` <span style="background:#1e3a5f;color:#60a5fa;font-size:10px;padding:1px 6px;border-radius:4px;">${creator.icon} ${esc(creator.name)}</span>` : '';
    return `<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:4px;">
      <span style="font-size:16px;">📦</span>
      <div style="flex:1;min-width:0;">
        <div style="font-weight:bold;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(f.name)}${creatorBadge}</div>
        <div class="muted" style="font-size:11px;">${esc(f.q_dir)} | ${esc(f.size_h)} | ${esc(f.mtime)}</div>
      </div>
      <div style="display:flex;gap:4px;flex-shrink:0;">
        <button class="btn btn-ok" style="font-size:11px;padding:3px 10px;" data-act="restore" data-path="${esc(f.path)}" title="Zurück in den Mods-Ordner verschieben">↩️ Zurückholen</button>
        <button class="btn btn-danger" style="font-size:11px;padding:3px 10px;" data-act="delete_q" data-path="${esc(f.path)}" title="Endgültig vom PC löschen">🗑</button>
      </div>
    </div>`;
  }).join('');
  document.getElementById('quarantine-list').innerHTML = cards;
}

// ---- Alle Mods: Tag-Verwaltung ----
let _allModsShown = 50;
let _allModsFiltered = [];

function collectAllUniqueFiles(data) {
  // Nutze die vollständige all_files-Liste vom Backend (enthält ALLE gescannten Mods)
  if (data.all_files && data.all_files.length > 0) {
    return data.all_files.slice().sort((a,b) => (a.path||'').localeCompare(b.path||''));
  }
  // Fallback: nur Problemdateien sammeln
  const seen = new Set();
  const all = [];
  for (const g of (data.groups || [])) {
    for (const f of (g.files || [])) {
      if (!seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const c of (data.corrupt || [])) {
    if (c.path && !seen.has(c.path)) { seen.add(c.path); all.push(c); }
  }
  for (const conf of (data.conflicts || [])) {
    for (const f of (conf.files || [])) {
      if (f.path && !seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const ap of (data.addon_pairs || [])) {
    for (const f of (ap.files || [])) {
      if (f.path && !seen.has(f.path)) { seen.add(f.path); all.push(f); }
    }
  }
  for (const o of (data.outdated || [])) {
    if (o.path && !seen.has(o.path)) { seen.add(o.path); all.push(o); }
  }
  all.sort((a,b) => (a.path||'').localeCompare(b.path||''));
  return all;
}

function renderAllMods(data) {
  const allFiles = collectAllUniqueFiles(data);
  const term = (document.getElementById('allmods-search').value || '').trim().toLowerCase();
  const tagFilter = document.getElementById('allmods-tag-filter').value;
  const catFilter = document.getElementById('allmods-cat-filter').value;

  // Populate tag filter dropdown (once)
  const sel = document.getElementById('allmods-tag-filter');
  if (sel.options.length <= 6) {
    const cfOpt1 = document.createElement('option');
    cfOpt1.value = '__curseforge';
    cfOpt1.textContent = '\ud83d\udd25 CurseForge';
    sel.appendChild(cfOpt1);
    const cfOpt2 = document.createElement('option');
    cfOpt2.value = '__manual';
    cfOpt2.textContent = '\ud83d\udce6 Manuell hinzugef\u00fcgt';
    sel.appendChild(cfOpt2);
    const cfOpt3 = document.createElement('option');
    cfOpt3.value = '__cf_update';
    cfOpt3.textContent = '\u2b06\ufe0f Update verf\u00fcgbar';
    sel.appendChild(cfOpt3);
    for (const t of AVAILABLE_TAGS) {
      const opt = document.createElement('option');
      opt.value = t.name;
      opt.textContent = t.name;
      sel.appendChild(opt);
    }
  }

  // Populate category filter dropdown (dynamically from data)
  const catSel = document.getElementById('allmods-cat-filter');
  if (catSel.options.length <= 1) {
    const cats = (data.stats && data.stats.category_counts) || [];
    for (const [name, count] of cats) {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = `${name} (${count})`;
      catSel.appendChild(opt);
    }
  }

  // Filter
  const filtered = allFiles.filter(f => {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop().toLowerCase();
    const ftags = MOD_TAGS[fpath] || [];
    const fnote = MOD_NOTES[fpath] || '';
    const cfInfo = getCurseForgeInfo(fpath);
    const deep = f.deep || {};
    const fcat = deep.category || '';
    const hay = (fname + ' ' + (f.mod_folder||'') + ' ' + ftags.join(' ') + ' ' + fnote + ' ' + fcat + ' ' + (cfInfo ? cfInfo.name + ' ' + cfInfo.author : '')).toLowerCase();

    if (term && !hay.includes(term)) return false;

    // Category filter
    if (catFilter && fcat !== catFilter) return false;

    if (tagFilter === '__tagged' && ftags.length === 0) return false;
    if (tagFilter === '__untagged' && ftags.length > 0) return false;
    if (tagFilter === '__noted' && !fnote) return false;
    if (tagFilter === '__curseforge' && !cfInfo) return false;
    if (tagFilter === '__manual' && cfInfo) return false;
    if (tagFilter === '__cf_update' && (!cfInfo || !cfInfo.has_update)) return false;
    if (tagFilter && !tagFilter.startsWith('__') && !ftags.includes(tagFilter)) return false;

    return true;
  });

  _allModsFiltered = filtered;
  _allModsShown = 50;

  // Summary
  const tagged = allFiles.filter(f => (MOD_TAGS[f.path]||[]).length > 0).length;
  const noted = allFiles.filter(f => !!MOD_NOTES[f.path]).length;
  const cfCount = allFiles.filter(f => !!getCurseForgeInfo(f.path)).length;
  const cfUpdates = allFiles.filter(f => { const c = getCurseForgeInfo(f.path); return c && c.has_update; }).length;
  const problemCount = (data.summary && data.summary.problem_files) || 0;
  document.getElementById('allmods-summary').innerHTML =
    `<b>${allFiles.length}</b> Mods gesamt | <b>\ud83d\udd25 ${cfCount}</b> CurseForge` +
    (cfUpdates > 0 ? ` (<b>\u2b06\ufe0f ${cfUpdates}</b> Updates)` : '') +
    ` | <b>${allFiles.length - cfCount}</b> manuell | <b>${tagged}</b> getaggt | <b>${noted}</b> mit Notiz` +
    (term || tagFilter || catFilter ? ` | <b>${filtered.length}</b> angezeigt (gefiltert)` : '');

  _renderAllModsPage();
}

function _renderAllModsPage() {
  const filtered = _allModsFiltered;
  const toShow = filtered.slice(0, _allModsShown);

  const cards = toShow.map(f => {
    const fpath = f.path || '';
    const fname = fpath.split(/[\\\\/]/).pop();
    const rel = f.rel && f.rel !== f.path ? f.rel : fpath;
    const showFull = document.getElementById('show_full').checked;
    const fullLine = (f.rel && f.rel !== f.path && showFull)
      ? `<div class="muted small" style="margin-top:2px;"><code>${esc(f.path)}</code></div>` : '';
    const creator = detectCreator(fname);
    const creatorBadge = creator
      ? `<a href="${esc(creator.url)}" target="_blank" rel="noopener" class="pill" style="background:#312e81;color:#a5b4fc;text-decoration:none;cursor:pointer;font-size:10px;" title="Mod von ${esc(creator.name)}">${creator.icon} ${esc(creator.name)}</a>` : '';
    const cfBadge = renderCurseForgeUI(fpath);
    const deep = f.deep || {};
    const fcat = deep.category || '';
    const _catColors = {
      'CAS (Haare 💇)':'#a855f7', 'CAS (Kleidung 👚)':'#06b6d4', 'CAS (Make-Up 💄)':'#ec4899',
      'CAS (Accessoire 💍)':'#f59e0b', 'CAS (Kleidung/Haare/Make-Up)':'#8b5cf6',
      'Objekt/Möbel':'#22c55e', 'Gameplay-Mod (Tuning)':'#ef4444', 'Mesh/Build-Mod':'#14b8a6',
      'Textur/Override':'#f97316', 'Sonstiges':'#64748b',
    };
    const catColor = _catColors[fcat] || '#475569';
    const catBadge = fcat
      ? `<span style="background:${catColor}22;color:${catColor};border:1px solid ${catColor}44;padding:1px 8px;border-radius:10px;font-size:10px;white-space:nowrap;">${esc(fcat)}</span>` : '';

    return `<div style="padding:10px 14px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;margin-bottom:6px;">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span style="font-weight:bold;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:50%;" title="${esc(fpath)}">${esc(fname)}</span>
        <span class="tag" style="font-size:10px;">${esc(f.root_label||'')}</span>
        <span class="muted small">${esc(f.size_h||'?')}</span>
        <span class="muted small">\ud83d\udcc5 ${esc(f.mtime||'?')}</span>
        ${creatorBadge}
        ${cfBadge}
        ${catBadge}
        <span class="muted small" style="margin-left:auto;">${esc(f.mod_folder||'')}</span>
      </div>
      <div class="muted small" style="margin-top:2px;"><code>${esc(rel)}</code></div>
      ${fullLine}
      <div style="margin-top:6px;">
        ${renderTagsUI(fpath)}
      </div>
      <div style="margin-top:4px;">
        ${renderNotesUI(fpath)}
      </div>
      <div class="flex" style="margin-top:6px;gap:4px;">
        <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="open_folder" data-path="${esc(fpath)}">📂 Ordner</button>
        <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="copy" data-path="${esc(fpath)}">📋 Pfad</button>
      </div>
    </div>`;
  }).join('');

  document.getElementById('allmods-list').innerHTML = cards || '<div class="muted">Keine Mods gefunden.</div>';

  const moreBtn = document.getElementById('allmods-loadmore');
  if (_allModsShown < filtered.length) {
    moreBtn.style.display = '';
    document.getElementById('btn_allmods_more').textContent = `\u2b07\ufe0f Mehr laden (${_allModsShown} von ${filtered.length})\u2026`;
  } else {
    moreBtn.style.display = 'none';
  }
}

// Event listeners for "Alle Mods" section
let _allModsSearchTimer = null;
document.getElementById('allmods-search').addEventListener('input', () => {
  clearTimeout(_allModsSearchTimer);
  _allModsSearchTimer = setTimeout(() => { if (window.__DATA) renderAllMods(window.__DATA); }, 300);
});
document.getElementById('allmods-tag-filter').addEventListener('change', () => {
  if (window.__DATA) renderAllMods(window.__DATA);
});
document.getElementById('allmods-cat-filter').addEventListener('change', () => {
  if (window.__DATA) renderAllMods(window.__DATA);
});
document.getElementById('btn_allmods_more').addEventListener('click', () => {
  _allModsShown += 50;
  _renderAllModsPage();
});

function renderOutdated(data) {
  const section = document.getElementById('outdated-section');
  const list = data.outdated || [];
  const gi = data.game_info;
  if (list.length === 0 || !gi) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';
  document.getElementById('outdated-game-ver').innerHTML =
    `Spielversion: <b>${esc(gi.version)}</b> | Patch vom: <b>${esc(gi.patch_date)}</b>`;

  const filterHigh = document.getElementById('outdated-filter-high');
  const filterMid = document.getElementById('outdated-filter-mid');
  const filterLow = document.getElementById('outdated-filter-low');

  function _render() {
    const showHigh = filterHigh.checked;
    const showMid = filterMid.checked;
    const showLow = filterLow.checked;
    const filtered = list.filter(f => {
      if (f.risk === 'hoch') return showHigh;
      if (f.risk === 'mittel') return showMid;
      return showLow;
    });

    const high = filtered.filter(f => f.risk === 'hoch').length;
    const mid = filtered.filter(f => f.risk === 'mittel').length;
    const low = filtered.filter(f => f.risk !== 'hoch' && f.risk !== 'mittel').length;
    document.getElementById('outdated-summary').innerHTML =
      `${filtered.length} von ${list.length} Mods angezeigt: ` +
      (high ? `<b style="color:#ef4444;">⚠️ ${high} hoch</b> ` : '') +
      (mid ? `<b style="color:#fbbf24;">⚡ ${mid} mittel</b> ` : '') +
      (low ? `<b style="color:#6ee7b7;">✅ ${low} niedrig</b>` : '');

    const cards = filtered.map(f => {
      const riskColors = {hoch:'#ef4444',mittel:'#fbbf24',niedrig:'#22c55e',unbekannt:'#94a3b8'};
      const riskIcons = {hoch:'⚠️',mittel:'⚡',niedrig:'✅',unbekannt:'❓'};
      const rc = riskColors[f.risk] || '#94a3b8';
      const ri = riskIcons[f.risk] || '❓';
      const name = (f.rel || f.path || '').split(/[\\/]/).pop();
      const folder = f.mod_folder || '';
      const daysStr = f.days_before_patch === 1 ? '1 Tag' : `${f.days_before_patch} Tage`;
      return `<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:6px;">
        <span style="font-size:18px;min-width:24px;text-align:center;">${ri}</span>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${esc(f.path)}">${esc(name)}</div>
          <div class="muted small">${esc(folder)} | ${esc(f.size_h)} | Geändert: ${esc(f.mtime)} | <b style="color:${rc};">${daysStr} vor Patch</b></div>
          <div class="muted small" style="color:${rc};">${esc(f.risk_reason || '')}</div>
        </div>
        <div style="display:flex;gap:4px;flex-shrink:0;">
          <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="open_folder" data-path="${esc(f.path)}" title="Ordner öffnen">📂</button>
          <button class="btn btn-ghost" style="font-size:11px;padding:3px 8px;" data-act="copy" data-path="${esc(f.path)}" title="Pfad kopieren">📋</button>
        </div>
      </div>`;
    }).join('');
    document.getElementById('outdated-list').innerHTML = cards || '<div class="muted">Keine Mods mit gewähltem Filter.</div>';
  }

  filterHigh.onchange = _render;
  filterMid.onchange = _render;
  filterLow.onchange = _render;
  _render();
}

function renderPerFile(data) {
  const map = buildPerFileMap(data);
  const term = (document.getElementById('pf-search').value || '').trim().toLowerCase();
  const showFull = document.getElementById('show_full').checked;

  // Sortiere: meiste Findings zuerst, dann alphabetisch
  let entries = Array.from(map.values());
  entries.sort((a, b) => {
    if (b.findings.length !== a.findings.length) return b.findings.length - a.findings.length;
    return a.file.path.localeCompare(b.file.path);
  });

  if (term) {
    entries = entries.filter(e => {
      const noteTxt = MOD_NOTES[e.file.path] || '';
      const tagsTxt = (MOD_TAGS[e.file.path] || []).join(' ');
      const hay = (e.file.path + ' ' + e.file.rel + ' ' + e.findings.map(f => f.typeLabel).join(' ') + ' ' + noteTxt + ' ' + tagsTxt).toLowerCase();
      return hay.includes(term);
    });
  }

  document.getElementById('perfile-summary').innerHTML =
    `<b>${entries.length}</b> Dateien mit Auff\u00e4lligkeiten gefunden.` +
    ` <span class="muted small">Sortiert: meiste Probleme zuerst.</span>`;

  // Z\u00e4hler f\u00fcr Zusammenfassung
  let cntCorrupt = 0, cntConflict = 0, cntAddon = 0, cntDupe = 0;
  for (const e of entries) {
    const cats = new Set(e.findings.map(fi => fi.category));
    if (cats.has('corrupt')) cntCorrupt++;
    if (cats.has('conflict')) cntConflict++;
    if (cats.has('addon')) cntAddon++;
    if (cats.has('group')) cntDupe++;
  }
  const statsHtml = [
    cntCorrupt ? `<span class="corrupt-status no_dbpf">\u26a0\ufe0f ${cntCorrupt} korrupt</span>` : '',
    cntConflict ? `<span class="conflict-badge">\ud83d\udd00 ${cntConflict} Konflikte</span>` : '',
    cntAddon ? `<span class="addon-badge">\ud83e\udde9 ${cntAddon} Addons</span>` : '',
    cntDupe ? `<span class="pill" style="background:#1e3a5f;color:#60a5fa;">${cntDupe} Duplikate</span>` : '',
  ].filter(Boolean).join(' ');
  document.getElementById('perfile-summary').innerHTML += `<div style="margin-top:6px;">${statsHtml}</div>`;

  const cards = entries.map(e => {
    const f = e.file;
    const fname = (f.rel || f.path).split(/[\\\\/]/).pop();
    const relPath = f.rel && f.rel !== f.path ? f.rel : '';
    const fullLine = (relPath && showFull)
      ? `<div class="muted small pathline" style="margin-top:2px;"><code>${esc(f.path)}</code></div>`
      : '';
    const checked = selected.has(f.path) ? 'checked' : '';

    // Kategorie-Badges oben
    const cats = new Set(e.findings.map(fi => fi.category));
    const badges = [];
    if (cats.has('corrupt')) badges.push('<span class="corrupt-status no_dbpf">⚠️ Korrupt</span>');
    if (cats.has('conflict')) badges.push('<span class="conflict-badge">🔀 Konflikt</span>');
    if (cats.has('addon')) badges.push('<span class="addon-badge">🧩 Addon</span>');
    const groupTypes = new Set(e.findings.filter(fi => fi.category === 'group').map(fi => fi.type));
    if (groupTypes.has('content')) badges.push('<span class="pill" style="background:#4c1d95;color:#c4b5fd;">Inhalt-Duplikat</span>');
    if (groupTypes.has('name')) badges.push('<span class="pill" style="background:#1e3a5f;color:#60a5fa;">Name-Duplikat</span>');
    if (groupTypes.has('similar')) badges.push('<span class="pill" style="background:#134e4a;color:#5eead4;">Ähnlich</span>');

    // Finding-Sektionen
    const sections = e.findings.map(fi => {
      if (fi.category === 'corrupt') {
        return `<div class="pf-section pf-corrupt">
          <div class="pf-section-title">\u26a0\ufe0f ${esc(fi.statusLabel)}</div>
          <div class="muted small">${esc(fi.statusHint)}</div>
          <div class="muted small" style="margin-top:6px; color:#fca5a5;">\ud83d\udc49 <b>Empfehlung:</b> Diese Datei in Quarant\u00e4ne verschieben. Sie funktioniert wahrscheinlich nicht und kann Fehler verursachen.</div>
        </div>`;
      }

      if (fi.category === 'group') {
        const icon = fi.type === 'name' ? '\ud83d\udcdb' : fi.type === 'content' ? '\ud83d\udce6' : '\ud83d\udd24';
        const explanation = fi.type === 'content'
          ? 'Diese Dateien sind <b>exakt identisch</b> \u2014 der Inhalt ist Byte f\u00fcr Byte gleich. Eine davon ist \u00fcberfl\u00fcssig und kann gel\u00f6scht werden.'
          : fi.type === 'name'
          ? 'Diese Dateien haben den <b>gleichen Namen</b> aber sind in verschiedenen Ordnern. Meistens ist eine davon veraltet.'
          : 'Diese Dateien haben <b>sehr \u00e4hnliche Namen</b> \u2014 k\u00f6nnten verschiedene Versionen desselben Mods sein.';
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">${esc(p.root_label)} \u00b7 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        const hint = fi.type === 'content'
          ? `<div class="muted small" style="margin-top:6px; color:#c4b5fd;">\ud83d\udc49 <b>Empfehlung:</b> Behalte die neueste Version und verschiebe die anderen in Quarant\u00e4ne.</div>`
          : fi.type === 'name'
          ? `<div class="muted small" style="margin-top:6px; color:#60a5fa;">\ud83d\udc49 <b>Empfehlung:</b> Pr\u00fcfe welche Version du brauchst (Datum vergleichen). Die \u00e4ltere kann meistens weg.</div>`
          : `<div class="muted small" style="margin-top:6px; color:#5eead4;">\ud83d\udc49 <b>Hinweis:</b> Pr\u00fcfe ob das verschiedene Versionen sind. Falls ja, behalte nur die neueste.</div>`;
        return `<div class="pf-section ${fi.typeClass}">
          <div class="pf-section-title">${icon} ${esc(fi.typeLabel)}: "${esc(fi.key)}"</div>
          <div class="muted small" style="margin-bottom:6px;">${explanation}</div>
          <div class="muted small" style="margin-bottom:4px;"><b>${fi.partners.length}</b> weitere Datei(en) mit gleichem ${fi.type === 'content' ? 'Inhalt' : 'Namen'}:</div>
          ${partnerList}
          ${hint}
        </div>`;
      }

      if (fi.category === 'addon') {
        const typePills = fi.topTypes.map(([n,c]) => `<span class="conflict-type-pill">${esc(n)}: ${c}</span>`).join('');
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">\ud83e\udde9 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        return `<div class="pf-section pf-addon">
          <div class="pf-section-title">\ud83e\udde9 Addon-Beziehung <span class="addon-ok">\u2705 OK</span></div>
          <div class="muted small">Diese Datei ist ein <b>Addon/Erweiterung</b> f\u00fcr einen anderen Mod (oder umgekehrt). Das ist normal und gewollt!</div>
          <div class="muted small" style="margin-top:4px;">${fi.sharedCount} geteilte Ressource-IDs \u00b7 ${typePills}</div>
          <div class="muted small" style="margin-top:4px;">Geh\u00f6rt zusammen mit:</div>
          ${partnerList}
          <div class="muted small" style="margin-top:6px; color:#6ee7b7;">\ud83d\udc49 <b>Aktion:</b> Nichts tun \u2014 <b>beide behalten!</b> Wenn du eins l\u00f6schst, funktioniert das andere nicht richtig.</div>
        </div>`;
      }

      if (fi.category === 'conflict') {
        const typePills = fi.topTypes.map(([n,c]) => `<span class="conflict-type-pill">${esc(n)}: ${c}</span>`).join('');
        const partnerList = fi.partnerFiles.map(p =>
          `<div class="pf-partner">\ud83d\udd00 <code>${esc((p.rel||p.path).split(/[\\\\/]/).pop())}</code> \u00b7 ${esc(p.size_h)} \u00b7 ${esc(p.mtime)}</div>`
        ).join('');
        const severity = fi.sharedCount >= 10 ? 'hoch' : fi.sharedCount >= 3 ? 'mittel' : 'niedrig';
        const sevColor = severity === 'hoch' ? '#fca5a5' : severity === 'mittel' ? '#fde68a' : '#94a3b8';
        const sevLabel = severity === 'hoch' ? '\u26a0\ufe0f Wichtig' : severity === 'mittel' ? '\u26a0 Pr\u00fcfen' : '\u2139\ufe0f Gering';
        const sevExplain = fi.sharedCount <= 2
          ? 'Nur 1-2 geteilte IDs \u2014 wahrscheinlich harmlos (z.B. Standard-Ressource die viele Mods nutzen).'
          : fi.sharedCount <= 20
          ? 'Mehrere geteilte IDs \u2014 k\u00f6nnte eine alte Version desselben Mods sein. Pr\u00fcfe Datum und Namen.'
          : 'Viele geteilte IDs \u2014 wahrscheinlich derselbe Mod in verschiedenen Versionen. Nur die neueste behalten!';
        return `<div class="pf-section pf-conflict">
          <div class="pf-section-title">\ud83d\udd00 Ressource-Konflikt <span style="color:${sevColor}; font-size:12px; margin-left:8px;">${sevLabel} (${fi.sharedCount} IDs)</span></div>
          <div class="muted small">${sevExplain}</div>
          <div class="muted small" style="margin-top:4px;">${typePills}</div>
          <div class="muted small" style="margin-top:6px;">Kollidiert mit ${fi.partners.length} Datei(en):</div>
          ${partnerList}
          <div class="muted small" style="margin-top:6px; color:#c4b5fd;">\ud83d\udc49 <b>Empfehlung:</b> ${fi.sharedCount <= 2 ? 'Wahrscheinlich OK \u2014 nur handeln wenn du Probleme im Spiel bemerkst.' : 'Behalte die neuere Datei (h\u00f6heres Datum) und verschiebe die \u00e4ltere in Quarant\u00e4ne.'}</div>
        </div>`;
      }

      return '';
    }).join('');

    // Gesamt-Empfehlung pro Karte
    const hasCats = new Set(e.findings.map(fi => fi.category));
    let recommendation = '';
    if (hasCats.has('corrupt')) {
      recommendation = `<div style="background:#2b1111; border:1px solid #6b2b2b; border-radius:8px; padding:8px 12px; margin-top:10px;">
        <span style="color:#fca5a5; font-weight:bold;">\u26a0\ufe0f Empfehlung: In Quarant\u00e4ne verschieben</span>
        <span class="muted small"> \u2014 Datei ist besch\u00e4digt</span>
      </div>`;
    } else if (hasCats.has('conflict') && !hasCats.has('addon')) {
      const maxShared = Math.max(...e.findings.filter(fi => fi.category === 'conflict').map(fi => fi.sharedCount));
      if (maxShared > 2) {
        recommendation = `<div style="background:#1a1a2e; border:1px solid #3a3a5e; border-radius:8px; padding:8px 12px; margin-top:10px;">
          <span style="color:#c4b5fd; font-weight:bold;">\ud83d\udd00 Empfehlung: Datum pr\u00fcfen</span>
          <span class="muted small"> \u2014 Falls eine \u00e4ltere Version: in Quarant\u00e4ne verschieben</span>
        </div>`;
      }
    } else if (hasCats.has('group') && !hasCats.has('conflict') && !hasCats.has('addon')) {
      const hasContent = e.findings.some(fi => fi.type === 'content');
      if (hasContent) {
        recommendation = `<div style="background:#1a1428; border:1px solid #3a2a5e; border-radius:8px; padding:8px 12px; margin-top:10px;">
          <span style="color:#c4b5fd; font-weight:bold;">\ud83d\udce6 Empfehlung: Duplikat entfernen</span>
          <span class="muted small"> \u2014 Identische Kopie existiert, eine davon ist \u00fcberfl\u00fcssig</span>
        </div>`;
      }
    }

    return `<div class="pf-card">
      <div class="pf-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" ${checked}>
          <span class="pf-name">${esc(fname)}</span>
        </div>
        <div class="pf-meta">
          ${badges.join(' ')}
        </div>
      </div>
      <div class="muted small pathline" style="margin-top:4px;"><code>${esc(relPath || f.path)}</code></div>
      ${fullLine}
      <div class="pf-meta" style="margin-top:6px;">
        <span class="tag">${esc(f.root_label)}</span>
        <span class="size" title="Dateigröße">${esc(f.size_h || '?')}</span>
        <span class="date" title="Zuletzt geändert — meistens das Datum vom Mod-Ersteller">📅 ${esc(f.mtime || '?')}</span>
      </div>
      ${renderTagsUI(f.path)}
      ${sections}
      ${recommendation}
      ${renderNotesUI(f.path)}
      <div class="flex" style="margin-top:10px;">
        <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}" title="Sicher in Quarantäne verschieben">📦 Quarantäne</button>
        <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}" title="Unwiderruflich löschen!">🗑 Löschen</button>
        <button class="btn" data-act="open_folder" data-path="${esc(f.path)}" title="Öffnet den Ordner im Windows Explorer">📂 Ordner öffnen</button>
        <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}" title="Kopiert den Dateipfad in die Zwischenablage">📋 Pfad kopieren</button>
      </div>
    </div>`;
  }).join('');

  document.getElementById('perfile-list').innerHTML = cards || '<p class="muted">Keine Dateien mit Auffälligkeiten.</p>';
}

// View-Toggle
let currentView = 'groups';
document.getElementById('view-toggle').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-view]');
  if (!btn) return;
  const view = btn.dataset.view;
  if (view === currentView) return;
  currentView = view;

  // Toggle-Buttons aktiv/inaktiv
  document.querySelectorAll('#view-toggle button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const groupsView = document.getElementById('groups-view');
  const perfileView = document.getElementById('perfile-view');
  const corruptSec = document.getElementById('corrupt-section');
  const addonSec = document.getElementById('addon-section');
  const conflictSec = document.getElementById('conflict-section');
  const title = document.getElementById('view-title');

  if (view === 'groups') {
    groupsView.style.display = 'block';
    perfileView.style.display = 'none';
    corruptSec.style.display = (window.__DATA && window.__DATA.corrupt && window.__DATA.corrupt.length) ? '' : 'none';
    addonSec.style.display = (window.__DATA && window.__DATA.addon_pairs && window.__DATA.addon_pairs.length) ? '' : 'none';
    conflictSec.style.display = (window.__DATA && window.__DATA.conflicts && window.__DATA.conflicts.length) ? '' : 'none';
    title.textContent = 'Gruppen';
  } else {
    groupsView.style.display = 'none';
    perfileView.style.display = 'block';
    corruptSec.style.display = 'none';
    addonSec.style.display = 'none';
    conflictSec.style.display = 'none';
    title.textContent = 'Pro Datei';
    if (window.__DATA) renderPerFile(window.__DATA);
  }
});

// Per-File Suche
let _pfSearchTimer = null;
document.getElementById('pf-search').addEventListener('input', () => {
  clearTimeout(_pfSearchTimer);
  _pfSearchTimer = setTimeout(() => {
    if (currentView === 'perfile' && window.__DATA) renderPerFile(window.__DATA);
  }, 300);
});

async function reloadData() {
  const data = await loadData();
  window.__DATA = data;
  _SEARCH_INDEX_DIRTY = true;  // Index bei nächster Suche neu bauen
  await Promise.all([loadNotes(), loadTags(), loadCurseForge()]);
  document.getElementById('summary').innerHTML = renderSummary(data);
  document.getElementById('roots').innerHTML = renderRoots(data);
  document.getElementById('groups').innerHTML = renderGroups(data);
  renderCorrupt(data);
  renderAddons(data);
  renderConflicts(data);
  renderOutdated(data);
  renderDependencies(data);
  updateNavBadges(data);
  checkAllOK(data);
  renderStats(data);
  loadQuarantine();
  renderAllMods(data);
  renderNonModFiles(data);
  if (currentView === 'perfile') renderPerFile(data);
  // re-apply checkbox states (selected Set already)
  document.querySelectorAll('input.sel[data-path]').forEach(cb => {
    cb.checked = selected.has(cb.dataset.path);
  });
  updateSelCount();
}

async function doQuarantine(path) {
  const res = await postAction('quarantine', path, {});
  console.log('[QUARANTINE]', path, res);
  setLast('📦 Quarantäne: ' + path);
  addLog('QUARANTINE ' + (res.moved ? 'OK' : 'NOTE') + ' :: ' + path + (res.to ? (' -> ' + res.to) : ''));
  removeRowsForPath(path);
  await reloadData();
  setTimeout(() => reloadData(), 300);
}

async function doDelete(path) {
  if (!confirm('Wirklich löschen?\n\n' + path)) return;
  const res = await postAction('delete', path, {});
  console.log('[DELETE]', path, res);
  setLast('🗑 Löschen: ' + path + ' (deleted=' + String(res.deleted) + ')');
  addLog('DELETE ' + (res.deleted ? 'OK' : 'NOTE') + ' :: ' + path + (res.note ? (' :: ' + res.note) : ''));
  removeRowsForPath(path);
  await reloadData();
  setTimeout(() => reloadData(), 300);
}

async function doRestore(path) {
  const res = await postAction('restore', path, {});
  console.log('[RESTORE]', path, res);
  if (res.restored) {
    setLast('↩️ Zurückgeholt: ' + (res.to || path));
    addLog('RESTORE OK :: ' + path + ' -> ' + (res.to || '?'));
  } else {
    setLast('⚠️ Datei nicht gefunden: ' + path);
    addLog('RESTORE NOTE :: ' + path + ' :: ' + (res.note || ''));
  }
  loadQuarantine();
}

async function doDeleteQ(path) {
  if (!confirm('Datei endgültig löschen?\\n\\n' + path)) return;
  const res = await postAction('delete_q', path, {});
  console.log('[DELETE_Q]', path, res);
  setLast('🗑 Quarantäne-Datei gelöscht: ' + path);
  addLog('DELETE_Q ' + (res.deleted ? 'OK' : 'NOTE') + ' :: ' + path);
  loadQuarantine();
}

async function doOpenFolder(path) {
  const res = await postAction('open_folder', path, {});
  console.log('[OPEN_FOLDER]', path, res);
  setLast('📂 Ordner: ' + path);
  addLog('OPEN_FOLDER :: ' + path);
}

async function copyPath(path) {
  await copyText(path);
  console.log('[COPY]', path);
  setLast('📋 Pfad kopiert: ' + path);
  addLog('COPY :: ' + path);
}

// Selection handling
document.addEventListener('change', (ev) => {
  const cb = ev.target.closest('input.sel[data-path]');
  if (!cb) return;
  const path = cb.dataset.path;
  if (cb.checked) selected.add(path);
  else selected.delete(path);
  updateSelCount();
});

function clearSelection() {
  selected.clear();
  document.querySelectorAll('input.sel[data-path]').forEach(cb => cb.checked = false);
  updateSelCount();
  setBatchStatus('Auswahl geleert.');
}

document.getElementById('btn_clear_sel').addEventListener('click', clearSelection);

// Quarantäne Aktualisieren-Button
document.getElementById('btn_reload_quarantine')?.addEventListener('click', () => loadQuarantine());

function selectGroupAll(gi) {
  const g = window.__DATA?.groups?.[gi];
  if (!g) return;
  for (const f of g.files) selected.add(f.path);
  document.querySelectorAll(`input.sel[data-gi="${gi}"]`).forEach(cb => cb.checked = true);
  updateSelCount();
  setBatchStatus(`Gruppe ${gi}: alle markiert.`);
}

function selectGroupRest(gi) {
  const g = window.__DATA?.groups?.[gi];
  if (!g) return;
  const keep = preferKeepPath(g.files);
  for (const f of g.files) {
    if (f.path !== keep) selected.add(f.path);
  }
  document.querySelectorAll(`input.sel[data-gi="${gi}"]`).forEach(cb => {
    cb.checked = (cb.dataset.path !== keep);
  });
  updateSelCount();
  setBatchStatus(`Gruppe ${gi}: Rest markiert (1 behalten).`);
}

async function batchAction(action, paths, confirmText=null) {
  paths = Array.from(new Set(paths)).filter(Boolean);
  if (paths.length === 0) return;

  if (confirmText) {
    if (!confirm(confirmText)) return;
  }

  document.body.classList.add('busy');
  try {
    let ok = 0, fail = 0;
    for (let i = 0; i < paths.length; i++) {
      const p = paths[i];
      setBatchStatus(`${action.toUpperCase()}… ${i+1}/${paths.length}\n${p}`);
      try {
        if (action === 'delete') {
          const res = await postAction('delete', p, {});
          console.log('[BATCH_DELETE]', p, res);
          addLog(`BATCH DELETE ${res.deleted ? 'OK' : 'NOTE'} :: ${p}` + (res.note ? (' :: ' + res.note) : ''));
        } else if (action === 'quarantine') {
          const res = await postAction('quarantine', p, {});
          console.log('[BATCH_QUARANTINE]', p, res);
          addLog(`BATCH QUARANTINE ${res.moved ? 'OK' : 'NOTE'} :: ${p}` + (res.to ? (' -> ' + res.to) : '') + (res.note ? (' :: ' + res.note) : ''));
        }
        removeRowsForPath(p);
        ok += 1;
      } catch (e) {
        console.error('[BATCH_ERR]', action, p, e);
        addLog(`BATCH ERROR ${action} :: ${p} :: ${e.message}`);
        fail += 1;
      }
    }
    setLast(`Batch ${action}: OK ${ok}, Fehler ${fail}`);
    setBatchStatus(`Fertig: ${action} | OK ${ok}, Fehler ${fail}`);
    clearSelection();
    await reloadData();
    setTimeout(() => reloadData(), 500);
  } finally {
    document.body.classList.remove('busy');
  }
}

document.getElementById('btn_q_sel').addEventListener('click', async () => {
  await batchAction('quarantine', Array.from(selected), `📦 ${selected.size} Dateien in Quarantäne verschieben?`);
});

document.getElementById('btn_d_sel').addEventListener('click', async () => {
  await batchAction('delete', Array.from(selected), `🗑 ${selected.size} Dateien WIRKLICH löschen?\n\nDas kann man nicht rückgängig machen!`);
});

document.getElementById('reload').addEventListener('click', async () => {
  try {
    // Trigger real rescan with progress
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'rescan'})
    });
    const rj = await r.json();
    if (!rj.ok && rj.error === 'scan already running') {
      alert('Ein Scan läuft bereits!');
      return;
    }
    // Show progress bar and start polling
    document.getElementById('progress-section').style.display = '';
    setLast('🔄 Scan gestartet…');
    addLog('RESCAN STARTED');
    pollProgress();
  } catch (e) {
    alert('Fehler: ' + e.message);
  }
});

let _progressTimer = null;
async function pollProgress() {
  try {
    const r = await fetch('/api/progress?token=' + TOKEN);
    const p = await r.json();
    const section = document.getElementById('progress-section');
    const bar = document.getElementById('progress-bar');
    const pct = document.getElementById('progress-pct');
    const phase = document.getElementById('progress-phase');
    const detail = document.getElementById('progress-detail');

    const phaseNames = {
      'collect': '📁 Sammle Dateien…',
      'name': '🔤 Prüfe Dateinamen…',
      'hashing_init': '#️⃣ Vorbereitung Hash-Prüfung…',
      'hashing': '#️⃣ Hash-Prüfung…',
      'integrity': '🔍 Integritäts-Check…',
      'conflicts': '⚡ Konflikte prüfen…',
      'deep': '🔬 Tiefenanalyse…',
      'finalize': '✨ Finalisiere…',
      'done': '✅ Fertig!',
      'error': '❌ Fehler',
    };
    phase.textContent = phaseNames[p.phase] || p.phase || 'Läuft…';
    detail.textContent = p.msg || '';

    if (p.total > 0 && p.cur > 0) {
      const percent = Math.min(100, Math.round((p.cur / p.total) * 100));
      bar.style.width = percent + '%';
      pct.textContent = percent + '%';
    } else if (p.phase === 'done') {
      bar.style.width = '100%';
      pct.textContent = '100%';
    } else {
      // indeterminate — pulsing animation
      bar.style.width = '30%';
      bar.style.animation = 'pulse 1.5s ease-in-out infinite alternate';
      pct.textContent = '';
    }

    if (p.done) {
      bar.style.animation = '';
      bar.style.width = '100%';
      bar.style.background = 'linear-gradient(90deg,#22c55e,#4ade80)';
      pct.textContent = '✅';
      setLast('✅ Scan abgeschlossen');
      addLog('RESCAN DONE');
      // Reload data and hide progress after delay
      setTimeout(async () => {
        await reloadData();
        setTimeout(() => { section.style.display = 'none'; bar.style.background = ''; }, 2000);
      }, 500);
      return; // stop polling
    }
    if (p.error) {
      bar.style.animation = '';
      bar.style.background = 'linear-gradient(90deg,#ef4444,#f87171)';
      phase.textContent = '❌ Fehler: ' + p.error;
      pct.textContent = '❌';
      setLast('❌ Scan-Fehler');
      addLog('RESCAN ERROR :: ' + p.error);
      setTimeout(() => { section.style.display = 'none'; bar.style.background = ''; }, 5000);
      return; // stop polling
    }
    // Continue polling
    _progressTimer = setTimeout(pollProgress, 400);
  } catch (e) {
    console.error('[PROGRESS_POLL]', e);
    setTimeout(pollProgress, 1000);
  }
}

// ---- Mod-Import-Manager: Drag & Drop + Upload ----
(function initImportDropzone() {
  const dropzone = document.getElementById('import-dropzone');
  const fileInput = document.getElementById('import-file-input');
  const folderInput = document.getElementById('import-folder-input');
  if (!dropzone || !fileInput) return;

  // Klick auf Dropzone -> Dateiauswahl öffnen
  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('button')) return; // Ordner-Button nicht doppelt
    fileInput.click();
  });

  // Drag-Events
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('drag-active');
  });
  dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-active');
  });
  dropzone.addEventListener('drop', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-active');
    // webkitGetAsEntry um Ordner rekursiv zu lesen
    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      const entries = [];
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
        if (entry) entries.push(entry);
      }
      if (entries.length > 0) {
        const statusEl = document.getElementById('import-status');
        statusEl.innerHTML = '📂 Lese Ordnerstruktur…';
        const collected = await collectFilesFromEntries(entries, '');
        if (collected.length > 0) {
          await handleUploadFiles(collected);
        } else {
          statusEl.innerHTML = '⚠️ Keine Dateien im Ordner gefunden.';
        }
        return;
      }
    }
    // Fallback: normale Dateien
    if (e.dataTransfer.files.length > 0) {
      const plain = [...e.dataTransfer.files].map(f => ({file: f, relativePath: ''}));
      await handleUploadFiles(plain);
    }
  });

  // Einzelne Dateien auswählen
  fileInput.addEventListener('change', async () => {
    if (fileInput.files.length > 0) {
      const plain = [...fileInput.files].map(f => ({file: f, relativePath: ''}));
      await handleUploadFiles(plain);
    }
    fileInput.value = '';
  });

  // Ordner auswählen (webkitdirectory)
  if (folderInput) {
    folderInput.addEventListener('change', async () => {
      if (folderInput.files.length > 0) {
        // webkitRelativePath enthält den vollen relativen Pfad inkl. Dateiname
        const items = [...folderInput.files].map(f => {
          // webkitRelativePath z.B. "ModFolder/subfolder/file.package"
          const parts = f.webkitRelativePath.split('/');
          // Alles außer der Datei selbst = relativer Ordnerpfad
          const relDir = parts.slice(0, -1).join('/');
          return {file: f, relativePath: relDir};
        });
        await handleUploadFiles(items);
      }
      folderInput.value = '';
    });
  }

  // Rekursiv alle Dateien aus FileSystemEntry-Einträgen sammeln
  async function collectFilesFromEntries(entries, basePath) {
    const results = [];
    for (const entry of entries) {
      if (entry.isFile) {
        try {
          const file = await new Promise((res, rej) => entry.file(res, rej));
          results.push({file, relativePath: basePath});
        } catch(e) { console.warn('[ENTRY]', e); }
      } else if (entry.isDirectory) {
        const subPath = basePath ? basePath + '/' + entry.name : entry.name;
        const dirReader = entry.createReader();
        // readEntries kann in Batches kommen, daher Loop
        const allSub = [];
        let batch;
        do {
          batch = await new Promise((res, rej) => dirReader.readEntries(res, rej));
          allSub.push(...batch);
        } while (batch.length > 0);
        const subFiles = await collectFilesFromEntries(allSub, subPath);
        results.push(...subFiles);
      }
    }
    return results;
  }

  // items = [{file: File, relativePath: 'sub/folder'}, ...]
  async function handleUploadFiles(items) {
    const statusEl = document.getElementById('import-status');
    const resultsEl = document.getElementById('import-results');
    const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';
    const targetRow = document.getElementById('import-target-row');

    const modItems = items; // Alle Dateien übernehmen (1:1 wie aus RAR/ZIP)
    if (modItems.length === 0) {
      statusEl.innerHTML = '⚠️ Keine Dateien gefunden.';
      return;
    }

    // Ordnerstruktur-Info anzeigen
    const hasFolders = modItems.some(it => it.relativePath);
    const folderSet = new Set(modItems.filter(it => it.relativePath).map(it => it.relativePath));
    if (hasFolders) {
      statusEl.innerHTML = `📤 Lade ${modItems.length} Datei(en) in ${folderSet.size} Ordner(n) hoch…`;
    } else {
      statusEl.innerHTML = `📤 Lade ${modItems.length} Datei(en) hoch…`;
    }
    resultsEl.innerHTML = '';
    targetRow.style.display = '';

    let newCount = 0, identicalCount = 0, updateCount = 0;
    const updateItems = [];
    const createdFolders = new Set();

    for (let i = 0; i < modItems.length; i++) {
      const item = modItems[i];
      const displayName = item.relativePath ? item.relativePath + '/' + item.file.name : item.file.name;
      statusEl.innerHTML = `📤 Lade ${i+1}/${modItems.length}: <b>${displayName}</b>…`;

      try {
        const b64 = await fileToBase64(item.file);
        const r = await fetch('/api/action', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({
            token: TOKEN, action: 'import_upload',
            filename: item.file.name, filedata: b64,
            subfolder, relative_path: item.relativePath || ''
          })
        });
        const d = await r.json();
        if (!d.ok) {
          console.error(`[UPLOAD] ${displayName}: ${d.error}`);
          continue;
        }
        if (d.status === 'new') {
          newCount++;
          if (item.relativePath) createdFolders.add(item.relativePath);
        }
        else if (d.status === 'identical') { identicalCount++; }
        else if (d.status === 'update') { updateCount++; updateItems.push({item, data: d, displayName}); }
      } catch (e) {
        console.error('[UPLOAD]', e);
      }
    }

    // Zusammenfassung
    let parts = [];
    if (newCount) parts.push(`📥 ${newCount} neu importiert`);
    if (createdFolders.size > 0) parts.push(`📁 ${createdFolders.size} Unterordner erstellt`);
    if (identicalCount) parts.push(`✅ ${identicalCount} übersprungen (identisch)`);
    if (updateCount) parts.push(`🔄 ${updateCount} Updates`);
    statusEl.innerHTML = `<b>Fertig!</b> ${parts.join(' · ')}`;

    // Update-Tabelle
    if (updateItems.length > 0) {
      let html = '<div style="margin:10px 0 6px;"><b>⚠️ Diese Dateien brauchen deine Entscheidung:</b></div>';
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="border-bottom:1px solid #334155;text-align:left;"><th style="padding:6px;">Datei</th><th style="padding:6px;">Größe</th><th style="padding:6px;">Vorhandene Datei</th><th style="padding:6px;">Aktion</th></tr></thead><tbody>';

      updateItems.forEach(ui => {
        const match = ui.data.matches.find(m => m.relation === 'update') || ui.data.matches[0];
        const tmpEsc = (ui.data.tmp_path||'').replace(/\\/g,'\\\\');
        const replEsc = (match.path||'').replace(/\\/g,'\\\\');
        const existName = match.path.split('\\').pop().split('/').pop();
        const existSize = match.existing_size_h || '?';

        html += `<tr data-upload-name="${ui.displayName}" style="border-bottom:1px solid #1e293b;">`;
        html += `<td style="padding:6px;">${ui.displayName}</td>`;
        html += `<td style="padding:6px;">${ui.data.size_h}</td>`;
        html += `<td style="padding:6px;font-size:12px;" class="muted">${existName} (${existSize})</td>`;
        html += `<td style="padding:6px;">`;
        html += `<button class="btn btn-ok" style="padding:3px 10px;font-size:12px;" onclick="confirmUploadReplace('${tmpEsc}','${replEsc}',this)">🔄 Ersetzen</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="this.closest('tr').style.display='none'">⏭ Überspringen</button>`;
        html += `</td></tr>`;
      });
      html += '</tbody></table>';
      resultsEl.innerHTML = html;
    } else if (newCount > 0) {
      resultsEl.innerHTML = '<div style="padding:12px;text-align:center;color:#22c55e;">✅ Alle neuen Mods wurden automatisch importiert!' + (createdFolders.size > 0 ? ' Ordnerstruktur wurde 1:1 übernommen.' : '') + '</div>';
    }
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const arrBuf = reader.result;
        const bytes = new Uint8Array(arrBuf);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        resolve(btoa(binary));
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  }
})();

// Upload-Ersetzen bestätigen
async function confirmUploadReplace(tmpPath, replacePath, btn) {
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_upload_confirm', tmp_path: tmpPath, replace_path: replacePath})
    });
    const d = await r.json();
    if (d.ok) {
      const row = btn.closest('tr');
      const actCell = row.querySelector('td:last-child');
      if (actCell) actCell.innerHTML = '<span style="color:#22c55e">✅ Aktualisiert</span>';
      row.style.opacity = '0.6';
      setLast('📥 Update: ' + replacePath.split('\\').pop().split('/').pop());
    } else {
      alert('Fehler: ' + (d.error||'unbekannt'));
    }
  } catch (e) {
    alert('Fehler: ' + e.message);
  }
}

// ---- Mod-Import-Manager: Ordner-Scan ----
document.getElementById('btn-import-scan').addEventListener('click', async () => {
  const source = document.getElementById('import-source').value.trim();
  if (!source) { alert('Bitte einen Quell-Ordner angeben!'); return; }
  const statusEl = document.getElementById('import-status');
  const resultsEl = document.getElementById('import-results');
  const actionsEl = document.getElementById('import-actions');
  const targetRow = document.getElementById('import-target-row');
  statusEl.textContent = '🔍 Scanne Ordner…';
  resultsEl.innerHTML = '';
  actionsEl.style.display = 'none';
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_scan', source})
    });
    const d = await r.json();
    if (!d.ok) { statusEl.textContent = '❌ ' + (d.error||'Fehler'); return; }
    if (d.count === 0) { statusEl.textContent = '⚠️ Keine .package / .ts4script Dateien gefunden.'; return; }
    statusEl.textContent = `✅ ${d.count} Mod-Datei(en) gefunden — prüfe auf Duplikate…`;
    targetRow.style.display = '';
    window.__importFiles = d.files;
    window.__importChecks = {};

    // Phase 1: Alle Dateien prüfen und sofort neue auto-importieren
    let checkedCount = 0;
    let autoImported = 0, updateCount = 0, identicalCount = 0, similarCount = 0;
    const needsDecision = []; // Nur Updates/Ähnliche brauchen User-Entscheidung
    const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';

    for (const f of d.files) {
      const cr = await fetch('/api/action', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({token: TOKEN, action: 'import_check', source_path: f.path})
      });
      const cd = await cr.json();
      checkedCount++;
      statusEl.textContent = `🔍 Prüfe ${checkedCount}/${d.count}…`;
      const st = cd.ok ? cd.status : 'error';
      window.__importChecks[f.path] = cd;

      if (st === 'new') {
        // Direkt importieren — kein Nachfragen nötig
        const ir = await fetch('/api/action', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({token: TOKEN, action: 'import_execute', source_path: f.path, subfolder, mode: 'copy', replace_path: ''})
        });
        const id = await ir.json();
        if (id.ok) autoImported++;
        statusEl.textContent = `📥 Importiere ${checkedCount}/${d.count}… (${autoImported} neu importiert)`;
      } else if (st === 'identical') {
        identicalCount++;
      } else if (st === 'update') {
        updateCount++;
        needsDecision.push({file: f, check: cd, status: st});
      } else if (st === 'similar') {
        similarCount++;
        needsDecision.push({file: f, check: cd, status: st});
      }
    }

    // Phase 2: Zusammenfassung anzeigen
    let summary = [];
    if (autoImported) summary.push(`📥 ${autoImported} neu importiert`);
    if (identicalCount) summary.push(`✅ ${identicalCount} übersprungen (identisch)`);
    if (updateCount) summary.push(`🔄 ${updateCount} Updates`);
    if (similarCount) summary.push(`🔶 ${similarCount} ähnlich`);
    statusEl.innerHTML = `<b>Fertig!</b> ${summary.join(' · ')}`;

    // Phase 3: Nur Dateien anzeigen die eine Entscheidung brauchen
    if (needsDecision.length > 0) {
      let html = '<div style="margin:10px 0 6px;"><b>⚠️ Diese Dateien brauchen deine Entscheidung:</b></div>';
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="border-bottom:1px solid #334155;text-align:left;"><th style="padding:6px;">Datei</th><th style="padding:6px;">Größe</th><th style="padding:6px;">Status</th><th style="padding:6px;">Vorhandene Datei</th><th style="padding:6px;">Aktion</th></tr></thead><tbody>';

      needsDecision.forEach((item, idx) => {
        const f = item.file;
        const cd = item.check;
        const st = item.status;
        const statusLabel = st === 'update' ? '<span style="color:#f59e0b">🔄 Update</span>' : '<span style="color:#f97316">🔶 Ähnlich</span>';
        const matchFile = cd.matches && cd.matches[0] ? cd.matches[0] : null;
        const matchInfo = matchFile ? `<span title="${matchFile.path}">${matchFile.name} (${matchFile.size_h})</span>` : '–';
        const replacePath = matchFile ? matchFile.path.replace(/\\/g,'\\\\') : '';
        const srcEsc = f.path.replace(/\\/g,'\\\\');

        html += `<tr data-src="${f.path}" data-status="${st}" style="border-bottom:1px solid #1e293b;">`;
        html += `<td style="padding:6px;">${f.name}</td>`;
        html += `<td style="padding:6px;">${f.size_h}</td>`;
        html += `<td style="padding:6px;">${statusLabel}</td>`;
        html += `<td style="padding:6px;font-size:12px;" class="muted">${matchInfo}</td>`;
        html += `<td style="padding:6px;">`;
        html += `<button class="btn btn-ok" style="padding:3px 10px;font-size:12px;" onclick="importFile('${srcEsc}','update','${replacePath}')">🔄 Ersetzen</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="importFile('${srcEsc}','copy','')">📥 Zusätzlich</button> `;
        html += `<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;" onclick="this.closest('tr').style.display='none'">⏭ Überspringen</button>`;
        html += `</td></tr>`;
      });
      html += '</tbody></table>';
      resultsEl.innerHTML = html;

      if (updateCount > 0) actionsEl.style.display = 'flex';
    } else {
      resultsEl.innerHTML = '<div style="padding:12px;text-align:center;color:#22c55e;">✅ Alle neuen Mods wurden automatisch importiert! Keine weiteren Aktionen nötig.</div>';
    }
  } catch (e) {
    statusEl.textContent = '❌ Fehler: ' + e.message;
  }
});

async function importFile(sourcePath, mode, replacePath) {
  const subfolder = document.getElementById('import-target-subfolder')?.value?.trim() || '';
  try {
    const r = await fetch('/api/action', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token: TOKEN, action: 'import_execute', source_path: sourcePath, subfolder, mode, replace_path: replacePath})
    });
    const d = await r.json();
    if (d.ok) {
      // Zeile als erledigt markieren
      const rows = document.querySelectorAll('#import-results tr[data-src]');
      rows.forEach(row => {
        if (row.dataset.src === sourcePath) {
          const actCell = row.querySelector('td:last-child');
          if (actCell) actCell.innerHTML = `<span style="color:#22c55e">✅ ${d.mode === 'update' ? 'Aktualisiert' : 'Importiert'}</span>`;
          row.style.opacity = '0.6';
        }
      });
      setLast(`📥 ${mode === 'update' ? 'Update' : 'Import'}: ${sourcePath.split('\\').pop()}`);
    } else {
      alert('Fehler: ' + (d.error||'unbekannt'));
    }
  } catch (e) {
    alert('Fehler: ' + e.message);
  }
}

// Batch-Import: Alle Updates übernehmen
document.getElementById('btn-import-all-update').addEventListener('click', async () => {
  const rows = document.querySelectorAll('#import-results tr[data-status="update"], #import-results tr[data-status="similar"]');
  const visible = [...rows].filter(r => r.style.display !== 'none');
  if (visible.length === 0) { alert('Keine offenen Updates/Ähnliche mehr.'); return; }
  if (!confirm(`🔄 ${visible.length} Mod(s) aktualisieren? Die vorhandenen Dateien werden überschrieben!`)) return;
  for (const row of visible) {
    const src = row.dataset.src;
    const check = window.__importChecks?.[src];
    const replacePath = check?.matches?.[0]?.path || '';
    await importFile(src, 'update', replacePath);
  }
  setLast(`🔄 ${visible.length} Mods aktualisiert`);
});

// Import-Liste leeren
document.getElementById('btn-import-clear').addEventListener('click', () => {
  document.getElementById('import-results').innerHTML = '';
  document.getElementById('import-status').textContent = '';
  document.getElementById('import-actions').style.display = 'none';
  document.getElementById('import-target-row').style.display = 'none';
  window.__importFiles = null;
  window.__importChecks = {};
});

// ---- Watcher-Polling: Prüft ob Auto-Rescan läuft ----
let _watcherTimer = null;
let _lastWatcherMsg = '';
async function pollWatcher() {
  try {
    const r = await fetch('/api/watcher?token=' + TOKEN);
    const w = await r.json();
    const banner = document.getElementById('watcher-banner');
    const filesSpan = document.getElementById('watcher-files');
    const eventSpan = document.getElementById('watcher-event');

    if (w.active) {
      banner.style.display = 'flex';
      filesSpan.textContent = w.files_watched;
      if (w.auto_rescan_msg && w.auto_rescan_msg !== _lastWatcherMsg) {
        _lastWatcherMsg = w.auto_rescan_msg;
        eventSpan.textContent = w.auto_rescan_msg;
        // Auto-Rescan wurde gestartet — Progress-Polling starten
        if (w.auto_rescan_msg.includes('🔄')) {
          const section = document.getElementById('progress-section');
          if (section) section.style.display = '';
          if (!_progressTimer) pollProgress();
        }
      } else if (w.last_event) {
        eventSpan.textContent = w.last_event;
      }
    } else {
      banner.style.display = 'none';
    }
  } catch (e) {
    console.error('[WATCHER_POLL]', e);
  }
  _watcherTimer = setTimeout(pollWatcher, 3000);
}
// Watcher-Polling starten
pollWatcher();

// Group and per-file actions (event delegation)
document.getElementById('groups').addEventListener('click', async (ev) => {
  // group actions
  const gbtn = ev.target.closest('button[data-gact]');
  if (gbtn) {
    const gact = gbtn.dataset.gact;
    const gi = Number(gbtn.dataset.gi);
    const g = window.__DATA?.groups?.[gi];
    if (!g) return;

    if (gact === 'ignore_group') {
      const gkey = gbtn.dataset.gkey;
      const gtype = gbtn.dataset.gtype;
      try {
        await postAction('ignore_group', '', { group_key: gkey, group_type: gtype });
        setLast('✅ Gruppe als korrekt markiert: ' + gkey);
        addLog('IGNORE_GROUP ' + gtype + '::' + gkey);
        await reloadData();
      } catch(e) { alert('Fehler: ' + e.message); }
      return;
    }
    if (gact === 'unignore_group') {
      const gkey = gbtn.dataset.gkey;
      const gtype = gbtn.dataset.gtype;
      try {
        await postAction('unignore_group', '', { group_key: gkey, group_type: gtype });
        setLast('↩️ Gruppe wird wieder gemeldet: ' + gkey);
        addLog('UNIGNORE_GROUP ' + gtype + '::' + gkey);
        await reloadData();
      } catch(e) { alert('Fehler: ' + e.message); }
      return;
    }
    if (gact === 'select_all') selectGroupAll(gi);
    else if (gact === 'select_rest') selectGroupRest(gi);
    else if (gact === 'quarantine_rest') {
      const keep = preferKeepPath(g.files);
      const rest = g.files.filter(f => f.path !== keep).map(f => f.path);
      await batchAction('quarantine', rest, `📦 Rest der Gruppe in Quarantäne?\n\nBehalte:\n${keep}\n\nAnzahl: ${rest.length}`);
    }
    else if (gact === 'delete_rest') {
      const keep = preferKeepPath(g.files);
      const rest = g.files.filter(f => f.path !== keep).map(f => f.path);
      await batchAction('delete', rest, `🗑 Rest der Gruppe WIRKLICH löschen?\n\nBehalte:\n${keep}\n\nAnzahl: ${rest.length}`);
    }
    return;
  }

  // per-file actions
  const btn = ev.target.closest('button[data-act]');
  if (!btn) return;
  const act = btn.dataset.act;
  const path = btn.dataset.path;

  try {
    if (act === 'quarantine') await doQuarantine(path);
    else if (act === 'delete') await doDelete(path);
    else if (act === 'open_folder') await doOpenFolder(path);
    else if (act === 'copy') await copyPath(path);
    else if (act === 'restore') await doRestore(path);
    else if (act === 'delete_q') await doDeleteQ(path);
  } catch (e) {
    alert('Fehler: ' + e.message);
    console.error('[ACTION_ERR]', act, path, e);
    setLast('❌ Fehler: ' + e.message);
    addLog('ERROR ' + act + ' :: ' + path + ' :: ' + e.message);
  }
});

let _groupsFilterTimer = null;
function _applyGroupsFilter() {
  if (window.__DATA) {
    document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
    if (currentView === 'perfile') renderPerFile(window.__DATA);
  }
}
for (const id of ['q','f_name','f_content','f_similar','g_mod','show_full','keep_ord1','f_show_ignored']) {
  const el = document.getElementById(id);
  if (id === 'q') {
    // Textsuche: debounce 300ms
    el.addEventListener('input', () => {
      clearTimeout(_groupsFilterTimer);
      _groupsFilterTimer = setTimeout(_applyGroupsFilter, 300);
    });
  } else {
    // Checkboxen: sofort anwenden
    el.addEventListener('input', _applyGroupsFilter);
    el.addEventListener('change', _applyGroupsFilter);
  }
}

// initial load
reloadData().then(()=>{
  setLast('✅ Daten geladen');
  addLog('PAGE LOAD');
  updateSelCount();
}).catch(e=>{
  document.getElementById('groups').innerHTML = '<p class="muted">Fehler: ' + esc(e.message) + '</p>';
  setLast('❌ Fehler beim Laden: ' + e.message);
  addLog('LOAD ERROR :: ' + e.message);
});

// Fehler-Analyse immer laden (unabhängig von Duplikat-Daten)
loadErrors();

// ---- Fehler-Analyse ----

async function loadErrors() {
  document.getElementById('error-summary').innerHTML = 'Suche Sims 4 Verzeichnis und lese Fehlerlogs…';
  try {
    const r = await fetch('/api/errors?token=' + encodeURIComponent(TOKEN));
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'unknown');
    if (j.note) {
      document.getElementById('error-summary').innerHTML = '⚠️ ' + esc(j.note);
      return;
    }
    renderErrors(j);
  } catch(e) {
    document.getElementById('error-summary').innerHTML = '<span style="color:#ef4444;">❌ Fehler beim Laden: ' + esc(e.message) + '</span>';
  }
}

function schwereIcon(s) {
  if (s === 'hoch') return '🔴';
  if (s === 'mittel') return '🟡';
  if (s === 'niedrig') return '🟢';
  return '⚪';
}

function schwereLabel(s) {
  if (s === 'hoch') return 'Schwerwiegend';
  if (s === 'mittel') return 'Mittel';
  if (s === 'niedrig') return 'Gering';
  return 'Unbekannt';
}

function renderErrors(data) {
  const errors = data.errors || [];
  const simsDir = data.sims4_dir || '(nicht gefunden)';

  const hoch = errors.filter(e => e.schwere === 'hoch').length;
  const mittel = errors.filter(e => e.schwere === 'mittel').length;
  const niedrig = errors.filter(e => e.schwere === 'niedrig').length;
  const unbekannt = errors.filter(e => e.schwere === 'unbekannt').length;

  let summaryHtml = '';
  if (errors.length === 0) {
    summaryHtml = '✅ <b>Keine Fehler gefunden!</b> Deine Fehlerlog-Dateien sind sauber.';
  } else {
    summaryHtml = `<b>${errors.length} Fehler</b> gefunden in <code>${esc(simsDir)}</code><br>`;
    if (hoch > 0) summaryHtml += `<span class="err-schwere hoch">${hoch}x Schwerwiegend</span> `;
    if (mittel > 0) summaryHtml += `<span class="err-schwere mittel">${mittel}x Mittel</span> `;
    if (niedrig > 0) summaryHtml += `<span class="err-schwere niedrig">${niedrig}x Gering</span> `;
    if (unbekannt > 0) summaryHtml += `<span class="err-schwere unbekannt">${unbekannt}x Unbekannt</span> `;
  }
  // Snapshot-Info (neu/bekannt/behoben)
  const snap = data.snapshot;
  if (snap && errors.length > 0) {
    summaryHtml += `<br><span style="font-size:12px; color:#94a3b8;">`;
    if (snap.fehler_neu > 0) summaryHtml += `🆕 ${snap.fehler_neu} neu `;
    if (snap.fehler_bekannt > 0) summaryHtml += `🔄 ${snap.fehler_bekannt} bekannt `;
    if (snap.fehler_behoben > 0) summaryHtml += `✅ ${snap.fehler_behoben} seit letztem Mal behoben `;
    summaryHtml += `</span>`;
  }
  document.getElementById('error-summary').innerHTML = summaryHtml;

  let html = '';
  for (const err of errors) {
    const modsHtml = (err.betroffene_mods && err.betroffene_mods.length > 0)
      ? `<div class="err-mods"><span class="muted small">Betroffene Mod-Dateien:</span> ${err.betroffene_mods.map(m => `<span class="err-mod-tag">${esc(m)}</span>`).join('')}</div>`
      : '';

    const rawHtml = err.raw_snippet
      ? `<details class="err-raw"><summary>📄 Originaler Log-Auszug anzeigen</summary><pre>${esc(err.raw_snippet)}</pre></details>`
      : '';

    const statusBadge = err.status === 'neu'
      ? '<span class="err-status neu">🆕 NEU</span>'
      : err.status === 'bekannt'
        ? '<span class="err-status bekannt">🔄 BEKANNT</span>'
        : '';

    html += `
    <div class="err-card ${err.schwere}">
      <div class="flex" style="align-items:center; gap:8px; flex-wrap:wrap;">
        <span>${schwereIcon(err.schwere)}</span>
        <span class="err-title">${esc(err.titel)}</span>
        <span class="err-schwere ${err.schwere}">${schwereLabel(err.schwere)}</span>
        ${statusBadge}
      </div>
      <div class="err-explain">${esc(err.erklaerung)}</div>
      <div class="err-solution">💡 <b>Lösung:</b> ${esc(err.loesung)}</div>
      ${modsHtml}
      <div class="err-meta">
        <span>📁 ${esc(err.datei)}</span>
        <span>📅 ${esc(err.datum)}</span>
        <span>📂 ${esc(err.kategorie)}</span>
      </div>
      ${rawHtml}
    </div>`;
  }

  document.getElementById('error-list').innerHTML = html;
}

document.getElementById('btn_reload_errors').addEventListener('click', () => {
  document.getElementById('error-summary').innerHTML = 'Lade Fehler…';
  document.getElementById('error-list').innerHTML = '';
  loadErrors();
});

document.getElementById('btn_save_html').addEventListener('click', () => {
  const html = document.documentElement.outerHTML;
  const blob = new Blob(['<!DOCTYPE html>\n' + html], {type: 'text/html; charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const ts = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
  a.href = url;
  a.download = 'Sims4_Scanner_' + ts + '.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  setLast('📄 HTML gespeichert als ' + a.download);
});

// ---- History & Mod-Inventar ----

loadHistory();

async function loadHistory() {
  try {
    const r = await fetch('/api/history?token=' + encodeURIComponent(TOKEN));
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'unknown');
    renderHistory(j);
  } catch(e) {
    document.getElementById('mod-snapshot-content').innerHTML = '<span style="color:#ef4444;">❌ ' + esc(e.message) + '</span>';
    document.getElementById('scan-history-content').innerHTML = '';
  }
}

function renderHistory(data) {
  // Mod-Snapshot
  const ms = data.mod_snapshot || {};
  if (ms.mods_gesamt > 0) {
    let modsHtml = `<div class="mod-stats">
      <div class="mod-stat"><div class="val">${ms.mods_gesamt}</div><div class="lbl">Mods gesamt</div></div>
      <div class="mod-stat"><div class="val">${ms.mods_package}</div><div class="lbl">.package</div></div>
      <div class="mod-stat"><div class="val">${ms.mods_script}</div><div class="lbl">.ts4script</div></div>
      <div class="mod-stat"><div class="val">${esc(ms.groesse_gesamt_h)}</div><div class="lbl">Gesamtgröße</div></div>
    </div>`;

    // Änderungen anzeigen
    const hasChanges = ms.neue > 0 || ms.entfernt > 0 || ms.geaendert > 0;
    if (hasChanges) {
      const ch = ms.changes || {};
      let changesHtml = '<div style="margin-top:8px;">';
      if (ms.neue > 0) changesHtml += `<span class="change-tag neu">+${ms.neue} neue Mods</span> `;
      if (ms.entfernt > 0) changesHtml += `<span class="change-tag entfernt">-${ms.entfernt} entfernte Mods</span> `;
      if (ms.geaendert > 0) changesHtml += `<span class="change-tag geaendert">~${ms.geaendert} geänderte Mods</span> `;
      changesHtml += '</div>';

      // Details aufklappbar
      if (ch.neue_mods && ch.neue_mods.length > 0) {
        changesHtml += `<details style="margin-top:8px;"><summary style="cursor:pointer; color:#86efac; font-size:12px;">📥 Neue Mods anzeigen (${ch.neue_mods.length})</summary>
          <div style="margin-top:4px;">${ch.neue_mods.map(m => `<span class="change-tag neu">${esc(m)}</span>`).join('')}</div></details>`;
      }
      if (ch.entfernte_mods && ch.entfernte_mods.length > 0) {
        changesHtml += `<details style="margin-top:4px;"><summary style="cursor:pointer; color:#fca5a5; font-size:12px;">📤 Entfernte Mods anzeigen (${ch.entfernte_mods.length})</summary>
          <div style="margin-top:4px;">${ch.entfernte_mods.map(m => `<span class="change-tag entfernt">${esc(m)}</span>`).join('')}</div></details>`;
      }
      if (ch.geaenderte_mods && ch.geaenderte_mods.length > 0) {
        changesHtml += `<details style="margin-top:4px;"><summary style="cursor:pointer; color:#fde68a; font-size:12px;">✏️ Geänderte Mods anzeigen (${ch.geaenderte_mods.length})</summary>
          <div style="margin-top:4px;">${ch.geaenderte_mods.map(m => `<span class="change-tag geaendert">${esc(m)}</span>`).join('')}</div></details>`;
      }

      document.getElementById('mod-changes').style.display = 'block';
      document.getElementById('mod-changes-content').innerHTML = changesHtml;
    }

    document.getElementById('mod-snapshot-content').innerHTML = modsHtml;
  } else {
    document.getElementById('mod-snapshot-content').innerHTML = '<span class="muted">Noch kein Mod-Inventar vorhanden. Starte einen Scan um eines zu erstellen.</span>';
  }

  // Scan-History Tabelle
  const hist = data.scan_history || [];
  if (hist.length === 0) {
    document.getElementById('scan-history-content').innerHTML = '<span class="muted">Noch keine Scan-History vorhanden.</span>';
    return;
  }

  let tableHtml = `<table class="hist-table">
    <thead><tr>
      <th>Datum</th>
      <th>Dateien</th>
      <th>Name-Duplikate</th>
      <th>Inhalt-Duplikate</th>
    </tr></thead><tbody>`;

  for (const h of hist) {
    tableHtml += `<tr>
      <td>${esc(h.timestamp || '')}</td>
      <td>${h.dateien_gesamt || 0}</td>
      <td>${h.duplikate_name_gruppen || 0} Gruppen / ${h.duplikate_name_dateien || 0} Dateien</td>
      <td>${h.duplikate_inhalt_gruppen || 0} Gruppen / ${h.duplikate_inhalt_dateien || 0} Dateien</td>
    </tr>`;
  }
  tableHtml += '</tbody></table>';
  document.getElementById('scan-history-content').innerHTML = tableHtml;

  // Verlaufs-Diagramm rendern
  renderHistoryChart(hist);
}

function renderHistoryChart(hist) {
  const chartArea = document.getElementById('history-chart-area');
  if (!hist || hist.length < 2) {
    chartArea.style.display = 'none';
    return;
  }
  chartArea.style.display = '';

  const canvas = document.getElementById('history-chart');
  const ctx = canvas.getContext('2d');
  const container = canvas.parentElement;

  // Set canvas size
  canvas.width = container.clientWidth - 24;
  canvas.height = 196;
  const W = canvas.width;
  const H = canvas.height;
  const pad = {top: 20, right: 20, bottom: 40, left: 50};

  // Data arrays (reversed since hist is newest-first)
  const data = [...hist].reverse();
  const labels = data.map(h => {
    const ts = h.timestamp || '';
    return ts.substring(0, 10); // YYYY-MM-DD
  });
  const values = data.map(h => h.dateien_gesamt || 0);
  const dupes = data.map(h => (h.duplikate_name_dateien || 0) + (h.duplikate_inhalt_dateien || 0));

  const maxVal = Math.max(...values, ...dupes, 1);
  const minVal = 0;

  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  function x(i) { return pad.left + (i / (data.length - 1)) * plotW; }
  function y(v) { return pad.top + plotH - (v / maxVal) * plotH; }

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  const gridSteps = 4;
  for (let i = 0; i <= gridSteps; i++) {
    const yy = pad.top + (i / gridSteps) * plotH;
    ctx.beginPath();
    ctx.moveTo(pad.left, yy);
    ctx.lineTo(W - pad.right, yy);
    ctx.stroke();
    // Label
    const val = Math.round(maxVal * (1 - i / gridSteps));
    ctx.fillStyle = '#64748b';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'right';
    ctx.fillText(val.toLocaleString(), pad.left - 6, yy + 3);
  }

  // Draw line: total files
  ctx.strokeStyle = '#6366f1';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const px = x(i), py = y(values[i]);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();

  // Fill area under total
  ctx.fillStyle = 'rgba(99, 102, 241, 0.1)';
  ctx.beginPath();
  ctx.moveTo(x(0), y(values[0]));
  for (let i = 1; i < data.length; i++) ctx.lineTo(x(i), y(values[i]));
  ctx.lineTo(x(data.length - 1), pad.top + plotH);
  ctx.lineTo(x(0), pad.top + plotH);
  ctx.closePath();
  ctx.fill();

  // Draw line: duplicates
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 3]);
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const px = x(i), py = y(dupes[i]);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();
  ctx.setLineDash([]);

  // Dots total
  for (let i = 0; i < data.length; i++) {
    ctx.fillStyle = '#6366f1';
    ctx.beginPath();
    ctx.arc(x(i), y(values[i]), 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Dots dupes
  for (let i = 0; i < data.length; i++) {
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(x(i), y(dupes[i]), 3, 0, Math.PI * 2);
    ctx.fill();
  }

  // X-axis labels (show max ~6)
  ctx.fillStyle = '#64748b';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'center';
  const step = Math.max(1, Math.floor(data.length / 6));
  for (let i = 0; i < data.length; i += step) {
    const short = labels[i].substring(5); // MM-DD
    ctx.fillText(short, x(i), H - pad.bottom + 16);
  }
  // Always show last
  if ((data.length - 1) % step !== 0) {
    ctx.fillText(labels[data.length - 1].substring(5), x(data.length - 1), H - pad.bottom + 16);
  }

  // Legend
  ctx.font = '11px system-ui';
  const legX = pad.left + 8;
  ctx.fillStyle = '#6366f1';
  ctx.fillRect(legX, pad.top - 14, 12, 3);
  ctx.fillStyle = '#94a3b8';
  ctx.textAlign = 'left';
  ctx.fillText('Mods gesamt', legX + 16, pad.top - 10);

  ctx.fillStyle = '#f59e0b';
  ctx.fillRect(legX + 110, pad.top - 14, 12, 3);
  ctx.fillStyle = '#94a3b8';
  ctx.fillText('Duplikate', legX + 126, pad.top - 10);
}

// ---- Mod-Listen-Export ----
document.getElementById('btn_export_modlist').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/mod_export?token=' + encodeURIComponent(TOKEN));
    if (!resp.ok) throw new Error('Export fehlgeschlagen');
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
    a.href = url;
    a.download = 'Sims4_ModListe_' + ts + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setLast('📥 Mod-Liste exportiert als ' + a.download);
    addLog('MOD_EXPORT :: ' + a.download);
  } catch(e) {
    alert('Export-Fehler: ' + e.message);
  }
});

document.getElementById('btn_reload_history').addEventListener('click', () => {
  document.getElementById('mod-snapshot-content').innerHTML = 'Lade…';
  document.getElementById('scan-history-content').innerHTML = 'Lade…';
  loadHistory();
});

</script>
<div id="lightbox-overlay" onclick="if(event.target===this)closeLightbox()"><div id="lightbox-content"></div></div>
<button id="lightbox-close" title="Schließen" onclick="closeLightbox()">✕</button>
<button id="back-to-top" title="Zurück nach oben" onclick="window.scrollTo({top:0,behavior:'smooth'});">⬆</button>
<script>
function openLightbox(src) {
  const ov = document.getElementById('lightbox-overlay');
  document.getElementById('lightbox-content').innerHTML =
    `<img class="lb-single" src="${src}" alt="Vorschau" onclick="event.stopPropagation()" />`;
  ov.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function openCompareGallery(gi) {
  if (!window.__DATA || !window.__DATA.groups || !window.__DATA.groups[gi]) return;
  const g = window.__DATA.groups[gi];
  const items = [];
  for (const f of g.files) {
    const fname = (f.path || '').split(/[\\\/]/).pop();
    const thumb = f.deep && f.deep.thumbnail_b64 ? f.deep.thumbnail_b64 : null;
    const cat = f.deep && f.deep.category ? f.deep.category : '';
    const size = f.size_h || '?';
    const mtime = f.mtime || '?';
    items.push({fname, thumb, cat, size, mtime, path: f.path});
  }
  if (items.filter(i => i.thumb).length === 0) {
    alert('Keine Vorschaubilder in dieser Gruppe vorhanden.');
    return;
  }
  const esc2 = s => s ? s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') : '';
  let html = `<div class="lb-gallery" onclick="event.stopPropagation()">`;
  html += `<div class="lb-gallery-title">🖼️ Bildvergleich — ${esc2(g.key_short || g.key)} (${items.length} Dateien)</div>`;
  for (const it of items) {
    if (it.thumb) {
      html += `<div class="lb-gallery-card">`;
      html += `<img src="${it.thumb}" alt="${esc2(it.fname)}" onclick="openLightbox(this.src)" style="cursor:zoom-in;" title="Klicken zum Vergrößern" />`;
      html += `<div class="lb-label">${esc2(it.fname)}</div>`;
      html += `<div class="lb-meta">${esc2(it.size)} · ${esc2(it.mtime)}${it.cat ? ' · ' + esc2(it.cat) : ''}</div>`;
      html += `</div>`;
    } else {
      html += `<div class="lb-gallery-card" style="border-color:#475569;opacity:0.5;">`;
      html += `<div style="width:120px;height:120px;background:#0f172a;border-radius:8px;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;color:#475569;font-size:36px;">?</div>`;
      html += `<div class="lb-label">${esc2(it.fname)}</div>`;
      html += `<div class="lb-meta">${esc2(it.size)} · ${esc2(it.mtime)} · Kein Bild</div>`;
      html += `</div>`;
    }
  }
  html += `<div class="lb-gallery-hint">Klicke auf ein Bild zum Vergrößern · ESC oder Hintergrund zum Schließen</div>`;
  html += `</div>`;
  const ov = document.getElementById('lightbox-overlay');
  document.getElementById('lightbox-content').innerHTML = html;
  ov.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeLightbox() {
  document.getElementById('lightbox-overlay').classList.remove('active');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeLightbox();
});
</script>

<!-- Tutorial Overlay -->
<div id="tutorial-overlay">
  <div id="tutorial-card">
    <div class="plumbob-container">
      <svg class="plumbob" viewBox="0 0 80 110" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="plumbGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#63e682;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#34d058;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#22863a;stop-opacity:1" />
          </linearGradient>
          <linearGradient id="plumbShine" x1="0%" y1="0%" x2="50%" y2="50%">
            <stop offset="0%" style="stop-color:rgba(255,255,255,0.4);stop-opacity:1" />
            <stop offset="100%" style="stop-color:rgba(255,255,255,0);stop-opacity:1" />
          </linearGradient>
        </defs>
        <polygon points="40,2 78,35 40,108 2,35" fill="url(#plumbGrad)" stroke="#2ea043" stroke-width="1.5" />
        <polygon points="40,2 78,35 40,108 2,35" fill="url(#plumbShine)" />
        <polygon points="40,6 72,35 40,100" fill="rgba(255,255,255,0.08)" />
      </svg>
    </div>
    <div class="tut-header">
      <div class="tut-icon" id="tut-step-icon"></div>
      <div class="tut-title" id="tut-step-title"></div>
    </div>
    <div class="tut-body" id="tut-step-body"></div>
    <div class="tut-dots" id="tut-dots"></div>
    <div class="tut-footer">
      <button class="tut-btn tut-btn-skip" id="tut-btn-skip" onclick="closeTutorial()">Überspringen</button>
      <button class="tut-btn" id="tut-btn-prev" onclick="tutorialPrev()">← Zurück</button>
      <button class="tut-btn tut-btn-primary" id="tut-btn-next" onclick="tutorialNext()">Weiter →</button>
    </div>
    <div class="tut-check">
      <input type="checkbox" id="tut-dont-show" checked>
      <label for="tut-dont-show">Beim nächsten Start nicht mehr anzeigen</label>
    </div>
  </div>
</div>

<script>
window.addEventListener('scroll', () => {
  document.getElementById('back-to-top').classList.toggle('visible', window.scrollY > 400);
});
</script>
</body>
</html>
"""
        html = html.replace("__TOKEN__", json.dumps(self.token))
        html = html.replace("__LOGFILE__", json.dumps(str(self.log_file)))
        return html


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sims4 Duplicate Scanner (Batch)")
        self.geometry("1000x720")
        self.minsize(920, 620)

        self.var_exts = tk.StringVar(value=".package,.ts4script")
        self.var_ignore = tk.StringVar(value="__pycache__,cache,thumbnails")
        self.var_do_name = tk.BooleanVar(value=True)
        self.var_do_content = tk.BooleanVar(value=True)
        self.var_do_conflicts = tk.BooleanVar(value=True)

        self.var_add_path = tk.StringVar(value="")
        self.var_sims4_dir = tk.StringVar(value="")
        self.var_cf_path = tk.StringVar(value="")
        self.var_status = tk.StringVar(value="Bereit.")
        self.var_detail = tk.StringVar(value="")
        self.var_minimize_on_close = tk.BooleanVar(value=True)

        self.server: LocalServer | None = None
        self.listbox = None
        self.progress = None
        self.btn_run = None
        self._minimized_to_tray = False

        self._build_ui()
        self._load_config_into_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Map>", self._on_map)

    def _build_ui(self):
        pad = 10

        top = ttk.Frame(self)
        top.pack(fill="x", padx=pad, pady=(pad, 0))

        left = ttk.LabelFrame(top, text="Ordner (werden geprüft)")
        left.pack(side="left", fill="both", expand=True, padx=(0, pad))

        self.listbox = tk.Listbox(left, height=12, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, padx=pad, pady=(pad, 6))

        add_row = ttk.Frame(left)
        add_row.pack(fill="x", padx=pad, pady=(0, 8))
        ent = ttk.Entry(add_row, textvariable=self.var_add_path)
        ent.pack(side="left", fill="x", expand=True)
        ttk.Button(add_row, text="Pfad hinzufügen", command=self.add_path_from_entry).pack(side="left", padx=(8, 0))
        ent.bind("<Return>", lambda _e: self.add_path_from_entry())

        btn_row = ttk.Frame(left)
        btn_row.pack(fill="x", padx=pad, pady=(0, pad))
        ttk.Button(btn_row, text="Ordner auswählen…", command=self.add_folder).pack(side="left")
        ttk.Button(btn_row, text="Auswahl entfernen", command=self.remove_selected).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Liste leeren", command=self.clear_list).pack(side="left")

        right = ttk.LabelFrame(top, text="Optionen")
        right.pack(side="left", fill="both", expand=False)

        opt = ttk.Frame(right)
        opt.pack(fill="both", expand=True, padx=pad, pady=pad)

        ttk.Label(opt, text="Extensions (Komma, '*' = alles):").pack(anchor="w")
        ttk.Entry(opt, textvariable=self.var_exts, width=40).pack(fill="x", pady=(2, 10))

        ttk.Label(opt, text="Ignoriere Ordner (Namen, Komma):").pack(anchor="w")
        ttk.Entry(opt, textvariable=self.var_ignore, width=40).pack(fill="x", pady=(2, 10))

        ttk.Checkbutton(opt, text="Duplikate nach Dateiname", variable=self.var_do_name).pack(anchor="w")
        ttk.Checkbutton(opt, text="Duplikate nach Inhalt (SHA-256)", variable=self.var_do_content).pack(anchor="w")
        ttk.Checkbutton(opt, text="Ressource-Konflikte (DBPF-IDs)", variable=self.var_do_conflicts).pack(anchor="w", pady=(0, 10))

        self.btn_run = ttk.Button(opt, text="Scan & Web-UI öffnen", command=self.run_scan)
        self.btn_run.pack(fill="x")

        self.btn_backup = ttk.Button(opt, text="📦 Backup erstellen", command=self.create_backup)
        self.btn_backup.pack(fill="x", pady=(10, 0))

        # Sims 4 Verzeichnis für Fehler-Analyse
        s4frame = ttk.LabelFrame(self, text="Sims 4 Verzeichnis (für Fehler-Analyse)")
        s4frame.pack(fill="x", padx=pad, pady=(10, 0))
        s4row = ttk.Frame(s4frame)
        s4row.pack(fill="x", padx=pad, pady=pad)
        ttk.Entry(s4row, textvariable=self.var_sims4_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(s4row, text="Ordner wählen…", command=self.pick_sims4_dir).pack(side="left", padx=(8, 0))
        ttk.Button(s4row, text="Auto", command=self.auto_find_sims4_dir).pack(side="left", padx=(4, 0))

        # CurseForge Manifest-Pfad
        cfframe = ttk.LabelFrame(self, text="CurseForge Manifest (für Mod-Erkennung)")
        cfframe.pack(fill="x", padx=pad, pady=(10, 0))
        cfrow = ttk.Frame(cfframe)
        cfrow.pack(fill="x", padx=pad, pady=pad)
        ttk.Entry(cfrow, textvariable=self.var_cf_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfrow, text="Datei wählen…", command=self.pick_cf_path).pack(side="left", padx=(8, 0))
        ttk.Button(cfrow, text="Auto", command=self.auto_find_cf_path).pack(side="left", padx=(4, 0))

        prog = ttk.Frame(self)
        prog.pack(fill="x", padx=pad, pady=(10, 0))
        ttk.Label(prog, textvariable=self.var_status).pack(anchor="w")
        self.progress = ttk.Progressbar(prog, mode="indeterminate")
        self.progress.pack(fill="x", pady=(6, 2))
        ttk.Label(prog, textvariable=self.var_detail).pack(anchor="w")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=pad, pady=(10, pad))
        ttk.Button(bottom, text="Web-UI nochmal öffnen", command=self.open_web).pack(side="left")
        ttk.Button(bottom, text="Server stoppen", command=self.stop_server).pack(side="left", padx=8)
        ttk.Button(bottom, text="❌ Beenden", command=self.quit_app).pack(side="right")
        ttk.Checkbutton(bottom, text="Beim Schließen minimieren (Server läuft weiter)",
                        variable=self.var_minimize_on_close).pack(side="right", padx=(0, 12))

        ttk.Label(self, text="Tipp: Mehrere Pfade auf einmal einfügen (Zeilenumbruch oder ';').").pack(anchor="w", padx=pad, pady=(0, pad))

    def pick_cf_path(self):
        p = filedialog.askopenfilename(
            title="CurseForge Manifest auswählen (AddonGameInstance.json)",
            filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")],
        )
        if p:
            self.var_cf_path.set(p)
            self._save_config_now()

    def auto_find_cf_path(self):
        """Sucht automatisch nach dem CurseForge-Manifest."""
        candidates = []
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            candidates.append(Path(localappdata) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json")
            # Alternative Pfade für ältere/neuere Versionen
            candidates.append(Path(localappdata) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
        # ProgramData
        progdata = os.environ.get("PROGRAMDATA", "")
        if progdata:
            candidates.append(Path(progdata) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
        # Laufwerke durchsuchen
        for drive in ["C:", "D:", "E:", "F:", "G:"]:
            candidates.append(Path(drive) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
            candidates.append(Path(drive) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json")
        for c in candidates:
            if c.exists():
                self.var_cf_path.set(str(c))
                self._save_config_now()
                messagebox.showinfo("Gefunden", f"CurseForge Manifest gefunden:\n\n{c}")
                return
        messagebox.showwarning("Nicht gefunden", "Konnte das CurseForge-Manifest nicht automatisch finden.\nBitte manuell auswählen.\n\nNormalerweise unter:\n%LOCALAPPDATA%\\Overwolf\\Curse\\GameInstances\\AddonGameInstance.json")

    def pick_sims4_dir(self):
        p = filedialog.askdirectory(title="Sims 4 Verzeichnis auswählen (z.B. Electronic Arts/Die Sims 4)")
        if p:
            self.var_sims4_dir.set(p)
            self._save_config_now()

    def auto_find_sims4_dir(self):
        d = find_sims4_userdir([])
        if d:
            self.var_sims4_dir.set(str(d))
            self._save_config_now()
            messagebox.showinfo("Gefunden", f"Sims 4 Verzeichnis gefunden:\n\n{d}")
        else:
            messagebox.showwarning("Nicht gefunden", "Konnte das Sims 4 Verzeichnis nicht automatisch finden.\nBitte manuell auswählen.")

    def _load_config_into_ui(self):
        """Lade gespeicherte Einstellungen aus der Konfiguration."""
        cfg = load_config()
        if "folders" in cfg:
            for folder in cfg.get("folders", []):
                if Path(folder).exists():
                    self.listbox.insert("end", folder)
        if "exts" in cfg:
            self.var_exts.set(cfg["exts"])
        if "ignore" in cfg:
            self.var_ignore.set(cfg["ignore"])
        if "sims4_dir" in cfg and cfg["sims4_dir"]:
            self.var_sims4_dir.set(cfg["sims4_dir"])
        else:
            # Beim ersten Start automatisch suchen
            d = find_sims4_userdir([])
            if d:
                self.var_sims4_dir.set(str(d))
        if "cf_path" in cfg and cfg["cf_path"]:
            self.var_cf_path.set(cfg["cf_path"])
        else:
            # Beim ersten Start automatisch suchen
            default_cf = Path(os.environ.get("LOCALAPPDATA", "")) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json"
            if default_cf.exists():
                self.var_cf_path.set(str(default_cf))
        if "minimize_on_close" in cfg:
            self.var_minimize_on_close.set(cfg["minimize_on_close"])
        self._tutorial_seen = cfg.get("tutorial_seen", False)

    def _save_config_now(self):
        """Speichere aktuelle Einstellungen in die Konfiguration."""
        folders = list(self.listbox.get(0, "end"))
        cfg = {
            "folders": folders,
            "exts": self.var_exts.get(),
            "ignore": self.var_ignore.get(),
            "sims4_dir": self.var_sims4_dir.get(),
            "cf_path": self.var_cf_path.get(),
            "minimize_on_close": self.var_minimize_on_close.get(),
            "tutorial_seen": getattr(self, '_tutorial_seen', False),
        }
        save_config(cfg)

    def on_close(self):
        """Beim Schließen des Fensters — minimiert in Taskleiste statt beendet."""
        if self.var_minimize_on_close.get():
            self.iconify()  # In Taskleiste minimieren (sichtbar bleiben)
            self._minimized_to_tray = True
            return
        self.quit_app()

    def _on_map(self, _event=None):
        """Fenster wurde wiederhergestellt (aus Taskleiste geholt)."""
        if self._minimized_to_tray:
            self._minimized_to_tray = False
            if self.server:
                self.var_status.set(f"Server läuft — Port {self.server.port}")
            else:
                self.var_status.set("Bereit.")

    def quit_app(self):
        """Programm wirklich beenden (Server stoppen + Fenster schließen)."""
        self.stop_server()
        self.destroy()

    def _existing_paths_lower(self) -> set[str]:
        return {str(self.listbox.get(i)).strip().lower() for i in range(self.listbox.size())}

    def add_paths(self, text: str):
        if not text:
            return
        raw = text.replace(";", "\n").splitlines()
        raw = [r.strip().strip('"').strip("'") for r in raw if r.strip()]

        existing = self._existing_paths_lower()
        added = 0
        invalid = []

        for r in raw:
            p = Path(r).expanduser()
            try:
                p = p.resolve()
            except Exception:
                pass

            key = str(p).strip().lower()
            if key in existing:
                continue

            if p.exists() and p.is_dir():
                self.listbox.insert("end", str(p))
                existing.add(key)
                added += 1
            else:
                invalid.append(r)

        if invalid:
            messagebox.showwarning(
                "Ungültige Pfade",
                "Diese Pfade sind keine gültigen Ordner:\n\n" + "\n".join(invalid[:25]) + ("" if len(invalid) <= 25 else "\n…"),
            )
        if added == 0 and not invalid:
            messagebox.showinfo("Info", "Keine neuen Ordner hinzugefügt (evtl. alles schon drin).")

        # Einstellungen merken
        self._save_config_now()

    def add_path_from_entry(self):
        self.add_paths(self.var_add_path.get().strip())
        self.var_add_path.set("")
        self._save_config_now()

    def add_folder(self):
        p = filedialog.askdirectory(title="Ordner auswählen")
        if p:
            self.add_paths(p)
        self._save_config_now()

    def clear_list(self):
        self.listbox.delete(0, "end")
        self._save_config_now()

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        for i in reversed(sel):
            self.listbox.delete(i)
        self._save_config_now()

    def set_progress_indet(self, on: bool, status: str, detail: str = ""):
        self.var_status.set(status)
        self.var_detail.set(detail)
        self.progress.configure(mode="indeterminate")
        if on:
            self.progress.start(10)
        else:
            self.progress.stop()

    def set_progress_det(self, cur: int, total: int, status: str, detail: str = ""):
        self.var_status.set(status)
        self.var_detail.set(detail)
        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=max(total, 1), value=cur)

    def create_backup(self):
        """Erstelle ein ZIP-Backup aller ausgewählten Ordner mit detailliertem Fortschritt."""
        roots_raw = list(self.listbox.get(0, "end"))
        if not roots_raw:
            messagebox.showwarning("Hinweis", "Bitte mindestens einen Ordner hinzufügen.")
            return

        # Dialog: Zielordner auswählen
        dest_dir = filedialog.askdirectory(title="Wo soll das Backup gespeichert werden?")
        if not dest_dir:
            return

        dest_path = Path(dest_dir)
        if not dest_path.exists() or not dest_path.is_dir():
            messagebox.showerror("Fehler", f"Ungültiger Zielordner: {dest_dir}")
            return

        # Timestamp in ZIP-Name
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = dest_path / f"sims4_backup_{stamp}.zip"

        self.btn_backup.configure(state="disabled")
        self.btn_run.configure(state="disabled")
        self.set_progress_indet(True, "Zähle Dateien...", "")
        self.update()

        def worker():
            try:
                # Phase 1: Alle Dateien zählen
                total_files = 0
                total_size = 0
                file_list = []
                
                for root_str in roots_raw:
                    root = Path(root_str).resolve()
                    if not root.exists():
                        continue
                    for dirpath, dirnames, filenames in os.walk(root):
                        for filename in filenames:
                            file_path = Path(dirpath) / filename
                            try:
                                size = file_path.stat().st_size
                                total_files += 1
                                total_size += size
                                file_list.append((file_path, size))
                            except Exception:
                                pass

                self.var_status.set("Erstelle Backup...")
                self.var_detail.set(f"Starte Archivierung: {total_files} Dateien ({human_size(total_size)})")
                self.update()

                # Phase 2: ZIP erstellen mit detailliertem Tracking
                start_time = time.time()
                packed_files = 0
                packed_size = 0
                update_interval = max(1, total_files // 20)  # Update alle 5% oder jede Datei, wenn < 20 Dateien

                with zipfile.ZipFile(str(zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path, file_size in file_list:
                        try:
                            arcname = file_path.relative_to(file_path.parent.parent)
                            zf.write(str(file_path), arcname=str(arcname))
                            packed_files += 1
                            packed_size += file_size
                        except Exception as e:
                            print(f"[BACKUP_WARN] {file_path}: {e}", flush=True)
                            continue

                        # UI Update (aber nicht zu oft für Performance)
                        if packed_files % update_interval == 0 or packed_files == total_files:
                            elapsed = time.time() - start_time
                            percent = int((packed_files / total_files) * 100) if total_files > 0 else 0
                            speed = (packed_size / (1024 * 1024)) / max(elapsed, 0.1)  # MB/s
                            
                            filename_display = file_path.name if len(file_path.name) <= 50 else file_path.name[:47] + "..."
                            
                            detail = (
                                f"{packed_files}/{total_files} Dateien ({percent}%)\n"
                                f"{human_size(packed_size)} / {human_size(total_size)}\n"
                                f"Geschwindigkeit: {speed:.1f} MB/s\n"
                                f"Datei: {filename_display}"
                            )
                            self.var_detail.set(detail)
                            self.update()

                # Fertig
                elapsed = time.time() - start_time
                self.progress.stop()
                self.btn_backup.configure(state="normal")
                self.btn_run.configure(state="normal")
                self.var_status.set("Fertig.")
                zip_size = zip_name.stat().st_size
                self.var_detail.set(
                    f"Backup erstellt: {zip_name.name}\n"
                    f"Größe: {human_size(zip_size)}\n"
                    f"Zeit: {elapsed:.1f}s"
                )
                self.update()
                messagebox.showinfo(
                    "Erfolg",
                    f"Backup erstellt:\n\n{zip_name}\n\n"
                    f"Dateien: {total_files}\n"
                    f"Größe: {human_size(zip_size)}\n"
                    f"Zeit: {elapsed:.1f}s"
                )

            except Exception as e:
                self.progress.stop()
                self.btn_backup.configure(state="normal")
                self.btn_run.configure(state="normal")
                err_msg = f"{type(e).__name__}: {e}"
                self.var_status.set("Fehler.")
                self.var_detail.set(err_msg)
                self.update()
                messagebox.showerror("Backup-Fehler", err_msg)

        threading.Thread(target=worker, daemon=True).start()

    def run_scan(self):
        # Einstellungen merken
        self._save_config_now()

        roots_raw = list(self.listbox.get(0, "end"))
        if not roots_raw:
            messagebox.showwarning("Hinweis", "Bitte mindestens einen Ordner hinzufügen.")
            return
        if not (self.var_do_name.get() or self.var_do_content.get()):
            messagebox.showwarning("Hinweis", "Bitte mindestens eine Duplikat-Art auswählen.")
            return

        roots = []
        invalid_roots = []
        for r in roots_raw:
            rp = Path(r).expanduser()
            if rp.exists() and rp.is_dir():
                roots.append(rp.resolve())
            else:
                invalid_roots.append(r)

        if invalid_roots:
            messagebox.showwarning("Ungültige Ordner", "Diese Ordner existieren nicht:\n\n" + "\n".join(invalid_roots[:25]))

        if not roots:
            messagebox.showwarning("Hinweis", "Keiner der Ordner existiert.")
            return

        exts = normalize_exts(self.var_exts.get())
        ignore_dirs = normalize_ignore_dirs(self.var_ignore.get())
        do_name = self.var_do_name.get()
        do_content = self.var_do_content.get()
        do_conflicts = self.var_do_conflicts.get()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        qdir = roots[0].parent / f"dupe_quarantine_{stamp}"

        self.btn_run.configure(state="disabled")
        self.set_progress_indet(True, "Starte…", "Initialisiere Scan…")

        def ui_progress(phase, cur, total, msg):
            def apply():
                if phase == "collect":
                    self.set_progress_indet(True, "Sammle Dateien…", msg)
                elif phase == "name":
                    self.set_progress_indet(True, "Prüfe Dateinamen…", msg)
                elif phase == "hashing_init":
                    if total and total > 0:
                        self.set_progress_det(0, total, "Hash-Prüfung…", msg)
                    else:
                        self.set_progress_indet(True, "Hash-Prüfung…", msg)
                elif phase == "hashing":
                    if total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Hash-Prüfung…", msg)
                    else:
                        self.set_progress_indet(True, "Hash-Prüfung…", msg)
                else:
                    if phase == 'integrity' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Integritäts-Check…", msg)
                    elif phase == 'conflicts' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Konflikte prüfen…", msg)
                    elif phase == 'deep' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Tiefenanalyse…", msg)
                    elif phase == 'categorize' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Kategorisiere…", msg)
                    else:
                        self.set_progress_indet(True, "Finalisiere…", msg)
            self.after(0, apply)

        def worker():
            try:
                files, name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs = scan_duplicates(
                    roots=roots,
                    exts=exts,
                    ignore_dirs=ignore_dirs,
                    do_name=do_name,
                    do_content=do_content,
                    do_conflicts=do_conflicts,
                    progress_cb=ui_progress,
                )

                ds = Dataset(roots, sims4_dir=self.var_sims4_dir.get())
                ds.all_scanned_files = files
                ds.build_from_scan(name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs)

                # DBPF-Cache laden
                deep_cache = load_deep_cache()

                # Tiefenanalyse für alle Gruppen (Stufe 1-5)
                ds.enrich_groups(progress_cb=ui_progress, deep_cache=deep_cache)

                # Auto-Kategorisierung ALLER Mods (nicht nur Problemdateien)
                ds.enrich_all_files(progress_cb=ui_progress, deep_cache=deep_cache)

                # DBPF-Cache speichern
                save_deep_cache(deep_cache)

                # Abhängigkeits-Erkennung
                ds.detect_dependencies()

                # Nicht-Mod-Dateien sammeln
                ds.collect_non_mod_files()

                # History-Snapshots speichern
                try:
                    scan_hist = save_scan_history(len(files), name_dupes, content_dupes, roots)
                    mod_snap = save_mod_snapshot(files, roots)
                except Exception as ex:
                    print(f"[HISTORY] Fehler beim Speichern: {ex}", flush=True)
                    scan_hist = {}
                    mod_snap = {}

                self.stop_server()
                srv = LocalServer(ds, qdir, sims4_dir=self.var_sims4_dir.get(), cf_path=self.var_cf_path.get())
                srv.app_ref = self
                srv.scan_history = scan_hist
                srv.mod_snapshot = mod_snap
                srv.start()
                self.server = srv

                def finish():
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=0, maximum=1)
                    self.var_status.set("Fertig.")
                    self.var_detail.set(
                        f"Dateien: {len(files)} | Gruppen: Name {len(name_dupes)} / Inhalt {len(content_dupes)} / Ähnlich {len(similar_dupes)} | Korrupt: {len(corrupt_files)} | Konflikte: {len(conflicts)} | Quarantäne: {qdir}"
                    )
                    self.btn_run.configure(state="normal")
                    self.open_web()

                self.after(0, finish)

            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"

                def fail(msg=err_msg):
                    self.progress.stop()
                    self.btn_run.configure(state="normal")
                    self.var_status.set("Fehler.")
                    self.var_detail.set(msg)
                    messagebox.showerror("Scan-Fehler", msg)

                self.after(0, fail)

        threading.Thread(target=worker, daemon=True).start()

    def open_web(self):
        if not self.server or not self.server.port:
            messagebox.showinfo("Info", "Noch kein Server aktiv. Erst 'Scan & Web-UI öffnen'.")
            return
        webbrowser.open(self.server.url())

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
            self.var_detail.set("Server gestoppt.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
