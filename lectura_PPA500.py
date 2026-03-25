import serial
import time
from datetime import datetime

# Configuración del puerto serie
ser = serial.Serial('COM7', 38400, timeout=0.5)

def enviar(cmd, delay=0.1):
    """Envía un comando al vatímetro y espera un pequeño delay."""
    ser.write((cmd + '\r').encode())
    time.sleep(delay)

def configurar_multil_newloc():
    """Configura MULTIL """
    print("Configurando MULTIL ")

    enviar("*CLS")          # limpia estados anteriores
    enviar("MULTIL,0")      # activa MULTIL

    # Configuración de canales
    enviar("MULTIL,1,1,1")   # Frecuencia
    enviar("MULTIL,2,1,2")   # Vatios
    enviar("MULTIL,3,1,50")  # Voltaje RMS
    enviar("MULTIL,4,1,51")  # Corriente RMS

#    enviar("NEWLOC,1")       # sincroniza la transmisión
#    enviar("MULTIL?")        # dispara la primera lectura para iniciar flujo

    print("Configuración completada\n")

def leer_multil():
    """Lee una línea de MULTIL desde el vatímetro."""
    ser.reset_input_buffer()
    ser.write(b"MULTIL?\r")
#    ser.write(b"NEWLOC;MULTIL?\r")
    return ser.readline().decode(errors='ignore').strip()

try:
    configurar_multil_newloc()

    while True:
        data = leer_multil()

        if data:
            try:
                valores = [float(x) for x in data.split(',')]

                if len(valores) == 4:
                    F, W, V, I = valores  # orden correcto
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # milisegundos
                    print(f"{timestamp} | {F:6.2f} Hz | {W:8.2f} W | {V:7.2f} V | {I:7.4f} A")
                else:
                    print("Formato inesperado:", data)

            except ValueError:
                print("Error parseando:", data)
        else:
            # No bloquear si no hay datos, simplemente espera
            time.sleep(0.05)

except KeyboardInterrupt:
    print("\nLectura detenida")

finally:
    ser.close()