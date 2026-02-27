#!/usr/bin/env python3
# mqtt_serial.py
#
# Lee datos de un dispositivo por serie y los envía a MQTT como JSON.
# V → Vin, A → Iin, W → W
# Por defecto usa COM4, pero se puede pasar otro puerto como argumento.

import json
import re
import serial
import time
import argparse
import paho.mqtt.client as mqtt

# MQTT settings
HOST = "155.210.152.63"
PORT = 8080
USERNAME = "emoncms"
PASSWORD = "paip2020"
TOPIC = "cooler"
DEVICE = ["vatimetro", "hwinfo", "pcm"]
# Serial settings
DEFAULT_SERIAL_PORT = "COM4"
HWINFO_JSON_PATH = "hwinfo.json"
BAUDRATE = 9600
TIMEOUT = 1  # segundos

# Expresiones regulares para parsear líneas
RE_V = re.compile(r"V\s+\dN\s+([0-9.E+-]+)")
RE_A = re.compile(r"A\s+\dN\s+([0-9.E+-]+)")
RE_W = re.compile(r"W\s+\dN\s+([0-9.E+-]+)")

def parse_line(line):
    """Intenta extraer Vin, Iin o W de una línea serie"""
    line = line.strip()
    vin, iin, w = None, None, None

    match_v = RE_V.search(line)
    if match_v:
        vin = float(match_v.group(1))
    
    match_a = RE_A.search(line)
    if match_a:
        iin = float(match_a.group(1))
    
    match_w = RE_W.search(line)
    if match_w:
        w = float(match_w.group(1))

    return vin, iin, w

def read_hwinfo_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        fields = {}
        for name, obj in data.items():
            if "Value" in obj:
                fields[name] = obj["Value"]

        return fields

    except Exception:
        return None


def main():
    # Argumentos
    parser = argparse.ArgumentParser(description="Leer serie y enviar a MQTT")
    parser.add_argument(
        "-p", "--port", default=DEFAULT_SERIAL_PORT,
        help=f"Puerto serie (default: {DEFAULT_SERIAL_PORT})"
    )
    args = parser.parse_args()
    serial_port = args.port

    # Inicializa MQTT
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(HOST, PORT, keepalive=30)
    client.loop_start()

    # Inicializa Serial
    ser = serial.Serial(serial_port, BAUDRATE, timeout=TIMEOUT)
    print(f"Leyendo datos de {serial_port} y enviando a MQTT...")

    vin_val, iin_val, w_val = None, None, None
    last_hwinfo_time = 0
    HWINFO_INTERVAL = 2  # Leer HWiNFO cada 2 segundos para no saturar
    try:
        while True:
            line = ser.readline().decode(errors="ignore")
            if not line:
                continue

            vin, iin, w = parse_line(line)

            # Actualiza valores si se detectaron
            if vin is not None:
                vin_val = vin
            if iin is not None:
                iin_val = iin
            if w is not None:
                w_val = w

            # Si tenemos un conjunto completo, lo enviamos
            if vin_val is not None and iin_val is not None and w_val is not None:
                payload = {
                    "measurement": "power_in",
                    "tags": {"device": DEVICE[0]},
                    "fields": {
                        "ver": "1",
                        "Vin": vin_val,
                        "Iin": iin_val,
                        "W": w_val
                    }
                }
                msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                info = client.publish(TOPIC, msg, qos=0, retain=False)
                info.wait_for_publish(timeout=5)
                print(f"Enviado: {msg}")

                # Reset para esperar la siguiente serie
                vin_val, iin_val, w_val = None, None, None
            
                # 2. GESTIÓN DE HWINFO (VÍA ARCHIVO JSON)
                # Solo leemos si ha pasado el intervalo definido
                current_time = time.time()
                if current_time - last_hwinfo_time > HWINFO_INTERVAL:
                    hwinfo_fields = read_hwinfo_json(HWINFO_JSON_PATH)
                    
                    if hwinfo_fields:
                        payload_hwinfo = {
                            "measurement": "hwinfo_data", # NOMBRE DISTINTO AQUÍ
                            "tags": {"device": DEVICE[1]},
                            "fields": {
                                "ver": "1",
                                **hwinfo_fields
                            }
                        }

                    msg_hwinfo = json.dumps(payload_hwinfo, separators=(",", ":"), ensure_ascii=False)
                    info = client.publish(TOPIC, msg_hwinfo, qos=0, retain=False)
                    info.wait_for_publish(timeout=5)
                    print(f"Enviado: {msg_hwinfo}")

                    hwinfo_fields = None

            # Opcional: pequeña espera para no saturar CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Detenido por el usuario.")
    finally:
        ser.close()
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
