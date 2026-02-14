# -*- coding: utf-8 -*-
"""Scan-Logik: Duplikat-, Ähnlichkeits-, Integritäts- und Konflikt-Erkennung."""

from __future__ import annotations

import os
import re
import sys
import time
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import defaultdict

from .utils import normalize_mod_name, file_sha256
from .dbpf import read_dbpf_resource_keys, read_dbpf_entries, _read_resource_data, check_package_integrity, res_type_name
from .constants import TUNING_TYPES
from .config import load_hash_cache, save_hash_cache


# ---- Schweregrad für Ressource-Typen ----
# Hoch: Tuning/Gameplay-Änderungen die nach Patches brechen können
# Mittel: CAS Parts, Sim-Daten, Object Definitions
# Niedrig: Thumbnails, Texturen, Meshes — meistens gewollte Overrides
_SEVERITY_HIGH = TUNING_TYPES | {
    0x6017E896,  # Sim Data
    0x220557DA,  # Sim Info
}
_SEVERITY_LOW = {
    0x3C1AF1F2,  # Thumbnail
    0xC8A5E01A, 0x3C2A8647, 0x5B282D45, 0xCD9DE247, 0x0580A2B4, 0x0580A2B6,  # weitere Thumbnails
    0xD382BF57,  # Texture (LRLE)
    0x2F7D0004,  # DST Image
    0x00B2D882,  # DDS Image (Object Definition texture)
    0x015A1849,  # Mesh (GEOM)
    0x01D10F34,  # Blend Geometry
    0x00AE6C67,  # Bone Delta
}


def _classify_conflict_severity(rkeys: list[tuple]) -> tuple[str, str]:
    """Bestimmt den Schweregrad eines Konflikts anhand der Resource-Typen.
    Returns: (severity, reason) — severity is 'hoch'/'mittel'/'niedrig'/'harmlos'.
    """
    has_low_only = all(rt in _SEVERITY_LOW for rt, _, _ in rkeys)
    tuning_count = sum(1 for rt, _, _ in rkeys if rt in TUNING_TYPES)
    high_non_tuning = sum(1 for rt, _, _ in rkeys if rt in _SEVERITY_HIGH and rt not in TUNING_TYPES)

    # Wenige geteilte Keys (1-2): fast immer harmlos, auch bei Tuning
    if len(rkeys) <= 2:
        if tuning_count > 0:
            return 'harmlos', f'Nur {len(rkeys)} geteilte Ressource(n) ({tuning_count}x Tuning) — einzelne gemeinsame Basis-Ressource, normalerweise kein Problem'
        return 'harmlos', f'Nur {len(rkeys)} geteilte Ressource(n) — die Mods teilen sich einzelne Assets, normalerweise kein Problem'

    if tuning_count > 0:
        return 'hoch', f'{tuning_count} Tuning-Ressource(n) betroffen — kann Gameplay-Fehler verursachen'
    elif has_low_only:
        return 'niedrig', 'Nur Texturen/Thumbnails/Meshes — meistens gewollt'
    elif high_non_tuning > 0:
        return 'mittel', f'{high_non_tuning} Sim-Data-Ressource(n) betroffen — könnte Darstellungsfehler verursachen'
    else:
        return 'mittel', 'CAS/Objekt-Ressourcen betroffen — könnte Darstellungsfehler verursachen'


def _extract_conflict_tuning_names(rkeys: list[tuple], paths: list[str]) -> list[str]:
    """Extrahiert die Tuning-Namen für Konflikte die Tuning-Ressourcen betreffen."""
    import re as _re
    tuning_keys = [(rt, rg, ri) for rt, rg, ri in rkeys if rt in TUNING_TYPES]
    if not tuning_keys or not paths:
        return []

    names = []
    # Lese aus der ersten Datei (günstiger als alle)
    first_path = Path(paths[0])
    try:
        entries = read_dbpf_entries(first_path)
        if not entries:
            return []
        tuning_instances = {ri for _, _, ri in tuning_keys}
        for e in entries:
            if e['type'] in TUNING_TYPES and e['instance'] in tuning_instances:
                data = _read_resource_data(first_path, e)
                if data and len(data) > 10:
                    try:
                        text = data.decode('utf-8', errors='ignore')[:500]
                        m = _re.search(r'\bn="([^"]+)"', text)
                        if m and len(names) < 8:
                            names.append(m.group(1))
                    except Exception:
                        pass
    except Exception:
        pass
    return names


# ---- Addon-Erkennung ----
_ADDON_KEYWORDS = re.compile(
    r'(?:^|[_\-\s!.])'
    r'(?:addon|add-on|add_on|extension|patch|fix|hotfix|override|compat|compatibility|compat_patch)'
    r'(?:[_\-\s!.]|$)',
    re.IGNORECASE,
)


def _is_addon_pair(path_a: str, path_b: str) -> bool:
    """Prüft ob zwei Packages eine Addon-Beziehung haben."""
    name_a = Path(path_a).stem.lower()
    name_b = Path(path_b).stem.lower()
    dir_a = str(Path(path_a).parent).lower()
    dir_b = str(Path(path_b).parent).lower()

    a_has_kw = _ADDON_KEYWORDS.search(name_a)
    b_has_kw = _ADDON_KEYWORDS.search(name_b)

    if a_has_kw or b_has_kw:
        if a_has_kw:
            # Teil VOR dem Addon-Keyword als Basis nehmen
            base_before = name_a[:a_has_kw.start()].strip('_- !.')
            base_full = _ADDON_KEYWORDS.sub('', name_a).strip('_- !.')
            if (base_before and base_before in name_b.strip('_- !.')) or \
               (base_full and base_full in name_b.strip('_- !.')):
                return True
        if b_has_kw:
            base_before = name_b[:b_has_kw.start()].strip('_- !.')
            base_full = _ADDON_KEYWORDS.sub('', name_b).strip('_- !.')
            if (base_before and base_before in name_a.strip('_- !.')) or \
               (base_full and base_full in name_a.strip('_- !.')):
                return True

    if dir_a == dir_b:
        norm_a = normalize_mod_name(Path(path_a).name)
        norm_b = normalize_mod_name(Path(path_b).name)
        if norm_a and norm_b and norm_a != norm_b:
            if norm_a.startswith(norm_b) or norm_b.startswith(norm_a):
                longer = name_a if len(name_a) > len(name_b) else name_b
                shorter = name_b if len(name_a) > len(name_b) else name_a
                extra = longer.replace(shorter, '', 1).strip('_- !.')
                if extra:
                    return True

    return False


def scan_duplicates(
    roots: list[Path],
    exts: set[str],
    ignore_dirs: set[str],
    do_name: bool,
    do_content: bool,
    do_conflicts: bool = False,
    progress_cb=None,
):
    """Hauptscan: Duplikate, Ähnliche, Korrupte, Konflikte und Addon-Paare erkennen."""

    def emit(phase, cur, total, msg):
        if progress_cb:
            progress_cb(phase, cur, total, msg)

    files: list[Path] = []
    non_mod_paths: list[Path] = []  # Nicht-Mod-Dateien (während Walk mitgesammelt)
    emit("collect", 0, None, "Sammle Dateien…")
    count = 0
    last_emit = time.time()
    visited_inodes = set()

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            filtered_dirs = []
            for d in dirnames:
                if d.lower() in ignore_dirs:
                    continue
                dir_path = Path(dirpath) / d
                try:
                    if dir_path.is_symlink():
                        continue
                    if sys.platform == 'win32':
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(dir_path))
                        if attrs != -1 and (attrs & 0x400):
                            continue
                except Exception:
                    pass
                filtered_dirs.append(d)
            dirnames[:] = filtered_dirs

            for fn in filenames:
                p = Path(dirpath) / fn
                try:
                    if not p.is_file():
                        continue
                    if p.is_symlink():
                        continue
                    try:
                        real_p = p.resolve()
                        stat_info = real_p.stat()
                        inode = (stat_info.st_ino, stat_info.st_dev)
                        if inode in visited_inodes:
                            continue
                        visited_inodes.add(inode)
                    except Exception:
                        pass
                    if exts and p.suffix.lower() not in exts:
                        non_mod_paths.append(p)  # Nicht-Mod-Datei merken
                        continue
                    files.append(p)
                    count += 1
                    now = time.time()
                    if now - last_emit > 0.15:
                        emit("collect", count, None, f"Sammle Dateien… ({count})")
                        last_emit = now
                except Exception:
                    pass

    emit("collect", count, None, f"Dateien gesammelt: {count}")

    name_dupes = {}
    if do_name:
        emit("name", None, None, "Prüfe Duplikate nach Dateiname…")
        by_name = defaultdict(list)
        for p in files:
            by_name[p.name.lower()].append(p)
        name_dupes = {k: v for k, v in by_name.items() if len(v) > 1}
        emit("name", None, None, f"Name-Gruppen: {len(name_dupes)}")

    content_dupes = {}
    if do_content:
        emit("hashing_init", 0, 0, "Bereite Hash-Prüfung vor…")
        by_size = defaultdict(list)
        for p in files:
            try:
                by_size[p.stat().st_size].append(p)
            except Exception:
                pass

        candidates = []
        for _, group in by_size.items():
            if len(group) > 1:
                candidates.extend(group)

        total = len(candidates)
        emit("hashing_init", 0, total, f"Hashing-Kandidaten: {total}")

        if total > 0:
            # Disk-Cache für SHA-256 Hashes laden
            hash_cache = load_hash_cache()
            by_hash = defaultdict(list)
            done = 0
            last_emit = time.time()
            cache_hits = 0

            def _hash_one(p: Path) -> tuple[Path, str | None]:
                """Hasht eine Datei mit Cache-Lookup."""
                try:
                    st = p.stat()
                    key = str(p)
                    entry = hash_cache.get(key)
                    if entry and abs(entry.get('mt', 0) - st.st_mtime) < 0.01 and entry.get('sz', -1) == st.st_size:
                        return p, entry['hash']
                    digest = file_sha256(p)
                    hash_cache[key] = {'mt': st.st_mtime, 'sz': st.st_size, 'hash': digest}
                    return p, digest
                except Exception:
                    return p, None

            # Paralleles Hashing mit ThreadPool (I/O-bound)
            with ThreadPoolExecutor(max_workers=6) as pool:
                futures = {pool.submit(_hash_one, p): p for p in candidates}
                for future in as_completed(futures):
                    p, digest = future.result()
                    if digest:
                        by_hash[digest].append(p)
                    done += 1
                    now = time.time()
                    if now - last_emit > 0.08 or done == total:
                        emit("hashing", done, total, f"Hashing… ({done}/{total})\n{p}")
                        last_emit = now

            content_dupes = {d: ps for d, ps in by_hash.items() if len(ps) > 1}

            # Hash-Cache auf Disk speichern
            try:
                save_hash_cache(hash_cache)
            except Exception:
                pass

        emit("finalize", None, None, f"Inhalt-Gruppen: {len(content_dupes)}")

    # Ähnliche Dateinamen
    similar_dupes = {}
    if do_name:
        emit("finalize", None, None, "Prüfe ähnliche Dateinamen…")
        by_normalized = defaultdict(list)
        for p in files:
            norm = normalize_mod_name(p.name)
            by_normalized[norm].append(p)
        for norm_key, paths in by_normalized.items():
            if len(paths) < 2:
                continue
            real_names = set(p.name.lower() for p in paths)
            if len(real_names) == 1:
                continue
            real_stems = set(p.stem.lower() for p in paths)
            if len(real_stems) == 1:
                continue
            similar_dupes[norm_key] = paths
        emit("finalize", None, None, f"Ähnliche Gruppen: {len(similar_dupes)}")

        if similar_dupes and name_dupes:
            similar_paths_all = set()
            for paths in similar_dupes.values():
                for p in paths:
                    similar_paths_all.add(str(p).lower())
            redundant_keys = []
            for name_key, name_paths in name_dupes.items():
                if all(str(p).lower() in similar_paths_all for p in name_paths):
                    redundant_keys.append(name_key)
            for k in redundant_keys:
                del name_dupes[k]
            if redundant_keys:
                emit("finalize", None, None,
                     f"Name-Gruppen: {len(redundant_keys)} in Ähnlich-Gruppen aufgegangen → {len(name_dupes)} verbleibend")

    # Korrupte .package + DBPF-Index vorauslesen (kombiniert, spart doppeltes Datei-Öffnen)
    corrupt_files = []
    pkg_integrity: dict[str, str] = {}  # pfad → status ('ok' oder Fehlertyp)
    emit("integrity", 0, None, "Prüfe .package-Integrität…")
    pkg_files = [p for p in files if p.suffix.lower() == '.package']
    checked = 0
    last_emit = time.time()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(check_package_integrity, p): p for p in pkg_files}
        for future in as_completed(futures):
            p = futures[future]
            try:
                status = future.result()
            except Exception:
                status = 'error'
            if status != 'ok':
                corrupt_files.append((p, status))
            pkg_integrity[str(p)] = status
            checked += 1
            now = time.time()
            if now - last_emit > 0.1:
                emit("integrity", checked, len(pkg_files), f"Integritäts-Check… ({checked}/{len(pkg_files)})")
                last_emit = now
    emit("integrity", len(pkg_files), len(pkg_files), f"Korrupte Dateien: {len(corrupt_files)}")

    # Ressource-Konflikte
    conflicts = []
    addon_pairs = []
    contained_in = []
    if do_conflicts:
        # Nur intakte .package-Dateien für Konflikt-Analyse verwenden
        ok_pkg_files = [p for p in pkg_files if pkg_integrity.get(str(p)) == 'ok']
        emit("conflicts", 0, len(ok_pkg_files), "Lese DBPF-Index für Konflikt-Analyse…")
        key_to_pkgs = defaultdict(list)
        pkg_key_sets: dict[str, set] = {}  # pro Package: Menge aller Resource-Keys
        done_c = 0
        last_emit = time.time()

        def _read_keys(p):
            return p, read_dbpf_resource_keys(p)

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_read_keys, p): p for p in ok_pkg_files}
            for future in as_completed(futures):
                try:
                    p, rkeys = future.result()
                except Exception:
                    done_c += 1
                    continue
                if rkeys:
                    seen_in_file = set()
                    for rk in rkeys:
                        if rk not in seen_in_file:
                            seen_in_file.add(rk)
                            key_to_pkgs[rk].append(p)
                    pkg_key_sets[str(p)] = seen_in_file
                done_c += 1
                now = time.time()
                if now - last_emit > 0.1:
                    emit("conflicts", done_c, len(ok_pkg_files), f"DBPF-Index lesen… ({done_c}/{len(ok_pkg_files)})")
                    last_emit = now

        emit("conflicts", len(ok_pkg_files), len(ok_pkg_files), "Suche Konflikte…")

        shared_keys = {k: paths for k, paths in key_to_pkgs.items() if len(paths) > 1}
        pair_map = defaultdict(list)
        for rk, paths in shared_keys.items():
            pk = frozenset(str(p) for p in paths)
            pair_map[pk].append(rk)

        for path_set, rkeys in pair_map.items():
            type_counter = defaultdict(int)
            for rt, rg, ri in rkeys:
                type_counter[res_type_name(rt)] += 1
            top_types = sorted(type_counter.items(), key=lambda x: -x[1])[:5]
            paths_sorted = sorted(path_set)

            # ── Subset-Erkennung: Mod A komplett in Mod B enthalten? ──
            # Nutze die echten Key-Sets statt pair_map (die teilt Keys auf bei 3+-Gruppen)
            if len(paths_sorted) == 2:
                keys_a = pkg_key_sets.get(paths_sorted[0], set())
                keys_b = pkg_key_sets.get(paths_sorted[1], set())
                if keys_a and keys_b:
                    actual_shared = len(keys_a & keys_b)
                    # Identische Keys (gleicher Mod, verschiedene Varianten)
                    if actual_shared == len(keys_a) == len(keys_b):
                        # Beide haben exakt die gleichen Resource-IDs
                        smaller_idx = 0 if (len(keys_a) <= len(keys_b)) else 1
                        bigger_idx = 1 - smaller_idx
                        contained_in.append({
                            'paths': paths_sorted,
                            'contained_path': paths_sorted[smaller_idx],
                            'container_path': paths_sorted[bigger_idx],
                            'shared_count': actual_shared,
                            'container_total': len(keys_b) if bigger_idx == 1 else len(keys_a),
                            'top_types': top_types,
                            'is_variant': True,
                        })
                        continue
                    # Echtes Subset: alle Keys von A sind in B
                    elif actual_shared == len(keys_a) and len(keys_a) < len(keys_b):
                        contained_in.append({
                            'paths': paths_sorted,
                            'contained_path': paths_sorted[0],
                            'container_path': paths_sorted[1],
                            'shared_count': actual_shared,
                            'container_total': len(keys_b),
                            'top_types': top_types,
                        })
                        continue
                    elif actual_shared == len(keys_b) and len(keys_b) < len(keys_a):
                        contained_in.append({
                            'paths': paths_sorted,
                            'contained_path': paths_sorted[1],
                            'container_path': paths_sorted[0],
                            'shared_count': actual_shared,
                            'container_total': len(keys_a),
                            'top_types': top_types,
                        })
                        continue

            # Schweregrad + Tuning-Namen
            severity, severity_reason = _classify_conflict_severity(rkeys)
            tuning_names = _extract_conflict_tuning_names(rkeys, paths_sorted) if severity == 'hoch' else []

            entry = {
                'paths': paths_sorted,
                'shared_count': len(rkeys),
                'top_types': top_types,
                'severity': severity,
                'severity_reason': severity_reason,
                'tuning_names': tuning_names,
            }
            if len(paths_sorted) == 2 and _is_addon_pair(paths_sorted[0], paths_sorted[1]):
                addon_pairs.append(entry)
            else:
                conflicts.append(entry)
        _sev_order = {'hoch': 0, 'mittel': 1, 'niedrig': 2, 'harmlos': 3}
        conflicts.sort(key=lambda c: (_sev_order.get(c.get('severity', 'mittel'), 1), -c['shared_count']))
        addon_pairs.sort(key=lambda c: -c['shared_count'])
        contained_in.sort(key=lambda c: -c['shared_count'])
        emit("conflicts", len(ok_pkg_files), len(ok_pkg_files),
             f"Konflikte: {len(conflicts)} Gruppen, {len(addon_pairs)} Addon-Paare, {len(contained_in)} enthaltene Mods")

    return files, name_dupes, content_dupes, similar_dupes, corrupt_files, conflicts, addon_pairs, contained_in, non_mod_paths
