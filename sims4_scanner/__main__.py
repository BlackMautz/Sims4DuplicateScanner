# -*- coding: utf-8 -*-
"""Entry-Point: python -m sims4_scanner"""

from .app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
