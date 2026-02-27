import subprocess

def find_pid_by_name(name):
    """
    Returns the first PID whose process name contains 'name'.
    Case-insensitive. Works without external libraries.
    """

    try:
        # Run tasklist command
        output = subprocess.check_output("tasklist", shell=True, text=True)
    except Exception as e:
        print("Error running tasklist:", e)
        return None

    name = name.lower()

    for line in output.splitlines():
        if name in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                # Second column is PID in tasklist output
                pid_str = parts[1]

                # Validate it's numeric
                if pid_str.isdigit():
                    return int(pid_str)

    return None
