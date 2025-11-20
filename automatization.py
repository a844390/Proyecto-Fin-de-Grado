import time
import csv
from collections import deque
from datetime import datetime
import psutil
import itertools
import sys

# ----------------------------

# Configuration

# ----------------------------

CSV_FILE = r"C:\Users\Pedro\Desktop\hwinfo_log.csv"  # HWiNFO CSV
UPDATE_INTERVAL = 10  # seconds (How often to check CSV)
ROLLING_HISTORY = 500
AFFINITY_INTERVAL = 180  # seconds (3 minutes - How often to rotate affinity)
LOG_FILE = r"C:\Users\Pedro\Desktop\affinity_rotation.log"
wanted_labels = ["CPU Package Power [W]"]
SETTLING_READINGS = 3  # Number of readings to ignore after affinity change for power stabilization

rolling_log = deque(maxlen=ROLLING_HISTORY)
affinity_averages = {}
last_affinity_change = time.time()
original_affinity = None # Variable to store the original affinity
readings_since_change = 0 # Tracker for the settling period

# Redirect stdout to log file (everything except power readings will also go here)

class Logger:
    def __init__(self, logfile):
        self.terminal = sys.stdout
        self.log = open(logfile, "a", buffering=1)  # line-buffered

    def write(self, message):
        # Filter out the line containing the latest HWiNFO read (it contains 'Latest:')
        if "Latest:" not in message:  
            self.log.write(message)
        # Always print to the terminal
        self.terminal.write(message)

    def flush(self):
        self.log.flush()
        self.terminal.flush()

# Redirect stdout to our Logger
sys.stdout = Logger(LOG_FILE)

# ----------------------------

# Define P-core and E-core IDs

# ----------------------------

P_CORES = [0, 1, 6, 7, 8, 9, 18, 19]
E_CORES = [2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17]

# Generate unique representative combinations based only on the count (N_P, N_E).

affinity_combinations = []
# r_p: Number of P-cores to select (0 to max P-cores)
for r_p in range(0, len(P_CORES) + 1):  
    # r_e: Number of E-cores to select (0 to max E-cores)
    for r_e in range(0, len(E_CORES) + 1): 
        
        # SKIP the combination where BOTH counts are zero (no cores selected)
        if r_p == 0 and r_e == 0:
            continue
        
        # Use simple slice [:] to get the first r_p and r_e cores as the representative set
        p_subset = P_CORES[:r_p]
        e_subset = E_CORES[:r_e]
        
        combo = p_subset + e_subset
        affinity_combinations.append(combo)

# ----------------------------

# Affinity Combination Check

# ----------------------------

def print_affinity_summary(combos, p_cores_set):
    """Prints a table summarizing the number of P and E cores in each combination."""
    print("\n" + "="*50)
    print("AFFINITY COMBINATIONS SUMMARY")
    print(f"Total Unique Combinations to Test: {len(combos)}")
    print(f"P-Cores Available: {len(p_cores_set)}, E-Cores Available: {len(E_CORES)}")
    print("="*50)
    
    # Store unique (N_P, N_E) pairs for a cleaner table display
    summary_data = []
    
    for i, combo in enumerate(combos):
        p_count = sum(1 for core in combo if core in p_cores_set)
        e_count = len(combo) - p_count
        summary_data.append((p_count, e_count, combo))

    # Print the table header
    print(f"{'Index':<5} | {'P-Cores':<7} | {'E-Cores':<7} | {'Total':<5} | Combination (Representative)")
    print("-" * 50)
    
    # Print the data rows
    for i, (p, e, combo) in enumerate(summary_data):
        print(f"{i:<5} | {p:<7} | {e:<7} | {p+e:<5} | {combo}")

    print("="*50 + "\n")


print_affinity_summary(affinity_combinations, set(P_CORES))

# ----------------------------

# Select Prime95 process

# ----------------------------

def get_prime95_process():
    for p in psutil.process_iter(['name','pid']):
        if 'prime95' in p.info['name'].lower():
            print(f"Prime95 process identified. PID: {p.info['pid']}")
            return psutil.Process(p.info['pid'])
    print("Prime95 process not found.")
    return None

# ----------------------------

# CSV Reading Function

# ----------------------------

def read_csv_latest(file_path):
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            if len(rows) < 2:
                return None
            headers = rows[0]
            last_row = rows[-1]
            return dict(zip(headers, last_row))
    except Exception as e:
        # We don't want to fail here, as the main loop handles the error
        print(f"Error reading CSV: {e}") 
        return None

# ----------------------------

# Affinity Rotation Function

# ----------------------------

def rotate_affinity(proc, combos, index=[0]):
    global readings_since_change # Use global tracker for settling period
    combo = combos[index[0] % len(combos)]
    
    # Apply new affinity
    proc.cpu_affinity(combo)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CPU affinity changed to cores: {combo}")
    index[0] += 1
    
    # Reset the reading counter after a change
    readings_since_change = 0 
    return combo

# ----------------------------

# Main Loop

# ----------------------------

proc = get_prime95_process()
if not proc:
    exit()

# --- Store Original Affinity ---
try:
    original_affinity = proc.cpu_affinity()
    print(f"Original CPU affinity stored: {original_affinity}")
except psutil.AccessDenied:
    print("Warning: Could not read original CPU affinity. The process is likely not owned by the user.")
    original_affinity = None

print(f"Monitoring CSV {CSV_FILE} every {UPDATE_INTERVAL} seconds...")
current_affinity = rotate_affinity(proc, affinity_combinations)
last_affinity_change = time.time()

try:
    while True:
        now = time.time()
        
        # Check if it's time to rotate affinity
        if now - last_affinity_change >= AFFINITY_INTERVAL:
            current_affinity = rotate_affinity(proc, affinity_combinations)
            last_affinity_change = now

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        latest = read_csv_latest(CSV_FILE)
        
        if latest:
            # --- Robust Data Conversion Logic ---
            readings = {}
            valid_reading = True
            for label in wanted_labels:
                value_str = latest.get(label, '0')
                try:
                    readings[label] = float(value_str)
                except ValueError:
                    # Catch the non-numeric string error (e.g., header/descriptive row)
                    print(f"[{timestamp}] WARNING: Failed to convert '{label}' value '{value_str}' to float. Skipping average update.")
                    readings[label] = None 
                    valid_reading = False
                    
            # Check if we got a valid reading (i.e., not None)
            if valid_reading:
                readings["Timestamp"] = timestamp
                readings["Affinity_Cores"] = current_affinity
                rolling_log.append(readings)

                # --- SETTLING PERIOD LOGIC ---
                if readings_since_change < SETTLING_READINGS:
                    # Log that we are skipping this reading for the average calculation
                    print(f"[{timestamp}] Affinity {current_affinity} Latest: {readings[wanted_labels[0]]} W | Status: Settling ({readings_since_change + 1}/{SETTLING_READINGS})")
                    readings_since_change += 1
                else:
                    # Only collect and average data after the settling period
                    avg_key = f"Cores_{'_'.join(map(str,current_affinity))}"
                    if avg_key not in affinity_averages:
                        affinity_averages[avg_key] = []
                    
                    # Add reading to the average
                    affinity_averages[avg_key].append(readings[wanted_labels[0]])
                    average = sum(affinity_averages[avg_key]) / len(affinity_averages[avg_key])
                    
                    # This line includes 'Latest:', so it will NOT be written to the log file by Logger.
                    print(f"[{timestamp}] Affinity {current_affinity} Latest: {readings[wanted_labels[0]]} W | Average: {average:.2f} W")
                    readings_since_change += 1 # Increment counter even after settling
        else:
            print(f"[{timestamp}] No data yet in CSV.")

        time.sleep(UPDATE_INTERVAL)

except KeyboardInterrupt:
    print("\nExiting...")
    
    ## --- Log Final Averages ---
    print("\n--- Final Affinity Average Power (W) ---")
    for avg_key, readings_list in affinity_averages.items():
        if readings_list:
            final_average = sum(readings_list) / len(readings_list)
            # This print statement will be written to the log file since it doesn't contain 'Latest:'
            print(f"{avg_key.replace('Cores_', 'Cores: ')} | Avg Power: {final_average:.2f} W")
    print("--------------------------------------\n")
    
    # --- Restore Original Affinity on Exit ---
    if original_affinity and proc.is_running():
        try:
            proc.cpu_affinity(original_affinity)
            print(f"Restored original CPU affinity: {original_affinity}")
        except psutil.AccessDenied:
            print("Error: Could not restore original CPU affinity due to permission issues.")
        except psutil.NoSuchProcess:
            print("Warning: Prime95 process is no longer running, affinity could not be restored.")
    elif original_affinity is not None:
         print("Warning: Prime95 process is no longer running, affinity could not be restored.")
    # ----------------------------------------