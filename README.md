# 🔍 Sims 4 Duplicate Scanner

Ein leistungsstarkes Werkzeug zum Finden, Vergleichen und Entfernen doppelter Sims 4 Mod-Dateien — mit moderner Web-UI.

## ✨ Features

- 🔍 **Duplikat-Erkennung** nach Dateiname, Größe und Inhalt (SHA-256)
- 📦 **DBPF-Tiefenanalyse** — liest .package-Dateien und zeigt interne Ressourcen
- 🖼️ **Thumbnail-Vorschau** — extrahiert und zeigt Vorschaubilder direkt aus .package-Dateien (DDS/PNG)
- 🖼️ **Bilder-Vergleich** — alle Versionen einer Mod nebeneinander vergleichen
- 📂 **Kategorisierung** — automatische Erkennung von CAS, Build/Buy, Tuning, Script etc.
- 📊 **Statistiken** — Übersicht über Mod-Typen, Größen und Duplikat-Gruppen
- 🗑️ **Batch-Operationen** — Quarantäne oder Löschen per Checkbox
- 💾 **ZIP-Backup** — Sicherung vor Aktionen mit Live-Progress
- 📋 **CSV-Logging** — vollständiger Audit-Trail aller Aktionen
- 🔗 **Symlink-Erkennung** — ignoriert Junctions/Symlinks automatisch
- 📁 **Alle Mods anzeigen** — komplette Mod-Bibliothek durchsuchen und filtern
- 📜 **Scan-Historie** — vergangene Scans vergleichen (Änderungen, neue/entfernte Dateien)
- 🌐 **Web-UI** — schönes responsives Interface im Browser (localhost)
- 🖥️ **Tkinter-GUI** — native Windows-Oberfläche für Einstellungen und Scan-Start
- 🔒 **100% Offline** — keine Daten werden gesendet, alles lokal
- ✨ **Einzelne EXE** — kein Python nötig, einfach Doppelklick

## 📥 Installation & Verwendung

### Option 1: EXE direkt verwenden (empfohlen)

1. Die neueste `Sims4DuplicateScanner.exe` aus den [Releases](https://github.com/BlackMautz/Sims4DuplicateScanner/releases) herunterladen
2. Doppelklick → fertig! (Keine Python-Installation nötig)

> ⚠️ Windows Defender oder euer Antivirus könnten beim ersten Start warnen — das ist normal bei selbst erstellten .exe-Dateien. Das Tool ist Open Source und sicher.

### Option 2: Aus Quellcode starten

```bash
# Python 3.10+ installieren
git clone https://github.com/BlackMautz/Sims4DuplicateScanner.git
cd Sims4DuplicateScanner
python sims4_duplicate_scanner.py
```

> Keine zusätzlichen Pakete nötig — nur Python-Standardbibliotheken!

### Option 3: Eigene EXE bauen

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Sims4DuplicateScanner" sims4_duplicate_scanner.py
# EXE erscheint in: dist/Sims4DuplicateScanner.exe
```

## 🎮 Verwendung

1. **Ordner wählen**: Sims 4 Mods-Ordner in der GUI eintragen
2. **Backup erstellen** (optional): "📦 Backup erstellen" Button drücken
3. **Scan starten**: "Scan & Web-UI öffnen" drücken
4. **Duplikate prüfen**: In der Web-UI Ergebnisse durchsehen
5. **Thumbnails vergleichen**: Auf Vorschaubilder klicken für Gruppen-Vergleich
6. **Aktion durchführen**: Checkboxen setzen → Quarantäne oder Löschen

## 🔬 Wie es funktioniert

### Duplikat-Erkennung
- **Nach Namen**: Findet Dateien mit gleichen Namen + Größe
- **Nach Inhalt (SHA-256)**: Findet byte-identische Dateien (auch unterschiedlich benannt)

### DBPF-Tiefenanalyse
- Liest das DBPF-Containerformat der .package-Dateien
- Zeigt interne Ressource-Typen (CAS Parts, Objects, Tuning XML, etc.)
- Extrahiert eingebettete Thumbnails (DDS/PNG → Browser-kompatibles Format)
- Ergebnis wird gecacht für schnelle Wiederholungs-Scans

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

### Datei-Filter
Scannt standardmäßig: `.package`, `.ts4script`
Ignoriert automatisch: Symlinks, Junctions, `__pycache__`, Cache-Ordner

## 📁 Dateien & Konfiguration

| Datei | Beschreibung |
|-------|-------------|
| `%APPDATA%\Sims4DupeScanner\sims4_duplicate_scanner_config.json` | Gespeicherte Einstellungen |
| `%APPDATA%\Sims4DupeScanner\dbpf_deep_cache.json` | DBPF-Analyse-Cache |
| `_sims4_quarantine/` | Quarantäne-Ordner (im Scan-Verzeichnis) |
| `_sims4_actions.csv` | Aktions-Log als CSV |

## ⚠️ Hinweise

- **Backup empfohlen!** Nutze den "📦 Backup erstellen" Button vor Löschaktionen
- **Symlinks/Junctions** werden automatisch ignoriert
- **Quarantäne** verschiebt Dateien statt sie zu löschen — sicherer als direktes Löschen
- **100% lokal** — keine Internet-Verbindung nötig, keine Daten werden gesendet

## 📜 Lizenz

MIT License — siehe [LICENSE](LICENSE)
