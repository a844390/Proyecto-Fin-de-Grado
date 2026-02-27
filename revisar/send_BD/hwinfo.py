#!/usr/bin/env python3
# mqtt_serial.py
#
# Lee datos de HWiNFO y los envía a MQTT como JSON.


import json
import time
import paho.mqtt.client as mqtt

# MQTT settings
HOST = "155.210.152.63"
PORT = 8080
USERNAME = "emoncms"
PASSWORD = "paip2020"
TOPIC = "cooler"
DEVICE = "hwinfo"
#HWiNFO settings
HWINFO_JSON_PATH = "../hwinfo.json"



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
    
    # Inicializa MQTT
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(HOST, PORT, keepalive=30)
    client.loop_start()

    last_hwinfo_time = 0
    HWINFO_INTERVAL = 1  # Leer HWiNFO cada 2 segundos para no saturar
    try:
        while True:
            
            # 2. GESTIÓN DE HWINFO (VÍA ARCHIVO JSON)
            # Solo leemos si ha pasado el intervalo definido
            current_time = time.time()
            if current_time - last_hwinfo_time > HWINFO_INTERVAL:
                hwinfo_fields = read_hwinfo_json(HWINFO_JSON_PATH)

                if hwinfo_fields:
                    payload_hwinfo = {
                        "measurement": "hwinfo_data",
                        "tags": {"device": DEVICE},
                        "fields": {
                            "ver": "1",
                            **hwinfo_fields
                        }
                    }

                    msg_hwinfo = json.dumps(
                        payload_hwinfo,
                        separators=(",", ":"),
                        ensure_ascii=False
                    )

                    info = client.publish(TOPIC, msg_hwinfo, qos=0, retain=False)
                    info.wait_for_publish(timeout=5)
                    print(f"Enviado: {msg_hwinfo}")

                    last_hwinfo_time = current_time
                    hwinfo_fields = None
                else:
                    print("No se pudieron leer datos de HWiNFO")

                

            # Opcional: pequeña espera para no saturar CPU
            time.sleep(1)

    except KeyboardInterrupt:
        print("Detenido por el usuario.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
