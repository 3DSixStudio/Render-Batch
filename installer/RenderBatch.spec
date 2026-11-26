# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Render Batch (onedir). Build:  pyinstaller installer/RenderBatch.spec --noconfirm
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT, "scs_render_core.py"), "."),
    (os.path.join(ROOT, "asset_render_core.py"), "."),
    (os.path.join(ROOT, "version.txt"), "."),
    (os.path.join(ROOT, "release_notes.md"), "."),
    (os.path.join(ROOT, "ui"), "ui"),
]

# Qt modules the app never uses - keeps the installer small
excludes = [
    "tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
    "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtPdf",
    "PySide6.QtBluetooth", "PySide6.QtPositioning", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtOpenGL",
    "PySide6.QtNetwork",
]

a = Analysis(
    [os.path.join(ROOT, "scs_batch_render_app.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=["blender_finder", "updater", "PySide6.QtSvg"],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RenderBatch",
    icon=os.path.join(ROOT, "icon.ico"),
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="RenderBatch", upx=False)
