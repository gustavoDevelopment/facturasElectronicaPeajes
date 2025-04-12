import time
import subprocess
import os

# Obtiene la ruta del script actual (el launcher.py)
base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_script = os.path.join(base_dir, "factusTurboV2.py")

while True:
    print(f"🚀 Ejecutando script: {ruta_script}")
    subprocess.run(["python", ruta_script], check=True)

    print("⏳ Esperando 1 minutos...\n")
    time.sleep(60)
