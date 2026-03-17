import subprocess
import requests
import time
import json
import os
import signal
import sys

# Ruta al ejecutable de LibreHardwareMonitor
LHM_PATH = r"C:\FreeHwMonitor\LibreHardwareMonitor.exe"
URL = "http://localhost:8085/data.json"

# Lanzar LibreHardwareMonitor en background
print("Iniciando LibreHardwareMonitor...")
lhm_proc = subprocess.Popen([LHM_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Esperar a que el servidor web esté activo
print("Esperando a que el servidor web esté disponible...")
timeout = 15
for _ in range(timeout):
    try:
        resp = requests.get(URL, timeout=1)
        if resp.status_code == 200:
            print("Servidor web activo.")
            break
    except requests.exceptions.RequestException:
        time.sleep(1)
else:
    print(f"No se pudo conectar a {URL}. Asegúrate de ejecutar como administrador.")
    lhm_proc.terminate()
    sys.exit(1)

# Función para extraer solo Fan #2 y Fan #7
def extraer_fans(node):
    resultado = {}
    if node.get("Type") == "Fan" and node.get("Value"):
        nombre = node["Text"]
        if nombre in ["Fan #2", "Fan #7"]:
            rpm = int(node["Value"].replace(" RPM", ""))
            resultado[nombre] = rpm
    for child in node.get("Children", []):
        resultado.update(extraer_fans(child))
    return resultado

# Bucle principal
try:
    while True:
        data = requests.get(URL).json()
        fans = extraer_fans(data)
        print("Ventiladores:")
        for k, v in fans.items():
            print(f"{k}: {v} RPM")
        print("-" * 30)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nDeteniendo script...")

finally:
    # Terminar LibreHardwareMonitor
    if lhm_proc.poll() is None:
        print("Cerrando LibreHardwareMonitor...")
        lhm_proc.terminate()
        try:
            lhm_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            lhm_proc.kill()
    print("Listo.")