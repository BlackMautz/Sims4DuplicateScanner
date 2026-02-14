# -*- coding: utf-8 -*-
"""HTTP-Server für die Web-UI des Sims 4 Duplikate Scanners."""

from __future__ import annotations

import json
import os
import re
import csv
import html as _html
import shutil
import secrets
import socket
import threading
import time
import base64 as _b64
import concurrent.futures
import tempfile as _tf
import uuid as _uuid
import subprocess
import platform as _plat
import urllib.request as _urlreq
from pathlib import Path
from datetime import datetime
from collections import Counter

from .constants import SCANNER_VERSION, DISCORD_WEBHOOK_URL
from .config import load_config, save_config, load_deep_cache, save_deep_cache
from .utils import safe_stat, human_size, best_root_index, is_under_any_root, ensure_unique_path, file_sha256, normalize_mod_name
from .dataset import Dataset, _read_curseforge_data
from .scanner import scan_duplicates
from .dbpf import analyze_package_deep
from .errors import parse_sims4_errors, list_exception_files
from .history import (
    _load_all_history, save_scan_history, save_error_snapshot, save_mod_snapshot,
    load_custom_creators, save_custom_creators,
    load_mod_notes, save_mod_notes,
    load_mod_tags, save_mod_tags,
)
from .update import check_for_update
from .watcher import ModFolderWatcher
from .tray import analyze_tray, build_mod_instance_index
from .savegame import analyze_savegames
from .tray_portraits import build_portrait_index, get_portrait_jpeg, match_renamed_sims, build_library_index
from .basegame_sims import BASEGAME_SIMS
from .townie_detector import detect_townies, PACK_SIMS
from .wiki_portraits import get_wiki_portrait, get_wiki_portrait_cached
from .name_translation import batch_translate_names
from .avatar_generator import generate_sim_avatar
from .web.template import build_html_page


class LocalServer:
    def __init__(self, dataset: Dataset, quarantine_dir: Path, sims4_dir: str = "", cf_path: str = ""):
        self.dataset = dataset
        self.quarantine_dir = quarantine_dir
        self.sims4_dir = sims4_dir
        self.cf_path = cf_path
        self.token = secrets.token_urlsafe(24)
        self.port: int | None = None
        self.httpd = None
        self.log_file = self.quarantine_dir / "_sims4_actions.log.txt"
        self.scan_history: dict = {}
        self.mod_snapshot: dict = {}
        self._progress: dict = {"active": False, "phase": "", "cur": 0, "total": 0, "msg": "", "done": False, "error": ""}
        self._progress_lock = threading.Lock()
        self._watcher: ModFolderWatcher | None = None
        self._auto_rescan_msg = ""
        self._auto_rescan_time: float = 0
        self._tray_cache: dict | None = None
        self._tray_analyzing = False
        self._savegame_cache: dict | None = None
        self._savegame_analyzing = False
        self._portrait_index: dict | None = None
        self._portrait_index_built = False
        self._tray_households: list = []
        self._library_cache: dict | None = None
        self._library_analyzing = False
        self._cache_lock = threading.Lock()

    def _start_watcher(self):
        roots = self.dataset.roots if self.dataset else []
        if not roots:
            return

        def on_change(changes: list[str]):
            with self._progress_lock:
                if self._progress.get("active"):
                    print("[WATCHER] Scan läuft bereits — Auto-Rescan übersprungen", flush=True)
                    return
            self._auto_rescan_msg = f"🔄 Änderungen erkannt ({len(changes)}), starte Auto-Rescan…"
            self._auto_rescan_time = time.time()
            self._trigger_rescan()

        self._watcher = ModFolderWatcher(roots, on_change=on_change, interval=5.0, debounce=4.0)
        self._watcher.start()

    def _trigger_rescan(self):
        self._do_rescan(label="Auto-Rescan")

    def _do_rescan(self, label: str = "Rescan"):
        """Gemeinsame Rescan-Logik für Auto- und manuellen Rescan."""
        server_ref = self

        def _worker():
            try:
                server_ref._progress_lock.acquire()
                server_ref._progress.update({"active": True, "phase": "collect", "cur": 0, "total": 0, "msg": f"{label}…", "done": False, "error": ""})
                server_ref._progress_lock.release()

                def progress_cb(phase, cur, total, msg):
                    with server_ref._progress_lock:
                        server_ref._progress.update({"phase": phase, "cur": cur or 0, "total": total or 0, "msg": msg or ""})

                roots = server_ref.dataset.roots
                exts = {".package", ".ts4script", ".zip", ".7z", ".rar"}
                ignore_dirs = {"__macosx", ".git", "__pycache__"}
                sims4_dir = server_ref.sims4_dir

                files, name_d, content_d, similar_d, corrupt, conflicts, addon_pairs, contained_in, non_mod_paths = scan_duplicates(
                    roots=roots, exts=exts, ignore_dirs=ignore_dirs,
                    do_name=True, do_content=True, do_conflicts=True,
                    progress_cb=progress_cb,
                )
                ds = Dataset(roots, sims4_dir=sims4_dir)
                ds.all_scanned_files = files
                ds.build_from_scan(name_d, content_d, similar_d, corrupt, conflicts, addon_pairs, contained_in)

                deep_cache = load_deep_cache()
                server_ref._progress_lock.acquire()
                server_ref._progress.update({"phase": "deep", "cur": 0, "total": 0, "msg": "Tiefenanalyse…"})
                server_ref._progress_lock.release()
                ds.enrich_groups(progress_cb=progress_cb, deep_cache=deep_cache)
                ds.enrich_all_files(progress_cb=progress_cb, deep_cache=deep_cache)
                ds.detect_dependencies()
                ds.collect_non_mod_files(preloaded_paths=non_mod_paths)
                save_deep_cache(deep_cache)

                try:
                    server_ref.scan_history = save_scan_history(len(files), name_d, content_d, roots)
                    server_ref.mod_snapshot = save_mod_snapshot(files, roots)
                except Exception:
                    pass

                server_ref.dataset = ds
                done_msg = f"{label} fertig! {len(files)} Dateien."
                with server_ref._progress_lock:
                    server_ref._progress.update({"active": False, "done": True, "phase": "done", "msg": done_msg})
                if label == "Auto-Rescan":
                    server_ref._auto_rescan_msg = f"✅ {done_msg}"
                    server_ref._auto_rescan_time = time.time()
                if server_ref._watcher and server_ref._watcher._running:
                    server_ref._watcher._snapshot = server_ref._watcher._build_snapshot()
                print(f"[RESCAN] {done_msg}", flush=True)
            except Exception as ex:
                with server_ref._progress_lock:
                    server_ref._progress.update({"active": False, "done": False, "error": str(ex), "phase": "error", "msg": str(ex)})
                print(f"[RESCAN] {label} Fehler: {ex}", flush=True)

        threading.Thread(target=_worker, daemon=True, name=label.replace(" ", "")).start()

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
        try:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            size_str = human_size(size) if size else "?"
            msg = f"[{ts}] {action:15} | Size: {size_str:12} | {path}"
            if note:
                msg += f" | Note: {note}"
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(msg + "\n")
            csv_file = self.quarantine_dir / "_sims4_actions.csv"
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
        quarantine_dir = self.quarantine_dir
        append_log = self._append_log
        server_ref = self

        # Quarantäne-Ordner wird erst bei Bedarf erstellt (in _append_log/_log_action)
        if quarantine_dir.exists():
            append_log(f"SERVER START {self.port}")

        HTML_PAGE = build_html_page()
        HTML_PAGE = HTML_PAGE.replace("__TOKEN__", json.dumps(self.token))
        HTML_PAGE = HTML_PAGE.replace("__LOGFILE__", json.dumps(str(self.log_file)))

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _send(self, status: int, content: bytes, ctype="text/html; charset=utf-8"):
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(content)

            def _json(self, status: int, obj: dict):
                try:
                    raw = json.dumps(obj, ensure_ascii=False, allow_nan=False, default=str).encode("utf-8")
                except (ValueError, TypeError) as exc:
                    raw = json.dumps({"ok": False, "error": f"JSON-Serialisierung fehlgeschlagen: {exc}"}, ensure_ascii=False).encode("utf-8")
                self._send(status, raw, "application/json; charset=utf-8")

            def _enrich_savegame_portraits(self, srv):
                """Hängt Metadaten an savegame_cache an (schnell, kein HTTP)."""
                with srv._cache_lock:
                    if srv._savegame_cache and "portrait_names" not in srv._savegame_cache:
                        if not srv._portrait_index_built:
                            tray_path = os.path.join(srv.sims4_dir, "Tray") if srv.sims4_dir else ""
                            if tray_path and os.path.isdir(tray_path):
                                srv._portrait_index, srv._tray_households = build_portrait_index(tray_path)
                            else:
                                srv._portrait_index = {}
                                srv._tray_households = []
                            srv._portrait_index_built = True
                        idx = srv._portrait_index or {}
                        hh_data = srv._savegame_cache.get("households", {})
                        if hh_data and idx:
                            extra = match_renamed_sims(idx, srv._tray_households, hh_data)
                            if extra:
                                idx.update(extra)
                                print(f"[PORTRAITS] Rename-Match: {len(extra)} umbenannte Sims zugeordnet", flush=True)
                                for name, path in extra.items():
                                    print(f"  → {name} ← {path.split(chr(92))[-1] if chr(92) in path else path.split('/')[-1]}", flush=True)
                        portrait_names = list(idx.keys())
                        srv._savegame_cache["portrait_names"] = portrait_names
                    if srv._savegame_cache and "basegame_names" not in srv._savegame_cache:
                        srv._savegame_cache["basegame_names"] = [s["full_name"] for s in srv._savegame_cache.get("sims", []) if s.get("full_name") in BASEGAME_SIMS]
                    if srv._savegame_cache and "townie_names" not in srv._savegame_cache:
                        townie_list = detect_townies(
                            srv._savegame_cache.get("sims", []),
                            BASEGAME_SIMS,
                            srv._savegame_cache.get("portrait_names", []),
                        )
                        srv._savegame_cache["townie_names"] = townie_list
                        print(f"[TOWNIES] {len(townie_list)} EA-Townies erkannt", flush=True)
                    if srv._savegame_cache and "duplicate_sims" not in srv._savegame_cache:
                        all_sims = srv._savegame_cache.get("sims", [])
                        name_counts = Counter(s.get("full_name", "") for s in all_sims)
                        dupe_names = {n for n, c in name_counts.items() if c > 1 and n}
                        dupe_list = []
                        for name in sorted(dupe_names):
                            entries = [s for s in all_sims if s.get("full_name") == name]
                            dupe_list.append({
                                "name": name,
                                "count": len(entries),
                                "households": list({s.get("household", "?") for s in entries}),
                            })
                        srv._savegame_cache["duplicate_sims"] = dupe_list
                        if dupe_list:
                            print(f"[WARNUNG] {len(dupe_list)} doppelte Sims erkannt!", flush=True)
                            for d in dupe_list:
                                print(f"  ⚠️ {d['count']}x {d['name']} (Haushalte: {', '.join(d['households'])})", flush=True)
                    if srv._savegame_cache:
                        cc_hh = {}
                        if srv._tray_cache:
                            for item in srv._tray_cache.get("items", []):
                                if item.get("type") == 1 and item.get("cc_count", 0) > 0:
                                    hh_name = item.get("name", "")
                                    if hh_name:
                                        existing = cc_hh.get(hh_name, [])
                                        for m in item.get("used_mods", []):
                                            if m["name"] not in [e["name"] for e in existing]:
                                                existing.append(m)
                                        cc_hh[hh_name] = existing
                        old_count = len(srv._savegame_cache.get("cc_by_household", {}))
                        srv._savegame_cache["cc_by_household"] = cc_hh
                        if cc_hh and old_count != len(cc_hh):
                            print(f"[CC] CC-Daten für {len(cc_hh)} Haushalte zugeordnet", flush=True)
                    if srv._savegame_cache:
                        lib_names = set()
                        if srv._library_cache:
                            for hh in srv._library_cache.get("households", []):
                                for sim in hh.get("sims", []):
                                    lib_names.add(sim.get("full_name", ""))
                        old_count = len(srv._savegame_cache.get("library_sim_names", []))
                        srv._savegame_cache["library_sim_names"] = list(lib_names)
                        if lib_names and old_count != len(lib_names):
                            print(f"[BIBLIOTHEK] {len(lib_names)} Sims in Bibliothek erkannt", flush=True)

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

            def _check_token_qs(self, u) -> bool:
                """Prüft Token aus Query-String. Gibt True zurück wenn ungültig (403 schon gesendet)."""
                qs = parse_qs(u.query)
                if qs.get("token", [""])[0] != token:
                    self._json(403, {"ok": False, "error": "bad token"})
                    return True
                return False

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
                    if self._check_token_qs(u): return
                    d = server_ref.dataset.to_json()
                    cfg = load_config()
                    d["ignored_groups"] = cfg.get("ignored_groups", [])
                    self._json(200, {"ok": True, "data": d})
                    return

                if u.path == "/api/update-check":
                    if self._check_token_qs(u): return
                    try:
                        info = check_for_update(timeout=6.0)
                        self._json(200, {"ok": True, **info})
                    except Exception as ex:
                        self._json(200, {"ok": True, "available": False, "current": SCANNER_VERSION, "error": str(ex)})
                    return

                if u.path == "/api/errors":
                    if self._check_token_qs(u): return
                    try:
                        sims_dir_str = server_ref.sims4_dir
                        sims_dir = Path(sims_dir_str) if sims_dir_str else None
                        if sims_dir and sims_dir.is_dir():
                            print(f"[ERRORS] Sims4 Dir: {sims_dir}", flush=True)
                            errs = parse_sims4_errors(sims_dir)
                            err_snap = save_error_snapshot(errs)
                            exc_files = list_exception_files(sims_dir)
                            print(f"[ERRORS] {len(errs)} Fehler gefunden ({err_snap.get('fehler_neu',0)} neu, {err_snap.get('fehler_bekannt',0)} bekannt, {err_snap.get('fehler_behoben',0)} behoben), {len(exc_files)} Log-Dateien", flush=True)
                            self._json(200, {"ok": True, "sims4_dir": str(sims_dir), "errors": errs, "snapshot": err_snap, "exception_files": exc_files})
                        else:
                            print("[ERRORS] Kein gültiges Sims4 Dir angegeben", flush=True)
                            self._json(200, {"ok": True, "sims4_dir": None, "errors": [], "note": "Kein gültiges Sims 4 Verzeichnis angegeben. Bitte in der GUI einstellen."})
                    except Exception as ex:
                        print(f"[ERRORS][CRASH] {type(ex).__name__}: {ex}", flush=True)
                        import traceback; traceback.print_exc()
                        self._json(500, {"ok": False, "error": f"Fehler bei Analyse: {type(ex).__name__}: {ex}"})
                    return

                if u.path == "/api/history":
                    if self._check_token_qs(u): return
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
                    if self._check_token_qs(u): return
                    try:
                        q_parent = quarantine_dir.parent
                        q_dirs = sorted(q_parent.glob("dupe_quarantine_*"), reverse=True)
                        q_files: list[dict] = []
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
                                        'path': str(fp), 'name': fp.name,
                                        'q_dir': qd.name, 'size': sz,
                                        'size_h': human_size(sz), 'mtime': mt,
                                    })
                        self._json(200, {
                            "ok": True, "files": q_files,
                            "total_count": len(q_files),
                            "total_size_h": human_size(total_size),
                            "q_dirs": [str(d) for d in q_dirs if d.is_dir()],
                        })
                    except Exception as ex:
                        print(f"[QUARANTINE_LIST][ERR] {ex}", flush=True)
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/progress":
                    if self._check_token_qs(u): return
                    with server_ref._progress_lock:
                        self._json(200, dict(server_ref._progress))
                    return

                if u.path == "/api/watcher":
                    if self._check_token_qs(u): return
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
                    if self._check_token_qs(u): return
                    try:
                        creators = load_custom_creators()
                        self._json(200, {"ok": True, "creators": creators})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/notes":
                    if self._check_token_qs(u): return
                    try:
                        notes = load_mod_notes()
                        self._json(200, {"ok": True, "notes": notes})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/tags":
                    if self._check_token_qs(u): return
                    try:
                        tags = load_mod_tags()
                        self._json(200, {"ok": True, "tags": tags})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/curseforge":
                    if self._check_token_qs(u): return
                    try:
                        cf_data = _read_curseforge_data(cf_manifest_path=server_ref.cf_path)
                        self._json(200, {"ok": True, "curseforge": cf_data})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/mod_export":
                    if self._check_token_qs(u): return
                    try:
                        ds = server_ref.dataset
                        notes = load_mod_notes()
                        tags = load_mod_tags()
                        lines = ["Name;Pfad;Ordner;Größe;Geändert;Creator;Tags;Notiz"]
                        if ds:
                            data = ds.to_json()
                            seen: set[str] = set()
                            all_files: list[dict] = []
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
                                lines.append(f"{fname};{fpath};{mfolder};{sz};{mt};{cat};{ftags};{fnote}")
                        csv_data = '\n'.join(lines)
                        self._send(200, csv_data.encode('utf-8-sig'), 'text/csv; charset=utf-8')
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if u.path == "/api/tutorial":
                    if self._check_token_qs(u): return
                    seen_ref = getattr(server_ref, 'app_ref', None)
                    tutorial_seen = getattr(seen_ref, '_tutorial_seen', False) if seen_ref else False
                    self._json(200, {"ok": True, "tutorial_seen": tutorial_seen})
                    return

                if u.path == "/api/tray":
                    if self._check_token_qs(u): return
                    qs = parse_qs(u.query)
                    force = qs.get("force", [""])[0] == "1"
                    if server_ref._tray_analyzing:
                        self._json(200, {"ok": True, "status": "analyzing", "data": None})
                        return
                    if server_ref._tray_cache and not force:
                        self._json(200, {"ok": True, "status": "ready", "data": server_ref._tray_cache})
                        return
                    # Analyse asynchron starten
                    server_ref._tray_analyzing = True
                    def _run_tray():
                        try:
                            sims4 = server_ref.sims4_dir
                            tray_path = os.path.join(sims4, "Tray") if sims4 else ""
                            if not tray_path or not os.path.isdir(tray_path):
                                server_ref._tray_cache = {"items": [], "mod_usage": {}, "summary": {"total_items": 0, "households": 0, "lots": 0, "rooms": 0, "items_with_cc": 0, "total_mods_used": 0, "max_cc_item": "", "max_cc_count": 0}, "error": "Tray-Ordner nicht gefunden"}
                                return
                            roots = [Path(r) for r in server_ref.dataset.roots] if hasattr(server_ref.dataset, 'roots') else []
                            if not roots:
                                server_ref._tray_cache = {"items": [], "mod_usage": {}, "summary": {"total_items": 0, "households": 0, "lots": 0, "rooms": 0, "items_with_cc": 0, "total_mods_used": 0, "max_cc_item": "", "max_cc_count": 0}, "error": "Keine Mod-Ordner konfiguriert"}
                                return
                            mod_idx = build_mod_instance_index(roots)
                            result = analyze_tray(tray_path, mod_idx)
                            server_ref._tray_cache = result
                            # Library-Cache invalidieren damit CC neu zugeordnet wird
                            if server_ref._library_cache:
                                server_ref._library_cache = None
                                print("[TRAY] Library-Cache invalidiert — CC wird beim nächsten Laden neu berechnet", flush=True)
                        except Exception as ex:
                            server_ref._tray_cache = {"items": [], "mod_usage": {}, "summary": {"total_items": 0, "households": 0, "lots": 0, "rooms": 0, "items_with_cc": 0, "total_mods_used": 0, "max_cc_item": "", "max_cc_count": 0}, "error": str(ex)}
                        finally:
                            server_ref._tray_analyzing = False
                    threading.Thread(target=_run_tray, daemon=True).start()
                    self._json(200, {"ok": True, "status": "started", "data": None})
                    return

                if u.path == "/api/library":
                    if self._check_token_qs(u): return
                    qs = parse_qs(u.query)
                    force = qs.get("force", [""])[0] == "1"
                    if server_ref._library_analyzing:
                        self._json(200, {"ok": True, "status": "analyzing", "data": None})
                        return
                    if server_ref._library_cache and not force:
                        self._json(200, {"ok": True, "status": "ready", "data": server_ref._library_cache})
                        return
                    server_ref._library_analyzing = True
                    def _run_library():
                        try:
                            sims4 = server_ref.sims4_dir
                            tray_path = os.path.join(sims4, "Tray") if sims4 else ""
                            if not tray_path or not os.path.isdir(tray_path):
                                server_ref._library_cache = {"households": [], "error": "Tray-Ordner nicht gefunden"}
                                return
                            hh_list = build_library_index(tray_path)
                            # Savegame-Sims für Cross-Referenz
                            savegame_sim_names = set()
                            if server_ref._savegame_cache:
                                savegame_sim_names = {s.get("full_name", "") for s in server_ref._savegame_cache.get("sims", [])}
                            total_sims = 0
                            active_sims = 0
                            library_only = 0
                            for hh in hh_list:
                                for sim in hh["sims"]:
                                    total_sims += 1
                                    sim["in_savegame"] = sim["full_name"] in savegame_sim_names
                                    if sim["in_savegame"]:
                                        active_sims += 1
                                    else:
                                        library_only += 1

                            # CC-Info aus Tray-Cache zuordnen
                            tray_cc_map = {}
                            total_cc_households = 0
                            cc_data_available = bool(server_ref._tray_cache)
                            if server_ref._tray_cache:
                                for item in server_ref._tray_cache.get("items", []):
                                    if item.get("type") == 1:  # Nur Haushalte
                                        tray_cc_map[item["instance_id"].lower()] = item
                            for hh in hh_list:
                                fid = hh.get("file_id", "").lower()
                                tray_item = tray_cc_map.get(fid)
                                if tray_item:
                                    hh["cc_count"] = tray_item["cc_count"]
                                    hh["used_mods"] = tray_item["used_mods"]
                                    if tray_item["cc_count"] > 0:
                                        total_cc_households += 1
                                else:
                                    hh["cc_count"] = 0
                                    hh["used_mods"] = []

                            # Duplikate erkennen: Sims die in mehreren Haushalten vorkommen
                            sim_occurrences = {}  # name -> [(hh_name, hh_file_id), ...]
                            for hh in hh_list:
                                hh_name = hh.get("display_name") or hh.get("name", "")
                                for sim in hh["sims"]:
                                    sname = sim["full_name"]
                                    if sname not in sim_occurrences:
                                        sim_occurrences[sname] = []
                                    sim_occurrences[sname].append(hh_name)
                            duplicate_sims = []
                            for sname, hh_names in sim_occurrences.items():
                                if len(hh_names) > 1:
                                    duplicate_sims.append({
                                        "name": sname,
                                        "count": len(hh_names),
                                        "households": hh_names,
                                        "in_savegame": sname in savegame_sim_names,
                                    })
                            duplicate_sims.sort(key=lambda d: (-d["count"], d["name"]))
                            if duplicate_sims:
                                print(f"[BIBLIOTHEK] {len(duplicate_sims)} doppelte Sims in Bibliothek erkannt", flush=True)

                            # Löschbar-Analyse: HH ist löschbar wenn ALLE Sims
                            # entweder im Savegame oder in mind. einem anderen HH existieren
                            safe_count = 0
                            for hh in hh_list:
                                hh_name = hh.get("display_name") or hh.get("name", "")
                                all_safe = True
                                unique_sims = []
                                for sim in hh["sims"]:
                                    sn = sim["full_name"]
                                    in_save = sn in savegame_sim_names
                                    in_other = len([h for h in sim_occurrences.get(sn, []) if h != hh_name]) > 0
                                    sim["is_unique"] = not in_save and not in_other
                                    if sim["is_unique"]:
                                        all_safe = False
                                        unique_sims.append(sn)
                                hh["safe_to_delete"] = all_safe
                                hh["unique_sims"] = unique_sims
                                if all_safe:
                                    safe_count += 1
                            if safe_count:
                                print(f"[BIBLIOTHEK] {safe_count} Haushalte sicher löschbar (ohne Sim-Verlust)", flush=True)

                            server_ref._library_cache = {
                                "households": hh_list,
                                "total_households": len(hh_list),
                                "total_sims": total_sims,
                                "active_sims": active_sims,
                                "library_only": library_only,
                                "total_cc_households": total_cc_households,
                                "cc_data_available": cc_data_available,
                                "duplicate_sims": duplicate_sims,
                                "safe_to_delete_count": safe_count,
                            }

                            # ── Portrait-Daten für Bibliotheks-Sims einbetten ──
                            lib_portrait_data = {}
                            lib_idx = server_ref._portrait_index or {}
                            lib_tray = 0
                            lib_wiki = 0
                            for hh in hh_list:
                                for sim in hh.get("sims", []):
                                    sname = sim.get("full_name", "")
                                    if not sname or sname in lib_portrait_data:
                                        continue
                                    try:
                                        jpeg = get_portrait_jpeg(lib_idx, sname)
                                        if jpeg:
                                            lib_portrait_data[sname] = "data:image/jpeg;base64," + _b64.b64encode(jpeg).decode("ascii")
                                            lib_tray += 1
                                            continue
                                        wiki_img = get_wiki_portrait(sname)
                                        if wiki_img:
                                            lib_portrait_data[sname] = "data:image/jpeg;base64," + _b64.b64encode(wiki_img).decode("ascii")
                                            lib_wiki += 1
                                    except Exception:
                                        pass
                            if lib_portrait_data:
                                server_ref._library_cache["portrait_data"] = lib_portrait_data
                                print(f"[BIBLIOTHEK] {len(lib_portrait_data)} Portraits eingebettet ({lib_tray} Tray, {lib_wiki} Wiki)", flush=True)

                            print(f"[BIBLIOTHEK] {len(hh_list)} Haushalte, {total_sims} Sims ({active_sims} im Spiel, {library_only} nur Bibliothek, {total_cc_households} mit CC)", flush=True)
                        except Exception as ex:
                            import traceback; traceback.print_exc()
                            server_ref._library_cache = {"households": [], "error": str(ex)}
                        finally:
                            server_ref._library_analyzing = False
                    threading.Thread(target=_run_library, daemon=True).start()
                    self._json(200, {"ok": True, "status": "started", "data": None})
                    return

                if u.path == "/api/savegame":
                    if self._check_token_qs(u): return
                    qs = parse_qs(u.query)
                    force = qs.get("force", [""])[0] == "1"
                    selected_save = qs.get("save", [""])[0]
                    # Bei Wechsel des Saves immer neu laden
                    if selected_save:
                        force = True
                    if server_ref._savegame_analyzing:
                        self._json(200, {"ok": True, "status": "analyzing", "data": None})
                        return
                    if server_ref._savegame_cache and not force:
                        # Portrait-Info anhängen
                        self._enrich_savegame_portraits(server_ref)
                        self._json(200, {"ok": True, "status": "ready", "data": server_ref._savegame_cache})
                        return
                    server_ref._savegame_analyzing = True
                    def _run_savegame():
                        try:
                            sims4 = server_ref.sims4_dir
                            saves_path = os.path.join(sims4, "saves") if sims4 else ""
                            if not saves_path or not os.path.isdir(saves_path):
                                server_ref._savegame_cache = {"sims": [], "sim_count": 0, "available_saves": [], "error": "Save-Ordner nicht gefunden"}
                                return
                            result = analyze_savegames(saves_path, selected_save)
                            server_ref._savegame_cache = result

                            # ── Portrait-Daten im Hintergrund einbetten ──
                            print("[PORTRAITS] Starte Portrait-Einbettung...", flush=True)
                            # Portrait-Index aufbauen
                            if not server_ref._portrait_index_built:
                                tray_path2 = os.path.join(sims4, "Tray") if sims4 else ""
                                if tray_path2 and os.path.isdir(tray_path2):
                                    server_ref._portrait_index, server_ref._tray_households = build_portrait_index(tray_path2)
                                else:
                                    server_ref._portrait_index = {}
                                    server_ref._tray_households = []
                                server_ref._portrait_index_built = True
                            idx = server_ref._portrait_index or {}
                            # Rename-Match
                            hh_data = result.get("households", {})
                            if hh_data and idx:
                                extra_m = match_renamed_sims(idx, server_ref._tray_households, hh_data)
                                if extra_m:
                                    idx.update(extra_m)
                            portrait_names = list(idx.keys())
                            result["portrait_names"] = portrait_names

                            portrait_data = {}
                            all_sims2 = result.get("sims", [])
                            tray_count = 0
                            wiki_count = 0
                            svg_count = 0
                            err_count = 0

                            # Phase 1: Tray-Portraits + Cached/Embedded (kein HTTP)
                            need_wiki = []  # Sims die Wiki-Download brauchen
                            sim_info_map = {}  # name -> sim dict für SVG-Fallback
                            seen = set()
                            for sim in all_sims2:
                                sim_name = sim.get("full_name", "")
                                if not sim_name or sim_name in seen:
                                    continue
                                seen.add(sim_name)
                                sim_info_map[sim_name] = sim
                                # Tray-Portrait (lokale SGI-Datei)
                                jpeg = get_portrait_jpeg(idx, sim_name)
                                if jpeg:
                                    portrait_data[sim_name] = "data:image/jpeg;base64," + _b64.b64encode(jpeg).decode("ascii")
                                    tray_count += 1
                                    continue
                                # Cached/Embedded Portrait (kein HTTP)
                                cached = get_wiki_portrait_cached(sim_name)
                                if cached:
                                    portrait_data[sim_name] = "data:image/jpeg;base64," + _b64.b64encode(cached).decode("ascii")
                                    wiki_count += 1
                                    continue
                                need_wiki.append(sim_name)

                            # Phase 2: Batch Name-Translation (50 pro Request statt einzeln)
                            if need_wiki:
                                print(f"[PORTRAITS] {len(need_wiki)} Sims brauchen Wiki-Download...", flush=True)
                                batch_translate_names(need_wiki)  # Pre-cache alle Übersetzungen

                            # Phase 3: Wiki-Downloads parallel (ThreadPool, 8 Worker)
                            def _fetch_wiki_portrait(sim_name):
                                try:
                                    img = get_wiki_portrait(sim_name)
                                    if img:
                                        return (sim_name, "data:image/jpeg;base64," + _b64.b64encode(img).decode("ascii"), "wiki")
                                    # SVG-Fallback
                                    si = sim_info_map.get(sim_name, {})
                                    svg = generate_sim_avatar(
                                        name=sim_name,
                                        gender=si.get("gender", "Unbekannt"),
                                        age=si.get("age", "Erwachsener"),
                                        skin_tone=si.get("skin_tone", ""),
                                        species=si.get("species", ""),
                                    )
                                    if svg:
                                        return (sim_name, "data:image/svg+xml;base64," + _b64.b64encode(svg).decode("ascii"), "svg")
                                except Exception:
                                    return (sim_name, None, "error")
                                return (sim_name, None, "none")

                            if need_wiki:
                                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                                    futures = {pool.submit(_fetch_wiki_portrait, name): name for name in need_wiki}
                                    for future in concurrent.futures.as_completed(futures):
                                        try:
                                            name, data_uri, src = future.result()
                                            if data_uri:
                                                portrait_data[name] = data_uri
                                                if src == "wiki":
                                                    wiki_count += 1
                                                elif src == "svg":
                                                    svg_count += 1
                                            elif src == "error":
                                                err_count += 1
                                        except Exception:
                                            err_count += 1

                            result["portrait_data"] = portrait_data
                            print(f"[PORTRAITS] {len(portrait_data)} Portraits eingebettet ({tray_count} Tray, {wiki_count} Wiki, {svg_count} SVG" + (f", {err_count} Fehler" if err_count else "") + ")", flush=True)
                        except Exception as ex:
                            server_ref._savegame_cache = {"sims": [], "sim_count": 0, "available_saves": [], "error": str(ex)}
                        finally:
                            server_ref._savegame_analyzing = False
                    threading.Thread(target=_run_savegame, daemon=True).start()
                    self._json(200, {"ok": True, "status": "started", "data": None})
                    return

                if u.path == "/api/sim-portrait":
                    if self._check_token_qs(u): return
                    qs = parse_qs(u.query)
                    sim_name = qs.get("name", [""])[0]
                    if not sim_name:
                        self._send(400, b"missing name", "text/plain")
                        return
                    # Portrait-Index lazy aufbauen
                    if not server_ref._portrait_index_built:
                        tray_path = os.path.join(server_ref.sims4_dir, "Tray") if server_ref.sims4_dir else ""
                        if tray_path and os.path.isdir(tray_path):
                            server_ref._portrait_index, server_ref._tray_households = build_portrait_index(tray_path)
                        else:
                            server_ref._portrait_index = {}
                            server_ref._tray_households = []
                        server_ref._portrait_index_built = True
                    idx = server_ref._portrait_index or {}
                    jpeg = get_portrait_jpeg(idx, sim_name)
                    if jpeg:
                        self._send(200, jpeg, "image/jpeg")
                        return
                    # Fallback 2: Wiki-Portrait für alle Sims versuchen
                    wiki_img = get_wiki_portrait(sim_name)
                    if wiki_img:
                        self._send(200, wiki_img, "image/jpeg")
                        return
                    # Fallback 3: SVG-Avatar generieren
                    sim_data = {}
                    if server_ref._savegame_cache:
                        for s in server_ref._savegame_cache.get("sims", []):
                            if s.get("full_name") == sim_name:
                                sim_data = s
                                break
                    svg = generate_sim_avatar(
                        name=sim_name,
                        gender=sim_data.get("gender", "Unbekannt"),
                        age=sim_data.get("age", "Erwachsener"),
                        skin_tone=sim_data.get("skin_tone", ""),
                        species=sim_data.get("species", ""),
                    )
                    self._send(200, svg, "image/svg+xml")
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
                        creators = load_custom_creators()
                        creators[key] = {"name": cname, "url": curl, "icon": cicon}
                        save_custom_creators(creators)
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
                        creators = load_custom_creators()
                        if key in creators:
                            del creators[key]
                            save_custom_creators(creators)
                        self._json(200, {"ok": True, "deleted": key})
                        print(f"[CREATOR] Deleted: {key}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "save_note":
                    try:
                        fpath = payload.get("path", "").strip()
                        note_text = payload.get("note", "").strip()
                        if not fpath:
                            self._json(400, {"ok": False, "error": "path erforderlich"})
                            return
                        notes = load_mod_notes()
                        if note_text:
                            notes[fpath] = note_text
                        elif fpath in notes:
                            del notes[fpath]
                        save_mod_notes(notes)
                        self._json(200, {"ok": True, "path": fpath})
                        print(f"[NOTE] Saved for: {Path(fpath).name}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "add_tag":
                    try:
                        fpath = payload.get("path", "").strip()
                        tag = payload.get("tag", "").strip()
                        if not fpath or not tag:
                            self._json(400, {"ok": False, "error": "path und tag erforderlich"})
                            return
                        tags = load_mod_tags()
                        if fpath not in tags:
                            tags[fpath] = []
                        if tag not in tags[fpath]:
                            tags[fpath].append(tag)
                        save_mod_tags(tags)
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
                        tags = load_mod_tags()
                        if fpath in tags and tag in tags[fpath]:
                            tags[fpath].remove(tag)
                            if not tags[fpath]:
                                del tags[fpath]
                        save_mod_tags(tags)
                        self._json(200, {"ok": True, "path": fpath, "tags": tags.get(fpath, [])})
                        print(f"[TAG] Removed '{tag}' from: {Path(fpath).name}", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                # ---- Mod-Import-Manager ----
                if action == "import_upload":
                    try:
                        filename = payload.get("filename", "").strip()
                        filedata_b64 = payload.get("filedata", "")
                        subfolder = payload.get("subfolder", "").strip()
                        relative_path = payload.get("relative_path", "").strip().replace("\\", "/")
                        if ".." in relative_path or ".." in subfolder:
                            self._json(400, {"ok": False, "error": "Ungültiger Pfad (Path Traversal nicht erlaubt)"})
                            return
                        if not filename:
                            self._json(400, {"ok": False, "error": "Kein Dateiname"})
                            return
                        file_bytes = _b64.b64decode(filedata_b64)
                        tmp_dir = Path(_tf.gettempdir()) / "sims4_import"
                        tmp_dir.mkdir(parents=True, exist_ok=True)
                        tmp_path = tmp_dir / filename
                        tmp_path.write_bytes(file_bytes)
                        src_name = filename.lower()
                        src_hash = file_sha256(tmp_path)
                        src_size = len(file_bytes)
                        matches: list[dict] = []
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
                            shutil.copy2(str(tmp_path), str(dest))
                            self._json(200, {"ok": True, "status": "new", "imported": True, "dest": str(dest), "size_h": human_size(src_size), "relative_path": relative_path})
                            print(f"[IMPORT_UPLOAD] NEW: {filename} -> {dest}", flush=True)
                            append_log(f"IMPORT_UPLOAD NEW {filename} -> {dest}")
                        elif all(m["relation"] == "identical" for m in matches):
                            self._json(200, {"ok": True, "status": "identical", "imported": False, "matches": matches})
                            print(f"[IMPORT_UPLOAD] IDENTICAL: {filename}", flush=True)
                        else:
                            self._json(200, {"ok": True, "status": "update", "imported": False, "matches": matches, "tmp_path": str(tmp_path), "size_h": human_size(src_size)})
                            print(f"[IMPORT_UPLOAD] UPDATE: {filename} ({len(matches)} match(es))", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_upload_confirm":
                    try:
                        tmp_path = Path(payload.get("tmp_path", ""))
                        replace_path = Path(payload.get("replace_path", ""))
                        if not tmp_path.exists():
                            self._json(400, {"ok": False, "error": "Temp-Datei nicht mehr vorhanden"})
                            return
                        # Sicherheitscheck: replace_path muss unter einem Mod-Root liegen
                        if not is_under_any_root(replace_path, server_ref.dataset.roots if server_ref.dataset else []):
                            self._json(400, {"ok": False, "error": "Zielpfad nicht erlaubt (nicht unter Mod-Ordner)"})
                            print(f"[BLOCKED] import_upload_confirm -> {replace_path}", flush=True)
                            return
                        shutil.copy2(str(tmp_path), str(replace_path))
                        self._json(200, {"ok": True, "replaced": True, "dest": str(replace_path)})
                        print(f"[IMPORT_UPLOAD] REPLACED: {tmp_path.name} -> {replace_path}", flush=True)
                        append_log(f"IMPORT_UPLOAD REPLACE {tmp_path.name} -> {replace_path}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_scan":
                    try:
                        source_dir = Path(payload.get("source", "").strip())
                        if not source_dir.exists() or not source_dir.is_dir():
                            self._json(400, {"ok": False, "error": f"Ordner nicht gefunden: {source_dir}"})
                            return
                        # Sicherheitscheck: keine System-Verzeichnisse scannen
                        _blocked = {"windows", "system32", "program files", "program files (x86)", "programdata"}
                        _src_parts = {p.lower() for p in source_dir.resolve().parts}
                        if _blocked & _src_parts:
                            self._json(400, {"ok": False, "error": "Systemverzeichnisse können nicht gescannt werden"})
                            return
                        mod_exts = {".package", ".ts4script"}
                        found_files: list[dict] = []
                        for fp in source_dir.rglob("*"):
                            if fp.is_file() and fp.suffix.lower() in mod_exts:
                                sz, mt = safe_stat(fp)
                                found_files.append({
                                    "path": str(fp), "name": fp.name,
                                    "size": sz, "size_h": human_size(sz),
                                    "mtime": datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S") if mt else "?",
                                })
                        self._json(200, {"ok": True, "files": found_files, "count": len(found_files)})
                        print(f"[IMPORT] Scan: {source_dir} -> {len(found_files)} Dateien", flush=True)
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_check":
                    try:
                        source_path = Path(payload.get("source_path", "").strip())
                        if not source_path.exists() or not source_path.is_file():
                            self._json(400, {"ok": False, "error": "Datei nicht gefunden"})
                            return
                        src_name = source_path.name.lower()
                        src_hash = file_sha256(source_path)
                        src_size, _ = safe_stat(source_path)
                        matches: list[dict] = []
                        existing_files = server_ref.dataset.all_scanned_files if server_ref.dataset else []

                        def _strip_version(n):
                            n = re.sub(r'[_\-\s]?v?\d+(\.\d+)*[a-z]?$', '', Path(n).stem, flags=re.IGNORECASE)
                            return n.lower().strip()

                        for ep in existing_files:
                            if not ep.exists():
                                continue
                            ep_name = ep.name.lower()
                            match_type = None
                            try:
                                ep_hash = file_sha256(ep)
                                if ep_hash == src_hash:
                                    match_type = "identical"
                            except Exception:
                                ep_hash = ""
                            if not match_type and ep_name == src_name:
                                match_type = "same_name"
                            if not match_type:
                                if _strip_version(src_name) == _strip_version(ep_name) and _strip_version(src_name):
                                    match_type = "similar_name"
                            if match_type:
                                ep_sz, ep_mt = safe_stat(ep)
                                matches.append({
                                    "path": str(ep), "name": ep.name,
                                    "size": ep_sz, "size_h": human_size(ep_sz),
                                    "match_type": match_type,
                                })
                        if any(m["match_type"] == "identical" for m in matches):
                            status = "identical"
                        elif any(m["match_type"] == "same_name" for m in matches):
                            status = "update"
                        elif any(m["match_type"] == "similar_name" for m in matches):
                            status = "similar"
                        else:
                            status = "new"
                        self._json(200, {"ok": True, "source": str(source_path), "hash": src_hash, "status": status, "matches": matches})
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                    return

                if action == "import_execute":
                    try:
                        source_path = Path(payload.get("source_path", "").strip())
                        subfolder = payload.get("subfolder", "").strip()
                        mode = payload.get("mode", "copy")
                        replace_path = payload.get("replace_path", "").strip()
                        # Sicherheitscheck: kein Path-Traversal im subfolder
                        if ".." in subfolder:
                            self._json(400, {"ok": False, "error": "Ungültiger Unterordner (Path Traversal nicht erlaubt)"})
                            return
                        if not source_path.exists() or not source_path.is_file():
                            self._json(400, {"ok": False, "error": "Quelldatei nicht gefunden"})
                            return
                        target_root = server_ref.dataset.roots[0] if server_ref.dataset and server_ref.dataset.roots else None
                        if not target_root:
                            self._json(400, {"ok": False, "error": "Kein Mods-Ordner bekannt"})
                            return
                        if mode == "update" and replace_path:
                            dest = Path(replace_path)
                            # Sicherheitscheck: Ziel muss unter einem Mod-Root liegen
                            if not is_under_any_root(dest, server_ref.dataset.roots if server_ref.dataset else []):
                                self._json(400, {"ok": False, "error": "Zielpfad nicht erlaubt (nicht unter Mod-Ordner)"})
                                return
                            if not dest.parent.exists():
                                dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(source_path), str(dest))
                            print(f"[IMPORT] UPDATE: {source_path.name} -> {dest}", flush=True)
                            append_log(f"IMPORT_UPDATE {source_path} -> {dest}")
                        else:
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

                # Rescan
                if action == "rescan":
                    with server_ref._progress_lock:
                        if server_ref._progress.get("active"):
                            self._json(200, {"ok": False, "error": "scan already running"})
                            return
                    server_ref._do_rescan(label="Rescan")
                    self._json(200, {"ok": True, "started": True})
                    return

                # Restore/delete_q: must be in quarantine
                if action in ("restore", "delete_q"):
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
                    pass
                elif not is_under_any_root(p, server_ref.dataset.roots):
                    self._json(400, {"ok": False, "error": "path not allowed (not under selected roots)"})
                    print(f"[BLOCKED] {action} -> {p}", flush=True)
                    append_log(f"BLOCKED {action} {p}")
                    return

                if action == "open_folder":
                    try:
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
                            server_ref._log_action("QUARANTINE", str(p), None, "MISSING", "file missing")
                            return
                        size, _ = safe_stat(p)
                        idx = best_root_index(p, server_ref.dataset.roots)
                        label = f"Ordner{idx + 1}" if idx is not None else "Unbekannt"
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
                        server_ref._log_action("QUARANTINE", str(p), size, "OK", f"moved to {dest}")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[QUARANTINE][ERR] {p} :: {ex}", flush=True)
                        server_ref._log_action("QUARANTINE", str(p), None, "ERROR", str(ex))
                    return

                if action == "delete":
                    try:
                        if not p.exists():
                            server_ref.dataset.remove_file(str(p))
                            self._json(200, {"ok": True, "deleted": False, "note": "file missing (removed from list)", "path": str(p)})
                            print(f"[DELETE][MISSING] {p}", flush=True)
                            server_ref._log_action("DELETE", str(p), None, "MISSING", "file missing")
                            return
                        if not p.is_file():
                            self._json(400, {"ok": False, "error": "not a file"})
                            print(f"[DELETE][NOT_FILE] {p}", flush=True)
                            server_ref._log_action("DELETE", str(p), None, "ERROR", "not a file")
                            return
                        size, _ = safe_stat(p)
                        p.unlink()
                        server_ref.dataset.remove_file(str(p))
                        self._json(200, {"ok": True, "deleted": True, "path": str(p)})
                        print(f"[DELETE] OK: {p}", flush=True)
                        server_ref._log_action("DELETE", str(p), size, "OK", "")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[DELETE][ERR] {p} :: {ex}", flush=True)
                        server_ref._log_action("DELETE", str(p), None, "ERROR", str(ex))
                    return

                if action == "restore":
                    try:
                        if not p.exists() or not p.is_file():
                            self._json(200, {"ok": True, "restored": False, "note": "file missing"})
                            return
                        size, _ = safe_stat(p)
                        target_root = server_ref.dataset.roots[0] if server_ref.dataset.roots else None
                        if not target_root:
                            self._json(400, {"ok": False, "error": "Kein Mod-Ordner bekannt"})
                            return
                        try:
                            rel_parts = p.relative_to(quarantine_dir.parent).parts
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
                    self._handle_bug_report(payload, server_ref, token, append_log)
                    return

                self._json(404, {"ok": False, "error": "unknown action"})
                print(f"[UNKNOWN_ACTION] {action} -> {p}", flush=True)
                append_log(f"UNKNOWN_ACTION {action} {p}")

            def _handle_bug_report(self, payload, server_ref, token, append_log):
                """Handles the send_bug_report action — extracted to keep do_POST manageable."""
                try:
                    category = payload.get("category", "").strip()
                    symptoms = payload.get("symptoms", [])

                    # Pfade in Texten anonymisieren (Benutzername entfernen)
                    def _sanitize_paths(text: str) -> str:
                        """Ersetzt C:\\Users\\XXX\\ durch C:\\Users\\***\\ in Texten."""
                        return re.sub(
                            r'([A-Za-z]:\\+[Uu]sers\\+)[^\\/:*?"<>|\r\n]+',
                            r'\1***',
                            text
                        )
                    description = payload.get("description", "").strip()

                    if not category:
                        self._json(400, {"ok": False, "error": "Bitte wähle eine Kategorie"})
                        return
                    if not symptoms and not description:
                        self._json(400, {"ok": False, "error": "Bitte wähle Symptome oder beschreibe das Problem"})
                        return

                    cat_labels = {
                        'crash': '💥 Absturz / Einfrieren', 'scan': '🔍 Scan-Problem',
                        'display': '🖥️ Anzeige-Fehler', 'action': '⚡ Aktion funktioniert nicht',
                        'import': '📥 Import-Problem', 'curseforge': '🔥 CurseForge-Problem',
                        'performance': '🐢 Performance-Problem', 'other': '❓ Sonstiges',
                    }
                    cat_label = cat_labels.get(category, category)
                    symptom_text = ', '.join(symptoms) if symptoms else 'Keine ausgewählt'
                    desc_text = description if description else 'Keine Beschreibung'
                    sys_info = f"Windows {_plat.version()} | Python {_plat.python_version()} | Scanner v{SCANNER_VERSION}"

                    game_ver = "Nicht gefunden"
                    sims4_path = Path(server_ref.sims4_dir) if server_ref.sims4_dir else None
                    if sims4_path and sims4_path.exists():
                        gv_file = sims4_path / "GameVersion.txt"
                        if gv_file.exists():
                            try:
                                game_ver = gv_file.read_text(encoding='utf-8', errors='replace').strip()[:200]
                            except Exception:
                                game_ver = "Nicht lesbar"

                    scan_summary = "Kein Scan vorhanden"
                    mod_type_stats = "Keine Daten"
                    ds = server_ref.dataset
                    s = {}
                    d_full = {}
                    if ds:
                        d_full = ds.to_json()
                        s = d_full.get('summary', {})
                        scan_summary = (
                            f"Dateien: {s.get('total_files', '?')} | "
                            f"Duplikate: Name {s.get('groups_name', 0)} / Inhalt {s.get('groups_content', 0)} / Ähnlich {s.get('groups_similar', 0)} | "
                            f"Korrupt: {s.get('corrupt_count', 0)} | Konflikte: {s.get('conflict_count', 0)}"
                        )
                        try:
                            type_counts: dict[str, int] = {}
                            for af in d_full.get('all_files', []):
                                ext = Path(af.get('path', '')).suffix.lower()
                                if ext:
                                    type_counts[ext] = type_counts.get(ext, 0) + 1
                            if type_counts:
                                mod_type_stats = ' | '.join(f"{ext}: {cnt}" for ext, cnt in sorted(type_counts.items(), key=lambda x: -x[1]))
                        except Exception:
                            mod_type_stats = "Fehler beim Zählen"

                    mod_folders = "Keine"
                    if ds and ds.roots:
                        mod_folders = ', '.join(str(r) for r in ds.roots)

                    all_exc_files_data: list[tuple[str, str]] = []
                    all_ui_exc_files_data: list[tuple[str, str]] = []
                    all_other_exc_files_data: list[tuple[str, str]] = []
                    error_messages: list[str] = []
                    broken_mods: list[str] = []

                    if sims4_path and sims4_path.exists():
                        exc_files = sorted(sims4_path.glob("lastException*.txt"),
                                           key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
                        for ef in exc_files[:1]:  # nur die neueste
                            try:
                                content = _sanitize_paths(ef.read_text(encoding='utf-8', errors='replace'))
                                all_exc_files_data.append((ef.name, content))
                                desync_match = re.search(r'<desyncdata>(.*?)</desyncdata>', content, re.DOTALL)
                                if desync_match:
                                    raw = desync_match.group(1).replace('&#13;&#10;', '\n').replace('&#10;', '\n').replace('&#13;', '\n')
                                    first_line = raw.strip().split('\n')[0][:300]
                                    if first_line and first_line not in error_messages:
                                        error_messages.append(first_line)
                                advice_match = re.search(r'<Advice>(.*?)</Advice>', content)
                                if advice_match:
                                    advice = advice_match.group(1).strip()
                                    if advice and advice not in error_messages:
                                        error_messages.append(f"[BE] {advice}")
                                cat_match = re.search(r'<categoryid>(.*?)</categoryid>', content)
                                if cat_match:
                                    cat_val = cat_match.group(1).strip()
                                    if cat_val and cat_val not in ('', 'Unknown'):
                                        broken_mods.append(cat_val)
                                mod_hits = re.findall(r'([a-zA-Z_]{3,}(?:mods?|interactions?|script|cheats?|overhaul)[a-zA-Z0-9_]*)', content, re.IGNORECASE)
                                mod_hits += re.findall(r'(?:TypeError|Error):\s*(\w+?)[\s(]', content)
                                for m in mod_hits:
                                    if len(m) > 5 and m.lower() not in ('module', 'import', 'error', 'false', 'string', 'version', 'typeerror', 'script'):
                                        if m not in broken_mods:
                                            broken_mods.append(m)
                            except Exception:
                                all_exc_files_data.append((ef.name, "NICHT LESBAR"))

                        ui_exc_files = sorted(sims4_path.glob("lastUIException*.txt"),
                                              key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
                        for uf in ui_exc_files[:1]:  # nur die neueste
                            try:
                                content = _sanitize_paths(uf.read_text(encoding='utf-8', errors='replace'))
                                all_ui_exc_files_data.append((uf.name, content))
                                desync_match = re.search(r'<desyncdata>(.*?)</desyncdata>', content, re.DOTALL)
                                if desync_match:
                                    raw = desync_match.group(1).replace('&#13;&#10;', '\n').replace('&#10;', '\n')
                                    first_line = raw.strip().split('\n')[0][:300]
                                    if first_line and first_line not in error_messages:
                                        error_messages.append(first_line)
                                cat_match = re.search(r'<categoryid>(.*?)</categoryid>', content)
                                if cat_match:
                                    cat_val = cat_match.group(1).strip()
                                    if cat_val and cat_val not in ('', 'Unknown') and cat_val not in broken_mods:
                                        broken_mods.append(cat_val)
                            except Exception:
                                all_ui_exc_files_data.append((uf.name, "NICHT LESBAR"))

                        # Sonstige *Exception*.txt (Mod-spezifische)
                        known_exc_names = {e[0] for e in all_exc_files_data} | {e[0] for e in all_ui_exc_files_data}
                        other_exc_files = sorted(
                            [f for f in sims4_path.glob("*Exception*.txt") if f.name not in known_exc_names],
                            key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True
                        )
                        for oef in other_exc_files[:5]:
                            try:
                                content = _sanitize_paths(oef.read_text(encoding='utf-8', errors='replace'))
                                all_other_exc_files_data.append((oef.name, content[:100000]))
                            except Exception:
                                all_other_exc_files_data.append((oef.name, "NICHT LESBAR"))

                    scanner_log_full = ""
                    if server_ref.log_file and server_ref.log_file.exists():
                        try:
                            scanner_log_full = _sanitize_paths(server_ref.log_file.read_text(encoding='utf-8', errors='replace'))
                        except Exception:
                            pass

                    # Mod-Logs aus mod_logs/ Ordner lesen
                    mod_logs_data: list[tuple[str, str]] = []
                    if sims4_path and sims4_path.exists():
                        mod_logs_dir = sims4_path / "mod_logs"
                        if mod_logs_dir.is_dir():
                            for ml_file in sorted(mod_logs_dir.glob("*.txt"), key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)[:5]:
                                try:
                                    ml_content = _sanitize_paths(ml_file.read_text(encoding='utf-8', errors='replace'))
                                    mod_logs_data.append((ml_file.name, ml_content[:50000]))
                                except Exception:
                                    mod_logs_data.append((ml_file.name, "NICHT LESBAR"))

                    # Auto-Analyse
                    has_exc = len(all_exc_files_data) > 0
                    has_ui_exc = len(all_ui_exc_files_data) > 0
                    has_other_exc = len(all_other_exc_files_data) > 0
                    broken_mods = list(dict.fromkeys(broken_mods))[:10]

                    has_corrupt = False
                    has_dupes = False
                    has_conflicts = False
                    dupe_count = 0
                    conflict_count = 0
                    corrupt_count = 0
                    if ds:
                        s2 = d_full.get('summary', {})
                        corrupt_count = s2.get('corrupt_count', 0)
                        conflict_count = s2.get('conflict_count', 0)
                        dupe_count = s2.get('groups_name', 0) + s2.get('groups_content', 0) + s2.get('groups_similar', 0)
                        has_corrupt = corrupt_count > 0
                        has_dupes = dupe_count > 0
                        has_conflicts = conflict_count > 0

                    critical_symptoms = ('Absturz', 'Einfrieren', 'wird nicht gestartet', 'Scan startet nicht')
                    has_critical_symptom = any(s_name in symptom_text for s_name in critical_symptoms)

                    if category in ('crash', 'scan') and (has_exc or has_critical_symptom):
                        severity = "🔴 Kritisch"
                    elif has_corrupt or (has_exc and category in ('crash', 'scan')):
                        severity = "🔴 Kritisch"
                    elif has_exc or has_conflicts or category == 'performance':
                        severity = "🟡 Mittel"
                    else:
                        severity = "🟢 Gering"

                    hints: list[str] = []
                    if has_corrupt:
                        hints.append(f"⛔ {corrupt_count} korrupte Datei(en) gefunden — echtes Problem!")
                    if has_exc and broken_mods:
                        hints.append(f"🔥 Fehlerhafte Mods/Quellen: {', '.join(broken_mods[:5])}")
                    elif has_exc:
                        hints.append("⚠️ Exception vorhanden — wahrscheinlich Mod-Konflikt")
                    if has_ui_exc:
                        hints.append("⚠️ UI-Exception vorhanden — möglicherweise UI-Mod-Problem")
                    if has_other_exc:
                        hints.append(f"📄 {len(all_other_exc_files_data)} Mod-Exception-Dateien gefunden")
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
                    if not has_exc and not has_ui_exc and not has_other_exc and not has_corrupt and not has_conflicts:
                        hints.append("✅ Keine Fehler in Logs — alles sauber")
                    if len(description) < 10 and not symptoms:
                        hints.append("🤷 Sehr wenig Info vom User — evtl. verwirrt")

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

                    # Creators / Notes / Tags laden
                    user_creators = load_custom_creators()
                    user_notes = load_mod_notes()
                    user_tags = load_mod_tags()

                    # Savegame-Daten sammeln (Sims, Haushalte, Welten)
                    savegame_data = server_ref._savegame_cache if server_ref._savegame_cache else None

                    # Tray / CC-Daten sammeln
                    tray_data = server_ref._tray_cache if server_ref._tray_cache else None

                    # Build HTML report
                    report_html = _build_bug_report_html(
                        cat_label, symptom_text, desc_text, sys_info, game_ver, mod_folders, mod_type_stats,
                        severity, verdict, hints, broken_mods, error_messages,
                        all_exc_files_data, all_ui_exc_files_data, all_other_exc_files_data, scanner_log_full,
                        ds, d_full, s, dupe_count, corrupt_count, conflict_count,
                        has_corrupt, has_dupes, has_conflicts,
                        user_creators=user_creators, user_notes=user_notes, user_tags=user_tags,
                        savegame_data=savegame_data, tray_data=tray_data,
                        mod_logs_data=mod_logs_data,
                    )
                    report_bytes = report_html.encode('utf-8')

                    # Discord embeds
                    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Mod-Zusammenfassung fuer Discord
                    mod_summary_lines = []
                    outdated_list = d_full.get('outdated', []) if d_full else []
                    outdated_high = [o for o in outdated_list if o.get('risk') == 'hoch']
                    if outdated_high:
                        mod_summary_lines.append(f"⚠️ {len(outdated_high)} Script-Mods veraltet (hohes Risiko)")
                    if outdated_list:
                        mod_summary_lines.append(f"📅 {len(outdated_list)} Mods aelter als letzter Patch")
                    cat_counts_list = d_full.get('stats', {}).get('category_counts', []) if d_full else []
                    if cat_counts_list:
                        top_cats = ', '.join(f"{n}: {c}" for n, c in cat_counts_list[:5])
                        mod_summary_lines.append(f"📊 {top_cats}")
                    deps_list = d_full.get('dependencies', []) if d_full else []
                    if deps_list:
                        mod_summary_lines.append(f"🔗 {len(deps_list)} Abhaengigkeiten erkannt")
                    if user_notes:
                        mod_summary_lines.append(f"📝 {len(user_notes)} Mod-Notizen vom User")
                    mod_summary_text = '\n'.join(mod_summary_lines) if mod_summary_lines else 'Keine erweiterten Daten'

                    # Sims-Zusammenfassung fuer Discord
                    sims_summary_text = 'Keine Spielstand-Analyse'
                    if savegame_data:
                        sg_sims = savegame_data.get('sims', [])
                        sg_hh = savegame_data.get('households', {})
                        sg_worlds = savegame_data.get('worlds', [])
                        sg_dupes = savegame_data.get('duplicate_sims', [])
                        sg_save = savegame_data.get('active_save', '?')
                        sg_lines = [f"Save: {sg_save}"]
                        sg_lines.append(f"Sims: {len(sg_sims)} | Haushalte: {len(sg_hh)} | Welten: {len(sg_worlds)}")
                        if sg_dupes:
                            sg_lines.append(f"⚠️ {len(sg_dupes)} doppelte Sim-Namen!")
                        age_stats = savegame_data.get('age_stats', {})
                        if age_stats:
                            sg_lines.append('Alter: ' + ', '.join(f"{k}: {v}" for k, v in sorted(age_stats.items(), key=lambda x: -x[1])))
                        sims_summary_text = '\n'.join(sg_lines)

                    # CC-Zusammenfassung fuer Discord
                    cc_summary_text = 'Keine CC-Analyse'
                    if tray_data:
                        t_sum = tray_data.get('summary', {})
                        cc_items = t_sum.get('items_with_cc', 0)
                        cc_total_mods = t_sum.get('total_mods_used', 0)
                        cc_max = t_sum.get('max_cc_item', '')
                        cc_max_cnt = t_sum.get('max_cc_count', 0)
                        cc_lines = [f"Items mit CC: {cc_items} | CC-Mods genutzt: {cc_total_mods}"]
                        if cc_max:
                            cc_lines.append(f"Meiste CC: {cc_max} ({cc_max_cnt} Teile)")
                        cc_summary_text = '\n'.join(cc_lines)

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
                            {"name": "🗂️ Mod-Analyse", "value": mod_summary_text[:1024], "inline": False},
                            {"name": "👥 Spielstand (Sims)", "value": sims_summary_text[:1024], "inline": False},
                            {"name": "🎨 CC-Analyse", "value": cc_summary_text[:1024], "inline": False},
                        ],
                        "footer": {"text": f"Scanner v{SCANNER_VERSION} | {report_time} | 📎 Details in .html Anhang"},
                    }
                    embed2 = {
                        "title": "🤖 Auto-Analyse",
                        "color": 0x4488FF if severity.startswith("🟢") else (0xFFAA00 if severity.startswith("🟡") else 0xFF0000),
                        "fields": [
                            {"name": "📊 Schweregrad", "value": severity, "inline": True},
                            {"name": "🏷️ Kategorie", "value": cat_label, "inline": True},
                            {"name": "🎯 Urteil", "value": verdict, "inline": False},
                            {"name": "📋 Hinweise", "value": hints_text[:1024], "inline": False},
                        ],
                    }
                    if broken_mods:
                        embed2["fields"].append({"name": "🔥 Verdächtige Mods", "value": ', '.join(broken_mods[:5])[:1024], "inline": False})
                    if error_messages:
                        err_preview = '\n'.join(f"• {e[:150]}" for e in error_messages[:3])
                        embed2["fields"].append({"name": "💬 Fehlermeldungen", "value": err_preview[:1024], "inline": False})

                    boundary = f"----BugReport{_uuid.uuid4().hex}"
                    body_parts: list[str] = []
                    webhook_payload = {"embeds": [embed1, embed2], "username": "Sims4 Scanner Bug Bot"}
                    body_parts.append(f'--{boundary}\r\n')
                    body_parts.append('Content-Disposition: form-data; name="payload_json"\r\n')
                    body_parts.append('Content-Type: application/json\r\n\r\n')
                    body_parts.append(json.dumps(webhook_payload))
                    body_parts.append('\r\n')

                    report_filename = f"bugreport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    body_parts.append(f'--{boundary}\r\n')
                    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{report_filename}"\r\n')
                    body_parts.append('Content-Type: text/html; charset=utf-8\r\n\r\n')

                    body_bytes = ''.join(body_parts).encode('utf-8') + report_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

                    req = _urlreq.Request(
                        DISCORD_WEBHOOK_URL, data=body_bytes,
                        headers={'Content-Type': f'multipart/form-data; boundary={boundary}', 'User-Agent': 'Sims4Scanner'},
                        method='POST',
                    )
                    _urlreq.urlopen(req, timeout=15)
                    self._json(200, {"ok": True})
                    print(f"[BUG_REPORT] Sent to Discord with .html — {cat_label} ({len(report_bytes)} bytes)", flush=True)
                    append_log(f"BUG_REPORT sent ({category}, {len(report_bytes)} bytes)")
                except Exception as ex:
                    print(f"[BUG_REPORT] Error: {ex}", flush=True)
                    self._json(500, {"ok": False, "error": str(ex)})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self._start_watcher()
        self._auto_tray_scan()

    def _auto_tray_scan(self):
        """Starte Tray-Analyse automatisch im Hintergrund beim Server-Start."""
        # Falls bereits vom Scan vorgeladen, überspringen
        if self._tray_cache:
            print("[TRAY] Daten aus Scan übernommen, Auto-Analyse übersprungen.", flush=True)
            return
        def _run():
            try:
                sims4 = self.sims4_dir
                tray_path = os.path.join(sims4, "Tray") if sims4 else ""
                if not tray_path or not os.path.isdir(tray_path):
                    return
                roots = [Path(r) for r in self.dataset.roots] if hasattr(self.dataset, 'roots') else []
                if not roots:
                    return
                self._tray_analyzing = True
                print("[TRAY] Auto-Analyse gestartet\u2026", flush=True)
                mod_idx = build_mod_instance_index(roots)
                result = analyze_tray(tray_path, mod_idx)
                self._tray_cache = result
                s = result.get('summary', {})
                print(f"[TRAY] Fertig: {s.get('total_items', 0)} Items, {s.get('items_with_cc', 0)} mit CC, {s.get('total_mods_used', 0)} Mods genutzt", flush=True)
            except Exception as ex:
                print(f"[TRAY] Auto-Analyse Fehler: {ex}", flush=True)
            finally:
                self._tray_analyzing = False
        threading.Thread(target=_run, daemon=True).start()

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


def _build_bug_report_html(
    cat_label, symptom_text, desc_text, sys_info, game_ver, mod_folders, mod_type_stats,
    severity, verdict, hints, broken_mods, error_messages,
    all_exc_files_data, all_ui_exc_files_data, all_other_exc_files_data, scanner_log_full,
    ds, d_full, s, dupe_count, corrupt_count, conflict_count,
    has_corrupt, has_dupes, has_conflicts,
    *, user_creators=None, user_notes=None, user_tags=None,
    savegame_data=None, tray_data=None, mod_logs_data=None,
) -> str:
    """Builds the full HTML bug report page with enriched mod list."""
    user_creators = user_creators or {}
    user_notes = user_notes or {}
    user_tags = user_tags or {}
    mod_logs_data = mod_logs_data or []
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _h(text):
        return _html.escape(str(text))

    sev_color = '#4caf50' if severity.startswith('🟢') else ('#ff9800' if severity.startswith('🟡') else '#f44336')
    sev_bg = '#e8f5e9' if severity.startswith('🟢') else ('#fff3e0' if severity.startswith('🟡') else '#ffebee')

    parts: list[str] = []
    parts.append(f'''<!DOCTYPE html>
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
.badge{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:0.75em;font-weight:600;margin:0 2px;vertical-align:middle}}
.badge-corrupt{{background:#f4433622;color:#f44336;border:1px solid #f4433655}}
.badge-dupe{{background:#ff980022;color:#ff9800;border:1px solid #ff980055}}
.badge-conflict{{background:#e91e6322;color:#e91e63;border:1px solid #e91e6355}}
.badge-outdated{{background:#9c27b022;color:#ce93d8;border:1px solid #9c27b055}}
.badge-script{{background:#2196f322;color:#64b5f6;border:1px solid #2196f355}}
.badge-ok{{background:#4caf5022;color:#81c784;border:1px solid #4caf5055}}
.badge-dep{{background:#00bcd422;color:#4dd0e1;border:1px solid #00bcd455}}
.mod-note{{color:#ffab40;font-style:italic;font-size:0.85em;margin-left:8px}}
.mod-creator{{color:#ce93d8;font-size:0.85em}}
.mod-category{{color:#81c784;font-size:0.85em}}
.mod-tags span{{display:inline-block;background:#37474f;color:#b0bec5;padding:1px 6px;border-radius:8px;font-size:0.72em;margin:0 2px}}
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

    # Übersicht
    parts.append(f'''
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

    # Auto-Analyse
    hints_html = ''.join(f'<div class="hint">{_h(h)}</div>' for h in hints)
    mods_html = ''.join(f'<span class="mod-tag">{_h(m)}</span>' for m in broken_mods) if broken_mods else '<span style="color:#888">Keine erkannt</span>'
    errors_html = ''.join(f'<div class="error-msg">{_h(e)}</div>' for e in error_messages) if error_messages else '<span style="color:#888">Keine</span>'
    verdict_clean = verdict.replace('**', '')
    parts.append(f'''
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

    # Korrupte Dateien
    if has_corrupt and ds:
        corrupts = d_full.get('corrupt', [])
        corrupt_rows = ''.join(f'<tr class="corrupt-row"><td>{_h(c.get("path","?"))}</td><td>{_h(c.get("error","?"))}</td></tr>' for c in corrupts)
        parts.append(f'''
<div><h2 onclick="toggle(this)">⛔ Korrupte Dateien ({corrupt_count})</h2>
<div class="section"><table><tr><th>Datei</th><th>Fehler</th></tr>{corrupt_rows}</table></div></div>
''')

    # Duplikate
    if has_dupes and ds:
        dup_html = ''
        for g in d_full.get('groups', []):
            files = g.get('files', [])
            if len(files) > 1:
                gtype = g.get('type', '').upper()
                rows = ''.join(f'<tr><td>{_h(fi.get("path","?"))}</td><td class="size-col">{_h(fi.get("size_hr","?"))}</td></tr>' for fi in files)
                dup_html += f'<h4 style="color:#61dafb;margin:10px 0 5px">{_h(gtype)} Gruppe</h4><table><tr><th>Datei</th><th>Größe</th></tr>{rows}</table>'
        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📦 Duplikate ({dupe_count} Gruppen)</h2>
<div class="section">{dup_html}</div></div>
''')

    # Mod-Konflikte
    if has_conflicts and ds:
        conflicts = d_full.get('conflicts', [])
        conf_html = ''
        for c_item in conflicts:
            c_files = c_item.get('files', [])
            res_name = c_item.get('resource', '?')
            rows = ''.join(f'<tr><td>{_h(cf.get("path","?"))}</td></tr>' for cf in c_files)
            conf_html += f'<h4 style="color:#ff9800;margin:10px 0 5px">Ressource: {_h(res_name)}</h4><table><tr><th>Datei</th></tr>{rows}</table>'
        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">⚡ Mod-Konflikte ({conflict_count})</h2>
<div class="section">{conf_html}</div></div>
''')

    # Exceptions
    for i, (fname, fcontent) in enumerate(all_exc_files_data):
        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">⚠️ lastException #{i+1}: {_h(fname)}</h2>
<div class="section"><pre>{_h(fcontent)}</pre></div></div>
''')
    for i, (fname, fcontent) in enumerate(all_ui_exc_files_data):
        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">🖥️ lastUIException #{i+1}: {_h(fname)}</h2>
<div class="section"><pre>{_h(fcontent)}</pre></div></div>
''')
    for i, (fname, fcontent) in enumerate(all_other_exc_files_data):
        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📄 Mod-Exception #{i+1}: {_h(fname)}</h2>
<div class="section"><pre>{_h(fcontent)}</pre></div></div>
''')

    # ── Spielstand-Analyse (Sims) ──
    if savegame_data:
        sg_sims = savegame_data.get('sims', [])
        sg_hh = savegame_data.get('households', {})
        sg_worlds = savegame_data.get('worlds', [])
        sg_dupes = savegame_data.get('duplicate_sims', [])
        sg_active = savegame_data.get('active_save', '?')
        sg_age = savegame_data.get('age_stats', {})
        sg_gender = savegame_data.get('gender_stats', {})
        sg_species = savegame_data.get('species_stats', {})
        sg_skin = savegame_data.get('skin_stats', {})
        sg_partner = savegame_data.get('partner_count', 0)
        sg_save_size = savegame_data.get('active_save_size_mb', '?')

        # Statistik-Karten
        sg_stats = f'''<div class="stats-bar">
<div class="stat-card"><div class="stat-num">{len(sg_sims)}</div><div class="stat-label">Sims</div></div>
<div class="stat-card"><div class="stat-num">{len(sg_hh)}</div><div class="stat-label">Haushalte</div></div>
<div class="stat-card"><div class="stat-num">{len(sg_worlds)}</div><div class="stat-label">Welten</div></div>
<div class="stat-card"><div class="stat-num">{sg_partner}</div><div class="stat-label">Partner</div></div>
<div class="stat-card"><div class="stat-num">{sg_save_size} MB</div><div class="stat-label">Save-Größe</div></div>
</div>'''

        # Demografie
        demo_parts = []
        if sg_age:
            demo_parts.append('<b>Alter:</b> ' + ', '.join(f'{_h(k)}: {v}' for k, v in sorted(sg_age.items(), key=lambda x: -x[1])))
        if sg_gender:
            demo_parts.append('<b>Geschlecht:</b> ' + ', '.join(f'{_h(k)}: {v}' for k, v in sorted(sg_gender.items(), key=lambda x: -x[1])))
        if sg_species:
            demo_parts.append('<b>Spezies:</b> ' + ', '.join(f'{_h(k)}: {v}' for k, v in sorted(sg_species.items(), key=lambda x: -x[1])))
        if sg_skin:
            top_skin = sorted(sg_skin.items(), key=lambda x: -x[1])[:5]
            demo_parts.append('<b>Hautfarbe:</b> ' + ', '.join(f'{_h(k)}: {v}' for k, v in top_skin))
        demo_html = '<br>'.join(demo_parts) if demo_parts else ''

        # Doppelte Sims
        dupe_sims_html = ''
        if sg_dupes:
            dupe_sims_html = '<h3 style="color:#ff6b6b;margin:15px 0 8px">⚠️ Doppelte Sim-Namen</h3>'
            dupe_sims_html += '<table><tr><th>Name</th><th>Anzahl</th><th>In Haushalten</th></tr>'
            for d in sg_dupes:
                dupe_sims_html += f'<tr><td>{_h(d.get("name", "?"))}</td><td>{d.get("count", 0)}</td><td>{_h(", ".join(d.get("households", [])))}</td></tr>'
            dupe_sims_html += '</table>'

        # Sim-Liste (vollständig mit allen Details)
        sim_table_html = ''
        if sg_sims:
            sim_table_html = '<h3 style="color:#61dafb;margin:15px 0 8px">📋 Sim-Liste</h3>'
            sim_table_html += '<div class="mod-list"><table><tr><th>Name</th><th>Haushalt</th><th>Welt</th><th>Alter</th><th>Geschl.</th><th>Spezies</th><th>Partner</th><th>Traits</th><th>Skills</th><th>Bez.</th><th>Stimmung</th><th>Tage</th><th>Gespielt</th></tr>'
            for sim in sorted(sg_sims, key=lambda x: (x.get('household', ''), x.get('full_name', ''))):
                played_icon = '✅' if sim.get('is_played') else '—'
                mood = sim.get('mood_emoji', '') + ' ' + sim.get('mood_label', '') if sim.get('mood_label') else '—'
                partner = sim.get('partner', '') or '—'
                age_days = sim.get('sim_age_days', 0)
                age_days_str = f'{age_days}d' if age_days else '—'
                sim_table_html += f'<tr><td>{_h(sim.get("full_name", "?"))}</td><td>{_h(sim.get("household", "?"))}</td><td>{_h(sim.get("world", "") or "—")}</td><td>{_h(sim.get("age", "?"))}</td><td>{_h(sim.get("gender", "?"))}</td><td>{_h(sim.get("species", "") or "—")}</td><td>{_h(partner)}</td><td>{sim.get("trait_count", 0)}</td><td>{sim.get("skill_count", 0)}</td><td>{sim.get("relationship_count", 0)}</td><td>{_h(mood)}</td><td>{_h(age_days_str)}</td><td>{played_icon}</td></tr>'
            sim_table_html += '</table></div>'

        # Welten-Übersicht (worlds ist eine Liste von Strings, Sims zählen wir selbst)
        worlds_html = ''
        if sg_worlds:
            # Sim-Count pro Welt aus der Sim-Liste berechnen
            world_sim_counts: dict[str, int] = {}
            world_hh_sets: dict[str, set] = {}
            for sim in sg_sims:
                sw = sim.get('world', '')
                if sw:
                    world_sim_counts[sw] = world_sim_counts.get(sw, 0) + 1
                    if sw not in world_hh_sets:
                        world_hh_sets[sw] = set()
                    world_hh_sets[sw].add(sim.get('household', ''))
            worlds_html = '<h3 style="color:#81c784;margin:15px 0 8px">🌍 Welten</h3>'
            worlds_html += '<table><tr><th>Welt</th><th>Sims</th><th>Haushalte</th></tr>'
            for w_name in sorted(sg_worlds, key=lambda x: -world_sim_counts.get(x, 0)):
                worlds_html += f'<tr><td>{_h(w_name)}</td><td>{world_sim_counts.get(w_name, 0)}</td><td>{len(world_hh_sets.get(w_name, set()))}</td></tr>'
            worlds_html += '</table>'

        # Verfügbare Spielstände
        saves_html = ''
        sg_saves = savegame_data.get('available_saves', [])
        if sg_saves:
            saves_html = '<h3 style="color:#64b5f6;margin:15px 0 8px">💾 Verfügbare Spielstände</h3>'
            saves_html += '<table><tr><th>Datei</th><th>Größe</th><th>Datum</th></tr>'
            for sv in sg_saves:
                saves_html += f'<tr><td>{_h(sv.get("file", "?"))}</td><td class="size-col">{sv.get("size_mb", "?")} MB</td><td>{_h(sv.get("date", "?"))}</td></tr>'
            saves_html += '</table>'

        # Enrichment-Daten
        enrichment_html = ''

        # Basegame-Sims (vorinstallierte Sims die im Save sind)
        bg_names = savegame_data.get('basegame_names', [])
        if bg_names:
            enrichment_html += '<h3 style="color:#ffab40;margin:15px 0 8px">🏠 Basegame-Sims im Spielstand</h3>'
            enrichment_html += f'<p style="color:#aaa">{len(bg_names)} vorinstallierte Sims erkannt:</p>'
            enrichment_html += '<p style="color:#ccc">' + ', '.join(_h(n) for n in sorted(bg_names)) + '</p>'

        # Townies (NPC-Sims die das Spiel generiert hat)
        townie_names = savegame_data.get('townie_names', [])
        if townie_names:
            enrichment_html += '<h3 style="color:#ce93d8;margin:15px 0 8px">👤 Erkannte Townies / NPCs</h3>'
            enrichment_html += f'<p style="color:#aaa">{len(townie_names)} Townies erkannt:</p>'
            enrichment_html += '<p style="color:#ccc">' + ', '.join(_h(n) for n in sorted(townie_names)) + '</p>'

        # Portrait-Namen (Sims mit Portrait-Bildern im Tray)
        portrait_names = savegame_data.get('portrait_names', [])
        if portrait_names:
            enrichment_html += '<h3 style="color:#64b5f6;margin:15px 0 8px">🖼️ Sims mit Portrait im Tray</h3>'
            enrichment_html += f'<p style="color:#aaa">{len(portrait_names)} Portraits gefunden:</p>'
            enrichment_html += '<p style="color:#ccc">' + ', '.join(_h(n) for n in sorted(portrait_names)) + '</p>'

        # Bibliothek-Sims
        library_names = savegame_data.get('library_sim_names', [])
        if library_names:
            enrichment_html += '<h3 style="color:#81c784;margin:15px 0 8px">📚 Sims in der Bibliothek</h3>'
            enrichment_html += f'<p style="color:#aaa">{len(library_names)} Bibliothek-Sims:</p>'
            enrichment_html += '<p style="color:#ccc">' + ', '.join(_h(n) for n in sorted(library_names)) + '</p>'

        parts.append(f'''
<div><h2 onclick="toggle(this)">👥 Spielstand-Analyse ({len(sg_sims)} Sims, Save: {_h(sg_active)})</h2>
<div class="section">
{sg_stats}
<div style="margin:10px 0;padding:10px;background:#1e1e3a;border-radius:8px">{demo_html}</div>
{dupe_sims_html}
{worlds_html}
{saves_html}
{enrichment_html}
{sim_table_html}
</div></div>
''')

    # ── CC-Analyse (Tray) ──
    if tray_data:
        t_items = tray_data.get('items', [])
        t_sum = tray_data.get('summary', {})
        t_usage = tray_data.get('mod_usage', {})

        cc_stats = f'''<div class="stats-bar">
<div class="stat-card"><div class="stat-num">{t_sum.get('total_items', 0)}</div><div class="stat-label">Tray-Items</div></div>
<div class="stat-card"><div class="stat-num">{t_sum.get('households', 0)}</div><div class="stat-label">Haushalte</div></div>
<div class="stat-card"><div class="stat-num">{t_sum.get('items_with_cc', 0)}</div><div class="stat-label">Mit CC</div></div>
<div class="stat-card"><div class="stat-num">{t_sum.get('total_mods_used', 0)}</div><div class="stat-label">CC-Mods</div></div>
</div>'''

        # CC pro Haushalt (nur die mit CC)
        cc_items = [i for i in t_items if i.get('cc_count', 0) > 0]
        cc_items.sort(key=lambda x: -x.get('cc_count', 0))
        cc_table_html = ''
        if cc_items:
            cc_table_html = '<h3 style="color:#ce93d8;margin:15px 0 8px">🎨 Items mit CC</h3>'
            cc_table_html += '<table><tr><th>Name</th><th>Typ</th><th>CC-Teile</th><th>Verwendete Mods</th></tr>'
            type_labels = {0: 'Lot', 1: 'Haushalt', 2: 'Raum', 3: 'Sim'}
            for ci in cc_items:
                ci_name = ci.get('name', '?')
                ci_type = type_labels.get(ci.get('type', -1), '?')
                ci_cc = ci.get('cc_count', 0)
                ci_mods = ci.get('used_mods', [])
                mod_names = ', '.join(m.get('name', '?') for m in ci_mods[:8])
                if len(ci_mods) > 8:
                    mod_names += f' (+{len(ci_mods) - 8})'
                cc_table_html += f'<tr><td>{_h(ci_name)}</td><td>{_h(ci_type)}</td><td>{ci_cc}</td><td style="font-size:0.85em;color:#aaa">{_h(mod_names)}</td></tr>'
            cc_table_html += '</table>'

        # Meistgenutzte CC-Mods
        top_mods_html = ''
        if t_usage:
            sorted_mods = sorted(t_usage.items(), key=lambda x: -(x[1].get('used_count', 0) if isinstance(x[1], dict) else 0))[:30]
            if sorted_mods:
                top_mods_html = '<h3 style="color:#64b5f6;margin:15px 0 8px">📊 Meistgenutzte CC-Mods</h3>'
                top_mods_html += '<table><tr><th>Mod</th><th>Verwendet in</th></tr>'
                for mod_path, usage_info in sorted_mods:
                    mod_name = usage_info.get('name', Path(mod_path).name) if isinstance(usage_info, dict) else str(mod_path)
                    cnt = usage_info.get('used_count', 0) if isinstance(usage_info, dict) else 0
                    top_mods_html += f'<tr><td>{_h(mod_name)}</td><td>{cnt}x</td></tr>'
                top_mods_html += '</table>'

        # CC pro Haushalt im Savegame
        cc_by_hh_html = ''
        if savegame_data:
            cc_hh = savegame_data.get('cc_by_household', {})
            if cc_hh:
                cc_by_hh_html = '<h3 style="color:#ffab40;margin:15px 0 8px">🏠 CC pro Haushalt (Spielstand)</h3>'
                cc_by_hh_html += '<table><tr><th>Haushalt</th><th>CC-Mods</th></tr>'
                for hh_name, mods in sorted(cc_hh.items(), key=lambda x: -len(x[1])):
                    mod_list = ', '.join(m.get('name', '?') for m in mods[:10])
                    if len(mods) > 10:
                        mod_list += f' (+{len(mods) - 10})'
                    cc_by_hh_html += f'<tr><td>{_h(hh_name)}</td><td style="font-size:0.85em;color:#aaa">{_h(mod_list)} ({len(mods)} Teile)</td></tr>'
                cc_by_hh_html += '</table>'

        parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">🎨 CC-Analyse ({t_sum.get('items_with_cc', 0)} Items mit CC)</h2>
<div class="section">
{cc_stats}
{cc_table_html}
{top_mods_html}
{cc_by_hh_html}
</div></div>
''')

    # Mod-Logs
    if mod_logs_data:
        for ml_name, ml_content in mod_logs_data:
            parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📝 Mod-Log: {_h(ml_name)}</h2>
<div class="section"><pre>{_h(ml_content)}</pre></div></div>
''')

    # --- Intelligente Mod-Liste mit Hinweisen ---
    # Lookup-Maps fuer schnellen Zugriff
    corrupt_paths = set()
    if d_full:
        for c_item in d_full.get('corrupt', []):
            corrupt_paths.add(c_item.get('path', ''))

    dupe_paths: dict[str, str] = {}  # path -> group type
    if d_full:
        for g in d_full.get('groups', []):
            gtype = g.get('type', '')
            for f in g.get('files', []):
                dupe_paths[f.get('path', '')] = gtype

    conflict_paths: set[str] = set()
    if d_full:
        for conf in d_full.get('conflicts', []):
            for f in conf.get('files', []):
                conflict_paths.add(f.get('path', ''))

    outdated_map: dict[str, dict] = {}
    if d_full:
        for o in d_full.get('outdated', []):
            outdated_map[o.get('path', '')] = o

    dep_file_set: set[str] = set()  # Dateien die in einer Abhängigkeit stehen
    if d_full:
        for dep in d_full.get('dependencies', []):
            for f_path in dep.get('files', []):
                dep_file_set.add(f_path)

    # all_files aus dem Dataset nutzen (mit deep-Analyse)
    all_files_data = d_full.get('all_files', []) if d_full else []
    # Falls leer, Fallback auf rglob
    use_enriched = len(all_files_data) > 0

    mod_list_html = ''
    total_mod_count = 0
    problem_mod_count = 0
    outdated_high_count = 0
    category_summary: dict[str, int] = {}

    if use_enriched and all_files_data:
        # Gruppiere nach root
        by_root: dict[str, list[dict]] = {}
        for f in all_files_data:
            ri = f.get('root_index')
            key = f"Ordner {ri}" if ri else "Unbekannt"
            by_root.setdefault(key, []).append(f)

        for root_label, files in sorted(by_root.items()):
            mod_list_html += f'<h4 style="color:#61dafb;margin:10px 0 5px">\U0001f4c2 {_h(root_label)}</h4>'
            mod_list_html += '<table><tr><th>Datei</th><th>Kategorie</th><th>Hinweise</th><th style="text-align:right">Gr\u00f6\u00dfe</th></tr>'
            for f in sorted(files, key=lambda x: str(x.get('rel', '')).lower()):
                total_mod_count += 1
                fp = f.get('path', '')
                rel = f.get('rel', '') or fp
                size_h = f.get('size_h', '?')

                # Deep-Analyse Kategorie
                deep = f.get('deep', {}) or {}
                cat = deep.get('category', '') if isinstance(deep, dict) else ''
                if cat:
                    category_summary[cat] = category_summary.get(cat, 0) + 1
                cat_html = f'<span class="mod-category">{_h(cat)}</span>' if cat else '<span style="color:#555">—</span>'

                # Badges / Hinweise sammeln
                badges = []
                has_problem = False
                if fp in corrupt_paths:
                    badges.append('<span class="badge badge-corrupt">\u26d4 Korrupt</span>')
                    has_problem = True
                if fp in dupe_paths:
                    dtype = dupe_paths[fp]
                    badges.append(f'<span class="badge badge-dupe">\U0001f4e6 Duplikat ({_h(dtype)})</span>')
                    has_problem = True
                if fp in conflict_paths:
                    badges.append('<span class="badge badge-conflict">\u26a1 Konflikt</span>')
                    has_problem = True
                if fp in outdated_map:
                    o = outdated_map[fp]
                    risk = o.get('risk', '')
                    days = o.get('days_before_patch', 0)
                    risk_lbl = {'hoch': '\U0001f534', 'mittel': '\U0001f7e1', 'niedrig': '\U0001f7e2'}.get(risk, '\u2754')
                    reason = o.get('risk_reason', '')
                    badges.append(f'<span class="badge badge-outdated">{risk_lbl} Veraltet ({days}d) — {_h(reason)}</span>')
                    if risk == 'hoch':
                        outdated_high_count += 1
                        has_problem = True
                if fp in dep_file_set:
                    badges.append('<span class="badge badge-dep">\U0001f517 Hat Abhängigkeit</span>')
                if fp.lower().endswith('.ts4script'):
                    badges.append('<span class="badge badge-script">\U0001f4dc Script</span>')

                # User-Daten: Creator, Notes, Tags
                extras = []
                if fp in user_creators or rel in user_creators:
                    creator = user_creators.get(fp, user_creators.get(rel, ''))
                    if creator:
                        extras.append(f'<span class="mod-creator">\U0001f464 {_h(creator)}</span>')
                if fp in user_notes or rel in user_notes:
                    note = user_notes.get(fp, user_notes.get(rel, ''))
                    if note:
                        extras.append(f'<span class="mod-note">\U0001f4dd {_h(note[:150])}</span>')
                if fp in user_tags or rel in user_tags:
                    file_tags = user_tags.get(fp, user_tags.get(rel, []))
                    if file_tags:
                        tag_html = ''.join(f'<span>{_h(t)}</span>' for t in file_tags)
                        extras.append(f'<span class="mod-tags">\U0001f3f7\ufe0f {tag_html}</span>')

                if has_problem:
                    problem_mod_count += 1

                badges_html = ' '.join(badges) if badges else '<span class="badge badge-ok">\u2705</span>'
                extras_html = '<br>'.join(extras) if extras else ''
                hints_cell = badges_html + (('<br>' + extras_html) if extras_html else '')

                row_style = ' style="background:#2d1b1b"' if has_problem else ''
                mod_list_html += f'<tr{row_style}><td>{_h(rel)}</td><td>{cat_html}</td><td>{hints_cell}</td><td class="size-col">{_h(size_h)}</td></tr>'

            mod_list_html += '</table>'
    elif ds and ds.roots:
        # Fallback: einfaches Listing ohne Analyse
        for root in ds.roots:
            root_path = Path(root)
            mod_list_html += f'<h4 style="color:#61dafb;margin:10px 0 5px">\U0001f4c2 {_h(str(root_path))}</h4>'
            if root_path.exists():
                mod_list_html += '<table><tr><th>Datei</th><th style="text-align:right">Gr\u00f6\u00dfe</th></tr>'
                for mf in sorted(root_path.rglob('*')):
                    if mf.is_file():
                        total_mod_count += 1
                        try:
                            rel = mf.relative_to(root_path)
                            size = mf.stat().st_size
                            size_str = f"{size / 1048576:.1f} MB" if size >= 1048576 else (f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B")
                            mod_list_html += f'<tr><td>{_h(str(rel))}</td><td class="size-col">{size_str}</td></tr>'
                        except Exception:
                            mod_list_html += f'<tr><td>{_h(mf.name)}</td><td class="size-col">?</td></tr>'
                mod_list_html += '</table>'

    # Mod-Zusammenfassung oben in der Liste
    summary_html = '<div class="stats-bar">'
    summary_html += f'<div class="stat-card"><div class="stat-num">{total_mod_count}</div><div class="stat-label">Mods gesamt</div></div>'
    summary_html += f'<div class="stat-card"><div class="stat-num" style="color:#f44336">{problem_mod_count}</div><div class="stat-label">Mit Problemen</div></div>'
    summary_html += f'<div class="stat-card"><div class="stat-num" style="color:#ce93d8">{outdated_high_count}</div><div class="stat-label">Veraltet (hoch)</div></div>'
    summary_html += f'<div class="stat-card"><div class="stat-num" style="color:#81c784">{len(category_summary)}</div><div class="stat-label">Kategorien</div></div>'
    summary_html += '</div>'

    # Kategorien-Uebersicht
    if category_summary:
        cat_sorted = sorted(category_summary.items(), key=lambda x: -x[1])
        cat_list_html = ' | '.join(f'{_h(n)}: {c}' for n, c in cat_sorted)
        summary_html += f'<p style="color:#888;margin:5px 0">\U0001f4ca {cat_list_html}</p>'

    # Outdated-Mods Zusammenfassung
    outdated_list = d_full.get('outdated', []) if d_full else []
    outdated_section_html = ''
    if outdated_list:
        outdated_section_html += '<h3 style="color:#ce93d8;margin:15px 0 8px">\u23f0 Veraltete Mods (vor letztem Patch)</h3>'
        outdated_section_html += '<table><tr><th>Datei</th><th>Risiko</th><th>Grund</th><th>Tage vor Patch</th></tr>'
        for o in outdated_list:
            risk = o.get('risk', '')
            risk_icon = {'hoch': '\U0001f534', 'mittel': '\U0001f7e1', 'niedrig': '\U0001f7e2'}.get(risk, '\u2754')
            risk_style = 'color:#f44336' if risk == 'hoch' else ('color:#ff9800' if risk == 'mittel' else 'color:#81c784')
            outdated_section_html += f'<tr><td>{_h(o.get("rel", o.get("path", "?")))}</td><td style="{risk_style}">{risk_icon} {_h(risk)}</td><td>{_h(o.get("risk_reason", ""))}</td><td class="size-col">{o.get("days_before_patch", "?")}</td></tr>'
        outdated_section_html += '</table>'

    # Abhaengigkeiten
    deps_section_html = ''
    deps_list = d_full.get('dependencies', []) if d_full else []
    if deps_list:
        deps_section_html += '<h3 style="color:#4dd0e1;margin:15px 0 8px">\U0001f517 Erkannte Abh\u00e4ngigkeiten</h3>'
        deps_section_html += '<table><tr><th>Typ</th><th>Beschreibung</th><th>Dateien</th></tr>'
        for dep in deps_list:
            dep_icon = dep.get('icon', '🔗')
            dep_label = dep.get('label', '?')
            dep_hint = dep.get('hint', '')
            dep_files = dep.get('files', [])
            dep_files_str = ', '.join(Path(f).name for f in dep_files[:5])
            if len(dep_files) > 5:
                dep_files_str += f' (+{len(dep_files) - 5})'
            deps_section_html += f'<tr><td>{_h(dep_icon)} {_h(dep_label)}</td><td style="font-size:0.85em;color:#aaa">{_h(dep_hint)}</td><td style="font-size:0.85em">{_h(dep_files_str)}</td></tr>'
        deps_section_html += '</table>'

    parts.append(f'''
<div><h2 onclick="toggle(this)">\U0001f4c1 Mod-Liste mit Analyse ({total_mod_count} Dateien, {problem_mod_count} Probleme)</h2>
<div class="section">
{summary_html}
{outdated_section_html}
{deps_section_html}
<h3 style="color:#61dafb;margin:15px 0 8px">\U0001f4cb Komplette Mod-Liste</h3>
<div class="mod-list">{mod_list_html}</div>
</div></div>
''')

    # Scanner-Log
    scanner_log_display = scanner_log_full if scanner_log_full else 'Keine Aktionen durchgeführt (Log wird bei Quarantäne/Lösch-Aktionen angelegt)'
    parts.append(f'''
<div class="collapsed"><h2 onclick="toggle(this)">📋 Scanner-Log</h2>
<div class="section"><pre>{_h(scanner_log_display)}</pre></div></div>
''')

    # Footer
    parts.append(f'''
<div class="footer">Scanner v{_h(SCANNER_VERSION)} | Report erstellt {_h(report_time)}</div>
</div></body></html>''')

    return ''.join(parts)
