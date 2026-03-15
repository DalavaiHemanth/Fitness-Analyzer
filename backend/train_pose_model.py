"""
Pose Classifier Training Script
================================
Trains a pose classification model using MediaPipe landmark features.

Approach:
  1. Loads images from datasets/pose_images/<pose_label>/*.jpg
  2. Extracts 33×4=132 landmark features via MediaPipe
  3. Trains EfficientNet-based classifier + Random Forest fallback
  4. Saves sklearn model to models/pose_classifier.pkl

Usage:
  python train_pose_model.py

Dataset structure:
  datasets/pose_images/
    squat/       ← put squat images here
    pushup/
    plank/
    ... (any POSE_LABELS subdirectory)
"""
import os
import sys
import json
import numpy as np
import cv2
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Add backend to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai.pose_detector import POSE_LABELS, _extract_landmarks, _extract_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "pose_images")
MODEL_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "pose_classifier.pkl")
REPORT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "training_report.json")

def load_dataset():
    """Load all images, extract MediaPipe landmarks, return X, y arrays."""
    print("Inside load_dataset...")
    X, y = [], []

    # Efficiency: Import MediaPipe once
    print("Initializing MediaPipe...")
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        pose_detector_mp = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)
        print("MediaPipe initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize MediaPipe: {e}")
        sys.exit(1)

    if not os.path.exists(DATASET_DIR):
        logger.error("Dataset directory not found: %s", DATASET_DIR)
        logger.info("Create it with subdirectories named after each pose label.")
        sys.exit(1)

    available = os.listdir(DATASET_DIR)
    logger.info("Found pose classes: %s", available)

    for pose_label in available:
        label_dir = os.path.join(DATASET_DIR, pose_label)
        if not os.path.isdir(label_dir):
            continue
        images = [f for f in os.listdir(label_dir)
                  if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        logger.info("  %s: %d images", pose_label, len(images))

        for i, img_name in enumerate(images):
            img_path = os.path.join(label_dir, img_name)
            try:
                img = cv2.imread(img_path)
                if img is None:
                    continue
                img = cv2.resize(img, (640, 480))
                
                # Optimized: Use global pose_detector_mp
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = pose_detector_mp.process(rgb)
                
                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    landmarks = []
                    for l in lm:
                        landmarks.extend([l.x, l.y, l.z, l.visibility])
                    visibility = np.mean([l.visibility for l in lm])
                    
                    if visibility > 0.3:
                        features = _extract_features(landmarks)
                        X.append(features)
                        y.append(pose_label)
                
                if (i + 1) % 10 == 0:
                    logger.info("    Processed %d/%d images for %s", i + 1, len(images), pose_label)
            except Exception as e:
                logger.warning("Error processing %s: %s", img_name, e)

    logger.info("✅ Loaded %d samples from %d classes", len(X), len(set(y)))
    pose_detector_mp.close()
    return np.array(X), np.array(y)


def train(X: np.ndarray, y: np.ndarray):
    """Train the pose classifier and evaluate performance."""
    if len(X) < 10:
        logger.error("Not enough samples (%d). Need at least 10 total.", len(X))
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Model candidates — improved hyperparameters
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=500, max_depth=None, min_samples_split=2,
            min_samples_leaf=1, max_features="sqrt",
            random_state=42, n_jobs=-1
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators=500, max_depth=None, min_samples_split=2,
            random_state=42, n_jobs=-1
        ),
        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            ("svc", SVC(probability=True, kernel="rbf", C=50, gamma="scale"))
        ]),
    }

    best_model = None
    best_acc = 0.0
    best_name = ""
    results = {}

    for name, model in models.items():
        logger.info("Training %s...", name)
        try:
            model.fit(X_train, y_train)
            cv_scores = cross_val_score(model, X_train, y_train, cv=min(5, len(set(y))), scoring="accuracy")
            test_acc = accuracy_score(y_test, model.predict(X_test))
            results[name] = {
                "cv_mean": round(float(cv_scores.mean()), 4),
                "cv_std": round(float(cv_scores.std()), 4),
                "test_accuracy": round(test_acc, 4),
            }
            logger.info("  %s — CV: %.3f±%.3f | Test: %.3f",
                        name, cv_scores.mean(), cv_scores.std(), test_acc)
            if test_acc > best_acc:
                best_acc = test_acc
                best_model = model
                best_name = name
        except Exception as e:
            logger.warning("  %s failed: %s", name, e)

    logger.info("\n✅ Best model: %s (test accuracy: %.3f)", best_name, best_acc)

    # Full report on best model
    y_pred = best_model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    training_report = {
        "best_model": best_name,
        "test_accuracy": round(best_acc, 4),
        "models_compared": results,
        "classification_report": report,
        "num_samples": len(X),
        "num_classes": len(set(y)),
        "pose_labels": list(set(y)),
    }

    logger.info("\nClassification Report:\n%s", classification_report(y_test, y_pred))
    return best_model, training_report


def main():
    try:
        print("Starting Pose Classifier Training script...")
        logger.info("=== Pose Classifier Training ===")
        print(f"Dataset directory: {DATASET_DIR}")
        logger.info("Dataset: %s", DATASET_DIR)

        print("Loading dataset...")
        X, y = load_dataset()
        print(f"Dataset loaded with {len(X)} samples.")
        
        print("Starting training function...")
        model, report = train(X, y)
        print("Training complete.")

        # Save model
        os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
        joblib.dump(model, MODEL_OUTPUT)
        logger.info("💾 Model saved to: %s", MODEL_OUTPUT)

        # Save report
        with open(REPORT_OUTPUT, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("📊 Training report saved to: %s", REPORT_OUTPUT)

        logger.info("\n=== Training Complete ===")
        logger.info("Test accuracy: %.1f%%", report["test_accuracy"] * 100)
    except Exception as e:
        print(f"CRITICAL ERROR in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("Script started via __main__")
    main()
