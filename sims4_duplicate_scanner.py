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
import threading
import hashlib
import time
import json
import shutil
import secrets
import socket
import webbrowser
import zipfile
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB

# ---- Persistente Einstellungen (Ordner/Optionen merken) ----
def _default_config_path() -> Path:
    # Windows: %APPDATA%\Sims4DupeScanner\config.json
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / "sims4_duplicate_scanner_config.json"
    return Path.home() / ".sims4_duplicate_scanner_config.json"


CONFIG_PATH = _default_config_path()


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
    ps = str(path).lower()
    best_i = None
    best_len = -1
    for i, r in enumerate(roots):
        rs = str(r).lower()
        if ps.startswith(rs) and len(rs) > best_len:
            best_i = i
            best_len = len(rs)
    return best_i


def is_under_any_root(path: Path, roots: list[Path]) -> bool:
    """Security: allow actions only inside chosen roots."""
    try:
        rp = path.resolve()
    except Exception:
        return False

    for r in roots:
        try:
            rr = r.resolve()
        except Exception:
            continue

        try:
            if rp.is_relative_to(rr):  # py3.9+
                return True
        except Exception:
            ps = str(rp).lower()
            rs = str(rr).lower().rstrip("\\/")
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


def scan_duplicates(
    roots: list[Path],
    exts: set[str],
    ignore_dirs: set[str],
    do_name: bool,
    do_content: bool,
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
                    if dir_path.is_symlink():
                        continue
                    # Also check if it's a junction (Windows)
                    if dir_path.is_dir() and os.path.islink(str(dir_path)):
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

    return files, name_dupes, content_dupes


class Dataset:
    def __init__(self, roots: list[Path]):
        self.roots = roots
        self.groups = []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    def build_from_scan(self, name_dupes: dict[str, list[Path]], content_dupes: dict[str, list[Path]]):
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

        def score(g):
            count = len(g["files"])
            size_each = g["size_each"] or 0
            return (count, count * size_each)

        groups.sort(key=score, reverse=True)
        self.groups = groups

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

        return {
            "created_at": self.created_at,
            "roots": [{"label": f"Ordner {i+1}", "path": str(r)} for i, r in enumerate(self.roots)],
            "summary": {
                "groups_name": sum(1 for g in self.groups if g["type"] == "name"),
                "groups_content": sum(1 for g in self.groups if g["type"] == "content"),
                "entries_total": sum(len(g["files"]) for g in self.groups),
                "wasted_bytes_est": wasted,
                "wasted_h": human_size(wasted),
            },
            "groups": self.groups,
        }


class LocalServer:
    def __init__(self, dataset: Dataset, quarantine_dir: Path):
        self.dataset = dataset
        self.quarantine_dir = quarantine_dir
        self.token = secrets.token_urlsafe(24)
        self.port = None
        self.httpd = None
        self.log_file = self.quarantine_dir / "_sims4_actions.log.txt"

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
                    self._json(200, {"ok": True, "data": dataset.to_json()})
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

                if not is_under_any_root(p, dataset.roots):
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
                            dataset.remove_file(str(p))
                            self._json(200, {"ok": True, "moved": False, "note": "file missing (removed from list)"})
                            print(f"[QUARANTINE][MISSING] {p}", flush=True)
                            self._log_action("QUARANTINE", str(p), None, "MISSING", "file missing")
                            return

                        size, _ = safe_stat(p)
                        idx = best_root_index(p, dataset.roots)
                        label = f"Ordner{idx+1}" if idx is not None else "Unbekannt"

                        if idx is not None:
                            rel = p.resolve().relative_to(dataset.roots[idx].resolve())
                            dest = quarantine_dir / label / rel
                        else:
                            dest = quarantine_dir / label / p.name

                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest = ensure_unique_path(dest)

                        shutil.move(str(p), str(dest))
                        dataset.remove_file(str(p))
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
                            dataset.remove_file(str(p))
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
                        dataset.remove_file(str(p))
                        self._json(200, {"ok": True, "deleted": True, "path": str(p)})
                        print(f"[DELETE] OK: {p}", flush=True)
                        self._log_action("DELETE", str(p), size, "OK", "")
                    except Exception as ex:
                        self._json(500, {"ok": False, "error": str(ex)})
                        print(f"[DELETE][ERR] {p} :: {ex}", flush=True)
                        self._log_action("DELETE", str(p), None, "ERROR", str(ex))
                    return

                self._json(404, {"ok": False, "error": "unknown action"})
                print(f"[UNKNOWN_ACTION] {action} -> {p}", flush=True)
                append_log(f"UNKNOWN_ACTION {action} {p}")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
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
  details.grp { background:#141a28; border:1px solid #232a3a; border-radius:14px; padding:10px 12px; margin:10px 0; }
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
  #batchbar { position:sticky; top:10px; z-index:5; }
  .selbox { transform: scale(1.15); margin-right:8px; }
  .busy { opacity:0.65; pointer-events:none; }
</style>
</head>
<body>
<h1>Sims4 Duplicate Scanner</h1>
<p class="muted">Batch-Löschen/Quarantäne (Checkboxen). 1x bestätigen statt 100x klicken.</p>

<div class="box notice">
  <b>Safety:</b> Nutze am besten <b>📦 Quarantäne</b>. <b>🗑 Löschen</b> ist endgültig.
</div>

<div id="last" class="muted">Letzte Aktion: –</div>

<div class="box" id="batchbar">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>Batch</b> <span class="pill" id="selcount">0 ausgewählt</span><br>
      <span class="muted small">Log-Datei am PC: <code id="logfile"></code></span>
    </div>
    <div class="flex">
      <button class="btn btn-ok" id="btn_q_sel">📦 Ausgewählte Quarantäne</button>
      <button class="btn btn-danger" id="btn_d_sel">🗑 Ausgewählte löschen</button>
      <button class="btn btn-ghost" id="btn_clear_sel">✖ Auswahl leeren</button>
      <button class="btn btn-ghost" id="reload">↻ Neu laden</button>
    </div>
  </div>
  <div class="hr"></div>
  <div id="batchstatus" class="muted small">Bereit.</div>
</div>

<div class="box">
  <div class="flex" style="justify-content:space-between;">
    <div>
      <b>Aktionen-Log</b> <span class="pill">bleibt gespeichert</span>
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
    <h3>Suche & Anzeige</h3>
    <input class="search" id="q" placeholder="z.B. wicked, mccc, Ordner 2, oder Teil vom Pfad…">
    <div class="flex" style="margin-top:10px;">
      <label><input type="checkbox" id="f_name" checked> Name-Duplikate</label>
      <label><input type="checkbox" id="f_content" checked> Inhalt-Duplikate</label>
      <label><input type="checkbox" id="g_mod" checked> nach Mod-Ordner gruppieren</label>
      <label><input type="checkbox" id="show_full" checked> voller Pfad</label>
      <label title="Bei Gruppen-Aktionen wird bevorzugt eine Datei in Ordner 1 behalten">
        <input type="checkbox" id="keep_ord1" checked> bei Gruppen: Ordner 1 behalten
      </label>
    </div>
    <div class="hr"></div>
    <div id="summary" class="muted">Lade…</div>
  </div>

  <div class="box">
    <h3>Ordner</h3>
    <ul id="roots" class="muted" style="margin:0; padding-left:18px;"></ul>
    <div class="hr"></div>
    <div class="muted">Tipp: <b>Inhalt</b> = wirklich identisch. <b>Name</b> kann unterschiedlich sein.</div>
  </div>
</div>

<div class="box">
  <h2>Gruppen</h2>
  <div id="groups">Lade…</div>
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

function fmtGroupHeader(g) {
  const t = g.type === 'name' ? 'Name' : 'Inhalt';
  const count = g.files.length;
  const per = g.size_each ? ('je ~ ' + humanSize(g.size_each)) : '';
  const folders = uniqueCount(g.files.map(f => f.mod_folder || '(Mods-Root)'));
  return `<span><b>${esc(g.key_short)}</b>
    <span class="pill">${t}</span>
    <span class="pill">${count} Dateien</span>
    <span class="pill">${folders} Ordner</span>
    ${per ? `<span class="pill">${esc(per)}</span>` : ''}
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

function renderFileRow(f, gi) {
  const exists = f.exists ? '' : ' <span class="pill">fehlt</span>';
  const showFull = document.getElementById('show_full').checked;

  const rel = f.rel && f.rel !== f.path ? f.rel : '';
  const mainLine = rel ? rel : f.path;
  const fullLine = (rel && showFull)
    ? `<div class="muted small pathline" style="margin-top:4px;"><code>${esc(f.path)}</code></div>`
    : '';

  const btns = `
    <button class="btn btn-ok" data-act="quarantine" data-path="${esc(f.path)}">📦 Quarantäne</button>
    <button class="btn btn-danger" data-act="delete" data-path="${esc(f.path)}">🗑 Löschen</button>
    <button class="btn" data-act="open_folder" data-path="${esc(f.path)}">📂 Ordner</button>
    <button class="btn btn-ghost" data-act="copy" data-path="${esc(f.path)}">📋 Pfad</button>
  `;

  const checked = selected.has(f.path) ? 'checked' : '';

  return `
  <div class="file" data-gi="${gi}">
    <div class="row1">
      <input class="sel selbox" type="checkbox" data-path="${esc(f.path)}" data-gi="${gi}" ${checked}>
      <span class="tag">${esc(f.root_label)}</span>
      <span class="size">${esc(f.size_h || '?')}</span>
      <span class="date">${esc(f.mtime || '?')}</span>
      ${exists}
    </div>
    <div class="pathline" style="margin-top:6px;"><code>${esc(mainLine)}</code></div>
    ${fullLine}
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

function renderGroups(data) {
  const term = document.getElementById('q').value.trim().toLowerCase();
  const showName = document.getElementById('f_name').checked;
  const showContent = document.getElementById('f_content').checked;
  const groupMod = document.getElementById('g_mod').checked;

  const out = [];
  for (let gi = 0; gi < data.groups.length; gi++) {
    const g = data.groups[gi];

    if (g.type === 'name' && !showName) continue;
    if (g.type === 'content' && !showContent) continue;

    const hay = (g.type + ' ' + g.key + ' ' + g.key_short + ' ' + g.files.map(x => x.path).join(' '));
    if (!matchesFilters(hay, term)) continue;

    const keepPath = preferKeepPath(g.files);
    const keepHint = keepPath ? `<span class="pill">behalte: ${esc(keepPath.split(/[\\/]/).pop())}</span>` : '';

    let inner = '';
    if (groupMod) {
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
        <button class="btn btn-ghost" data-gact="select_all" data-gi="${gi}">✅ Alle markieren</button>
        <button class="btn btn-ghost" data-gact="select_rest" data-gi="${gi}">✅ Rest markieren (1 behalten)</button>
        <button class="btn btn-ok" data-gact="quarantine_rest" data-gi="${gi}">📦 Rest in Quarantäne</button>
        <button class="btn btn-danger" data-gact="delete_rest" data-gi="${gi}">🗑 Rest löschen</button>
        ${keepHint}
      </div>
    `;

    out.push(`<details class="grp">
      <summary>${fmtGroupHeader(g)}</summary>
      <div class="files">${tools}${inner}</div>
    </details>`);
  }
  return out.length ? out.join('') : '<p class="muted">Keine Treffer (Filter/Suche?).</p>';
}

function renderSummary(data) {
  const s = data.summary;
  return `
    Erstellt: <b>${esc(data.created_at)}</b><br>
    Gruppen: <b>${s.groups_name}</b> Name / <b>${s.groups_content}</b> Inhalt<br>
    Einträge: <b>${s.entries_total}</b><br>
    Verschwendeter Speicher (identische Duplikate): <b>${esc(s.wasted_h)}</b>
  `;
}

function renderRoots(data) {
  return data.roots.map(r => `<li><b>${esc(r.label)}:</b> <code>${esc(r.path)}</code></li>`).join('');
}

async function reloadData() {
  const data = await loadData();
  window.__DATA = data;
  document.getElementById('summary').innerHTML = renderSummary(data);
  document.getElementById('roots').innerHTML = renderRoots(data);
  document.getElementById('groups').innerHTML = renderGroups(data);
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
    await reloadData();
    setLast('↻ Neu geladen');
    addLog('RELOAD');
  } catch (e) {
    alert('Fehler: ' + e.message);
  }
});

// Group and per-file actions (event delegation)
document.getElementById('groups').addEventListener('click', async (ev) => {
  // group actions
  const gbtn = ev.target.closest('button[data-gact]');
  if (gbtn) {
    const gact = gbtn.dataset.gact;
    const gi = Number(gbtn.dataset.gi);
    const g = window.__DATA?.groups?.[gi];
    if (!g) return;

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
  } catch (e) {
    alert('Fehler: ' + e.message);
    console.error('[ACTION_ERR]', act, path, e);
    setLast('❌ Fehler: ' + e.message);
    addLog('ERROR ' + act + ' :: ' + path + ' :: ' + e.message);
  }
});

for (const id of ['q','f_name','f_content','g_mod','show_full','keep_ord1']) {
  const el = document.getElementById(id);
  el.addEventListener('input', () => {
    if (window.__DATA) document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
  });
  el.addEventListener('change', () => {
    if (window.__DATA) document.getElementById('groups').innerHTML = renderGroups(window.__DATA);
  });
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

        self.var_add_path = tk.StringVar(value="")
        self.var_status = tk.StringVar(value="Bereit.")
        self.var_detail = tk.StringVar(value="")

        self.server: LocalServer | None = None
        self.listbox = None
        self.progress = None
        self.btn_run = None

        self._build_ui()
        self._load_config_into_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
        ttk.Checkbutton(opt, text="Duplikate nach Inhalt (SHA-256)", variable=self.var_do_content).pack(anchor="w", pady=(0, 10))

        self.btn_run = ttk.Button(opt, text="Scan & Web-UI öffnen", command=self.run_scan)
        self.btn_run.pack(fill="x")

        self.btn_backup = ttk.Button(opt, text="📦 Backup erstellen", command=self.create_backup)
        self.btn_backup.pack(fill="x", pady=(10, 0))

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

        ttk.Label(self, text="Tipp: Mehrere Pfade auf einmal einfügen (Zeilenumbruch oder ';').").pack(anchor="w", padx=pad, pady=(0, pad))

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

    def _save_config_now(self):
        """Speichere aktuelle Einstellungen in die Konfiguration."""
        folders = list(self.listbox.get(0, "end"))
        cfg = {
            "folders": folders,
            "exts": self.var_exts.get(),
            "ignore": self.var_ignore.get(),
        }
        save_config(cfg)

    def on_close(self):
        """Beim Schließen des Fensters."""
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
                    self.set_progress_indet(True, "Finalisiere…", msg)
            self.after(0, apply)

        def worker():
            try:
                files, name_dupes, content_dupes = scan_duplicates(
                    roots=roots,
                    exts=exts,
                    ignore_dirs=ignore_dirs,
                    do_name=do_name,
                    do_content=do_content,
                    progress_cb=ui_progress,
                )

                ds = Dataset(roots)
                ds.build_from_scan(name_dupes, content_dupes)

                self.stop_server()
                srv = LocalServer(ds, qdir)
                srv.start()
                self.server = srv

                def finish():
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=0, maximum=1)
                    self.var_status.set("Fertig.")
                    self.var_detail.set(
                        f"Dateien: {len(files)} | Gruppen: Name {len(name_dupes)} / Inhalt {len(content_dupes)} | Quarantäne: {qdir} | Log: {srv.log_file}"
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
