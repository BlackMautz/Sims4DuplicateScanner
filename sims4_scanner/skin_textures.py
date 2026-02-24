# -*- coding: utf-8 -*-
"""Sim-Textur-Extraktor: Liest Skin-Composite-Texturen aus localsimtexturecache.package.

Die localsimtexturecache.package enthält die endgültigen Skin-Composites,
die das Spiel für aktiv geladene Sims rendert. Jeder Sim hat eine 1024×2048
DDS-Textur (uncompressed RGBA, 32-bit), die alle Skin-Overlays, Make-up,
Tattoos etc. zusammenfasst.

Ressource-Typ 0x00B2D882 = DDS-Textur  (LRLE im DBPF-Index, aber als DDS gespeichert)
Ressource-Typ 0xDA15D619 = Metadaten    (kleine Protobuf-Blobs)
"""

from __future__ import annotations

import os
import struct
import base64
import json
import hashlib
import time
import threading

from .dbpf import read_dbpf_entries, _read_resource_data, _dds_to_png
from pathlib import Path

# Sims 4 Texture Ressource-Typen
_RES_DDS_TEXTURE = 0x00B2D882   # DDS Skin Composite
_RES_TEXTURE_META = 0xDA15D619  # Texture Metadata

# ── In-Memory Cache für Textur-Ergebnisse (mtime+size validiert) ──
_texture_cache_lock = threading.Lock()
_texture_cache: dict | None = None       # Cached result dict
_texture_cache_key: tuple | None = None  # (mtime, size) des cache files


def extract_sim_textures(sims4_dir: str, max_dim: int = 512) -> dict:
    """Extrahiert alle Sim-Skin-Texturen aus localsimtexturecache.package.

    Args:
        sims4_dir: Pfad zum "Die Sims 4" Benutzerordner
        max_dim: Maximale Bildgröße für PNG-Ausgabe (512 empfohlen)

    Returns:
        dict mit:
            "textures": [{
                "instance_hex": str,
                "width": int, "height": int,
                "png_b64": str (data:image/png;base64,...),
                "raw_size": int,
            }, ...],
            "count": int,
            "cache_size": int,
            "error": str | None
    """
    cache_path = Path(sims4_dir) / "localsimtexturecache.package"
    result = {"textures": [], "count": 0, "cache_size": 0, "error": None}

    if not cache_path.is_file():
        result["error"] = "localsimtexturecache.package nicht gefunden"
        return result

    try:
        st = cache_path.stat()
        result["cache_size"] = st.st_size
        file_key = (st.st_mtime, st.st_size, max_dim)
    except OSError:
        result["error"] = "Konnte Cache-Datei nicht lesen"
        return result

    # In-Memory Cache prüfen (gleiche Datei → gleiche Texturen)
    global _texture_cache, _texture_cache_key
    with _texture_cache_lock:
        if _texture_cache is not None and _texture_cache_key == file_key:
            print("[TEXTUR] Cache-Hit: Texturen aus Memory", flush=True)
            return _texture_cache

    entries = read_dbpf_entries(cache_path)
    if not entries:
        result["error"] = "Konnte DBPF-Index nicht lesen"
        return result

    # Nur DDS-Texturen filtern
    dds_entries = [e for e in entries if e["type"] == _RES_DDS_TEXTURE]
    if not dds_entries:
        result["error"] = "Keine Texturen im Cache gefunden"
        return result

    textures = []
    for entry in dds_entries:
        instance_hex = f"{entry['instance']:016x}"
        raw = _read_resource_data(cache_path, entry)
        if not raw:
            continue

        # DDS-Header lesen für Dimensions-Info
        width = height = 0
        if len(raw) >= 20 and raw[:4] == b'DDS ':
            height = struct.unpack_from('<I', raw, 12)[0]
            width = struct.unpack_from('<I', raw, 16)[0]

        # DDS → PNG konvertieren
        png_data = _dds_to_png(raw, max_dim=max_dim)
        if not png_data:
            continue

        png_b64 = "data:image/png;base64," + base64.b64encode(png_data).decode("ascii")
        textures.append({
            "instance_hex": instance_hex,
            "width": width,
            "height": height,
            "png_b64": png_b64,
            "raw_size": len(raw),
        })

    result["textures"] = textures
    result["count"] = len(textures)

    # In Memory-Cache speichern für nächsten Aufruf
    with _texture_cache_lock:
        _texture_cache = result
        _texture_cache_key = file_key
        print(f"[TEXTUR] {len(textures)} Texturen konvertiert und gecacht", flush=True)

    return result


def extract_texture_full_res(sims4_dir: str, instance_hex: str) -> bytes | None:
    """Extrahiert eine einzelne Textur in voller Auflösung als PNG.

    Args:
        sims4_dir: Pfad zum Sims 4 Benutzerordner
        instance_hex: 16-stellige Hex-Instance-ID

    Returns:
        PNG-Bytes oder None
    """
    cache_path = Path(sims4_dir) / "localsimtexturecache.package"
    if not cache_path.is_file():
        return None

    target_instance = int(instance_hex, 16)
    entries = read_dbpf_entries(cache_path)
    if not entries:
        return None

    for entry in entries:
        if entry["type"] == _RES_DDS_TEXTURE and entry["instance"] == target_instance:
            raw = _read_resource_data(cache_path, entry)
            if not raw:
                return None
            # Volle Auflösung (1024px Breite)
            return _dds_to_png(raw, max_dim=1024)

    return None
