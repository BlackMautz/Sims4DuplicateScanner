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

# ── Trait-Map: Tuning-Instance-ID → (DE-Name-M, DE-Name-F oder None) ────────
# Extrahiert via STBL-Cross-Referenz aus den Spieldaten (SimData Trait Schema
# enthält display_name STBL-Key, die gegen die deutsche Lokalisierung aufgelöst wird).
# Tuples (m_name, f_name) für geschlechtsabhängige Formen.
# Kategorien: P=Persönlichkeit, R=Belohnung, T=Kleinkind, I=Baby
_TRAIT_P = {  # CAS-Persönlichkeitseigenschaften
    9322:  ("Fröhlich", None),
    9332:  ("Düster", None),
    9337:  ("Spinner", "Spinnerin"),
    9599:  ("Faul", None),
    9602:  ("Einzelgänger", "Einzelgängerin"),
    9604:  ("Musikliebhaber", None),
    9617:  ("Perfektionist", "Perfektionistin"),
    9620:  ("Snob", None),
    16823: ("Ehrgeizig", None),
    16824: ("Selbstsicher", None),
    16826: ("Bro", None),
    16830: ("Kindisch", None),
    16832: ("Tollpatschig", None),
    16833: ("Sprunghaft", None),
    16836: ("Böse", None),
    16838: ("Familienbewusst", None),
    16841: ("Geek", None),
    16843: ("Vielfraß", None),
    16844: ("Mag keine Kinder", None),
    16845: ("Hitzkopf", None),
    16848: ("Unberechenbar", None),
    16850: ("Kreativ", None),
    16857: ("Gemein", None),
    16858: ("Ordentlich", None),
    16860: ("Chaot", "Chaotin"),
    27176: ("Genießer", "Genießerin"),
    27419: ("Aktiv", None),
    27454: ("Romantisch", None),
    27913: ("Materialistisch", None),
    27914: ("Liebt die Natur", None),
    27915: ("Gut", None),
    27916: ("Bücherwurm", None),
    27917: ("Genie", None),
    27918: ("Kunstliebhaber", None),
    29571: ("Gesellig", None),
    124879: ("Eifersüchtig", None),
    131783: ("Kleptomanisch", None),
    132627: ("Vegetarisch", None),
    253268: ("Mutig", None),
    275418: ("Kaltherzig", None),
    311267: ("Treu", None),
    427231: ("Fiesling", None),
    # Kleinkind (CAS-wählbar)
    140739: ("Heikel", None),
    140740: ("Engelsgleich", None),
    140741: ("Wild", None),
    140742: ("Charmeur", "Charmeurin"),
    140743: ("Albern", None),
    140744: ("Anhänglich", None),
    140745: ("Neugierig", None),
    140746: ("Unabhängig", None),
    # Baby/Infant (CAS-wählbar)
    273755: ("Ruhig", None),
    273756: ("Vorsichtig", None),
    273757: ("Gefühlsstark", None),
    273758: ("Sensibel", None),
    273759: ("Sonnig", None),
    273760: ("Zappelig", None),
}

_TRAIT_R = {  # Belohnungs-/Aspirations-Eigenschaften
    26197: ("Essenz des Geschmacks", None),
    26198: ("Meister der Zaubertränke", None),
    26199: ("Frischekoch", "Frischeköchin"),
    26200: ("Verführerisch", None),
    26201: ("Gesellschaft", None),
    26202: ("Spieler", "Spielerin"),
    26203: ("Betörend", None),
    26388: ("Antiseptisch", None),
    26389: ("Kaum hungrig", None),
    26390: ("Ruhe des Anglers", None),
    26391: ("Stahlblase", None),
    26392: ("Niemals erschöpft", None),
    26393: ("Unabhängig", None),
    26427: ("Sportskanone", None),
    26439: ("Schamlos", None),
    26476: ("Sorglos", None),
    26498: ("Fruchtbar", None),
    26639: ("Blitzputzer", None),
    26686: ("Guter Küsser", "Gute Küsserin"),
    26691: ("Supermentor", "Supermentorin"),
    26899: ("Ehrlich", None),
    27080: ("Hoher Stoffwechsel", None),
    27081: ("Langlebig", None),
    27082: ("Geschäftstüchtig", None),
    27083: ("Häuslich", None),
    27084: ("Niederträchtig", None),
    27085: ("Grübler", "Grüblerin"),
    27086: ("Schneller Lerner", None),
    27087: ("Aufgeschlossen", None),
    27091: ("Geliebt", None),
    27170: ("Urkomisch", None),
    27172: ("Perfekter Gastgeber", None),
    27184: ("Superhirn", None),
    27217: ("Ekel", None),
    27328: ("Geschickt", None),
    27692: ("Professionell", None),
    27772: ("Webmaster", None),
    27942: ("Klug", None),
    27947: ("Sparsam", None),
    28009: ("Fesselnder Musiker", None),
    29618: ("Körperlich begabt", None),
    29619: ("Kreativ begabt", None),
    29620: ("Mental begabt", None),
    29622: ("Sozial begabt", None),
    29827: ("Patriarch", "Matriarchin"),
    29837: ("Indirekt", None),
    30922: ("Poetisch", None),
    31924: ("Markttauglich", None),
    32110: ("Kostenlose Dienste", None),
    32111: ("Genügsam", None),
    32423: ("Kreativer Visionär", None),
    32424: ("Nachteule", None),
    32426: ("Frühaufsteher", "Frühaufsteherin"),
    32429: ("Erinnerungswürdig", None),
    32431: ("Beziehungen", None),
    32442: ("Profi-Faulenzer", None),
    32444: ("Unternehmerisch", None),
    32621: ("Blitzleser", "Blitzleserin"),
    32635: ("Beobachtend", None),
    35504: ("Immer willkommen", None),
    35511: ("Super-Gärtner", None),
    35719: ("Sammler", None),
    39880: ("Gelehrter", None),
    75815: ("Expressionistisch", None),
    76817: ("Eins mit der Natur", None),
    76821: ("Taxator", None),
    132296: ("Schmelzmeister", None),
    143145: ("Glückl. Kleinkind", None),
    143156: ("Bilderbuch-KK", None),
    183028: ("Selten müde", None),
    183034: ("Braucht niemanden", None),
    183035: ("Immer satt", None),
    183037: ("Immer frisch", None),
    194391: ("Schatzjäger", None),
    231050: ("Krankheitsimmunität", None),
    273818: ("Unglückl. Baby", None),
    273819: ("Glückl. Baby", None),
    273820: ("Bilderbuch-Baby", None),
    274012: ("Neugieriger Nachbar", None),
    297768: ("Inspirierter Entdecker", None),
    368744: ("Übung macht den Meister", None),
    397870: ("Kleptomanie+", None),
    460574: ("Aktive Phantasie", None),
}

# Zusammengeführtes Lookup: trait_id → ("P"/"R", name_M, name_F)
_TRAIT_LOOKUP: dict = {}
for _tid, (_nm, _nf) in _TRAIT_P.items():
    _TRAIT_LOOKUP[_tid] = ("P", _nm, _nf)
for _tid, (_nm, _nf) in _TRAIT_R.items():
    _TRAIT_LOOKUP[_tid] = ("R", _nm, _nf)


# ── Likes/Dislikes-Preference-Maps ───────────────────────────────────────────
# SimData-Instance-IDs → (Kategorie_DE, Item_DE)
# 7 Kategorien: Farbe, Deko, Musik, Aktivitäten, Mode, Eigenschaft, Kommunikation
_LIKE_MAP: dict[int, tuple[str, str]] = {
    # Farbe (11)
    257862: ("Farbe", "Orange"), 257863: ("Farbe", "Rot"),
    257864: ("Farbe", "Gelb"), 258213: ("Farbe", "Schwarz"),
    258214: ("Farbe", "Blau"), 258215: ("Farbe", "Braun"),
    258216: ("Farbe", "Grau"), 258217: ("Farbe", "Grün"),
    258218: ("Farbe", "Rosa"), 258219: ("Farbe", "Lila"),
    258220: ("Farbe", "Weiß"),
    # Deko (21)
    257870: ("Deko", "Einfach"), 257871: ("Deko", "Zeitgenössisch"),
    257872: ("Deko", "Terrasse"), 257889: ("Deko", "Boho"),
    257890: ("Deko", "Cosmolux"), 257892: ("Deko", "Franz. Landhaus"),
    257893: ("Deko", "Garten"), 257894: ("Deko", "Gotischer Bauernhof"),
    257895: ("Deko", "Tropisch"), 257896: ("Deko", "Mission"),
    257897: ("Deko", "Modern"), 257898: ("Deko", "Queen Anne"),
    257900: ("Deko", "Vorstadtmodern"), 257901: ("Deko", "Tudor"),
    258203: ("Deko", "Skandinavisch"), 325841: ("Deko", "Industrial"),
    325843: ("Deko", "Art Déco"), 325845: ("Deko", "Vintage"),
    325847: ("Deko", "Luxus"), 325848: ("Deko", "Niedlich"),
    326011: ("Deko", "Shabby Chic"),
    # Musik (21)
    258269: ("Musik", "Alternative"), 258270: ("Musik", "Blues"),
    258271: ("Musik", "Klassik"), 258272: ("Musik", "Elektronik"),
    258273: ("Musik", "Hip-Hop"), 258274: ("Musik", "Kindermusik"),
    258275: ("Musik", "Schlaflieder"), 258276: ("Musik", "Pop"),
    258277: ("Musik", "Retro"), 258278: ("Musik", "Romantik"),
    258279: ("Musik", "Gruselmusik"), 258280: ("Musik", "S-Pop"),
    258281: ("Musik", "Winterfeiertag"), 274594: ("Musik", "Cottage Core"),
    312569: ("Musik", "Oldies"), 343176: ("Musik", "R&B"),
    346279: ("Musik", "Batuu"), 346280: ("Musik", "Brasilianisch"),
    443884: ("Musik", "Naturgeräusche"), 479931: ("Musik", "Ballsaal"),
    480290: ("Musik", "Afro Beats"),
    # Aktivitäten (31)
    258764: ("Aktivitäten", "Kochen"), 258765: ("Aktivitäten", "Fitness"),
    258766: ("Aktivitäten", "Malen"), 258767: ("Aktivitäten", "Videospiele"),
    258768: ("Aktivitäten", "Geige"), 264178: ("Aktivitäten", "Comedy"),
    264180: ("Aktivitäten", "Angeln"), 264181: ("Aktivitäten", "Gartenarbeit"),
    264182: ("Aktivitäten", "Handwerk"), 264184: ("Aktivitäten", "Unfug"),
    264185: ("Aktivitäten", "Mixologie"), 264187: ("Aktivitäten", "Programmieren"),
    264191: ("Aktivitäten", "Raketenwiss."), 264195: ("Aktivitäten", "Schreiben"),
    264197: ("Aktivitäten", "Gitarre"), 264198: ("Aktivitäten", "Klavier"),
    272670: ("Mode", "Einfach"),  # Fashion_Basics (Likes)
    274574: ("Aktivitäten", "Stricken"), 283161: ("Mode", "Boho"),
    283162: ("Mode", "Country"), 283164: ("Mode", "Hipster"),
    283165: ("Mode", "Sportlich"), 283166: ("Mode", "Elegant"),
    283167: ("Mode", "Preppy"), 283168: ("Mode", "Rocker"),
    283169: ("Mode", "Streetwear"),
    339783: ("Aktivitäten", "Nektarherstellung"),
    339784: ("Aktivitäten", "Reitsport"), 352326: ("Aktivitäten", "Edelsteinkunde"),
    371191: ("Aktivitäten", "Töpfern"), 376967: ("Aktivitäten", "Tätowieren"),
    395732: ("Aktivitäten", "Romantik"), 399843: ("Aktivitäten", "Thanatologie"),
    444978: ("Aktivitäten", "Kräuterkunde"), 448272: ("Aktivitäten", "Herstellung"),
    460836: ("Aktivitäten", "Schwertkunst"), 464658: ("Aktivitäten", "Bogenschießen"),
    465079: ("Aktivitäten", "Turmspringen"), 472902: ("Aktivitäten", "Papierbasteln"),
    483105: ("Aktivitäten", "Insektenkunde"),
    # Eigenschaft (18)
    305944: ("Eigenschaft", "Pessimist"), 305945: ("Eigenschaft", "Streitsüchtig"),
    305946: ("Eigenschaft", "Idealist"), 305947: ("Eigenschaft", "Emotional"),
    305948: ("Eigenschaft", "Egozentrisch"), 305949: ("Eigenschaft", "Romantiker"),
    305960: ("Eigenschaft", "Kinderfreund"), 305961: ("Eigenschaft", "Tierfreund"),
    305964: ("Eigenschaft", "Energiegeladen"), 305965: ("Eigenschaft", "Stubenhocker"),
    305966: ("Eigenschaft", "Temperamentvoll"), 305967: ("Eigenschaft", "Naturfreund"),
    305968: ("Eigenschaft", "Schelmisch"), 305969: ("Eigenschaft", "Lustig"),
    305970: ("Eigenschaft", "Verkopft"), 305971: ("Eigenschaft", "Optimist"),
    305972: ("Eigenschaft", "Fleißig"), 305973: ("Eigenschaft", "Ambitionslos"),
    # Kommunikation (18)
    306462: ("Kommunikation", "Körperliche Nähe"),
    306463: ("Kommunikation", "Flirten"), 306464: ("Kommunikation", "Komplimente"),
    306465: ("Kommunikation", "Tiefgründiges"), 306466: ("Kommunikation", "Geschichten"),
    306467: ("Kommunikation", "Albernheiten"), 306468: ("Kommunikation", "Pipi-Humor"),
    306469: ("Kommunikation", "Witze"), 306470: ("Kommunikation", "Streiche"),
    306471: ("Kommunikation", "Täuschung"), 306472: ("Kommunikation", "Bosheit"),
    306473: ("Kommunikation", "Streit"), 306474: ("Kommunikation", "Zuneigung"),
    306475: ("Kommunikation", "Smalltalk"), 306476: ("Kommunikation", "Hobbys"),
    306477: ("Kommunikation", "Interessen"), 306478: ("Kommunikation", "Klatsch"),
    306479: ("Kommunikation", "Beschwerden"),
}

_DISLIKE_MAP: dict[int, tuple[str, str]] = {
    # Farbe (11)
    257855: ("Farbe", "Rot"), 257860: ("Farbe", "Orange"),
    257861: ("Farbe", "Gelb"), 258204: ("Farbe", "Grün"),
    258205: ("Farbe", "Blau"), 258207: ("Farbe", "Lila"),
    258208: ("Farbe", "Braun"), 258209: ("Farbe", "Schwarz"),
    258210: ("Farbe", "Weiß"), 258211: ("Farbe", "Grau"),
    258212: ("Farbe", "Rosa"),
    # Deko (21)
    257867: ("Deko", "Einfach"), 257868: ("Deko", "Zeitgenössisch"),
    257869: ("Deko", "Terrasse"), 257873: ("Deko", "Cosmolux"),
    257875: ("Deko", "Franz. Landhaus"), 257876: ("Deko", "Gotischer Bauernhof"),
    257877: ("Deko", "Mission"), 257878: ("Deko", "Modern"),
    257879: ("Deko", "Queen Anne"), 257884: ("Deko", "Vorstadtmodern"),
    257885: ("Deko", "Tudor"), 257886: ("Deko", "Boho"),
    257887: ("Deko", "Tropisch"), 257888: ("Deko", "Garten"),
    258202: ("Deko", "Skandinavisch"), 325840: ("Deko", "Industrial"),
    325842: ("Deko", "Art Déco"), 325844: ("Deko", "Vintage"),
    325846: ("Deko", "Luxus"), 325849: ("Deko", "Niedlich"),
    326010: ("Deko", "Shabby Chic"),
    # Musik (21)
    258255: ("Musik", "Alternative"), 258256: ("Musik", "Blues"),
    258257: ("Musik", "Klassik"), 258258: ("Musik", "Elektronik"),
    258259: ("Musik", "Hip-Hop"), 258260: ("Musik", "Kindermusik"),
    258261: ("Musik", "Schlaflieder"), 258262: ("Musik", "Pop"),
    258263: ("Musik", "Retro"), 258264: ("Musik", "Romantik"),
    258265: ("Musik", "Gruselmusik"), 258266: ("Musik", "S-Pop"),
    258267: ("Musik", "Winterfeiertag"), 274593: ("Musik", "Cottage Core"),
    312568: ("Musik", "Oldies"), 343175: ("Musik", "R&B"),
    346276: ("Musik", "Brasilianisch"), 346277: ("Musik", "Batuu"),
    443890: ("Musik", "Naturgeräusche"), 479937: ("Musik", "Ballsaal"),
    480296: ("Musik", "Afro Beats"),
    # Aktivitäten (31)
    258758: ("Aktivitäten", "Kochen"), 258759: ("Aktivitäten", "Fitness"),
    258760: ("Aktivitäten", "Malen"), 258761: ("Aktivitäten", "Videospiele"),
    258762: ("Aktivitäten", "Geige"), 264143: ("Aktivitäten", "Comedy"),
    264145: ("Aktivitäten", "Angeln"), 264146: ("Aktivitäten", "Gartenarbeit"),
    264147: ("Aktivitäten", "Handwerk"), 264149: ("Aktivitäten", "Unfug"),
    264150: ("Aktivitäten", "Mixologie"), 264160: ("Aktivitäten", "Programmieren"),
    264164: ("Aktivitäten", "Raketenwiss."), 264168: ("Aktivitäten", "Schreiben"),
    264171: ("Aktivitäten", "Gitarre"), 264172: ("Aktivitäten", "Klavier"),
    274572: ("Aktivitäten", "Stricken"),
    339781: ("Aktivitäten", "Nektarherstellung"),
    339782: ("Aktivitäten", "Reitsport"), 352325: ("Aktivitäten", "Edelsteinkunde"),
    371192: ("Aktivitäten", "Töpfern"), 376966: ("Aktivitäten", "Tätowieren"),
    395731: ("Aktivitäten", "Romantik"), 399842: ("Aktivitäten", "Thanatologie"),
    444983: ("Aktivitäten", "Kräuterkunde"), 448271: ("Aktivitäten", "Herstellung"),
    460835: ("Aktivitäten", "Schwertkunst"), 464659: ("Aktivitäten", "Bogenschießen"),
    465078: ("Aktivitäten", "Turmspringen"), 472901: ("Aktivitäten", "Papierbasteln"),
    483104: ("Aktivitäten", "Insektenkunde"),
    # Mode (9)
    272669: ("Mode", "Einfach"), 283148: ("Mode", "Boho"),
    283149: ("Mode", "Country"), 283150: ("Mode", "Hipster"),
    283151: ("Mode", "Sportlich"), 283152: ("Mode", "Elegant"),
    283153: ("Mode", "Preppy"), 283154: ("Mode", "Rocker"),
    283155: ("Mode", "Streetwear"),
    # Eigenschaft (18)
    306407: ("Eigenschaft", "Ambitionslos"), 306408: ("Eigenschaft", "Streitsüchtig"),
    306409: ("Eigenschaft", "Naturfreund"), 306410: ("Eigenschaft", "Egozentrisch"),
    306411: ("Eigenschaft", "Emotional"), 306412: ("Eigenschaft", "Lustig"),
    306413: ("Eigenschaft", "Fleißig"), 306414: ("Eigenschaft", "Energiegeladen"),
    306415: ("Eigenschaft", "Idealist"), 306416: ("Eigenschaft", "Kinderfreund"),
    306417: ("Eigenschaft", "Stubenhocker"), 306418: ("Eigenschaft", "Schelmisch"),
    306419: ("Eigenschaft", "Optimist"), 306420: ("Eigenschaft", "Pessimist"),
    306421: ("Eigenschaft", "Tierfreund"), 306422: ("Eigenschaft", "Romantiker"),
    306423: ("Eigenschaft", "Verkopft"), 306424: ("Eigenschaft", "Temperamentvoll"),
    # Kommunikation (18)
    306481: ("Kommunikation", "Zuneigung"), 306482: ("Kommunikation", "Streit"),
    306483: ("Kommunikation", "Beschwerden"), 306484: ("Kommunikation", "Komplimente"),
    306485: ("Kommunikation", "Täuschung"), 306486: ("Kommunikation", "Tiefgründiges"),
    306487: ("Kommunikation", "Flirten"), 306488: ("Kommunikation", "Klatsch"),
    306489: ("Kommunikation", "Hobbys"), 306490: ("Kommunikation", "Interessen"),
    306491: ("Kommunikation", "Witze"), 306492: ("Kommunikation", "Bosheit"),
    306493: ("Kommunikation", "Körperliche Nähe"), 306494: ("Kommunikation", "Pipi-Humor"),
    306495: ("Kommunikation", "Streiche"), 306496: ("Kommunikation", "Albernheiten"),
    306497: ("Kommunikation", "Smalltalk"), 306498: ("Kommunikation", "Geschichten"),
}


# ── Relationship-Bit-Map ────────────────────────────────────────────────────
# SimData-Instance-IDs → (Kategorie, Priorität, Label_DE)
# Höhere Priorität = stärker.  Kategorie: F=Freundschaft, R=Romantik, X=Kompatibilität
_REL_FRIEND_BITS: dict[int, tuple[int, str]] = {
    15794: (4, "Beste Freunde"),      # friendship-bff
    15799: (3, "Gute Freunde"),       # friendship-good_friends
    15797: (2, "Freunde"),            # friendship-friend
    15803: (1, "Bekannt"),            # has_met
}
_REL_ROMANCE_BITS: dict[int, tuple[int, str]] = {
    15839: (6, "Seelenverwandte"),    # RomanticCombo_Soulmates
    15822: (5, "Verheiratet"),        # romantic-Married
    15837: (4, "Liebhaber"),          # RomanticCombo_Lovers
    98756: (3, "Romantisch"),         # HaveBeenRomantic
    10150: (2, "Erster Kuss"),        # romantic_FirstKiss
    15815: (1, "Geschieden"),         # romantic-Divorced
}
_REL_COMPAT_BITS: dict[int, str] = {
    308877: "Toll",       # relationshipbit_Compatibility_Amazing
    308890: "Gut",        # relationshipbit_Compatibility_Good
    308879: "Schlecht",   # relationshipbit_Compatibility_Bad
}
_REL_FAMILY_BITS: dict[int, str] = {
    8802: "Geschwister",  # family_brother_sister
}
# f4/f5-Track-IDs → Familien-Typ (asymmetrisch: f4=A→B, f5=B→A)
_REL_FAMILY_TRACKS: dict[int, str] = {
    8809: "Elternteil",        # family_Target_IsParentOf_Actor
    8805: "Kind",              # family_Target_IsSonOrDaughterOf_Actor
    8807: "Enkelkind",         # family_Target_IsGrandchildOf_Actor
    8808: "Großelternteil",    # family_Target_IsGrandparentOf_Actor
    467759: "Schwiegereltern", # family_Target_IsParentInLawOf_Actor
    467871: "Schwiegerkind",   # family_Target_IsChildInLawOf_Actor
    8829: "Stiefelternteil",   # in case present
}


def _trait_name(tid: int, is_female: bool = False) -> str | None:
    """Gibt den deutschen Trait-Namen zurück, oder None falls unbekannt/verborgen."""
    entry = _TRAIT_LOOKUP.get(tid)
    if not entry:
        return None
    _, name_m, name_f = entry
    if is_female and name_f:
        return name_f
    return name_m


def _read_packed_varints(blob: bytes) -> list:
    """Liest aufeinanderfolgende Varints aus einem rohen Byte-Blob (ohne Protobuf-Tags).
    Wird für f30.f10.f1 verwendet, das Trait-Tuning-IDs als packed varints enthält."""
    values: list = []
    pos = 0
    blen = len(blob)
    while pos < blen:
        val = 0
        shift = 0
        while pos < blen:
            b = blob[pos]
            pos += 1
            val |= (b & 0x7F) << shift
            shift += 7
            if not (b & 0x80):
                break
        values.append(val)
    return values


def _extract_trait_names(sub: dict, is_female: bool = False) -> dict:
    """Extrahiert Trait-NAMEN und Likes/Dislikes aus f30.f10.f1 (packed varints).

    Die Trait-Tuning-IDs werden gegen _TRAIT_LOOKUP, _LIKE_MAP und _DISLIKE_MAP
    aufgelöst. Ergebnis: Dict mit Listen für personality_names, bonus_names,
    likes (Kategorie→Items) und dislikes (Kategorie→Items).
    """
    result: dict = {
        "personality_names": [], "bonus_names": [],
        "likes": {}, "dislikes": {},
    }
    for t30, v30 in sub.get(30, []):
        if t30 != "bytes":
            continue
        f30 = _parse_pb(v30, max_depth=1)
        for t10, v10 in f30.get(10, []):
            if t10 != "bytes":
                continue
            f10 = _parse_pb(v10, max_depth=1)
            for t1, v1 in f10.get(1, []):
                if t1 != "bytes":
                    continue
                varints = _read_packed_varints(v1)
                for vid in varints:
                    # Persönlichkeits- / Belohnungstraits
                    entry = _TRAIT_LOOKUP.get(vid)
                    if entry:
                        cat, name_m, name_f = entry
                        name = name_f if (is_female and name_f) else name_m
                        if cat == "P":
                            result["personality_names"].append(name)
                        elif cat == "R":
                            result["bonus_names"].append(name)
                        continue
                    # Likes
                    like = _LIKE_MAP.get(vid)
                    if like:
                        cat_de, item_de = like
                        result["likes"].setdefault(cat_de, []).append(item_de)
                        continue
                    # Dislikes
                    dislike = _DISLIKE_MAP.get(vid)
                    if dislike:
                        cat_de, item_de = dislike
                        result["dislikes"].setdefault(cat_de, []).append(item_de)
            break  # nur erster f10-Eintrag
        break  # nur erster f30-Eintrag
    return result


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

# Kleinkind-Skills (5 Level, eigene XP-Kurve):
#   Bewegung, Kommunikation, Denken, Phantasie, Töpfchen
#   Deltas: [0, 320, 720, 1200, 1680]
_TODDLER_SKILL_XP = [0, 320, 1040, 2240, 3920]

# Minor-Skills (5 Level): Tanzen, Selvadorad. Kultur, Haustier-Training,
# Fotografie, Medien-Produkt., Unternehmertum, Thanatologie,
# Tischtennis, Saftpong, Verkaufen, Arbeitsmoral (Retail-hidden)
_MINOR_SKILL_XP = [0, 800, 2000, 5000, 12580]

# Skill-ID → Typ-Zuordnung
_MINOR_SKILLS = {
    128145, 174687, 161220,           # Tanzen, Selvadorad. Kultur, Haustier-Training
    105774, 192655,                   # Fotografie, Medien-Produkt.
    274197, 380495,                   # Unternehmertum, Thanatologie
    212561, 213548,                   # Tischtennis, Saftpong (hidden)
    111902, 111903,                   # Verkaufen, Arbeitsmoral (Retail-hidden)
    158659,                           # Bowling
    255249,                           # Medium
}
_CHILD_SKILLS = {16718, 16719, 16720, 16721}  # Kreativität, Geist, Motorik, Soziales
_TODDLER_SKILLS = {136140, 140170, 140504, 140706, 144913}  # Bewegung, Kommunikation, Denken, Phantasie, Töpfchen

# ── Bedürfnisse (Commodity-IDs aus f30.f2) ───────────────────────────────────
_NEED_MAP = {
    16652: ("Blase",    "🚽"),
    16654: ("Energie",  "⚡"),
    16655: ("Spaß",     "🎮"),
    16656: ("Hunger",   "🍔"),
    16657: ("Hygiene",  "🚿"),
    16658: ("Sozial",   "💬"),
}

# ── Karriere-Map: SimData-Instance-ID → (DE-Name-M, DE-Name-F oder None) ────
# Tuning-IDs aus SimData (type 0x545AC67A) der Spielpakete.
# Karrierenamen aus der deutschen STBL-Lokalisierung.
# Tupel: (männlich, weiblich_oder_None) für geschlechtsabhängige Formen.
_CAREER_MAP: dict = {
    # ── Vollanstellungen (Erwachsene) ────────────────────────────────────────
    9231:   ("Gastronomie", None),           # career_Adult_Culinary
    12893:  ("Astronaut", "Astronautin"),     # career_Adult_Astronaut
    27927:  ("Verbrecher", "Verbrecherin"),   # career_Adult_Criminal
    27929:  ("Entertainer", "Entertainerin"), # career_Adult_Entertainer
    27930:  ("Maler", "Malerin"),             # career_Adult_Painter
    27931:  ("Geheimagent", "Geheimagentin"), # career_Adult_SecretAgent
    27932:  ("Technikguru", None),            # career_Adult_TechGuru
    27933:  ("Schriftsteller", "Schriftstellerin"),  # career_Adult_Writer
    106458: ("Sportler", "Sportlerin"),       # career_Adult_Athletic
    106460: ("Business", None),               # career_Adult_Business
    193202: ("Stil-Influencer", "Stil-Influencerin"),  # career_Adult_StyleInfluencer
    452992: ("Parkarbeiter", "Parkarbeiterin"),  # career_Adult_ParkWorker
    # ── Aktive Karrieren ─────────────────────────────────────────────────────
    107230: ("Arzt", "Ärztin"),               # career_Adult_Active_Doctor
    107255: ("Wissenschaftler", "Wissenschaftlerin"),  # career_Adult_Active_Scientist
    189135: ("Schauspieler", "Schauspielerin"),  # career_Adult_Active_ActorCareer
    # ── Freelancer ───────────────────────────────────────────────────────────
    205686: ("Freelancer (Kunst)", None),     # career_Adult_Freelancer_Artist
    # ── Teilzeitjobs (Erwachsene) ────────────────────────────────────────────
    208723: ("Babysitter (Teilzeit)", None),  # career_Adult_PartTime_Babysitter
    208737: ("Barista (Teilzeit)", None),     # career_Adult_PartTime_Barista
    208761: ("Fast-Food (Teilzeit)", None),   # career_Adult_PartTime_FastFood
    208779: ("Handarbeit (Teilzeit)", None),  # career_Adult_PartTime_ManualLabor
    208874: ("Einzelhandel (Teilzeit)", None),  # career_Adult_PartTime_Retail
    205662: ("Rettungsschwimmer (Teilzeit)", "Rettungsschwimmerin (Teilzeit)"),  # career_Adult_PartTime_Lifeguard
    207607: ("Fischer (Teilzeit)", "Fischerin (Teilzeit)"),  # career_Adult_PartTime_Fisherman
    208405: ("Taucher (Teilzeit)", "Taucherin (Teilzeit)"),  # career_Adult_PartTime_Diver
    # ── Kleinunternehmen ─────────────────────────────────────────────────────
    400290: ("Kleinunternehmen", None),       # career_SmallBusiness_Employee
    # ── Teenager-Karrieren ───────────────────────────────────────────────────
    9541:   ("Oberschule", None),             # career_Teen_HighSchool
    35157:  ("Fast-Food (Teen)", None),       # career_Teen_FastFood
    35218:  ("Handarbeit (Teen)", None),      # career_Teen_ManualLabor
    35219:  ("Einzelhandel (Teen)", None),    # career_Teen_Retail
    35220:  ("Barista (Teen)", None),         # career_Teen_Barista
    35221:  ("Babysitter (Teen)", None),      # career_Teen_Babysitter
    208881: ("Rettungsschwimmer (Teen)", "Rettungsschwimmerin (Teen)"),  # career_Teen_Lifeguard
    273911: ("Streamer (Teen)", "Streamerin (Teen)"),  # career_Teen_StreamerSideHustle
    277663: ("Simsfluencer (Teen)", None),    # career_Teen_SimsfluencerSideHustle
    # ── Kind-Karriere ────────────────────────────────────────────────────────
    12895:  ("Grundschule", None),            # career_Child_GradeSchool
    # ── Freiwillig ───────────────────────────────────────────────────────────
    186513: ("Pfadfinder", "Pfadfinderin"),   # career_Volunteer_Scouting
    199274: ("Schauspielclub", None),         # career_Volunteer_DramaClub
    217092: ("E-Sport", None),                # career_Volunteer_E-Sports
    # ── NPC-Karrieren ────────────────────────────────────────────────────────
    110326: ("Sensenmann", None),             # career_Adult_NPC_GrimReaper
    112015: ("Bibliothekar", "Bibliothekarin"),  # career_Adult_NPC_Librarian
    143285: ("Marktverkäufer", "Marktverkäuferin"),  # career_Adult_NPC_StallVendor
    143653: ("Vermieter", "Vermieterin"),     # career_Adult_NPC_Landlord
    183371: ("Väterchen Frost", None),        # career_Adult_NPC_FatherWinter
    206662: ("Kuriositätenladen", None),      # career_Adult_NPC_CurioShopOwner
    224750: ("Professor (Kunst)", "Professorin (Kunst)"),  # career_Adult_NPC_ProfessorNPC_Arts
    224751: ("Professor (Wissensch.)", "Professorin (Wissensch.)"),  # career_Adult_NPC_ProfessorNPC_Science
    260407: ("Gartenladen", None),            # career_Adult_CottageWorld_NPC_GardenShopOwner
    260408: ("Lebensmittelladen", None),      # career_Adult_CottageWorld_NPC_GroceryOwner
    260409: ("Lieferservice", None),          # career_Adult_CottageWorld_NPC_GroceryDelivery
    260410: ("Bürgermeister", "Bürgermeisterin"),  # career_Adult_CottageWorld_NPC_Mayor
    260411: ("Pub-Besitzer", "Pub-Besitzerin"),  # career_Adult_CottageWorld_NPC_PubOwner
    276665: ("Blumenverkäufer", "Blumenverkäuferin"),  # career_Adult_NPC_StallVendor_Wedding_Flower
    294303: ("Barkeeper", None),              # career_Adult_NPC_Bartender_WolfTown
    324722: ("Mysteriöser Rancher", "Mysteriöse Rancherin"),  # career_Adult_EP14World_NPC_MysteriousRancher
    324723: ("Pferdetrainer", "Pferdetrainerin"),  # career_Adult_EP14World_NPC_HorseTrainer
    402986: ("Bäckerei", None),               # career_Adult_EP18_NPC_BakeryStall
    402987: ("Süßwarenstand", None),          # career_Adult_EP18_NPC_SweetStall
    402988: ("Töpferstand", None),            # career_Adult_EP18_NPC_PotteryStall
    441239: ("Gnom-Laden", None),             # career_Adult_EP19World_NPC_GnomeShop
    441266: ("Apotheke", None),               # career_Adult_EP19World_NPC_ApothecaryShop
    447351: ("Kryptid", None),                # career_Adult_NPC_Cryptid
    # ── Weitere Karrieren (DLC / EP) ─────────────────────────────────────────
    106132: ("Detektiv", "Detektivin"),       # detectiveCareer_1
    135201: ("Aktivist", "Aktivistin"),       # careers_Adult_Activist
    135363: ("Social Media", None),           # careers_Adult_SocialMedia
    136115: ("Kritiker", "Kritikerin"),       # careers_Adult_Critic
    186159: ("Gärtner", "Gärtnerin"),         # careers_Adult_Gardener
    202483: ("Militär", None),                # careers_Adult_Military
    204960: ("Naturschützer", "Naturschützerin"),  # careers_Adult_Conservationist
    206791: ("Freelancer", "Freelancerin"),   # careers_Adult_Freelancer_No_Agency
    207568: ("Freelancer (Programmierung)", None),  # careers_Adult_Freelancer_Agency_Programmer
    207579: ("Freelancer (Schreiben)", None),  # careers_Adult_Freelancer_Agency_Writer
    217872: ("Ingenieur", "Ingenieurin"),     # careers_Adult_Engineer
    223698: ("Universität", None),            # University_BaseCareer
    232767: ("Stadtplaner", "Stadtplanerin"), # careers_Adult_CivilDesigner
    232809: ("Freelancer (Handwerk)", None),  # careers_Adult_Freelancer_Agency_Maker
    248315: ("Firmenarbeiter", "Firmenarbeiterin"),  # careers_Adult_CorporateWorker
    366724: ("Liebesberater", "Liebesberaterin"),  # careers_Adult_RomanceConsultant
    377586: ("Bestatter", "Bestatterin"),     # careers_Adult_Mortician
    377623: ("Sensenmann (aktiv)", None),     # careers_Adult_Active_Reaper
    439108: ("Naturheilkundler", "Naturheilkundlerin"),  # workFromHomeCareer_Naturopath
    466304: ("Adlig", "Adlige"),             # career_Noble
    # ── Weitere NPC-Karrieren ────────────────────────────────────────────────
    109456: ("Haushaltshilfe", None),         # career_Adult_NPC_Maid
    109457: ("Briefträger", "Briefträgerin"), # career_Adult_NPC_Mailman
    109458: ("Barkeeper", None),              # career_Adult_NPC_Bartender
    110043: ("Pizzalieferant", "Pizzalieferantin"),  # career_Adult_NPC_PizzaDelivery
    122818: ("DJ", None),                     # career_Adult_NPC_DJ
    197295: ("Paparazzo", None),              # career_Adult_NPC_Paparazzi
    242362: ("Öko-Inspektor", "Öko-Inspektorin"),  # career_Adult_NPC_EcoInspector
    400748: ("Dubiose Gestalt", None),        # career_Adult_NPC_ShadyNPC
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
    if skill_id in _TODDLER_SKILLS:
        thresholds = _TODDLER_SKILL_XP
        max_lvl = 5
    elif skill_id in _MINOR_SKILLS:
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


# ── Outfit-Extraktion ────────────────────────────────────────────

# Outfit-Kategorie-IDs → deutsche Namen
_OUTFIT_CATEGORY_NAMES = {
    0: "Alltag", 1: "Formal", 2: "Sport", 3: "Schlaf",
    4: "Party", 5: "Badebekleidung", 6: "Kaltes Wetter",
    7: "Heißes Wetter", 8: "Karriere", 9: "Spezial", 10: "Batuu",
}

# Body-Type-IDs → deutsche Slot-Namen  (Sims 4 BodyType enum)
_BODY_TYPE_NAMES = {
    1: "Hut", 2: "Haare", 3: "Oberteil", 4: "Oberteil",
    5: "Unterteil", 6: "Schuhe", 7: "Handschuhe", 8: "Ganzkörper",
    10: "Ganzkörper", 11: "Ohrring", 14: "Brille", 15: "Halskette",
    16: "Ring", 17: "Armband", 18: "Tattoo", 19: "Strümpfe",
    20: "Socken", 24: "Makeup", 25: "Lippenstift", 26: "Lidschatten",
    27: "Eyeliner", 28: "Nagellack", 29: "Augenbrauen",
    30: "Wimpern", 33: "Gesichtsbehaarung", 35: "Skindetail",
    36: "Hautfarbe", 37: "Sommersprossen", 40: "Kopfschmuck",
    41: "Mantel",
}


def _extract_outfits(sub: dict) -> list:
    """Extrahiert CAS-Part-IDs aus dem Sim-Blob.

    Unterstützt zwei Formate:
    1. Altes Format (bis ~2024): f9 = OutfitList als bytes
       → f1 = repeated OutfitCategory → f2 = Outfit → f3/f5 = body_types/parts
    2. Neues Format (ab ~2025, v1.121+): f9 = fixed32 (Referenz),
       Outfit-Daten in f47 (AppearanceTracker):
       → f47.f11 = aktuell getragenes Outfit (f4=Basis, f5=Kleidung)
       → f47.f27 = Garderoben-Katalog (alle CAS-Parts aller Outfits)
       → f47.f22 = Outfit-Konfigurationen

    Returns:
        Liste von dicts:
        [{"category": str, "category_id": int, "parts": [int, ...], "body_types": [int, ...]}, ...]
    """
    outfits = []

    # ── 1) Altes Format: f9 als bytes (OutfitList) ──
    for t, f9_blob in sub.get(9, []):
        if t != "bytes" or len(f9_blob) < 4:
            continue

        outfit_list = _parse_pb(f9_blob, max_depth=1)
        for ct, cat_blob in outfit_list.get(1, []):
            if ct != "bytes" or len(cat_blob) < 2:
                continue
            cat_sub = _parse_pb(cat_blob, max_depth=1)
            cat_id = None
            for ctt, ctv in cat_sub.get(1, []):
                if ctt == "varint":
                    cat_id = ctv
                    break
            if cat_id is None:
                continue
            cat_name = _OUTFIT_CATEGORY_NAMES.get(cat_id, f"Kategorie {cat_id}")
            for ot, outfit_blob in cat_sub.get(2, []):
                if ot != "bytes" or len(outfit_blob) < 2:
                    continue
                outfit_sub = _parse_pb(outfit_blob, max_depth=1)
                part_ids = []
                for pt, pv in outfit_sub.get(5, []):
                    if pt == "fixed64":
                        if pv > 0:
                            part_ids.append(pv)
                    elif pt == "varint":
                        if pv > 0x100:
                            part_ids.append(pv)
                    elif pt == "bytes" and len(pv) >= 8:
                        for off in range(0, len(pv) - 7, 8):
                            val = struct.unpack_from("<Q", pv, off)[0]
                            if val > 0:
                                part_ids.append(val)
                body_types = []
                for bt_t, bt_v in outfit_sub.get(3, []):
                    if bt_t == "varint":
                        body_types.append(bt_v)
                    elif bt_t == "bytes":
                        bpos = 0
                        while bpos < len(bt_v):
                            bval, bpos = decode_varint(bt_v, bpos)
                            body_types.append(bval)
                if part_ids:
                    outfits.append({
                        "category": cat_name,
                        "category_id": cat_id,
                        "parts": part_ids,
                        "body_types": body_types,
                    })

    if outfits:
        return outfits

    # ── 2) Neues Format: f47 (AppearanceTracker) ──
    for t47, v47 in sub.get(47, []):
        if t47 != "bytes" or len(v47) < 10:
            continue
        f47 = _parse_pb(v47, max_depth=1)

        # f47.f11 = aktuell getragenes Outfit
        equipped_ids = []
        for t11, v11 in f47.get(11, []):
            if t11 != "bytes":
                continue
            f11 = _parse_pb(v11, max_depth=1)

            # f11.f5 = Kleidungsteile (Hauptoutfit)
            for _, part_blob in f11.get(5, []):
                if _ != "bytes":
                    continue
                part = _parse_pb(part_blob, max_depth=1)
                for pt, pv in part.get(1, []):
                    if pt == "varint" and pv > 0:
                        equipped_ids.append(pv)

            # f11.f4 = Basis-Teile (Hauttextur, genetische Merkmale)
            for _, part_blob in f11.get(4, []):
                if _ != "bytes":
                    continue
                part = _parse_pb(part_blob, max_depth=1)
                for pt, pv in part.get(1, []):
                    if pt == "varint" and pv > 0:
                        equipped_ids.append(pv)

            # f11.f6 + f11.f7 = gepackte Varint-Listen (Accessoires/Extras)
            for fn in (6, 7):
                for pt, pv in f11.get(fn, []):
                    if pt == "bytes" and len(pv) > 0:
                        bpos = 0
                        while bpos < len(pv):
                            try:
                                val, bpos = decode_varint(pv, bpos)
                                if val > 100:
                                    equipped_ids.append(val)
                            except Exception:
                                break

        # f47.f27 = Garderoben-Katalog (alle CAS-Parts)
        wardrobe_ids = set()
        for t27, v27 in f47.get(27, []):
            if t27 != "bytes":
                continue
            f27 = _parse_pb(v27, max_depth=1)
            for _, entry_blob in f27.get(1, []):
                if _ != "bytes":
                    continue
                entry = _parse_pb(entry_blob, max_depth=1)
                for pt, pv in entry.get(1, []):
                    if pt == "varint" and pv > 0:
                        wardrobe_ids.add(pv)

        # f47.f22 = Outfit-Konfigurationen
        outfit_configs = len(f47.get(22, []))

        if equipped_ids:
            outfits.append({
                "category": "Aktuell",
                "category_id": 0,
                "parts": equipped_ids,
                "body_types": [],
            })

        if wardrobe_ids - set(equipped_ids):
            outfits.append({
                "category": "Garderobe",
                "category_id": 99,
                "parts": list(wardrobe_ids - set(equipped_ids)),
                "body_types": [],
            })

        break

    return outfits


# ── Spezies/Okkult-Typ-Mapping (aus f63 CAS-Template-IDs) ────────────────────
# Die erste f63.f1.f1-ID identifiziert den Spezies-/Okkult-Typ
_SPECIES_MAP: dict = {
    115980: "Haustier",      # Katze/Hund (Cats & Dogs)
    332484: "Pferd",          # Horse Ranch
    306424: "Werwolf",        # Werewolves
    306425: "Zauberer",       # Realm of Magic (Spellcaster)
    461328: "Fee",            # Enchanted by Nature (Fairy/Fae)
    # Folgende IDs sind geschätzt (nicht in diesem Save verifiziert):
    149552: "Vampir",         # Vampires GP
    149553: "Vampir",         # Vampires GP (alt. Form)
    213766: "Meerjungfrau",   # Island Living
    213819: "Meerjungfrau",   # Island Living (alt.)
    116023: "Alien",          # Get to Work
    116024: "Alien",          # Get to Work (alt.)
}

_SPECIES_EMOJI: dict = {
    "Haustier": "🐾", "Pferd": "🐴", "Werwolf": "🐺",
    "Zauberer": "🧙", "Fee": "🧚", "Vampir": "🧛",
    "Meerjungfrau": "🧜", "Alien": "👽", "Okkult": "✨",
}


def _extract_species(sub: dict) -> str:
    """Erkennt den Spezies-/Okkult-Typ aus f63 (Sekundärform).

    Liest die CAS-Template-ID (f63.f1.f1) und mappt sie zum Typ.
    Gibt leeren String zurück wenn kein f63 vorhanden.
    """
    if 63 not in sub:
        return ""
    for t, v in sub.get(63, []):
        if t != "bytes":
            continue
        f63 = _parse_pb(v, max_depth=1)
        for et, ev in f63.get(1, []):
            if et != "bytes":
                continue
            inner = _parse_pb(ev, max_depth=1)
            fid = _get_pb_varint(inner, 1)
            if fid and fid in _SPECIES_MAP:
                return _SPECIES_MAP[fid]
        break
    return "Okkult"  # f63 vorhanden aber Typ unbekannt


def _extract_trait_details(sub: dict) -> dict:
    """Extrahiert Trait-Aufschlüsselung aus f18.

    f18 Struktur:
      f1 = Aspirations-Trait (1 Eintrag, ID der Aspiration)
      f2 = Alle Traits inkl. versteckter System-Traits (~60-80)
      f3 = Bonus-/Belohnungs-Traits
      f4 = Lebensstil-Traits (Lifestyle)
      f5 = Likes & Dislikes

    Returns:
        dict: {personality: int, bonus: int, lifestyle: int, likes: int, total: int}
    """
    result = {"personality": 0, "bonus": 0, "lifestyle": 0, "likes": 0, "total": 0, "aspiration": 0}
    for t, v in sub.get(18, []):
        if t != "bytes":
            continue
        f18 = _parse_pb(v, max_depth=1)
        for fnum in sorted(f18.keys()):
            count = 0
            for et, ev in f18[fnum]:
                if et == "varint":
                    count += 1
                elif et == "bytes":
                    inner = _parse_pb(ev, max_depth=1)
                    for _fk, _entries in inner.items():
                        for _t, _v in _entries:
                            if _t == "varint":
                                count += 1
            if fnum == 1:
                result["aspiration"] = count
            elif fnum == 2:
                result["personality"] = count
            elif fnum == 3:
                result["bonus"] = count
            elif fnum == 4:
                result["lifestyle"] = count
            elif fnum == 5:
                result["likes"] = count
            result["total"] += count
        break
    return result


def _extract_career_info(sub: dict, is_female: bool = False) -> tuple:
    """Extrahiert Karrierenamen + Level aus f30.f12 (CareerTracker).

    f30.f12.f1 = aktive Karriere:
      f1.f1 = Karriere-Tuning-ID (SimData Instance-ID)
      f1.f4 = Karrierelevel (1-10)

    Gibt (career_name, career_level) zurück.
    career_name = deutscher Name oder englischer Fallback, "" wenn keine Karriere.
    """
    for t30, v30 in sub.get(30, []):
        if t30 != "bytes":
            continue
        f30 = _parse_pb(v30, max_depth=1)
        for t12, v12 in f30.get(12, []):
            if t12 != "bytes":
                continue
            f12 = _parse_pb(v12, max_depth=1)
            for t1, v1 in f12.get(1, []):
                if t1 != "bytes":
                    continue
                career = _parse_pb(v1, max_depth=1)
                cid = _get_pb_varint(career, 1)
                if not cid:
                    continue
                level = _get_pb_varint(career, 4) or 0
                entry = _CAREER_MAP.get(cid)
                if entry:
                    name_m, name_f = entry
                    name = name_f if (is_female and name_f) else name_m
                else:
                    name = f"Karriere #{cid}"
                return (name, level)
            break  # nur erster f12-Eintrag
        break  # nur erster f30-Eintrag
    return ("", 0)


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
    zone_to_lot_name: dict = {}  # zone_id → Lot-Name (benutzerdefiniert)
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
            zone_id_val = None
            lot_name_val = ""
            for t, v in lot_sub.get(2, []):
                if t == "fixed64" and v:
                    zone_id_val = v
            # Lot-Name (f3 = bytes → string, z.B. "Zypressenhain")
            for t, v in lot_sub.get(3, []):
                if t == "bytes":
                    try:
                        lot_name_val = v.decode("utf-8", errors="replace")
                    except Exception:
                        pass
            if zone_id_val:
                zone_to_world[zone_id_val] = nb_name
                if lot_name_val:
                    zone_to_lot_name[zone_id_val] = lot_name_val

    # ── Haushalt→Welt-Mapping + Haushaltsdaten aus f5 ──
    # f5.f3 = Haushaltsname, f5.f4 = home_zone, f5.f5 = Simoleons,
    # f5.f21 = Gallery-Username, f5.f31 = gespielt
    household_to_world: dict = {}      # Haushaltsname → Weltname
    household_funds: dict = {}         # Haushaltsname → Simoleons
    household_username: dict = {}      # Haushaltsname → Gallery-Username
    household_lot_name: dict = {}      # Haushaltsname → Lot-Name

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
        if hh_name and home_zone:
            if home_zone in zone_to_world:
                household_to_world[hh_name] = zone_to_world[home_zone]
            if home_zone in zone_to_lot_name:
                household_lot_name[hh_name] = zone_to_lot_name[home_zone]

        # Simoleons (f5 = varint)
        hh_funds = _get_pb_varint(hh_sub, 5)
        if hh_name and hh_funds is not None:
            household_funds[hh_name] = hh_funds

        # Gallery-Username (f21 = bytes → string)
        hh_user = ""
        for t, v in hh_sub.get(21, []):
            if t == "bytes":
                try:
                    hh_user = v.decode("utf-8", errors="replace")
                except Exception:
                    pass
        if hh_name and hh_user:
            household_username[hh_name] = hh_user

        hh_f31 = _get_pb_varint(hh_sub, 31)
        if hh_f31 and hh_f31 > 0:
            hh_f14 = _get_pb_varint(hh_sub, 14)
            if hh_f14 == 0:  # Eigener Haushalt, nicht Basegame
                if hh_name:
                    played_household_names.add(hh_name)

    # ── Relationship-Service: Beziehungsanzahl + Details aus f2.f8.f13 ──
    # Speichert für jede Sim-ID die Anzahl der Beziehungspaare und Details.
    rel_counts = defaultdict(int)  # sim_id → Anzahl Beziehungen
    # rel_details: sim_id → [(partner_id, friendship_label, romance_label, family_label, compat_label)]
    rel_details: dict[int, list] = defaultdict(list)
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
                    if not sim_a or not sim_b:
                        continue
                    rel_counts[sim_a] += 1
                    rel_counts[sim_b] += 1

                    # ── f3: Relationship-Bits ──
                    friend_label = ""
                    friend_prio = 0
                    romance_label = ""
                    romance_prio = 0
                    compat_label = ""
                    family_bit = ""
                    for t3, v3 in pair.get(3, []):
                        if t3 != "bytes":
                            continue
                        f3 = _parse_pb(v3, max_depth=1)
                        for tf1, vf1 in f3.get(1, []):
                            if tf1 != "bytes":
                                continue
                            bit_ids = _read_packed_varints(vf1)
                            for bid in bit_ids:
                                fb = _REL_FRIEND_BITS.get(bid)
                                if fb and fb[0] > friend_prio:
                                    friend_prio, friend_label = fb
                                rb = _REL_ROMANCE_BITS.get(bid)
                                if rb and rb[0] > romance_prio:
                                    romance_prio, romance_label = rb
                                cb = _REL_COMPAT_BITS.get(bid)
                                if cb:
                                    compat_label = cb
                                fam = _REL_FAMILY_BITS.get(bid)
                                if fam:
                                    family_bit = fam
                        break  # nur erstes f3-Sub

                    # ── f4/f5: Familien-Tracks (asymmetrisch) ──
                    family_a = family_bit  # A's Rolle gegenüber B
                    family_b = family_bit  # B's Rolle gegenüber A
                    for t4, v4 in pair.get(4, []):
                        if t4 != "bytes":
                            continue
                        f4 = _parse_pb(v4, max_depth=1)
                        for tf1, vf1 in f4.get(1, []):
                            if tf1 != "bytes":
                                continue
                            for tid in _read_packed_varints(vf1):
                                ft = _REL_FAMILY_TRACKS.get(tid)
                                if ft:
                                    family_a = ft
                        break
                    for t5, v5 in pair.get(5, []):
                        if t5 != "bytes":
                            continue
                        f5 = _parse_pb(v5, max_depth=1)
                        for tf1, vf1 in f5.get(1, []):
                            if tf1 != "bytes":
                                continue
                            for tid in _read_packed_varints(vf1):
                                ft = _REL_FAMILY_TRACKS.get(tid)
                                if ft:
                                    family_b = ft
                        break

                    # Für A: B ist family_a (z.B. Kind von A → B="Kind")
                    rel_details[sim_a].append(
                        (sim_b, friend_label, romance_label, family_a, compat_label))
                    # Für B: A ist family_b
                    rel_details[sim_b].append(
                        (sim_a, friend_label, romance_label, family_b, compat_label))
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
        last_name = _get_pb_string(sub, 6) or ""
        if not first_name:
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

    # id → Name-Mapping für Relationship-Details
    id_to_name: dict[int, str] = {}
    for _sub, _idx, _fn, _ln, _sid in raw_list:
        if _sid is not None:
            id_to_name[_sid] = f"{_fn} {_ln}".strip()

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

        # Spezies/Okkult-Erkennung (f63 → konkreter Typ)
        species = _extract_species(sub)
        species_emoji = _SPECIES_EMOJI.get(species, "")

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

        # Trait-Aufschlüsselung (f18 → kategorisierte Counts)
        trait_details = _extract_trait_details(sub)
        trait_count = trait_details["total"]

        # Trait-NAMEN aus f30.f10.f1 (packed varints → Tuning-IDs)
        is_female = (gender == "Weiblich")
        trait_names = _extract_trait_names(sub, is_female)
        trait_details["personality_names"] = trait_names["personality_names"]
        trait_details["bonus_names"] = trait_names["bonus_names"]
        likes = trait_names["likes"]    # Dict[str, List[str]]
        dislikes = trait_names["dislikes"]

        # Karriere (f30.f12 = CareerTracker)
        career_name, career_level = _extract_career_info(sub, is_female)

        # Beziehungsanzahl aus Relationship-Service (f2.f8.f13)
        relationship_count = rel_counts.get(sim_id, 0) if sim_id else 0

        # Beziehungs-Details: benannte Beziehungen mit Typ-Labels
        # Sortiert: Familie > Romantik > Freundschaft > Bekannt
        relationships_detail: list[dict] = []
        if sim_id and sim_id in rel_details:
            for partner_id, fr, ro, fam, comp in rel_details[sim_id]:
                pname = id_to_name.get(partner_id, "")
                if not pname:
                    continue
                # Priorität: Familie(4) > Romantik(3) > Freundschaft(2) > Bekannt(1)
                sort_key = 0
                if fam:
                    sort_key = 40
                if ro:
                    sort_key = max(sort_key, 30)
                if fr == "Beste Freunde":
                    sort_key = max(sort_key, 24)
                elif fr == "Gute Freunde":
                    sort_key = max(sort_key, 23)
                elif fr == "Freunde":
                    sort_key = max(sort_key, 22)
                relationships_detail.append({
                    "name": pname,
                    "friendship": fr,
                    "romance": ro,
                    "family": fam,
                    "compat": comp,
                    "_sort": sort_key,
                })
            # Sortieren: wichtigste Beziehungen zuerst (alle)
            relationships_detail.sort(key=lambda r: (-r["_sort"], r["name"]))
            for rd in relationships_detail:
                del rd["_sort"]

        # Skills (f30 → f13 = RankedStatisticTracker → XP-basierte Level)
        skills = _extract_skills(sub)
        skill_count = len(skills)

        # Bedürfnisse (f30 → f2 = CommodityTracker → Motive)
        needs = _extract_needs(sub)

        # Stimmung (f53)
        mood_val, mood_label, mood_emoji = _extract_mood(sub)

        # Sim-Alter in Tagen (f34)
        sim_age_days = _extract_sim_age_days(sub)

        # Outfits (f9 → CAS-Part-IDs + Body-Types)
        outfits = _extract_outfits(sub)
        # Zusammenfassung: Gesamtzahl Teile, Kategorien-Liste
        outfit_total_parts = 0
        outfit_categories = []
        all_cas_part_ids = set()
        for o in outfits:
            outfit_total_parts += len(o["parts"])
            if o["category"] not in outfit_categories:
                outfit_categories.append(o["category"])
            for pid in o["parts"]:
                all_cas_part_ids.add(pid)

        # Aktiv gespielt?
        # f42=1 → Sim wurde irgendwann vom Spieler gesteuert
        # ODER: Sim gehört zum aktiven Haushalt (f31=1 + f14=0)
        is_played = (
            _get_pb_varint(sub, 42) == 1
            or (household or "") in played_household_names
        )

        # Haushaltsdaten zuordnen
        hh_key = household if household else last_name
        sim_funds = household_funds.get(hh_key, 0)
        sim_username = household_username.get(hh_key, "")
        sim_lot_name = household_lot_name.get(hh_key, "")

        sims.append({
            "sim_id": sim_id if sim_id is not None else 0,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}".strip(),
            "household": hh_key,
            "world": household_to_world.get(household, household_to_world.get(last_name, "")),
            "lot_name": sim_lot_name,
            "gender": gender,
            "gender_emoji": gender_emoji,
            "age": age,
            "age_emoji": age_emoji,
            "species": species,
            "species_emoji": species_emoji,
            "partner": partner_name,
            "skin_tone": skin_tone,
            "trait_count": trait_count,
            "trait_details": trait_details,
            "career_name": career_name,
            "career_level": career_level,
            "likes": likes,
            "dislikes": dislikes,
            "relationship_count": relationship_count,
            "relationships_detail": relationships_detail,
            "skill_count": skill_count,
            "top_skills": [{"name": n, "level": l, "max_level": ml}
                           for n, l, ml, _xp, _mod in skills],
            "needs": needs,
            "mood_value": round(mood_val, 1),
            "mood_label": mood_label,
            "mood_emoji": mood_emoji,
            "sim_age_days": sim_age_days,
            "is_played": is_played,
            "simoleons": sim_funds,
            "gallery_username": sim_username,
            "outfits": outfits,
            "outfit_total_parts": outfit_total_parts,
            "outfit_categories": outfit_categories,
            "cas_part_ids": list(all_cas_part_ids),
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
            _detect_family_roles(cached_sims)
        if cached_sims and "skill_count" not in cached_sims[0]:
            cached_sims = None
        if cached_sims and "world" not in cached_sims[0]:
            cached_sims = None
        if cached_sims and not cr.get("world_v2"):
            cached_sims = None
        # v3.3: Neue Felder (Spezies-Typ, Trait-Details, Karriere, Simoleons)
        if cached_sims and "trait_details" not in cached_sims[0]:
            cached_sims = None
        # v3.4: Outfit-Daten aus f47 (AppearanceTracker) statt f9
        if cached_sims and cached_sims[0].get("outfit_total_parts", 0) == 0:
            # Alte Cache-Daten ohne f47-Outfits → invalidieren
            cached_sims = None
        # v3.5: Trait-Namen (personality_names, bonus_names)
        if cached_sims and "personality_names" not in cached_sims[0].get("trait_details", {}):
            cached_sims = None
        # v3.5: Karrierenamen (career_name)
        if cached_sims and "career_name" not in cached_sims[0]:
            cached_sims = None
        # v3.5: Likes/Dislikes
        if cached_sims and "likes" not in cached_sims[0]:
            cached_sims = None
        # v3.5: Relationship-Details
        if cached_sims and "relationships_detail" not in cached_sims[0]:
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
