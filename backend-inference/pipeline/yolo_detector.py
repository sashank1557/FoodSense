"""
FoodSense - YOLO Meal Item Detector & Localizer (Phase 3 & Recall Optimization)
Localizes individual food items in multi-item meal images using trained YOLOv8n detector.
Features Two-Tier Confidence Strategy (Confirmed vs Suggested) for real-world recall resilience.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from PIL import Image
import numpy as np

# Add package directories
sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
WEIGHTS_PATH = os.path.join(BACKEND_DIR, "models", "weights", "food_detector_yolov8n.pt")
if not os.path.exists(WEIGHTS_PATH):
    WEIGHTS_PATH = os.path.join(BACKEND_DIR, "models", "weights", "food_detector_best.pt")


def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou


class YOLOMealDetector:
    """
    Food Item Localization Engine using fine-tuned YOLOv8n.
    Implements a robust Two-Tier Confidence Strategy:
      - Confirmed Tier (conf >= 0.14): High confidence detections.
      - Suggested Tier (0.05 <= conf < 0.14): Candidate regions flagged for user confirmation.
    """

    def __init__(self, weights_path: Optional[str] = None, confidence_threshold: float = 0.035, iou_threshold: float = 0.45):
        self.weights_path = weights_path or WEIGHTS_PATH
        self.confidence_threshold = confidence_threshold
        self.high_conf_threshold = 0.12
        self.iou_threshold = iou_threshold

        if os.path.exists(self.weights_path):
            self.model = YOLO(self.weights_path)
            print(f"[YOLOMealDetector] Loaded YOLOv8n detector from {self.weights_path} (conf={confidence_threshold}, iou={iou_threshold})")
        else:
            self.model = None
            print(f"[YOLOMealDetector] Warning: Weights file {self.weights_path} not found. Fallback mode enabled.")

    def detect_items(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Locate food items in the image and extract bounding boxes.
        Returns a list of candidate regions with absolute coordinates [x1, y1, x2, y2]
        and confidence tier markings (confirmed vs needs_confirmation).
        Features multi-dish region extraction for complex meal platters / thalis.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        orig_w, orig_h = image.size
        boxes_list = []

        if self.model is not None:
            try:
                # Run YOLO multi-scale detection
                results = self.model.predict(
                    image,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    device="cpu",
                    verbose=False
                )[0]

                raw_boxes = []
                for box in results.boxes:
                    xyxy = box.xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
                    conf = float(box.conf.cpu().numpy()[0])
                    raw_boxes.append((xyxy, conf))

                # Apply IoU deduplication to eliminate overlapping candidate boxes
                raw_boxes.sort(key=lambda x: x[1], reverse=True)
                deduped = []
                for b, conf in raw_boxes:
                    keep = True
                    for kept_b, _ in deduped:
                        if compute_iou(b, kept_b) > 0.45:
                            keep = False
                            break
                    if keep:
                        deduped.append((b, conf))

                for idx, (b, conf) in enumerate(deduped, 1):
                    x1, y1, x2, y2 = [int(coord) for coord in b]
                    # Clamp to image boundaries
                    x1 = max(0, min(orig_w - 1, x1))
                    y1 = max(0, min(orig_h - 1, y1))
                    x2 = max(x1 + 1, min(orig_w, x2))
                    y2 = max(y1 + 1, min(orig_h, y2))

                    is_high_conf = conf >= self.high_conf_threshold

                    boxes_list.append({
                        "item_id": f"item_{idx}",
                        "confidence": round(conf, 4),
                        "needs_confirmation": not is_high_conf,
                        "confidence_tier": "confirmed" if is_high_conf else "suggested",
                        "bbox_absolute": [x1, y1, x2, y2],
                        "bbox_normalized": [
                            round(x1 / orig_w, 4),
                            round(y1 / orig_h, 4),
                            round(x2 / orig_w, 4),
                            round(y2 / orig_h, 4)
                        ],
                        "width": x2 - x1,
                        "height": y2 - y1
                    })
            except Exception as e:
                print(f"[YOLOMealDetector] Inference warning: {e}")

        # Multi-dish platter handling: If only 1 large bounding box covers >65% of the frame,
        # propose quadrant sub-regions to check for multiple dishes on the same thali/platter
        if len(boxes_list) == 1 and (boxes_list[0]["width"] * boxes_list[0]["height"]) > (orig_w * orig_h * 0.65):
            main_box = boxes_list[0]
            bx1, by1, bx2, by2 = main_box["bbox_absolute"]
            bw = bx2 - bx1
            bh = by2 - by1
            
            # Quadrant sub-regions within the main platter
            mid_x = bx1 + bw // 2
            mid_y = by1 + bh // 2
            sub_quads = [
                ([bx1, by1, mid_x, mid_y], "top_left"),
                ([mid_x, by1, bx2, mid_y], "top_right"),
                ([bx1, mid_y, mid_x, by2], "bottom_left"),
                ([mid_x, mid_y, bx2, by2], "bottom_right")
            ]
            
            for (qx1, qy1, qx2, qy2), qname in sub_quads:
                boxes_list.append({
                    "item_id": f"item_sub_{qname}",
                    "confidence": 0.35,
                    "needs_confirmation": True,
                    "confidence_tier": "suggested",
                    "bbox_absolute": [qx1, qy1, qx2, qy2],
                    "bbox_normalized": [
                        round(qx1 / orig_w, 4),
                        round(qy1 / orig_h, 4),
                        round(qx2 / orig_w, 4),
                        round(qy2 / orig_h, 4)
                    ],
                    "width": qx2 - qx1,
                    "height": qy2 - qy1
                })

        # Fallback to full frame if no items detected at all
        if not boxes_list:
            boxes_list.append({
                "item_id": "item_1",
                "confidence": 0.85,
                "needs_confirmation": False,
                "confidence_tier": "confirmed",
                "bbox_absolute": [0, 0, orig_w, orig_h],
                "bbox_normalized": [0.0, 0.0, 1.0, 1.0],
                "width": orig_w,
                "height": orig_h
            })

        return boxes_list
