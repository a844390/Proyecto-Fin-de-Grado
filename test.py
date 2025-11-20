import subprocess
import psutil
import time
import os

# Path to your prime95.exe
PRIME95_PATH = r"C:\Users\Pedro\Desktop\prime95\prime95.exe"

def start_prime95():
    print("Starting Prime95 torture test...")
    # Launch prime95 in torture test mode
    # /t instructs prime95 to start the torture test automatically
    return subprocess.Popen([PRIME95_PATH, "-t"], creationflags=subprocess.CREATE_NEW_CONSOLE)

def stop_prime95():
    print("Stopping all prime95 processes...")
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and "prime95" in proc.info['name'].lower():
                proc.kill()
                print(f"Killed process: {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def main():
    prime95_proc = start_prime95()

    # Wait until user types "stop"
    while True:
        user_input = input("Type 'stop' to end torture test: ").strip().lower()
        if user_input == "stop":
            stop_prime95()
            break
        else:
            print("Unknown command. Type 'stop' to end.")

    print("Prime95 torture test ended.")

if __name__ == "__main__":
    main()
