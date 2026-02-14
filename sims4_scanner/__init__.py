# -*- coding: utf-8 -*-
"""Sims 4 Duplicate Scanner – modulares Paket.

Starten mit:
    python -m sims4_scanner
"""

from .constants import SCANNER_VERSION

__version__ = SCANNER_VERSION
__all__ = [
    "SCANNER_VERSION",
    "scan_duplicates",
    "Dataset",
    "LocalServer",
    "App",
]


def scan_duplicates(*args, **kwargs):
    """Convenience re-export."""
    from .scanner import scan_duplicates as _scan
    return _scan(*args, **kwargs)


def Dataset(*args, **kwargs):          # noqa: N802
    from .dataset import Dataset as _DS
    return _DS(*args, **kwargs)


def LocalServer(*args, **kwargs):      # noqa: N802
    from .server import LocalServer as _LS
    return _LS(*args, **kwargs)


def App(*args, **kwargs):              # noqa: N802
    from .app import App as _App
    return _App(*args, **kwargs)
