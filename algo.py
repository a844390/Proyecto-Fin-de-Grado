import ctypes

SHMEM_NAME = "Global\\HWiNFO_SENS_SM2"
FILE_MAP_READ = 0x0004
kernel32 = ctypes.windll.kernel32

h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, SHMEM_NAME)
if not h_map:
    print("HWiNFO shared memory NOT found.")
else:
    print("HWiNFO shared memory FOUND.")
    kernel32.CloseHandle(h_map)
