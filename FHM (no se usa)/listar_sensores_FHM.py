import subprocess
import requests
import time
import sys

# Ruta al ejecutable de LibreHardwareMonitor
LHM_PATH = r"C:\FreeHwMonitor\LibreHardwareMonitor.exe"
URL = "http://localhost:8085/data.json"

print("Iniciando LibreHardwareMonitor...")
lhm_proc = subprocess.Popen(
    [LHM_PATH],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

print("Esperando a que el servidor web esté disponible...")

timeout = 15
for _ in range(timeout):
    try:
        resp = requests.get(URL, timeout=1)
        if resp.status_code == 200:
            print("Servidor web activo.\n")
            break
    except requests.exceptions.RequestException:
        time.sleep(1)
else:
    print(f"No se pudo conectar a {URL}.")
    lhm_proc.terminate()
    sys.exit(1)


# Función recursiva para extraer todos los sensores
def extraer_sensores(node):
    sensores = []

    # Si tiene SensorId es un sensor real
    if "SensorId" in node:
        nombre = node.get("Text", "Unknown")
        tipo = node.get("Type", "Unknown")
        valor = node.get("Value", "")
        sensores.append((nombre, tipo, valor))

    for child in node.get("Children", []):
        sensores.extend(extraer_sensores(child))

    return sensores


try:
    data = requests.get(URL).json()
    sensores = extraer_sensores(data)

    print("Sensores detectados:\n")

    for nombre, tipo, valor in sensores:
        print(f"{nombre:30} → {tipo:15} → {valor}")

    print(f"\nTotal sensores encontrados: {len(sensores)}")

except KeyboardInterrupt:
    print("\nInterrumpido por el usuario.")

finally:
    if lhm_proc.poll() is None:
        print("\nCerrando LibreHardwareMonitor...")
        lhm_proc.terminate()
        try:
            lhm_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            lhm_proc.kill()

    print("Listo.")