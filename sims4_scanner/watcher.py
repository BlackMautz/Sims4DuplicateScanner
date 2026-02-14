# -*- coding: utf-8 -*-
"""ModFolderWatcher: Überwacht Mod-Ordner auf Dateiänderungen."""

from __future__ import annotations

import os
import sys
import time
import ctypes
import threading
from pathlib import Path


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
        self._snapshot: dict[str, tuple[float, int]] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_change_time: float | None = None
        self._pending_changes: list[str] = []
        self.last_event: str = ""
        self.last_event_time: float = 0

    def _build_snapshot(self) -> dict[str, tuple[float, int]]:
        snap: dict[str, tuple[float, int]] = {}
        ignore_dirs = {"__macosx", ".git", "__pycache__"}
        for root in self.roots:
            if not root.exists():
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    filtered = []
                    for d in dirnames:
                        if d.lower() in ignore_dirs:
                            continue
                        dp = Path(dirpath) / d
                        try:
                            if dp.is_symlink():
                                continue
                            if sys.platform == 'win32':
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
        changes: list[str] = []
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
