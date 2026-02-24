# 🔍 Sims 4 Duplicate Scanner

Ein leistungsstarkes All-in-One-Werkzeug für Die Sims 4 — Mod-Verwaltung, Spielstand-Analyse und Sim-Datenbank mit moderner Web-UI.

---

## 🆕 Was ist neu in v3.5.0?

### 🧬 Character Sheet — RPG-Stil Sim-Steckbrief
- **Vollbild-Modal** — Klick auf einen Sim öffnet ein detailliertes Character Sheet im RPG-Stil
- **Fähigkeiten-Balken** — alle erlernten Skills mit Level und Fortschrittsbalken
- **Vitalwerte** — Bedürfnisse (Hunger, Energie, Spaß, etc.) als farbige Balken (grün/gelb/rot)
- **Ausrüstungs-Grid** — CC-Mods des Sims als visuelles Emoji-Grid mit Thumbnails
- **CC-Thumbnails** — Vorschaubilder werden direkt aus .package-Dateien extrahiert und angezeigt

### 🧠 Deutsche Trait-Namen
- **139 Eigenschaften** mit korrekten deutschen Namen (z.B. „Kreativ", „Romantisch")
- **Geschlechts-abhängig** — weibliche Formen wo nötig (z.B. „Romantische" statt „Romantisch")
- **Persönlichkeit, Bonus & Aspiration** — getrennte Kategorien mit Emoji-Chips (🧠 ⭐ 🌟)

### 💼 Deutsche Karriere-Namen
- **~100 Karrieren** mit deutschen Namen (z.B. „Astronaut", „Meisterkoch", „Technik-Guru")
- **Karriere-Level** — Stufe 1-10 wird auf der Sim-Karte und im Character Sheet angezeigt
- **Geschlechts-abhängig** — z.B. „Astronautin" vs. „Astronaut"

### ❤️ Vorlieben & Abneigungen
- **258 Vorlieben/Abneigungen** aus dem Spielstand extrahiert und mit deutschen Namen angezeigt
- **7 Kategorien** — Farbe (🎨), Deko (🏠), Musik (🎵), Aktivitäten (🎯), Mode (👗), Eigenschaft (💭), Kommunikation (💬)
- **Kategorie-gruppiert** — übersichtliche Darstellung im Character Sheet nach Kategorie sortiert

### 🤝 Beziehungs-Details
- **Freundschafts-Stufen** — Bekannt → Freunde → Gute Freunde → Beste Freunde
- **Romantik-Stufen** — Erster Kuss → Freund/Freundin → Verlobt → Verheiratet → Seelenverwandte
- **Familien-Typen** — Elternteil, Kind, Großelternteil, Enkelkind, Geschwister, Schwieger-Beziehungen
- **Asymmetrische Erkennung** — Eric → Vivian = „Elternteil", Vivian → Eric = „Kind"
- **Kompatibilität** — Toll (⭐), Gut (👍), Schlecht (⚡)
- **Farbcodierte Tags** — Familie (lila), Romantik (pink), Freundschaft (blau), Kompatibilität (gold)
- **Scrollbarer Container** — alle Beziehungen sichtbar, kein Limit

### 🎨 Hautton-Konflikte
- **Skin-Mod-Erkennung** — findet CC-Mods die Standard-Hauttöne überschreiben
- **Konflikt-Analyse** — zeigt welche Skin-Mods sich gegenseitig beeinflussen

### 🖼️ Portrait-System verbessert
- **Batch-Prefetch** — Wiki-Portraits werden parallel vorgeladen (schnellerer Start)
- **Negative-Cache auf Disk** — Sims ohne Wiki-Bild werden nicht erneut gesucht
- **Thread-sicherer Index** — Portrait-Index wird nur einmal aufgebaut

### ⚡ Performance
- **Tray-Parsing parallelisiert** — Package-Dateien werden parallel gelesen
- **Thumbnail-Schnellextraktion** — `extract_thumbnail_fast()` für CC-Vorschaubilder
- **+2.700 neue Zeilen** Code, 8 Dateien geändert

---

## 📋 Was war neu in v3.2.0?

### 🎮 Sims 4 Loading Screen
- **3D-Plumbob** — echter Sims 4 Ladebildschirm mit rotierendem 3D-Plumbob (Three.js WebGL)
- **Animierter Fortschritt** — Ladebalken zeigt den Scan-Fortschritt in Echtzeit
- **Rotierende Tipps** — wechselnde Lade-Nachrichten im Sims-Stil („Retikuliere Splines…“)
- **Skip-Button** — Ladebildschirm kann jederzeit übersprungen werden

### 🛡️ Maximale Sicherheit — Quarantäne-First
- **Niemals sofort löschen** — ALLE Aktionen verschieben Dateien zuerst in die Quarantäne, nichts wird direkt gelöscht
- **Endgültig löschen nur im Quarantäne-Tab** — permanentes Löschen ist nur noch aus der Quarantäne-Ansicht möglich
- **Lösch-Buttons entfernt** — alle „🗑 Löschen“-Buttons aus der gesamten UI entfernt, nur noch „📦 Quarantäne“
- **Batch-Aktionen nur Quarantäne** — Massen-Aktionen verschieben immer in Quarantäne
- **Server-Sicherung** — auch auf Backend-Ebene führt `delete` intern eine Quarantäne-Verschiebung durch

### 🗂️ Tray-Cleaner Fix (kritischer Bug behoben)
- **Instance-ID Gruppierung** — vorher wurden Tray-Dateien falsch nach vollem Dateinamen gruppiert, was zu 81% Fehlerkennungen führte
- **Quarantäne statt Löschen** — Tray-Cleaner verschiebt jetzt in Quarantäne statt direkt zu löschen
- **Fehlende Dateitypen** — .hhi, .sgi, .rmi werden jetzt auch erkannt

---

## 📋 Was war neu in v3.1.0?

### 🛡️ Sicherheit & Benutzerfreundlichkeit
- **Dashboard-Sicherheitshinweis** — beim Start wird klar erklärt: 📦 Quarantäne = SICHER (rückgängig machbar), 🗑️ Löschen = ENDGÜLTIG
- **Bestätigungsdialoge überarbeitet** — jede Lösch-Aktion warnt deutlich vor Datenverlust und empfiehlt Quarantäne
- **Quarantäne-Bestätigung** — zeigt Dateinamen und erklärt, dass Dateien jederzeit zurückgeholt werden können
- **Batch-Sicherheit** — Massen-Aktionen mit klaren Warnungen und Sicherheitstipps
- **Tutorial** — zeigt sich beim ersten Start automatisch (nicht mehr vorausgewählt)

### 🔬 Script-Mod-Prüfung (komplett neu)
- **Schweregrad-System** — jedes Muster wird als 🔴 Kritisch, 🟠 Hoch, 🟡 Mittel oder 🟢 Niedrig eingestuft
- **Verständliche Erklärungen** — jeder Fund wird in einfacher Sprache erklärt (was macht das Muster? Warum wurde es gefunden?)
- **Bekannte Mods** — MCCC, WickedWhims, UI Cheats, etc. werden automatisch erkannt und als ✅ sicher markiert
- **Empfehlungen** — pro Script-Mod individuelle Handlungsempfehlung
- **Quarantäne-Button** — unbekannte Mods können direkt in Quarantäne verschoben werden

### 🖼️ CC-Galerie verbessert
- **Alle Items auf einmal** — keine "Mehr laden"-Paginierung mehr, alle CC-Teile werden sofort angezeigt
- **Lazy-Loading** — Bilder werden erst beim Scrollen geladen (Performance bleibt gut)

### 📝 Alle Info-Texte überarbeitet
- **Tray-Cleaner** — erklärt jetzt verständlich, was der Tray-Ordner ist und was verwaiste Dateien sind
- **Script-Check** — erklärt was Script-Mods sind und dass ein Fund ≠ Gefahr bedeutet
- **Cache/Backup/Speicherplatz** — alle Erklärungen für Einsteiger umgeschrieben
- **Ergebnisanzeigen** — aussagekräftige Boxen statt kryptischer Listen

### ⚡ Performance & Stabilität
- **Tray-Index** — nur noch Instance-IDs statt voller Schlüssel (weniger RAM, schneller)
- **DBPF Safety-Cap** — Dateien mit >500.000 Einträgen werden übersprungen (Hang-Schutz)
- **Version im Konsolentitel** — Versionsnummer direkt sichtbar

---

## 📋 Was war neu in v3.0.0?

### 🏗️ Komplettes Refactoring
- **Monolith aufgelöst** — von einer einzelnen 10.000-Zeilen-Datei auf saubere Modul-Struktur (`sims4_scanner/`) umgebaut
- **20 Code-Quality-Fixes** — Sicherheit, Error Handling, Input-Validierung
- **14 Performance-Optimierungen** — Caching, Lazy Loading, parallele Verarbeitung

### 🧬 Spielstand-Analyse
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
- **Character Sheet** — RPG-Stil Steckbrief mit Skills, Vitalwerten, Traits, Karriere
- **139 deutsche Trait-Namen** — geschlechts-abhängig (Persönlichkeit, Bonus, Aspiration)
- **~100 deutsche Karriere-Namen** — mit Level-Anzeige (Stufe 1-10)
- **258 Vorlieben/Abneigungen** — 7 Kategorien mit deutschen Namen
- **Beziehungs-Details** — Freundschaft, Romantik, Familie, Kompatibilität mit farbigen Tags
- **CC-Thumbnails** — Vorschaubilder aus .package-Dateien extrahiert

### 📊 Statistiken & Übersichten
- Mod-Aktivitäts-Heatmap (GitHub-Style, letzte 365 Tage)
- Altersverteilung, Geschlechterverteilung
- Spezies-Statistiken, Hautton-Verteilung
- Welten-Übersicht mit Sim-Anzahl pro Welt
- Haushalts-Gruppierung

### �️ Sicherheit & UX
- **Quarantäne-First-Prinzip** — es wird niemals sofort etwas gelöscht, alle Aktionen verschieben in die Quarantäne
- **Endgültig löschen nur im Quarantäne-Tab** — permanentes Löschen ist nur aus der Quarantäne-Ansicht möglich
- **Dashboard-Sicherheitshinweis** — erklärt sofort beim Start: Quarantäne = sicher, alles wird nur verschoben
- **Bestätigungsdialoge** — klare Warnungen bei allen Quarantäne-Aktionen
- **Hilfe-Panel** — erreichbar über jede Seite, erklärt alle Funktionen
- **28 individuelle Tabs** — jede Funktion hat ihren eigenen Bereich
- **Dashboard Health Score** — Gesundheitsbewertung des Mods-Ordners auf einen Blick

### 🔬 Erweiterte Prüfungen
- **Script-Mod-Prüfung** — Schweregrad-System, bekannte Mods erkannt, verständliche Erklärungen
- **CC-Check** — prüft Custom Content auf Probleme
- **Broken CC Finder** — findet defekte/inkompatible CC-Dateien
- **Tray-Cleaner** — findet verwaiste Tray-Dateien (Galerie-Reste)
- **Speicherplatz-Analyse** — zeigt Ordnergrößen und die größten Dateien

### �🛠️ Weitere Features
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
├── skin_textures.py          # Hautton-/Skin-Textur-Analyse
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
