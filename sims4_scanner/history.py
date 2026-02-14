# -*- coding: utf-8 -*-
"""History, Snapshots und persistente Benutzer-Daten (Creators, Notes, Tags)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime

from .utils import human_size


# ---- History / Snapshots ----

def _history_dir() -> Path:
    """History-Ordner im selben Verzeichnis wie das Programm."""
    d = Path(__file__).resolve().parent.parent / "history"
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
            meta = {k: v for k, v in data.items() if k != "details" and k != "mods"}
            meta["_file"] = fp.name
            results.append(meta)
        except Exception:
            pass
    return results


# -- Custom Creators (persistent) --

_CUSTOM_CREATORS_FILE = Path(__file__).resolve().parent.parent / "custom_creators.json"


def load_custom_creators() -> dict:
    try:
        if _CUSTOM_CREATORS_FILE.exists():
            with _CUSTOM_CREATORS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[CREATORS] Fehler beim Laden: {ex}", flush=True)
    return {}


def save_custom_creators(creators: dict):
    try:
        with _CUSTOM_CREATORS_FILE.open("w", encoding="utf-8") as f:
            json.dump(creators, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[CREATORS] Fehler beim Speichern: {ex}", flush=True)


# -- Mod-Notizen (persistent) --

_MOD_NOTES_FILE = Path(__file__).resolve().parent.parent / "mod_notes.json"


def load_mod_notes() -> dict:
    try:
        if _MOD_NOTES_FILE.exists():
            with _MOD_NOTES_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[NOTES] Fehler beim Laden: {ex}", flush=True)
    return {}


def save_mod_notes(notes: dict):
    try:
        with _MOD_NOTES_FILE.open("w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[NOTES] Fehler beim Speichern: {ex}", flush=True)


# -- Mod-Tags (persistent) --

_MOD_TAGS_FILE = Path(__file__).resolve().parent.parent / "mod_tags.json"


def load_mod_tags() -> dict:
    try:
        if _MOD_TAGS_FILE.exists():
            with _MOD_TAGS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as ex:
        print(f"[TAGS] Fehler beim Laden: {ex}", flush=True)
    return {}


def save_mod_tags(tags: dict):
    try:
        with _MOD_TAGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[TAGS] Fehler beim Speichern: {ex}", flush=True)


# ---- Scan-History ----

def save_scan_history(files_count: int, name_dupes: dict, content_dupes: dict, roots: list[Path]) -> dict:
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


# ---- Fehler-Snapshot ----

def save_error_snapshot(errors: list[dict]) -> dict:
    prev = _load_latest("errors")
    prev_keys: set[str] = set()
    if prev and "error_keys" in prev:
        prev_keys = set(prev["error_keys"])

    current_keys: set[str] = set()
    for e in errors:
        key = f"{e.get('titel', '')}|{e.get('datei', '')}|{e.get('erklaerung', '')[:80]}"
        current_keys.add(key)
        if key in prev_keys:
            e["status"] = "bekannt"
        else:
            e["status"] = "neu"

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


# ---- Mod-Snapshot ----

def save_mod_snapshot(files: list[Path], roots: list[Path]) -> dict:
    MOD_EXTS = {".package", ".ts4script"}
    mod_files = [p for p in files if p.suffix.lower() in MOD_EXTS]

    seen_resolved: set[str] = set()
    unique_mod_files: list[Path] = []
    for p in mod_files:
        try:
            resolved = str(p.resolve()).lower()
        except Exception:
            resolved = str(p).lower()
        if resolved not in seen_resolved:
            seen_resolved.add(resolved)
            unique_mod_files.append(p)

    prev = _load_latest("mods")
    prev_mods: dict[str, dict] = {}
    if prev and "mods" in prev:
        prev_mods = {m["name"].lower(): m for m in prev["mods"]}

    current_mods: list[dict] = []
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

    neue = current_names - prev_names
    entfernt = prev_names - current_names
    geaendert: set[str] = set()
    for m in current_mods:
        key = m["name"].lower()
        prev_m = prev_mods.get(key)
        if prev_m and (prev_m.get("size") != m["size"] or prev_m.get("mtime") != m["mtime"]):
            geaendert.add(key)

    changes = {
        "neue_mods": sorted(list(neue))[:100],
        "entfernte_mods": sorted(list(entfernt))[:100],
        "geaenderte_mods": sorted(list(geaendert))[:100],
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
        "mods": current_mods,
    }

    p = _save_json("mods", data)
    print(f"[HISTORY] Mod-Snapshot: {data['mods_gesamt']} Mods | +{len(neue)} neu, -{len(entfernt)} entfernt, ~{len(geaendert)} geändert | {p}", flush=True)
    return data
