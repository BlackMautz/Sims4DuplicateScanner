# -*- coding: utf-8 -*-
"""Auto-Update-Check und -Download über die GitHub Releases API."""

from __future__ import annotations

import os
import re
import sys
import json
import tempfile
import subprocess

from .constants import SCANNER_VERSION, GITHUB_REPO

_update_cache: dict | None = None


def _parse_version(v: str) -> tuple[int, ...]:
    """'v2.3.0' oder '2.3.0' → (2, 3, 0)"""
    v = v.strip().lstrip("vV")
    parts: list[int] = []
    for p in v.split("."):
        m = re.match(r"(\d+)", p)
        if m:
            parts.append(int(m.group(1)))
    return tuple(parts) if parts else (0,)


def check_for_update(timeout: float = 5.0) -> dict:
    """Fragt GitHub Releases API ab. Ergebnis wird gecacht (einmal pro App-Start)."""
    global _update_cache
    if _update_cache is not None:
        return _update_cache

    result: dict = {
        "available": False, "current": SCANNER_VERSION,
        "latest": SCANNER_VERSION, "url": "", "name": "", "body": "",
        "download_url": "",
    }
    try:
        from urllib.request import urlopen, Request
        req = Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "Sims4DupScanner"},
        )
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = data.get("tag_name", "")
        latest = _parse_version(tag)
        current = _parse_version(SCANNER_VERSION)
        result["latest"] = tag.lstrip("vV")
        result["name"] = data.get("name", "")
        result["body"] = data.get("body", "")
        result["url"] = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
        for asset in data.get("assets", []):
            if asset.get("name", "").lower().endswith(".exe"):
                result["download_url"] = asset.get("browser_download_url", "")
                break
        if latest > current:
            result["available"] = True
            print(f"[UPDATE] Neue Version verfügbar: {tag} (aktuell: {SCANNER_VERSION})", flush=True)
        else:
            print(f"[UPDATE] Aktuelle Version {SCANNER_VERSION} ist aktuell (latest: {tag})", flush=True)
    except Exception as ex:
        print(f"[UPDATE] Check fehlgeschlagen: {type(ex).__name__}: {ex}", flush=True)

    _update_cache = result
    return result


def _get_exe_path() -> str:
    """Gibt den Pfad der laufenden EXE zurück (oder '' wenn nicht als EXE gestartet)."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return ''


def download_update(download_url: str, progress_cb=None) -> str:
    """Lädt die neue EXE herunter. Gibt den Pfad der heruntergeladenen Datei zurück.

    progress_cb(downloaded_bytes, total_bytes) wird regelmäßig aufgerufen.
    """
    from urllib.request import urlopen, Request

    exe_path = _get_exe_path()
    if not exe_path:
        raise RuntimeError("Update nur als EXE möglich, nicht im Entwicklungsmodus")

    # Neben die aktuelle EXE als .update herunterladen
    update_path = exe_path + ".update"

    print(f"[UPDATE] Lade herunter: {download_url}", flush=True)
    req = Request(download_url, headers={"User-Agent": "Sims4DupScanner"})
    resp = urlopen(req, timeout=60)

    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    chunk_size = 256 * 1024  # 256 KB

    with open(update_path, "wb") as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if progress_cb:
                progress_cb(downloaded, total)

    resp.close()

    # Prüfe ob die Datei eine gültige EXE ist (PE-Header)
    with open(update_path, "rb") as f:
        header = f.read(2)
    if header != b"MZ":
        os.remove(update_path)
        raise RuntimeError("Heruntergeladene Datei ist keine gültige EXE")

    file_size = os.path.getsize(update_path)
    print(f"[UPDATE] Download abgeschlossen: {file_size / 1048576:.1f} MB → {update_path}", flush=True)
    return update_path


def apply_update_and_restart(update_path: str):
    """Erstellt ein Batch-Script das die alte EXE ersetzt und die neue startet.

    Ablauf:
    1. Zone-Identifier (Internet-Markierung) von der neuen EXE entfernen
    2. Warte bis die aktuelle EXE nicht mehr gesperrt ist
    3. Lösche die alte EXE
    4. Benenne die neue (.update) in den alten Namen um
    5. Starte die neue EXE
    6. Lösche das Batch-Script
    """
    exe_path = _get_exe_path()
    if not exe_path:
        raise RuntimeError("Update nur als EXE möglich")

    exe_name = os.path.basename(exe_path)
    exe_dir = os.path.dirname(exe_path)

    # Zone.Identifier entfernen (Windows "Aus dem Internet"-Blockierung)
    # Ohne das kann Windows SmartScreen die neue EXE blockieren
    try:
        zi_path = update_path + ":Zone.Identifier"
        if os.path.exists(zi_path):
            os.remove(zi_path)
            print("[UPDATE] Zone.Identifier entfernt", flush=True)
    except Exception:
        pass
    # Alternativ via PowerShell (robuster)
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f'Unblock-File -Path "{update_path}"'],
            timeout=5, capture_output=True,
        )
        print("[UPDATE] Unblock-File ausgeführt", flush=True)
    except Exception:
        pass

    # Batch-Script im selben Ordner erstellen
    bat_path = os.path.join(exe_dir, "_update.bat")
    update_name = os.path.basename(update_path)

    # Das Script wartet max 30 Sekunden (60 x 0.5s) bis die alte EXE frei ist
    bat_content = f'''@echo off
echo Sims 4 Duplikate Scanner wird aktualisiert...
echo Bitte warte einen Moment...
cd /d "{exe_dir}"

REM Warte kurz damit der alte Prozess sicher beendet ist
ping -n 3 127.0.0.1 >nul 2>&1

set RETRIES=0
:WAIT_LOOP
if %RETRIES% GEQ 60 (
    echo Update fehlgeschlagen - Programm laeuft noch.
    pause
    goto END
)
del "{exe_name}" >nul 2>&1
if exist "{exe_name}" (
    set /a RETRIES+=1
    ping -n 2 127.0.0.1 >nul 2>&1
    goto WAIT_LOOP
)

echo Installiere neue Version...
rename "{update_name}" "{exe_name}"
if errorlevel 1 (
    echo Umbenennung fehlgeschlagen!
    pause
    goto END
)

echo Update abgeschlossen! Starte Scanner...
ping -n 2 127.0.0.1 >nul 2>&1
start "" "{exe_dir}\\{exe_name}"

:END
REM Kurz warten damit start den Prozess starten kann
ping -n 3 127.0.0.1 >nul 2>&1
del "%~f0" >nul 2>&1
'''

    with open(bat_path, "w", encoding="ascii", errors="replace") as f:
        f.write(bat_content)

    print(f"[UPDATE] Starte Update-Script: {bat_path}", flush=True)

    # CREATE_BREAKAWAY_FROM_JOB (0x01000000) sorgt dafür, dass das Batch-Script
    # NICHT mit dem Parent-Prozess stirbt (PyInstaller Job-Object-Problem)
    CREATE_BREAKAWAY_FROM_JOB = 0x01000000
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        cwd=exe_dir,
        creationflags=(
            subprocess.CREATE_NEW_CONSOLE
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | CREATE_BREAKAWAY_FROM_JOB
        ),
        close_fds=True,
    )

    # Kurz warten damit das Batch-Script sicher gestartet ist
    import time
    time.sleep(1)

    # App beenden damit die EXE freigegeben wird
    print("[UPDATE] App wird beendet für Update...", flush=True)
    os._exit(0)
