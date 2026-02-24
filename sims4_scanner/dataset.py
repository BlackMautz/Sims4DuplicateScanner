# -*- coding: utf-8 -*-
"""Dataset-Klasse: Aufbereitung und Serialisierung von Scan-Ergebnissen."""

from __future__ import annotations

import os
import re
import json
import ctypes
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

from .constants import CORRUPT_LABELS, TS4_PATCH_DATES
from .config import cache_entry_valid
from .utils import safe_stat, human_size, best_root_index, file_sha256, extract_version, normalize_mod_name
from .dbpf import analyze_package_deep, analyze_with_cache


def _read_curseforge_data(mods_dir: str = "", cf_manifest_path: str = "") -> dict:
    """Liest CurseForge/Overwolf-Manifest und gibt ein Dict {normalisierter_pfad: info} zurück."""
    result = {}
    try:
        if cf_manifest_path and Path(cf_manifest_path).exists():
            manifest_path = Path(cf_manifest_path)
        else:
            manifest_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Overwolf" / "Curse" / "GameInstances" / "AddonGameInstance.json"
        if not manifest_path.exists():
            return result
        raw = manifest_path.read_text(encoding="utf-8", errors="ignore")
        raw = raw.lstrip('\ufeff\x00')
        idx = raw.find('[')
        if idx > 0:
            raw = raw[idx:]
        instances = json.loads(raw)
        for inst in instances:
            if not isinstance(inst, dict):
                continue
            if inst.get("gameTypeID") != 78062:
                continue
            for addon in inst.get("installedAddons", []):
                try:
                    if not isinstance(addon, dict):
                        continue
                    mod_name = addon.get("name", "")
                    author = addon.get("primaryAuthor", "")
                    url = addon.get("webSiteURL", "") or ""
                    thumb = addon.get("thumbnailUrl", "") or ""
                    installed_file = addon.get("installedFile") or {}
                    latest_file = addon.get("latestFile") or {}
                    installed_id = installed_file.get("id", 0) if isinstance(installed_file, dict) else 0
                    latest_id = latest_file.get("id", 0) if isinstance(latest_file, dict) else 0
                    has_update = installed_id != latest_id and latest_id > 0
                    game_ver = ""
                    if isinstance(installed_file, dict):
                        gvs = installed_file.get("gameVersion") or []
                        if gvs and isinstance(gvs, list):
                            game_ver = str(gvs[0])
                    latest_game_ver = ""
                    if isinstance(latest_file, dict):
                        lgvs = latest_file.get("gameVersion") or []
                        if lgvs and isinstance(lgvs, list):
                            latest_game_ver = str(lgvs[0])
                    date_installed = addon.get("dateInstalled", "") or ""
                    date_updated = addon.get("dateUpdated", "") or ""
                    info = {
                        "name": mod_name, "author": author, "url": url, "thumbnail": thumb,
                        "has_update": has_update, "installed_version": game_ver,
                        "latest_version": latest_game_ver,
                        "latest_file_name": (latest_file.get("fileName", "") or "") if isinstance(latest_file, dict) else "",
                        "download_url": (latest_file.get("downloadUrl", "") or "") if isinstance(latest_file, dict) else "",
                        "date_installed": date_installed[:10] if date_installed else "",
                        "date_updated": date_updated[:10] if date_updated else "",
                    }
                    for fp in addon.get("filePaths", []):
                        if fp:
                            norm = os.path.normcase(os.path.normpath(fp))
                            result[norm] = info
                except Exception:
                    continue
    except Exception as ex:
        print(f"[CURSEFORGE] Fehler beim Lesen: {ex}", flush=True)
    return result


def _read_game_version(sims4_dir: str) -> dict | None:
    """Liest die Spielversion und das Patch-Datum aus GameVersion.txt."""
    if not sims4_dir:
        return None
    gv = Path(sims4_dir) / "GameVersion.txt"
    if not gv.exists():
        return None
    try:
        text = gv.read_text(encoding='utf-8', errors='ignore').strip()
        version = ''.join(c for c in text if c.isprintable() or c == '.')
        mtime = gv.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        return {
            'version': version,
            'patch_date': dt.strftime('%Y-%m-%d %H:%M'),
            'patch_ts': mtime,
        }
    except Exception:
        return None


class Dataset:
    def __init__(self, roots: list[Path], sims4_dir: str = ""):
        self.roots = roots
        self.sims4_dir = sims4_dir
        self.game_info = _read_game_version(sims4_dir)
        self.groups = []
        self.corrupt = []
        self.conflicts = []
        self.addon_pairs = []
        self.contained_in = []
        self.skin_conflicts: list[dict] = []
        self.all_scanned_files: list[Path] = []
        self.non_mod_files: list[dict] = []
        self.tray_data = None  # wird vom Scan befüllt
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._json_cache: dict | None = None  # to_json() Cache
        self._json_cache_key: str = ""  # Invalidierungs-Schlüssel
        self._generation: int = 0  # Inkrementiert bei jeder Mutation

    def collect_non_mod_files(self, preloaded_paths=None):
        """Sammelt alle Nicht-Mod-Dateien aus den Mod-Ordnern.
        
        Args:
            preloaded_paths: Optional — Liste von Path-Objekten die bereits beim Scanner-Walk
                             gesammelt wurden (spart einen kompletten Directory-Walk).
        """
        mod_exts = {".package", ".ts4script", ".zip", ".7z", ".rar"}
        ignore_dirs = {"__macosx", ".git", "__pycache__"}
        non_mod = []
        by_ext: dict[str, list] = {}

        if preloaded_paths is not None:
            # Pfade wurden schon beim Scan gesammelt — kein erneuter Walk nötig
            source_paths = preloaded_paths
        else:
            # Fallback: kompletten Walk machen (Abwärtskompatibilität)
            source_paths = []
            for root in self.roots:
                if not root.exists():
                    continue
                for dirpath, dirnames, filenames in os.walk(root):
                    filtered = []
                    for d in dirnames:
                        if d.lower() in ignore_dirs:
                            continue
                        dp = Path(dirpath) / d
                        try:
                            if dp.is_symlink():
                                continue
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
                            ext = p.suffix.lower()
                            if ext in mod_exts:
                                continue
                            source_paths.append(p)
                        except Exception:
                            pass

        for p in source_paths:
            try:
                if not p.is_file():
                    continue
                ext = p.suffix.lower()
                size, mtime = safe_stat(p)
                idx = best_root_index(p, self.roots)
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
                dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S") if mtime else "?"
                obj = {
                    "path": str(p), "name": p.name, "rel": rel_str,
                    "ext": ext if ext else "(keine)", "mod_folder": mod_folder,
                    "size": size, "size_h": human_size(size), "mtime": dt,
                }
                non_mod.append(obj)
                by_ext.setdefault(ext if ext else "(keine)", []).append(obj)
            except Exception:
                pass
        non_mod.sort(key=lambda f: (f["ext"], f["name"].lower()))
        self.non_mod_files = non_mod
        self._non_mod_by_ext = sorted(by_ext.items(), key=lambda x: -len(x[1]))

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
            "path": str(p), "rel": rel_str, "mod_folder": mod_folder,
            "root_label": label, "root_index": (idx + 1) if idx is not None else None,
            "size": size, "size_h": human_size(size), "mtime": dt, "exists": p.exists(),
        }

    def build_from_scan(self, name_dupes, content_dupes, similar_dupes=None, corrupt_files=None, conflicts=None, addon_pairs=None, contained_in=None):
        groups = []
        for filename, paths in name_dupes.items():
            files = [self._file_obj(p) for p in sorted(paths, key=lambda x: str(x).lower())]
            groups.append({"type": "name", "key": filename, "key_short": filename, "size_each": None, "files": files})
        for digest, paths in content_dupes.items():
            paths_sorted = sorted(paths, key=lambda x: str(x).lower())
            size0, _ = safe_stat(paths_sorted[0])
            files = [self._file_obj(p) for p in paths_sorted]
            groups.append({"type": "content", "key": digest, "key_short": digest[:12] + "…", "size_each": size0, "files": files})
        if similar_dupes:
            for norm_key, paths in similar_dupes.items():
                paths_sorted = sorted(paths, key=lambda x: str(x).lower())
                files = []
                for p in paths_sorted:
                    fobj = self._file_obj(p)
                    fobj["version"] = extract_version(p.name)
                    try:
                        fobj["hash"] = file_sha256(p)
                    except Exception:
                        fobj["hash"] = None
                    files.append(fobj)
                groups.append({"type": "similar", "key": norm_key, "key_short": norm_key, "size_each": None, "files": files})

        def score(g):
            count = len(g["files"])
            size_each = g["size_each"] or 0
            return (count, count * size_each)
        groups.sort(key=score, reverse=True)
        self.groups = groups

        self.corrupt = []
        if corrupt_files:
            for p, status in corrupt_files:
                fobj = self._file_obj(p)
                label, hint = CORRUPT_LABELS.get(status, (status, ''))
                self.corrupt.append({**fobj, 'status': status, 'status_label': label, 'status_hint': hint})

        self.conflicts = []
        if conflicts:
            for c in conflicts:
                file_objs = [self._file_obj(Path(ps)) for ps in c['paths']]
                self.conflicts.append({
                    'files': file_objs, 'shared_count': c['shared_count'], 'top_types': c['top_types'],
                    'severity': c.get('severity', 'mittel'), 'severity_reason': c.get('severity_reason', ''),
                    'tuning_names': c.get('tuning_names', []),
                })

        self.addon_pairs = []
        if addon_pairs:
            for c in addon_pairs:
                file_objs = [self._file_obj(Path(ps)) for ps in c['paths']]
                self.addon_pairs.append({'files': file_objs, 'shared_count': c['shared_count'], 'top_types': c['top_types']})

        self.contained_in = []
        if contained_in:
            for c in contained_in:
                file_objs = [self._file_obj(Path(ps)) for ps in c['paths']]
                contained_obj = self._file_obj(Path(c['contained_path']))
                container_obj = self._file_obj(Path(c['container_path']))
                self.contained_in.append({
                    'files': file_objs,
                    'contained': contained_obj,
                    'container': container_obj,
                    'shared_count': c['shared_count'],
                    'container_total': c['container_total'],
                    'top_types': c['top_types'],
                    'is_variant': c.get('is_variant', False),
                })

    def enrich_groups(self, progress_cb=None, deep_cache=None):
        """Tiefenanalyse für alle Gruppen."""
        if not self.groups:
            return
        total_files = 0
        for g in self.groups:
            total_files += 1 if g['type'] == 'content' else len(g['files'])
        done = 0
        for g in self.groups:
            file_keys = {}
            if g['type'] == 'content':
                first_deep = None
                for f in g['files']:
                    p = Path(f['path'])
                    if p.suffix.lower() != '.package':
                        continue
                    deep = analyze_with_cache(p, deep_cache)
                    if deep:
                        first_deep = deep[0]
                        if deep[1] is not None:
                            file_keys[f['path']] = deep[1]
                    break
                if first_deep:
                    for f in g['files']:
                        f['deep'] = first_deep
                done += 1
                if progress_cb and done % 3 == 0:
                    progress_cb("deep", done, total_files, f"Tiefenanalyse… ({done}/{total_files})")
            else:
                for f in g['files']:
                    p = Path(f['path'])
                    if p.suffix.lower() != '.package':
                        done += 1
                        continue
                    if g['type'] == 'similar':
                        deep = analyze_package_deep(p)
                        if deep and deep_cache is not None:
                            try:
                                st = p.stat()
                                deep_cache[str(p)] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': deep[0]}
                            except Exception:
                                pass
                    else:
                        deep = analyze_with_cache(p, deep_cache)
                    if deep:
                        info = deep[0]
                        keys = deep[1]
                        if keys is not None:
                            file_keys[f['path']] = keys
                        f['deep'] = info
                    done += 1
                    if progress_cb and done % 3 == 0:
                        progress_cb("deep", done, total_files, f"Tiefenanalyse… ({done}/{total_files})")

            if g['type'] == 'similar' and len(file_keys) >= 2:
                all_keys_union = set()
                for ks in file_keys.values():
                    all_keys_union |= ks
                shared = set.intersection(*file_keys.values())
                total = len(all_keys_union)
                overlap_pct = len(shared) / total * 100 if total > 0 else 0
                if overlap_pct >= 80:
                    rec = "update"
                    rec_text = "Wahrscheinlich ein Update — behalte nur die neueste Version"
                    rec_color = "#f59e0b"
                elif overlap_pct >= 30:
                    rec = "unclear"
                    rec_text = "Teilweise überlappend — manuell prüfen"
                    rec_color = "#8b5cf6"
                else:
                    rec = "different"
                    rec_text = "Verschiedene Items — wahrscheinlich beide behalten"
                    rec_color = "#22c55e"
                g['deep_comparison'] = {
                    'overlap_pct': round(overlap_pct, 1), 'shared_keys': len(shared),
                    'total_keys': total, 'recommendation': rec,
                    'recommendation_text': rec_text, 'recommendation_color': rec_color,
                }

            cats = [f.get('deep', {}).get('category', '') for f in g['files'] if f.get('deep')]
            if cats:
                common_cat = Counter(cats).most_common(1)[0][0]
                g['group_category'] = common_cat

        if progress_cb:
            progress_cb("deep", total_files, total_files, "Tiefenanalyse abgeschlossen")

    def enrich_all_files(self, progress_cb=None, deep_cache=None):
        """Kategorisiert ALLE gescannten .package-Dateien."""
        if not self.all_scanned_files:
            return
        if not hasattr(self, '_all_deep'):
            self._all_deep = {}
        analyzed = set(self._all_deep.keys())
        for g in self.groups:
            for f in g.get('files', []):
                d = f.get('deep')
                if d:
                    ps = f['path']
                    analyzed.add(ps)
                    self._all_deep[ps] = d
        for c in self.corrupt:
            d = c.get('deep')
            if d:
                analyzed.add(c.get('path', ''))
        for coll in (self.conflicts, self.addon_pairs, self.contained_in):
            for entry in coll:
                for f in entry.get('files', []):
                    d = f.get('deep')
                    if d:
                        ps = f.get('path', '')
                        analyzed.add(ps)
                        self._all_deep[ps] = d
        todo = [p for p in self.all_scanned_files if str(p) not in analyzed and p.suffix.lower() == '.package']
        if not todo:
            if progress_cb:
                progress_cb("categorize", 0, 0, "Alle Dateien bereits kategorisiert")
            return
        total = len(todo)
        cached_count = 0
        for i, p in enumerate(todo):
            ps = str(p)
            try:
                if deep_cache is not None and ps in deep_cache:
                    ce = deep_cache[ps]
                    if cache_entry_valid(ce, p):
                        self._all_deep[ps] = ce['deep']
                        cached_count += 1
                        if progress_cb and ((i + 1) % 50 == 0 or i + 1 == total):
                            progress_cb("categorize", i + 1, total, f"Kategorisiere… ({i + 1}/{total}, {cached_count} aus Cache)")
                        continue
                result = analyze_package_deep(p)
                if result:
                    self._all_deep[ps] = result[0]
                    if deep_cache is not None:
                        try:
                            st = p.stat()
                            deep_cache[ps] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': result[0]}
                        except Exception:
                            pass
            except Exception:
                pass
            if progress_cb and ((i + 1) % 20 == 0 or i + 1 == total):
                progress_cb("categorize", i + 1, total, f"Kategorisiere… ({i + 1}/{total}, {cached_count} aus Cache)")
        if progress_cb:
            progress_cb("categorize", total, total, f"Kategorisierung abgeschlossen ({cached_count}/{total} aus Cache)")

    def detect_skin_conflicts(self):
        """Erkennt Skin/Overlay-Konflikte die zu Stein-Haut und Texturfehlern führen."""
        import re as _re
        _SKIN_BODY_TYPES = {'Gesichts-Overlay', 'Kopf', 'Körper'}
        _SKIN_KEYWORDS = _re.compile(
            r'(?:skin(?:tone|detail|overlay|blend|replacement)?|freckle|mole|birthmark|wrinkle|scar|blemish|dimple|body.?preset|default.?skin|face.?overlay)',
            _re.IGNORECASE,
        )
        _deep_map = getattr(self, '_all_deep', {})

        def _is_skin_mod(path_str: str, deep: dict | None = None) -> tuple[bool, list[str]]:
            """Prüft ob ein Mod Skin/Overlay-Ressourcen enthält. Returns (is_skin, reasons)."""
            reasons = []
            if deep is None:
                deep = _deep_map.get(path_str, {})
            if not isinstance(deep, dict):
                return False, reasons
            body_types = deep.get('cas_body_types', [])
            skin_types = [bt for bt in body_types if bt in _SKIN_BODY_TYPES]
            if skin_types:
                reasons.append(f"Body-Typ: {', '.join(skin_types)}")
            cat = deep.get('category', '')
            if 'Make-Up' in cat and skin_types:
                reasons.append(f"Kategorie: {cat}")
            fname = Path(path_str).stem if path_str else ''
            if _SKIN_KEYWORDS.search(fname):
                reasons.append(f"Dateiname: '{fname}' enthält Skin-Keyword")
            return len(reasons) > 0, reasons

        skin_conflicts = []

        # 1. Konflikte die Skin-Mods betreffen
        for conf in self.conflicts:
            files_with_skin = []
            for f in conf.get('files', []):
                ps = f.get('path', '')
                deep = f.get('deep') or _deep_map.get(ps, {})
                is_skin, reasons = _is_skin_mod(ps, deep)
                if is_skin:
                    files_with_skin.append({'file': f, 'reasons': reasons})
            has_cas = any(name == 'CAS Part' for name, count in conf.get('top_types', []))
            if files_with_skin and has_cas:
                skin_conflicts.append({
                    'type': 'conflict',
                    'severity': 'hoch',
                    'icon': '⚔️',
                    'label': 'Skin-Konflikt — Mods überschreiben sich gegenseitig',
                    'hint': 'Zwei oder mehr Skin/Overlay-Mods teilen dieselben CAS-Part-IDs. Nur einer wird im Spiel angezeigt, der andere kann als Stein-Textur erscheinen.',
                    'action': 'Behalte nur EINEN Skin-Mod dieser Art und verschiebe die anderen in Quarantäne.',
                    'files': conf.get('files', []),
                    'shared_count': conf.get('shared_count', 0),
                    'top_types': conf.get('top_types', []),
                    'skin_details': files_with_skin,
                })

        # 2. Korrupte Skin-Mods
        for c in self.corrupt:
            ps = c.get('path', '')
            deep = c.get('deep') or _deep_map.get(ps, {})
            is_skin, reasons = _is_skin_mod(ps, deep)
            if is_skin:
                skin_conflicts.append({
                    'type': 'corrupt',
                    'severity': 'hoch',
                    'icon': '💀',
                    'label': 'Korrupter Skin-Mod — verursacht Stein-Haut',
                    'hint': f"Die Datei ist beschädigt ({c.get('status_label', 'Defekt')}) und enthält Skin-Daten. Das verursacht fast sicher Textur-Fehler.",
                    'action': 'Sofort in Quarantäne verschieben und eine frische Version herunterladen.',
                    'files': [c],
                    'shared_count': 0,
                    'top_types': [],
                    'skin_details': [{'file': c, 'reasons': reasons}],
                })

        # 3. Skin-Mods die potentiell ohne Mesh sind (Recolors die Stein-Haut verursachen können)
        for ps, deep in _deep_map.items():
            if not isinstance(deep, dict):
                continue
            is_skin, reasons = _is_skin_mod(ps, deep)
            if not is_skin:
                continue
            is_recolor = deep.get('is_recolor', False)
            body_types = deep.get('cas_body_types', [])
            has_skin_bt = any(bt in _SKIN_BODY_TYPES for bt in body_types)
            if is_recolor and has_skin_bt:
                already_listed = any(
                    any(f.get('path', '') == ps for f in sc.get('files', []))
                    for sc in skin_conflicts
                )
                if not already_listed:
                    fobj = self._file_obj(Path(ps))
                    fobj['deep'] = deep
                    skin_conflicts.append({
                        'type': 'recolor_warning',
                        'severity': 'niedrig',
                        'icon': '🎨',
                        'label': 'Skin-Recolor ohne eigenes Mesh',
                        'hint': 'Dieser Mod ist ein Recolor/Override für Skin-Texturen. Falls der Original-Skin-Mod fehlt, kann es zu Stein-Haut kommen.',
                        'action': 'Stelle sicher, dass der passende Basis-Skin-Mod installiert ist.',
                        'files': [fobj],
                        'shared_count': 0,
                        'top_types': [],
                        'skin_details': [{'file': fobj, 'reasons': reasons}],
                    })

        # Sortierung: hoch → mittel → niedrig
        _sev_order = {'hoch': 0, 'mittel': 1, 'niedrig': 2}
        skin_conflicts.sort(key=lambda x: (_sev_order.get(x.get('severity', 'mittel'), 1), -x.get('shared_count', 0)))
        self.skin_conflicts = skin_conflicts

    def detect_dependencies(self):
        """Erkennt Abhängigkeiten und Zusammengehörigkeit zwischen Mod-Dateien."""
        if not self.all_scanned_files:
            self.dependencies = []
            self.missing_deps = []
            return
        by_stem = defaultdict(list)
        for p in self.all_scanned_files:
            by_stem[p.stem.lower()].append(p)
        pairs = []
        for stem, paths in by_stem.items():
            exts = set(p.suffix.lower() for p in paths)
            if '.package' in exts and '.ts4script' in exts:
                pkgs = [p for p in paths if p.suffix.lower() == '.package']
                scripts = [p for p in paths if p.suffix.lower() == '.ts4script']
                pairs.append({
                    'type': 'script_pair', 'label': 'Script + Package',
                    'hint': 'Diese Dateien gehören zusammen — bitte BEIDE behalten oder BEIDE entfernen!',
                    'icon': '🔗', 'files': [str(p) for p in sorted(pkgs + scripts)], 'stem': stem,
                })

        # ---- Python-Import-Analyse für .ts4script Dateien ----
        import zipfile
        import ast

        # Bekannte Mod-Bibliotheken und ihre erwarteten Dateinamen
        _KNOWN_LIBS = {
            'sims4communitylib': ('Sims4CommunityLib', 'sims4communitylib'),
            's4cl': ('Sims4CommunityLib', 'sims4communitylib'),
            'wickedwhims': ('WickedWhims', 'wickedwhims'),
            'turbolib': ('TurboLib / WickedWhims', 'turbolib'),
            'basemental': ('Basemental Drugs/Gangs', 'basemental'),
            'deviantcore': ('DeviantCore', 'deviantcore'),
            'kuttoe': ('Kuttoe Utilities', 'kuttoe'),
            'lot51_core': ('Lot51 Core Library', 'lot51_core'),
            'tmex': ('TMEX Framework', 'tmex'),
            'codebase': ('Basemental CodeBase', 'codebase'),
        }

        # Sammle alle verfügbaren Module UND Imports in EINEM Durchlauf (Single-Pass)
        ts4scripts = [p for p in self.all_scanned_files if p.suffix.lower() == '.ts4script']
        installed_modules = set()
        # Vorbereiteter Cache: {script_path: (own_modules, external_imports)}
        _script_import_cache: dict[Path, tuple[set, set]] = {}

        _STDLIB_PREFIXES = {
            'os', 'sys', 'io', 're', 'math', 'json', 'time', 'random', 'copy',
            'collections', 'functools', 'itertools', 'types', 'abc', 'string',
            'enum', 'struct', 'pathlib', 'threading', 'logging', 'traceback',
            'importlib', 'inspect', 'textwrap', 'operator', 'contextlib',
            'weakref', 'heapq', 'bisect', 'array', 'queue', 'socket',
            'http', 'xml', 'html', 'csv', 'hashlib', 'base64', 'pickle',
            'shutil', 'glob', 'tempfile', 'subprocess', 'unittest', 'pprint',
            'datetime', 'calendar', 'decimal', 'fractions', 'statistics',
            'codecs', 'locale', 'gettext', 'argparse', 'configparser',
            'signal', 'errno', 'ctypes', 'platform', 'uuid',
            # TS4 eigene Module
            'sims4', 'sims', 'server', 'native', 'protocolbuffers',
            'cas', 'distributor', 'interactions', 'objects', 'services',
            'zone', 'game_services', 'clock', 'event_testing', 'situations',
            'ui', 'routing', 'autonomy', 'careers', 'relationships', 'whims',
            'aspirations', 'bucks', 'buffs', 'traits', 'statistics_module',
            'tunable_multiplier', 'element_utils', 'date_and_time',
            'animation', 'postures', 'socials', 'world', 'terrain',
            'build_buy', 'placement', 'caches', 'gsi_handlers',
            'filters', 'rewards', 'crafting', 'drama_scheduler',
            'holidays', 'seasons', 'clubs', 'fame', 'plex', 'venues',
            'business', 'retail', 'restaurants', 'veterinarian', 'adoption',
            'notebook', 'households', 'travel_group', 'publicity', 'away_actions',
            'lunar_cycle', 'open_street_director', 'conditional_layers',
            'tag', 'lot_decoration', 'display_snippet_tuning',
        }

        # Single-Pass: ZIP nur einmal öffnen, sowohl Module als auch Imports sammeln
        for sp in ts4scripts:
            installed_modules.add(sp.stem.lower())
            try:
                with zipfile.ZipFile(str(sp), 'r') as zf:
                    names = zf.namelist()
                    # Module sammeln
                    own_modules = set()
                    for name in names:
                        parts = name.replace('\\', '/').split('/')
                        if parts[0] and parts[0] not in ('__pycache__',):
                            own_modules.add(parts[0].lower())
                    installed_modules |= own_modules

                    # Imports sammeln
                    external_imports = set()
                    for name in names:
                        if not name.endswith('.py'):
                            continue
                        try:
                            code = zf.read(name).decode('utf-8', errors='ignore')
                            try:
                                tree = ast.parse(code)
                                for node in ast.walk(tree):
                                    if isinstance(node, ast.Import):
                                        for alias in node.names:
                                            top = alias.name.split('.')[0].lower()
                                            if top and top not in _STDLIB_PREFIXES:
                                                external_imports.add(top)
                                    elif isinstance(node, ast.ImportFrom):
                                        if node.module:
                                            top = node.module.split('.')[0].lower()
                                            if top and top not in _STDLIB_PREFIXES:
                                                external_imports.add(top)
                            except SyntaxError:
                                for line in code.split('\n'):
                                    line = line.strip()
                                    m = re.match(r'^(?:from\s+(\S+)|import\s+(\S+))', line)
                                    if m:
                                        mod_name = (m.group(1) or m.group(2)).split('.')[0].lower()
                                        if mod_name and mod_name not in _STDLIB_PREFIXES:
                                            external_imports.add(mod_name)
                        except Exception:
                            pass
                    external_imports -= own_modules
                    _script_import_cache[sp] = (own_modules, external_imports)
            except Exception:
                pass

        import_deps = []
        missing_deps = []

        # Zweiter Schritt: Imports auswerten (kein erneutes ZIP-Öffnen nötig)
        for sp, (own_mods, external_imports) in _script_import_cache.items():
            if external_imports:
                for imp in sorted(external_imports):
                    lib_info = _KNOWN_LIBS.get(imp)
                    is_installed = imp in installed_modules
                    if lib_info:
                        lib_name, _ = lib_info
                        if not is_installed:
                            missing_deps.append({
                                'type': 'missing_import',
                                'label': f'⚠️ Fehlende Abhängigkeit: {lib_name}',
                                'hint': f'"{sp.name}" importiert „{imp}" ({lib_name}), aber dieser Mod ist nicht installiert!',
                                'icon': '❌', 'files': [str(sp)], 'stem': sp.stem.lower(),
                                'import_name': imp, 'lib_name': lib_name, 'installed': False,
                            })
                        else:
                            import_deps.append({
                                'type': 'import_dependency',
                                'label': f'Importiert: {lib_name}',
                                'hint': f'"{sp.name}" benötigt „{lib_name}" — ist installiert ✅',
                                'icon': '📦', 'files': [str(sp)], 'stem': sp.stem.lower(),
                                'import_name': imp, 'lib_name': lib_name, 'installed': True,
                            })
                    elif not is_installed:
                        missing_deps.append({
                            'type': 'missing_import',
                            'label': f'⚠️ Fehlender Import: {imp}',
                            'hint': f'"{sp.name}" importiert „{imp}", aber kein passender Mod gefunden!',
                            'icon': '❓', 'files': [str(sp)], 'stem': sp.stem.lower(),
                            'import_name': imp, 'lib_name': imp, 'installed': False,
                        })

        _DEP_RE = re.compile(
            r'(?:^|[_\-.\s])(?:requires?|needs?|depends?(?:_?on)?|patch[_\-]?for|addon[_\-]?for|based[_\-]?on|extension[_\-]?for)[_\-.\s]+(.+)',
            re.IGNORECASE,
        )
        name_deps = []
        all_stems = {p.stem.lower(): p for p in self.all_scanned_files}
        for p in self.all_scanned_files:
            m = _DEP_RE.search(p.stem)
            if m:
                dep_name = normalize_mod_name(m.group(1))
                candidates = []
                for other_stem, other_p in all_stems.items():
                    if other_p == p:
                        continue
                    if dep_name and dep_name in normalize_mod_name(other_stem):
                        candidates.append(other_p)
                if candidates:
                    name_deps.append({
                        'type': 'name_dependency', 'label': 'Benötigt Basis-Mod',
                        'hint': f'"{p.name}" scheint einen anderen Mod zu benötigen.',
                        'icon': '📎', 'files': [str(p)] + [str(c) for c in candidates[:3]], 'stem': p.stem.lower(),
                    })
        prefix_groups = defaultdict(list)
        for p in self.all_scanned_files:
            parts = re.split(r'[_\-\s]+', p.stem.lower())
            if len(parts) >= 2:
                prefix = parts[0]
                if len(prefix) >= 3:
                    prefix_groups[prefix].append(p)
        families = []
        for prefix, members in prefix_groups.items():
            if len(members) >= 3:
                families.append({
                    'type': 'mod_family', 'label': f'Mod-Familie „{prefix}"',
                    'hint': f'{len(members)} Dateien mit dem Prefix „{prefix}" — gehören vermutlich zusammen.',
                    'icon': '👨\u200d👩\u200d👧\u200d👦', 'files': [str(p) for p in sorted(members)],
                    'stem': prefix, 'count': len(members),
                })
        families.sort(key=lambda f: -f['count'])
        # Fehlende Deps zuerst, dann Import-Deps, dann Paare, dann Name-Deps, dann Familien
        self.dependencies = missing_deps + import_deps + pairs + name_deps + families[:20]
        self.missing_deps = missing_deps

    def _invalidate_json_cache(self):
        self._json_cache = None
        self._json_cache_key = ""
        self._generation += 1

    def remove_file(self, file_path: str):
        target = (file_path or "").strip().lower()
        # Gruppen: Datei entfernen, Gruppen mit < 2 Dateien rauswerfen
        for g in self.groups:
            g["files"] = [f for f in g["files"] if str(f.get("path", "")).strip().lower() != target]
        self.groups = [g for g in self.groups if len(g["files"]) >= 2]
        # Korrupte Dateien
        self.corrupt = [c for c in self.corrupt if str(c.get("path", "")).strip().lower() != target]
        # Konflikte, Addon-Paare, Contained-In: Dateien entfernen, Einträge mit < 2 rauswerfen
        for coll_name in ('conflicts', 'addon_pairs', 'contained_in'):
            coll = getattr(self, coll_name)
            for entry in coll:
                entry['files'] = [f for f in entry['files'] if str(f.get('path', '')).strip().lower() != target]
            setattr(self, coll_name, [e for e in coll if len(e['files']) >= 2])
        # Skin-Konflikte: Dateien entfernen, aber Einträge mit >= 1 Datei behalten (einzelne Skin-Mods)
        for entry in self.skin_conflicts:
            entry['files'] = [f for f in entry['files'] if str(f.get('path', '')).strip().lower() != target]
        self.skin_conflicts = [e for e in self.skin_conflicts if len(e['files']) >= 1]
        self._invalidate_json_cache()

    def to_json(self) -> dict:
        # Cache prüfen: Generation-Counter statt nur Längen (erkennt auch Änderungen innerhalb)
        cache_key = f"{self._generation}:{len(self.groups)}:{len(self.corrupt)}:{len(self.conflicts)}:{len(self.all_scanned_files)}:{len(self.non_mod_files)}:{len(getattr(self, 'skin_conflicts', []))}"
        if self._json_cache is not None and self._json_cache_key == cache_key:
            return self._json_cache
        wasted = 0
        for g in self.groups:
            if g["type"] == "content" and g["size_each"] is not None and len(g["files"]) > 1:
                wasted += g["size_each"] * (len(g["files"]) - 1)

        seen_paths_stats = set()
        all_unique_files = []
        for g in self.groups:
            for f in g.get('files', []):
                if f['path'] not in seen_paths_stats:
                    seen_paths_stats.add(f['path'])
                    all_unique_files.append(f)
        for c in self.corrupt:
            p = c.get('path', '')
            if p and p not in seen_paths_stats:
                seen_paths_stats.add(p)
                all_unique_files.append(c)
        for conf in self.conflicts:
            for f in conf.get('files', []):
                p = f.get('path', '')
                if p and p not in seen_paths_stats:
                    seen_paths_stats.add(p)
                    all_unique_files.append(f)
        for ap in self.addon_pairs:
            for f in ap.get('files', []):
                p = f.get('path', '')
                if p and p not in seen_paths_stats:
                    seen_paths_stats.add(p)
                    all_unique_files.append(f)

        total_size = sum(f.get('size', 0) for f in all_unique_files)
        folder_sizes = {}
        folder_counts = {}
        for f in all_unique_files:
            mf = f.get('mod_folder', '(Mods-Root)')
            folder_sizes[mf] = folder_sizes.get(mf, 0) + f.get('size', 0)
            folder_counts[mf] = folder_counts.get(mf, 0) + 1

        sorted_by_size = sorted(all_unique_files, key=lambda f: -(f.get('size', 0)))
        top10 = [{'path': f.get('path', ''), 'rel': f.get('rel', ''), 'mod_folder': f.get('mod_folder', ''), 'size': f.get('size', 0), 'size_h': f.get('size_h', '?')} for f in sorted_by_size[:10]]
        sorted_folders = sorted(folder_sizes.items(), key=lambda x: -x[1])
        top10_folders = [{'name': n, 'size': s, 'size_h': human_size(s), 'count': folder_counts.get(n, 0)} for n, s in sorted_folders[:10]]

        outdated = []
        if self.game_info:
            patch_ts = self.game_info['patch_ts']
            # Patch-Daten als Timestamps für patches_behind Berechnung
            _patch_timestamps = []
            for pd_str, pd_ver, pd_desc in TS4_PATCH_DATES:
                try:
                    pts = datetime.strptime(pd_str, '%Y-%m-%d').timestamp()
                    _patch_timestamps.append((pts, pd_ver, pd_desc))
                except Exception:
                    pass

            seen_paths = set()
            all_files = []
            for g in self.groups:
                for f in g.get('files', []):
                    if f['path'] not in seen_paths:
                        seen_paths.add(f['path'])
                        all_files.append(f)
            for c in self.corrupt:
                p = c.get('path', '')
                if p and p not in seen_paths:
                    seen_paths.add(p)
                    all_files.append(c)
            for f in all_files:
                mt_str = f.get('mtime', '?')
                if mt_str == '?':
                    continue
                try:
                    mt = datetime.strptime(mt_str, '%Y-%m-%d %H:%M:%S').timestamp()
                except Exception:
                    continue
                if mt < patch_ts:
                    days_old = int((patch_ts - mt) / 86400)
                    f_copy = dict(f)
                    f_copy['days_before_patch'] = days_old

                    # Berechne wie viele Patches der Mod hinterher ist
                    missed_patches = [(v, d) for ts, v, d in _patch_timestamps if ts > mt]
                    f_copy['patches_behind'] = len(missed_patches)
                    f_copy['missed_patches'] = missed_patches[:5]  # max 5 für die Anzeige

                    p_lower = f.get('path', '').lower()
                    if p_lower.endswith('.ts4script'):
                        f_copy['risk'] = 'hoch'
                        f_copy['risk_reason'] = 'Script-Mod — bricht häufig nach Patches'
                    else:
                        deep = f.get('deep', {})
                        cat = deep.get('category', '') if isinstance(deep, dict) else ''
                        if 'Tuning' in cat or 'Gameplay' in cat:
                            f_copy['risk'] = 'mittel'
                            f_copy['risk_reason'] = 'Tuning-Mod — kann nach Patches Probleme machen'
                        elif 'CAS' in cat:
                            f_copy['risk'] = 'niedrig'
                            f_copy['risk_reason'] = 'CAS/CC — bricht selten nach Patches'
                        elif 'Objekt' in cat:
                            f_copy['risk'] = 'niedrig'
                            f_copy['risk_reason'] = 'Objekt/Möbel — bricht selten'
                        else:
                            f_copy['risk'] = 'unbekannt'
                            f_copy['risk_reason'] = 'Typ nicht erkannt'
                    outdated.append(f_copy)
            outdated.sort(key=lambda x: (-{'hoch': 3, 'mittel': 2, 'niedrig': 1}.get(x.get('risk', ''), 0), -x.get('days_before_patch', 0)))

        all_files_list = []
        _deep_map = getattr(self, '_all_deep', {})
        if self.all_scanned_files:
            seen_all = set()
            existing_objs = {}
            for f in all_unique_files:
                existing_objs[f.get('path', '')] = f
            for p in self.all_scanned_files:
                ps = str(p)
                if ps in seen_all:
                    continue
                seen_all.add(ps)
                if ps in existing_objs:
                    obj = existing_objs[ps]
                else:
                    obj = self._file_obj(p)
                if not obj.get('deep') and ps in _deep_map:
                    obj['deep'] = _deep_map[ps]
                all_files_list.append(obj)

        total_scanned = len(all_files_list) if all_files_list else len(all_unique_files)
        cat_source = all_files_list if all_files_list else all_unique_files
        cat_counts = {}
        for f in cat_source:
            deep = f.get('deep', {})
            cat = deep.get('category', '') if isinstance(deep, dict) else ''
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            else:
                cat_counts['Unbekannt'] = cat_counts.get('Unbekannt', 0) + 1
        cat_counts_sorted = sorted(cat_counts.items(), key=lambda x: -x[1])

        activity_heatmap = {}
        _heatmap_names = {}
        for f in cat_source:
            mt_str = f.get('mtime', '?')
            if mt_str == '?':
                continue
            try:
                day = mt_str[:10]
                activity_heatmap[day] = activity_heatmap.get(day, 0) + 1
                fname = (f.get('rel', '') or f.get('path', '')).replace('\\', '/').split('/')[-1]
                if fname:
                    if day not in _heatmap_names:
                        _heatmap_names[day] = []
                    _heatmap_names[day].append(fname)
            except Exception:
                pass
        activity_heatmap_full = {}
        for day, count in activity_heatmap.items():
            names = _heatmap_names.get(day, [])
            activity_heatmap_full[day] = {"count": count, "mods": names, "more": count - len(names)}

        deps = getattr(self, 'dependencies', [])

        result = {
            "created_at": self.created_at,
            "roots": [{"label": f"Ordner {i+1}", "path": str(r)} for i, r in enumerate(self.roots)],
            "game_info": self.game_info,
            "summary": {
                "groups_name": sum(1 for g in self.groups if g["type"] == "name"),
                "groups_content": sum(1 for g in self.groups if g["type"] == "content"),
                "groups_similar": sum(1 for g in self.groups if g["type"] == "similar"),
                "corrupt_count": len(self.corrupt), "conflict_count": len(self.conflicts),
                "addon_count": len(self.addon_pairs), "contained_count": len(self.contained_in),
                "outdated_count": len(outdated),
                "dependency_count": len(deps),
                "missing_dep_count": len(getattr(self, 'missing_deps', [])),
                "skin_conflict_count": len(getattr(self, 'skin_conflicts', [])),
                "entries_total": sum(len(g["files"]) for g in self.groups),
                "total_files": total_scanned, "problem_files": len(all_unique_files),
                "total_size": total_size, "total_size_h": human_size(total_size),
                "wasted_bytes_est": wasted, "wasted_h": human_size(wasted),
                "non_mod_count": len(self.non_mod_files),
            },
            "stats": {
                "category_counts": cat_counts_sorted, "top10_biggest": top10,
                "top10_folders": top10_folders, "activity_heatmap": activity_heatmap_full,
            },
            "groups": self.groups, "corrupt": self.corrupt,
            "conflicts": self.conflicts, "addon_pairs": self.addon_pairs,
            "contained_in": self.contained_in,
            "skin_conflicts": getattr(self, 'skin_conflicts', []),
            "outdated": outdated, "dependencies": deps,
            "all_files": all_files_list, "non_mod_files": self.non_mod_files,
            "non_mod_by_ext": getattr(self, '_non_mod_by_ext', []),
            "tray": self.tray_data,
        }
        # Cache speichern
        self._json_cache = result
        self._json_cache_key = cache_key
        return result
