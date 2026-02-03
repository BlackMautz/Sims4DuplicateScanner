# Sims4 Duplicate Scanner

Ein Werkzeug zum Finden und Entfernen doppelter Sims 4 Mod-Dateien.

## Features

- 🔍 Doppelte Dateien nach **Namen** und **Inhalt (SHA-256)** erkennen
- 📦 **Batch-Quarantäne** oder **Batch-Löschen** mit Checkboxen
- 🌐 **Web-UI** zur Verwaltung (localhost)
- 💾 **ZIP-Backups** mit Live-Progress (optional, vor Aktionen empfohlen)
- 📋 **CSV-Logging** aller Aktionen
- 🔗 Ignoriert **Symlinks/Junctions** automatisch
- ✨ **EXE-Version** ohne Python-Installation

## Installation & Verwendung

### Option 1: EXE direkt verwenden (einfach)
1. Download die neueste `Sims4DuplicateScanner.exe` aus den [Releases](../../releases)
2. Doppelklick → fertig! (Keine Python-Installation nötig)

### Option 2: Aus Quellcode starten (für Entwickler)

1. **Python 3.13+ installieren**
   ```bash
   winget install Python.Python.3.13
   ```

2. **Repository klonen**
   ```bash
   git clone https://github.com/dein-username/sims4-duplicate-scanner.git
   cd sims4-duplicate-scanner
   ```

3. **Starten** (keine zusätzlichen Pakete nötig!)
   ```bash
   python sims4_duplicate_scanner.py
   ```

### Option 3: Eigene EXE bauen

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Sims4DuplicateScanner" sims4_duplicate_scanner.py
# EXE erscheint in: dist/Sims4DuplicateScanner.exe
```

> Tipp: `requirements.txt` ist optional – nur falls du PyInstaller brauchst.

## Verwendung

1. **Ordner hinzufügen**: Sims 4 Mod-Ordner in der GUI eintragen
2. **Backup erstellen** (optional): "📦 Backup erstellen" Button drücken
3. **Scan starten**: "Scan & Web-UI öffnen" drücken
4. **Duplikate prüfen**: In der Web-UI überprüfen
5. **Aktion durchführen**: 
   - Checkboxen setzen
   - "Ausgewählte quarantäne" oder "Ausgewählte löschen"

## Quarantäne-Ordner & Logs

- Quarantäne: `_sims4_quarantine/` (im Scan-Verzeichnis)
- Aktions-Log: `_sims4_actions.log.txt`
- CSV-Export: `_sims4_actions.csv`

## Wie es funktioniert

### Duplikat-Erkennung

**Nach Namen:**
- Findet alle Dateien mit gleichen Namen + Größe
- Gruppiert diese zusammen

**Nach Inhalt (SHA-256):**
- Berechnet Hash der gesamten Datei (100% byte-identisch)
- Findet Dateien mit identischem Inhalt (auch mit unterschiedlichen Namen)
- ⚠️ Das ist **exakt**, keine "ähnlich"-Erkennung!

### Datei-Filter

**Scannt standardmäßig nur:**
- `.package` (Sims 4 Package-Dateien)
- `.ts4script` (Sims 4 Script Mods)

Du kannst die Extensions in der GUI anpassen!

**Ignoriert automatisch:**
- Symlinks & Junctions (z.B. `mklink /J`)
- Ordner wie `__pycache__`, `cache`, `thumbnails`

### Batch-Operationen

**"Ausgewählte quarantäne / löschen":**
- Betrifft nur Dateien mit Checkbox ✓

**"Rest in Quarantäne / Rest löschen":**
- Betrifft alle **anderen** Dateien in der Gruppe
- **Behält immer 1 Original-Datei** (sicher!)
- Moves/Deletes den Rest

### Ordnerspeicherung & Config

**GUI speichert deine Einstellungen:**
- **Windows:** `%APPDATA%\Sims4DupeScanner\sims4_duplicate_scanner_config.json`
- Ordner, Filter, Einstellungen persistent

**EXE speichert:**
- Im **selben Verzeichnis wie die EXE**
- Falls du die EXE verschiebst → neue Config!

### Logs & Audit Trail

**_sims4_actions.csv** speichert:
| Spalte | Inhalt |
|--------|--------|
| Timestamp | Wann die Aktion erfolgte |
| Action | QUARANTINE, DELETE, etc. |
| Size (Bytes) | Dateigröße in Bytes |
| Size (Human) | Lesbar (z.B. 2.5 MB) |
| Path | Vollständiger Dateipfad |
| Status | SUCCESS, FAILED, etc. |
| Note | Details (z.B. Fehler) |

→ Datei liegt in: `_sims4_quarantine/_sims4_actions.csv`

### Backup

**ZIP-Struktur:**
- Erhält die **Ordnerstruktur ab dem Scan-Verzeichnis**
- Wenn du `/Mods/Folder/subfolder/file.package` scannst → wird gespeichert als `Folder/subfolder/file.package` im ZIP
- Später problemlos extrahierbar zur Wiederherstellung

**Zeitstempel im Namen:**
- Format: `sims4_backup_YYYYMMDD_HHMMSS.zip`
- Bsp: `sims4_backup_20260203_135204.zip`

## Notes

⚠️ **Backup empfohlen!** Nutze die "📦 Backup erstellen" Button, um einen ZIP vor Aktionen zu erstellen.

📌 **Symlinks/Junctions**: Werden automatisch ignoriert, um keine falschen Duplikate zu zählen.

## Lizenz

MIT License
