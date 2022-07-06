# -*- mode: python ; coding: utf-8 -*-
"""
Example build.spec file

This hits most of the major notes required for
building a stand alone version of your Gooey application.
"""


import os
import platform
import gooey
gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')


print("GOOEY ROOT PRINTED BELOW----------------------------------------------------------------------------")
print(gooey_root)
print("GOOEY LANGUAGES PRINTED BELOW----------------------------------------------------------------------------")
print(gooey_languages)
print("GOOEY IMAGES PRINTED BELOW----------------------------------------------------------------------------")
print(gooey_images)


from PyInstaller.building.api import EXE, PYZ, COLLECT
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Tree
from PyInstaller.building.osx import BUNDLE

block_cipher = None

a = Analysis(['lister.py'],  # replace me with your path
             pathex=['/Users/fathoni/Code/lister/'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             datas=[ ('config.json', '.') ]
             )
pyz = PYZ(a.pure)

# options = [('u', None, 'OPTION'), ('v', None, 'OPTION'), ('w', None, 'OPTION')]
options= [('u', None, 'OPTION')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          gooey_languages,
          gooey_images,
          name='lister',
          debug=True,
          strip=None,
          upx=True,
          console=False,
          icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))


info_plist = {'addition_prop': 'additional_value'}
app = BUNDLE(exe,
             name='lister.app',
             bundle_identifier=None,
             info_plist=info_plist
            )

print("APP PRINTED BELOW----------------------------------------------------------------------------")
print(app)
import shutil
#copy config.json to dist directory (using DISTPATH - a global variable available in the Spec file.) with config.json
# as the file name
shutil.copyfile('config.json', '{0}/config.json'.format(DISTPATH))

import sys
directory = os.getcwd()
print("CURRENT DIRECTORY ______________________________________________________________ :")
print(directory)
print("Python version")
print (sys.version)