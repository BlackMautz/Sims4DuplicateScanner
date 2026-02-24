# -*- coding: utf-8 -*-
"""Sims-4-Fehlerlog-Analyse und Sims-4-Verzeichnis-Erkennung.

Tiefenanalyse: XML-Parsing, Traceback-Extraktion, Mod-Erkennung aus Pfaden,
BetterExceptions-Integration, Duplikat-Zusammenfassung, UI-Widget-Erkennung.
"""

from __future__ import annotations

import os
import re
import ctypes
import html as html_mod
from collections import Counter
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
#  Bekannte Mod-Pfad-Muster → lesbarer Name
# ---------------------------------------------------------------------------
_KNOWN_MOD_PATHS: list[tuple[str, str]] = [
    (r"mc_cmd_center|mc_utils|mc_injections|mc_workaround", "MC Command Center (MCCC)"),
    (r"WickedWhims_v\w+\\wickedwhims|wickedwhims\\", "WickedWhims"),
    (r"turbolib2?\\", "TurboLib (WickedWhims)"),
    (r"NisaK\\|wickedpervs\\|LL_\d", "Wicked Perversions (NisaK)"),
    (r"Sims4CommunityLib|sims4communitylib|s4cl", "Sims4CommunityLib"),
    (r"kuttoe|HomeRegions", "Kuttoe Home Regions"),
    (r"basemental", "Basemental Drugs"),
    (r"littlemssam|LittleMsSam", "LittleMsSam"),
    (r"roBurky|meaningful_stories", "Meaningful Stories"),
    (r"zerbu|Venue_Changes", "Zerbu Venue Changes"),
    (r"ui_cheats|UICheats", "UI Cheats Extension"),
    (r"tmex|twistedmexi", "TwistedMexi"),
    (r"polarbearsims", "PolarBearSims"),
    (r"ColonolNutty|CustomGenderSettings", "ColonolNutty"),
    (r"lot51|Lot51", "Lot51"),
    (r"simvasion", "Simvasion"),
    (r"scarlet|Scarlet", "Scarlet"),
]

# ActionScript-UI-Widgets → verständliche Komponente
_UI_WIDGET_MAP: dict[str, str] = {
    "BuffDisplayAnimator": "Moodlet-/Buff-Anzeige",
    "BuffDisplay": "Moodlet-/Buff-Anzeige",
    "BuffItemBlock": "Moodlet-/Buff-Anzeige",
    "SimHubMain": "Sim-Info-Hub (unten links)",
    "ClubPanelButton": "Club-Panel / Gruppen-Button",
    "HUDCheatSheet": "Cheat-Hilfe-Overlay (HUD)",
    "InventoryGrid": "Inventar-Raster",
    "CareerPanel": "Karriere-Panel",
    "SimInfoTray": "Sim-Info-Leiste",
    "RelationshipsPanel": "Beziehungs-Panel",
    "SkillsPanel": "Fähigkeiten-Panel",
    "MapViewManager": "Kartenansicht",
    "LiveModePanel": "Live-Modus Panel",
    "BuildBuyPanel": "Bau-/Kaufmodus Panel",
    "CASPanel": "Erstelle einen Sim (CAS)",
    "NotificationManager": "Benachrichtigungen",
}


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


# ---------------------------------------------------------------------------
#  Hilfsfunktionen für Tiefenanalyse
# ---------------------------------------------------------------------------

def _decode_xml_text(raw: str) -> str:
    """Dekodiere XML-Entitäten (&#13;&#10; → Zeilenumbrüche usw.)."""
    text = html_mod.unescape(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def _extract_reports_from_xml(content: str) -> list[dict]:
    """Extrahiere einzelne <report>-Blöcke aus Sims 4 XML-Logs.

    Gibt eine Liste von dicts zurück mit:
    - createtime, categoryid, desyncdata (dekodiert), type
    """
    reports: list[dict] = []
    for m in re.finditer(r'<report>(.*?)</report>', content, re.DOTALL):
        block = m.group(1)
        ct = ""
        cm = re.search(r'<createtime>(.*?)</createtime>', block)
        if cm:
            ct = cm.group(1)
        cat = ""
        catm = re.search(r'<categoryid>(.*?)</categoryid>', block)
        if catm:
            cat = _decode_xml_text(catm.group(1))
        data = ""
        dm = re.search(r'<desyncdata>(.*?)</desyncdata>', block, re.DOTALL)
        if dm:
            data = _decode_xml_text(dm.group(1))
        reports.append({"createtime": ct, "categoryid": cat, "desyncdata": data})
    return reports


def _extract_be_info(content: str) -> dict:
    """Lese BetterExceptions-Tags aus dem XML."""
    info: dict = {}
    bm = re.search(r'<BetterExceptions>(.*?)</BetterExceptions>', content, re.DOTALL)
    if bm:
        block = bm.group(1)
        for tag in ["BEversion", "Advice", "BadObjectCC", "WasBlank"]:
            tm = re.search(rf'<{tag}>(.*?)</{tag}>', block)
            if tm:
                info[tag] = _decode_xml_text(tm.group(1))
    return info


def _extract_mods_from_traceback(text: str) -> list[str]:
    """Erkenne Mod-Namen aus Python-Traceback-Pfaden.

    Sucht nach bekannten Mod-Pfad-Mustern und extrahiert
    auch unbekannte Mod-Pfade die nicht zum EA-Basisspiel gehören.
    """
    found: list[str] = []
    found_set: set[str] = set()

    # Bekannte Mods per Pfad-Muster
    for pattern, name in _KNOWN_MOD_PATHS:
        if re.search(pattern, text, re.IGNORECASE) and name not in found_set:
            found.append(name)
            found_set.add(name)

    # .ts4script und .package Dateien im Text
    for ext_match in re.finditer(r'([\w\-\.]+\.(?:ts4script|package))', text, re.IGNORECASE):
        fname = ext_match.group(1)
        if fname.lower() not in found_set:
            found_set.add(fname.lower())
            found.append(fname)

    return found


def _extract_traceback_snippet(text: str, max_lines: int = 25) -> str:
    """Extrahiere einen lesbaren Traceback-Auszug aus decodiertem Text."""
    lines = text.split("\n")
    tb_start = -1
    tb_end = -1
    for i, line in enumerate(lines):
        if "Traceback (most recent call last)" in line:
            tb_start = i
        if tb_start >= 0 and i > tb_start:
            # Ende des Tracebacks: Zeile die mit Error/Exception endet
            stripped = line.strip()
            if stripped and not stripped.startswith("File ") and not stripped.startswith("at ") and "in " not in stripped:
                if any(kw in stripped for kw in ["Error", "Exception", "assert"]):
                    tb_end = i + 1
                    break
    if tb_start >= 0:
        end = tb_end if tb_end > tb_start else min(tb_start + max_lines, len(lines))
        snippet_lines = lines[tb_start:end]
        return "\n".join(snippet_lines[:max_lines])

    # Kein Traceback gefunden — ersten sinnvollen Block nehmen
    # Für UI-Fehler: Error-Zeile + Stacktrace
    error_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and ("Error" in stripped or "at " in stripped or "exception" in stripped.lower()):
            error_lines.append(stripped)
            if len(error_lines) >= max_lines:
                break
    if error_lines:
        return "\n".join(error_lines)

    # Fallback: erste nicht-leere Zeilen
    non_empty = [l.strip() for l in lines if l.strip()]
    return "\n".join(non_empty[:max_lines])


def _identify_ui_component(text: str) -> str | None:
    """Erkenne die betroffene UI-Komponente aus ActionScript-Fehlern."""
    for widget_key, widget_name in _UI_WIDGET_MAP.items():
        if widget_key in text:
            return widget_name
    # Generische Erkennung: widgets.XXX.YYY::ZZZ
    m = re.search(r'widgets\.[\w.]+::(\w+)', text)
    if m:
        return m.group(1)
    return None


def _count_unique_reports(reports: list[dict]) -> dict[str, int]:
    """Zähle Duplikate basierend auf categoryid + Fehlertyp."""
    counter: Counter[str] = Counter()
    for r in reports:
        # Normalisiere: entferne runtime-werte (rtim=...)
        key_text = re.sub(r'rtim=\d+', '', r.get("desyncdata", ""))
        # Kürze auf ersten sinnvollen Teil für Gruppierung
        key_text = key_text[:300]
        key = f"{r.get('categoryid', '')}|{key_text[:200]}"
        counter[key] += 1
    return dict(counter)


# ---------------------------------------------------------------------------
#  Haupt-Parsing
# ---------------------------------------------------------------------------

def parse_sims4_errors(sims4_dir: Path) -> list[dict]:
    """Liest alle relevanten Fehlerlogs und gibt verständliche Erklärungen zurück.

    Tiefenanalyse mit:
    - XML-Parsing und Report-Extraktion
    - BetterExceptions-Integration
    - Traceback-Pfad-Analyse für Mod-Erkennung
    - Duplikat-Zusammenfassung
    - UI-Widget-Erkennung
    """
    errors: list[dict] = []

    # -----------------------------------------------------------------------
    #  Muster für Python-Fehler
    # -----------------------------------------------------------------------
    PYTHON_PATTERNS = [
        {
            "regex": r"ImportError.*No module named '([^']+)'",
            "titel": "Fehlende Mod-Abhängigkeit",
            "erklaerung": "Ein Mod versucht das Modul '{1}' zu laden, das nicht installiert ist.",
            "loesung": "Prüfe ob der Mod alle benötigten Dateien hat. Eventuell fehlt ein Zusatz-Mod oder eine Bibliothek.",
            "schwere": "hoch",
        },
        {
            "regex": r"ModuleNotFoundError.*No module named '([^']+)'",
            "titel": "Python-Modul fehlt",
            "erklaerung": "Das Python-Modul '{1}' wurde nicht gefunden.",
            "loesung": "Ein Mod benötigt eine Bibliothek die fehlt. Mod aktualisieren oder die fehlende Datei nachinstallieren.",
            "schwere": "hoch",
        },
        {
            "regex": r"AttributeError.*'(\w+)' object has no attribute '(\w+)'",
            "titel": "Veralteter oder inkompatibler Mod",
            "erklaerung": "Objekt '{1}' hat kein Attribut '{2}'. Das passiert wenn ein Mod veraltete Funktionen aufruft.",
            "loesung": "Aktualisiere den betroffenen Mod. Häufig nach einem Spiel-Patch nötig.",
            "schwere": "hoch",
        },
        {
            "regex": r"AttributeError.*'NoneType' object has no attribute '(\w+)'",
            "titel": "Objekt nicht gefunden (NoneType)",
            "erklaerung": "Ein Mod versucht auf '{1}' zuzugreifen, aber das Objekt existiert nicht (ist None).",
            "loesung": "Oft ein Timing-Problem oder ein gelöschtes Spielobjekt. Mod aktualisieren.",
            "schwere": "hoch",
        },
        {
            "regex": r"AssertionError.*?EventManager[\s\S]*?EventManagerService is disabled",
            "titel": "EventManager deaktiviert",
            "erklaerung": "Ein Mod versucht Events zu registrieren, aber der EventManager ist deaktiviert (z.B. beim Speichern/Laden).",
            "loesung": "Dies ist ein bekannter EA-Bug der beim Zonenwechsel oder Speichern auftritt. Meist harmlos, aber kann bei häufigem Auftreten auf Mod-Konflikte hinweisen.",
            "schwere": "niedrig",
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
            "erklaerung": "Die Datei '{1}' wurde nicht gefunden.",
            "loesung": "Die Datei wurde gelöscht oder verschoben. Mod neu installieren.",
            "schwere": "mittel",
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
        {
            "regex": r"RuntimeError.*maximum recursion",
            "titel": "Endlosschleife (Rekursion)",
            "erklaerung": "Ein Mod hat eine Endlosschleife ausgelöst (maximale Rekursionstiefe überschritten).",
            "loesung": "Zwei Mods rufen sich gegenseitig auf. Mod-Konflikte prüfen, einen der Mods deaktivieren.",
            "schwere": "hoch",
        },
        {
            "regex": r"IndexError.*(?:list|tuple) index out of range",
            "titel": "Index außerhalb des Bereichs",
            "erklaerung": "Ein Mod greift auf eine Position in einer Liste zu die nicht existiert.",
            "loesung": "Mod aktualisieren. Kann auch durch fehlende CC/Tuning-Dateien ausgelöst werden.",
            "schwere": "mittel",
        },
        {
            "regex": r"ValueError.*(?:invalid literal|could not convert)",
            "titel": "Ungültiger Wert",
            "erklaerung": "Ein Mod versucht einen ungültigen Wert zu verarbeiten.",
            "loesung": "Mod aktualisieren oder beschädigte Einstellungsdateien löschen.",
            "schwere": "mittel",
        },
        {
            "regex": r"OSError|IOError|PermissionError",
            "titel": "Datei-/Zugriffsfehler",
            "erklaerung": "Ein Mod konnte nicht auf eine Datei zugreifen (Berechtigungsproblem oder Datei gesperrt).",
            "loesung": "Prüfe ob Antivirus den Zugriff blockiert. Spiel als Administrator ausführen kann helfen.",
            "schwere": "mittel",
        },
    ]

    # -----------------------------------------------------------------------
    #  WickedWhims-spezifische Muster
    # -----------------------------------------------------------------------
    WW_PATTERNS = [
        {
            "regex": r"KeyError.*_cache_sex_posture_animation_data",
            "titel": "WickedWhims: Kaputte Animation",
            "erklaerung": "Eine WickedWhims-Animation ist veraltet oder beschädigt.",
            "loesung": "Benutze Sims 4 Studio → 'Find Resource' mit der Resource-ID um die kaputte Animation zu finden und zu entfernen.",
            "schwere": "niedrig",
        },
        {
            "regex": r"WickedWhims.*outdated.*broken",
            "titel": "WickedWhims: Veraltete/Kaputte Mods erkannt",
            "erklaerung": "WickedWhims hat veraltete oder kaputte Animations-Mods erkannt.",
            "loesung": "Die Resource-IDs in Sims 4 Studio suchen und betroffene Dateien entfernen oder aktualisieren.",
            "schwere": "mittel",
        },
        {
            "regex": r"TurboLib.*Failed to run '([^']+)'.*from '([^']+)'.*?(\w+Error:.*?)$",
            "titel": "TurboLib/WickedWhims: Funktionsfehler",
            "erklaerung": "TurboLib konnte '{1}' von '{2}' nicht ausführen: {3}",
            "loesung": "WickedWhims und alle zugehörigen Mods aktualisieren. Bei 'NoneType' Fehlern kann ein Spielobjekt fehlen.",
            "schwere": "mittel",
        },
    ]

    # -----------------------------------------------------------------------
    #  MCCC-spezifische Muster
    # -----------------------------------------------------------------------
    MCCC_PATTERNS = [
        {
            "regex": r"mc_cmd_center.*failed to load|MCCC.*load.*fail",
            "titel": "MCCC: Laden fehlgeschlagen",
            "erklaerung": "MC Command Center konnte nicht korrekt geladen werden.",
            "loesung": "MCCC komplett neu installieren. Alle mc_*.ts4script und mc_*.package Dateien ersetzen.",
            "schwere": "hoch",
        },
        {
            "regex": r"mc_cmd_center.*?(\w+Error.*?)(?:\n|rtim|$)",
            "titel": "MCCC: Fehler",
            "erklaerung": "MC Command Center hat einen Fehler: {1}",
            "loesung": "MCCC auf die neueste Version aktualisieren: https://deaderpool-mccc.com",
            "schwere": "mittel",
        },
    ]

    # -----------------------------------------------------------------------
    #  UI/ActionScript-Muster
    # -----------------------------------------------------------------------
    UI_PATTERNS = [
        {
            "regex": r"Error #1009.*?Cannot access a property or method of a null object",
            "titel": "UI-Fehler: Null-Objekt-Zugriff",
            "schwere": "mittel",
        },
        {
            "regex": r"Error #1010.*?A term is undefined and has no properties",
            "titel": "UI-Fehler: Undefinierter Wert",
            "schwere": "mittel",
        },
        {
            "regex": r"Error #1069.*?Property \w+ not found",
            "titel": "UI-Fehler: Eigenschaft nicht gefunden",
            "schwere": "mittel",
        },
        {
            "regex": r"Error #1034.*?Type Coercion failed",
            "titel": "UI-Fehler: Typ-Konvertierung fehlgeschlagen",
            "schwere": "mittel",
        },
    ]

    ALL_PYTHON_PATTERNS = PYTHON_PATTERNS + WW_PATTERNS + MCCC_PATTERNS

    # -----------------------------------------------------------------------
    #  Dateien sammeln — nur die NEUESTE pro Typ (ältere = Backup)
    # -----------------------------------------------------------------------
    log_files: list[tuple[str, Path]] = []

    def newest_file(pattern: str) -> Path | None:
        files = list(sims4_dir.glob(pattern))
        if not files:
            return None
        files.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
        return files[0]

    nf = newest_file("lastException*.txt")
    if nf:
        log_files.append(("Python-Fehler", nf))

    nf = newest_file("lastUIException*.txt")
    if nf:
        log_files.append(("UI-Fehler", nf))

    nf = newest_file("WickedWhims*Exception*.txt")
    if nf:
        log_files.append(("WickedWhims-Fehler", nf))

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

        # Begrenze auf 500KB pro Datei
        if len(content) > 500_000:
            content = content[:500_000]

        try:
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
        except Exception:
            mtime = "unbekannt"

        # ---------------------------------------------------------------
        #  BetterExceptions-Info extrahieren
        # ---------------------------------------------------------------
        be_info = _extract_be_info(content)
        be_advice = be_info.get("Advice", "")
        be_bad_cc = be_info.get("BadObjectCC", "").lower() == "true"

        # ---------------------------------------------------------------
        #  Ist es ein XML-Log? → Reports extrahieren
        # ---------------------------------------------------------------
        is_xml = "<report>" in content or "<root>" in content
        is_ww_log = "WickedWhims" in log_path.name

        if is_xml:
            reports = _extract_reports_from_xml(content)
            if not reports:
                continue

            # Duplikate zählen
            dupes = _count_unique_reports(reports)
            total_reports = len(reports)

            # Nur einzigartige Reports analysieren (nach categoryid)
            seen_categories: dict[str, dict] = {}
            for r in reports:
                cat = r["categoryid"]
                if cat not in seen_categories:
                    seen_categories[cat] = r

            for cat_key, report in seen_categories.items():
                data = report["desyncdata"]
                if not data.strip():
                    continue

                # Anzahl dieses Fehlertyps
                count = sum(v for k, v in dupes.items() if cat_key in k)

                # Mods aus Traceback erkennen
                mods_found = _extract_mods_from_traceback(data)

                # Traceback-Snippet extrahieren
                snippet = _extract_traceback_snippet(data)

                # UI-Komponente erkennen
                ui_component = _identify_ui_component(data)

                # ----- UI-Fehler (ActionScript) -----
                is_ui_error = any(f"Error #{n}" in data for n in ["1009", "1010", "1069", "1034"])

                if is_ui_error:
                    # UI-Fehler-Typ bestimmen
                    titel = "UI-Fehler (ActionScript)"
                    loesung = "Cache löschen (localthumbcache.package). Wenn der Fehler bleibt, UI-Mods prüfen."
                    for up in UI_PATTERNS:
                        if re.search(up["regex"], data, re.IGNORECASE):
                            titel = up["titel"]
                            break

                    # Detaillierte Erklärung
                    if ui_component:
                        erklaerung = f"UI-Komponente '{ui_component}' hat einen Fehler."
                    else:
                        erklaerung = "Die Benutzeroberfläche hat einen Flash/ActionScript-Fehler."

                    if count > 1:
                        erklaerung += f" (Trat {count}x auf in dieser Session)"

                    # Stacktrace auswerten
                    as_stack: list[str] = []
                    for sm in re.finditer(r'at (widgets\.[^\r\n]+)', data):
                        as_stack.append(sm.group(1).strip())
                    if as_stack:
                        erklaerung += f"\n→ Callstack: {' → '.join(as_stack[:4])}"

                    if not mods_found:
                        erklaerung += "\n→ Dies ist wahrscheinlich ein EA Base-Game Bug, kein Mod-Problem."
                        loesung = "Meist ein harmloser EA-Bug. Cache löschen (localthumbcache.package) kann helfen. Wenn es das Spiel stört, im EA-Forum melden."

                    key = f"UI|{titel}|{cat_key}|{log_path.name}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    errors.append({
                        "kategorie": kategorie,
                        "datei": log_path.name,
                        "datum": mtime,
                        "titel": titel,
                        "erklaerung": erklaerung,
                        "loesung": loesung,
                        "schwere": "niedrig" if not mods_found else "mittel",
                        "betroffene_mods": mods_found,
                        "raw_snippet": snippet,
                        "anzahl": count,
                        "total_reports": total_reports,
                        "be_advice": be_advice if be_advice else None,
                    })
                    continue

                # ----- Python-Fehler -----
                matched = False
                for pat in ALL_PYTHON_PATTERNS:
                    mp = re.search(pat["regex"], data, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if mp:
                        groups = mp.groups()
                        erklaerung = pat["erklaerung"]
                        for i, g in enumerate(groups, 1):
                            erklaerung = erklaerung.replace(f"{{{i}}}", str(g) if g else "?")

                        if mods_found:
                            erklaerung += f"\n→ Beteiligte Mods: {', '.join(mods_found)}"
                        if count > 1:
                            erklaerung += f" (Trat {count}x auf)"
                        if be_advice and be_advice != "Not available. More info may be in BE Report.":
                            erklaerung += f"\n→ BetterExceptions sagt: {be_advice}"
                        if be_bad_cc:
                            erklaerung += "\n→ ⚠️ BetterExceptions: Vermutlich kaputtes CC-Objekt!"

                        key = f"PY|{pat['titel']}|{cat_key}|{log_path.name}"
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
                            "betroffene_mods": mods_found,
                            "raw_snippet": snippet,
                            "anzahl": count,
                            "total_reports": total_reports,
                            "be_advice": be_advice if be_advice else None,
                        })
                        matched = True
                        break  # Nur bestes Match pro Report

                if not matched and data.strip():
                    # Unbekannter Fehler mit Mod-Info
                    first_error_line = ""
                    for line in data.split("\n"):
                        ls = line.strip()
                        if ls and any(kw in ls for kw in ["Error", "Exception", "Traceback"]):
                            first_error_line = ls[:300]
                            break

                    key = f"UNK|{cat_key}|{log_path.name}|{first_error_line[:80]}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    erkl = first_error_line if first_error_line else "Fehler konnte nicht automatisch klassifiziert werden."
                    if mods_found:
                        erkl += f"\n→ Beteiligte Mods: {', '.join(mods_found)}"
                    if count > 1:
                        erkl += f" (Trat {count}x auf)"

                    errors.append({
                        "kategorie": kategorie,
                        "datei": log_path.name,
                        "datum": mtime,
                        "titel": "Sonstiger Fehler",
                        "erklaerung": erkl,
                        "loesung": "Betroffenen Mod aktualisieren oder in der Sims 4 Community nach dem Fehler fragen.",
                        "schwere": "unbekannt",
                        "betroffene_mods": mods_found,
                        "raw_snippet": snippet,
                        "anzahl": count,
                        "total_reports": total_reports,
                        "be_advice": be_advice if be_advice else None,
                    })

        elif is_ww_log:
            # WickedWhims-Logformat: Plain-Text mit Tracebacks
            # Einzelne Fehlerblöcke splitten
            blocks = re.split(r'(?=Game Version:.*WickedWhims Version:)', content)
            block_counter: Counter[str] = Counter()
            unique_blocks: dict[str, str] = {}
            for block in blocks:
                if not block.strip():
                    continue
                # Normalisierungs-Key: Fehlertyp + letzte Zeile
                lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
                error_line = ""
                for l in reversed(lines):
                    if any(kw in l for kw in ["Error:", "Error ", "Failed"]):
                        error_line = l[:200]
                        break
                bkey = error_line if error_line else (lines[-1][:200] if lines else "")
                block_counter[bkey] += 1
                if bkey not in unique_blocks:
                    unique_blocks[bkey] = block

            for bkey, block in unique_blocks.items():
                count = block_counter[bkey]
                mods_found = _extract_mods_from_traceback(block)
                snippet = _extract_traceback_snippet(block)

                # WW-Version aus Header
                ww_ver_m = re.search(r'WickedWhims Version:\s*(v\w+)', block)
                ww_version = ww_ver_m.group(1) if ww_ver_m else ""

                matched = False
                for pat in WW_PATTERNS:
                    mp = re.search(pat["regex"], block, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if mp:
                        groups = mp.groups()
                        erklaerung = pat["erklaerung"]
                        for i, g in enumerate(groups, 1):
                            erklaerung = erklaerung.replace(f"{{{i}}}", str(g) if g else "?")
                        if ww_version:
                            erklaerung += f" (WW {ww_version})"
                        if mods_found:
                            erklaerung += f"\n→ Beteiligte Mods: {', '.join(mods_found)}"
                        if count > 1:
                            erklaerung += f" (Trat {count}x auf)"

                        key = f"WW|{pat['titel']}|{bkey[:60]}|{log_path.name}"
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
                            "betroffene_mods": mods_found,
                            "raw_snippet": snippet,
                            "anzahl": count,
                        })
                        matched = True
                        break

                if not matched:
                    # Allgemeine Python-Patterns versuchen
                    for pat in PYTHON_PATTERNS:
                        mp = re.search(pat["regex"], block, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if mp:
                            groups = mp.groups()
                            erklaerung = pat["erklaerung"]
                            for i, g in enumerate(groups, 1):
                                erklaerung = erklaerung.replace(f"{{{i}}}", str(g) if g else "?")
                            if ww_version:
                                erklaerung += f" (WW {ww_version})"
                            if mods_found:
                                erklaerung += f"\n→ Beteiligte Mods: {', '.join(mods_found)}"
                            if count > 1:
                                erklaerung += f" (Trat {count}x auf)"

                            key = f"WW2|{pat['titel']}|{bkey[:60]}|{log_path.name}"
                            if key in seen_keys:
                                continue
                            seen_keys.add(key)

                            errors.append({
                                "kategorie": kategorie,
                                "datei": log_path.name,
                                "datum": mtime,
                                "titel": f"WickedWhims: {pat['titel']}",
                                "erklaerung": erklaerung,
                                "loesung": pat["loesung"],
                                "schwere": pat["schwere"],
                                "betroffene_mods": mods_found,
                                "raw_snippet": snippet,
                                "anzahl": count,
                            })
                            matched = True
                            break

                if not matched:
                    key = f"WW_UNK|{bkey[:80]}|{log_path.name}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    erkl = bkey if bkey else "WickedWhims-Fehler konnte nicht klassifiziert werden."
                    if mods_found:
                        erkl += f"\n→ Beteiligte Mods: {', '.join(mods_found)}"
                    if count > 1:
                        erkl += f" (Trat {count}x auf)"
                    errors.append({
                        "kategorie": kategorie,
                        "datei": log_path.name,
                        "datum": mtime,
                        "titel": "WickedWhims: Sonstiger Fehler",
                        "erklaerung": erkl,
                        "loesung": "WickedWhims und zugehörige Mods aktualisieren.",
                        "schwere": "unbekannt",
                        "betroffene_mods": mods_found,
                        "raw_snippet": snippet,
                        "anzahl": count,
                    })

        else:
            # Mod-Logs oder sonstige Text-Dateien
            mod_files_found: set[str] = set()
            for i, line in enumerate(content.splitlines()):
                if i >= 500:
                    break
                ts4_matches = re.findall(r'[\w\-\.]+\.ts4script', line, re.IGNORECASE)
                mod_files_found.update(ts4_matches)
                pkg_matches = re.findall(r'[\w\-\.]+\.package', line, re.IGNORECASE)
                mod_files_found.update(pkg_matches)

            # Auch Mod-Namen aus Pfaden
            mods_from_path = _extract_mods_from_traceback(content[:50000])
            all_mods = sorted(set(list(mod_files_found) + mods_from_path))

            matched = False
            for pat in ALL_PYTHON_PATTERNS:
                mp = re.search(pat["regex"], content, re.IGNORECASE)
                if mp:
                    groups = mp.groups()
                    erklaerung = pat["erklaerung"]
                    for i, g in enumerate(groups, 1):
                        erklaerung = erklaerung.replace(f"{{{i}}}", str(g) if g else "?")
                    if all_mods:
                        erklaerung += f"\n→ Beteiligte Mods: {', '.join(all_mods[:10])}"

                    key = f"TXT|{pat['titel']}|{log_path.name}"
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
                        "betroffene_mods": all_mods,
                        "raw_snippet": _extract_traceback_snippet(content),
                    })
                    matched = True

            if not matched and ("error" in content.lower() or "exception" in content.lower()):
                first_error = ""
                for line in content.splitlines():
                    line_stripped = line.strip()
                    if any(kw in line_stripped.lower() for kw in ["error", "exception", "traceback"]):
                        first_error = line_stripped[:300]
                        break

                key = f"TXT_UNK|{log_path.name}|{first_error[:80]}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    errors.append({
                        "kategorie": kategorie,
                        "datei": log_path.name,
                        "datum": mtime,
                        "titel": "Sonstiger Fehler",
                        "erklaerung": first_error if first_error else "Ein Fehler wurde erkannt, konnte aber nicht automatisch klassifiziert werden.",
                        "loesung": "Betroffenen Mod aktualisieren oder in der Sims 4 Community nach dem Fehler fragen.",
                        "schwere": "unbekannt",
                        "betroffene_mods": all_mods,
                        "raw_snippet": _extract_traceback_snippet(content),
                    })

    schwere_order = {"hoch": 0, "mittel": 1, "niedrig": 2, "unbekannt": 3}
    errors.sort(key=lambda e: (schwere_order.get(e["schwere"], 99), e.get("datei", "")))

    return errors
