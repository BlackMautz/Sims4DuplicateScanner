#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sims 4 Duplicate Scanner – Einstiegspunkt (EXE / CLI).

Dieses Skript ist nur ein duenner Wrapper.
Die gesamte Logik liegt im Paket ``sims4_scanner/``.
"""

import sys
import os

# Sicherstellen, dass das Verzeichnis dieses Skripts im Suchpfad liegt,
# damit `import sims4_scanner` auch als PyInstaller-Onefile funktioniert.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from sims4_scanner.app import App   # noqa: E402


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()