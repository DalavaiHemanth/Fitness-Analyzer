import os
import cv2
import sys
import numpy as np

# Add backend to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai.pose_detector import _extract_landmarks

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "pose_images")

def debug_one():
    img_path = os.path.join(DATASET_DIR, "squat", "squat_0.jpg")
    print(f"Opening {img_path}")
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to load image")
        return
    img = cv2.resize(img, (640, 480))
    print("Running _extract_landmarks...")
    landmarks, visibility = _extract_landmarks(img)
    print(f"Done. Landmarks found: {len(landmarks) > 0}, Visibility: {visibility}")

if __name__ == "__main__":
    debug_one()
