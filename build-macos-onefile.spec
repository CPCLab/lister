import os
import platform
import gooey

gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, "languages"), prefix="gooey/languages")
gooey_images = Tree(os.path.join(gooey_root, "images"), prefix="gooey/images")
import shutil
from pathlib import Path

from PyInstaller.building.api import EXE, PYZ, COLLECT
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Tree
from PyInstaller.building.osx import BUNDLE

block_cipher = None

a = Analysis(
    ["lister.py"],  # replace me with your path
    pathex=["/Users/fathoni/Code/lister/"],
    hiddenimports=[],
    hookspath=None,
    runtime_hooks=None,
)
pyz = PYZ(a.pure)

options = [("u", None, "OPTION")]


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    options,
    gooey_languages,
    gooey_images,
    name="lister",
    debug=False,
    strip=None,
    upx=True,
    console=False,
    icon=os.path.join(gooey_root, "images", "program_icon.ico"),
)

if platform.system() == "Darwin":
    info_plist = {"addition_prop": "additional_value"}
    app = BUNDLE(exe, name="lister.app", bundle_identifier=None, info_plist=info_plist)

home = str(Path.home())
file_path = home + "/Apps/lister/config.json"
shutil.copyfile("config.json", file_path)
