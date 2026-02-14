# -*- coding: utf-8 -*-
"""Auto-Update-Check über die GitHub Releases API."""

from __future__ import annotations

import re
import json

from .constants import SCANNER_VERSION, GITHUB_REPO

_update_cache: dict | None = None


def _parse_version(v: str) -> tuple[int, ...]:
    """'v2.3.0' oder '2.3.0' → (2, 3, 0)"""
    v = v.strip().lstrip("vV")
    parts: list[int] = []
    for p in v.split("."):
        m = re.match(r"(\d+)", p)
        if m:
            parts.append(int(m.group(1)))
    return tuple(parts) if parts else (0,)


def check_for_update(timeout: float = 5.0) -> dict:
    """Fragt GitHub Releases API ab. Ergebnis wird gecacht (einmal pro App-Start)."""
    global _update_cache
    if _update_cache is not None:
        return _update_cache

    result: dict = {
        "available": False, "current": SCANNER_VERSION,
        "latest": SCANNER_VERSION, "url": "", "name": "", "body": "",
    }
    try:
        from urllib.request import urlopen, Request
        req = Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "Sims4DupScanner"},
        )
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = data.get("tag_name", "")
        latest = _parse_version(tag)
        current = _parse_version(SCANNER_VERSION)
        result["latest"] = tag.lstrip("vV")
        result["name"] = data.get("name", "")
        result["body"] = data.get("body", "")
        result["url"] = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
        for asset in data.get("assets", []):
            if asset.get("name", "").lower().endswith(".exe"):
                result["download_url"] = asset.get("browser_download_url", "")
                break
        if latest > current:
            result["available"] = True
            print(f"[UPDATE] Neue Version verfügbar: {tag} (aktuell: {SCANNER_VERSION})", flush=True)
        else:
            print(f"[UPDATE] Aktuelle Version {SCANNER_VERSION} ist aktuell (latest: {tag})", flush=True)
    except Exception as ex:
        print(f"[UPDATE] Check fehlgeschlagen: {type(ex).__name__}: {ex}", flush=True)

    _update_cache = result
    return result
