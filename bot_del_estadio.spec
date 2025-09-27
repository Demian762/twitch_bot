# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bot_del_estadio.py'],
    pathex=[],
    binaries=[('D:\\02 - practicas Python\\00_twitch_bot\\ffmpeg\\ffmpeg.exe', 'ffmpeg'), ('D:\\02 - practicas Python\\00_twitch_bot\\bot-env\\Lib\\site-packages\\fake_useragent\\data\\browsers.json', 'fake_useragent/data')],
    datas=[('storage/*', 'storage'), ('telegram_bot', 'telegram_bot')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='bot_del_estadio',
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
