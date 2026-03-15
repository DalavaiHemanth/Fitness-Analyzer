import sys
import os

try:
    print("Attempting to import train_pose_model...")
    import train_pose_model
    print("Import successful.")
    if __name__ == "__main__":
        print("Calling train_pose_model.main()...")
        train_pose_model.main()
except Exception as e:
    print(f"ERROR CAUGHT DURING IMPORT/EXECUTION: {e}")
    import traceback
    traceback.print_exc()
except SystemExit as e:
    print(f"SystemExit CAUGHT: {e.code}")
