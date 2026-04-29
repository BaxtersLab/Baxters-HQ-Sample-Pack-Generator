# PyInstaller spec for building HQSPG GUI — Windows
# Run: pyinstaller hqspg_gui.spec

block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=['.', 'bspg'],
    binaries=[],
    datas=[
        ('hqspg\\assets\\BHQSPGBackdrop.png', 'hqspg\\assets'),
        ('hqspg\\assets\\check_black.svg',     'hqspg\\assets'),
        ('gui\\styles.qss',                    'gui'),
        ('config',                             'config'),
        ('resources.qrc',                      '.'),
    ],
    hiddenimports=[
        'bspg.gui.flowchart.flowchart_widget',
        'bspg.gui.flowchart.chop_settings_popup',
        'bspg.gui.settings_panel.settings_window',
        'bspg.gui.top_lanes.lane1_run_status',
        'bspg.gui.top_lanes.lane2_file_io',
        'bspg.core.config',
        'bspg.core.logging',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='BaxtersHQSPG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='hqspg\\assets\\hqspg_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BaxtersHQSPG',
)
