#!/usr/bin/env python3
# serie_json_2_hwinfo_mqtt.py
#
# Lee JSON de serie, lo inserta en HWiNFO y lo envía por MQTT.
# Combina funcionalidades de serie_json_2_HWiNFO.py y vatimetro.py.

import sys
import time
import json
import serial
import serial.tools.list_ports
import winreg
import argparse
import paho.mqtt.client as mqtt

# ========= WHITELIST =========

# ====== MAPEADO DE SENSORES ======
# group = agrupación (ej: LoopWater)
# type  = Temp0, Temp1, Fan0, Volt0, Other0, ...
# name  = cómo se muestra en HWiNFO
# unit  = solo si type empieza con "Other"
SENSORS = {
    # ---- Water temps (ADS1256) ----
    "water_in":        {"group":"WaterLoop", "type":"Temp0",  "name":"Water In (°C)"},
    "water_out":       {"group":"WaterLoop", "type":"Temp1",  "name":"Water Out (°C)"},
    # ---- Air temps ----
    "air_in_top":      {"group":"WaterLoop",   "type":"Temp2",  "name":"Air In Top (°C)"},
    "air_out_top":     {"group":"WaterLoop",   "type":"Temp3",  "name":"Air Out Top (°C)"},
    "air_in_bottom":   {"group":"WaterLoop",   "type":"Temp4",  "name":"Air In Bottom (°C)"},
    "air_out_bottom":  {"group":"WaterLoop",   "type":"Temp5",  "name":"Air Out Bottom (°C)"},
    "extra_temp1":     {"group":"WaterLoop", "type":"Temp6",  "name":"Extra Temp 1 (°C)"},
    "extra_temp2":     {"group":"WaterLoop", "type":"Temp7",  "name":"Extra Temp 2 (°C)"},
    # ---- Electrical (INA3221) ----
    "fans_power":      {"group":"WaterLoop", "type":"Power0", "name":"Fans Power (W)"},
    "pump_power":      {"group":"WaterLoop", "type":"Power1", "name":"Pump Power (W)"},
    "aux_power":       {"group":"WaterLoop", "type":"Power2", "name":"Aux Power (W)"},
    "fans_voltage":    {"group":"WaterLoop", "type":"Volt0",  "name":"Fans Voltage (V)"},
    "fans_current":    {"group":"WaterLoop", "type":"Current0","name":"Fans Current (A)"},
    "pump_voltage":    {"group":"WaterLoop", "type":"Volt1",  "name":"Pump Voltage (V)"},
    "pump_current":    {"group":"WaterLoop", "type":"Current1","name":"Pump Current (A)"},
    "aux_voltage":     {"group":"WaterLoop", "type":"Volt2",   "name":"Aux voltage (V)"},
    "aux_current":     {"group":"WaterLoop", "type":"Current2", "name":"Aux Current (A)"},
    # ---- RPM + Flow ----
#    "pump_rpm":        {"group":"LoopFlow",  "type":"Fan0",   "name":"Pump RPM"},
#    "fan1_rpm":        {"group":"LoopFlow",  "type":"Fan1",   "name":"Fan1 RPM"},
#    "fan2_rpm":        {"group":"LoopFlow",  "type":"Fan2",   "name":"Fan2 RPM"},
    "flow_lpm":        {"group":"WaterLoop",  "type":"Other0", "name":"Flow", "unit":"L/min"},
}

# ====== MQTT SETTINGS ======
MQTT_HOST = "155.210.152.63"
MQTT_PORT = 8080
MQTT_USERNAME = "emoncms"
MQTT_PASSWORD = "paip2020"
MQTT_TOPIC = "cooler"
MQTT_DEVICE = "sensors"
MQTT_MEASUREMENT = "sensors"

# ====== FUNCIONES ======
def write_hwinfo_sensor(group: str, stype: str, name: str, value: float, unit: str | None = None):
    reg_path = fr"Software\HWiNFO64\Sensors\Custom\{group}\{stype}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as keyreg:
        winreg.SetValueEx(keyreg, "Name",  0, winreg.REG_SZ, name)
        winreg.SetValueEx(keyreg, "Value", 0, winreg.REG_SZ, f"{value:.2f}")
        if stype.lower().startswith("other") and unit:
            winreg.SetValueEx(keyreg, "Unit", 0, winreg.REG_SZ, unit)

def choose_port_interactive() -> str:
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No se detectan puertos serie.")
        sys.exit(1)
    print("\nPuertos serie disponibles:")
    for i, p in enumerate(ports):
        print(f"[{i}] {p.device} ({p.description})")
    while True:
        try:
            idx = int(input("Selecciona el puerto (número): "))
            return ports[idx].device
        except (ValueError, IndexError):
            print("Índice no válido. Intenta de nuevo.")

# ====== MAIN ======
def main():
    ap = argparse.ArgumentParser(
        description="Bridge Serie -> HWiNFO + MQTT. "
                    "Lee JSON de serie, lo inserta en HWiNFO y lo envía por MQTT."
    )
    ap.add_argument("port", nargs="?", help="Puerto COM (ej. COM6). Si no se pasa, se listarán y podrás elegir.")
    ap.add_argument("--baud", type=int, default=115200, help="Baudrate (por defecto 115200)")
    ap.add_argument("--prefix", default="HWiNFO:", help="Prefijo de línea para procesar (por defecto 'HWiNFO:')")
    args = ap.parse_args()

    print("ℹ️  Uso:")
    print("    python serie_json_2_hwinfo_mqtt.py COM6 --baud 115200 --prefix HWiNFO:\n")

    port = args.port or choose_port_interactive()
    print(f"✅ Puerto: {port}  |  Baud: {args.baud}  |  Prefijo: '{args.prefix}'\n")

    # Inicializar MQTT
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    print(f"✅ MQTT conectado a {MQTT_HOST}:{MQTT_PORT} en topic '{MQTT_TOPIC}'\n")

    ser = serial.Serial(port, args.baud, timeout=1.0)
    time.sleep(2)  # algunos ESP reinician al abrir el puerto

    while True:
        try:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode(errors="ignore").rstrip("\r\n")

            # Eco de todo lo que llega (debug/pass-through)
            print(line)

            if not line.startswith(args.prefix):
                continue  # ignorar si no lleva prefijo

            payload = line[len(args.prefix):].strip()
            if not payload:
                continue

            # Solo JSON válido
            try:
                data = json.loads(payload)
                if not isinstance(data, dict):
                    continue
            except json.JSONDecodeError:
                print("⚠️  JSON inválido, ignorado.")
                continue

            print("    [HWiNFO] Decodificando")
            # Recorremos pares clave/valor para HWiNFO
            for k, v in data.items():
                if k not in SENSORS:
                    continue  # whitelist estricta
                try:
                    val = float(v)
                except (ValueError, TypeError):
                    continue
                meta = SENSORS[k]
                write_hwinfo_sensor(
                    meta["group"],
                    meta["type"],
                    meta["name"],
                    val,
                    unit=meta.get("unit")
                )
                print(f"       [HWiNFO] {k} -> {val:.2f}")

            # Enviar JSON completo por MQTT
            mqtt_payload = {
                "measurement": MQTT_MEASUREMENT,
                "tags": {"device": MQTT_DEVICE},
                "fields": data
            }
            msg = json.dumps(mqtt_payload, separators=(",", ":"), ensure_ascii=False)
            info = client.publish(MQTT_TOPIC, msg, qos=0, retain=False)
            info.wait_for_publish(timeout=5)
            print(f"       [MQTT] Enviado: {msg}")

        except KeyboardInterrupt:
            print("\nSaliendo…")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")

    ser.close()
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()