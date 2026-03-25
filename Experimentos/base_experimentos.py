"""
base_experimentos.py

Flujo base para ejecución de experimentos de rendimiento térmico/eléctrico.

Autor: [Tu nombre]
Fecha: [Fecha]

Descripción:
Este script implementa el flujo base para experimentos:
- Configuración hardware (V/F, ventilación)
- Estabilización
- Monitorización
- Ejecución de carga
- Recolección de datos
"""

import os
import time
import subprocess
import threading
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

# =========================
# CONFIGURACIÓN
# =========================

@dataclass
class ConfigExperimento:
    nombre: str
    duracion_test: int  # segundos
    perfil_xtu: str
    perfil_ventilacion: str
    metricas: List[str]
    afinidad_cores: Optional[List[int]] = None
    temperatura_objetivo: Optional[float] = None


# =========================
# LOGGING
# =========================

def configurar_logging(nombre_experimento: str):
    logging.basicConfig(
        filename=f"{nombre_experimento}.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


# =========================
# 1 → VOLTAJE Y FRECUENCIA
# =========================

def cargar_perfil_xtu(perfil_path: str):
    """
    Carga un perfil de Intel XTU.
    """
    logging.info(f"Cargando perfil XTU: {perfil_path}")

    # TODO: implementar llamada real
    # Ejemplo:
    # subprocess.run(["xtucli", "-import", perfil_path])

    pass


# =========================
# 2 → VENTILADORES Y BOMBA
# =========================

def aplicar_config_ventilacion(config_path: str):
    """
    Reemplaza la configuración de FanControl y reinicia el servicio.
    """
    logging.info(f"Aplicando configuración de ventilación: {config_path}")

    # TODO:
    # - copiar archivo config
    # - reiniciar FanControl

    pass


# =========================
# 3 → CONDICIONES INICIALES
# =========================

def esperar_estabilidad_temperatura(temp_objetivo: float, tolerancia: float = 1.0):
    """
    Espera hasta que la temperatura del agua sea estable.
    """
    logging.info("Esperando estabilidad térmica...")

    while True:
        temp_actual = leer_temperatura_agua()

        if abs(temp_actual - temp_objetivo) <= tolerancia:
            logging.info("Temperatura estable alcanzada")
            break

        time.sleep(5)


def leer_temperatura_agua() -> float:
    """
    Lee la temperatura del agua desde sensores.
    """
    # TODO: integrar HWinfo o sensor externo
    return 25.0


# =========================
# 4 → MÉTRICAS
# =========================

def inicializar_metricas(metricas: List[str]):
    """
    Prepara las fuentes de datos.
    """
    logging.info(f"Inicializando métricas: {metricas}")

    # TODO:
    # - HWinfo
    # - Intel PCM
    # - sensores externos

    pass


# =========================
# 5 → MONITORIZACIÓN
# =========================

class Monitor:
    def __init__(self, metricas: List[str]):
        self.metricas = metricas
        self.running = False

    def start(self):
        logging.info("Iniciando monitorización")
        self.running = True
        threading.Thread(target=self._loop).start()

    def _loop(self):
        while self.running:
            datos = self._leer_metricas()
            # TODO: almacenar en buffer o DB
            logging.debug(datos)
            time.sleep(1)

    def stop(self):
        logging.info("Deteniendo monitorización")
        self.running = False

    def _leer_metricas(self) -> Dict:
        # TODO: implementar
        return {m: 0 for m in self.metricas}


# =========================
# 6 → TEST DE CARGA
# =========================

def lanzar_test_carga(duracion: int) -> subprocess.Popen:
    """
    Lanza un test tipo Prime95.
    """
    logging.info("Lanzando test de carga")

    # TODO: sustituir por tu ejecutable real
    proceso = subprocess.Popen(["stress", "--cpu", "8"])

    time.sleep(duracion)

    return proceso


# =========================
# 7 → AFINIDAD
# =========================

def fijar_afinidad(proceso: subprocess.Popen, cores: List[int]):
    """
    Fija afinidad del proceso a determinados cores.
    """
    logging.info(f"Fijando afinidad: {cores}")

    # TODO: usar psutil o taskset
    # Ejemplo Linux:
    # subprocess.run(["taskset", "-p", mask, str(proceso.pid)])

    pass


# =========================
# 8 → LIMPIEZA
# =========================

def matar_proceso(proceso: subprocess.Popen):
    logging.info("Matando proceso de carga")

    proceso.terminate()

    try:
        proceso.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proceso.kill()


def limpiar():
    logging.info("Limpieza final del experimento")
    # TODO: cerrar procesos extra, sensores, etc.


# =========================
# 9 → RESULTADOS
# =========================

def generar_resumen():
    logging.info("Generando resumen de resultados")

    # TODO:
    # - medias
    # - máximos
    # - export CSV / JSON

    pass


# =========================
# FLUJO PRINCIPAL
# =========================

def ejecutar_experimento(config: ConfigExperimento):
    configurar_logging(config.nombre)

    logging.info("=== INICIO EXPERIMENTO ===")

    try:
        # 1
        cargar_perfil_xtu(config.perfil_xtu)

        # 2
        aplicar_config_ventilacion(config.perfil_ventilacion)

        # 3
        if config.temperatura_objetivo:
            esperar_estabilidad_temperatura(config.temperatura_objetivo)

        # 4
        inicializar_metricas(config.metricas)

        # 5
        monitor = Monitor(config.metricas)
        monitor.start()

        # 6
        proceso = lanzar_test_carga(config.duracion_test)

        # 7
        if config.afinidad_cores:
            fijar_afinidad(proceso, config.afinidad_cores)

        # Esperar fin del test
        proceso.wait()

        # 8
        monitor.stop()
        matar_proceso(proceso)

        # 9
        generar_resumen()

    except Exception as e:
        logging.error(f"Error en experimento: {e}")

    finally:
        limpiar()
        logging.info("=== FIN EXPERIMENTO ===")


# =========================
# EJEMPLO DE USO
# =========================

if __name__ == "__main__":
    config = ConfigExperimento(
        nombre="exp_001",
        duracion_test=60,
        perfil_xtu="perfiles/xtu_default.xml",
        perfil_ventilacion="perfiles/fans_alto.json",
        metricas=["cpu_temp", "cpu_power", "rpm"],
        afinidad_cores=[0, 1, 2, 3],
        temperatura_objetivo=30.0
    )

    ejecutar_experimento(config)