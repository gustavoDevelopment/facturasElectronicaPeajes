# PyInstaller: pyinstaller facturae.spec  ->  dist/FacturaeOptimus (.app en macOS)
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("customtkinter")
datas.append(("build/tenant/tenants.json", "build/tenant"))
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
    name="FacturaeOptimus",
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="FacturaeOptimus")

if sys.platform == "darwin":
    app = BUNDLE(coll, name="FacturaeOptimus.app", bundle_identifier="com.facturae.optimus")
