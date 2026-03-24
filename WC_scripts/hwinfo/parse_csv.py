#script que toma como input un .csv y añade una columna a la derecha con una x en cada fila 

import csv

def add_column_to_csv(input_file, output_file):
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    # Añadir una nueva columna con "x" en cada fila
    for row in rows:
        row.append('x')

    # Escribir el nuevo contenido en un nuevo archivo CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
# Ejemplo de uso
input_csv = 'C:\\Users\\chave\\Documents\\GitHub\\Proyecto-Fin-de-Grado\\WC_scripts\\hwinfo\\hwinfo_csv_to_mqtt_parametros.csv'  # Reemplaza con el nombre de tu archivo CSV
output_csv = 'C:\\Users\\chave\\Documents\\GitHub\\Proyecto-Fin-de-Grado\\WC_scripts\\hwinfo\\hwinfo_csv_to_mqtt.csv'  # Reemplaza con el nombre del archivo de salida
add_column_to_csv(input_csv, output_csv)
