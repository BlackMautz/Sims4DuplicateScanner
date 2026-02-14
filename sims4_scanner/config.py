# -*- coding: utf-8 -*-
"""Persistente Konfiguration und DBPF-Analyse-Cache."""

from __future__ import annotations

import os
import json
from pathlib import Path


# ---- Basis-Pfad ----
def _appdata_path(filename: str) -> Path:
    """Erzeugt Pfad im APPDATA-Ordner (oder Fallback auf Home)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / filename
    return Path.home() / f".sims4_{filename}"


# ---- Generische versionierte Cache-Funktionen ----
def _load_versioned_cache(path: Path, version: int = 1) -> dict:
    """Lädt einen versionierten JSON-Cache. Gibt entries-dict zurück."""
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("version") == version:
                return data.get("entries", data)
    except Exception as exc:
        print(f"[CACHE] Warnung: {path.name} konnte nicht geladen werden: {exc}", flush=True)
    return {}


def _save_versioned_cache(path: Path, entries: dict, version: int = 1, wrap_entries: bool = True) -> None:
    """Speichert einen versionierten JSON-Cache."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if wrap_entries:
            payload = {"version": version, "entries": entries}
        else:
            payload = entries
            payload["version"] = version
        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"[CACHE] Warnung: {path.name} konnte nicht gespeichert werden: {exc}", flush=True)


# ---- Persistente Einstellungen (Ordner/Optionen merken) ----
CONFIG_PATH = _appdata_path("sims4_duplicate_scanner_config.json")


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[CONFIG] Warnung: Config konnte nicht geladen werden: {exc}", flush=True)
    return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[CONFIG] Warnung: Config konnte nicht gespeichert werden: {exc}", flush=True)


# ---- DBPF-Analyse-Cache ----
_DEEP_CACHE_PATH = _appdata_path("dbpf_deep_cache.json")

def load_deep_cache() -> dict:
    return _load_versioned_cache(_DEEP_CACHE_PATH)


def cache_entry_valid(entry: dict, path: Path) -> bool:
    """Prüft ob ein Cache-Eintrag noch aktuell ist (gleiche mtime + Größe)."""
    try:
        st = path.stat()
        return (abs(entry.get('mt', 0) - st.st_mtime) < 0.01
                and entry.get('sz', -1) == st.st_size)
    except Exception:
        return False


# ---- SHA-256 Hash-Cache ----
_HASH_CACHE_PATH = _appdata_path("sha256_hash_cache.json")

def load_hash_cache() -> dict:
    return _load_versioned_cache(_HASH_CACHE_PATH)

def save_hash_cache(entries: dict) -> None:
    entries = cleanup_cache(entries)
    _save_versioned_cache(_HASH_CACHE_PATH, entries)


def cleanup_cache(entries: dict, max_stale_days: int = 30) -> dict:
    """Entfernt Cache-Einträge für Dateien die nicht mehr existieren.
    
    Wird beim Speichern aufgerufen um unbegrenztes Cache-Wachstum zu verhindern.
    """
    import time as _time
    now = _time.time()
    max_age = max_stale_days * 86400
    cleaned = {}
    removed = 0
    for path, entry in entries.items():
        # Behalte wenn Datei noch existiert ODER wenn sie kürzlich gecacht wurde
        try:
            if os.path.exists(path):
                cleaned[path] = entry
            elif isinstance(entry, dict) and (now - entry.get('mt', 0)) < max_age:
                cleaned[path] = entry  # Kürzlich gecacht, Datei vielleicht temporär weg
            else:
                removed += 1
        except Exception:
            cleaned[path] = entry  # Im Zweifel behalten
    if removed > 0:
        print(f"[CACHE] {removed} verwaiste Cache-Einträge entfernt", flush=True)
    return cleaned


def save_deep_cache(entries: dict) -> None:
    entries = cleanup_cache(entries)
    _save_versioned_cache(_DEEP_CACHE_PATH, entries)


# ---- Savegame-Analyse-Cache ----
_SAVEGAME_CACHE_PATH = _appdata_path("savegame_cache.json")

def load_savegame_cache() -> dict:
    return _load_versioned_cache(_SAVEGAME_CACHE_PATH)

def save_savegame_cache(entries: dict) -> None:
    _save_versioned_cache(_SAVEGAME_CACHE_PATH, entries)


# ---- Tray-Analyse-Cache ----
_TRAY_CACHE_PATH = _appdata_path("tray_analysis_cache.json")

def load_tray_cache() -> dict:
    return _load_versioned_cache(_TRAY_CACHE_PATH)

def save_tray_cache(data: dict) -> None:
    _save_versioned_cache(_TRAY_CACHE_PATH, data, wrap_entries=False)
