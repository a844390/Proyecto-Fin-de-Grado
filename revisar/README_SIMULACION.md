# Simulación de Vatimetro

He modificado el script `vatimetro.py` para que puedas probarlo sin tener el vatimetro físico disponible.

## Modo Simulación Integrado

El script ahora tiene un **modo simulación** que genera datos realistas sin necesidad de puerto serial.

### Uso Básico

```bash
# Generar 10 muestras y guardar en CSV
python vatimetro.py --simulate -n 10 -f output.csv

# Generar datos infinitamente (Ctrl+C para detener)
python vatimetro.py --simulate
```

### Opciones Disponibles

| Flag | Descripción | Ejemplo |
|------|-------------|---------|
| `-s, --simulate` | Activar modo simulación | `--simulate` |
| `-n, --num-samples` | Número de muestras (0 = infinito) | `-n 20` |
| `-f, --file` | Archivo CSV de salida | `-f datos.csv` |
| `-p, --port` | Puerto serie (solo sin simulación) | `-p COM3` |

### Ejemplos

```bash
# 15 muestras en datos.csv
python vatimetro.py -s -n 15 -f datos.csv

# Modo infinito (hasta Ctrl+C)
python vatimetro.py -s

# Generar 100 muestras 
python vatimetro.py --simulate --num-samples 100
```

### Datos Generados

Los datos simulados incluyen valores realistas:
- **Vin**: 220-240V (voltaje) ±5%
- **Iin**: 2.5A (corriente) ±5%  
- **W**: 550W (potencia) ±5%

Cada fila tiene timestamp ISO8601 y es idéntica a los datos que generaría el vatimetro real.

## Script Simulador Independiente

También creé `vatimetro_simulator.py` con dos modos:

### Modo CSV (generar directamente)
```bash
python vatimetro_simulator.py -m csv -n 20 -i 0.5 -o output.csv
```

### Modo Serial (mostrar líneas serie como depuración)
```bash
python vatimetro_simulator.py -m serial -n 24 -i 0.2
```

## Ficheros Generados

La simulación crea archivos CSV con este formato:

```csv
timestamp,Vin,Iin,W
2026-03-11T10:15:48.385051,239.15,2.48,547.11
2026-03-11T10:15:48.838021,230.19,2.433,528.81
```

## Instalación de Dependencias (para puerto real)

Si luego quieres usar el vatimetro real:

```bash
pip install pyserial
```

En modo simulación, `pyserial` **no es necesario**.

## Comparación

| Aspecto | Sin Simulación | Con Simulación |
|--------|---|---|
| Requiere vatimetro físico | ✓ | ✗ |
| Requiere puerto COM disponible | ✓ | ✗ |
| Requiere pyserial | ✓ | ✗ |
| Datos realistas | ✓ | ✓ |
| Útil para testing | - | ✓ |

---

**Probado exitosamente**: 10 muestras generadas correctamente con timestamps y valores realistas en CSV.
