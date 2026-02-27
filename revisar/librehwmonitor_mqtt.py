import subprocess
import requests
import time
import sys
import os
import re
import json
from datetime import datetime

LHM_PATH = r"C:\FreeHwMonitor\LibreHardwareMonitor.exe"
URL = "http://localhost:8085/data.json"
INTERVALO = 1
LOG_FILE = "librehwmonitor.json"

# Al iniciar, reiniciamos el log
with open(LOG_FILE, "w") as f:
    f.write("")

print("Iniciando LibreHardwareMonitor...")
lhm_proc = subprocess.Popen(
    [LHM_PATH],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

print("Esperando servidor web...")
for _ in range(15):
    try:
        if requests.get(URL, timeout=1).status_code == 200:
            break
    except:
        time.sleep(1)
else:
    print("No se pudo conectar.")
    lhm_proc.terminate()
    sys.exit(1)

def limpiar():
    os.system("cls")

def extraer_numero(texto):
    nums = re.findall(r'\d+', texto)
    return int(nums[0]) if nums else None

def recorrer(node, fans, temps, volts, power, load, ram):
    if "SensorId" in node:
        nombre = node.get("Text", "")
        tipo = node.get("Type", "")
        valor = node.get("Value", "")

        if not valor or valor == "-":
            return

        # 🌀 VENTILADORES
        if tipo == "Fan":
            rpm = int(str(valor).replace(" RPM", ""))
            if rpm > 0:
                if nombre == "Fan #2":
                    fans["Ventiladores"] = rpm
                elif nombre == "Fan #7":
                    fans["Bomba"] = rpm

        # 🌡 TEMPERATURAS CPU y RAM
        elif tipo == "Temperature":
            try:
                val = float(str(valor).replace(",", ".").replace(" °C", ""))
            except:
                return
            if "CPU Package" in nombre:
                temps["CPU Package"] = val
            elif ("P-Core" in nombre or "E-Core" in nombre) and "Distance" not in nombre:
                idx = extraer_numero(nombre)
                temps[idx-1] = val
            elif "DIMM" in nombre:
                ram[nombre] = val

        # 🔌 VOLTAJES
        elif tipo == "Voltage":
            try:
                val = float(str(valor).replace(",", ".").replace(" V", ""))
            except:
                return
            if "CPU Core" in nombre:
                volts["CPU Package"] = val
            elif "P-Core" in nombre or "E-Core" in nombre:
                idx = extraer_numero(nombre)
                volts[idx-1] = val

        # ⚡ POTENCIA
        elif tipo == "Power":
            try:
                val = float(str(valor).replace(",", ".").replace(" W", ""))
            except:
                return
            power[nombre] = val

        # 📊 LOAD
        elif tipo == "Load":
            if "CPU Core #" in nombre:
                idx = extraer_numero(nombre)
                load[idx-1] = float(str(valor).replace(",", ".").replace(" %", ""))

    for child in node.get("Children", []):
        recorrer(child, fans, temps, volts, power, load, ram)

def guardar_log(fans, temps, volts, power, load, ram):
    fields = {}

    # Ventiladores
    for k, v in fans.items():
        key = k.lower().replace(" ", "_")
        fields[key] = v

    # Temperaturas cores
    for k, v in temps.items():
        if k == "CPU Package":
            fields["cpu_package_temp"] = v
        else:
            fields[f"core{k}_temp"] = v

    # Voltajes cores
    for k, v in volts.items():
        if k == "CPU Package":
            fields["cpu_package_volt"] = v
        else:
            fields[f"core{k}_volt"] = v

    # Potencia
    for k, v in power.items():
        key = k.lower().replace(" ", "_") + "_power"
        fields[key] = v

    # Load cores
    for k, v in load.items():
        fields[f"core{k}_load"] = v

    # RAM
    for k, v in ram.items():
        key = k.lower().replace(" ", "_") + "_temp"
        fields[key] = v

    line = {
        "measurement": "librehwmonitor",
        "tags": {"device": "librehwmonitor"},
        "fields": fields,
        "timestamp": datetime.utcnow().isoformat()
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(line) + "\n")

try:
    while True:
        data = requests.get(URL).json()

        fans = {}
        temps = {}
        volts = {}
        power = {}
        load = {}
        ram = {}

        recorrer(data, fans, temps, volts, power, load, ram)
        # limpiar()

        # Guardar log
        guardar_log(fans, temps, volts, power, load, ram)

       
        time.sleep(INTERVALO)

except KeyboardInterrupt:
    print("\nDeteniendo monitor...")

finally:
    if lhm_proc.poll() is None:
        lhm_proc.terminate()