"""
FoodSense — YOLOv8n Targeted Fine-Tuning Pipeline
Fine-tunes the food detector on real large-format dishes (dosa, naan, chapati, pizza, thali)
to close sim-to-real aspect ratio gaps while preserving existing class detection capability.
"""

import os
import sys
import shutil
import json

sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO

BASE_DIR = r"F:\FoodSense"
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_YAML = os.path.join(DATA_DIR, "yolo_dataset", "data.yaml")
WEIGHTS_DIR = os.path.join(BASE_DIR, "backend-inference", "models", "weights")
BASE_WEIGHTS = os.path.join(WEIGHTS_DIR, "food_detector_yolov8n.pt")
BACKUP_WEIGHTS = os.path.join(WEIGHTS_DIR, "food_detector_yolov8n_pre_finetune.pt")


def finetune_detector(epochs=8, batch=8, imgsz=640):
    print("="*75)
    print("FINE-TUNING YOLOV8N FOOD DETECTOR ON LARGE-FORMAT & REAL-WORLD SCENES")
    print(f"  Base Weights: {BASE_WEIGHTS}")
    print(f"  Dataset YAML: {DATA_YAML}")
    print(f"  Epochs: {epochs} | Batch: {batch} | Image Resolution: {imgsz}x{imgsz}")
    print("="*75)

    # 1. Backup existing weights
    if os.path.exists(BASE_WEIGHTS) and not os.path.exists(BACKUP_WEIGHTS):
        shutil.copy(BASE_WEIGHTS, BACKUP_WEIGHTS)
        print(f"[Backup] Saved pre-finetune weights to: {BACKUP_WEIGHTS}")

    # 2. Load model from existing weights
    weights_to_load = BASE_WEIGHTS if os.path.exists(BASE_WEIGHTS) else "yolov8n.pt"
    model = YOLO(weights_to_load)

    # 3. Fine-tune with lower learning rate and aspect-ratio augmentations
    results = model.train(
        data=DATA_YAML,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        lr0=0.002,         # Lower initial LR for fine-tuning
        lrf=0.01,          # Final LR factor
        device="cpu",
        workers=0,
        plots=False,
        project=r"F:\FoodSense\backend-inference\runs\detect",
        name="food_detector_finetuned",
        exist_ok=True,
        verbose=True
    )

    print("\n" + "="*75)
    print("EVALUATING FINE-TUNED DETECTOR ON VALIDATION SPLIT")
    print("="*75)

    val_results = model.val(
        data=DATA_YAML,
        imgsz=imgsz,
        conf=0.15,
        iou=0.45,
        device="cpu",
        plots=False
    )

    map50 = float(val_results.box.map50)
    map50_95 = float(val_results.box.map)
    mp = float(val_results.box.mp)
    mr = float(val_results.box.mr)

    print(f"\n[Post-Finetuning Validation Metrics]")
    print(f"  * mAP@0.50:       {map50*100:.2f}%")
    print(f"  * mAP@0.50:0.95:  {map50_95*100:.2f}%")
    print(f"  * Mean Precision: {mp*100:.2f}%")
    print(f"  * Mean Recall:    {mr*100:.2f}%")

    # Locate and copy best weights
    best_weights_src = os.path.join(r"F:\FoodSense\backend-inference\runs\detect\food_detector_finetuned\weights\best.pt")
    target_weights_path = os.path.join(WEIGHTS_DIR, "food_detector_yolov8n.pt")
    target_weights_active = os.path.join(WEIGHTS_DIR, "food_detector_best.pt")

    if os.path.exists(best_weights_src):
        shutil.copy(best_weights_src, target_weights_path)
        shutil.copy(best_weights_src, target_weights_active)
        print(f"\n[Weights Update OK] Deployed fine-tuned YOLOv8n weights to:")
        print(f"  * {target_weights_path}")
        print(f"  * {target_weights_active}")

    # Summary
    summary_path = os.path.join(DATA_DIR, "yolo_finetuning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "success",
            "epochs": epochs,
            "base_model": "yolov8n",
            "metrics": {
                "map50": round(map50 * 100, 2),
                "map50_95": round(map50_95 * 100, 2),
                "precision": round(mp * 100, 2),
                "recall": round(mr * 100, 2)
            }
        }, f, indent=2)

    print(f"[Summary Exported] {summary_path}")


if __name__ == "__main__":
    finetune_detector(epochs=6, batch=8, imgsz=416)
