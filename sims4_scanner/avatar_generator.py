# -*- coding: utf-8 -*-
"""SVG-Avatar-Generator für Sims ohne SGI-Portrait.

Erzeugt ein einzigartiges, stilisiertes Avatar-Bild basierend auf
Geschlecht, Alter, Hautton und Spezies des Sims.
"""

from __future__ import annotations

import hashlib
import math


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """HSL → RGB Konvertierung."""
    if s == 0:
        v = int(l * 255)
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    def hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
    return int(r * 255), int(g * 255), int(b * 255)


def _skin_color(skin_tone: str) -> str:
    """Hautton → Farbe für den Avatar-Körper."""
    mapping = {
        "Sehr hell": "#FDEBD0",
        "Hell":      "#F5CBA7",
        "Mittel":    "#D4A574",
        "Dunkel":    "#8D6E63",
    }
    return mapping.get(skin_tone, "#E0C8A8")


def generate_sim_avatar(
    name: str,
    gender: str = "Unbekannt",
    age: str = "Erwachsener",
    skin_tone: str = "",
    species: str = "",
    size: int = 256,
) -> bytes:
    """Erzeugt ein SVG-Avatar als bytes.

    Das Avatar zeigt eine stilisierte Silhouette mit:
    - Einzigartiger Hintergrundfarbe basierend auf dem Namen
    - Geschlechtsspezifischer Silhouette
    - Hautton-basierter Körperfarbe
    - Altersabhängigen Details
    - Spezies-Markierungen (Vampir-Zähne, Zauberer-Hut)
    """
    # Deterministische Farben aus dem Namen generieren
    h1 = int(hashlib.md5(name.encode()).hexdigest()[:4], 16) % 360
    h2 = (h1 + 35) % 360

    is_male = gender == "Männlich"
    is_female = gender == "Weiblich"

    # Hintergrundfarben
    if is_male:
        bg1 = _hsl_to_rgb(h1 / 360, 0.55, 0.25)
        bg2 = _hsl_to_rgb(h2 / 360, 0.50, 0.15)
    elif is_female:
        bg1 = _hsl_to_rgb(h1 / 360, 0.55, 0.28)
        bg2 = _hsl_to_rgb(h2 / 360, 0.50, 0.15)
    else:
        bg1 = _hsl_to_rgb(h1 / 360, 0.35, 0.25)
        bg2 = _hsl_to_rgb(h2 / 360, 0.30, 0.15)

    bg1_hex = f"#{bg1[0]:02x}{bg1[1]:02x}{bg1[2]:02x}"
    bg2_hex = f"#{bg2[0]:02x}{bg2[1]:02x}{bg2[2]:02x}"

    # Akzentfarbe (für Glow/Dekorationen)
    accent = _hsl_to_rgb(h1 / 360, 0.7, 0.55)
    accent_hex = f"#{accent[0]:02x}{accent[1]:02x}{accent[2]:02x}"
    accent_dim = _hsl_to_rgb(h1 / 360, 0.5, 0.35)
    accent_dim_hex = f"#{accent_dim[0]:02x}{accent_dim[1]:02x}{accent_dim[2]:02x}"

    # Hautfarbe
    skin = _skin_color(skin_tone)

    # Haarfarbe aus Name-Hash
    h_hair = int(hashlib.md5(f"{name}:hair".encode()).hexdigest()[:2], 16)
    hair_colors = [
        "#1a1a2e",  # Schwarz
        "#4a3728",  # Dunkelbraun
        "#7a5c3c",  # Braun
        "#c49a6c",  # Hellbraun / Blond
        "#e8c170",  # Blond
        "#8b1a1a",  # Rot/Auburn
        "#2d1b2e",  # Sehr dunkel
        "#5c3317",  # Kastanie
    ]
    hair = hair_colors[h_hair % len(hair_colors)]

    # Altersbedingte Skalierung
    scale = 1.0
    y_offset = 0
    if age == "Baby":
        scale = 0.5
        y_offset = 50
    elif age == "Kleinkind":
        scale = 0.6
        y_offset = 35
    elif age == "Kind":
        scale = 0.75
        y_offset = 20
    elif age == "Teen":
        scale = 0.9
        y_offset = 6

    # ── SVG-Aufbau ──
    cx, cy_head = 128, 80  # Kopfmittelpunkt
    head_r = 38  # Kopfradius

    # Körper (Schultern + Torso)
    if is_male:
        shoulder_w = 90
        body_path = f"M{cx - shoulder_w},{size} C{cx - shoulder_w},{cy_head + head_r + 30} {cx - shoulder_w // 2},{cy_head + head_r + 10} {cx},{cy_head + head_r + 8} C{cx + shoulder_w // 2},{cy_head + head_r + 10} {cx + shoulder_w},{cy_head + head_r + 30} {cx + shoulder_w},{size} Z"
    elif is_female:
        shoulder_w = 75
        body_path = f"M{cx - shoulder_w},{size} C{cx - shoulder_w},{cy_head + head_r + 35} {cx - shoulder_w // 2},{cy_head + head_r + 12} {cx},{cy_head + head_r + 8} C{cx + shoulder_w // 2},{cy_head + head_r + 12} {cx + shoulder_w},{cy_head + head_r + 35} {cx + shoulder_w},{size} Z"
    else:
        shoulder_w = 80
        body_path = f"M{cx - shoulder_w},{size} C{cx - shoulder_w},{cy_head + head_r + 32} {cx - shoulder_w // 2},{cy_head + head_r + 11} {cx},{cy_head + head_r + 8} C{cx + shoulder_w // 2},{cy_head + head_r + 11} {cx + shoulder_w},{cy_head + head_r + 32} {cx + shoulder_w},{size} Z"

    # Haare
    hair_svg = ""
    h_style = int(hashlib.md5(f"{name}:style".encode()).hexdigest()[:2], 16) % 6

    if is_female:
        if h_style < 2:
            # Lange Haare
            hair_svg = f'''<ellipse cx="{cx}" cy="{cy_head - 5}" rx="{head_r + 8}" ry="{head_r + 5}" fill="{hair}" />
            <path d="M{cx - head_r - 6},{cy_head + 10} Q{cx - head_r - 12},{cy_head + 80} {cx - head_r + 5},{cy_head + 95} L{cx - head_r + 15},{cy_head + 50} Z" fill="{hair}" opacity="0.9" />
            <path d="M{cx + head_r + 6},{cy_head + 10} Q{cx + head_r + 12},{cy_head + 80} {cx + head_r - 5},{cy_head + 95} L{cx + head_r - 15},{cy_head + 50} Z" fill="{hair}" opacity="0.9" />'''
        elif h_style < 4:
            # Bob / Mittellang
            hair_svg = f'''<ellipse cx="{cx}" cy="{cy_head - 5}" rx="{head_r + 7}" ry="{head_r + 4}" fill="{hair}" />
            <path d="M{cx - head_r - 5},{cy_head + 5} Q{cx - head_r - 8},{cy_head + 45} {cx - head_r + 10},{cy_head + 55} L{cx - head_r + 10},{cy_head + 20} Z" fill="{hair}" opacity="0.85" />
            <path d="M{cx + head_r + 5},{cy_head + 5} Q{cx + head_r + 8},{cy_head + 45} {cx + head_r - 10},{cy_head + 55} L{cx + head_r - 10},{cy_head + 20} Z" fill="{hair}" opacity="0.85" />'''
        else:
            # Hochgesteckt / Pferdeschwanz
            hair_svg = f'''<ellipse cx="{cx}" cy="{cy_head - 8}" rx="{head_r + 5}" ry="{head_r + 2}" fill="{hair}" />
            <circle cx="{cx}" cy="{cy_head - head_r - 8}" r="15" fill="{hair}" />'''
    else:
        if h_style < 3:
            # Kurze Haare
            hair_svg = f'''<ellipse cx="{cx}" cy="{cy_head - 8}" rx="{head_r + 5}" ry="{head_r}" fill="{hair}" />'''
        elif h_style < 5:
            # Etwas länger oben
            hair_svg = f'''<path d="M{cx - head_r - 3},{cy_head - 3} Q{cx - head_r},{cy_head - head_r - 15} {cx},{cy_head - head_r - 18} Q{cx + head_r},{cy_head - head_r - 15} {cx + head_r + 3},{cy_head - 3} Q{cx + head_r + 5},{cy_head - head_r} {cx},{cy_head - head_r - 5} Q{cx - head_r - 5},{cy_head - head_r} {cx - head_r - 3},{cy_head - 3} Z" fill="{hair}" />'''
        else:
            # Undercut / Igel
            hair_svg = f'''<path d="M{cx - head_r},{cy_head} Q{cx - head_r - 2},{cy_head - head_r - 5} {cx},{cy_head - head_r - 12} Q{cx + head_r + 2},{cy_head - head_r - 5} {cx + head_r},{cy_head} Q{cx + head_r - 5},{cy_head - head_r + 8} {cx},{cy_head - head_r + 5} Q{cx - head_r + 5},{cy_head - head_r + 8} {cx - head_r},{cy_head} Z" fill="{hair}" />'''

    # Spezies-Extras
    species_svg = ""
    if species == "Vampir":
        # Kleine Fangzähne + roter Glow
        species_svg = f'''
        <line x1="{cx - 8}" y1="{cy_head + 22}" x2="{cx - 6}" y2="{cy_head + 30}" stroke="white" stroke-width="2.5" stroke-linecap="round" />
        <line x1="{cx + 8}" y1="{cy_head + 22}" x2="{cx + 6}" y2="{cy_head + 30}" stroke="white" stroke-width="2.5" stroke-linecap="round" />
        <circle cx="{cx}" cy="{cy_head}" r="{head_r + 15}" fill="none" stroke="#cc0000" stroke-width="1" opacity="0.3" />'''
    elif species == "Zauberer":
        # Funkelnde Partikel
        sparkle_x = [cx - 45, cx + 50, cx - 30, cx + 35, cx]
        sparkle_y = [cy_head - 40, cy_head - 25, cy_head + 60, cy_head + 50, cy_head - 55]
        for i, (sx, sy) in enumerate(zip(sparkle_x, sparkle_y)):
            r_sp = 2 + (i % 3)
            species_svg += f'<circle cx="{sx}" cy="{sy}" r="{r_sp}" fill="{accent_hex}" opacity="{0.4 + (i % 3) * 0.2}"><animate attributeName="opacity" values="{0.4 + (i % 3) * 0.2};0.8;{0.4 + (i % 3) * 0.2}" dur="{1.5 + i * 0.3}s" repeatCount="indefinite"/></circle>'

    # Augen
    eye_y = cy_head + 2
    eye_sep = 14
    eye_color = accent_hex if species == "Vampir" else "#2c3e50"
    if species == "Vampir":
        eye_color = "#cc2200"
    eyes_svg = f'''
    <ellipse cx="{cx - eye_sep}" cy="{eye_y}" rx="5" ry="5.5" fill="white" />
    <ellipse cx="{cx + eye_sep}" cy="{eye_y}" rx="5" ry="5.5" fill="white" />
    <circle cx="{cx - eye_sep}" cy="{eye_y}" r="3" fill="{eye_color}" />
    <circle cx="{cx + eye_sep}" cy="{eye_y}" r="3" fill="{eye_color}" />
    <circle cx="{cx - eye_sep + 1}" cy="{eye_y - 1}" r="1" fill="white" />
    <circle cx="{cx + eye_sep + 1}" cy="{eye_y - 1}" r="1" fill="white" />'''

    # Mund (lächelnd)
    mouth_y = cy_head + 16
    mouth_svg = f'<path d="M{cx - 10},{mouth_y} Q{cx},{mouth_y + 8} {cx + 10},{mouth_y}" stroke="#c0392b" stroke-width="2" fill="none" stroke-linecap="round" />'

    # Baby/Kleinkind: Schnuller statt Mund
    if age in ("Baby", "Kleinkind"):
        mouth_svg = f'''<circle cx="{cx}" cy="{mouth_y + 2}" r="6" fill="#FFB6C1" stroke="#FF69B4" stroke-width="1" />
        <circle cx="{cx}" cy="{mouth_y + 2}" r="3" fill="#FF69B4" />'''

    # Ältere Sims: graue Haare
    if age == "Älterer":
        hair = "#9e9e9e"

    # ── Initials-Badge unten ──
    initials = ""
    parts = name.split()
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[-1][0]).upper()
    elif parts:
        initials = parts[0][:2].upper()

    # ── Zusammenbau ──
    transform = ""
    if scale < 1.0:
        transform = f' transform="translate({cx * (1 - scale)},{y_offset + 128 * (1 - scale)}) scale({scale})"'

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg1_hex}" />
      <stop offset="100%" stop-color="{bg2_hex}" />
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="40%" r="50%">
      <stop offset="0%" stop-color="{accent_hex}" stop-opacity="0.15" />
      <stop offset="100%" stop-color="{accent_hex}" stop-opacity="0" />
    </radialGradient>
    <clipPath id="card"><rect width="{size}" height="{size}" rx="8" /></clipPath>
  </defs>

  <g clip-path="url(#card)">
    <!-- Hintergrund -->
    <rect width="{size}" height="{size}" fill="url(#bg)" />
    <rect width="{size}" height="{size}" fill="url(#glow)" />

    <!-- Dekorative Kreise -->
    <circle cx="30" cy="30" r="60" fill="{accent_hex}" opacity="0.06" />
    <circle cx="220" cy="200" r="80" fill="{accent_hex}" opacity="0.04" />

    <g{transform}>
      <!-- Körper -->
      <path d="{body_path}" fill="{skin}" opacity="0.9" />

      <!-- Haare (hinter Kopf) -->
      {hair_svg}

      <!-- Kopf -->
      <circle cx="{cx}" cy="{cy_head}" r="{head_r}" fill="{skin}" />

      <!-- Augen -->
      {eyes_svg}

      <!-- Mund -->
      {mouth_svg}

      <!-- Spezies-Extras -->
      {species_svg}
    </g>

    <!-- Initials-Badge -->
    <rect x="{size - 52}" y="{size - 36}" width="44" height="28" rx="6" fill="{accent_dim_hex}" opacity="0.85" />
    <text x="{size - 30}" y="{size - 16}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="white" opacity="0.9">{initials}</text>
  </g>
</svg>'''

    return svg.encode("utf-8")
