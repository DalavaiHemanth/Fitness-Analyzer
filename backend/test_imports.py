import os
import sys

imports = [
    "os", "sys", "json", "numpy", "cv2", "joblib", "logging",
    "sklearn.ensemble", "sklearn.svm", "sklearn.model_selection",
    "sklearn.metrics", "sklearn.preprocessing", "sklearn.pipeline"
]

for imp in imports:
    try:
        print(f"Importing {imp}...")
        __import__(imp)
        print(f" {imp} OK")
    except Exception as e:
        print(f"FAILED to import {imp}: {e}")

print("Testing MediaPipe...")
try:
    import mediapipe as mp
    print("MediaPipe OK")
except Exception as e:
    print(f"FAILED to import mediapipe: {e}")
