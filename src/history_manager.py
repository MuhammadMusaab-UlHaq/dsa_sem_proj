import datetime
import os

HISTORY_FILE = "history.txt"

def log_trip(start_name, end_name, mode, time_min):
    """Appends search details + timestamp to history.txt"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {start_name} -> {end_name} | Mode: {mode} | Time: {time_min:.1f} min\n"
    
    # Get the directory of the current script to ensure file is saved correctly
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, HISTORY_FILE)

    with open(file_path, "a") as f:
        f.write(entry)

def get_history():
    """Read and return the last 5 lines from the file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, HISTORY_FILE)

    if not os.path.exists(file_path):
        return ["No history found."]

    with open(file_path, "r") as f:
        lines = f.readlines()
        
    return lines[-5:] if lines else ["History is empty."]