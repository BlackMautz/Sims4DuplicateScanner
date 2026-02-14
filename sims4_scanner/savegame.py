# -*- coding: utf-8 -*-
"""Savegame-Analyse: Extrahiert Sims, Haushalte und Welten aus Sims 4 Spielständen."""

from __future__ import annotations

import os
import struct
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

from .protobuf import decode_varint, parse_pb, pb_string, pb_varint


# ── QFS / RefPack Dekompression ──────────────────────────────────

def _decompress_qfs(data: bytes) -> bytes:
    """Dekomprimiert QFS/RefPack-komprimierte Daten (EA-internes Format).
    Optimiert: verwendet memoryview + bytearray-Slicing statt Byte-für-Byte."""
    if len(data) < 6 or data[1] != 0xFB:
        return data

    flags = data[0]
    pos = 2

    if flags & 0x80:
        uncomp_size = (data[pos] << 24) | (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3]
        pos += 4
    else:
        uncomp_size = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
        pos += 3

    out = bytearray(uncomp_size)
    out_pos = 0
    dlen = len(data)

    while pos < dlen and out_pos < uncomp_size:
        b0 = data[pos]

        if b0 < 0x80:
            if pos + 1 >= dlen:
                break
            b1 = data[pos + 1]
            pos += 2
            num_plain = b0 & 0x03
            num_copy = ((b0 & 0x1C) >> 2) + 3
            copy_offset = ((b0 & 0x60) << 3) + b1 + 1

        elif b0 < 0xC0:
            if pos + 2 >= dlen:
                break
            b1 = data[pos + 1]
            b2 = data[pos + 2]
            pos += 3
            num_plain = ((b1 & 0xC0) >> 6) & 0x03
            num_copy = (b0 & 0x3F) + 4
            copy_offset = ((b1 & 0x3F) << 8) + b2 + 1

        elif b0 < 0xE0:
            if pos + 3 >= dlen:
                break
            b1 = data[pos + 1]
            b2 = data[pos + 2]
            b3 = data[pos + 3]
            pos += 4
            num_plain = b0 & 0x03
            num_copy = ((b0 & 0x0C) << 6) + b3 + 5
            copy_offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1

        elif b0 < 0xFC:
            pos += 1
            num_plain = ((b0 & 0x1F) << 2) + 4
            num_copy = 0
            copy_offset = 0

        else:
            pos += 1
            num_plain = b0 & 0x03
            num_copy = 0
            copy_offset = 0

        # Kopiere Plain-Bytes als Block statt einzeln
        if num_plain > 0:
            end_plain = min(pos + num_plain, dlen)
            avail = end_plain - pos
            out_end = min(out_pos + avail, uncomp_size)
            chunk = out_end - out_pos
            if chunk > 0:
                out[out_pos:out_end] = data[pos:pos + chunk]
                out_pos = out_end
                pos += chunk

        # Backreference: muss Byte-für-Byte bleiben wegen möglicher Überlappung
        if num_copy > 0:
            src = out_pos - copy_offset
            if src >= 0 and copy_offset >= num_copy:
                # Keine Überlappung → Block-Kopie
                end_copy = min(out_pos + num_copy, uncomp_size)
                chunk = end_copy - out_pos
                out[out_pos:end_copy] = out[src:src + chunk]
                out_pos = end_copy
            else:
                # Überlappung → einzeln
                for _ in range(num_copy):
                    if out_pos >= uncomp_size or src < 0:
                        break
                    out[out_pos] = out[src]
                    out_pos += 1
                    src += 1

    return bytes(out[:out_pos])


# ── DBPF-Index-Leser für Save-Dateien ───────────────────────────

def _read_save_entries(path: str) -> list:
    """Liest alle DBPF-Einträge einer Sims 4 Save-Datei."""
    entries = []
    try:
        with open(path, "rb") as f:
            header = f.read(96)
            if len(header) < 96 or header[:4] != b"DBPF":
                return []

            index_count = struct.unpack_from("<I", header, 36)[0]
            index_offset = struct.unpack_from("<Q", header, 64)[0]  # 64-bit Offset (DBPF v2)

            f.seek(index_offset)
            # DBPF 2.1: Lies Index-Daten (großzügig, max 40 bytes/entry)
            all_idx = f.read(index_count * 40)

            epos = 0
            # ── DBPF 2.1 Index-Flags ──
            # Die ersten 4 Bytes geben an, welche Felder für ALLE Einträge
            # konstant sind. Für jedes gesetzte Bit folgt ein 4-Byte-Wert
            # direkt nach den Flags (vor den eigentlichen Einträgen).
            # Felder: 0=Type, 1=Group, 2=InstanceHigh, 3=InstanceLow,
            #         4=Offset, 5=FileSize|Flags, 6=MemSize
            idx_flags = struct.unpack_from("<I", all_idx, epos)[0]; epos += 4

            # Konstante Werte lesen
            const_vals = {}
            for bit in range(7):
                if idx_flags & (1 << bit):
                    const_vals[bit] = struct.unpack_from("<I", all_idx, epos)[0]
                    epos += 4

            for _ in range(index_count):
                if epos + 4 > len(all_idx):
                    break

                # Pro Feld: Konstanten-Wert nutzen oder aus Index lesen
                def _read_field(bit):
                    nonlocal epos
                    if bit in const_vals:
                        return const_vals[bit]
                    val = struct.unpack_from("<I", all_idx, epos)[0]
                    epos += 4
                    return val

                t = _read_field(0)       # Type
                g = _read_field(1)       # Group
                ih = _read_field(2)      # Instance High
                il = _read_field(3)      # Instance Low
                offset = _read_field(4)  # Offset
                fsf = _read_field(5)     # FileSize | Flags
                filesize = fsf & 0x7FFFFFFF
                compressed = bool(fsf & 0x80000000)
                memsize = _read_field(6) # MemSize
                if compressed:
                    epos += 4  # Skip comp_type + committed
                instance = (ih << 32) | il
                entries.append({
                    "type": t, "group": g, "instance": instance,
                    "offset": offset, "size": filesize,
                    "compressed": compressed, "memsize": memsize,
                })
    except Exception:
        pass
    return entries


def _read_entry_data(path: str, entry: dict) -> bytes:
    """Liest und dekomprimiert einen DBPF-Eintrag."""
    try:
        with open(path, "rb") as f:
            f.seek(entry["offset"])
            raw = f.read(entry["size"])
        if entry["compressed"] and len(raw) > 5 and raw[1] == 0xFB:
            return _decompress_qfs(raw)
        return raw
    except Exception:
        return b""


# ── Protobuf-Helfer (nutzt shared protobuf.py) ──────────────────

# Lokale Aliase für Abwärtskompatibilität
_decode_varint = decode_varint
_parse_pb = parse_pb
_get_pb_string = pb_string
_get_pb_varint = pb_varint


# ── Sim-Extraktion ──────────────────────────────────────────────

# Alter-Mapping (f8 Varint → Bezeichnung)
_AGE_MAP = {
    1: "Baby",
    2: "Kleinkind",
    4: "Kind",
    8: "Teen",
    16: "Junger Erwachsener",
    32: "Erwachsener",
    64: "Älterer",
    128: "Älterer",
}

_AGE_EMOJI = {
    "Baby": "👶", "Kleinkind": "🧒", "Kind": "🧒",
    "Teen": "🧑", "Junger Erwachsener": "🧑", "Erwachsener": "🧑",
    "Älterer": "👴",
}

# Geschlecht-Mapping (f7 Varint → Bezeichnung)
_GENDER_MAP = {4096: "Männlich", 8192: "Weiblich"}
_GENDER_EMOJI = {"Männlich": "♂️", "Weiblich": "♀️"}

# ── Skill-Map (Ranked-Statistic IDs aus f30.f13 → Deutsche Namen) ────────────
# WICHTIG: Dies sind die RANKED-STAT-IDs (XP-basiert), NICHT die Commodity-IDs!
# f30.f13 = echte Skills (XP-Werte), f30.f2 = Commodities/Motive (irrelevant)
_SKILL_MAP = {
    # ─── Base Game – Haupt-Skills (Ranked Stats) ───
    # Fix: 16698 = Komödie (war fälschlich "Schreiben"), 16700 = Gartenarbeit (war "Violine")
    16699: "Charisma",        16698: "Komödie",        16705: "Kochen",
    16659: "Fitness",         16695: "Mixologie",      16700: "Gartenarbeit",
    16701: "Gourmet-Kochen",  16702: "Gitarre",        16703: "Programmieren",
    16704: "Heimwerken",      16706: "Logik",           16707: "Unfug",
    16708: "Malerei",         16709: "Klavier",        16710: "Raketenwiss.",
    16713: "Violine",         16714: "Schreiben",
    # Base Game – Neben-Skills
    16712: "Videospiele",     39397: "Angeln",
    # Kind-Skills
    16718: "Kreativität (K)", 16719: "Geist (K)",
    16720: "Motorik (K)",     16721: "Soziales (K)",
    # Kleinkind-Skills
    136140: "Bewegung (KK)",  140170: "Kommunikation (KK)",
    140504: "Denken (KK)",    140706: "Phantasie (KK)",
    144913: "Töpfchen (KK)",
    # Expansion / Game / Stuff Packs
    104198: "Backen",         101920: "Herbologie",
    105774: "Fotografie",     117858: "Wellness",
    # Get to Work – versteckte Retail-Skills
    111902: "Verkaufen",      111903: "Arbeitsmoral",
    121612: "DJ-Mixen",       128145: "Tanzen",
    137811: "Singen",         149556: "Vampir-Lehre",
    149665: "Orgel",          160504: "Erziehung",
    161190: "Tierarzt",       161220: "Haustier-Training",
    174237: "Archäologie",    174687: "Selvadorad. Kultur",
    186703: "Blumenarrangement",
    192655: "Medien-Produkt.", 194727: "Schauspiel",
    # Discover University – versteckte Skills
    212561: "Tischtennis",    213548: "Saftpong",
    217413: "Robotik",        221014: "Forschung & Debatte",
    231908: "Fertigung",      234806: "Saftmachen",
    239521: "Stricken",       245613: "Skifahren",
    245639: "Klettern",       246054: "Snowboarden",
    259758: "Kreuzstich",
    # High School Years
    274197: "Unternehmertum",
    # Horse Ranch
    315761: "Nektar-Herst.",  322708: "Reiten",
    324631: "Temperament (P)", 324632: "Agilität (P)",
    324633: "Springen (P)",   324634: "Ausdauer (P)",
    # Crystal Creations Kit
    350972: "Gemmologie",
    # Lovestruck
    368684: "Romantik",
    # Businesses & Hobbies
    371129: "Töpfern",        371481: "Tätowieren",
    # Bowling Night Stuff
    158659: "Bowling",
    # Paranormal Stuff
    255249: "Medium",
    # Life & Death
    380495: "Thanatologie",
    # Enchanted By Nature
    434909: "Naturleben",     439222: "Kräuterkunde",
    # Adventure Awaits / Royalty & Legacy (IDs aus S4CL noch nicht bestätigt)
    450214: "Skill (AA/RL?)", 452067: "Skill (AA/RL?)",
    454328: "Skill (AA/RL?)",
}

# ── XP-Schwellwerte (kumulativ) pro Level ────────────────────────────────────
# Ermittelt aus EA-Savegame-Analyse: Vorgegebene Sims haben exakte Werte,
# die den Ausgaben von convert_from_user_value(level) entsprechen.
# Die EA-Python-Engine nutzt event_intervals (Deltas pro Level-Stufe),
# convert_from_user_value(level) = sum(event_intervals[:level]).
#
# Erwachsene Haupt-Skills (10 Level):
#   Deltas: [0, 1540, 2160, 3600, 5280, 7200, 10140, 13440, 17100, 21120]
_MAJOR_SKILL_XP = [0, 1540, 3700, 7300, 12580, 19780, 29920, 43360, 60460, 81580]

# Kind-Skills (10 Level, eigene XP-Kurve):
#   Kreativität, Geist, Motorik, Soziales
_CHILD_SKILL_XP = [0, 1100, 2780, 5130, 7749, 10899, 14309, 17999, 21969, 26199]

# Minor-Skills (5 Level): Tanzen, Selvadorad. Kultur, Haustier-Training,
# Fotografie, Medien-Produkt., Unternehmertum, Nektar-Herst., Thanatologie,
# Tischtennis, Saftpong, Verkaufen, Arbeitsmoral (Retail-hidden)
_MINOR_SKILL_XP = [0, 800, 2000, 5000, 12580]

# Skill-ID → Typ-Zuordnung
_MINOR_SKILLS = {
    128145, 174687, 161220,           # Tanzen, Selvadorad. Kultur, Haustier-Training
    105774, 192655,                   # Fotografie, Medien-Produkt.
    274197, 315761, 380495,           # Unternehmertum, Nektar-Herst., Thanatologie
    212561, 213548,                   # Tischtennis, Saftpong (hidden)
    111902, 111903,                   # Verkaufen, Arbeitsmoral (Retail-hidden)
    158659,                           # Bowling
    255249,                           # Medium
}
_CHILD_SKILLS = {16718, 16719, 16720, 16721}  # Kreativität, Geist, Motorik, Soziales
_HORSE_SKILLS = {324631, 324632, 324633, 324634}  # Temperament, Agilität, Springen, Ausdauer

# ── Bedürfnisse (Commodity-IDs aus f30.f2) ───────────────────────────────────
_NEED_MAP = {
    16652: ("Blase",    "🚽"),
    16654: ("Energie",  "⚡"),
    16655: ("Spaß",     "🎮"),
    16656: ("Hunger",   "🍔"),
    16657: ("Hygiene",  "🚿"),
    16658: ("Sozial",   "💬"),
}


def _extract_needs(sub: dict) -> list:
    """Extrahiert Bedürfnisse aus f30 → f2 (CommodityTracker) → f1 (Einträge).

    Gibt Liste von dicts zurück: [{name, value, emoji, percent}]
    Werte reichen typisch von -100 bis +100, normalisiert auf 0-100%.
    """
    needs = []
    for t, v in sub.get(30, []):
        if t != "bytes":
            continue
        f30 = _parse_pb(v, max_depth=1)
        for st, sv in f30.get(2, []):
            if st != "bytes":
                continue
            container = _parse_pb(sv, max_depth=1)
            for sst, ssv in container.get(1, []):
                if sst != "bytes":
                    continue
                entry = _parse_pb(ssv, max_depth=1)
                nid = None
                nval = None
                for et, ev in entry.get(1, []):
                    if et == "varint":
                        nid = ev
                for et, ev in entry.get(2, []):
                    if et == "fixed32":
                        nval = struct.unpack("<f", struct.pack("<I", ev))[0]
                if nid in _NEED_MAP and nval is not None:
                    name, emoji = _NEED_MAP[nid]
                    # Normalisierung: Werte gehen -100..+100, auf 0-100% mappen
                    pct = max(0, min(100, (nval + 100) / 2.0))
                    needs.append({
                        "name": name,
                        "value": round(nval, 1),
                        "emoji": emoji,
                        "percent": round(pct),
                    })
        break  # Nur erster f30-Block
    # Nach Wert absteigend sortieren
    needs.sort(key=lambda x: -x["value"])
    return needs


def _xp_to_level(xp: float, skill_id: int) -> tuple:
    """Konvertiert XP-Punkte zu (level, max_level)."""
    if skill_id in _MINOR_SKILLS:
        thresholds = _MINOR_SKILL_XP
        max_lvl = 5
    elif skill_id in _CHILD_SKILLS:
        thresholds = _CHILD_SKILL_XP
        max_lvl = 10
    else:
        thresholds = _MAJOR_SKILL_XP
        max_lvl = 10
    level = 1
    for i, threshold in enumerate(thresholds):
        if xp >= threshold:
            level = i + 1
    return min(level, max_lvl), max_lvl


def _extract_skills(sub: dict) -> list:
    """Extrahiert Skills aus f30 → f13 (RankedStatisticTracker) → f1 (Einträge).

    f30.f13 enthält die echten Skill-XP-Werte (RankedStatistic).
    Gibt Liste von (skill_name, level, max_level, raw_xp) zurück.
    Sortierung: bekannte Skills nach XP absteigend, Mod-Skills am Ende.
    """
    skills = []
    for t, v in sub.get(30, []):
        if t != "bytes":
            continue
        f30 = _parse_pb(v, max_depth=1)
        for st, sv in f30.get(13, []):
            if st != "bytes":
                continue
            container = _parse_pb(sv, max_depth=1)
            for sst, ssv in container.get(1, []):
                if sst != "bytes":
                    continue
                entry = _parse_pb(ssv, max_depth=1)
                sid = None
                xp_val = None
                for et, ev in entry.get(1, []):
                    if et == "varint":
                        sid = ev
                for et, ev in entry.get(2, []):
                    if et == "fixed32":
                        xp_val = struct.unpack("<f", struct.pack("<I", ev))[0]
                if sid is not None and xp_val is not None:
                    if sid in _SKILL_MAP:
                        name = _SKILL_MAP[sid]
                        is_mod = False
                    else:
                        # Unbekannte Skills (Mods/DLCs) trotzdem zählen
                        name = "Mod-Skill #{}".format(sid % 10000)
                        is_mod = True
                    lvl, max_lvl = _xp_to_level(xp_val, sid)
                    if lvl >= 1:
                        skills.append((name, lvl, max_lvl, xp_val, is_mod))
    # Duplikate entfernen (gleicher Skill-Name → höchsten Level behalten)
    seen = {}
    for name, lvl, mlvl, xp, is_mod in skills:
        if name not in seen or xp > seen[name][3]:
            seen[name] = (name, lvl, mlvl, xp, is_mod)
    skills = list(seen.values())
    # Bekannte Skills nach XP absteigend, Mod-Skills am Ende
    skills.sort(key=lambda x: (x[4], -x[3]))
    return skills


def _extract_mood(sub: dict) -> tuple:
    """Extrahiert Stimmungswert aus f53 (fixed32 → float).

    Gibt (mood_value, mood_label, mood_emoji) zurück.
    """
    for t, v in sub.get(53, []):
        if t == "fixed32":
            fval = struct.unpack("<f", struct.pack("<I", v))[0]
            if fval > 30:
                return (fval, "Sehr glücklich", "😊")
            elif fval > 10:
                return (fval, "Glücklich", "🙂")
            elif fval > -10:
                return (fval, "Neutral", "😐")
            elif fval > -30:
                return (fval, "Traurig", "😢")
            else:
                return (fval, "Sehr traurig", "😭")
    return (0, "Unbekannt", "")


def _extract_sim_age_days(sub: dict) -> int:
    """Extrahiert Sim-Alter in Spieltagen aus f34 (Minuten seit Erstellung)."""
    v = _get_pb_varint(sub, 34)
    return v // (24 * 60) if v else 0


# ── Fallback-Mapping: Region-ID → Weltname für namenlose Nachbarschaften ──
# Neuere DLCs speichern den Weltnamen nicht im Protobuf-Feld f3.
# Diese Welten werden über ihre f4-Varint-Region-ID identifiziert.
REGION_ID_MAP: dict = {
    329915: "Chestnut Ridge",      # Horse Ranch
    359471: "Tomarang",            # For Rent
    395690: "Ciudad Enamorada",    # Lovestruck
    415482: "Ravenwood",           # Life & Death
    417419: "Nordhaven",           # Businesses & Hobbies
    455807: "Innisgreen",          # Enchanted by Nature
    474272: "Gibbi Point",         # Adventure Awaits
    487001: "Ondarion",            # Royalty & Legacy
}


def _extract_sims_from_zone(zone_data: bytes) -> list:
    """Extrahiert Sim-Daten aus der Zone-Ressource (Typ 0x0D).

    Protobuf-Struktur pro Sim-Blob (f6-Eintrag):
        f1  = Sim-ID (fixed64)
        f5  = Vorname  (string)
        f6  = Nachname (string)
        f7  = Geschlecht (varint: 4096=M, 8192=W)
        f8  = Alter (varint: 1=Baby..64=Älterer)
        f12 = Hautton (string, CSV-Floats)
        f15 = Partner-Sim-ID (fixed64)
        f18 = Traits-Blob (bytes)
        f21 = Beziehungen-Blob (bytes)
        f22 = Haushaltsname (string)
        f30 = Skills/Statistiken-Blob (bytes)
        f34 = Sim-Alter in Minuten (varint)
        f53 = Stimmungswert (fixed32 → float, -75..+75)
        f63 = Okkult-Sekundärform (bytes, nur bei Okkulten)
    """
    top_fields = _parse_pb(zone_data, max_depth=1)
    sims = []

    # ── Zone→Welt-Mapping aus f4 (Nachbarschaften) ──
    # f4 enthält Nachbarschafts-Blobs mit:
    #   f3 = Nachbarschaftsname (bytes → string, z.B. "Willow Creek")
    #   f5 = Lot-Einträge, jeweils mit f2 = Zone-ID (fixed64)
    # Haushalt-f4 (home_zone) verweist auf eine dieser Zone-IDs.
    zone_to_world: dict = {}  # zone_id → Weltname
    for vtype, nb_blob in top_fields.get(4, []):
        if vtype != "bytes" or len(nb_blob) < 10:
            continue
        nb_sub = _parse_pb(nb_blob, max_depth=1)
        nb_name = ""
        for t, v in nb_sub.get(3, []):
            if t == "bytes":
                try:
                    nb_name = v.decode("utf-8", errors="replace")
                except Exception:
                    pass
        # Fallback: Namenlose Nachbarschaften über Region-ID identifizieren
        if not nb_name:
            region_id = _get_pb_varint(nb_sub, 4)
            if region_id and region_id in REGION_ID_MAP:
                nb_name = REGION_ID_MAP[region_id]
        if not nb_name:
            continue
        for lt, lv in nb_sub.get(5, []):
            if lt != "bytes":
                continue
            lot_sub = _parse_pb(lv, max_depth=1)
            for t, v in lot_sub.get(2, []):
                if t == "fixed64" and v:
                    zone_to_world[v] = nb_name

    # ── Haushalt→Welt-Mapping aus f5 ──
    # f5.f3 = Haushaltsname, f5.f4 = home_zone (fixed64 → Zone-ID)
    household_to_world: dict = {}  # Haushaltsname → Weltname

    # ── Aktive Haushalte ermitteln (f5-Einträge) ──
    # f5 enthält Haushaltsdaten.  f31=1 → gespielter Haushalt.
    # f14=0 → eigener Haushalt (nicht Basegame/Galerie).
    # f3 = Haushaltsname, der mit sim f22 übereinstimmt.
    played_household_names: set = set()
    for vtype, hh_blob in top_fields.get(5, []):
        if vtype != "bytes" or len(hh_blob) < 10:
            continue
        hh_sub = _parse_pb(hh_blob, max_depth=1)

        # Haushaltsname (f3 = bytes)
        hh_name = ""
        for t, v in hh_sub.get(3, []):
            if t == "bytes":
                try:
                    hh_name = v.decode("utf-8", errors="replace")
                except Exception:
                    pass

        # Home-Zone (f4 = fixed64)
        home_zone = None
        for t, v in hh_sub.get(4, []):
            if t == "fixed64":
                home_zone = v
                break
        if hh_name and home_zone and home_zone in zone_to_world:
            household_to_world[hh_name] = zone_to_world[home_zone]

        hh_f31 = _get_pb_varint(hh_sub, 31)
        if hh_f31 and hh_f31 > 0:
            hh_f14 = _get_pb_varint(hh_sub, 14)
            if hh_f14 == 0:  # Eigener Haushalt, nicht Basegame
                if hh_name:
                    played_household_names.add(hh_name)

    # ── Relationship-Service: Beziehungsanzahl aus f2.f8.f13 ──
    # Speichert für jede Sim-ID die Anzahl der Beziehungspaare.
    rel_counts = defaultdict(int)  # sim_id → Anzahl Beziehungen
    for vtype, f2_blob in top_fields.get(2, []):
        if vtype != "bytes":
            continue
        f2_sub = _parse_pb(f2_blob, max_depth=1)
        for vt2, f8_blob in f2_sub.get(8, []):
            if vt2 != "bytes":
                continue
            f8_sub = _parse_pb(f8_blob, max_depth=1)
            for vt3, f13_blob in f8_sub.get(13, []):
                if vt3 != "bytes":
                    continue
                f13_sub = _parse_pb(f13_blob, max_depth=1)
                for vt4, pair_blob in f13_sub.get(1, []):
                    if vt4 != "bytes":
                        continue
                    pair = _parse_pb(pair_blob, max_depth=1)
                    sim_a = _get_pb_varint(pair, 1)
                    sim_b = _get_pb_varint(pair, 2)
                    if sim_a and sim_b:
                        rel_counts[sim_a] += 1
                        rel_counts[sim_b] += 1
                break  # Nur erster f13-Block
            break  # Nur erster f8-Block
        break  # Nur erster f2-Block

    # f6 enthält die einzelnen Sim-Datensätze
    if 6 not in top_fields:
        return sims

    # Erster Pass: Sim-IDs aufsammeln für Partner-Zuordnung
    id_to_idx = {}  # sim_id -> index in sims
    raw_list = []   # (sub-fields, idx)

    for idx, (vtype, sim_blob) in enumerate(top_fields[6]):
        if vtype != "bytes" or len(sim_blob) < 10:
            continue
        sub = _parse_pb(sim_blob, max_depth=1)
        first_name = _get_pb_string(sub, 5)
        last_name = _get_pb_string(sub, 6)
        if not first_name or not last_name:
            continue
        # Sim-ID (f1 fixed64)
        sim_id = None
        for t, v in sub.get(1, []):
            if t == "fixed64":
                sim_id = v
                break
        raw_list.append((sub, idx, first_name, last_name, sim_id))
        if sim_id is not None:
            id_to_idx[sim_id] = len(raw_list) - 1

    # Zweiter Pass: Alle Daten extrahieren
    for raw_idx, (sub, idx, first_name, last_name, sim_id) in enumerate(raw_list):
        household = _get_pb_string(sub, 22)

        # Geschlecht
        f7 = _get_pb_varint(sub, 7)
        gender = _GENDER_MAP.get(f7, "Unbekannt")
        gender_emoji = _GENDER_EMOJI.get(gender, "")

        # Alter
        f8 = _get_pb_varint(sub, 8)
        age = _AGE_MAP.get(f8, "Unbekannt")
        age_emoji = _AGE_EMOJI.get(age, "🧑")

        # Okkult-Erkennung (f63 = hat Sekundärform → Okkult)
        is_occult = 63 in sub
        species = "Okkult" if is_occult else ""

        # Partner (f15 = fixed64 → Sim-ID eines anderen Sims)
        partner_name = ""
        for t, v in sub.get(15, []):
            if t == "fixed64" and v in id_to_idx:
                pidx = id_to_idx[v]
                _, _, pfirst, plast, _ = raw_list[pidx]
                partner_name = f"{pfirst} {plast}"
                break

        # Hautton (f12 = CSV-Floats → Kategorie)
        skin_tone = ""
        skin_str = _get_pb_string(sub, 12)
        if skin_str:
            try:
                vals = [float(x) for x in skin_str.strip(",").split(",") if x]
                dominant = max(vals) if vals else 0
                if dominant > 0.5:
                    skin_tone = "Dunkel"
                elif dominant > 0.2:
                    skin_tone = "Mittel"
                elif dominant > 0:
                    skin_tone = "Hell"
                else:
                    skin_tone = "Sehr hell"
            except (ValueError, TypeError):
                pass

        # Trait-Anzahl (f18 → Sub-Blob parsen → Entries zählen)
        trait_count = 0
        for t, v in sub.get(18, []):
            if t == "bytes":
                trait_sub = _parse_pb(v, max_depth=1)
                for fnum, entries in trait_sub.items():
                    for tt, tv in entries:
                        if tt == "bytes":
                            ssub = _parse_pb(tv, max_depth=1)
                            trait_count += sum(
                                1 for _entries in ssub.values()
                                for _t, _v in _entries if _t == "varint"
                            )
                        elif tt == "varint":
                            trait_count += 1

        # Beziehungsanzahl aus Relationship-Service (f2.f8.f13)
        relationship_count = rel_counts.get(sim_id, 0) if sim_id else 0

        # Skills (f30 → f13 = RankedStatisticTracker → XP-basierte Level)
        skills = _extract_skills(sub)
        skill_count = len(skills)

        # Bedürfnisse (f30 → f2 = CommodityTracker → Motive)
        needs = _extract_needs(sub)

        # Stimmung (f53)
        mood_val, mood_label, mood_emoji = _extract_mood(sub)

        # Sim-Alter in Tagen (f34)
        sim_age_days = _extract_sim_age_days(sub)

        # Aktiv gespielt?
        # f42=1 → Sim wurde irgendwann vom Spieler gesteuert
        # ODER: Sim gehört zum aktiven Haushalt (f31=1 + f14=0)
        is_played = (
            _get_pb_varint(sub, 42) == 1
            or (household or "") in played_household_names
        )

        sims.append({
            "sim_id": sim_id if sim_id is not None else 0,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "household": household if household else last_name,
            "world": household_to_world.get(household, household_to_world.get(last_name, "")),
            "gender": gender,
            "gender_emoji": gender_emoji,
            "age": age,
            "age_emoji": age_emoji,
            "species": species,
            "partner": partner_name,
            "skin_tone": skin_tone,
            "trait_count": trait_count,
            "relationship_count": relationship_count,
            "skill_count": skill_count,
            "top_skills": [{"name": n, "level": l, "max_level": ml}
                           for n, l, ml, _xp, _mod in skills],
            "needs": needs,
            "mood_value": round(mood_val, 1),
            "mood_label": mood_label,
            "mood_emoji": mood_emoji,
            "sim_age_days": sim_age_days,
            "is_played": is_played,
            "index": idx,
        })

    return sims


# Alters-Ordnung für Familien-Erkennung (niedrig = jung)
_AGE_ORDER = {
    "Baby": 0, "Kleinkind": 1, "Kind": 2, "Teen": 3,
    "Junger Erwachsener": 4, "Erwachsener": 5, "Älterer": 6,
}

_ADULT_AGES = {"Junger Erwachsener", "Erwachsener", "Älterer"}
_CHILD_AGES = {"Baby", "Kleinkind", "Kind", "Teen"}


def _detect_family_roles(sims: list) -> None:
    """Erkennt Familienrollen innerhalb von Haushalten.

    Fügt jedem Sim folgende Felder hinzu:
      - family_role: 'Elternteil', 'Kind', 'Geschwister', 'Einzelgänger'
      - family_members: [{'name': ..., 'role': ..., 'age': ...}, ...]
      - rel_score: 'wenige' | 'einige' | 'viele' | 'sehr viele'
    """
    # Haushalte gruppieren
    hh_groups = defaultdict(list)
    for sim in sims:
        hh_groups[sim["household"]].append(sim)

    for hh_name, members in hh_groups.items():
        if len(members) == 1:
            sim = members[0]
            sim["family_role"] = "Einzelgänger"
            sim["family_members"] = []
            continue

        # Rollen-Erkennung innerhalb des Haushalts
        adults = [s for s in members if s["age"] in _ADULT_AGES]
        children = [s for s in members if s["age"] in _CHILD_AGES]

        # Partner-Set: Sims die einen Partner im Haushalt haben
        partner_set = set()
        for s in members:
            if s["partner"]:
                partner_set.add(s["full_name"])
                partner_set.add(s["partner"])

        for sim in members:
            others = [m for m in members if m["full_name"] != sim["full_name"]]

            if sim["age"] in _ADULT_AGES:
                if children:
                    sim["family_role"] = "Elternteil"
                elif len(adults) > 1 and sim["full_name"] in partner_set:
                    sim["family_role"] = "Partner"
                elif len(adults) > 1:
                    # Gleicher Nachname = Geschwister, sonst Mitbewohner
                    same_ln = [a for a in adults if a["last_name"] == sim["last_name"] and a["full_name"] != sim["full_name"]]
                    sim["family_role"] = "Geschwister" if same_ln else "Mitbewohner"
                else:
                    sim["family_role"] = "Einzelgänger"
            elif sim["age"] in _CHILD_AGES:
                if adults:
                    sim["family_role"] = "Kind"
                else:
                    # Nur Kinder im Haushalt → Geschwister
                    sim["family_role"] = "Geschwister"

            # Familienmitglieder-Liste
            sim["family_members"] = [
                {
                    "name": o["full_name"],
                    "role": _other_role_label(sim, o, adults, children, partner_set),
                    "age": o["age"],
                    "gender": o["gender"],
                }
                for o in others
            ]

    # Beziehungs-Score
    for sim in sims:
        rc = sim.get("relationship_count", 0)
        if rc == 0:
            sim["rel_score"] = "keine"
        elif rc <= 3:
            sim["rel_score"] = "wenige"
        elif rc <= 8:
            sim["rel_score"] = "einige"
        elif rc <= 15:
            sim["rel_score"] = "viele"
        else:
            sim["rel_score"] = "sehr viele"


def _other_role_label(sim: dict, other: dict, adults: list, children: list,
                      partner_set: set) -> str:
    """Bestimmt wie 'other' aus Sicht von 'sim' benannt wird."""
    # Partner-Beziehung
    if sim.get("partner") == other["full_name"]:
        return "Partner"

    sim_is_adult = sim["age"] in _ADULT_AGES
    other_is_adult = other["age"] in _ADULT_AGES

    if sim_is_adult and not other_is_adult:
        return "Kind"
    if not sim_is_adult and other_is_adult:
        return "Elternteil"
    if sim["last_name"] == other["last_name"]:
        return "Geschwister"
    if sim_is_adult and other_is_adult:
        return "Mitbewohner"
    return "Mitbewohner"


def _extract_worlds_from_zone(zone_data: bytes) -> list:
    """Extrahiert Welten/Nachbarschaften aus f4."""
    fields = _parse_pb(zone_data, max_depth=1)
    worlds = []

    # Bekannte Weltennamen
    WORLD_NAMES = {
        "Willow": "Willow Creek", "Oasis": "Oasis Springs",
        "Windenburg": "Windenburg", "San": "San Sequoia",
        "Newcrest": "Newcrest", "Magnolia": "Magnolia Promenade",
        "Granite": "Granite Falls", "Forgotten": "Forgotten Hollow",
        "Brindleton": "Brindleton Bay", "Selvadorada": "Selvadorada",
        "Del": "Del Sol Valley", "Stranger": "StrangerVille",
        "Sulani": "Sulani", "Britechester": "Britechester",
        "Glimmerbrook": "Glimmerbrook", "Evergreen": "Evergreen Harbor",
        "Batuu": "Batuu", "Komorebi": "Mt. Komorebi",
        "Henford": "Henford-on-Bagley", "Tartosa": "Tartosa",
        "Copperdale": "Copperdale", "Moonwood": "Moonwood Mill",
    }

    if 4 not in fields:
        return worlds

    for vtype, world_blob in fields[4]:
        if vtype != "bytes":
            continue
        world_name = ""
        for key, full_name in WORLD_NAMES.items():
            if key.encode("ascii") in world_blob:
                world_name = full_name
                break
        if world_name and world_name not in worlds:
            worlds.append(world_name)

    return worlds


# ── Hauptfunktion ───────────────────────────────────────────────

def analyze_savegames(saves_dir: str, selected_save: str = "") -> dict:
    """Analysiert den aktuellsten (oder gewählten) Spielstand.

    Args:
        saves_dir: Pfad zum saves-Ordner
        selected_save: Optionaler Dateiname eines bestimmten Saves

    Returns:
        dict mit keys: active_save, sims, households, worlds, available_saves, error
    """
    from .config import load_savegame_cache, save_savegame_cache

    result = {
        "active_save": "",
        "active_save_size_mb": 0,
        "sims": [],
        "sim_count": 0,
        "households": {},
        "household_count": 0,
        "worlds": [],
        "world_count": 0,
        "available_saves": [],
        "error": "",
    }

    if not saves_dir or not os.path.isdir(saves_dir):
        result["error"] = "Save-Ordner nicht gefunden"
        return result

    # Finde alle .save Dateien (ohne .ver0, .ver1, etc.)
    save_files = []
    for f in os.listdir(saves_dir):
        if f.endswith(".save") and ".save." not in f:
            full = os.path.join(saves_dir, f)
            if os.path.isfile(full):
                save_files.append(full)

    # Nach Änderungsdatum sortieren (neuester zuerst)
    save_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    if not save_files:
        result["error"] = "Keine Spielstände gefunden"
        return result

    # Available-Liste für Dropdown
    for sf in save_files:
        name = os.path.basename(sf)
        size_mb = round(os.path.getsize(sf) / (1024 * 1024), 1)
        mtime = os.path.getmtime(sf)
        date_str = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M")
        result["available_saves"].append({
            "file": name,
            "size_mb": size_mb,
            "date": date_str,
        })

    # Welchen Save analysieren?
    target_path = ""
    if selected_save:
        # Bestimmten Save laden
        for sf in save_files:
            if os.path.basename(sf) == selected_save:
                target_path = sf
                break
        if not target_path:
            result["error"] = f"Spielstand '{selected_save}' nicht gefunden"
            return result
    else:
        # Neuesten Save nehmen
        target_path = save_files[0]

    save_name = os.path.basename(target_path)
    save_size = os.path.getsize(target_path)
    save_mtime = os.path.getmtime(target_path)
    result["active_save"] = save_name
    result["active_save_size_mb"] = round(save_size / (1024 * 1024), 1)

    # Disk-Cache prüfen: gleiche Datei (mtime+size) → gespeicherte Ergebnisse verwenden
    sg_cache = load_savegame_cache()
    cache_key = target_path
    cached = sg_cache.get(cache_key)
    if cached and abs(cached.get('mt', 0) - save_mtime) < 0.01 and cached.get('sz', -1) == save_size:
        # Cache-Hit! Ergebnisse übernehmen
        cr = cached.get('result', {})
        cached_sims = cr.get("sims", [])
        # Cache-Version-Check: neue Felder vorhanden?
        if cached_sims and "family_role" not in cached_sims[0]:
            # Alte Cache-Version → Familien-Erkennung nachholen
            _detect_family_roles(cached_sims)
        if cached_sims and "skill_count" not in cached_sims[0]:
            # Alte Cache-Version → Skills/Mood/Alter fehlen → Cache verwerfen
            cached_sims = None
        if cached_sims and "world" not in cached_sims[0]:
            # Alte Cache-Version → Welt-Info fehlt → Cache verwerfen
            cached_sims = None
        if cached_sims and not cr.get("world_v2"):
            # Alte Cache-Version → unvollständiges Welt-Mapping → Cache verwerfen
            cached_sims = None
        if cached_sims:
            result["sims"] = cached_sims
            result["sim_count"] = cr.get("sim_count", 0)
            result["households"] = cr.get("households", {})
            result["household_count"] = cr.get("household_count", 0)
            result["worlds"] = cr.get("worlds", [])
            result["world_count"] = cr.get("world_count", 0)
            result["age_stats"] = cr.get("age_stats", {})
            result["gender_stats"] = cr.get("gender_stats", {})
            result["species_stats"] = cr.get("species_stats", {})
            result["skin_stats"] = cr.get("skin_stats", {})
            result["partner_count"] = cr.get("partner_count", 0)
            print(f"[SAVEGAME] Cache-Hit für {save_name}", flush=True)
            return result

    try:
        entries = _read_save_entries(target_path)
        if not entries:
            result["error"] = "Keine DBPF-Daten im Spielstand"
            return result

        # Zone (Typ 0x0D) enthält die Sim-Daten
        zone_entries = [e for e in entries if e["type"] == 0x0D]
        if not zone_entries:
            result["error"] = "Keine Zone-Daten im Spielstand"
            return result

        zone_data = _read_entry_data(target_path, zone_entries[0])
        if not zone_data:
            result["error"] = "Zone-Daten leer"
            return result

        # Sims extrahieren
        sims = _extract_sims_from_zone(zone_data)

        # Familien-Erkennung + Beziehungs-Score
        _detect_family_roles(sims)

        result["sims"] = sims
        result["sim_count"] = len(sims)

        # Haushalte gruppieren
        households = defaultdict(list)
        for sim in sims:
            households[sim["household"]].append(sim["full_name"])
        result["households"] = dict(households)
        result["household_count"] = len(households)

        # Statistiken
        age_counts = Counter(s["age"] for s in sims)
        gender_counts = Counter(s["gender"] for s in sims)
        species_counts = Counter(s["species"] for s in sims if s["species"])
        skin_counts = Counter(s["skin_tone"] for s in sims if s["skin_tone"])
        partner_count = sum(1 for s in sims if s["partner"])
        result["age_stats"] = dict(age_counts)
        result["gender_stats"] = dict(gender_counts)
        result["species_stats"] = dict(species_counts)
        result["skin_stats"] = dict(skin_counts)
        result["partner_count"] = partner_count

        # Welten extrahieren
        worlds = _extract_worlds_from_zone(zone_data)
        result["worlds"] = worlds
        result["world_count"] = len(worlds)

        # Ergebnisse im Disk-Cache speichern
        sg_cache[cache_key] = {
            'mt': save_mtime,
            'sz': save_size,
            'result': {
                "sims": sims,
                "sim_count": len(sims),
                "households": dict(households),
                "household_count": len(households),
                "worlds": worlds,
                "world_count": len(worlds),
                "age_stats": dict(age_counts),
                "gender_stats": dict(gender_counts),
                "species_stats": dict(species_counts),
                "skin_stats": dict(skin_counts),
                "partner_count": partner_count,
                "world_v2": True,
            },
        }
        save_savegame_cache(sg_cache)
        print(f"[SAVEGAME] Analyse gespeichert im Cache für {save_name}", flush=True)

    except Exception as ex:
        result["error"] = str(ex)

    return result
