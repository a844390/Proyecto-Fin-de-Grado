import win32gui
import win32con
import win32api
import time
import subprocess

# Abrir XTU
xtu_path = r"C:\Program Files\Intel\Intel(R) Extreme Tuning Utility\Client\XtuUiLauncher.exe"
subprocess.Popen(xtu_path)

time.sleep(5)

# Buscar ventana de XTU
hwnd = win32gui.FindWindow(None, "Intel® Extreme Tuning Utility")

if hwnd:
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(2)

    # Pulsar Ctrl + Shift + F1
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
    win32api.keybd_event(win32con.VK_F12, 0, 0, 0)

    time.sleep(0.5)

    # Soltar teclas
    win32api.keybd_event(win32con.VK_F1, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

else:
    print("No se encontró la ventana de XTU")