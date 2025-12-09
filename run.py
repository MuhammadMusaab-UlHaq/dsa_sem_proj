import sys
import os
import traceback

# Add 'src' to the python path so imports work correctly
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
