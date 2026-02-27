#!/usr/bin/env python3
# sensors_serie_json_mqtt.py
#
# Lee JSON desde puerto serie y lo publica por MQTT.

import sys
import time
import json
import argparse
import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt

# ====== MQTT SETTINGS ======
MQTT_HOST = "155.210.152.63"
MQTT_PORT = 8080
MQTT_USERNAME = "emoncms"
MQTT_PASSWORD = "paip2020"
MQTT_TOPIC = "cooler"
MQTT_DEVICE = "sensors"
MQTT_MEASUREMENT = "sensors"


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


def main():
    ap = argparse.ArgumentParser(
        description="Bridge Serie -> MQTT. Lee JSON de serie y lo envía por MQTT."
    )
    ap.add_argument("port", nargs="?", help="Puerto COM (ej. COM6). Si no se pasa, se listarán y podrás elegir.")
    ap.add_argument("--baud", type=int, default=115200, help="Baudrate (por defecto 115200)")
    ap.add_argument("--prefix", default="HWiNFO:", help="Prefijo de línea para procesar (por defecto 'HWiNFO:')")
    args = ap.parse_args()

    print("ℹ️  Uso:")
    print("    python sensors_serie_json_mqtt.py COM6 --baud 115200 --prefix HWiNFO:\n")

    port = args.port or choose_port_interactive()
    print(f"✅ Puerto: {port}  |  Baud: {args.baud}  |  Prefijo: '{args.prefix}'\n")

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
            print(line)

            if not line.startswith(args.prefix):
                continue

            payload = line[len(args.prefix):].strip()
            if not payload:
                continue

            try:
                data = json.loads(payload)
                if not isinstance(data, dict):
                    continue
            except json.JSONDecodeError:
                print("⚠️  JSON inválido, ignorado.")
                continue

            mqtt_payload = {
                "measurement": MQTT_MEASUREMENT,
                "tags": {"device": MQTT_DEVICE},
                "fields": data,
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
