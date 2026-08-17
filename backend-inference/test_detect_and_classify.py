"""
FoodSense — Multi-Item Meal Detection & Classification Pipeline
End-to-End Proof-of-Concept:
  1. YOLO locates individual food bounding boxes in meal photos
  2. MobileNetV2 CNN classifies each cropped bounding box at 224x224
  3. Nutrition database resolves per-item macros and meal aggregate totals
  4. Healthy alternatives are suggested for each identified item

Usage:
    python test_detect_and_classify.py path/to/meal_image.jpg
"""

import sys
import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add package directories
sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
from torchvision import models
from ultralytics import YOLO
from pipeline.knn_recommender import FoodSenseKNNRecommender

# Project directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) if os.path.basename(SCRIPT_DIR) == "backend-inference" else SCRIPT_DIR

YOLO_WEIGHTS = os.path.join(SCRIPT_DIR, "models", "weights", "food_detector_yolov8n.pt")
CNN_WEIGHTS = os.path.join(SCRIPT_DIR, "models", "weights", "food_classifier_mobilenet_20class.pt")
if not os.path.exists(CNN_WEIGHTS):
    CNN_WEIGHTS = os.path.join(SCRIPT_DIR, "models", "weights", "food_classifier_mobilenet.pt")

CLASS_NAMES_PATH = os.path.join(PROJECT_ROOT, "data", "class_names.json")
NUTRITION_PATH = os.path.join(PROJECT_ROOT, "data", "nutrition_table.json")

# ImageNet normalization parameters matching CNN training
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
IMAGE_SIZE = (224, 224)


def load_cnn_classifier(weights_path, num_classes):
    """Load validated MobileNetV2 CNN classifier."""
    base_mobilenet = models.mobilenet_v2(weights=None)
    in_features = base_mobilenet.classifier[1].in_features  # 1280
    base_mobilenet.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, num_classes)
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state_dict = torch.load(weights_path, map_location=device)
    base_mobilenet.load_state_dict(state_dict)
    base_mobilenet.to(device)
    base_mobilenet.eval()
    return base_mobilenet, device


def preprocess_crop(crop_img):
    """Preprocess single cropped bounding box for CNN inference."""
    img = crop_img.convert("RGB").resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, axis=0)
    return arr


def run_meal_analysis(image_path, conf_thresh=0.15, iou_thresh=0.45, output_annotated_path="meal_analysis_output.jpg"):
    print("\n" + "="*75)
    print("FOODSENSE: MULTI-ITEM MEAL DETECTION & CLASSIFICATION PIPELINE")
    print(f"Image: {image_path}")
    print("="*75)

    # 1. Load configuration and models
    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        class_names = json.load(f)
    with open(NUTRITION_PATH, "r", encoding="utf-8") as f:
        nutrition_table = json.load(f)

    print(f"-> Loading YOLOv8n detector from {YOLO_WEIGHTS} ...")
    detector = YOLO(YOLO_WEIGHTS)

    print(f"-> Loading MobileNetV2 CNN classifier from {CNN_WEIGHTS} ...")
    cnn_model, device = load_cnn_classifier(CNN_WEIGHTS, len(class_names))

    print(f"-> Loading FoodSenseKNNRecommender (6D Nutrition Space)...")
    knn_engine = FoodSenseKNNRecommender()

    # 2. Run YOLO Object Detection
    full_image = Image.open(image_path).convert("RGB")
    img_w, img_h = full_image.size

    print(f"-> Running YOLO detection (conf={conf_thresh}, iou={iou_thresh}) ...")
    yolo_results = detector.predict(full_image, conf=conf_thresh, iou=iou_thresh, device="cpu", verbose=False)[0]

    raw_boxes = []
    for box in yolo_results.boxes:
        xyxy = box.xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
        yolo_conf = float(box.conf.cpu().numpy()[0])
        yolo_cls_id = int(box.cls.cpu().numpy()[0])
        raw_boxes.append((xyxy, yolo_conf, yolo_cls_id))

    # Apply IoU deduplication across boxes to prevent multi-detection of the same dish
    def compute_iou(boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return iou

    raw_boxes.sort(key=lambda x: x[1], reverse=True)
    detected_boxes = []
    for box in raw_boxes:
        keep = True
        for kept in detected_boxes:
            if compute_iou(box[0], kept[0]) > 0.50:
                keep = False
                break
        if keep:
            detected_boxes.append(box)

    # Fallback to full frame if no distinct bounding boxes detected
    if len(detected_boxes) == 0:
        print("  [Note] No multi-item sub-boxes found; evaluating full meal frame.")
        detected_boxes.append((np.array([0, 0, img_w, img_h]), 1.0, 0))

    print(f"-> Detected {len(detected_boxes)} food item regions. Running CNN fine-grained classification...")

    # 3. Crop & Classify Each Bounding Box with CNN
    analyzed_items = []
    annotated_img = full_image.copy()
    draw = ImageDraw.Draw(annotated_img)

    for idx, (xyxy, yolo_conf, yolo_cls_id) in enumerate(detected_boxes, 1):
        x1, y1, x2, y2 = xyxy
        # Add 5% padding margin
        pad_x = (x2 - x1) * 0.05
        pad_y = (y2 - y1) * 0.05
        cx1 = max(0, int(x1 - pad_x))
        cy1 = max(0, int(y1 - pad_y))
        cx2 = min(img_w, int(x2 + pad_x))
        cy2 = min(img_h, int(y2 + pad_y))

        crop = full_image.crop((cx1, cy1, cx2, cy2))
        input_tensor = torch.from_numpy(preprocess_crop(crop)).float().to(device)

        with torch.no_grad():
            logits = cnn_model(input_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        top_idx = int(np.argmax(probs))
        cnn_class = class_names[top_idx]
        cnn_conf = float(probs[top_idx])

        # Top 3 probabilities
        top3_indices = np.argsort(probs)[-3:][::-1]
        top3_list = [{"class": class_names[i], "prob": float(probs[i])} for i in top3_indices]

        # Resolve nutrition
        nutrition_info = nutrition_table.get(cnn_class, {})

        analyzed_items.append({
            "item_index": idx,
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "cnn_class": cnn_class,
            "cnn_confidence": cnn_conf,
            "yolo_confidence": yolo_conf,
            "top3": top3_list,
            "nutrition": nutrition_info
        })

        # Draw bounding box on annotated image
        draw.rectangle([(x1, y1), (x2, y2)], outline=(230, 80, 0), width=4)
        label_text = f"#{idx}: {cnn_class} ({cnn_conf*100:.1f}%)"
        draw.rectangle([(x1, max(0, y1 - 22)), (x1 + len(label_text)*9, y1)], fill=(230, 80, 0))
        draw.text((x1 + 4, max(0, y1 - 18)), label_text, fill=(255, 255, 255))

    # 4. Print Per-Item Breakdown
    print("\n" + "="*75)
    print("ITEMIZED FOOD DETECTION & CLASSIFICATION BREAKDOWN")
    print("="*75)

    tot_cal = 0.0
    tot_protein = 0.0
    tot_carbs = 0.0
    tot_fat = 0.0
    tot_fiber = 0.0
    gi_list = []

    for item in analyzed_items:
        i = item["item_index"]
        c = item["cnn_class"]
        conf = item["cnn_confidence"]
        bbox = item["bbox"]
        nut = item["nutrition"]

        disp_name = nut.get("display_name", c)
        serving = nut.get("serving_size", "1 serving")
        cal = float(nut.get("calories", 0))
        prot = float(nut.get("protein", 0))
        carb = float(nut.get("carbs", 0))
        fat = float(nut.get("fat", 0))
        fib = float(nut.get("fiber", 0))
        gi = nut.get("glycemic_index", 50)

        tot_cal += cal
        tot_protein += prot
        tot_carbs += carb
        tot_fat += fat
        tot_fiber += fib
        if gi is not None:
            gi_list.append(gi)

        # Dynamic KNN Recommendation
        knn_swaps = knn_engine.recommend(c, k=2)

        top3_str = ", ".join([f"{t['class']}: {t['prob']*100:.1f}%" for t in item["top3"]])
        print(f"\n[Item #{i}] {disp_name.upper()}")
        print(f"  * Detected Box:       [x1={bbox[0]}, y1={bbox[1]}, x2={bbox[2]}, y2={bbox[3]}]")
        print(f"  * CNN Classification: {c} (Confidence: {conf*100:.2f}%)")
        print(f"  * Top-3 Probabilities: {top3_str}")
        print(f"  * Portion Size:        {serving}")
        print(f"  * Macros:              {cal:.0f} kcal | Protein: {prot:.1f}g | Carbs: {carb:.1f}g | Fat: {fat:.1f}g | Fiber: {fib:.1f}g | GI: {gi}")
        if knn_swaps:
            best_swap = knn_swaps[0]
            print(f"  * KNN Healthy Swap:   -> {best_swap['name']} ({best_swap['calories']:.0f} kcal | {best_swap['protein']:.1f}g P | {best_swap['carbs']:.1f}g C | {best_swap['fat']:.1f}g F | GI: {best_swap['glycemic_index']})")
            print(f"                         Dynamic Reason: {best_swap['reason']}")
            if len(knn_swaps) > 1:
                alt2 = knn_swaps[1]
                print(f"  * Alternative Option:  -> {alt2['name']} ({alt2['calories']:.0f} kcal) [Dist: {alt2['raw_distance']:.3f}]")

    # 5. Print Meal Total Nutrition Summary
    avg_gi = np.mean(gi_list) if gi_list else 50
    print("\n" + "="*75)
    print("TOTAL MEAL NUTRITION SUMMARY")
    print("="*75)
    print(f"  * Total Items Detected:     {len(analyzed_items)}")
    print(f"  * Total Calories:           {tot_cal:.0f} kcal")
    print(f"  * Total Protein:            {tot_protein:.1f} g  ({(tot_protein*4/tot_cal*100) if tot_cal>0 else 0:.1f}% of total calories)")
    print(f"  * Total Carbohydrates:      {tot_carbs:.1f} g  ({(tot_carbs*4/tot_cal*100) if tot_cal>0 else 0:.1f}% of total calories)")
    print(f"  * Total Dietary Fats:       {tot_fat:.1f} g  ({(tot_fat*9/tot_cal*100) if tot_cal>0 else 0:.1f}% of total calories)")
    print(f"  * Total Fiber:              {tot_fiber:.1f} g")
    print(f"  * Average Glycemic Index:   {avg_gi:.1f} ({'HIGH' if avg_gi>=70 else 'MODERATE' if avg_gi>=55 else 'LOW'} GI)")

    if tot_cal > 800:
        print("  ! Dietary Note: High-calorie meal. Consider replacing high-fat gravies/fried items with grilled or steamed options.")
    if tot_fiber < 6:
        print("  ! Dietary Note: Low fiber intake. Add raw cucumber/salad or whole-grain breads to lower glycemic spike.")

    # 6. Save Annotated Image
    annotated_img.save(output_annotated_path)
    print(f"\n[Annotated Image Saved] -> {output_annotated_path}")
    print("="*75 + "\n")
    return analyzed_items, tot_cal


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_img = sys.argv[1]
    else:
        # Default test on a generated multi-item validation meal
        target_img = os.path.join(DATA_DIR, "yolo_dataset", "images", "val", "meal_val_00000.jpg")

    run_meal_analysis(target_img)
