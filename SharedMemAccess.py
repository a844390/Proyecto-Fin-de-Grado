import ctypes
import time

# ---- CONFIG ----
SHMEM_NAME = "Global\\HWiNFO_SENS_SM2"
HWINFO_SIGNATURE = 0x53534D32  # Example signature, adjust if needed
READ_INTERVAL = 2  # seconds

# ---- HWiNFO Structures ----
HWI_STRING_LEN2 = 128
HWI_UNIT_STRING_LEN = 16

class SmSensorsReadingElement(ctypes.Structure):
    _fields_ = [
        ("Type", ctypes.c_uint),
        ("Idx", ctypes.c_uint),
        ("Id", ctypes.c_uint),
        ("LabelOrig", ctypes.c_char * HWI_STRING_LEN2),
        ("LabelUser", ctypes.c_char * HWI_STRING_LEN2),
        ("Unit", ctypes.c_char * HWI_UNIT_STRING_LEN),
        ("Value", ctypes.c_double),
        ("ValueMin", ctypes.c_double),
        ("ValueMax", ctypes.c_double),
        ("ValueAvg", ctypes.c_double),
    ]

class SmSensorsSensorElement(ctypes.Structure):
    _fields_ = [
        ("Id", ctypes.c_uint),
        ("Instance", ctypes.c_uint),
        ("LabelOrig", ctypes.c_char * HWI_STRING_LEN2),
        ("LabelUser", ctypes.c_char * HWI_STRING_LEN2),
    ]

class SmSensorsSharedMem2(ctypes.Structure):
    _fields_ = [
        ("Signature", ctypes.c_uint),
        ("Version", ctypes.c_uint),
        ("Revision", ctypes.c_uint),
        ("PollTime", ctypes.c_int64),
        ("SensorSection_Offset", ctypes.c_uint),
        ("SensorSection_SizeOfElement", ctypes.c_uint),
        ("SensorSection_NumElements", ctypes.c_uint),
        ("ReadingSection_Offset", ctypes.c_uint),
        ("ReadingSection_SizeOfElement", ctypes.c_uint),
        ("ReadingElements_NumElements", ctypes.c_uint),
    ]

# ---- WINDOWS API ----
kernel32 = ctypes.windll.kernel32
FILE_MAP_READ = 0x0004

def open_shared_memory():
    h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHMEM_NAME)
    if not h_map:
        raise RuntimeError("Cannot open HWiNFO shared memory. Make sure HWiNFO is running with shared memory enabled.")
    ptr = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, 0)
    kernel32.CloseHandle(h_map)
    return ptr

def read_struct(ptr, struct_type, offset=0):
    addr = ptr + offset
    return struct_type.from_address(addr)

# ---- SENSOR READING ----
class SensorReading:
    def __init__(self, reading, sensor):
        self.Id = reading.Id
        self.Index = reading.Idx
        self.Type = reading.Type
        self.LabelOrig = reading.LabelOrig.decode(errors="ignore").rstrip("\x00")
        self.LabelUser = reading.LabelUser.decode(errors="ignore").rstrip("\x00")
        self.Unit = reading.Unit.decode(errors="ignore").rstrip("\x00")
        self.Value = reading.Value
        self.ValueMin = reading.ValueMin
        self.ValueMax = reading.ValueMax
        self.ValueAvg = reading.ValueAvg
        self.GroupId = sensor.Id
        self.GroupInstanceId = sensor.Instance
        self.GroupLabelUser = sensor.LabelUser.decode(errors="ignore").rstrip("\x00")
        self.GroupLabelOrig = sensor.LabelOrig.decode(errors="ignore").rstrip("\x00")

# ---- MAIN READ FUNCTION ----
def read_hwinfo_sensors():
    ptr = open_shared_memory()
    header = read_struct(ptr, SmSensorsSharedMem2)
    sensors = []
    readings = []

    sensor_base = ptr + header.SensorSection_Offset
    for i in range(header.SensorSection_NumElements):
        s = read_struct(sensor_base + i * header.SensorSection_SizeOfElement, SmSensorsSensorElement)
        sensors.append(s)

    reading_base = ptr + header.ReadingSection_Offset
    for i in range(header.ReadingElements_NumElements):
        r = read_struct(reading_base + i * header.ReadingSection_SizeOfElement, SmSensorsReadingElement)
        readings.append(r)

    result = [SensorReading(r, sensors[r.Idx]) for r in readings]
    return result

# ---- FILTERED LOOP ----
if __name__ == "__main__":
    try:
        sensor_data = read_hwinfo_sensors()
        print(f"Read {len(sensor_data)} sensor readings:")
        for s in sensor_data:
            print(f"{s.LabelUser}: {s.Value} {s.Unit} (Type {s.Type})")
    except Exception as e:
        print("Error reading HWiNFO shared memory:", e)

