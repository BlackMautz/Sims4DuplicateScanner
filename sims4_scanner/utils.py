# -*- coding: utf-8 -*-
"""Hilfsfunktionen: Dateisystem, Normalisierung, Hashing."""

from __future__ import annotations

import os
import re
import hashlib
import time
from pathlib import Path

from .constants import CHUNK_SIZE


def normalize_exts(ext_text: str) -> set[str]:
    ext_text = (ext_text or "").strip()
    if ext_text == "" or ext_text == "*":
        return set()
    exts = {e.strip().lower() for e in ext_text.split(",") if e.strip()}
    return {e if e.startswith(".") else f".{e}" for e in exts}


def normalize_ignore_dirs(ignore_text: str) -> set[str]:
    ignore_text = (ignore_text or "").strip()
    return {d.strip().lower() for d in ignore_text.split(",") if d.strip()}


def safe_stat(p: Path):
    try:
        st = p.stat()
        return st.st_size, st.st_mtime
    except Exception:
        return None, None


def human_size(n: int | None) -> str:
    if n is None:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.2f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return f"{n} B"


def file_sha256(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError) as exc:
        print(f"[HASH] Fehler beim Lesen von {path.name}: {exc}", flush=True)
        return ""


def best_root_index(path: Path, roots: list[Path]) -> int | None:
    candidates = set()
    candidates.add(str(path).lower())
    try:
        candidates.add(str(path.resolve()).lower())
    except Exception:
        pass

    best_i = None
    best_len = -1
    for i, r in enumerate(roots):
        root_candidates = set()
        root_candidates.add(str(r).lower())
        try:
            root_candidates.add(str(r.resolve()).lower())
        except Exception:
            pass

        for ps in candidates:
            for rs in root_candidates:
                if ps.startswith(rs) and len(rs) > best_len:
                    best_i = i
                    best_len = len(rs)
    return best_i


def is_under_any_root(path: Path, roots: list[Path]) -> bool:
    """Security: allow actions only inside chosen roots."""
    path_variants = set()
    path_variants.add(str(path).lower().rstrip("\\/"))
    try:
        path_variants.add(str(path.resolve()).lower().rstrip("\\/"))
    except Exception:
        pass

    if not path_variants:
        return False

    for r in roots:
        root_variants = set()
        root_variants.add(str(r).lower().rstrip("\\/"))
        try:
            root_variants.add(str(r.resolve()).lower().rstrip("\\/"))
        except Exception:
            pass

        for ps in path_variants:
            for rs in root_variants:
                if ps == rs:
                    return True
                if ps.startswith(rs + os.sep):
                    return True
    return False


def ensure_unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suf = dest.suffix
    parent = dest.parent
    for i in range(1, 10000):
        cand = parent / f"{stem}__dup{i}{suf}"
        if not cand.exists():
            return cand
    return parent / f"{stem}__dup{int(time.time())}{suf}"


# ---- Ähnliche Dateinamen: Normalisierung ----

_VERSION_RE = re.compile(
    r'[_\- ]+'
    r'(?:'
    r'v\d+[\._]?\d*[a-z]?'
    r'|\d{3,}[a-z]?'
    r'|\d+\.\d+(?:\.\d+)*[a-z]?'
    r')'
    r'(?:[_\- ]*(?:patch|fix|update|hotfix)\d*)?',
    re.IGNORECASE,
)

_COPY_RE = re.compile(
    r'[_\- ]*(?:'
    r'\(\d+\)'
    r'|copy'
    r'|kopie'
    r'|- copy'
    r'|_old'
    r'|_backup'
    r'|_bak'
    r'|_original'
    r'|_new'
    r'|_neu'
    r')',
    re.IGNORECASE,
)

_EXTRA_STRIP_RE = re.compile(r'[_\- ]+$')


def normalize_mod_name(filename: str) -> str:
    """Normalisiert einen Mod-Dateinamen für Ähnlichkeitsvergleich."""
    name = Path(filename).stem.lower()
    for _ in range(3):
        name = _COPY_RE.sub('', name)
    for _ in range(3):
        name = _VERSION_RE.sub('', name, count=1)
    name = _EXTRA_STRIP_RE.sub('', name)
    if not name.strip():
        name = Path(filename).stem.lower()
    return name.strip()


def extract_version(filename: str) -> str:
    """Versucht eine Versionsnummer aus dem Dateinamen zu extrahieren."""
    stem = Path(filename).stem
    m = re.search(r'[_\- ]v(\d+(?:[\._]\d+)*[a-z]?)', stem, re.IGNORECASE)
    if m:
        return 'v' + m.group(1)
    m = re.search(r'[_\- ](\d+\.\d+(?:\.\d+)*[a-z]?)', stem, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'[_\- ](\d{3,}[a-z]?)', stem, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'\((\d+)\)', stem)
    if m:
        return f"({m.group(1)})"
    return ""
