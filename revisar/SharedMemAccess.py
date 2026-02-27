import ctypes
import struct

# =========================
# Windows API
# =========================
kernel32 = ctypes.windll.kernel32
FILE_MAP_READ = 0x0004

# TIPOS CORRECTOS (CRÍTICO)
kernel32.OpenFileMappingW.restype = ctypes.c_void_p
kernel32.MapViewOfFile.restype   = ctypes.c_void_p
kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

SHM_NAMES = [
    "HWiNFO_SENS_SM2",
    "Global\\HWiNFO_SENS_SM2",
    "HWiNFO_Sensors",
    "Global\\HWiNFO_Sensors"
]

def read_hwinfo():
    hMapFile = None
    used_name = None

    # 1. Buscar mapping válido
    for name in SHM_NAMES:
        h = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
        if h:
            hMapFile = h
            used_name = name
            break

    if not hMapFile:
        print("❌ No se pudo abrir ningún Shared Memory de HWiNFO")
        return

    print(f"✅ Shared Memory abierto: {used_name}")

    # 2. Mapear memoria
    pBuf = kernel32.MapViewOfFile(
        hMapFile,
        FILE_MAP_READ,
        0, 0, 0
    )

    if not pBuf:
        print("❌ No se pudo mapear la vista de memoria")
        kernel32.CloseHandle(hMapFile)
        return

    try:
        # 3. Leer firma
        signature = ctypes.string_at(pBuf, 4).decode("ascii")

        if signature != "HWiS":
            print(f"❌ Firma inválida para SM2: {signature}")
            return

        print("✅ Firma SM2 válida (HWiS)")

        # 4. Leer cabecera básica (offsets oficiales)
        version    = struct.unpack_from("I", ctypes.string_at(pBuf + 8, 4))[0]
        revision   = struct.unpack_from("I", ctypes.string_at(pBuf + 12, 4))[0]
        numSensors = struct.unpack_from("I", ctypes.string_at(pBuf + 28, 4))[0]

        print("📊 Información HWiNFO")
        print(f"   Firma: {signature}")
        print(f"   Versión: {version}")
        print(f"   Revisión: {revision}")
        print(f"   Sensores detectados: {numSensors}")

    finally:
        kernel32.UnmapViewOfFile(pBuf)
        kernel32.CloseHandle(hMapFile)

if __name__ == "__main__":
    read_hwinfo()
