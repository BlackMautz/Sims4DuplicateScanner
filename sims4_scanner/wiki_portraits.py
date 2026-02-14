# -*- coding: utf-8 -*-
"""Wiki-Portraits: Lädt Sim-Bilder aus dem Sims-Wiki als Fallback wenn keine SGI vorhanden."""

import os
import hashlib
import time
import json
from pathlib import Path
from urllib.parse import quote
from typing import Optional
import requests
from .name_translation import german_to_english_name
from .embedded_portraits import get_embedded_portrait

# Rate-Limiting: max 1 Wiki-Request pro 0.15 Sekunden (~ 6-7 req/s)
_last_wiki_request: float = 0.0
_WIKI_MIN_INTERVAL: float = 0.15

def _wiki_rate_limit():
    """Wartet falls nötig, um das Wiki nicht zu überlasten."""
    global _last_wiki_request
    now = time.time()
    elapsed = now - _last_wiki_request
    if elapsed < _WIKI_MIN_INTERVAL:
        time.sleep(_WIKI_MIN_INTERVAL - elapsed)
    _last_wiki_request = time.time()


def _wiki_cache_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / "wiki_portraits_cache"
    return Path.home() / ".sims4_wiki_portraits_cache"


def _user_portraits_dir() -> Path:
    """Ordner für benutzerdefinierte Portraits mit lesbaren Sim-Namen.

    Pfad: %APPDATA%/Sims4DupeScanner/portraits/
    Dateien: 'Vorname Nachname.jpg' (z.B. 'Bella Grusel.jpg')
    Dieser Ordner hat höchste Priorität – Bilder hier überschreiben alles.
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Sims4DupeScanner" / "portraits"
    return Path.home() / ".sims4_portraits"


# Cache-Ordner für Wiki-Bilder (MD5-Hashes, intern)
WIKI_CACHE_DIR = _wiki_cache_dir()
# Ordner für benutzerdefinierte Portraits (lesbare Namen)
USER_PORTRAITS_DIR = _user_portraits_dir()
# Negativ-Cache: Sims die kein Wiki-Portrait haben (nicht immer wieder abfragen)
NEGATIVE_CACHE_FILE = WIKI_CACHE_DIR / "_no_portrait.json"

def _load_negative_cache() -> dict:
    """Lädt den Negativ-Cache (Sims ohne Wiki-Portrait)."""
    try:
        if NEGATIVE_CACHE_FILE.exists():
            data = json.loads(NEGATIVE_CACHE_FILE.read_text(encoding='utf-8'))
            # Einträge älter als 30 Tage entfernen (Wiki könnte inzwischen Bild haben)
            now = time.time()
            max_age = 30 * 86400  # 30 Tage
            cleaned = {}
            for name, ts in data.items():
                if isinstance(ts, (int, float)) and (now - ts) < max_age:
                    cleaned[name] = ts
                elif isinstance(ts, dict):
                    # Legacy-Format: prüfe ob Timestamp-Feld existiert
                    legacy_ts = ts.get("ts", ts.get("time", 0))
                    if isinstance(legacy_ts, (int, float)) and (now - legacy_ts) < max_age:
                        cleaned[name] = ts
                    # else: abgelaufener Legacy-Eintrag, wird entfernt
                else:
                    cleaned[name] = ts
            if len(cleaned) < len(data):
                print(f"[WIKI] {len(data) - len(cleaned)} abgelaufene Negativ-Cache-Einträge entfernt", flush=True)
                _save_negative_cache(cleaned)
            return cleaned
    except Exception:
        pass
    return {}

def _save_negative_cache(cache: dict):
    """Speichert den Negativ-Cache."""
    try:
        _ensure_cache_dir()
        NEGATIVE_CACHE_FILE.write_text(json.dumps(cache), encoding='utf-8')
    except Exception:
        pass

def _ensure_cache_dir():
    """Stellt sicher dass der Cache-Ordner existiert."""
    WIKI_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_user_dir():
    """Stellt sicher dass der User-Portraits-Ordner existiert."""
    USER_PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Entfernt ungültige Zeichen aus einem Dateinamen."""
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, '_')
    return name.strip('. ')


def _find_user_portrait(sim_name: str) -> Optional[bytes]:
    """Sucht Portrait im User-Ordner (lesbare Namen: 'Vorname Nachname.jpg')."""
    if not sim_name:
        return None
    safe_name = _safe_filename(sim_name)
    # JPG und PNG unterstützen
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        portrait_file = USER_PORTRAITS_DIR / (safe_name + ext)
        if portrait_file.exists():
            try:
                data = portrait_file.read_bytes()
                if len(data) > 100:
                    return data
            except Exception:
                pass
    return None

def _find_headshot_url(english_name: str) -> Optional[str]:
    """Fragt die Wiki-API direkt nach der Headshot-Datei für einen Sim.
    
    Konstruiert den erwarteten Dateinamen (z.B. 'Bjorn_Bjergsen_headshot.png')
    und fragt die API ob diese Datei existiert.
    """
    headers = {"User-Agent": "Sims4DuplicateScanner/2.6.1"}
    
    def _scale_url(raw_url: str) -> str:
        """Baut eine skalierte URL aus der API-URL."""
        # Entferne alles nach dem Dateinamen und füge Skalierung hinzu
        import re as _re
        base = _re.split(r'/revision/', raw_url)[0]
        return base + '/revision/latest/scale-to-width-down/250'
    
    # --- Stufe 1: Direkt nach _headshot.png fragen ---
    try:
        file_name = english_name.replace(" ", "_") + "_headshot.png"
        api_url = (
            f"https://sims.fandom.com/api.php?action=query"
            f"&titles=File:{quote(file_name)}"
            f"&prop=imageinfo&iiprop=url&format=json"
        )
        
        _wiki_rate_limit()
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1":
                    imageinfo = page_info.get("imageinfo", [])
                    if imageinfo:
                        url = imageinfo[0].get("url", "")
                        if url:
                            return _scale_url(url)
    except Exception:
        pass
    
    # --- Stufe 2: Direkt nach Simname.png fragen (neuere Sims) ---
    # Manche Wiki-Dateien nutzen Unterstrich (Emilia_Ernest.png),
    # andere keine Trennung (LilyFeng.png) - beides probieren
    for sep in ["_", ""]:
      try:
        file_name = english_name.replace(" ", sep) + ".png"
        api_url = (
            f"https://sims.fandom.com/api.php?action=query"
            f"&titles=File:{quote(file_name)}"
            f"&prop=imageinfo&iiprop=url|size&format=json"
        )
        _wiki_rate_limit()
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1":
                    imageinfo = page_info.get("imageinfo", [])
                    if imageinfo:
                        info = imageinfo[0]
                        url = info.get("url", "")
                        # Nur Portrait-artige Bilder (nicht zu breit/flach)
                        w = info.get("width", 0)
                        h = info.get("height", 0)
                        if url and h > 0 and w / h < 1.5:
                            # Bild ist hoch genug (kein Banner/CAS)
                            return _scale_url(url)
      except Exception:
        pass
    
    # --- Stufe 3: Infobox-Bild über pageimages API ---
    try:
        wiki_name = english_name.replace(" ", "_")
        api_url = (
            f"https://sims.fandom.com/api.php?action=query"
            f"&titles={quote(wiki_name)}"
            f"&prop=pageimages&format=json&pithumbsize=250"
        )
        _wiki_rate_limit()
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id == "-1":
                    continue
                
                thumbnail = page_info.get("thumbnail", {})
                img_url = thumbnail.get("source", "")
                
                if not img_url:
                    continue
                
                # Nur echte Portrait-Bilder akzeptieren, keine Icons/Logos/Pack-Art
                bad_patterns = [
                    "cover_art", "icon", "logo", "ep14", "ep15", "ep16",
                    "pack", "expansion", "stuff", "game_pack", "kit",
                    "trait_", "aspiration_", "career_", "skill_",
                    "ts4_cas", "_cas.", "_cas_", "milestone", "deceased", "male.png", "female.png",
                    "relexpectations",
                ]
                img_lower = img_url.lower()
                if any(bad in img_lower for bad in bad_patterns):
                    continue
                
                # Skaliere auf 250px
                img_url = img_url.replace("/scale-to-width-down/225", "/scale-to-width-down/250")
                img_url = img_url.replace("/scale-to-width-down/300", "/scale-to-width-down/250")
                img_url = img_url.replace("/scale-to-width-down/400", "/scale-to-width-down/250")
                return img_url
    except Exception:
        pass
    
    # --- Stufe 4: Disambiguierungs-Seiten auflösen ---
    # Manche Sims (z.B. Holly Alto) haben eine Disambig-Seite, die eigentliche
    # Sims-4-Seite heißt dann z.B. "Holly Alto (The Sims 4: Get Famous)"
    try:
        wiki_name = english_name.replace(" ", "_")
        api_url = (
            f"https://sims.fandom.com/api.php?action=query"
            f"&titles={quote(wiki_name)}"
            f"&prop=categories|links&pllimit=50&format=json"
        )
        _wiki_rate_limit()
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id == "-1":
                    continue
                # Prüfe ob es eine Disambig-Seite ist
                cats = [c.get("title", "") for c in page_info.get("categories", [])]
                is_disambig = any("isambig" in c.lower() for c in cats)
                if not is_disambig:
                    continue
                # Suche nach Sims-4-Link
                links = [l.get("title", "") for l in page_info.get("links", [])]
                ts4_link = None
                for link in links:
                    if "The Sims 4" in link or "the sims 4" in link.lower():
                        ts4_link = link
                        break
                if ts4_link:
                    print(f"[WIKI] Disambig aufgelöst: {english_name} → {ts4_link}", flush=True)
                    # Bilder auf der aufgelösten Seite suchen
                    ts4_wiki = ts4_link.replace(" ", "_")
                    _wiki_rate_limit()
                    img_api = (
                        f"https://sims.fandom.com/api.php?action=query"
                        f"&titles={quote(ts4_wiki)}"
                        f"&prop=images&format=json"
                    )
                    r_imgs = requests.get(img_api, headers=headers, timeout=10)
                    if r_imgs.status_code == 200:
                        img_pages = r_imgs.json().get("query", {}).get("pages", {})
                        # Finde Portrait-Bild: Simname im Dateinamen, kein CAS/icon
                        sim_last = english_name.split()[-1].lower() if english_name else ""
                        sim_first = english_name.split()[0].lower() if english_name else ""
                        for _, ip in img_pages.items():
                            for img in ip.get("images", []):
                                title = img.get("title", "")  # z.B. "File:Holly Alto (Del Sol Valley).png"
                                tl = title.lower()
                                # Muss Sim-Namen enthalten, kein CAS/icon/trait
                                if sim_last not in tl and sim_first not in tl:
                                    continue
                                if "_cas" in tl or "cas." in tl or "icon" in tl or "trait" in tl:
                                    continue
                                # Bild-Info holen (Größe prüfen)
                                _wiki_rate_limit()
                                fi_api = (
                                    f"https://sims.fandom.com/api.php?action=query"
                                    f"&titles={quote(title.replace(' ', '_'))}"
                                    f"&prop=imageinfo&iiprop=url|size&format=json"
                                )
                                r_fi = requests.get(fi_api, headers=headers, timeout=10)
                                if r_fi.status_code == 200:
                                    fi_pages = r_fi.json().get("query", {}).get("pages", {})
                                    for fi_id, fi_info in fi_pages.items():
                                        if fi_id == "-1":
                                            continue
                                        ii = fi_info.get("imageinfo", [])
                                        if ii:
                                            w = ii[0].get("width", 0)
                                            h = ii[0].get("height", 0)
                                            url = ii[0].get("url", "")
                                            if url and h > 0 and w / h < 1.5:
                                                return _scale_url(url)
    except Exception:
        pass
    
    return None

def get_wiki_portrait_cached(sim_name: str) -> Optional[bytes]:
    """Gibt ein Wiki-Portrait zurück (kein HTTP).

    Reihenfolge:
    1. User-Ordner (portraits/Vorname Nachname.jpg) – benutzerdefiniert
    2. Eingebettete Portraits (in der EXE)
    3. Datei-Cache (wiki_portraits_cache/hash.jpg)
    """
    if not sim_name:
        return None
    # 1. User-Ordner (lesbare Namen, höchste Prio)
    user_img = _find_user_portrait(sim_name)
    if user_img:
        return user_img
    # 2. Eingebettete Portraits (kein I/O)
    english_name = german_to_english_name(sim_name)
    name_hash = hashlib.md5(english_name.encode()).hexdigest()
    embedded = get_embedded_portrait(name_hash)
    if embedded:
        return embedded
    # 3. Datei-Cache (für neue Sims die nicht eingebettet sind)
    cache_file = WIKI_CACHE_DIR / f"{name_hash}.jpg"
    if cache_file.exists():
        try:
            data = cache_file.read_bytes()
            if len(data) > 1000:
                return data
        except Exception:
            pass
    return None


def get_wiki_portrait(sim_name: str) -> Optional[bytes]:
    """Lädt Sim-Portrait aus Wiki, mit Caching und Name-Übersetzung.

    Reihenfolge:
    1. User-Ordner (portraits/Vorname Nachname.jpg) – benutzerdefiniert
    2. Eingebettete Portraits (in der EXE)
    3. Datei-Cache (wiki_portraits_cache/hash.jpg)
    4. Wiki-HTTP-Download (wird in User-Ordner gespeichert)
    """
    if not sim_name:
        return None

    # 1. User-Ordner (lesbare Namen, höchste Prio)
    user_img = _find_user_portrait(sim_name)
    if user_img:
        return user_img

    # Deutschen Namen ins Englische übersetzen
    english_name = german_to_english_name(sim_name)
    name_hash = hashlib.md5(english_name.encode()).hexdigest()

    # 2. Eingebettete Portraits (kein I/O)
    embedded = get_embedded_portrait(name_hash)
    if embedded:
        return embedded

    # 3. Datei-Cache prüfen (alter MD5-Cache)
    _ensure_cache_dir()
    cache_file = WIKI_CACHE_DIR / f"{name_hash}.jpg"
    if cache_file.exists():
        try:
            data = cache_file.read_bytes()
            if len(data) > 1000:
                # Migrieren: auch mit lesbarem Namen speichern
                _save_to_user_dir(sim_name, data)
                return data
        except Exception:
            pass

    # Negativ-Cache prüfen (Sim hat kein Wiki-Portrait)
    neg_cache = _load_negative_cache()
    if english_name in neg_cache:
        return None

    # 4. Vom Wiki laden - direkte Headshot-Suche
    try:
        img_url = _find_headshot_url(english_name)

        if not img_url:
            # Kein Headshot gefunden - im Negativ-Cache merken
            neg_cache[english_name] = time.time()
            _save_negative_cache(neg_cache)
            return None
        
        print(f"[WIKI] Headshot gefunden für {english_name}", flush=True)

        headers = {"User-Agent": "Sims4DuplicateScanner/2.6.1"}
        _wiki_rate_limit()
        response = requests.get(img_url, headers=headers, timeout=15)

        if response.status_code == 200 and len(response.content) > 1000:
            # In User-Ordner mit lesbarem Namen speichern
            _save_to_user_dir(sim_name, response.content)
            # Auch im alten Cache für Kompatibilität
            try:
                cache_file.write_bytes(response.content)
            except Exception:
                pass
            return response.content

    except Exception:
        pass

    return None


def _save_to_user_dir(sim_name: str, data: bytes):
    """Speichert Portrait im User-Ordner mit lesbarem Namen."""
    try:
        _ensure_user_dir()
        safe_name = _safe_filename(sim_name)
        out_file = USER_PORTRAITS_DIR / f"{safe_name}.jpg"
        if not out_file.exists():
            out_file.write_bytes(data)
    except Exception:
        pass