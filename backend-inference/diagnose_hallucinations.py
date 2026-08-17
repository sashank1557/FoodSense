"""
Diagnostic script to demonstrate hallucination root cause and test real images.
Creates a composite plate of Chapati, Kadai Paneer, and Kaathi Roll (NO Dosa).
"""

import os
import sys
from PIL import Image

sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pipeline.yolo_detector import YOLOMealDetector
from pipeline.cnn_classifier import IndianFoodClassifier
from pipeline.knn_recommender import FoodSenseKNNRecommender
import json

def run_diagnostic():
    print("=================================================================")
    print("RUNNING HALLUCINATION DIAGNOSTIC ON REAL FOOD IMAGES")
    print("=================================================================")

    # 1. Load actual test images
    chapati_img_path = r"F:\FoodSense\data\test_224\chapati\test_00005.jpg"
    paneer_img_path = r"F:\FoodSense\data\test_224\kadai_paneer\test_00003.jpg" if os.path.exists(r"F:\FoodSense\data\test_224\kadai_paneer\test_00003.jpg") else r"F:\FoodSense\data\test_224\kadai_paneer\test_00010.jpg"
    roll_img_path = r"F:\FoodSense\data\test_224\kaathi_rolls\test_00001.jpg" if os.path.exists(r"F:\FoodSense\data\test_224\kaathi_rolls\test_00001.jpg") else r"F:\FoodSense\data\test_224\kaathi_rolls\test_00004.jpg"

    if not os.path.exists(paneer_img_path):
        import glob
        paneer_img_path = glob.glob(r"F:\FoodSense\data\test_224\kadai_paneer\*.jpg")[0]
    if not os.path.exists(roll_img_path):
        import glob
        roll_img_path = glob.glob(r"F:\FoodSense\data\test_224\kaathi_rolls\*.jpg")[0]

    img_chapati = Image.open(chapati_img_path).convert("RGB")
    img_paneer = Image.open(paneer_img_path).convert("RGB")
    img_roll = Image.open(roll_img_path).convert("RGB")

    # Create a 640x640 plate containing Chapati (left), Paneer (top-right), Roll (bottom-right)
    composite = Image.new("RGB", (640, 640), color=(235, 230, 220))
    composite.paste(img_chapati.resize((280, 280)), (30, 180))
    composite.paste(img_paneer.resize((260, 260)), (340, 40))
    composite.paste(img_roll.resize((260, 260)), (340, 340))

    composite_path = r"F:\FoodSense\data\diagnostic_thali_no_dosa.jpg"
    composite.save(composite_path)
    print(f"Saved diagnostic composite plate to: {composite_path}")
    print("Ground truth dishes on this plate: [chapati, kadai_paneer, kaathi_rolls] (NO dosa)")

    # 2. Test YOLO detector
    detector = YOLOMealDetector(confidence_threshold=0.035, iou_threshold=0.45)
    boxes = detector.detect_items(composite)
    print(f"\nYOLO Raw Detections Count: {len(boxes)}")
    for b in boxes:
        print(f"  - Box: {b.get('item_id')} | BBox: {b.get('bbox_absolute')} | Conf: {b.get('confidence')} | Tier: {b.get('confidence_tier')}")

    # 3. Test CNN classification on crops
    classifier = IndianFoodClassifier()
    print("\nClassifying each detected crop:")
    for b in boxes:
        bbox = b["bbox_absolute"]
        crop = composite.crop(bbox)
        pred = classifier.predict_crop(crop, top_k=3)
        print(f"  - Crop {b.get('item_id')}: Top-1: '{pred['class_id']}' (Conf: {pred['confidence']}) | Top-3: {pred['top_k']}")

if __name__ == "__main__":
    run_diagnostic()
