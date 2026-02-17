import subprocess
import csv
import io

PCM_PATH = r"C:\Program Files (x86)\PCM\pcm.exe"

cmd = [
    PCM_PATH,
    "-csv"
]

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,           # decodes bytes → str
    bufsize=1            # line-buffered
)

csv_reader = None

try:
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue

        # PCM prints CSV header once — detect & initialize parser
        if csv_reader is None:
            header = next(csv.reader([line]))
            csv_reader = header
            print("CSV HEADER:", header)
            continue

        values = next(csv.reader([line]))
        record = dict(zip(csv_reader, values))

        # 👇 manipulate metrics here
        print(record)

except KeyboardInterrupt:
    print("Stopping PCM...")
finally:
    proc.terminate()
    proc.wait()
