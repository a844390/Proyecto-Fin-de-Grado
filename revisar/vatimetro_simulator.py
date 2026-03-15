#!/usr/bin/env python3
# vatimetro_simulator.py
#
# Simula datos del vatimetro generando líneas serie realistas
# Genera datos con variaciones aleatorias para pruebas

import random
import time
import argparse
import re
import csv
from datetime import datetime

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


def generate_realistic_data():
    """Genera datos realistas del vatimetro con variaciones"""
    # Valores base realistas
    base_vin = 230.0  # Voltaje nominal
    base_iin = 2.5    # Corriente nominal
    base_w = 550.0    # Potencia nominal
    
    # Agregar variaciones aleatorias pequeñas (± 5%)
    vin = base_vin + random.uniform(-11.5, 11.5)
    iin = base_iin + random.uniform(-0.125, 0.125)
    w = base_w + random.uniform(-27.5, 27.5)
    
    return round(vin, 2), round(iin, 3), round(w, 2)


def generate_serial_line(value_type, value):
    """Genera una línea serie en el formato del vatimetro"""
    # Formato esperado del vatimetro: "V  0N  230.45" (similar para A y W)
    if value_type == 'V':
        return f"V  0N  {value:.2f}"
    elif value_type == 'A':
        return f"A  0N  {value:.3f}"
    elif value_type == 'W':
        return f"W  0N  {value:.2f}"


def simulate_to_csv(num_samples=10, output_file="vatimetro_data_simulated.csv", interval=0.5):
    """Simula datos del vatimetro y los guarda en CSV"""
    print(f"\n=== Simulando {num_samples} muestras ===")
    print(f"Intervalo: {interval}s, Archivo: {output_file}\n")
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['timestamp', 'Vin', 'Iin', 'W']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for i in range(num_samples):
            vin, iin, w = generate_realistic_data()
            
            row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Vin': vin,
                'Iin': iin,
                'W': w
            }
            
            writer.writerow(row)
            print(f"[{i+1:3d}/{num_samples}] Vin: {vin:7.2f}V | Iin: {iin:6.3f}A | W: {w:7.2f}W")
            
            if i < num_samples - 1:
                time.sleep(interval)
    
    print(f"\n✓ Datos guardados en: {output_file}")


def simulate_serial_lines(num_lines=30, interval=0.3):
    """Simula líneas serie individuales para probar el parsing"""
    print(f"\n=== Simulando {num_lines} líneas serie ===")
    print(f"Intervalo: {interval}s\n")
    
    vin_val, iin_val, w_val = None, None, None
    complete_samples = 0
    
    for i in range(num_lines):
        vin, iin, w = generate_realistic_data()
        
        # Alternar los tipos de línea para simular patrones reales
        line_type = ['V', 'A', 'W'][i % 3]
        
        if line_type == 'V':
            line = generate_serial_line('V', vin)
            vin_val = vin
        elif line_type == 'A':
            line = generate_serial_line('A', iin)
            iin_val = iin
        else:  # W
            line = generate_serial_line('W', w)
            w_val = w
        
        # Parsear la línea como lo haría el script real
        parsed_vin, parsed_iin, parsed_w = parse_line(line)
        
        print(f"[{i+1:3d}] Raw: {line:20s} | Parsed: V={parsed_vin} A={parsed_iin} W={parsed_w}")
        
        # Contar muestras completas
        if vin_val is not None and iin_val is not None and w_val is not None:
            complete_samples += 1
            print(f"      ✓ MUESTRA COMPLETA #{complete_samples}: Vin={vin_val:.2f}V, Iin={iin_val:.3f}A, W={w_val:.2f}W\n")
            vin_val, iin_val, w_val = None, None, None
        
        time.sleep(interval)
    
    print(f"\n✓ Simulación completada. Muestras completas generadas: {complete_samples}")


def main():
    parser = argparse.ArgumentParser(description="Simulador del vatimetro")
    parser.add_argument(
        "-m", "--mode", 
        choices=['csv', 'serial'], 
        default='csv',
        help="Modo de simulación: 'csv' (guardar directamente) o 'serial' (simular líneas serie)"
    )
    parser.add_argument(
        "-n", "--num", 
        type=int, 
        default=10,
        help="Número de muestras/líneas a generar"
    )
    parser.add_argument(
        "-i", "--interval", 
        type=float, 
        default=0.5,
        help="Intervalo entre muestras en segundos"
    )
    parser.add_argument(
        "-o", "--output", 
        default="vatimetro_data_simulated.csv",
        help="Archivo de salida CSV"
    )
    
    args = parser.parse_args()
    
    if args.mode == 'csv':
        simulate_to_csv(args.num, args.output, args.interval)
    else:
        simulate_serial_lines(args.num, args.interval)


if __name__ == "__main__":
    main()
