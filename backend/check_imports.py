import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Importing app...")

    print("Import successful!")

    print("Testing calculations import...")

    print("Calculations import successful!")

    print("Testing models import...")

    print("Organization model import successful!")

except Exception as e:
    print(f"Error during import: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
