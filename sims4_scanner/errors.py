# -*- coding: utf-8 -*-
"""Sims-4-Fehlerlog-Analyse und Sims-4-Verzeichnis-Erkennung."""

from __future__ import annotations

import os
import re
import ctypes
from pathlib import Path
from datetime import datetime


def find_sims4_userdir(scan_roots: list[Path] | None = None) -> Path | None:
    """Versucht das Sims 4 Benutzerverzeichnis automatisch zu finden."""
    candidates: list[Path] = []

    if scan_roots:
        for r in scan_roots:
            p = r
            for _ in range(6):
                if (p / "GameVersion.txt").exists() or (p / "Options.ini").exists():
                    return p
                if p.parent == p:
                    break
                p = p.parent
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

    userprofile = os.environ.get("USERPROFILE", str(Path.home()))

    doc_paths: set[Path] = set()
    doc_paths.add(Path(userprofile) / "Documents")
    doc_paths.add(Path(userprofile) / "Dokumente")
    doc_paths.add(Path(userprofile) / "OneDrive" / "Documents")
    doc_paths.add(Path(userprofile) / "OneDrive" / "Dokumente")

    try:
        import ctypes.wintypes
        CSIDL_PERSONAL = 5
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
        if buf.value:
            doc_paths.add(Path(buf.value))
    except Exception:
        pass

    sims4_names = ["Die Sims 4", "The Sims 4", "Les Sims 4", "Los Sims 4"]

    for doc in doc_paths:
        for name in sims4_names:
            candidate = doc / "Electronic Arts" / name
            if candidate.exists() and (candidate / "Options.ini").exists():
                return candidate
            if candidate.exists() and (candidate / "Mods").exists():
                candidates.append(candidate)

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

    if candidates:
        return candidates[0]

    return None


def list_exception_files(sims4_dir: Path) -> list[dict]:
    """Listet alle Exception-Dateien mit Name, Datum und Größe auf."""
    result: list[dict] = []
    patterns = ["lastException*.txt", "lastUIException*.txt", "WickedWhims*Exception*.txt"]
    for pat in patterns:
        files = sorted(sims4_dir.glob(pat),
                       key=lambda x: x.stat().st_mtime if x.exists() else 0,
                       reverse=True)
        for i, f in enumerate(files):
            try:
                st = f.stat()
                mtime = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y %H:%M")
                size_kb = round(st.st_size / 1024, 1)
                result.append({"name": f.name, "datum": mtime, "groesse_kb": size_kb,
                               "ist_aktuell": i == 0})
            except Exception:
                result.append({"name": f.name, "datum": "?", "groesse_kb": 0, "ist_aktuell": False})
    return result


def parse_sims4_errors(sims4_dir: Path) -> list[dict]:
    """Liest alle relevanten Fehlerlogs und gibt verständliche Erklärungen zurück."""
    errors: list[dict] = []

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

    log_files: list[tuple[str, Path]] = []

    def newest_file(pattern: str) -> Path | None:
        files = list(sims4_dir.glob(pattern))
        if not files:
            return None
        files.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
        return files[0]

    newest = newest_file("lastException*.txt")
    if newest:
        log_files.append(("Python-Fehler", newest))

    newest = newest_file("lastUIException*.txt")
    if newest:
        log_files.append(("UI-Fehler", newest))

    newest = newest_file("WickedWhims*Exception*.txt")
    if newest:
        log_files.append(("WickedWhims-Fehler", newest))

    mod_logs = sims4_dir / "mod_logs"
    if mod_logs.exists():
        seen_mod_names: set[str] = set()
        mod_log_files = sorted(mod_logs.glob("*.txt"),
                               key=lambda f: f.stat().st_mtime if f.exists() else 0,
                               reverse=True)
        for f in mod_log_files:
            base = re.sub(r'_?\d+[\._]\d+.*$', '', f.stem).lower()
            if base not in seen_mod_names:
                seen_mod_names.add(base)
                log_files.append(("Mod-Log", f))

    seen_keys: set[str] = set()

    for kategorie, log_path in log_files:
        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if not content.strip():
            continue

        if len(content) > 100_000:
            content = content[:100_000]

        try:
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
        except Exception:
            mtime = "unbekannt"

        mod_files_found: set[str] = set()
        for i, line in enumerate(content.splitlines()):
            if i >= 200:
                break
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

        if not matched and ("error" in content.lower() or "exception" in content.lower()):
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

    schwere_order = {"hoch": 0, "mittel": 1, "niedrig": 2, "unbekannt": 3}
    errors.sort(key=lambda e: schwere_order.get(e["schwere"], 99))

    return errors
