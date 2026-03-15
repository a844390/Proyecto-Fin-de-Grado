#!/usr/bin/env python3
# vatimetro.py
#
# Lee datos de un dispositivo por serie y los almacena en CSV.
# V → Vin, A → Iin, W → W
# Por defecto usa COM4, pero se puede pasar otro puerto como argumento.

import csv
import re
import time
import argparse
import random
from datetime import datetime

# Intenta importar serial, pero es opcional en modo simulación
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# Serial settings
DEFAULT_SERIAL_PORT = "COM4"
BAUDRATE = 9600
TIMEOUT = 1  # segundos
DEFAULT_CSV_FILE = "vatimetro_data.csv"

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


def generate_simulated_serial_line():
    """Genera una línea serie simulada realista"""
    base_vin = 230.0
    base_iin = 2.5
    base_w = 550.0
    
    vin = base_vin + random.uniform(-11.5, 11.5)
    iin = base_iin + random.uniform(-0.125, 0.125)
    w = base_w + random.uniform(-27.5, 27.5)
    
    # Retorna líneas alternadas (V, A, W)
    cycle = getattr(generate_simulated_serial_line, 'cycle', 0)
    generate_simulated_serial_line.cycle = (cycle + 1) % 3
    
    if cycle == 0:
        return f"V  0N  {vin:.2f}"
    elif cycle == 1:
        return f"A  0N  {iin:.3f}"
    else:
        return f"W  0N  {w:.2f}"



def main():
    # Argumentos
    parser = argparse.ArgumentParser(description="Leer serie y guardar en CSV")
    parser.add_argument(
        "-p", "--port", default=DEFAULT_SERIAL_PORT,
        help=f"Puerto serie (default: {DEFAULT_SERIAL_PORT})"
    )
    parser.add_argument(
        "-f", "--file", default=DEFAULT_CSV_FILE,
        help=f"Archivo CSV (default: {DEFAULT_CSV_FILE})"
    )
    parser.add_argument(
        "-s", "--simulate", action="store_true",
        help="Modo simulación: genera datos realistas en lugar de leer serie"
    )
    parser.add_argument(
        "-n", "--num-samples", type=int, default=0,
        help="Número de muestras en modo simulación (0 = infinito)"
    )
    args = parser.parse_args()
    serial_port = args.port
    csv_file = args.file
    simulate_mode = args.simulate
    num_samples = args.num_samples

    # Inicializa archivo CSV
    csv_f = open(csv_file, 'a', newline='', encoding='utf-8')
    csv_writer = csv.DictWriter(csv_f, fieldnames=['timestamp', 'Vin', 'Iin', 'W'])
    
    # Escribe encabezados si el archivo está vacío
    if csv_f.tell() == 0:
        csv_writer.writeheader()

    if simulate_mode:
        print(f"[MODO SIMULACIÓN] Generando datos realistas...")
        print(f"Guardando en: {csv_file}")
        if num_samples > 0:
            print(f"Objetivo: {num_samples} muestras")
        else:
            print("Objetivo: infinito (Presiona Ctrl+C para detener)")
        print()
    else:
        # Verifica que serial esté disponible
        if not SERIAL_AVAILABLE:
            print(f"❌ Error: módulo 'pyserial' no está instalado")
            print(f"💡 Sugerencias:")
            print(f"   - Instala: pip install pyserial")
            print(f"   - O usa modo simulación: python vatimetro.py --simulate")
            csv_f.close()
            return
            
        # Inicializa Serial
        try:
            ser = serial.Serial(serial_port, BAUDRATE, timeout=TIMEOUT)
            print(f"Leyendo datos de {serial_port} y guardando en {csv_file}...")
        except serial.SerialException as e:
            print(f"❌ Error al abrir puerto {serial_port}: {e}")
            print(f"💡 Sugerencia: ejecuta con --simulate para usar modo simulación")
            csv_f.close()
            return

    vin_val, iin_val, w_val = None, None, None
    sample_count = 0
    
    try:
        while True:
            if simulate_mode:
                line = generate_simulated_serial_line()
                time.sleep(0.05)  # Simula lectura de serie
            else:
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

            # Si tenemos un conjunto completo, lo guardamos
            if vin_val is not None and iin_val is not None and w_val is not None:
                row = {
                    'timestamp': datetime.now().isoformat(),
                    'Vin': vin_val,
                    'Iin': iin_val,
                    'W': w_val
                }
                csv_writer.writerow(row)
                csv_f.flush()
                sample_count += 1
                status = f"[{sample_count:3d}]" if simulate_mode else ""
                print(f"{status} Guardado: Vin={vin_val:7.2f}V | Iin={iin_val:6.3f}A | W={w_val:7.2f}W")

                # Reset para esperar la siguiente serie
                vin_val, iin_val, w_val = None, None, None
                
                # Control de muestras en simulación
                if simulate_mode and num_samples > 0 and sample_count >= num_samples:
                    print(f"\n✓ Simulación completada: {sample_count} muestras generadas")
                    break
            # Opcional: pequeña espera para no saturar CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n\nDetenido por el usuario después de {sample_count} muestras.")
    finally:
        if not simulate_mode:
            ser.close()
        csv_f.close()
        print(f"✓ Datos guardados en: {csv_file}")

if __name__ == "__main__":
    main()
