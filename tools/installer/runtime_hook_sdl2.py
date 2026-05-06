# PyInstaller runtime hook: set SDL2 DLL search path for frozen apps
import os
import sys

if getattr(sys, 'frozen', False):
    os.environ['PYSDL2_DLL_PATH'] = sys._MEIPASS
