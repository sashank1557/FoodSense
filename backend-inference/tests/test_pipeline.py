"""
FoodSense - Full Pipeline Integration Test (YOLO -> CNN -> Nutrition DB -> KNN -> Totals)
"""

import os
import sys
import io
import time
from PIL import Image, ImageDraw

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline.nutrition_db import INDIAN_FOOD_CLASSES, NUTRITION_DB, calculate_meal_totals
from pipeline.cnn_classifier import IndianFoodClassifier
from pipeline.yolo_detector import YOLOMealDetector
from pipeline.knn_recommender import NutritionKNNRecommender


def create_mock_meal_image() -> Image.Image:
    """Create a synthetic 600x600 multi-dish Indian meal thali image."""
    img = Image.new("RGB", (600, 600), (235, 230, 220))
    draw = ImageDraw.Draw(img)
    
    # Large steel thali plate rim
    draw.ellipse([20, 20, 580, 580], fill=(215, 215, 220), outline=(170, 170, 180), width=6)
    
    # Katori 1 (Top Left: Dal Tadka - Yellow)
    draw.ellipse([60, 60, 270, 270], fill=(235, 185, 45), outline=(180, 180, 190), width=4)
    # Katori 2 (Top Right: Paneer Butter Masala - Orange Red)
    draw.ellipse([330, 60, 540, 270], fill=(220, 85, 35), outline=(180, 180, 190), width=4)
    # Bottom Left: Steamed Rice (White mound)
    draw.ellipse([60, 310, 280, 530], fill=(248, 248, 245), outline=(180, 180, 190), width=4)
    # Bottom Right: Roti / Chapati (Golden Wheat)
    draw.ellipse([320, 310, 540, 530], fill=(205, 165, 110), outline=(160, 120, 70), width=4)
    
    return img


def test_full_pipeline():
    print(f"==================================================")
    print(f"FoodSense: End-to-End Pipeline Integration Test")
    print(f"==================================================")
    
    t0 = time.time()
    detector = YOLOMealDetector(confidence_threshold=0.25, iou_threshold=0.45)
    classifier = IndianFoodClassifier()
    recommender = NutritionKNNRecommender()
    print(f"Pipeline components initialized in {round((time.time() - t0)*1000, 1)}ms\n")
    
    # 1. Create multi-item meal
    meal_img = create_mock_meal_image()
    print(f"Input Meal Photo Dimensions: {meal_img.size[0]}x{meal_img.size[1]} px")
    
    # 2. YOLO Localization
    boxes = detector.detect_items(meal_img)
    print(f"YOLO Localization: Found {len(boxes)} distinct food items.")
    assert len(boxes) >= 1, "YOLO should detect food regions"
    
    # 3. Iterate through detected items
    detections = []
    for idx, box in enumerate(boxes):
        crop = detector.extract_crop(meal_img, box["bbox_absolute"])
        classification = classifier.predict_crop(crop, top_k=3)
        class_id = classification["class_id"]
        confidence = classification["confidence"]
        
        # Override class_id for synthetic color katoris if needed for demo test
        nutrition = NUTRITION_DB.get(class_id)
        alts = recommender.recommend(class_id, k=2)
        
        det_record = {
            "item_id": f"item_{idx+1}",
            "class_id": class_id,
            "label": nutrition["display_name"] if nutrition else class_id,
            "category": nutrition["category"] if nutrition else "General",
            "confidence": confidence,
            "bbox": box,
            "nutrition": nutrition,
            "healthier_alternatives": alts
        }
        detections.append(det_record)
        
        print(f"\nItem #{idx+1}: {det_record['label']} ({det_record['category']})")
        print(f"  * Confidence:   {confidence * 100:.1f}%")
        print(f"  * Bounding Box: {box['bbox_absolute']} (Normalized: {box['bbox_normalized']})")
        if nutrition:
            print(f"  * Nutrition:    {nutrition['calories']} kcal | P: {nutrition['protein']}g | C: {nutrition['carbs']}g | F: {nutrition['fat']}g | GI: {nutrition['glycemic_index']}")
        if alts:
            print(f"  * Healthy Alt:  {alts[0]['name']} ({alts[0]['calorie_delta']:+0.1f} kcal, GI {alts[0]['gi_delta']:+0.1f})")

    # 4. Meal Macro Totals
    totals = calculate_meal_totals(detections)
    print(f"\n==================================================")
    print(f"Aggregated Meal Totals:")
    print(f"  - Total Calories: {totals['calories']} kcal")
    print(f"  - Total Protein:  {totals['protein']}g ({totals['protein_pct']}%)")
    print(f"  - Total Carbs:    {totals['carbs']}g ({totals['carbs_pct']}%)")
    print(f"  - Total Fat:      {totals['fat']}g ({totals['fat_pct']}%)")
    print(f"  - Total Fiber:    {totals['fiber']}g")
    print(f"==================================================")
    print(f"Full Pipeline Integration Test SUCCESSFUL!")
    print(f"==================================================")


if __name__ == "__main__":
    test_full_pipeline()
