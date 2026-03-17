import pandas as pd
import re

# Cargar CSV
df = pd.read_csv("librehwmonitor_csv_to_mqtt_todos.csv")

# Contador global de cores
core_counter = 0

# Función para renumerar cores de 0 a 19 y eliminar p_ / e_ 
def normalize_cores(sensor):
    global core_counter
    # Detectar cores
    if any(x in sensor for x in ['_core_', '_p_core_', '_e_core_']):
        # Reemplazar cualquier prefijo de P- o E-core por 'core_'
        new_sensor = re.sub(r'^(p_|e_)?core_|_p_core_|_e_core_', 'core_', sensor)
        core_counter += 1
        if core_counter > 19:  # limitar máximo 19
            core_counter = 19
        return new_sensor
    return sensor

# Aplicar la función
df['sensor_json'] = df['sensor_json'].apply(normalize_cores)

# Guardar CSV resultante
df.to_csv("sensores_normalizados.csv", index=False)
print("CSV normalizado guardado como sensores_normalizados.csv")