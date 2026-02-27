#!/usr/bin/env python3
# pcm_csv_to_mqtt.py
#
# Lanza Intel PCM en modo CSV, extrae métricas seleccionadas y publica JSON por MQTT.

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import paho.mqtt.client as mqtt

# ====== MQTT SETTINGS (por defecto) ======
MQTT_HOST = "155.210.152.63"
MQTT_PORT = 8080
MQTT_USERNAME = "emoncms"
MQTT_PASSWORD = "paip2020"
MQTT_TOPIC = "cooler"
MQTT_DEVICE = "pcm"
MQTT_MEASUREMENT = "pcm"

# ====== PCM SETTINGS (fijos) ======
PCM_EXE = r"C:\Program Files (x86)\PCM\pcm.exe"
PCM_INTERVAL = 1
PCM_EXTRA_ARGS = ["-csv"]
MAPPING_FILE = "pcm_csv_to_mqtt_parametros_filtrada.csv"
PCM_STDERR_LOG_FILE = "pcm_stderr.log"

CORE0_COMPONENT = "Core0 (Socket 0)"
CORE_PATTERN = re.compile(r"^Core\d+ \(Socket \d+\)$")


def sanitize_token(text: str) -> str:
    token = text.strip().lower()
    token = re.sub(r"[^a-z0-9]+", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token


def json_key(component: str, metric: str) -> str:
    return f"{sanitize_token(component)}_{sanitize_token(metric)}"


def parse_csv_line(line: str) -> List[str]:
    return next(csv.reader([line]))


def iter_clean_lines(stream: Iterable[str]):
    for raw in stream:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        if line.startswith("Failed to seek in the pmem device"):
            continue
        if line.startswith("Driver Unloaded"):
            continue
        if line.startswith("Error:"):
            continue
        if line.startswith("INFO:"):
            continue
        if line.startswith("Failed to set acquisition mode"):
            continue
        if line.startswith("PS "):
            continue
        yield line


def load_mapping(mapping_path: Path) -> Tuple[List[Tuple[str, str]], List[str]]:
    selected_pairs: List[Tuple[str, str]] = []
    core_template_metrics: List[str] = []

    with mapping_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            component = (row.get("component") or "").strip()
            metric = (row.get("metric") or "").strip()
            if not component or not metric:
                continue
            if component == CORE0_COMPONENT:
                if metric not in core_template_metrics:
                    core_template_metrics.append(metric)
            else:
                pair = (component, metric)
                if pair not in selected_pairs:
                    selected_pairs.append(pair)

    return selected_pairs, core_template_metrics


def build_pair_index(components: List[str], metrics: List[str]) -> Dict[Tuple[str, str], int]:
    pair_to_index: Dict[Tuple[str, str], int] = {}
    for idx, (component, metric) in enumerate(zip(components, metrics)):
        key = (component.strip(), metric.strip())
        if key not in pair_to_index:
            pair_to_index[key] = idx
    return pair_to_index


def parse_float(value: str):
    txt = value.strip()
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(
        description="Lanza PCM, extrae métricas seleccionadas y publica JSON por MQTT."
    )
    ap.add_argument(
        "--json-log",
        action="store_true",
        help="Guarda cada payload JSON publicado en un archivo .jsonl (modo depuración)",
    )
    ap.add_argument(
        "--json-log-file",
        default="pcm_mqtt_debug.jsonl",
        help="Ruta del archivo de depuración JSONL (usado con --json-log)",
    )
    args = ap.parse_args()

    mapping_path = Path(MAPPING_FILE)
    if not mapping_path.exists():
        print(f"❌ No existe el mapping: {mapping_path}")
        sys.exit(1)

    fixed_pairs, core_template_metrics = load_mapping(mapping_path)
    if not core_template_metrics:
        print("⚠️ No se encontró plantilla Core0 en el mapping; no se expandirán métricas por core.")

    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    print(f"✅ MQTT conectado a {MQTT_HOST}:{MQTT_PORT} topic='{MQTT_TOPIC}'")

    cmd = [PCM_EXE, str(PCM_INTERVAL), *PCM_EXTRA_ARGS]
    print(f"▶ Ejecutando: {' '.join(cmd)}")

    debug_json_fh = None
    pcm_stderr_fh = Path(PCM_STDERR_LOG_FILE).open("a", encoding="utf-8", newline="")
    print(f"📝 Log stderr PCM: {PCM_STDERR_LOG_FILE}")
    if args.json_log:
        debug_path = Path(args.json_log_file)
        debug_json_fh = debug_path.open("a", encoding="utf-8", newline="")
        print(f"🧪 JSON debug activado: {debug_path}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=pcm_stderr_fh,
        text=True,
        encoding="utf-8",
        errors="ignore",
        bufsize=1,
    )

    components_header = None
    metrics_header = None
    pair_to_index: Dict[Tuple[str, str], int] = {}
    selected_pairs: List[Tuple[str, str]] = []
    missing_once = set()

    try:
        assert proc.stdout is not None
        for line in iter_clean_lines(proc.stdout):
            if components_header is None:
                if line.startswith("System,"):
                    components_header = parse_csv_line(line)
                continue

            if metrics_header is None:
                if not line.startswith("Date,"):
                    continue

                metrics_header = parse_csv_line(line)
                n = min(len(components_header), len(metrics_header))
                components_header = components_header[:n]
                metrics_header = metrics_header[:n]
                pair_to_index = build_pair_index(components_header, metrics_header)

                detected_cores = []
                for comp in components_header:
                    c = comp.strip()
                    if CORE_PATTERN.match(c) and c not in detected_cores:
                        detected_cores.append(c)

                selected_pairs = list(fixed_pairs)
                for core_name in detected_cores:
                    for metric in core_template_metrics:
                        pair = (core_name, metric)
                        if pair not in selected_pairs:
                            selected_pairs.append(pair)

                print(
                    f"✅ Cabeceras detectadas: {len(components_header)} columnas | "
                    f"cores: {len(detected_cores)} | pares seleccionados: {len(selected_pairs)}"
                )
                continue

            row = parse_csv_line(line)
            if len(row) < len(metrics_header):
                continue

            fields = {}
            for component, metric in selected_pairs:
                idx = pair_to_index.get((component, metric))
                if idx is None:
                    key = (component, metric)
                    if key not in missing_once:
                        missing_once.add(key)
                        print(f"⚠️ No encontrado en cabecera: {component} | {metric}")
                    continue

                val = parse_float(row[idx])
                if val is None:
                    continue

                fields[json_key(component, metric)] = val

            if not fields:
                continue

            mqtt_payload = {
                "measurement": MQTT_MEASUREMENT,
                "tags": {"device": MQTT_DEVICE},
                "fields": fields,
            }
            msg = json.dumps(mqtt_payload, separators=(",", ":"), ensure_ascii=False)
            info = client.publish(MQTT_TOPIC, msg, qos=0, retain=False)
            info.wait_for_publish(timeout=5)
            if debug_json_fh is not None:
                debug_json_fh.write(msg + "\n")
                debug_json_fh.flush()
            print(f"[MQTT] Enviado ({len(fields)} fields)")

    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            pass
        if debug_json_fh is not None:
            debug_json_fh.close()
        pcm_stderr_fh.close()
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
