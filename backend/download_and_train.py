"""
Dataset Downloader & Model Trainer
==================================
This script downloads a small dataset of fitness pose images using DuckDuckGo search 
and then automatically trains the MediaPipe + RandomForest pose detector.
"""

import os
import time
import requests
import logging
from duckduckgo_search import DDGS

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# The poses we want to train
POSES = [
    "squat", "pushup", "plank", "deadlift", "bicep_curl", 
    "shoulder_press", "lunge", "jumping_jack", "warrior_pose", "downward_dog"
]

IMAGES_PER_POSE = 100
DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "pose_images")

def download_images():
    logger.info("Starting image download for %d poses...", len(POSES))
    os.makedirs(DATASET_DIR, exist_ok=True)
    
    with DDGS() as ddgs:
        for pose in POSES:
            pose_dir = os.path.join(DATASET_DIR, pose)
            os.makedirs(pose_dir, exist_ok=True)
            
            # Check if we already have enough images
            existing = len([f for f in os.listdir(pose_dir) if f.endswith('.jpg')])
            if existing >= IMAGES_PER_POSE:
                logger.info("✅ %s already has %d images, skipping download.", pose, existing)
                continue
                
            query = f"person doing {pose.replace('_', ' ')} exercise workout full body clear"
            logger.info("Downloading images for: %s", pose)
            
            try:
                results = list(ddgs.images(query, max_results=IMAGES_PER_POSE + 20))
                
                count = existing
                for i, res in enumerate(results):
                    if count >= IMAGES_PER_POSE:
                        break
                        
                    url = res.get('image')
                    if not url:
                        continue
                        
                    try:
                        # Fetch image
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            filepath = os.path.join(pose_dir, f"{pose}_{count}.jpg")
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            count += 1
                            time.sleep(0.5) # Be gentle to servers
                    except Exception as e:
                        logger.debug("Failed to download %s: %s", url, e)
                        
                logger.info("Successfully downloaded %d images for %s", count - existing, pose)
            except Exception as e:
                logger.error("Error searching for %s: %s", pose, e)

if __name__ == "__main__":
    download_images()
    
    logger.info("====================================")
    logger.info("Dataset downloaded! Starting training...")
    logger.info("====================================")
    
    # Run the training script
    import subprocess
    train_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_pose_model.py")
    subprocess.run(["python", train_script])
