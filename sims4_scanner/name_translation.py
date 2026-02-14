# -*- coding: utf-8 -*-
"""Deutsch-Englisch-Übersetzung für Sim-Namen fürs Wiki.

Drei Stufen:
1. Statische Übersetzungstabelle (Vorname + Nachname, z.B. Kassandra Grusel → Cassandra Goth)
2. Deutsches Wiki Langlinks (automatisch: DE-Wiki-Seite → EN-Wiki-Seite)
3. Nachnamen-Fallback (nur Nachname tauschen, z.B. Goldblume → Goldbloom)
"""

import time
import json
import os
from pathlib import Path
from urllib.parse import quote
import requests
from typing import Optional

# --- Stufe 1: Volle Namensübersetzungen (nur wo sich auch Vornamen ändern) ---
FULL_NAME_TRANSLATIONS = {
    "Kassandra Grusel": "Cassandra Goth",
    "Pinki Keen": "Pinky Keen",
}

# --- Stufe 3: Nachnamen-Übersetzungen (Vorname bleibt gleich) ---
GERMAN_LASTNAME_TO_ENGLISH = {
    "Grusel": "Goth",
    "Goldblume": "Goldbloom",
}

# Rükwärts-Kompatibilität: alias
german_to_english = FULL_NAME_TRANSLATIONS

# Cache für DE-Wiki-Langlink-Ergebnisse (Stufe 2)
def _langlink_cache_path() -> str:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "Sims4DupeScanner", "wiki_portraits_cache", "_langlink_cache.json")
    return os.path.join(str(Path.home()), ".sims4_wiki_portraits_cache", "_langlink_cache.json")

_LANGLINK_CACHE_FILE = _langlink_cache_path()
_langlink_cache = {}  # type: dict

def _load_langlink_cache():
    """Lädt den Langlink-Cache (DE→EN Übersetzungen)."""
    global _langlink_cache
    try:
        if os.path.exists(_LANGLINK_CACHE_FILE):
            with open(_LANGLINK_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # Unbegrenzt gültig - nur bei manuellem Cache-Leeren neu laden
            _langlink_cache = data
    except Exception:
        _langlink_cache = {}

def _save_langlink_cache():
    """Speichert den Langlink-Cache."""
    try:
        os.makedirs(os.path.dirname(_LANGLINK_CACHE_FILE), exist_ok=True)
        with open(_LANGLINK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_langlink_cache, f, ensure_ascii=False)
    except Exception:
        pass

def _lookup_de_wiki_langlink(german_name: str) -> Optional[str]:
    """Sucht den deutschen Namen im DE-Wiki und folgt dem Langlink zum EN-Wiki.
    
    Returns: Englischer Name oder None
    """
    global _langlink_cache
    
    # Cache prüfen
    if not _langlink_cache:
        _load_langlink_cache()
    
    if german_name in _langlink_cache:
        return _langlink_cache[german_name].get("en")  # kann None sein (negativ-cache)
    
    wiki_name = german_name.replace(" ", "_")
    headers = {"User-Agent": "Sims4DuplicateScanner/2.6.1"}
    
    try:
        r = requests.get(
            "https://sims.fandom.com/de/api.php?action=query"
            "&titles=%s&prop=langlinks&lllang=en&format=json" % quote(wiki_name, safe=''),
            headers=headers, timeout=8
        )
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for pid, pinfo in pages.items():
                if pid != "-1":
                    for ll in pinfo.get("langlinks", []):
                        if ll.get("lang") == "en":
                            en_name = ll.get("*", "")
                            if en_name:
                                print("[WIKI] DE->EN Langlink: %s -> %s" % (german_name, en_name), flush=True)
                                _langlink_cache[german_name] = {"en": en_name, "ts": time.time()}
                                _save_langlink_cache()
                                return en_name
    except Exception:
        pass
    
    # Nicht gefunden - negativ cachen
    _langlink_cache[german_name] = {"en": None, "ts": time.time()}
    _save_langlink_cache()
    return None


def batch_lookup_de_wiki_langlinks(german_names: list) -> dict:
    """Batch-Lookup: Übersetzt bis zu 50 deutsche Namen auf einmal via Wiki-API.
    
    Die MediaWiki-API unterstützt titles=Name1|Name2|... (max 50 pro Request).
    Statt 200 einzelne Requests → 4 Batch-Requests.
    
    Returns: dict {german_name: english_name_or_None}
    """
    global _langlink_cache
    
    if not _langlink_cache:
        _load_langlink_cache()
    
    result = {}
    uncached = []
    
    # Erst Cache prüfen
    for name in german_names:
        if name in _langlink_cache:
            result[name] = _langlink_cache[name].get("en")
        else:
            uncached.append(name)
    
    if not uncached:
        return result
    
    headers = {"User-Agent": "Sims4DuplicateScanner/2.6.1"}
    batch_size = 50  # MediaWiki API Limit
    cache_dirty = False
    
    for i in range(0, len(uncached), batch_size):
        batch = uncached[i:i + batch_size]
        titles_param = "|".join(name.replace(" ", "_") for name in batch)
        
        try:
            r = requests.get(
                "https://sims.fandom.com/de/api.php?action=query"
                "&titles=%s&prop=langlinks&lllang=en&format=json" % quote(titles_param, safe='|_'),
                headers=headers, timeout=15
            )
            if r.status_code != 200:
                continue
            
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            # Mapping: normalisierter Titel → Original-Name
            normalized = {}
            for n in data.get("query", {}).get("normalized", []):
                normalized[n.get("to", "")] = n.get("from", "")
            
            found_titles = set()
            for pid, pinfo in pages.items():
                title = pinfo.get("title", "")
                # Finde den deutschen Original-Namen
                de_name = normalized.get(title, title).replace("_", " ")
                found_titles.add(de_name)
                
                if pid == "-1":
                    # Seite existiert nicht
                    _langlink_cache[de_name] = {"en": None, "ts": time.time()}
                    result[de_name] = None
                    cache_dirty = True
                    continue
                
                en_name = None
                for ll in pinfo.get("langlinks", []):
                    if ll.get("lang") == "en":
                        en_name = ll.get("*", "")
                        break
                
                if en_name:
                    print("[WIKI] DE->EN Langlink: %s -> %s" % (de_name, en_name), flush=True)
                    _langlink_cache[de_name] = {"en": en_name, "ts": time.time()}
                else:
                    _langlink_cache[de_name] = {"en": None, "ts": time.time()}
                result[de_name] = en_name
                cache_dirty = True
            
            # Namen die nicht in der Response waren (z.B. Redirect-Ziele)
            for name in batch:
                if name not in result:
                    _langlink_cache[name] = {"en": None, "ts": time.time()}
                    result[name] = None
                    cache_dirty = True
        except Exception:
            # Bei Fehler: einzelne Namen als nicht-gefunden markieren
            for name in batch:
                if name not in result:
                    result[name] = None
    
    # Cache nur 1× am Ende speichern statt pro Name
    if cache_dirty:
        _save_langlink_cache()
    
    return result


def german_to_english_name(german_name: str) -> str:
    """Übersetzt deutschen Sim-Namen ins Englische fürs Wiki.
    
    Dreistufig:
    1. Volle Namenstabelle (Kassandra Grusel -> Cassandra Goth)
    2. DE-Wiki Langlink (automatisch, cached)
    3. Nachnamen-Ersetzung (Goldblume -> Goldbloom)
    
    Falls keine Übersetzung gefunden: Name unverändert zurückgeben.
    """
    # Stufe 1: Direkte volle Übersetzung
    if german_name in FULL_NAME_TRANSLATIONS:
        return FULL_NAME_TRANSLATIONS[german_name]
    
    # Stufe 2: DE-Wiki Langlink (automatisch)
    en_from_wiki = _lookup_de_wiki_langlink(german_name)
    if en_from_wiki:
        return en_from_wiki
    
    # Stufe 3: Nachnamen-Ersetzung
    parts = german_name.rsplit(" ", 1)
    if len(parts) == 2:
        vorname, nachname = parts
        if nachname in GERMAN_LASTNAME_TO_ENGLISH:
            return vorname + " " + GERMAN_LASTNAME_TO_ENGLISH[nachname]
    
    # Sonderzeichen-Bereinigung (ö->o, etc.) für Wiki-Kompatibilität
    result = german_name
    result = result.replace("\u00f6", "o").replace("\u00d6", "O")
    result = result.replace("\u00fc", "u").replace("\u00dc", "U")
    result = result.replace("\u00e4", "a").replace("\u00c4", "A")
    
    return result


def batch_translate_names(german_names: list) -> dict:
    """Übersetzt eine Liste deutscher Sim-Namen ins Englische (optimiert für Batch).
    
    Nutzt die Batch-Wiki-API (50 Namen pro Request) statt einzelner Requests.
    Returns: dict {german_name: english_name}
    """
    result = {}
    need_wiki = []
    
    for name in german_names:
        # Stufe 1: Direkte volle Übersetzung
        if name in FULL_NAME_TRANSLATIONS:
            result[name] = FULL_NAME_TRANSLATIONS[name]
        else:
            need_wiki.append(name)
    
    # Stufe 2: Batch-Wiki-Lookup
    if need_wiki:
        wiki_results = batch_lookup_de_wiki_langlinks(need_wiki)
        for name in need_wiki:
            en = wiki_results.get(name)
            if en:
                result[name] = en
            else:
                # Stufe 3: Nachnamen-Ersetzung
                parts = name.rsplit(" ", 1)
                if len(parts) == 2:
                    vorname, nachname = parts
                    if nachname in GERMAN_LASTNAME_TO_ENGLISH:
                        result[name] = vorname + " " + GERMAN_LASTNAME_TO_ENGLISH[nachname]
                        continue
                # Sonderzeichen-Bereinigung
                clean = name
                clean = clean.replace("\u00f6", "o").replace("\u00d6", "O")
                clean = clean.replace("\u00fc", "u").replace("\u00dc", "U")
                clean = clean.replace("\u00e4", "a").replace("\u00c4", "A")
                result[name] = clean
    
    return result