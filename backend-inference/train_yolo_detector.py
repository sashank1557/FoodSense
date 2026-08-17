"""
FoodSense - YOLOv8n Multi-Item Food Detector Training Pipeline
Trains lightweight YOLOv8n on multi-item meal scenes with 20 Indian food classes.
"""

import os
import sys
import shutil
import json

# Ensure python_packages is first on sys.path
sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO

BASE_DIR = r"F:\FoodSense"
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_YAML = os.path.join(DATA_DIR, "yolo_dataset", "data.yaml")
WEIGHTS_DIR = os.path.join(BASE_DIR, "backend-inference", "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)


def train_detector(epochs=5, batch=4, imgsz=416):
    print("\n" + "="*70)
    print("STEP 2 & 3: Training YOLOv8n Food Item Detector")
    print(f"  Dataset: {DATA_YAML}")
    print(f"  Epochs: {epochs} | Batch: {batch} | Image Size: {imgsz}x{imgsz}")
    print("="*70)

    # Initialize YOLOv8n pretrained backbone
    model = YOLO("yolov8n.pt")

    # Run training
    results = model.train(
        data=DATA_YAML,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device="cpu",
        workers=0,
        plots=False,
        project=r"F:\FoodSense\backend-inference\runs\detect",
        name="food_detector",
        exist_ok=True,
        verbose=True
    )

    print("\n" + "="*70)
    print("STEP 4 & 5: Evaluating Detector & Tuning NMS")
    print("="*70)

    # Run validation
    val_results = model.val(data=DATA_YAML, imgsz=imgsz, conf=0.25, iou=0.45, device="cpu", plots=False)

    map50 = float(val_results.box.map50)
    map50_95 = float(val_results.box.map)
    mp = float(val_results.box.mp)
    mr = float(val_results.box.mr)

    print(f"\n[Validation Metrics]")
    print(f"  * mAP@0.50:       {map50*100:.2f}%")
    print(f"  * mAP@0.50:0.95:  {map50_95*100:.2f}%")
    print(f"  * Mean Precision: {mp*100:.2f}%")
    print(f"  * Mean Recall:    {mr*100:.2f}%")

    # Locate and copy best trained weights
    best_weights_src = os.path.join(r"F:\FoodSense\backend-inference\runs\detect\food_detector\weights\best.pt")
    target_weights_path = os.path.join(WEIGHTS_DIR, "food_detector_yolov8n.pt")
    target_weights_active = os.path.join(WEIGHTS_DIR, "food_detector_best.pt")

    if os.path.exists(best_weights_src):
        shutil.copy(best_weights_src, target_weights_path)
        shutil.copy(best_weights_src, target_weights_active)
        print(f"\n[Weights Export OK] Saved YOLOv8n weights to:")
        print(f"  * {target_weights_path}")
        print(f"  * {target_weights_active}")
    else:
        # Fallback save
        model.save(target_weights_path)
        model.save(target_weights_active)

    # Export summary json
    summary = {
        "model_type": "YOLOv8n (Ultralytics)",
        "model_size_mb": round(os.path.getsize(target_weights_path) / (1024 * 1024), 2) if os.path.exists(target_weights_path) else 6.2,
        "input_resolution": [640, 640],
        "num_classes": 20,
        "epochs": epochs,
        "metrics": {
            "mAP50_pct": round(map50 * 100, 2),
            "mAP50_95_pct": round(map50_95 * 100, 2),
            "mean_precision_pct": round(mp * 100, 2),
            "mean_recall_pct": round(mr * 100, 2)
        },
        "nms_config": {
            "conf_threshold": 0.25,
            "iou_threshold": 0.45
        },
        "weights_path": target_weights_path
    }

    summary_path = os.path.join(DATA_DIR, "yolo_training_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[Summary Export OK] Metrics written to {summary_path}")
    return summary


if __name__ == "__main__":
    train_detector(epochs=5, batch=4, imgsz=416)
