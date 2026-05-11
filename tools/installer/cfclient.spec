# -*- coding: utf-8 -*-
# PyInstaller spec file for cfclient (Aeroflie PC Client)
# Build with: pyinstaller cfclient.spec

import os
import sys
from pathlib import Path

# Add the src directory to the path so PyInstaller can find modules
_base_dir = Path(SPECPATH)
_src_dir = _base_dir.parent.parent / 'src'

_block_cipher = None

# Collect .ui files
_ui_dir = _src_dir / 'cfclient' / 'ui'
_ui_files = []
for root, dirs, files in os.walk(_ui_dir):
    for f in files:
        if f.endswith('.ui'):
            full_path = os.path.join(root, f)
            rel_dir = os.path.relpath(os.path.dirname(full_path), _ui_dir)
            dest = os.path.join('cfclient', 'ui', rel_dir)
            _ui_files.append((full_path, dest))

# Collect locale files
_locale_dir = _src_dir / 'cfclient' / 'locale'
_locale_files = []
if _locale_dir.exists():
    for f in os.listdir(_locale_dir):
        if f.endswith('.json') or f.endswith('.qm'):
            _locale_files.append(
                (os.path.join(_locale_dir, f), 'cfclient/locale')
            )

# Collect config files
_config_dir = _src_dir / 'cfclient' / 'configs'
_config_files = []
for root, dirs, files in os.walk(_config_dir):
    for f in files:
        full_path = os.path.join(root, f)
        rel_dir = os.path.relpath(os.path.dirname(full_path), _config_dir)
        dest = os.path.join('cfclient', 'configs', rel_dir)
        _config_files.append((full_path, dest))

# Collect resource files
_res_dir = _src_dir / 'cfclient' / 'resources'
_res_files = []
for root, dirs, files in os.walk(_res_dir):
    for f in files:
        full_path = os.path.join(root, f)
        rel_dir = os.path.relpath(os.path.dirname(full_path), _res_dir)
        dest = os.path.join('cfclient', 'resources', rel_dir)
        _res_files.append((full_path, dest))

# Collect icon files
_icon_dir = _src_dir / 'cfclient' / 'ui' / 'icons'
_icon_files = []
if _icon_dir.exists():
    for f in os.listdir(_icon_dir):
        _icon_files.append(
            (os.path.join(_icon_dir, f), 'cfclient/ui/icons')
        )

# Collect vispy glsl shader files (loaded at runtime via pkgutil)
_vispy_files = []
try:
    import vispy
    _vispy_root = os.path.dirname(vispy.__file__)
    for root, dirs, files in os.walk(_vispy_root):
        for f in files:
            if f.endswith('.glsl') or f.endswith('.frag') or f.endswith('.vert'):
                full_path = os.path.join(root, f)
                rel_dir = os.path.relpath(os.path.dirname(full_path), _vispy_root)
                dest = os.path.join('vispy', rel_dir)
                _vispy_files.append((full_path, dest))
    print(f"Collected {len(_vispy_files)} vispy shader files")
except ImportError:
    pass

# Merge all data files
_added_files = _ui_files + _locale_files + _config_files + _res_files + _icon_files + _vispy_files

a = Analysis(
    [os.path.join(_src_dir, 'cfclient', 'gui.py')],
    pathex=[str(_src_dir)],
    binaries=[],
    datas=_added_files,
    hiddenimports=[
        'PyQt6',
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtXml',
        'PyQt6.QtPrintSupport',
        'pyqtgraph',
        'pyqtgraph.opengl',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'vispy',
        'vispy.app',
        'vispy.app.backends._pyqt6',
        'vispy.scene',
        'vispy.gloo',
        'vispy.io',
        'vispy.util',
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.GLUT',
        'yaml',
        'zmq',
        'serial',
        'usb',
        'appdirs',
        'sdl2dll',
        'scipy',
        'cflib',
        'cflib.crtp',
        'cflib.crtp.radiodriver',
        'cflib.crtp.serialdriver',
        'cflib.crtp.tcpdriver',
        'cflib.crtp.udpdriver',
        'cflib.crtp.usbdriver',
        'cflib.crtp.pcap',
        'cflib.crazyflie',
        'cflib.crazyflie.param',
        'cflib.crazyflie.log',
        'cflib.crazyflie.mem',
        'cflib.crazyflie.commander',
        'cflib.crazyflie.high_level_commander',
        'cflib.crazyflie.localization',
        'cflib.crazyflie.syncCrazyflie',
        'cflib.crazyflie.toc',
        'cflib.crazyflie.toccache',
        'cflib.crazyflie.swarm',
        'cflib.crazyflie.mem.deck_memory',
        'cflib.crazyflie.mem.lighthouse_memory',
        'cflib.crazyflie.mem.memory_tester',
        'cflib.crazyflie.mem.paa3905_memory',
        'cflib.bootloader',
        'cflib.bootloader.boottypes',
        'cflib.bootloader.target',
        'cflib.bootloader.cloader',
        'cflib.cpx',
        'cflib.cpx.transports',
        'cflib.drivers',
        'cflib.drivers.crazyradio',
        'cflib.drivers.cfusb',
        'cflib.localization',
        'cflib.localization.lighthouse_initial_estimator',
        'cflib.localization._ippe',
        'cflib.localization.param_io',
        'cflib.positioning',
        'cflib.positioning.lighthouse_positioning',
        'cflib.utils',
        'cflib.utils.reset_estimator',
        'cflib.utils.param_file_helper',
        'cflib.utils.uri_helper',
        'cfclient',
        'cfclient.ui',
        'cfclient.ui.tabs',
        'cfclient.ui.dialogs',
        'cfclient.ui.widgets',
        'cfclient.ui.widgets.hexspinbox',
        'cfclient.ui.widgets.ai',
        'cfclient.ui.widgets.plotwidget',
        'cfclient.ui.widgets.super_slider',
        'cfclient.ui.wizards',
        'cfclient.ui.wizards.lighthouse_geo_bs_estimation_wizard',
        'cfclient.utils',
        'cfclient.utils.i18n',
        'cfclient.utils.singleton',
        'cfclient.utils.periodictimer',
        'cfclient.utils.logdatawriter',
        'cfclient.utils.cli_tr',
        'cfclient.utils.cflib_translator',
        'cfclient.utils.config',
        'cfclient.utils.config_manager',
        'cfclient.utils.input',
        'cfclient.utils.input.inputreaderinterface',
        'cfclient.utils.input.inputreaders',
        'cfclient.utils.input.inputreaders.pysdl2',
        'cfclient.utils.input.inputreaders.linuxjsdev',
        'cfclient.utils.input.inputinterfaces',
        'cfclient.utils.input.inputinterfaces.leapmotion',
        'cfclient.utils.input.inputinterfaces.wiimote',
        'cfclient.utils.input.inputinterfaces.zmqpull',
        'cfclient.utils.input.mux',
        'cfclient.utils.input.mux.nomux',
        'cfclient.utils.input.mux.takeovermux',
        'cfclient.utils.input.mux.takeoverselectivemux',
        'cfclient.utils.logconfigreader',
        'cfclient.utils.ui',
        'cfclient.utils.zmq_led_driver',
        'cfclient.utils.zmq_param',
        'cfloader',
        'cfzmq',
        'lpslib',
        'lpslib.lopoanchor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(_base_dir, 'runtime_hook_sdl2.py')],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'IPython',
        'jupyter',
        'test',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

# Add SDL2.dll binary from sdl2dll package
try:
    import sdl2dll
    _sdl2_dll_dir = os.path.join(os.path.dirname(sdl2dll.__file__), 'dll')
    if os.path.isdir(_sdl2_dll_dir):
        for f in os.listdir(_sdl2_dll_dir):
            if f.endswith('.dll'):
                a.binaries.append((f, os.path.join(_sdl2_dll_dir, f), 'BINARY'))
        print(f"Added {len([f for f in os.listdir(_sdl2_dll_dir) if f.endswith('.dll')])} SDL2 DLLs to bundle")
except ImportError:
    print("WARNING: sdl2dll not found, SDL2 DLLs will not be bundled")

pyz = PYZ(a.pure, a.zipped_data, cipher=_block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FormflieHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(_src_dir, 'cfclient', 'ui', 'icons', 'cfclient.ico'),
)
