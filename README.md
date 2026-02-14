# 🔍 Sims 4 Duplicate Scanner

Ein leistungsstarkes All-in-One-Werkzeug für Die Sims 4 — Mod-Verwaltung, Spielstand-Analyse und Sim-Datenbank mit moderner Web-UI.

---

## 🆕 Was ist neu in v3.0.0?

### 🏗️ Komplettes Refactoring
- **Monolith aufgelöst** — von einer einzelnen 10.000-Zeilen-Datei auf saubere Modul-Struktur (`sims4_scanner/`) umgebaut
- **20 Code-Quality-Fixes** — Sicherheit, Error Handling, Input-Validierung
- **14 Performance-Optimierungen** — Caching, Lazy Loading, parallele Verarbeitung

### 🧬 Spielstand-Analyse (NEU!)
- **Alle Sims auslesen** — Name, Alter, Geschlecht, Hautton, Spezies
- **Wohnort/Welt** — jeder Sim wird seiner Welt zugeordnet (Willow Creek, Tomarang, Ondarion, etc.)
- **Alle 30+ Welten** unterstützt, inkl. neuer DLCs (Chestnut Ridge, Ciudad Enamorada, Ravenwood, Nordhaven, Innisgreen, Gibbi Point, Ondarion)
- **Haushalt & Beziehungen** — Partner, Familien-Rollen (Eltern, Kinder, Singles)
- **Stimmung** — aktuelle Laune mit Emoji (😄 Glücklich, 😢 Traurig, 😡 Wütend, etc.)
- **Skills** — alle erlernten Fähigkeiten mit Level
- **Charaktereigenschaften** — Traits mit deutscher Übersetzung
- **Okkult-Erkennung** — Vampir, Werwolf, Fee, Meerjungfrau, Alien, Hexe, etc.
- **Spezies** — Mensch, Hund, Katze, Fuchs, Pferd, Kleintier
- **Portraits** — automatischer Download aus dem Sims Wiki
- **Duplikat-Sims** — findet doppelte Sims über alle Spielstände
- **Statistiken** — Altersverteilung, Geschlecht, Spezies, Hautton, Welten-Übersicht
- **Deutsch/Englisch** — automatische Namensübersetzung (z.B. "Bella Goth" ↔ "Bella Grusel")

### 🌐 Verbesserte Web-UI
- **Filter** — nach Alter, Geschlecht, Welt, Spezies, Okkult-Typ
- **Volltextsuche** — über alle Sims und Mods
- **Sortierung** — nach allen Feldern
- **Sim-Karten** — mit Portrait, Details und Tags
- **Welt-Tags** — farbige Badges zeigen die Welt jedes Sims

---

## ✨ Alle Features

### 🔍 Mod-Scanner
- **Duplikat-Erkennung** nach Dateiname, Größe und Inhalt (SHA-256)
- **DBPF-Tiefenanalyse** — liest .package-Dateien und zeigt interne Ressourcen
- **Thumbnail-Vorschau** — extrahiert Vorschaubilder direkt aus .package-Dateien
- **Bilder-Vergleich** — alle Versionen einer Mod nebeneinander
- **Kategorisierung** — CAS, Build/Buy, Tuning, Script, UI, Animation, Audio
- **Batch-Operationen** — Quarantäne oder Löschen per Checkbox
- **ZIP-Backup** — Sicherung vor Aktionen mit Live-Progress
- **CSV-Logging** — vollständiger Audit-Trail
- **Scan-Historie** — vergangene Scans vergleichen
- **CurseForge-Integration** — erkennt über CurseForge installierte Mods

### 🧬 Spielstand-Analyse
- **Automatische Erkennung** — findet alle Spielstände im Sims 4 Ordner
- **DBPF + Protobuf Parsing** — liest die .save-Dateien direkt
- **QFS-Dekompression** — EA's proprietäres Kompressionsformat
- **Disk-Cache** — einmal analysiert, sofort verfügbar
- **Alle 395+ Sims** in einem typischen Spielstand

### 📊 Statistiken & Übersichten
- Mod-Aktivitäts-Heatmap (GitHub-Style, letzte 365 Tage)
- Altersverteilung, Geschlechterverteilung
- Spezies-Statistiken, Hautton-Verteilung
- Welten-Übersicht mit Sim-Anzahl pro Welt
- Haushalts-Gruppierung

### 🛠️ Weitere Features
- 🐛 **Bug Report System** — automatische Analyse mit HTML-Report an Discord
- 📖 **Interaktives Tutorial** — Schritt-für-Schritt beim ersten Start
- 💬 **Discord Support** — schwebender Support-Button
- ☕ **Buy me a Coffee** — Unterstützungs-Link
- 🔄 **Auto-Update Check** — prüft auf neue Versionen (GitHub Releases)
- 🔒 **100% Offline** — keine Daten werden gesendet (außer Update-Check & Bug-Reports, nur mit User-Klick)
- ✨ **Einzelne EXE** — kein Python nötig, einfach Doppelklick

---

## 📥 Installation & Verwendung

### Option 1: EXE direkt verwenden (empfohlen)

1. Die neueste `Sims4DuplicateScanner.exe` aus den [Releases](https://github.com/BlackMautz/Sims4DuplicateScanner/releases) herunterladen
2. Doppelklick → fertig! (Keine Python-Installation nötig)

> ⚠️ Windows Defender oder euer Antivirus könnten beim ersten Start warnen — das ist normal bei selbst erstellten .exe-Dateien. Das Tool ist Open Source und sicher.

### Option 2: Aus Quellcode starten

```bash
git clone https://github.com/BlackMautz/Sims4DuplicateScanner.git
cd Sims4DuplicateScanner
python sims4_duplicate_scanner.py
```

> Keine zusätzlichen Pakete nötig — nur Python-Standardbibliotheken!

### Option 3: Eigene EXE bauen

```bash
pip install pyinstaller
pyinstaller Sims4DuplicateScanner.spec --noconfirm
# EXE erscheint in: dist/Sims4DuplicateScanner.exe
```

---

## 🎮 Verwendung

### Mod-Scanner
1. **Ordner wählen**: Sims 4 Mods-Ordner in der GUI eintragen
2. **Backup erstellen** (optional): "📦 Backup erstellen" Button drücken
3. **Scan starten**: "Scan & Web-UI öffnen" drücken
4. **Duplikate prüfen**: In der Web-UI Ergebnisse durchsehen
5. **Aktion durchführen**: Checkboxen setzen → Quarantäne oder Löschen

### Spielstand-Analyse
1. Wird automatisch erkannt und im Hintergrund analysiert
2. In der Web-UI auf "Sims" klicken
3. Alle Sims durchsuchen, filtern und sortieren
4. Portraits werden automatisch aus dem Sims Wiki geladen

---

## 🔬 Technische Details

### DBPF-Parsing
- Liest das DBPF v2.1 Containerformat (Index-Flags, konstante Felder)
- QFS/RefPack-Dekompression für EA's proprietäres Format
- Ressource-Typen: CAS Parts, Objects, Tuning XML, Thumbnails

### Protobuf-Parsing
- Eigener leichtgewichtiger Protobuf-Decoder (kein protoc/protobuf-Library nötig)
- Felder: varint, fixed32, fixed64, length-delimited (bytes)
- Verschachtelte Strukturen: Zone → Nachbarschaften → Lots → Households → Sims

### REGION_ID_MAP
Neuere DLC-Welten speichern keinen Namen im Protobuf. Diese werden über ihre Region-ID identifiziert:

| Region-ID | Welt | DLC |
|-----------|------|-----|
| 329915 | Chestnut Ridge | Horse Ranch |
| 359471 | Tomarang | For Rent |
| 395690 | Ciudad Enamorada | Lovestruck |
| 415482 | Ravenwood | Life & Death |
| 417419 | Nordhaven | Businesses & Hobbies |
| 455807 | Innisgreen | Enchanted by Nature |
| 474272 | Gibbi Point | Adventure Awaits |
| 487001 | Ondarion | Royalty & Legacy |

### Kategorisierung

| Kategorie | Beschreibung |
|-----------|-------------|
| CAS | Create-a-Sim Inhalte (Kleidung, Haare, etc.) |
| Build/Buy | Bau- und Kaufmodus-Objekte |
| Tuning | Gameplay-Modifikationen (XML) |
| Script | Python-Script-Mods (.ts4script) |
| UI/Strings | Interface-Texte und Übersetzungen |
| Animation | Animationen und Clips |
| Audio | Sound-Dateien |
| Mixed | Gemischte Inhalte |

---

## 📁 Projekt-Struktur

```
sims4_duplicate_scanner.py    # Einstiegspunkt (Thin Wrapper)
sims4_scanner/                # Hauptmodul
├── __init__.py
├── app.py                    # Hauptlogik & Tkinter-GUI
├── server.py                 # HTTP-Server (Web-UI)
├── savegame.py               # Spielstand-Analyse (DBPF/Protobuf)
├── scanner.py                # Mod-Scanner & Duplikat-Erkennung
├── config.py                 # Konfiguration & Cache
├── constants.py              # Konstanten & Mappings
├── protobuf.py               # Protobuf-Parser
├── name_translation.py       # DE/EN Namensübersetzung
├── wiki_portraits.py         # Wiki-Portrait-Download
└── web/
    └── template.py           # HTML/CSS/JS Web-UI Template
```

## 📁 Dateien & Konfiguration

| Datei | Beschreibung |
|-------|-------------|
| `%APPDATA%\Sims4DupeScanner\sims4_duplicate_scanner_config.json` | Gespeicherte Einstellungen |
| `%APPDATA%\Sims4DupeScanner\dbpf_deep_cache.json` | DBPF-Analyse-Cache |
| `%APPDATA%\Sims4DupeScanner\savegame_cache.json` | Spielstand-Cache |
| `_sims4_quarantine/` | Quarantäne-Ordner (im Scan-Verzeichnis) |
| `_sims4_actions.csv` | Aktions-Log als CSV |

---

## ⚠️ Hinweise

- **Backup empfohlen!** Nutze den "📦 Backup erstellen" Button vor Löschaktionen
- **Symlinks/Junctions** werden automatisch ignoriert
- **Quarantäne** verschiebt Dateien statt sie zu löschen — sicherer als direktes Löschen
- **100% lokal** — keine Internet-Verbindung nötig, keine Daten werden gesendet

## 💬 Support & Community

- **Discord**: [discord.gg/HWWEr7pQpR](https://discord.gg/HWWEr7pQpR)
- **GitHub Issues**: [Issues](https://github.com/BlackMautz/Sims4DuplicateScanner/issues)
- **Buy me a Coffee**: [buymeacoffee.com/MrBlackMautz](https://buymeacoffee.com/MrBlackMautz)

## 📜 Lizenz

MIT License — siehe [LICENSE](LICENSE)
