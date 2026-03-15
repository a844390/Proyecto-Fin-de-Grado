#!/usr/bin/env python3
# app_vatimetro.py
#
# Interfaz visual que te da la opción de leer los datos del vatímetro y
# guardarlos en un csv, o sacarlos por pantallla.
# V → Vin, A → Iin, W → W
# Por defecto lee de COM4, pero se puede pasar otro puerto como argumento.

import serial
from serial.tools import list_ports
import csv
import argparse
import re
from datetime import datetime
import sys

# Variables Globales
DEFAULT_SERIAL_PORT = "COM5"
DEFAULT_CSV_FILE = "vatimetro_data.csv"
TIMEOUT = 1  # segundos
BAUDRATE = 9600

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

def list_available_ports():
    """Lista los puertos COM disponibles"""
    ports = list_ports.comports()
    return ports

def show_port_menu():
    """Muestra un menú para seleccionar puerto COM"""
    print("\n" + "="*50)
    print("PUERTOS DISPONIBLES:")
    print("="*50)
    
    ports = list_available_ports()
    
    if not ports:
        print("⚠ No se detectaron puertos COM disponibles")
        print("\nOpciones:")
        print("1. Introducir puerto manualmente (ej: COM5)")
        print("2. Salir")
        choice = input("\nSelecciona una opción (1 o 2): ").strip()
        
        if choice == "1":
            port = input("Introduce el puerto COM (ej: COM4): ").strip().upper()
            return port if port else DEFAULT_SERIAL_PORT
        else:
            return None
    else:
        for i, port in enumerate(ports, 1):
            print(f"{i}. {port.device} - {port.description}")
        
        print(f"\n{len(ports)+1}. Introducir puerto manualmente")
        print(f"{len(ports)+2}. Salir")
        
        try:
            choice = int(input(f"\nSelecciona un puerto (1-{len(ports)+2}): ").strip())
            
            if 1 <= choice <= len(ports):
                return ports[choice-1].device
            elif choice == len(ports) + 1:
                port = input("Introduce el puerto COM (ej: COM4): ").strip().upper()
                return port if port else DEFAULT_SERIAL_PORT
            else:
                return None
        except ValueError:
            print("Entrada inválida")
            return None

def show_main_menu():
    """Muestra el menú principal"""
    print("\n" + "="*50)
    print("INTERFAZ DEL VATÍMETRO")
    print("="*50)
    print("1. Leer datos en pantalla")
    print("2. Guardar datos en CSV")
    print("3. Cambiar puerto COM")
    print("4. Salir")
    
    return input("\nSelecciona una opción (1-4): ").strip()


# Lee datos del vatímetro desde el puerto serie

def read_vatimetro_data(port):
    """Lee datos del vatímetro desde el puerto serie especificado"""
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            print(f"\n✓ Conectado al vatímetro en {port}. Esperando datos...")
            print("(Presiona Ctrl+C para detener)\n")
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Datos recibidos: {line}")
                    yield line
    except serial.SerialException as e:
        print(f"\n✗ Error al conectar con el puerto {port}: {e}")
        print("Comprueba que el vatímetro está conectado correctamente.")
        return
    except KeyboardInterrupt:
        print("\n\nLectura interrumpida por el usuario.")
        return



#generar interfaz visual con opciones para guardar en csv o mostrar en pantalla
def main():
    parser = argparse.ArgumentParser(description="Interfaz para leer datos del vatímetro")
    parser.add_argument("--port", default=None, help="Puerto serie del vatímetro (default: seleccionar interactivamente)")
    parser.add_argument("--csv", action="store_true", help="Guardar datos en CSV en lugar de mostrar en pantalla")
    args = parser.parse_args()

    current_port = args.port or DEFAULT_SERIAL_PORT

    while True:
        # Si se especificó --csv en argumentos, ejecutar modo CSV una vez
        if args.csv:
            print(f"\nGuardando datos en {DEFAULT_CSV_FILE}...")
            with open(DEFAULT_CSV_FILE, mode='w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Vin (V)", "Iin (A)", "W (W)"])
                try:
                    for line in read_vatimetro_data(current_port):
                        vin, iin, w = parse_line(line)
                        if vin is not None or iin is not None or w is not None:
                            timestamp = datetime.now().isoformat()
                            writer.writerow([timestamp, vin, iin, w])
                            print(f"{timestamp} - Vin: {vin} V, Iin: {iin} A, W: {w} W")
                except KeyboardInterrupt:
                    pass
            return
        
        # Menú interactivo
        choice = show_main_menu()
        
        if choice == "1":
            # Leer datos en pantalla
            print("\nMostrando datos en pantalla...")
            try:
                for line in read_vatimetro_data(current_port):
                    vin, iin, w = parse_line(line)
                    if vin is not None or iin is not None or w is not None:
                        timestamp = datetime.now().isoformat()
                        print(f"{timestamp} - Vin: {vin} V, Iin: {iin} A, W: {w} W")
            except KeyboardInterrupt:
                pass
                
        elif choice == "2":
            # Guardar en CSV
            print(f"\nGuardando datos en {DEFAULT_CSV_FILE}...")
            with open(DEFAULT_CSV_FILE, mode='w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Vin (V)", "Iin (A)", "W (W)"])
                try:
                    for line in read_vatimetro_data(current_port):
                        vin, iin, w = parse_line(line)
                        if vin is not None or iin is not None or w is not None:
                            timestamp = datetime.now().isoformat()
                            writer.writerow([timestamp, vin, iin, w])
                            print(f"{timestamp} - Vin: {vin} V, Iin: {iin} A, W: {w} W")
                except KeyboardInterrupt:
                    pass
                    
        elif choice == "3":
            # Cambiar puerto COM
            new_port = show_port_menu()
            if new_port:
                current_port = new_port
                print(f"✓ Puerto cambiado a: {current_port}")
            else:
                print("Operación cancelada")
                
        elif choice == "4":
            # Salir
            print("\n¡Hasta luego!")
            sys.exit(0)
        else:
            print("Opción inválida")

if __name__ == "__main__":
    main()