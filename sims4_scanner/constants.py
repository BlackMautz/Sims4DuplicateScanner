# -*- coding: utf-8 -*-
"""Zentrale Konstanten und Konfigurationswerte für den Sims 4 Duplikate Scanner."""

from __future__ import annotations

import base64 as _b64

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
SCANNER_VERSION = "3.2.0"
# Webhook-URL ist base64-kodiert, damit sie nicht direkt im Quelltext steht
_WEBHOOK_ENC = (
    b"aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTQ3MDE5MDQ4NTgyNDg2"
    b"ODU0NC9lRFFZajBlSFdLOEViZUllaXVEZEFXaXJqV1pMV3RZSERQSEU2WXVoaGtW"
    b"TGZvR2RpWGF4ZlAyZk9ZWF8zZjlyNHJLZQ=="
)
DISCORD_WEBHOOK_URL = _b64.b64decode(_WEBHOOK_ENC).decode("ascii")
GITHUB_REPO = "BlackMautz/Sims4DuplicateScanner"

# Bekannte DBPF Resource Types (TS4)
RESOURCE_TYPE_NAMES = {
    0x034AEECB: "CAS Part",
    0x00B2D882: "Object Definition",
    0x545AC67A: "Buff Tuning",
    0x03B33DDF: "Trait Tuning",
    0xE882D22F: "Object Tuning",
    0x339BC0E4: "Interaction Tuning",
    0x0C772E27: "Lot Tuning",
    0xCB5FDDC7: "Action Tuning",
    0xC0DB5AE7: "Instance Tuning",
    0x6017E896: "Sim Data",
    0x220557DA: "Sim Info",
    0xD382BF57: "Texture (LRLE)",
    0x00000000: "Null",
    0x736884F1: "Region Tuning",
    0xE5105066: "Recipe Tuning",
    0x7FB6AD72: "Aspiration Tuning",
    0x0904DF10: "Career Tuning",
    0x8B18FF6E: "Walkby Tuning",
    0x6A4ABC1C: "Situation Tuning",
    # --- Erweiterte Typen für Tiefenanalyse ---
    0x015A1849: "Mesh (GEOM)",
    0x01D10F34: "Blend Geometry",
    0x0166038C: "NameMap",
    0x3C1AF1F2: "Thumbnail",
    0x2F7D0004: "DST Image",
    0x00AE6C67: "Bone Delta",
    0x062C8204: "Hotspot Control",
    0x025ED6F4: "Sim Outfit",
    0xD3044521: "Color List",
    0x0355E0A6: "Footprint",
    0xB61DE6B4: "Region Sort",
    0xF1EDBD86: "Slot Tuning",
}

# TS4 CAS Body Types
CAS_BODY_TYPES = {
    1: "Oberteil", 2: "Ganzkörper", 3: "Unterteil", 4: "Schuhe",
    5: "Hut", 6: "Brille", 7: "Halskette", 8: "Armband",
    9: "Ohrringe", 10: "Ring", 11: "Handschuhe", 12: "Socken",
    13: "Strumpfhose", 14: "Haarfarbe", 15: "Make-Up", 16: "Lidschatten",
    17: "Lippenstift", 18: "Wimpern", 19: "Gesichtsbehaarung",
    20: "Oberteil-Accessoire", 21: "Brustbehaarung", 22: "Tattoo",
    24: "Haare", 25: "Gesichts-Overlay", 26: "Kopf", 27: "Körper",
    28: "Ohrläppchen", 29: "Zähne", 30: "Fingernägel", 31: "Fußnägel",
}

TUNING_TYPES = {
    0x545AC67A, 0x03B33DDF, 0xE882D22F, 0x339BC0E4, 0x0C772E27,
    0xCB5FDDC7, 0xC0DB5AE7, 0x736884F1, 0xE5105066, 0x7FB6AD72,
    0x0904DF10, 0x8B18FF6E, 0x6A4ABC1C,
}

CORRUPT_LABELS = {
    'empty': ('Leer', 'Datei ist 0 Bytes groß'),
    'too_small': ('Zu klein', 'Datei hat weniger als 96 Bytes (kein gültiger DBPF-Header)'),
    'no_dbpf': ('Kein DBPF', 'Datei hat keinen gültigen DBPF-Magic-Header — möglicherweise beschädigt oder falsches Format'),
    'wrong_version': ('Falsche Version', 'DBPF v1 (TS2/TS3) statt v2 (TS4) — falsches Spiel?'),
    'unreadable': ('Nicht lesbar', 'Datei konnte nicht gelesen werden (Berechtigung/Zugriff)'),
}

# Bekannte große TS4-Patches (Datum, Version, Beschreibung)
# Nur Major-Patches die Mods brechen können (Gameplay-Updates, Pack-Releases)
TS4_PATCH_DATES = [
    ("2024-12-17", "1.108",  "Life & Death EP"),
    ("2024-10-01", "1.106",  "Reloaded (Freies Basis-Update)"),
    ("2024-07-25", "1.105",  "Lovestruck EP"),
    ("2024-05-14", "1.103",  "Crystal Creations SP"),
    ("2024-03-28", "1.102",  "For Rent EP / Update"),
    ("2024-01-23", "1.100",  "New Year 2024 Patch"),
    ("2023-12-05", "1.99",   "Horse Ranch Update"),
    ("2023-10-31", "1.98",   "Growing Together Update"),
    ("2023-09-21", "1.97",   "Decades Update"),
    ("2023-07-27", "1.96",   "Growing Together EP"),
    ("2023-06-01", "1.95",   "Infant Update"),
    ("2023-03-14", "1.94",   "Infant Update"),
    ("2023-01-31", "1.93",   "HSY Update"),
    ("2022-12-13", "1.92",   "Holiday 2022 Patch"),
    ("2022-10-25", "1.91",   "Werewolves Update"),
    ("2022-09-13", "1.90",   "HSY EP"),
    ("2022-07-26", "1.89",   "Werewolves GP"),
    ("2022-06-14", "1.88",   "Pronoun Update"),
    ("2022-05-24", "1.87",   "Wedding Stories Update"),
    ("2022-03-01", "1.85",   "Wedding Stories GP"),
]
