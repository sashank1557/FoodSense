"""
FoodSense - KNN Recommendation Verification (Phase 4)
Sanity-checks category-filtered recommendations for representative Indian food classes.
"""

import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline.nutrition_db import INDIAN_FOOD_CLASSES, NUTRITION_DB
from pipeline.knn_recommender import NutritionKNNRecommender

def test_knn_recommender():
    print(f"==================================================")
    print(f"FoodSense Phase 4: Validating KNN Recommendation Engine")
    print(f"==================================================")
    
    recommender = NutritionKNNRecommender()
    
    test_classes = ["steamed_rice", "naan", "poori", "samosa", "paneer_butter_masala", "gulab_jamun"]
    
    for cls in test_classes:
        base_item = NUTRITION_DB[cls]
        recs = recommender.recommend(cls, k=2)
        print(f"\nDish: {base_item['display_name']} ({base_item['category']}) | {base_item['calories']} kcal | GI: {base_item['glycemic_index']} | Fat: {base_item['fat']}g | Fiber: {base_item['fiber']}g")
        assert len(recs) >= 1, f"Expected recommendations for {cls}"
        
        for r in recs:
            cal_str = f"{r['calorie_delta']:+0.1f} kcal"
            gi_str = f"GI {r['gi_delta']:+0.1f}"
            print(f"  -> Recommended: {r['name']} ({r['category']}) | {r['calories']} kcal ({cal_str}) | {gi_str} | Reason: {r['reason']}")
            # Sanity check: Category should match or be related
            assert r["category"] == base_item["category"], f"Category mismatch: {r['category']} vs {base_item['category']}"
            
    print(f"\n==================================================")
    print(f"Phase 4 KNN Verification SUCCESSFUL!")
    print(f"==================================================")

if __name__ == "__main__":
    test_knn_recommender()
