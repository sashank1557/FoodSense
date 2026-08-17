"""
FoodSense — YOLO Detection Recall Diagnostic Script (Step 1)
Evaluates YOLOv8n detector across ultra-low confidence thresholds (0.01 - 0.25)
to diagnose threshold filtering vs model blind spots on large dishes like masala_dosa.
"""

import os
import sys
import glob
import json
from PIL import Image

sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(CURRENT_DIR, "models", "weights", "food_detector_yolov8n.pt")

def diagnose_recall():
    print("="*75)
    print("YOLO RECALL DIAGNOSTIC: TESTING THRESHOLD SENSITIVITY & BLIND SPOTS")
    print("="*75)

    if not os.path.exists(WEIGHTS_PATH):
        print(f"Error: Weights not found at {WEIGHTS_PATH}")
        return

    model = YOLO(WEIGHTS_PATH)

    # Test on single-item dosa images and val meals
    dosa_imgs = glob.glob(r"F:\FoodSense\data\test_224\masala_dosa\*.jpg")[:5]
    meal_imgs = glob.glob(r"F:\FoodSense\data\yolo_dataset\images\val\*.jpg")[:3]

    test_images = dosa_imgs + meal_imgs
    thresholds = [0.25, 0.15, 0.08, 0.04, 0.01]

    for img_path in test_images:
        img_name = os.path.basename(img_path)
        img = Image.open(img_path)
        w, h = img.size
        print(f"\n--- Testing Image: {img_name} ({w}x{h}) ---")

        for conf in thresholds:
            results = model.predict(img, conf=conf, iou=0.45, device="cpu", verbose=False)[0]
            boxes = results.boxes
            count = len(boxes)
            confidences = [round(float(b.conf[0]), 3) for b in boxes]
            boxes_coords = [[int(c) for c in b.xyxy[0].cpu().numpy()] for b in boxes]
            print(f"  Threshold {conf:.2f} -> Detected {count} boxes | Confs: {confidences} | Bboxes: {boxes_coords[:2]}")

if __name__ == "__main__":
    diagnose_recall()
