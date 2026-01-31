# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Custom Autocorrect.

Build with: pyinstaller CustomAutocorrect.spec
Or use: python build.py
"""

block_cipher = None

# Bundled data files
# Format: (source_path, destination_folder_in_bundle)
datas = [
    ('resources/icon.png', 'resources'),
    ('resources/words.txt', 'resources'),
]

# Hidden imports that PyInstaller might miss
# These are dynamically imported or platform-specific
hiddenimports = [
    # Windows keyboard backend
    'keyboard._winkeyboard',
    # Windows tray backend
    'pystray._win32',
    # UI Automation for password field detection
    'comtypes',
    'comtypes.client',
    'comtypes.stream',
    # Pillow/tkinter interaction
    'PIL._tkinter_finder',
    # Tkinter for dialogs (should be included but just in case)
    'tkinter',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'tkinter.ttk',
]

a = Analysis(
    ['src/custom_autocorrect/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude packages we don't need to reduce size
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'hypothesis',
        '_pytest',
    ],
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
    name='CustomAutocorrect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression to reduce size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',  # Windows executable icon
)
