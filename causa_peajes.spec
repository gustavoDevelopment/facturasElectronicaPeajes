# PyInstaller: pyinstaller causa_peajes.spec  ->  dist/CausaPeajes (.app en macOS)
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("customtkinter")
datas.append(("build/tenant/tenants.json", "build/tenant"))
datas.append(("assets/icon.png", "assets"))
datas.append(("assets/icon.ico", "assets"))
for plantilla in glob.glob("main/build/tenant/*/plantilla.json"):
    datas.append((plantilla, "build/tenant/" + os.path.basename(os.path.dirname(plantilla))))

a = Analysis(
    ["gui_main.py"],
    pathex=[".", "main"],
    datas=datas,
    hiddenimports=["main.config", "main.settings", "main.logger"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="CausaPeajes",
    console=False,
    icon="assets/icon.ico" if sys.platform == "win32" else "assets/icon.icns",
)
coll = COLLECT(exe, a.binaries, a.datas, name="CausaPeajes")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Causa Peajes.app",
        icon="assets/icon.icns",
        bundle_identifier="com.causapeajes.app",
    )
