import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import glob
from PIL import Image
import torch
import numpy as np

sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pipeline.yolo_detector import YOLOMealDetector
from pipeline.cnn_classifier import IndianFoodClassifier

def diagnose():
    print("==========================================================================")
    print("RAW UNTHRESHOLDED INFERENCE DIAGNOSIS")
    print("==========================================================================")

    detector = YOLOMealDetector(confidence_threshold=0.01, iou_threshold=0.45)
    classifier = IndianFoodClassifier()

    print(f"\nModel 20-Class Vocabulary ({len(classifier.classes)} classes):")
    print(classifier.classes)

    # -------------------------------------------------------------------------
    # FAILURE 1: Chole Bhature raw diagnosis
    # -------------------------------------------------------------------------
    cb_images = glob.glob(r"F:\FoodSense\data\test_224\chole_bhature\*.jpg")[:3]
    print("\n-------------------------------------------------------------------------")
    print("FAILURE 1: Chole Bhature Raw Output Analysis")
    print("-------------------------------------------------------------------------")
    for i, img_path in enumerate(cb_images, 1):
        img = Image.open(img_path).convert("RGB")
        print(f"\n[Chole Bhature Sample #{i}]: {os.path.basename(img_path)} (Size: {img.size})")

        # 1. Raw YOLO detections at very low threshold
        yolo_res = detector.detect_items(img)
        print(f"  YOLO Detections count (conf >= 0.01): {len(yolo_res)}")
        for b in yolo_res:
            print(f"    - Box: {b['item_id']} | Conf: {b['confidence']} | BBox: {b['bbox_absolute']}")

        # 2. Raw CNN prediction on full image
        full_pred = classifier.predict_crop(img, top_k=5)
        print(f"  Full-image CNN Top-5:")
        for k in full_pred["top_k"]:
            print(f"    • {k['class_id']:15s}: {k['confidence']*100:5.2f}%")

        # 3. Raw CNN prediction on each YOLO crop
        for b in yolo_res:
            bbox = b["bbox_absolute"]
            crop = img.crop(bbox)
            crop_pred = classifier.predict_crop(crop, top_k=5)
            print(f"  Crop {b['item_id']} ({bbox}) CNN Top-5:")
            for k in crop_pred["top_k"]:
                print(f"    • {k['class_id']:15s}: {k['confidence']*100:5.2f}%")

    # -------------------------------------------------------------------------
    # FAILURE 2: Vada in Idli + Vada raw diagnosis
    # -------------------------------------------------------------------------
    print("\n-------------------------------------------------------------------------")
    print("FAILURE 2: Medu Vada / Vada Class Coverage Diagnosis")
    print("-------------------------------------------------------------------------")
    print("Checking if 'vada' or 'medu_vada' exists in 20-class vocabulary:")
    is_vada_in_classes = "medu_vada" in classifier.classes or "vada" in classifier.classes
    print(f"  -> Is 'vada'/'medu_vada' in 20 trained classes? {is_vada_in_classes}")

    # Check Idli sample
    idli_images = glob.glob(r"F:\FoodSense\data\test_224\idli\*.jpg")[:1]
    if idli_images:
        img = Image.open(idli_images[0]).convert("RGB")
        print(f"\n[Idli Sample]: {os.path.basename(idli_images[0])}")
        full_pred = classifier.predict_crop(img, top_k=5)
        print("  Full-image CNN Top-5:")
        for k in full_pred["top_k"]:
            print(f"    • {k['class_id']:15s}: {k['confidence']*100:5.2f}%")

if __name__ == "__main__":
    diagnose()
