# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

a = Analysis(['main.py'],
             pathex=[SPECPATH],
             binaries=[],
             datas=[('main.kv', '.'), ('screen_home.kv', '.'), ('screen_login.kv', '.'), ('screen_main.kv', '.'),
                     ('screen_gass_emission.kv', '.'), ('screen_diesel_emission.kv', '.'),
                     ('config.ini', '.'),
                     ('./assets/images/*.png', 'assets/images'), ('./assets/images/*.jpg', 'assets/images'),
                     ('./assets/images/*.ico', 'assets/images'),
                     ('./assets/fonts/*.ttf', 'assets/fonts'), ('./assets/fonts/*.otf', 'assets/fonts'),],
             hiddenimports=[],
             hookspath=[kivymd_hooks_path],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='TRB-VIIMS-GassEmissionMeterApp-Pandeglang',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon='./assets/images/logo-emission-app.ico' )
