"""
FoodSense - Data & Nutrition DB Seed Script (Phase 1)
Validates all 19 classes, prints summary metrics, and generates seed JSON.
"""

import os
import sys
import json

# Ensure pipeline path is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pipeline.nutrition_db import (
    NUTRITION_DB,
    INDIAN_FOOD_CLASSES,
    get_item_nutrition,
    calculate_meal_totals,
    export_seed_json
)

def run_seed():
    print(f"==================================================")
    print(f"FoodSense Phase 1: Validating 19-Class Nutrition DB")
    print(f"==================================================")
    print(f"Total defined classes: {len(INDIAN_FOOD_CLASSES)}")
    
    assert len(INDIAN_FOOD_CLASSES) == 19, f"Expected 19 classes, found {len(INDIAN_FOOD_CLASSES)}"
    
    categories = set()
    for class_id in INDIAN_FOOD_CLASSES:
        item = NUTRITION_DB.get(class_id)
        assert item is not None, f"Missing data for class: {class_id}"
        assert "calories" in item, f"Missing calories for {class_id}"
        assert "protein" in item, f"Missing protein for {class_id}"
        assert "carbs" in item, f"Missing carbs for {class_id}"
        assert "fat" in item, f"Missing fat for {class_id}"
        assert "fiber" in item, f"Missing fiber for {class_id}"
        assert "glycemic_index" in item, f"Missing glycemic index for {class_id}"
        assert len(item.get("healthy_alternatives", [])) >= 1, f"Missing healthy alternatives for {class_id}"
        categories.add(item["category"])
        
        print(f"[OK] [{item['category']:<12}] {item['display_name']:<28} | {item['calories']:>5.1f} kcal | P: {item['protein']:>4.1f}g | C: {item['carbs']:>4.1f}g | F: {item['fat']:>4.1f}g | GI: {item['glycemic_index']}")

    print(f"\nUnique Food Categories ({len(categories)}): {', '.join(sorted(categories))}")
    
    # Export seed JSON
    seed_output = os.path.join(current_dir, "data", "nutrition_seed.json")
    export_seed_json(seed_output)
    print(f"[OK] Exported seed JSON database to: {seed_output}")
    
    # Test meal total aggregation
    sample_meal = [
        {"class_id": "roti", "portion_multiplier": 2.0},
        {"class_id": "dal_tadka", "portion_multiplier": 1.0},
        {"class_id": "paneer_butter_masala", "portion_multiplier": 0.5}
    ]
    totals = calculate_meal_totals(sample_meal)
    print(f"\nSample Meal Calculation (2x Roti + 1x Dal + 0.5x Paneer Butter Masala):")
    print(f"  - Total Calories: {totals['calories']} kcal")
    print(f"  - Total Protein:  {totals['protein']} g ({totals['protein_pct']}%)")
    print(f"  - Total Carbs:    {totals['carbs']} g ({totals['carbs_pct']}%)")
    print(f"  - Total Fat:      {totals['fat']} g ({totals['fat_pct']}%)")
    print(f"  - Total Fiber:    {totals['fiber']} g")
    print(f"==================================================")
    print(f"Phase 1 Verification SUCCESSFUL!")
    print(f"==================================================")

if __name__ == "__main__":
    run_seed()
