# -*- mode: python ; coding: utf-8 -*-
# linux-onefile

import gooey

gooey_root = os.path.dirname(gooey.__file__)

block_cipher = None

a = Analysis(
    ["../lister.py"],
    pathex=["/home/fath/Code/lister"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
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
    name="lister",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(gooey_root, "images", "program_icon.ico"),
)

import shutil

shutil.copyfile("config.json", "{0}/config.json".format(DISTPATH))
