# -*- mode: python ; coding: utf-8 -*-
import os

# Get the base directory using an absolute path
basedir = os.path.abspath('.')

a = Analysis(
    ['src/main.py'],
    pathex=[basedir],
    binaries=[],
    datas=[
        ('src/api', 'api'),
        ('src/ui', 'ui'),
        ('src/utils', 'utils'),
        ('.env', '.'),
    ],
    hiddenimports=[
        # Core modules
        'sqlite3',
        'requests', 
        'python_dotenv',
        'dotenv',
        'psutil',
        'asyncio',
        'flet',
        
        # Standard library modules
        'json',
        'datetime',
        'time',
        'os',
        'sys',
        
        # Submodules that might be needed
        'sqlite3.dbapi2',
        'flet.version',
        'flet.web_renderer',
        'dotenv.main',
        'dotenv.parser',
        'dotenv.variables',
    ],
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
    name='aichat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
