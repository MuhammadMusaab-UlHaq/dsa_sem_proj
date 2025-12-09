import datetime
import os

HISTORY_FILE = "history.txt"

def _get_history_path():
    """Helper to get the full path to history.txt in the outputs folder."""
    # Go up two levels from 'src' to get to Project Root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "outputs")
    
    # Create the outputs directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    return os.path.join(output_dir, HISTORY_FILE)

def log_trip(start_name, end_name, mode, time_min):
    """Appends search details + timestamp to history.txt in outputs/"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {start_name} -> {end_name} | Mode: {mode} | Time: {time_min:.1f} min\n"
    
    file_path = _get_history_path()

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(entry)
        
def get_history(limit=10):
    """Read and return the last N trips from history."""
    file_path = _get_history_path()

    if not os.path.exists(file_path):
        return ["No history found."]

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    return lines[-limit:] if lines else ["History is empty."]


def clear_history():
    """Clear all trip history."""
    file_path = _get_history_path()
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def get_frequent_destinations(top_n=5):
    """Analyze history to find most frequent destinations."""
    file_path = _get_history_path()
    if not os.path.exists(file_path):
        return []
    
    destinations = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                # Parse: [timestamp] start -> end | Mode: x | Time: y min
                parts = line.split(" -> ")
                if len(parts) >= 2:
                    dest = parts[1].split(" | ")[0].strip()
                    destinations[dest] = destinations.get(dest, 0) + 1
            except:
                continue
    
    # Sort by frequency
    sorted_dests = sorted(destinations.items(), key=lambda x: x[1], reverse=True)
    return sorted_dests[:top_n]