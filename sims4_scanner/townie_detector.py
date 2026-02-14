# -*- coding: utf-8 -*-
"""EA-Townie-Erkennung für Sims 4.

Townies = vom Spiel automatisch generierte NPCs.
Ein Sim ist ein Townie, wenn er:
  - KEIN bekannter premade Sim ist (Basegame oder Pack)
  - NICHT im Tray gefunden wurde (= kein Portrait-Match)

Enthält außerdem eine umfangreiche Liste bekannter EA-Pack-Sims
(deutsche Namen), damit diese nicht als Townies markiert werden.
"""

from __future__ import annotations

# ══════════════════════════════════════════════════════════════════
#  Bekannte premade Sims aus Erweiterungspacks (deutsche Namen)
# ══════════════════════════════════════════════════════════════════

# ── Get Together (Windenburg) ─────────────────────────────────
_WINDENBURG = {
    # Behr
    "Candy Behr", "Yuki Behr",
    # Bjergsen
    "Clara Bjergsen", "Bjorn Bjergsen", "Sofia Bjergsen", "Elsa Bjergsen",
    # Bro/Bros
    "Sergio Romeo", "Joaquin Le Chien",
    # Free Spirits
    "Ulrike Faust", "Maaike Haas",
    # Fyres
    "Moira Fyres", "Dominic Fyres", "Siobhan Fyres", "Morgan Fyres",
    # Munch
    "Mila Munch", "Gunther Munch", "Wolfgang Munch", "Lucas Munch",
    # Partihaus
    "Marcus Flex", "Paolo Rocca", "Jade Rosa", "Eva Capricciosa",
    # Villareal
    "Jacques Villareal", "Luna Villareal", "Hugo Villareal", "Max Villareal",
    # Weitere Windenburg-Sims
    "Sienna Grove", "Rohan Elderberry", "Arun Bheeda", "Jesminder Bheeda",
    "Raj Rasoya", "Geeta Rasoya", "Pinki Keen", "Mitchell Baker",
}

# ── City Living (San Myshuno) ────────────────────────────────
_SAN_MYSHUNO = {
    "Salim Benali",
    "Jesminder Bheeda", "Arun Bheeda",
    "Victor Feng", "Lily Feng",
    "Baako Jang", "Anaya Jang", "Billie Jang",
    "Miko Ojo", "Akira Kibo", "Darling Walsh",
    "Diego Lobo",
    "Penny Pizzazz",
    "Geeta Rasoya", "Raj Rasoya",
}

# ── Vampires (Forgotten Hollow) ──────────────────────────────
_FORGOTTEN_HOLLOW = {
    "Vladislaus Straud",
    "Caleb Vatore", "Lilith Vatore",
}

# ── Cats & Dogs (Brindleton Bay) ─────────────────────────────
_BRINDLETON_BAY = {
    # Delgato
    "Brent Hecking", "Brant Hecking",
    # Roswell
    "Catarina Lynx", "Izzy Roswell",
    # Spencer-Kim-Lewis erweitert
    # Andere
    "Clara Bjergsen",  # (auch Windenburg)
}

# ── Get Famous (Del Sol Valley) ──────────────────────────────
_DEL_SOL_VALLEY = {
    "Thorne Bailey", "Octavia Moon",
    "Judith Ward",
    "Venessa Jeong", "Baby Ariel",
}

# ── Island Living (Sulani) ───────────────────────────────────
_SULANI = {
    "Duane Talla", "Lilliana Talla", "Tiara Talla", "Alika Talla",
    "Oliana Ngata", "Mele Ngata", "Nalani Ngata",
    "Makoa Kealoha",
}

# ── Realm of Magic (Glimmerbrook) ────────────────────────────
_GLIMMERBROOK = {
    "Morgyn Ember",
    "Simeon Silversweig",
    "L. Faba",
    "Tomax Collette", "Darrel Charm", "Grace Anansi",
    "Emilia Jones", "Gemma Charm",
}

# ── Discover University (Britechester) ───────────────────────
_BRITECHESTER = {
    "Becca Clarke", "Cameron Fletcher",
}

# ── Eco Lifestyle (Evergreen Harbor) ─────────────────────────
_EVERGREEN_HARBOR = {
    "Knox Greenburg", "Bess Sterling",
    "Jules Rico", "Jeb Harris",
    "Yasemin Tinker", "Faye Tinker", "Tina Tinker",
}

# ── Snowy Escape (Mt. Komorebi) ──────────────────────────────
_MT_KOMOREBI = {
    "Jenna Akiyama", "Kado Akiyama", "Taku Akiyama", "Miki Akiyama",
    "Naoki Ito", "Megumi Ito", "Kiyoshi Ito", "Nanami Ito",
    "Shigeru Nishidake", "Sachiko Nishidake", "Kaori Nishidake",
}

# ── Cottage Living (Henford-on-Bagley) ───────────────────────
_HENFORD = {
    "Agatha Crumplebottom", "Agatha Knautschgesicht",  # DE: Knautschgesicht
    "Agnes Knautschgesicht", "Agnes Crumplebottom",
    "Kim Goldbloom", "Sara Scott",
}

# ── Werewolves (Moonwood Mill) ───────────────────────────────
_MOONWOOD_MILL = {
    "Kristopher Volkov", "Lily Zhu", "Lou Howell", "Jacob Volkov",
    "Rory Oaklow", "Greg",
}

# ── High School Years (Copperdale) ───────────────────────────
_COPPERDALE = {
    "Keoni Ipa'a",
}

# ── Growing Together (San Sequoia) ───────────────────────────
_SAN_SEQUOIA = {
    "Celeste Michaelson", "Christopher Michaelson", "Atlas Michaelson", "Orion Michaelson",
    "Ignacio Robles", "Bernice Robles", "Ian Robles", "Aurelio Robles",
    "Jay Robles", "Doli Ruano", "Tala Ruano",
    "Xochitl Luna", "Karmine Luna", "Eleanor Sullivan",
}

# ── Horse Ranch (Chestnut Ridge) ─────────────────────────────
_CHESTNUT_RIDGE = {
    "Clay Hess", "Sierra Hess",
    "Mabel Prescott", "Leonard Prescott",
}

# ── For Rent (Tomarang) ─────────────────────────────────────
_TOMARANG = {
    "Vanesha Cahyaputri", "Zhafira Cahyaputri",
    "Thi Linh",
    "Chánh Linh", "Arturo Linh",
    "Liên Sadya", "Alon Sadya", "Cam Sadya",
    "Bua Bun Ma", "Kasem Bun Ma", "Nin Bun Ma", "Sud Bun Ma",
}

# ── StrangerVille ────────────────────────────────────────────
_STRANGERVILLE = {
    "Ted Roswell", "Erwin Pries",
    "Christie Pike", "Jess Sigworth",
    "Dylan Sigworth", "George Cahill",
}

# ── Jungle Adventure (Selvadorada) ───────────────────────────
_SELVADORADA: set[str] = set()

# ── Outdoor Retreat (Granite Falls) ──────────────────────────
_GRANITE_FALLS: set[str] = set()

# ── Lovestruck (Ciudad Enamorada) ────────────────────────────
_CIUDAD_ENAMORADA: set[str] = set()

# ── Life & Death (Ravenwood) ─────────────────────────────────
_RAVENWOOD: set[str] = set()

# ══════════════════════════════════════════════════════════════════
#  Komplettes Set aller bekannten Pack-Sims
# ══════════════════════════════════════════════════════════════════

PACK_SIMS: frozenset[str] = frozenset(
    _WINDENBURG | _SAN_MYSHUNO | _FORGOTTEN_HOLLOW |
    _BRINDLETON_BAY | _DEL_SOL_VALLEY | _SULANI |
    _GLIMMERBROOK | _BRITECHESTER | _EVERGREEN_HARBOR |
    _MT_KOMOREBI | _HENFORD | _MOONWOOD_MILL |
    _COPPERDALE | _SAN_SEQUOIA | _CHESTNUT_RIDGE |
    _TOMARANG | _STRANGERVILLE | _SELVADORADA |
    _GRANITE_FALLS | _CIUDAD_ENAMORADA | _RAVENWOOD
)
"""Frozenset aller bekannten premade Pack-Sim-Namen."""


def detect_townies(
    sims: list[dict],
    basegame_names: set[str] | frozenset[str],
    portrait_names: list[str] | set[str],
) -> list[str]:
    """Erkennt Townies unter den Savegame-Sims.

    Ein Sim ist ein Townie, wenn er:
      1) KEIN Basegame-Sim ist
      2) KEIN bekannter Pack-Sim ist
      3) NICHT im Tray gefunden wurde (kein Portrait-Match → nicht aktiv gespielt)

    Returns:
        Liste der full_names aller erkannten Townies.
    """
    known = basegame_names | PACK_SIMS
    tray_set = set(portrait_names) if not isinstance(portrait_names, set) else portrait_names

    townies = []
    for sim in sims:
        name = sim.get("full_name", "")
        if not name:
            continue
        # Premade → kein Townie
        if name in known:
            continue
        # Im Tray gefunden → vom Spieler erstellt/gespielt → kein Townie
        if name in tray_set:
            continue
        # Alles andere → Townie
        townies.append(name)

    return townies


# Export für andere Module
__all__ = ["detect_townies", "PACK_SIMS"]
