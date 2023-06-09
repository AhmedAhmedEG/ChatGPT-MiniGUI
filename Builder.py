from cx_Freeze import setup, Executable
from pathlib import Path
import os

file_excludes = ['Qt6WebEngineCore.dll', 'lupdate.exe', 'Qt6Designer.dll', 'Qt6Quick.dll', 'Qt6DesignerComponents.dll',
                 'Qt6Network.dll', 'qtwebengine_devtools_resources.pak', 'qtwebengine_resources.pak', 'Qt6Qml.dll',
                 'Qt6QuickTemplates2.dll', 'Qt6Quick3DRuntimeRender.dll']

module_excludes = ['tkinter', 'PySide6.qml', 'PySide6.translations.qtwebengine_locales',
                   'PySide6.QtBluetooth', 'PySide6.QtNetwork', 'PySide6.QtNfc', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine',
                   'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebKit', 'PySide6.QtWebKitWidgets',
                   'PySide6.QtWebSockets', 'PySide6.QtSql', 'PySide6.QtNetwork', 'PySide6.QtScript']

setup(name=f'ChatGPT MiniGUI v1.0.0.0',
      version='1.0.0.0',
      options={'build_exe': {'include_files': [('Resources', 'Resources')],
                             'excludes': module_excludes}},

      executables=[Executable(script='ChatGPT-MiniGUI.py', icon='Resources/Icon.ico', base='Win32GUI')])

for root, dirs, files in os.walk('build'):

    for filename in files:

        if filename in file_excludes:
            os.remove(Path(root) / Path(filename))
