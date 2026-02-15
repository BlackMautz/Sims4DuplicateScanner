# -*- coding: utf-8 -*-
"""DBPF v2 Parser, DDS-Decoder und Tiefenanalyse für .package-Dateien."""

from __future__ import annotations

import re
import zlib
import base64
import struct as _struct
from pathlib import Path
from collections import defaultdict

from .constants import RESOURCE_TYPE_NAMES, CAS_BODY_TYPES, TUNING_TYPES


def res_type_name(type_id: int) -> str:
    return RESOURCE_TYPE_NAMES.get(type_id, f"0x{type_id:08X}")


def read_dbpf_resource_keys(path: Path) -> list[tuple[int, int, int]] | None:
    """Liest Resource Keys (Type, Group, Instance) aus einer DBPF v2 .package-Datei."""
    try:
        with open(path, 'rb') as f:
            header = f.read(96)
            if len(header) < 96 or header[:4] != b'DBPF':
                return None
            major = _struct.unpack_from('<I', header, 4)[0]
            if major != 2:
                return None
            entry_count = _struct.unpack_from('<I', header, 36)[0]
            index_size = _struct.unpack_from('<I', header, 44)[0]
            index_offset = _struct.unpack_from('<Q', header, 64)[0]
            if entry_count > 500000:  # Sicherheit: korrupte Dateien abfangen
                return None
            if entry_count == 0:
                return []
            if index_offset == 0 or index_size < 4:
                return []
            f.seek(index_offset)
            index_data = f.read(index_size)
            if len(index_data) < index_size:
                return None

        pos = 0
        flags = _struct.unpack_from('<I', index_data, pos)[0]
        pos += 4
        const_vals = [None, None, None, None]
        for i in range(4):
            if flags & (1 << i):
                if pos + 4 > len(index_data):
                    return None
                const_vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                pos += 4
        header_bytes = pos
        remaining = index_size - header_bytes
        if entry_count > 0 and remaining > 0:
            entry_size = remaining // entry_count
        else:
            return []
        key_field_count = sum(1 for v in const_vals if v is None)
        key_bytes = key_field_count * 4
        skip_bytes = entry_size - key_bytes
        if skip_bytes < 0:
            return None

        keys = []
        for _ in range(entry_count):
            vals = list(const_vals)
            for i in range(4):
                if vals[i] is None:
                    if pos + 4 > len(index_data):
                        break
                    vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                    pos += 4
            if None in vals:
                break
            rtype, group, ihi, ilo = vals
            instance = (ihi << 32) | ilo
            keys.append((rtype, group, instance))
            pos += skip_bytes

        return keys
    except Exception:
        return None


def check_package_integrity(path: Path) -> str:
    """Prüft die DBPF-Integrität einer .package-Datei."""
    try:
        size = path.stat().st_size
        if size == 0:
            return 'empty'
        if size < 96:
            return 'too_small'
        with open(path, 'rb') as f:
            header = f.read(96)
        if len(header) < 96:
            return 'too_small'
        if header[:4] != b'DBPF':
            return 'no_dbpf'
        major = _struct.unpack_from('<I', header, 4)[0]
        if major != 2:
            return 'wrong_version'
        return 'ok'
    except (PermissionError, OSError):
        return 'unreadable'


def read_dbpf_entries(path: Path) -> list[dict] | None:
    """Liest den vollständigen DBPF v2 Index mit Offsets, Größen und Kompression."""
    try:
        with open(path, 'rb') as f:
            header = f.read(96)
            if len(header) < 96 or header[:4] != b'DBPF':
                return None
            major = _struct.unpack_from('<I', header, 4)[0]
            if major != 2:
                return None
            entry_count = _struct.unpack_from('<I', header, 36)[0]
            index_size = _struct.unpack_from('<I', header, 44)[0]
            index_offset = _struct.unpack_from('<Q', header, 64)[0]
            if entry_count == 0 or index_offset == 0 or index_size < 4:
                return []
            f.seek(index_offset)
            index_data = f.read(index_size)
            if len(index_data) < index_size:
                return None

        pos = 0
        flags = _struct.unpack_from('<I', index_data, pos)[0]
        pos += 4
        const_vals = [None, None, None, None]
        for i in range(4):
            if flags & (1 << i):
                if pos + 4 > len(index_data):
                    return None
                const_vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                pos += 4
        header_bytes = pos
        remaining = index_size - header_bytes
        if entry_count > 0 and remaining > 0:
            entry_size = remaining // entry_count
        else:
            return []
        key_field_count = sum(1 for v in const_vals if v is None)
        key_bytes = key_field_count * 4
        meta_bytes = entry_size - key_bytes

        entries = []
        for _ in range(entry_count):
            vals = list(const_vals)
            for i in range(4):
                if vals[i] is None:
                    if pos + 4 > len(index_data):
                        break
                    vals[i] = _struct.unpack_from('<I', index_data, pos)[0]
                    pos += 4
            if None in vals:
                break
            rtype, group, ihi, ilo = vals
            instance = (ihi << 32) | ilo
            offset = comp_size = uncomp_size = 0
            compression = 0
            if meta_bytes >= 16 and pos + meta_bytes <= len(index_data):
                offset = _struct.unpack_from('<I', index_data, pos)[0]
                file_size_raw = _struct.unpack_from('<I', index_data, pos + 4)[0]
                uncomp_size = _struct.unpack_from('<I', index_data, pos + 8)[0]
                compression = _struct.unpack_from('<H', index_data, pos + 12)[0]
                comp_size = file_size_raw & 0x7FFFFFFF
            pos += meta_bytes
            entries.append({
                'type': rtype, 'group': group, 'instance': instance,
                'offset': offset, 'comp_size': comp_size,
                'uncomp_size': uncomp_size, 'compression': compression,
            })
        return entries
    except Exception:
        return None


def _read_resource_data(path: Path, entry: dict) -> bytes | None:
    """Liest und dekomprimiert eine einzelne Ressource aus einer .package-Datei."""
    try:
        size_to_read = entry.get('comp_size') or entry.get('uncomp_size') or 0
        if size_to_read <= 0 or entry.get('offset', 0) <= 0:
            return None
        with open(path, 'rb') as f:
            f.seek(entry['offset'])
            raw = f.read(size_to_read)
        if not raw:
            return None
        comp = entry.get('compression', 0)
        if comp == 0x5A42:
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return raw
        elif comp == 0xFFFF:
            try:
                return zlib.decompress(raw)
            except Exception:
                return None
        return raw
    except Exception:
        return None


# ---- DDS → PNG Konvertierung ----

def _dds_to_png(dds_data: bytes, max_dim: int = 128) -> bytes | None:
    """Dekodiert DDS-Textur (DXT1/DXT5/unkomprimiert) und liefert PNG-Bytes."""
    try:
        if len(dds_data) < 128 or dds_data[:4] != b'DDS ':
            return None
        height = _struct.unpack_from('<I', dds_data, 12)[0]
        width = _struct.unpack_from('<I', dds_data, 16)[0]
        pf_flags = _struct.unpack_from('<I', dds_data, 80)[0]
        pf_fourcc = dds_data[84:88]
        pf_rgbbitcount = _struct.unpack_from('<I', dds_data, 88)[0]
        pf_rmask = _struct.unpack_from('<I', dds_data, 92)[0]
        pf_gmask = _struct.unpack_from('<I', dds_data, 96)[0]
        pf_bmask = _struct.unpack_from('<I', dds_data, 100)[0]
        pf_amask = _struct.unpack_from('<I', dds_data, 104)[0]
        if width < 8 or height < 8 or width > 2048 or height > 2048:
            return None
        pixel_data = dds_data[128:]
        rgba = None
        if pf_flags & 0x4:
            if pf_fourcc in (b'DXT1', b'DST1'):
                rgba = _decode_dxt1(pixel_data, width, height)
            elif pf_fourcc in (b'DXT5', b'DST5'):
                rgba = _decode_dxt5(pixel_data, width, height)
        elif pf_flags & 0x40:
            if pf_rgbbitcount == 32:
                rgba = _decode_rgba(pixel_data, width, height, pf_rmask, pf_gmask, pf_bmask, pf_amask)
            elif pf_rgbbitcount == 24:
                rgba = _decode_rgb24(pixel_data, width, height)
        if not rgba:
            return None
        if width > max_dim or height > max_dim:
            rgba, width, height = _downscale_rgba(rgba, width, height, max_dim)
        return _rgba_to_png(rgba, width, height)
    except Exception:
        return None


def _decode_dxt1(data: bytes, w: int, h: int) -> bytearray | None:
    bw, bh = (w + 3) // 4, (h + 3) // 4
    needed = bw * bh * 8
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    pos = 0
    for by in range(bh):
        for bx in range(bw):
            c0 = _struct.unpack_from('<H', data, pos)[0]
            c1 = _struct.unpack_from('<H', data, pos + 2)[0]
            bits = _struct.unpack_from('<I', data, pos + 4)[0]
            pos += 8
            r0, g0, b0 = (c0 >> 11) << 3, ((c0 >> 5) & 63) << 2, (c0 & 31) << 3
            r1, g1, b1 = (c1 >> 11) << 3, ((c1 >> 5) & 63) << 2, (c1 & 31) << 3
            colors = [(r0, g0, b0, 255), (r1, g1, b1, 255)]
            if c0 > c1:
                colors.append(((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3, 255))
                colors.append(((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3, 255))
            else:
                colors.append(((r0+r1)//2, (g0+g1)//2, (b0+b1)//2, 255))
                colors.append((0, 0, 0, 0))
            for py in range(4):
                for px in range(4):
                    x, y = bx*4+px, by*4+py
                    if x < w and y < h:
                        idx = (bits >> (2*(py*4+px))) & 3
                        c = colors[idx]
                        p = (y*w+x)*4
                        out[p:p+4] = bytes(c)
    return out


def _decode_dxt5(data: bytes, w: int, h: int) -> bytearray | None:
    bw, bh = (w + 3) // 4, (h + 3) // 4
    needed = bw * bh * 16
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    pos = 0
    for by in range(bh):
        for bx in range(bw):
            a0 = data[pos]; a1 = data[pos+1]
            abits = int.from_bytes(data[pos+2:pos+8], 'little')
            pos += 8
            alphas = [a0, a1]
            if a0 > a1:
                for i in range(6):
                    alphas.append(((6-i)*a0 + (1+i)*a1) // 7)
            else:
                for i in range(4):
                    alphas.append(((4-i)*a0 + (1+i)*a1) // 5)
                alphas.extend([0, 255])
            c0 = _struct.unpack_from('<H', data, pos)[0]
            c1 = _struct.unpack_from('<H', data, pos+2)[0]
            bits = _struct.unpack_from('<I', data, pos+4)[0]
            pos += 8
            r0, g0, b0 = (c0 >> 11) << 3, ((c0 >> 5) & 63) << 2, (c0 & 31) << 3
            r1, g1, b1 = (c1 >> 11) << 3, ((c1 >> 5) & 63) << 2, (c1 & 31) << 3
            colors = [(r0, g0, b0), (r1, g1, b1),
                      ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3),
                      ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3)]
            for py in range(4):
                for px in range(4):
                    x, y = bx*4+px, by*4+py
                    if x < w and y < h:
                        ci = (bits >> (2*(py*4+px))) & 3
                        ai = (abits >> (3*(py*4+px))) & 7
                        r, g, b = colors[ci]
                        a = alphas[ai]
                        p = (y*w+x)*4
                        out[p:p+4] = bytes((r, g, b, a))
    return out


def _decode_rgba(data: bytes, w: int, h: int, rm: int, gm: int, bm: int, am: int) -> bytearray | None:
    needed = w * h * 4
    if len(data) < needed:
        return None
    def _shift(mask):
        if mask == 0: return 0, 0
        s = 0
        while mask and not (mask & 1): mask >>= 1; s += 1
        return s, mask
    rs, _ = _shift(rm); gs, _ = _shift(gm); bs, _ = _shift(bm); as_, _ = _shift(am)
    out = bytearray(needed)
    for i in range(w * h):
        px = _struct.unpack_from('<I', data, i*4)[0]
        out[i*4]   = (px >> rs) & 0xFF
        out[i*4+1] = (px >> gs) & 0xFF
        out[i*4+2] = (px >> bs) & 0xFF
        out[i*4+3] = ((px >> as_) & 0xFF) if am else 255
    return out


def _decode_rgb24(data: bytes, w: int, h: int) -> bytearray | None:
    needed = w * h * 3
    if len(data) < needed:
        return None
    out = bytearray(w * h * 4)
    for i in range(w * h):
        b, g, r = data[i*3], data[i*3+1], data[i*3+2]
        out[i*4:i*4+4] = bytes((r, g, b, 255))
    return out


def _downscale_rgba(rgba: bytearray, w: int, h: int, max_dim: int):
    scale = max(w, h) / max_dim
    nw, nh = max(1, int(w / scale)), max(1, int(h / scale))
    out = bytearray(nw * nh * 4)
    for ny in range(nh):
        for nx in range(nw):
            sx = min(int(nx * scale), w - 1)
            sy = min(int(ny * scale), h - 1)
            sp = (sy * w + sx) * 4
            dp = (ny * nw + nx) * 4
            out[dp:dp+4] = rgba[sp:sp+4]
    return out, nw, nh


def _rgba_to_png(rgba: bytearray, w: int, h: int) -> bytes:
    import io
    def _crc32(data):
        return zlib.crc32(data) & 0xFFFFFFFF
    raw_rows = bytearray()
    stride = w * 4
    for y in range(h):
        raw_rows.append(0)
        raw_rows.extend(rgba[y*stride:(y+1)*stride])
    compressed = zlib.compress(bytes(raw_rows), 6)
    buf = io.BytesIO()
    buf.write(b'\x89PNG\r\n\x1a\n')
    ihdr_data = _struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    ihdr_chunk = b'IHDR' + ihdr_data
    buf.write(_struct.pack('>I', len(ihdr_data)))
    buf.write(ihdr_chunk)
    buf.write(_struct.pack('>I', _crc32(ihdr_chunk)))
    idat_chunk = b'IDAT' + compressed
    buf.write(_struct.pack('>I', len(compressed)))
    buf.write(idat_chunk)
    buf.write(_struct.pack('>I', _crc32(idat_chunk)))
    iend_chunk = b'IEND'
    buf.write(_struct.pack('>I', 0))
    buf.write(iend_chunk)
    buf.write(_struct.pack('>I', _crc32(iend_chunk)))
    return buf.getvalue()


# ---- Tiefenanalyse ----

# CAS Body Type Regex-Patterns
_AGE = r'[ycpte][fmu]'
_NAME_TO_BODY = [
    (re.compile(rf'(?:{_AGE})?Hair_|hair(?:style)?|wig', re.I), 24),
    (re.compile(r'(?:haircolor|hair_color|recolor.*hair)', re.I), 14),
    (re.compile(rf'(?:{_AGE})?Top_|(?:shirt|hoodie|jacket|blouse|sweater|tshirt|vest|coat|tank|cardigan|tee(?:_)|polo|crop(?:top|_)|blazer|pullover|parka)', re.I), 1),
    (re.compile(rf'(?:{_AGE})?Body_|(?:fullbody|full_body|dress|gown|jumpsuit|romper|onesie|bodysuit|chemise|lingerie|swimsuit|bikini|bathrobe|pajama|pyjama|nightgown|costume)', re.I), 2),
    (re.compile(rf'(?:{_AGE})?Bottom_|(?:pant|jean|skirt|shorts|trouser|legging|underwear(?!_set))', re.I), 3),
    (re.compile(rf'(?:{_AGE})?Shoe|(?:boot|sandal|sneaker|heel|slipper|loafer|flats?(?:_)|stiletto|platform|clog|mule|moccasin)', re.I), 4),
    (re.compile(rf'(?:{_AGE})?Hat_|Acc_Hat|(?:beanie|(?:^|_)cap(?:_|$)|crown|headband|headwear|turban|beret|tiara|helmet|hood(?:_|$))', re.I), 5),
    (re.compile(r'Acc_Glass|(?:glasses|sunglasses|spectacles|eyewear|monocle)', re.I), 6),
    (re.compile(r'Acc_Neck|(?:necklace|choker|pendant|collar(?:_|$)|chain(?:_neck))', re.I), 7),
    (re.compile(r'Acc_Wrist|Acc_Bracelet|(?:bracelet|bangle|wristband|cuff(?:_|$))', re.I), 8),
    (re.compile(r'Acc_Ear|(?:earring|ear_ring|ear(?:Drop|Round|Pentagon|Stud|Hoop|Dangle|Clip|Cuff|Wrap|Plug))', re.I), 9),
    (re.compile(r'Acc_Ring|(?:(?:^|_)ring(?:_|$))', re.I), 10),
    (re.compile(r'Acc_Glove|(?:glove|mitten)', re.I), 11),
    (re.compile(rf'(?:{_AGE})?Sock|sock', re.I), 12),
    (re.compile(r'(?:tight|stocking|pantyhose|legwear)', re.I), 13),
    (re.compile(r'Makeup|MakeUp|Make_Up|Facepaint|(?:blush|bronzer|contour|face_paint|highlight(?:er)?)', re.I), 15),
    (re.compile(r'(?:eyeshadow|eye_shadow)', re.I), 16),
    (re.compile(r'(?:lipstick|lip_stick|lip(?:_)?color|lipgloss|lip_gloss)', re.I), 17),
    (re.compile(r'(?:eyelash|eyeliner|lashes)', re.I), 18),
    (re.compile(r'(?:beard|facial_hair|facialhair|mustache|goatee|stubble|sideburn)', re.I), 19),
    (re.compile(r'Acc_Top|(?:scarf|shawl|cape|poncho)', re.I), 20),
    (re.compile(r'tattoo', re.I), 22),
    (re.compile(r'(?:skin(?:tone|detail|overlay|blend)?|freckle|mole|birthmark|wrinkle|scar|blemish|dimple)', re.I), 25),
    (re.compile(r'(?:nail(?:s|polish)?|fingernail|manicure)', re.I), 30),
    (re.compile(r'(?:toenail|pedicure)', re.I), 31),
    (re.compile(r'(?:eyebrow|brow(?:s|_))', re.I), 15),
]

# Alter/Geschlecht-Patterns (auf Modul-Ebene, werden nur 1× compiliert)
_AGE_PATTERNS = [
    (re.compile(r'(?:^|[_\-\s.])(?:toddler|td|tu)(?:[_\-\s.]|$)', re.I), 'Kleinkind'),
    (re.compile(r'(?:^|[_\-\s.])(?:child|cu|cf|cm)(?:[_\-\s.]|$)', re.I), 'Kind'),
    (re.compile(r'(?:^|[_\-\s.])(?:teen|tu)(?:[_\-\s.]|$)', re.I), 'Teen'),
    (re.compile(r'(?:^|[_\-\s.])(?:elder|eu|ef|em)(?:[_\-\s.]|$)', re.I), 'Ältere'),
    (re.compile(r'(?:^|[_\-\s.])(?:adult|youngadult|ya|au)(?:[_\-\s.]|$)', re.I), 'Erwachsene'),
]
_GENDER_PATTERNS = [
    (re.compile(r'(?:^|[_\-\s.])(?:female|[ycepta]f)(?:[_\-\s.]|$)', re.I), 'Weiblich'),
    (re.compile(r'(?:^|[_\-\s.])(?:male|[ycepta]m)(?:[_\-\s.]|$)', re.I), 'Männlich'),
]


def analyze_package_deep(path: Path):
    """Tiefenanalyse einer .package-Datei.
    Returns: (info_dict, all_keys_set) oder None bei Fehler.
    """
    if path.suffix.lower() != '.package':
        return None
    entries = read_dbpf_entries(path)
    if entries is None:
        return None

    type_counts = defaultdict(int)
    for e in entries:
        type_counts[res_type_name(e['type'])] += 1

    cas_count = sum(1 for e in entries if e['type'] == 0x034AEECB)
    mesh_count = sum(1 for e in entries if e['type'] in (0x015A1849, 0x01D10F34))
    texture_count = sum(1 for e in entries if e['type'] in (0xD382BF57, 0x2F7D0004))
    tuning_count = sum(1 for e in entries if e['type'] in TUNING_TYPES)

    if cas_count > 0:
        category = "CAS"
    elif mesh_count > 0 and tuning_count > 0:
        category = "Objekt/Möbel"
    elif tuning_count > 5:
        category = "Gameplay-Mod (Tuning)"
    elif mesh_count > 0:
        category = "Mesh/Build-Mod"
    elif texture_count > 0:
        category = "Textur/Override"
    else:
        category = "Sonstiges"

    all_keys = set((e['type'], e['group'], e['instance']) for e in entries)

    result = {
        'total_resources': len(entries),
        'type_breakdown': dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        'category': category,
        'cas_body_types': [],
        'tuning_names': [],
        'thumbnail_b64': None,
        'age_gender': [],
        'is_recolor': False,
    }

    # Thumbnail suchen
    _THUMB_TYPES = (0x3C1AF1F2, 0xC8A5E01A, 0x3C2A8647, 0x5B282D45, 0xCD9DE247, 0x0580A2B4, 0x0580A2B6)
    thumb_entries = [e for e in entries if e['type'] in _THUMB_TYPES]
    for te in thumb_entries[:5]:
        data = _read_resource_data(path, te)
        if data and len(data) > 8:
            if data[:4] == b'\x89PNG':
                result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(data).decode()
                break
            elif data[:2] == b'\xff\xd8':
                result['thumbnail_b64'] = 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
                break

    if not result['thumbnail_b64']:
        for e in entries:
            usz = e.get('uncomp_size', 0) or e.get('comp_size', 0)
            if usz > 200_000 or e['type'] in _THUMB_TYPES:
                continue
            data = _read_resource_data(path, e)
            if data and len(data) > 8:
                if data[:4] == b'\x89PNG':
                    result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(data).decode()
                    break
                elif data[:2] == b'\xff\xd8':
                    result['thumbnail_b64'] = 'data:image/jpeg;base64,' + base64.b64encode(data).decode()
                    break

    if not result['thumbnail_b64']:
        dds_entries = [e for e in entries if e['type'] == 0x00B2D882]
        dds_entries.sort(key=lambda e: abs((e.get('uncomp_size', 0) or e.get('comp_size', 0)) - 16000))
        for de in dds_entries[:3]:
            data = _read_resource_data(path, de)
            if data and len(data) > 128 and data[:4] == b'DDS ':
                png_data = _dds_to_png(data, max_dim=128)
                if png_data:
                    result['thumbnail_b64'] = 'data:image/png;base64,' + base64.b64encode(png_data).decode()
                    break

    # CAS Parts Body Type
    cas_entries = [e for e in entries if e['type'] == 0x034AEECB]
    body_types = set()
    cas_part_names = []
    for ce in cas_entries[:20]:
        data = _read_resource_data(path, ce)
        if not data or len(data) < 20:
            continue
        try:
            version = _struct.unpack_from('<I', data, 0)[0]
            if not (18 <= version <= 55):
                continue
            num_presets = _struct.unpack_from('<I', data, 8)[0]
            pos = 12
            for _ in range(min(num_presets, 100)):
                if pos + 12 > len(data):
                    break
                pos += 8
                xml_size = _struct.unpack_from('<I', data, pos)[0]
                pos += 4 + xml_size
            if pos >= len(data) - 2:
                continue
            name_len = data[pos]
            name_bytes = data[pos + 1:pos + 1 + name_len]
            pos += 1 + name_len
            part_name = ''
            if name_len >= 2 and name_bytes[1:2] == b'\x00':
                try:
                    part_name = name_bytes.decode('utf-16-le', errors='ignore')
                except Exception:
                    part_name = name_bytes.decode('ascii', errors='ignore')
            else:
                part_name = name_bytes.decode('ascii', errors='ignore')
            if part_name and len(cas_part_names) < 5:
                cas_part_names.append(part_name)
        except Exception:
            pass

    file_stem = path.stem
    all_name_sources = cas_part_names + [file_stem]
    for src_name in all_name_sources:
        if not src_name:
            continue
        for pat, bt_id in _NAME_TO_BODY:
            if pat.search(src_name):
                body_types.add(bt_id)
                break

    result['cas_body_types'] = [CAS_BODY_TYPES.get(bt, f"Typ {bt}") for bt in sorted(body_types)]

    ages = set()
    genders = set()
    for src_name in all_name_sources:
        if not src_name:
            continue
        for pat, label in _AGE_PATTERNS:
            if pat.search(src_name):
                ages.add(label)
        for pat, label in _GENDER_PATTERNS:
            if pat.search(src_name):
                genders.add(label)
    age_gender = sorted(ages) + sorted(genders)
    result['age_gender'] = age_gender if age_gender else []

    # ---- Recolor-Erkennung ----
    # Recolor = CAS mod ohne eigene Mesh-Geometrie (nur Texturen/Overrides)
    if cas_count > 0:
        has_mesh = mesh_count > 0
        has_recolor_hint = any(
            re.search(r'(?:recolor|recolour|swatch|palette|retexture|texture.?swap|override)', src, re.I)
            for src in all_name_sources if src
        )
        result['is_recolor'] = (not has_mesh) or has_recolor_hint

    # Tuning XML Names
    tuning_entries = [e for e in entries if e['type'] in TUNING_TYPES]
    names = []
    for te in tuning_entries[:20]:
        data = _read_resource_data(path, te)
        if not data or len(data) < 10:
            continue
        try:
            text = data.decode('utf-8', errors='ignore')
            m = re.search(r'\bn="([^"]+)"', text[:500])
            if m:
                names.append(m.group(1))
        except Exception:
            pass
    result['tuning_names'] = names[:10]

    # Kategorie verfeinern
    if result['category'] == 'CAS' and body_types:
        _HAIR_TYPES = {14, 24}
        _CLOTHING_TYPES = {1, 2, 3, 4, 5, 11, 12, 13}
        _MAKEUP_TYPES = {15, 16, 17, 18, 19, 25, 26, 27}
        _ACCESSOIRE_TYPES = {6, 7, 8, 9, 10, 20, 22, 28, 29, 30, 31}
        if body_types & _HAIR_TYPES:
            result['category'] = 'CAS (Haare 💇)'
        elif body_types & _CLOTHING_TYPES:
            result['category'] = 'CAS (Kleidung 👚)'
        elif body_types & _MAKEUP_TYPES:
            result['category'] = 'CAS (Make-Up 💄)'
        elif body_types & _ACCESSOIRE_TYPES:
            result['category'] = 'CAS (Accessoire 💍)'
        else:
            result['category'] = 'CAS (Kleidung/Haare/Make-Up)'
    elif result['category'] == 'CAS':
        result['category'] = 'CAS (Kleidung/Haare/Make-Up)'

    return result, all_keys


def analyze_with_cache(path: Path, deep_cache: dict | None):
    """Führt analyze_package_deep aus mit Cache-Unterstützung."""
    from .config import cache_entry_valid
    ps = str(path)
    if deep_cache is not None and ps in deep_cache:
        ce = deep_cache[ps]
        if cache_entry_valid(ce, path):
            return (ce['deep'], None)
    result = analyze_package_deep(path)
    if result and deep_cache is not None:
        try:
            st = path.stat()
            deep_cache[ps] = {'mt': st.st_mtime, 'sz': st.st_size, 'deep': result[0]}
        except Exception:
            pass
    return result
