"""
FoodSense — Flask ML Inference API (Phase 5)
Loads YOLOv8n detector, MobileNetV2 CNN classifier, and True 6D KNN nutrition recommender once at startup.
Exposes /analyze, /health, /classes, and /lookup_item endpoints with standardized JSON responses.
"""

import os
import sys
import time
import io
import uuid
import json
import logging
from typing import Dict, Any, List

# Add package directories and avoid duplicate OpenMP runtime collisions
sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FoodSenseAPI")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..")) if os.path.basename(CURRENT_DIR) == "backend-inference" else CURRENT_DIR

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from pipeline.yolo_detector import YOLOMealDetector
from pipeline.cnn_classifier import IndianFoodClassifier
from pipeline.knn_recommender import FoodSenseKNNRecommender

CLASS_NAMES_PATH = os.path.join(PROJECT_ROOT, "data", "class_names.json")
NUTRITION_PATH = os.path.join(PROJECT_ROOT, "data", "nutrition_table.json")

app = Flask(__name__)
CORS(app)


# Pipeline Manager Singleton
class PipelineManager:
    """Manages one-time model initialization and lifecycle."""

    def __init__(self):
        logger.info("Initializing FoodSense AI Inference Pipeline (One-Time Startup)...")
        start_t = time.time()

        # Load 20 class names and nutrition table
        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
            self.class_names = json.load(f)
        with open(NUTRITION_PATH, "r", encoding="utf-8") as f:
            self.nutrition_table = json.load(f)

        # 1. Initialize YOLOv8n detector
        yolo_weights = os.path.join(CURRENT_DIR, "models", "weights", "food_detector_yolov8n.pt")
        self.detector = YOLOMealDetector(weights_path=yolo_weights, confidence_threshold=0.15, iou_threshold=0.45)

        # 2. Initialize MobileNetV2 CNN classifier
        cnn_weights = os.path.join(CURRENT_DIR, "models", "weights", "food_classifier_mobilenet_20class.pt")
        if not os.path.exists(cnn_weights):
            cnn_weights = os.path.join(CURRENT_DIR, "models", "weights", "food_classifier_mobilenet.pt")
        self.classifier = IndianFoodClassifier(model_path=cnn_weights, classes=self.class_names)

        # 3. Initialize True 6D KNN Recommender
        self.recommender = FoodSenseKNNRecommender()

        self.loaded_at = time.time()
        elapsed_ms = round((self.loaded_at - start_t) * 1000, 2)
        logger.info(f"All models initialized successfully in {elapsed_ms}ms! Ready for requests.")

    def get_item_info(self, class_id: str) -> Dict[str, Any]:
        """Look up nutrition, display name, portion, and KNN healthy alternative for a class."""
        if class_id not in self.class_names:
            return None

        nut = self.nutrition_table.get(class_id, {})
        display_name = nut.get("display_name", class_id.replace("_", " ").title())
        portion = nut.get("serving_size", "1 serving")
        cal = float(nut.get("calories", 200))
        prot = float(nut.get("protein", 5))
        carb = float(nut.get("carbs", 30))
        fat = float(nut.get("fat", 8))
        fib = float(nut.get("fiber", 2))
        gi = int(nut.get("glycemic_index", 50))

        knn_swaps = self.recommender.recommend(class_id, k=1)
        if knn_swaps:
            top_swap = knn_swaps[0]
            alt_obj = {
                "name": top_swap["name"],
                "macros": {
                    "calories": top_swap["calories"],
                    "protein": top_swap["protein"],
                    "carbs": top_swap["carbs"],
                    "fat": top_swap["fat"],
                    "fiber": top_swap["fiber"],
                    "gi": top_swap["glycemic_index"]
                },
                "reason": top_swap["reason"]
            }
        else:
            alt_obj = None

        return {
            "label": class_id,
            "display_name": display_name,
            "confidence": 1.0,
            "portion": portion,
            "macros": {
                "calories": round(cal, 1),
                "protein": round(prot, 1),
                "carbs": round(carb, 1),
                "fat": round(fat, 1),
                "fiber": round(fib, 1),
                "gi": gi
            },
            "healthy_alternative": alt_obj
        }

    def process_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Execute full inference pipeline:
        Image -> YOLO (Localization) -> CNN (Classification) -> Nutrition DB -> KNN (Recommendations) -> Meal Totals
        """
        start_time = time.time()
        img_w, img_h = image.size

        # Step 1: Detect items and bounding boxes with YOLO
        detected_boxes = self.detector.detect_items(image)

        items = []
        tot_cal = 0.0
        tot_protein = 0.0
        tot_carbs = 0.0
        tot_fat = 0.0
        tot_fiber = 0.0
        gi_values = []

        raw_classified = []
        for idx, box_info in enumerate(detected_boxes, 1):
            bbox = box_info.get("bbox_absolute") or box_info.get("bbox") or [0, 0, img_w, img_h]
            x1, y1, x2, y2 = bbox

            # Ensure valid crop boundaries
            x1_c = max(0, min(x1, img_w - 1))
            y1_c = max(0, min(y1, img_h - 1))
            x2_c = max(x1_c + 1, min(x2, img_w))
            y2_c = max(y1_c + 1, min(y2, img_h))

            # Skip trivial/empty box dimensions
            if (x2_c - x1_c) < 20 or (y2_c - y1_c) < 20:
                continue

            crop_img = image.crop((x1_c, y1_c, x2_c, y2_c))

            # Step 2: Classify cropped region with MobileNetV2 CNN
            pred_res = self.classifier.predict_crop(crop_img)
            pred_class = pred_res["class_id"]
            cnn_conf = pred_res["confidence"]
            yolo_conf = box_info.get("confidence", 0.85)

            # DISCARD LOW-CONFIDENCE SOFTMAX NOISE:
            # Detections below 55% CNN confidence are discarded to prevent phantom guesses
            if cnn_conf < 0.55:
                print(f"[Inference Pipeline] Discarded low-confidence crop '{pred_class}' ({cnn_conf:.2%}) at {bbox}")
                continue

            raw_classified.append({
                "box_info": box_info,
                "bbox": bbox,
                "class_id": pred_class,
                "confidence": cnn_conf,
                "yolo_conf": yolo_conf,
                "combined_score": round(cnn_conf * 0.7 + yolo_conf * 0.3, 4)
            })

        # Step 3: Strict Spatial NMS & Cross-Detection Deduplication
        # Sort by combined score
        raw_classified.sort(key=lambda x: x["combined_score"], reverse=True)
        clustered = []
        for cand in raw_classified:
            b1 = cand["bbox"]
            cls1 = cand["class_id"]
            is_dup = False
            for kept in clustered:
                b2 = kept["bbox"]
                cls2 = kept["class_id"]
                
                # Compute IoU between bounding boxes
                xA = max(b1[0], b2[0])
                yA = max(b1[1], b2[1])
                xB = min(b1[2], b2[2])
                yB = min(b1[3], b2[3])
                inter = max(0, xB - xA) * max(0, yB - yA)
                areaA = (b1[2] - b1[0]) * (b1[3] - b1[1])
                areaB = (b2[2] - b2[0]) * (b2[3] - b2[1])
                iou = inter / float(areaA + areaB - inter + 1e-6)

                # If same class with overlap > 0.30 OR different class with severe overlap > 0.45, suppress lower score
                if (cls1 == cls2 and iou > 0.30) or (iou > 0.45):
                    is_dup = True
                    break

            if not is_dup:
                clustered.append(cand)

        # Fallback for simple single-dish photo if all crops were suppressed
        if not clustered:
            full_pred = self.classifier.predict_crop(image)
            if full_pred["confidence"] >= 0.50:
                clustered.append({
                    "box_info": {"confidence": 0.85, "needs_confirmation": False, "confidence_tier": "confirmed"},
                    "bbox": [0, 0, img_w, img_h],
                    "class_id": full_pred["class_id"],
                    "confidence": full_pred["confidence"],
                    "yolo_conf": 0.85,
                    "combined_score": full_pred["confidence"]
                })

        # Cap at 8 highest-confidence distinct items
        final_candidates = clustered[:8]

        items = []
        tot_cal = 0.0
        tot_protein = 0.0
        tot_carbs = 0.0
        tot_fat = 0.0
        tot_fiber = 0.0
        gi_values = []

        for idx, entry in enumerate(final_candidates, 1):
            class_id = entry["class_id"]
            confidence = entry["confidence"]
            bbox = entry["bbox"]
            box_info = entry["box_info"]

            # Step 4: Lookup nutrition & Glycemic Index
            nut = self.nutrition_table.get(class_id, {})
            display_name = nut.get("display_name", class_id.replace("_", " ").title())
            portion = nut.get("serving_size", "1 serving")
            cal = float(nut.get("calories", 200))
            prot = float(nut.get("protein", 5))
            carb = float(nut.get("carbs", 30))
            fat = float(nut.get("fat", 8))
            fib = float(nut.get("fiber", 2))
            gi = int(nut.get("glycemic_index", 50))

            tot_cal += cal
            tot_protein += prot
            tot_carbs += carb
            tot_fat += fat
            tot_fiber += fib
            gi_values.append(gi)

            # Step 5: Generate KNN healthier alternatives
            knn_swaps = self.recommender.recommend(class_id, k=1)
            if knn_swaps:
                top_swap = knn_swaps[0]
                alt_obj = {
                    "name": top_swap["name"],
                    "macros": {
                        "calories": top_swap["calories"],
                        "protein": top_swap["protein"],
                        "carbs": top_swap["carbs"],
                        "fat": top_swap["fat"],
                        "fiber": top_swap["fiber"],
                        "gi": top_swap["glycemic_index"]
                    },
                    "reason": top_swap["reason"]
                }
            else:
                alt_obj = None

            items.append({
                "item_id": f"item_{idx}",
                "label": class_id,
                "display_name": display_name,
                "confidence": round(confidence, 4),
                "needs_confirmation": False,
                "confidence_tier": "confirmed",
                "bbox": bbox,
                "portion": portion,
                "macros": {
                    "calories": round(cal, 1),
                    "protein": round(prot, 1),
                    "carbs": round(carb, 1),
                    "fat": round(fat, 1),
                    "fiber": round(fib, 1),
                    "gi": gi
                },
                "healthy_alternative": alt_obj
            })

        # Step 6: Compute meal summary
        avg_gi = round(float(np.mean(gi_values)), 1) if gi_values else 50.0

        dietary_notes = []
        if tot_cal > 800:
            dietary_notes.append("High-calorie meal. Consider replacing high-fat gravies or fried items with grilled/steamed options.")
        if tot_fiber < 6:
            dietary_notes.append("Low fiber intake. Add a raw salad, cucumber, or whole-grain breads to lower post-meal glycemic spikes.")
        if avg_gi >= 70:
            dietary_notes.append("High glycemic meal. Pairing with lemon or raw fiber will help moderate blood glucose release.")
        if not dietary_notes:
            dietary_notes.append("Well-balanced macronutrient meal.")

        meal_summary = {
            "total_items": len(items),
            "total_calories": round(tot_cal, 1),
            "total_protein": round(tot_protein, 1),
            "total_carbs": round(tot_carbs, 1),
            "total_fat": round(tot_fat, 1),
            "total_fiber": round(tot_fiber, 1),
            "average_gi": avg_gi,
            "dietary_note": " ".join(dietary_notes)
        }

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Processed meal in {processing_time_ms}ms: {len(items)} items detected ({[it['label'] for it in items]})")

        return {
            "status": "success",
            "meal_id": f"meal_{uuid.uuid4().hex[:8]}",
            "items": items,
            "meal_summary": meal_summary,
            "processing_time_ms": processing_time_ms
        }


# Initialize singleton pipeline once at startup
pipeline = PipelineManager()


@app.route("/health", methods=["GET"])
def health():
    """Lightweight health check endpoint for cold-start monitoring."""
    uptime_sec = round(time.time() - pipeline.loaded_at, 1)
    return jsonify({
        "status": "healthy",
        "service": "FoodSense-Inference-Backend",
        "supported_classes": len(pipeline.class_names),
        "models_ready": True,
        "uptime_seconds": uptime_sec
    }), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Main Meal Analysis Endpoint.
    Accepts multipart image upload ('file' or 'image' field) or raw image payload.
    """
    try:
        image = None

        # 1. Check multipart file upload
        if "file" in request.files:
            file_obj = request.files["file"]
            if file_obj.filename != "":
                image = Image.open(file_obj.stream)
        elif "image" in request.files:
            file_obj = request.files["image"]
            if file_obj.filename != "":
                image = Image.open(file_obj.stream)

        # 2. Check raw binary payload
        if image is None and request.data:
            try:
                image = Image.open(io.BytesIO(request.data))
            except Exception:
                pass

        if image is None:
            return jsonify({
                "status": "error",
                "error": "Bad Request",
                "message": "No valid image provided. Please upload an image file using multipart form field 'file' or 'image'."
            }), 400

        # Run full pipeline
        response_payload = pipeline.process_image(image)
        return jsonify(response_payload), 200

    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": "Internal Server Error",
            "message": "An error occurred during food image analysis."
        }), 500


@app.route("/classes", methods=["GET"])
def get_classes():
    """Return all supported food classes and nutrition database."""
    return jsonify({
        "status": "success",
        "classes": pipeline.class_names,
        "database": pipeline.nutrition_table
    }), 200


@app.route("/lookup_item", methods=["GET", "POST"])
def lookup_item():
    """Look up nutrition and KNN recommendations for a specific class label."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        class_id = data.get("label") or data.get("class_id")
    else:
        class_id = request.args.get("label") or request.args.get("class_id")

    if not class_id or class_id not in pipeline.class_names:
        return jsonify({
            "status": "error",
            "error": "Invalid Class",
            "message": f"Class '{class_id}' is not in the supported 20-class registry."
        }), 400

    item_info = pipeline.get_item_info(class_id)
    return jsonify({
        "status": "success",
        "item": item_info
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"FoodSense Flask Inference API running on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
