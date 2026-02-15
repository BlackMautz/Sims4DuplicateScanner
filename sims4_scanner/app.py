# -*- coding: utf-8 -*-
"""Tkinter-GUI (Hauptfenster) fuer den Sims 4 Duplicate Scanner."""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .constants import SCANNER_VERSION
from .config import load_config, save_config, load_deep_cache, save_deep_cache
from .utils import normalize_exts, normalize_ignore_dirs, human_size
from .scanner import scan_duplicates
from .dataset import Dataset
from .server import LocalServer
from .errors import find_sims4_userdir
from .tray import analyze_tray, build_mod_instance_index
from .update import check_for_update, download_update, apply_update_and_restart
from .history import save_scan_history, save_mod_snapshot

print(f"\n  Sims4 Duplicate Scanner v{SCANNER_VERSION}", flush=True)
print(f"  Python {sys.version.split()[0]}\n", flush=True)


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
        self.var_do_conflicts = tk.BooleanVar(value=True)

        self.var_add_path = tk.StringVar(value="")
        self.var_sims4_dir = tk.StringVar(value="")
        self.var_cf_path = tk.StringVar(value="")
        self.var_status = tk.StringVar(value="Bereit.")
        self.var_detail = tk.StringVar(value="")
        self.var_minimize_on_close = tk.BooleanVar(value=True)

        self.server: LocalServer | None = None
        self.listbox = None
        self.progress = None
        self.btn_run = None
        self._minimized_to_tray = False

        self._build_ui()
        self._load_config_into_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Map>", self._on_map)

        # Auto-Update Check im Hintergrund
        self._update_banner_frame = None
        self._update_info = None
        threading.Thread(target=self._check_update_bg, daemon=True).start()

    # ------------------------------------------------------------------
    # Update-Banner + Auto-Update
    # ------------------------------------------------------------------
    def _check_update_bg(self):
        """Prueft im Hintergrund auf Updates und startet ggf. Auto-Update."""
        try:
            info = check_for_update(timeout=6.0)
            if info.get("available"):
                self._update_info = info
                dl_url = info.get("download_url", "")
                if dl_url and getattr(sys, 'frozen', False):
                    # Auto-Update: direkt herunterladen
                    self.after(0, lambda: self._start_auto_update(info))
                else:
                    # Fallback: Banner mit Link (z.B. im Dev-Modus oder keine EXE im Release)
                    self.after(0, lambda: self._show_update_banner(info))
        except Exception:
            pass

    def _start_auto_update(self, info: dict):
        """Zeigt Download-Banner und startet den Download im Hintergrund."""
        if self._update_banner_frame:
            return
        f = tk.Frame(self, bg="#2563eb", cursor="arrow")
        f.pack(fill="x", before=list(self.winfo_children())[0])

        self._update_lbl = tk.Label(f,
            text=f"\u2b07  Lade Update v{info.get('latest', '?')} herunter...",
            bg="#2563eb", fg="white", font=("Segoe UI", 11, "bold"), pady=6)
        self._update_lbl.pack(side="left", padx=(12, 0))

        self._update_progress = tk.Label(f, text="0%", bg="#2563eb", fg="#93c5fd",
                                         font=("Segoe UI", 10), pady=6)
        self._update_progress.pack(side="left", padx=(8, 0))

        self._update_banner_frame = f

        threading.Thread(target=self._do_auto_update, args=(info,), daemon=True).start()

    def _do_auto_update(self, info: dict):
        """Download + Apply im Hintergrund-Thread."""
        try:
            dl_url = info.get("download_url", "")

            def on_progress(downloaded, total):
                if total > 0:
                    pct = int(downloaded * 100 / total)
                    mb = downloaded / 1048576
                    total_mb = total / 1048576
                    txt = f"{pct}%  ({mb:.1f} / {total_mb:.1f} MB)"
                else:
                    mb = downloaded / 1048576
                    txt = f"{mb:.1f} MB"
                self.after(0, lambda t=txt: self._update_progress.config(text=t))

            update_path = download_update(dl_url, progress_cb=on_progress)

            # UI aktualisieren: "Installiere..."
            self.after(0, lambda: self._update_lbl.config(
                text=f"\u2705  Update v{info.get('latest', '?')} heruntergeladen! Installiere..."))
            self.after(0, lambda: self._update_progress.config(text=""))
            self.after(0, lambda: self._update_banner_frame.config(bg="#16a34a"))
            self.after(0, lambda: self._update_lbl.config(bg="#16a34a"))
            self.after(0, lambda: self._update_progress.config(bg="#16a34a"))

            # Kurz warten damit User die Nachricht sieht
            import time
            time.sleep(2)

            # Server stoppen falls aktiv
            if hasattr(self, 'server') and self.server:
                try:
                    self.server.stop()
                except Exception:
                    pass

            # Update anwenden und neustarten
            apply_update_and_restart(update_path)

        except Exception as ex:
            print(f"[UPDATE] Auto-Update fehlgeschlagen: {ex}", flush=True)
            # Fallback: normales Banner mit Link anzeigen
            self.after(0, lambda: self._update_banner_frame.pack_forget() if self._update_banner_frame else None)
            self._update_banner_frame = None
            self.after(0, lambda: self._show_update_banner(info))

    def _show_update_banner(self, info: dict):
        """Zeigt ein gelbes Update-Banner oben im Fenster (Fallback)."""
        if self._update_banner_frame:
            return
        f = tk.Frame(self, bg="#f59e0b", cursor="hand2")
        f.pack(fill="x", before=list(self.winfo_children())[0])

        txt = f"\U0001f514  Neue Version verfuegbar: v{info.get('latest', '?')}  (du hast v{SCANNER_VERSION})"
        lbl = tk.Label(f, text=txt, bg="#f59e0b", fg="#1a1a1a",
                       font=("Segoe UI", 11, "bold"), pady=6)
        lbl.pack(side="left", padx=(12, 0))

        btn_dl = tk.Button(f, text="\u2b07 Herunterladen", bg="#451a03", fg="white",
                           font=("Segoe UI", 10, "bold"), bd=0, padx=10, pady=3,
                           cursor="hand2",
                           command=lambda: webbrowser.open(info.get("url", "")))
        btn_dl.pack(side="left", padx=(12, 0))

        btn_close = tk.Button(f, text="\u2715", bg="#f59e0b", fg="#1a1a1a",
                              font=("Segoe UI", 12, "bold"), bd=0,
                              cursor="hand2",
                              command=lambda: (f.pack_forget(), setattr(self, '_update_banner_frame', None)))
        btn_close.pack(side="right", padx=(0, 8))

        self._update_banner_frame = f

    # ------------------------------------------------------------------
    # UI aufbauen
    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = 10

        top = ttk.Frame(self)
        top.pack(fill="x", padx=pad, pady=(pad, 0))

        left = ttk.LabelFrame(top, text="Ordner (werden gepr\u00fcft)")
        left.pack(side="left", fill="both", expand=True, padx=(0, pad))

        self.listbox = tk.Listbox(left, height=12, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, padx=pad, pady=(pad, 6))

        add_row = ttk.Frame(left)
        add_row.pack(fill="x", padx=pad, pady=(0, 8))
        ent = ttk.Entry(add_row, textvariable=self.var_add_path)
        ent.pack(side="left", fill="x", expand=True)
        ttk.Button(add_row, text="Pfad hinzuf\u00fcgen", command=self.add_path_from_entry).pack(side="left", padx=(8, 0))
        ent.bind("<Return>", lambda _e: self.add_path_from_entry())

        btn_row = ttk.Frame(left)
        btn_row.pack(fill="x", padx=pad, pady=(0, pad))
        ttk.Button(btn_row, text="Ordner ausw\u00e4hlen\u2026", command=self.add_folder).pack(side="left")
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
        ttk.Checkbutton(opt, text="Duplikate nach Inhalt (SHA-256)", variable=self.var_do_content).pack(anchor="w")
        ttk.Checkbutton(opt, text="Ressource-Konflikte (DBPF-IDs)", variable=self.var_do_conflicts).pack(anchor="w", pady=(0, 10))

        self.btn_backup = ttk.Button(opt, text="\U0001f4e6 Backup erstellen", command=self.create_backup)
        self.btn_backup.pack(fill="x")

        self.btn_run = tk.Button(
            opt, text="\u25b6  Scan & Web-UI\n     \u00f6ffnen",
            command=self.run_scan,
            bg="#2ecc71", fg="white",
            activebackground="#27ae60", activeforeground="white",
            font=("Segoe UI", 18, "bold"),
            relief="raised", bd=3, cursor="hand2",
        )
        self.btn_run.pack(fill="both", expand=True, pady=(12, 0))

        # Sims 4 Verzeichnis fuer Fehler-Analyse
        s4frame = ttk.LabelFrame(self, text="Sims 4 Verzeichnis (f\u00fcr Fehler-Analyse)")
        s4frame.pack(fill="x", padx=pad, pady=(10, 0))
        s4row = ttk.Frame(s4frame)
        s4row.pack(fill="x", padx=pad, pady=pad)
        ttk.Entry(s4row, textvariable=self.var_sims4_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(s4row, text="Ordner w\u00e4hlen\u2026", command=self.pick_sims4_dir).pack(side="left", padx=(8, 0))
        ttk.Button(s4row, text="Auto", command=self.auto_find_sims4_dir).pack(side="left", padx=(4, 0))

        # CurseForge Manifest-Pfad
        cfframe = ttk.LabelFrame(self, text="CurseForge Manifest (f\u00fcr Mod-Erkennung)")
        cfframe.pack(fill="x", padx=pad, pady=(10, 0))
        cfrow = ttk.Frame(cfframe)
        cfrow.pack(fill="x", padx=pad, pady=pad)
        ttk.Entry(cfrow, textvariable=self.var_cf_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfrow, text="Datei w\u00e4hlen\u2026", command=self.pick_cf_path).pack(side="left", padx=(8, 0))
        ttk.Button(cfrow, text="Auto", command=self.auto_find_cf_path).pack(side="left", padx=(4, 0))

        prog = ttk.Frame(self)
        prog.pack(fill="x", padx=pad, pady=(10, 0))
        ttk.Label(prog, textvariable=self.var_status).pack(anchor="w")
        self.progress = ttk.Progressbar(prog, mode="indeterminate")
        self.progress.pack(fill="x", pady=(6, 2))
        ttk.Label(prog, textvariable=self.var_detail).pack(anchor="w")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=pad, pady=(10, pad))
        ttk.Button(bottom, text="Web-UI nochmal \u00f6ffnen", command=self.open_web).pack(side="left")
        ttk.Button(bottom, text="Server stoppen", command=self.stop_server).pack(side="left", padx=8)
        ttk.Button(bottom, text="\u274c Beenden", command=self.quit_app).pack(side="right")
        ttk.Checkbutton(bottom, text="Beim Schlie\u00dfen minimieren (Server l\u00e4uft weiter)",
                        variable=self.var_minimize_on_close).pack(side="right", padx=(0, 12))

        ttk.Label(self, text="Tipp: Mehrere Pfade auf einmal einf\u00fcgen (Zeilenumbruch oder ';').").pack(anchor="w", padx=pad, pady=(0, pad))

    # ------------------------------------------------------------------
    # CurseForge / Sims4-Dir Picker
    # ------------------------------------------------------------------
    def pick_cf_path(self):
        p = filedialog.askopenfilename(
            title="CurseForge Manifest ausw\u00e4hlen (AddonGameInstance.json)",
            filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")],
        )
        if p:
            self.var_cf_path.set(p)
            self._save_config_now()

    def auto_find_cf_path(self):
        """Sucht automatisch nach dem CurseForge-Manifest."""
        candidates = []
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            candidates.append(Path(localappdata) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json")
            candidates.append(Path(localappdata) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
        progdata = os.environ.get("PROGRAMDATA", "")
        if progdata:
            candidates.append(Path(progdata) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
        for drive in ["C:", "D:", "E:", "F:", "G:"]:
            candidates.append(Path(drive) / "CurseForge" / "GameInstances" / "AddonGameInstance.json")
            candidates.append(Path(drive) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json")
        for c in candidates:
            if c.exists():
                self.var_cf_path.set(str(c))
                self._save_config_now()
                messagebox.showinfo("Gefunden", f"CurseForge Manifest gefunden:\n\n{c}")
                return
        messagebox.showwarning("Nicht gefunden",
                               "Konnte das CurseForge-Manifest nicht automatisch finden.\n"
                               "Bitte manuell ausw\u00e4hlen.\n\n"
                               "Normalerweise unter:\n"
                               "%LOCALAPPDATA%\\Overwolf\\Curse\\GameInstances\\AddonGameInstance.json")

    def pick_sims4_dir(self):
        p = filedialog.askdirectory(title="Sims 4 Verzeichnis ausw\u00e4hlen (z.B. Electronic Arts/Die Sims 4)")
        if p:
            self.var_sims4_dir.set(p)
            self._save_config_now()

    def auto_find_sims4_dir(self):
        d = find_sims4_userdir([])
        if d:
            self.var_sims4_dir.set(str(d))
            self._save_config_now()
            messagebox.showinfo("Gefunden", f"Sims 4 Verzeichnis gefunden:\n\n{d}")
        else:
            messagebox.showwarning("Nicht gefunden",
                                   "Konnte das Sims 4 Verzeichnis nicht automatisch finden.\n"
                                   "Bitte manuell ausw\u00e4hlen.")

    # ------------------------------------------------------------------
    # Konfiguration laden / speichern
    # ------------------------------------------------------------------
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
        if "sims4_dir" in cfg and cfg["sims4_dir"]:
            self.var_sims4_dir.set(cfg["sims4_dir"])
        else:
            d = find_sims4_userdir([])
            if d:
                self.var_sims4_dir.set(str(d))
        if "cf_path" in cfg and cfg["cf_path"]:
            self.var_cf_path.set(cfg["cf_path"])
        else:
            default_cf = Path(os.environ.get("LOCALAPPDATA", "")) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json"
            if default_cf.exists():
                self.var_cf_path.set(str(default_cf))
        if "minimize_on_close" in cfg:
            self.var_minimize_on_close.set(cfg["minimize_on_close"])
        self._tutorial_seen = cfg.get("tutorial_seen", False)

    def _save_config_now(self):
        """Speichere aktuelle Einstellungen in die Konfiguration."""
        folders = list(self.listbox.get(0, "end"))
        cfg = load_config()
        cfg.update({
            "folders": folders,
            "exts": self.var_exts.get(),
            "ignore": self.var_ignore.get(),
            "sims4_dir": self.var_sims4_dir.get(),
            "cf_path": self.var_cf_path.get(),
            "minimize_on_close": self.var_minimize_on_close.get(),
            "tutorial_seen": getattr(self, '_tutorial_seen', False),
        })
        save_config(cfg)

    # ------------------------------------------------------------------
    # Fenster-Events
    # ------------------------------------------------------------------
    def on_close(self):
        """Beim Schliessen — minimiert in Taskleiste statt beendet."""
        if self.var_minimize_on_close.get():
            self.iconify()
            self._minimized_to_tray = True
            return
        self.quit_app()

    def _on_map(self, _event=None):
        """Fenster wurde wiederhergestellt."""
        if self._minimized_to_tray:
            self._minimized_to_tray = False
            if self.server:
                self.var_status.set(f"Server l\u00e4uft \u2014 Port {self.server.port}")
            else:
                self.var_status.set("Bereit.")

    def quit_app(self):
        """Programm wirklich beenden."""
        self.stop_server()
        self.destroy()

    # ------------------------------------------------------------------
    # Ordner-Verwaltung
    # ------------------------------------------------------------------
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
                "Ung\u00fcltige Pfade",
                "Diese Pfade sind keine g\u00fcltigen Ordner:\n\n" + "\n".join(invalid[:25]) + ("" if len(invalid) <= 25 else "\n\u2026"),
            )
        if added == 0 and not invalid:
            messagebox.showinfo("Info", "Keine neuen Ordner hinzugef\u00fcgt (evtl. alles schon drin).")

        self._save_config_now()

    def add_path_from_entry(self):
        self.add_paths(self.var_add_path.get().strip())
        self.var_add_path.set("")
        self._save_config_now()

    def add_folder(self):
        p = filedialog.askdirectory(title="Ordner ausw\u00e4hlen")
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

    # ------------------------------------------------------------------
    # Fortschritts-Helfer
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------
    def create_backup(self):
        """Erstelle ein ZIP-Backup aller ausgewaehlten Ordner."""
        roots_raw = list(self.listbox.get(0, "end"))
        if not roots_raw:
            messagebox.showwarning("Hinweis", "Bitte mindestens einen Ordner hinzuf\u00fcgen.")
            return

        dest_dir = filedialog.askdirectory(title="Wo soll das Backup gespeichert werden?")
        if not dest_dir:
            return

        dest_path = Path(dest_dir)
        if not dest_path.exists() or not dest_path.is_dir():
            messagebox.showerror("Fehler", f"Ung\u00fcltiger Zielordner: {dest_dir}")
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = dest_path / f"sims4_backup_{stamp}.zip"

        self.btn_backup.configure(state="disabled")
        self.btn_run.configure(state="disabled")
        self.set_progress_indet(True, "Z\u00e4hle Dateien...", "")
        self.update()

        def worker():
            try:
                # Phase 1: Alle Dateien zaehlen
                total_files = 0
                total_size = 0
                file_list = []

                for root_str in roots_raw:
                    root = Path(root_str).resolve()
                    if not root.exists():
                        continue
                    for dirpath, _dirnames, filenames in os.walk(root):
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

                # Phase 2: ZIP erstellen
                start_time = time.time()
                packed_files = 0
                packed_size = 0
                update_interval = max(1, total_files // 20)

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

                        if packed_files % update_interval == 0 or packed_files == total_files:
                            elapsed = time.time() - start_time
                            percent = int((packed_files / total_files) * 100) if total_files > 0 else 0
                            speed = (packed_size / (1024 * 1024)) / max(elapsed, 0.1)

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
                    f"Gr\u00f6\u00dfe: {human_size(zip_size)}\n"
                    f"Zeit: {elapsed:.1f}s"
                )
                self.update()
                messagebox.showinfo(
                    "Erfolg",
                    f"Backup erstellt:\n\n{zip_name}\n\n"
                    f"Dateien: {total_files}\n"
                    f"Gr\u00f6\u00dfe: {human_size(zip_size)}\n"
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

    # ------------------------------------------------------------------
    # Scan & Server
    # ------------------------------------------------------------------
    def run_scan(self):
        self._save_config_now()

        roots_raw = list(self.listbox.get(0, "end"))
        if not roots_raw:
            messagebox.showwarning("Hinweis", "Bitte mindestens einen Ordner hinzuf\u00fcgen.")
            return
        if not (self.var_do_name.get() or self.var_do_content.get()):
            messagebox.showwarning("Hinweis", "Bitte mindestens eine Duplikat-Art ausw\u00e4hlen.")
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
            messagebox.showwarning("Ung\u00fcltige Ordner",
                                   "Diese Ordner existieren nicht:\n\n" + "\n".join(invalid_roots[:25]))

        if not roots:
            messagebox.showwarning("Hinweis", "Keiner der Ordner existiert.")
            return

        exts = normalize_exts(self.var_exts.get())
        ignore_dirs = normalize_ignore_dirs(self.var_ignore.get())
        do_name = self.var_do_name.get()
        do_content = self.var_do_content.get()
        do_conflicts = self.var_do_conflicts.get()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        qdir = roots[0].parent / f"dupe_quarantine_{stamp}"

        self.btn_run.configure(state="disabled")
        self.set_progress_indet(True, "Starte\u2026", "Initialisiere Scan\u2026")

        def ui_progress(phase, cur, total, msg):
            def apply():
                if phase == "collect":
                    self.set_progress_indet(True, "Sammle Dateien\u2026", msg)
                elif phase == "name":
                    self.set_progress_indet(True, "Pr\u00fcfe Dateinamen\u2026", msg)
                elif phase == "hashing_init":
                    if total and total > 0:
                        self.set_progress_det(0, total, "Hash-Pr\u00fcfung\u2026", msg)
                    else:
                        self.set_progress_indet(True, "Hash-Pr\u00fcfung\u2026", msg)
                elif phase == "hashing":
                    if total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Hash-Pr\u00fcfung\u2026", msg)
                    else:
                        self.set_progress_indet(True, "Hash-Pr\u00fcfung\u2026", msg)
                else:
                    if phase == 'integrity' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Integrit\u00e4ts-Check\u2026", msg)
                    elif phase == 'conflicts' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Konflikte pr\u00fcfen\u2026", msg)
                    elif phase == 'deep' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Tiefenanalyse\u2026", msg)
                    elif phase == 'categorize' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Kategorisiere\u2026", msg)
                    elif phase == 'tray_index' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Tray: Mod-Index\u2026", msg)
                    elif phase == 'tray' and total and total > 0 and cur is not None:
                        self.set_progress_det(cur, total, "Tray-Analyse\u2026", msg)
                    else:
                        self.set_progress_indet(True, "Finalisiere\u2026", msg)
            self.after(0, apply)

        def worker():
            try:
                files, name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs, contained_in, _non_mod_paths = scan_duplicates(
                    roots=roots,
                    exts=exts,
                    ignore_dirs=ignore_dirs,
                    do_name=do_name,
                    do_content=do_content,
                    do_conflicts=do_conflicts,
                    progress_cb=ui_progress,
                )

                ds = Dataset(roots, sims4_dir=self.var_sims4_dir.get())
                ds.all_scanned_files = files
                ds.build_from_scan(name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs, contained_in)

                deep_cache = load_deep_cache()
                ds.enrich_groups(progress_cb=ui_progress, deep_cache=deep_cache)
                ds.enrich_all_files(progress_cb=ui_progress, deep_cache=deep_cache)
                save_deep_cache(deep_cache)
                ds.detect_dependencies()
                ds.collect_non_mod_files()

                # ── Tray-Analyse (direkt im Scan) ──────────────────
                sims4 = self.var_sims4_dir.get()
                tray_path = os.path.join(sims4, "Tray") if sims4 else ""
                if tray_path and os.path.isdir(tray_path):
                    try:
                        ui_progress('tray_index', 0, 1, 'Mod-Index wird aufgebaut\u2026')
                        mod_idx = build_mod_instance_index(
                            roots,
                            progress_cb=lambda c, t, n: ui_progress('tray_index', c, t, n),
                        )
                        ui_progress('tray', 0, 1, 'Tray-Dateien werden gescannt\u2026')
                        tray_result = analyze_tray(
                            tray_path, mod_idx,
                            progress_cb=lambda c, t, n: ui_progress('tray', c, t, n),
                        )
                        ds.tray_data = tray_result
                        s = tray_result.get('summary', {})
                        print(f"[TRAY] Fertig: {s.get('total_items', 0)} Items, "
                              f"{s.get('items_with_cc', 0)} mit CC, "
                              f"{s.get('total_mods_used', 0)} Mods genutzt", flush=True)
                    except Exception as ex:
                        print(f"[TRAY] Analyse-Fehler: {ex}", flush=True)

                try:
                    scan_hist = save_scan_history(len(files), name_dupes, content_dupes, roots)
                    mod_snap = save_mod_snapshot(files, roots)
                except Exception as ex:
                    print(f"[HISTORY] Fehler beim Speichern: {ex}", flush=True)
                    scan_hist = {}
                    mod_snap = {}

                self.stop_server()
                srv = LocalServer(ds, qdir, sims4_dir=self.var_sims4_dir.get(), cf_path=self.var_cf_path.get())
                # Tray-Cache aus Scan übergeben
                if hasattr(ds, 'tray_data') and ds.tray_data:
                    srv._tray_cache = ds.tray_data
                srv.app_ref = self
                srv.scan_history = scan_hist
                srv.mod_snapshot = mod_snap
                srv.start()
                self.server = srv

                def finish():
                    self.progress.stop()
                    self.progress.configure(mode="determinate", value=0, maximum=1)
                    self.var_status.set("Fertig.")
                    self.var_detail.set(
                        f"Dateien: {len(files)} | Gruppen: Name {len(name_dupes)} / Inhalt {len(content_dupes)} / \u00c4hnlich {len(similar_dupes)} | Korrupt: {len(corrupt_files)} | Konflikte: {len(conflicts)} | Quarant\u00e4ne: {qdir}"
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
            messagebox.showinfo("Info", "Noch kein Server aktiv. Erst 'Scan & Web-UI \u00f6ffnen'.")
            return
        webbrowser.open(self.server.url())

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
            self.var_detail.set("Server gestoppt.")
