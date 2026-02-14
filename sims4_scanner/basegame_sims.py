# -*- coding: utf-8 -*-
"""Bekannte vorgefertigte Sims aus dem Sims 4 Basegame.

Enthält die vollständigen Namen der EA-erstellten Sims, die mit dem
Basisspiel (ohne Erweiterungen) in Willow Creek und Oasis Springs leben.
Deutsche Version.
"""

from __future__ import annotations

# ── Willow Creek ─────────────────────────────────────────────────

# Grusel-Familie (EN: Goth)
_GRUSEL = {
    "Bella Grusel",
    "Mortimer Grusel",
    "Kassandra Grusel",
    "Alexander Grusel",
}

# Landgraab-Familie
_LANDGRAAB = {
    "Geoffrey Landgraab",
    "Nancy Landgraab",
    "Malcolm Landgraab",
}

# Spencer-Kim-Lewis-Familie
_SPENCER_KIM_LEWIS = {
    "Dennis Kim",
    "Alice Spencer-Kim",
    "Olivia Kim-Lewis",
    "Eric Lewis",
}

# Pancakes-Familie
_PANCAKES = {
    "Bob Pancakes",
    "Eliza Pancakes",
}

# Beste Freunde auf Lebenszeit (EN: BFF Household)
_BFF = {
    "Liberty Lee",
    "Travis Scott",
    "Summer Holiday",
}

# ── Oasis Springs ────────────────────────────────────────────────

# Caliente-Haushalt (inkl. Don Lothario)
_CALIENTE = {
    "Dina Caliente",
    "Nina Caliente",
    "Don Lothario",
    "Katrina Caliente",  # Später hinzugefügt, aber Basegame-Update
}

# Mitbewohner (EN: Roomies)
_ROOMIES = {
    "J Huntington III",
    "Gavin Richards",
    "Mitchell Kalani",
}

# ── Komplettes Set ───────────────────────────────────────────────

BASEGAME_SIMS: frozenset[str] = frozenset(
    _GRUSEL | _LANDGRAAB | _SPENCER_KIM_LEWIS | _PANCAKES |
    _BFF | _CALIENTE | _ROOMIES
)
"""Frozenset aller bekannten Basegame-Sim-Namen (Vollname)."""


def is_basegame_sim(full_name: str) -> bool:
    """Prüft ob ein Sim ein vorgefertigter Basegame-Sim ist."""
    return full_name in BASEGAME_SIMS
