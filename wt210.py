import serial
import time
import csv

# Configuración del puerto serial
puerto = 'COM4'
baudrate = 9600  # Ajusta según tu dispositivo
timeout = 1       # Tiempo de espera de lectura en segundos

# Archivo donde se guardarán las mediciones
archivo_csv = 'mediciones.csv'

# Abrimos el puerto serial
try:
    ser = serial.Serial(puerto, baudrate, timeout=timeout)
    print(f"Conectado a {puerto}")
except serial.SerialException as e:
    print(f"No se pudo abrir el puerto {puerto}: {e}")
    exit()

# Abrimos el archivo CSV en modo append
with open(archivo_csv, mode='a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'Medicion'])  # Encabezado CSV

    try:
        while True:
            if ser.in_waiting:  # Si hay datos disponibles
                linea = ser.readline().decode('utf-8').strip()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{timestamp} - {linea}")
                
                # Guardamos en CSV
                writer.writerow([timestamp, linea])
                file.flush()  # Asegura que se escriba en disco

                

    except KeyboardInterrupt:
        print("Lectura detenida por el usuario")
    finally:
        ser.close()
        print("Puerto serial cerrado")
