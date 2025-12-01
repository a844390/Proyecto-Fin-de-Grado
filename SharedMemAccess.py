import ctypes
import sys

# ---- CONFIGURATION ----
SHMEM_NAME = "Global\\HWiNFO_SENS_SM2"
HWINFO_SIGNATURE = 0xDEADBEEF
MAX_DISPLAY_READINGS = 5  # Only show first 5 readings per sensor

# Example IDs (replace with actual IDs from your system)
SENSOR_ID = 0xF0002A00
SENSOR_INST = 0x0
READING_ID = 0x5000000

FILE_MAP_READ = 0x0004
kernel32 = ctypes.windll.kernel32

# ---- STRUCTS ----
class HWiNFO_READING(ctypes.Structure):
    _fields_ = [
        ("dwSensorID", ctypes.c_uint32),
        ("dwSensorInst", ctypes.c_uint32),
        ("dwReadingID", ctypes.c_uint32),
        ("Value", ctypes.c_double),
        ("ValueMin", ctypes.c_double),
        ("ValueMax", ctypes.c_double),
        ("dwReserved", ctypes.c_uint32 * 8)
    ]

class HWiNFO_SENSOR(ctypes.Structure):
    _fields_ = [
        ("dwSensorID", ctypes.c_uint32),
        ("dwSensorInst", ctypes.c_uint32),
        ("dwReadingIDCount", ctypes.c_uint32),
        ("_padding", ctypes.c_uint32)  # align to 16 bytes
    ]

class HWiNFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("Signature", ctypes.c_uint32),
        ("Version", ctypes.c_uint32),
        ("Revision", ctypes.c_uint32),
        ("PollingPeriod", ctypes.c_uint32),
        ("dwSensorCount", ctypes.c_uint32)
    ]

# ---- MEMORY FUNCTIONS ----
def open_hwinfo_shared_memory():
    """Open HWiNFO shared memory and return pointer with logging."""
    print("[LOG] Attempting to open HWiNFO shared memory...")
    print(f"[LOG] Memory Name: {SHMEM_NAME}")

    h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHMEM_NAME)
    if not h_map:
        print(f"[ERROR] HWiNFO shared memory '{SHMEM_NAME}' not found.")
        print("[ERROR] Make sure HWiNFO is running and 'Shared Memory Support' is enabled.")
        sys.exit(1)
    else:
        print(f"[LOG] OpenFileMappingW succeeded. Handle: {h_map}")

    ptr = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, 0)
    if not ptr:
        print("[ERROR] Failed to map view of HWiNFO shared memory.")
        kernel32.CloseHandle(h_map)
        sys.exit(1)
    else:
        print(f"[LOG] MapViewOfFile succeeded. Pointer: {hex(ptr)}")

    # Close the handle; mapping remains valid
    kernel32.CloseHandle(h_map)
    print("[LOG] Closed file mapping handle, pointer is still valid.")
    return ptr


def close_hwinfo_shared_memory(ptr):
    if ptr:
        kernel32.UnmapViewOfFile(ptr)

# ---- READ SPECIFIC VALUE ----
def read_hwinfo_value(sensor_id, sensor_inst, reading_id):
    print("[LOG] Opening HWiNFO shared memory...")
    ptr = open_hwinfo_shared_memory()
    try:
        print("[LOG] Reading header...")
        header = HWiNFO_HEADER.from_address(ptr)
        print(f"[LOG] Header Signature={hex(header.Signature)}, SensorCount={header.dwSensorCount}")

        if header.Signature != HWINFO_SIGNATURE:
            raise RuntimeError("HWiNFO shared memory signature mismatch.")

        sensor_ptr = ptr + ctypes.sizeof(HWiNFO_HEADER)
        print("[LOG] Starting to iterate over sensors...")
        for s_index in range(header.dwSensorCount):
            print(f"[LOG] Reading sensor {s_index} at address {hex(sensor_ptr)}")
            sensor = HWiNFO_SENSOR.from_address(sensor_ptr)
            print(f"[LOG] Sensor ID={hex(sensor.dwSensorID)}, Inst={sensor.dwSensorInst}, ReadingCount={sensor.dwReadingIDCount}")

            readings_ptr = sensor_ptr + ctypes.sizeof(HWiNFO_SENSOR)

            if sensor.dwSensorID == sensor_id and sensor.dwSensorInst == sensor_inst:
                print(f"[LOG] Target sensor matched. Iterating over {sensor.dwReadingIDCount} readings...")
                for r in range(sensor.dwReadingIDCount):
                    reading_addr = readings_ptr + r * ctypes.sizeof(HWiNFO_READING)
                    reading = HWiNFO_READING.from_address(reading_addr)
                    print(f"[LOG] Reading {r}: ID={hex(reading.dwReadingID)}, Value={reading.Value}")
                    if reading.dwReadingID == reading_id:
                        print("[LOG] Target reading matched. Returning value.")
                        return reading.Value

            # Move to next sensor
            sensor_ptr = readings_ptr + sensor.dwReadingIDCount * ctypes.sizeof(HWiNFO_READING)
            print(f"[LOG] Moving to next sensor at address {hex(sensor_ptr)}")

        print("[LOG] Target sensor/reading not found in shared memory.")
        return None
    finally:
        print("[LOG] Closing shared memory.")
        close_hwinfo_shared_memory(ptr)


# ---- LIST SENSORS ----
def list_hwinfo_sensors():
    """
    List sensors and a few readings per sensor to explore IDs.
    """
    print("[LOG] Opening HWiNFO shared memory...")
    ptr = open_hwinfo_shared_memory()
    header = HWiNFO_HEADER.from_address(ptr)
    print("Raw header:", [header.Signature, header.Version, header.Revision, header.PollingPeriod, header.dwSensorCount])

    try:
        header = HWiNFO_HEADER.from_address(ptr)
        if header.Signature != HWINFO_SIGNATURE:
            raise RuntimeError("HWiNFO shared memory signature mismatch.")

        print(f"Found {header.dwSensorCount} sensors:\n")

        sensor_ptr = ptr + ctypes.sizeof(HWiNFO_HEADER)
        for s_index in range(header.dwSensorCount):
            sensor = HWiNFO_SENSOR.from_address(sensor_ptr)
            print(f"Sensor {s_index}: ID={hex(sensor.dwSensorID)}, Inst={sensor.dwSensorInst}, Readings={sensor.dwReadingIDCount}")

            readings_ptr = sensor_ptr + ctypes.sizeof(HWiNFO_SENSOR)
            for r in range(min(sensor.dwReadingIDCount, MAX_DISPLAY_READINGS)):
                reading = HWiNFO_READING.from_address(readings_ptr + r * ctypes.sizeof(HWiNFO_READING))
                print(f"  Reading {r}: ID={hex(reading.dwReadingID)}, Value={reading.Value:.2f}, Min={reading.ValueMin:.2f}, Max={reading.ValueMax:.2f}")
            if sensor.dwReadingIDCount > MAX_DISPLAY_READINGS:
                print(f"  ... ({sensor.dwReadingIDCount - MAX_DISPLAY_READINGS} more readings)")
            print("-" * 50)

            # Move to next sensor
            sensor_ptr = readings_ptr + sensor.dwReadingIDCount * ctypes.sizeof(HWiNFO_READING)

    finally:
        close_hwinfo_shared_memory(ptr)

# ---- MAIN ----
if __name__ == "__main__":
    print("Listing sensors and first few readings:\n")
    try:
        list_hwinfo_sensors()
    except Exception as e:
        print(f"Error: {e}")
