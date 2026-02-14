# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['sims4_duplicate_scanner.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sims4_scanner',
        'sims4_scanner.app',
        'sims4_scanner.server',
        'sims4_scanner.scanner',
        'sims4_scanner.dataset',
        'sims4_scanner.dbpf',
        'sims4_scanner.config',
        'sims4_scanner.constants',
        'sims4_scanner.errors',
        'sims4_scanner.history',
        'sims4_scanner.name_translation',
        'sims4_scanner.protobuf',
        'sims4_scanner.savegame',
        'sims4_scanner.tray',
        'sims4_scanner.tray_portraits',
        'sims4_scanner.update',
        'sims4_scanner.utils',
        'sims4_scanner.watcher',
        'sims4_scanner.wiki_portraits',
        'sims4_scanner.embedded_portraits',
        'sims4_scanner.townie_detector',
        'sims4_scanner.avatar_generator',
        'sims4_scanner.basegame_sims',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Sims4DuplicateScanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
