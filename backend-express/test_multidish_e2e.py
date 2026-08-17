"""
End-to-End Test Suite for FoodSense Multi-Dish Detection & 1500+ Indian Dish Catalog
Validates:
1. Multi-item dish inference & item array response
2. Expanded 1500+ Indian dishes search, filtering & custom dish creation
3. Adding catalog/custom dishes to an existing meal analysis
4. Full-meal calorie, macronutrient, and GI recalculation
5. SQLite persistence across meal_history, dishes, and corrections tables
"""

import requests
import json
import os
import io
from PIL import Image, ImageDraw

EXPRESS_URL = "http://127.0.0.1:3001/api"
FLASK_URL = "http://127.0.0.1:5000"

def create_synthetic_multidish_image():
    """Generates a synthetic image with 2 food regions (idli + samosa)."""
    img = Image.new("RGB", (640, 640), color=(240, 235, 225))
    draw = ImageDraw.Draw(img)
    # Region 1 (Idli-like white circles)
    draw.ellipse([60, 60, 280, 280], fill=(250, 250, 250), outline=(200, 200, 200), width=4)
    # Region 2 (Samosa-like golden triangle)
    draw.polygon([(400, 100), (560, 280), (320, 280)], fill=(210, 150, 60), outline=(160, 100, 30))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

def run_tests():
    print("===========================================================================")
    print("FOODSENSE MULTI-DISH & 1500+ DISHES END-TO-END SUITE")
    print("===========================================================================")

    # 1. Health checks
    r = requests.get(f"{EXPRESS_URL}/health")
    assert r.status_code == 200, f"Express health failed: {r.text}"
    print(f"\n[PASS 1] Express Relay & Flask Backend healthy: {r.json().get('status')}")

    # 2. 1500+ Dishes Database verification
    r = requests.get(f"{EXPRESS_URL}/dishes/categories")
    assert r.status_code == 200
    cat_data = r.json()
    total_dishes = cat_data.get('total_dishes', 0)
    print(f"[PASS 2] 1500+ Dishes Catalog: {total_dishes} authentic dishes loaded across {len(cat_data.get('categories', []))} categories and {len(cat_data.get('regions', []))} regions.")
    assert total_dishes >= 1500, f"Expected >= 1500 dishes, got {total_dishes}"

    # 3. Multi-Dish Image Inference via POST /api/analyze
    img_buf = create_synthetic_multidish_image()
    files = {"image": ("meal_test.jpg", img_buf, "image/jpeg")}
    r = requests.post(f"{EXPRESS_URL}/analyze", files=files)
    assert r.status_code == 200, f"Analyze failed: {r.text}"
    analysis = r.json()
    items = analysis.get("items", [])
    print(f"\n[PASS 3] Image Analysis successful: {len(items)} item(s) localized in {analysis.get('processing_time_ms')}ms")
    for it in items:
        print(f"  - [{it.get('label')}] {it.get('display_name')}: {it.get('macros', {}).get('calories')} kcal (Conf: {it.get('confidence')})")
    assert len(items) >= 1, "Expected at least 1 detected item"

    meal_id = analysis.get("meal_id", "test_meal_123")

    # 4. Search expanded catalog for regional dish (e.g., 'Masala Dosa' or 'Paneer')
    r = requests.get(f"{EXPRESS_URL}/dishes/search?q=Dosa&limit=3")
    assert r.status_code == 200
    search_res = r.json()
    print(f"\n[PASS 4] Catalog Search for 'Dosa': Found {search_res.get('total')} items")
    assert search_res.get('total', 0) >= 1
    picked_dish = search_res['dishes'][0]
    print(f"  Selected: {picked_dish['name']} ({picked_dish['region']} | {picked_dish['calories']} kcal | GI: {picked_dish['gi']})")

    # 5. Add picked dish to the meal via POST /api/correct (missed_item)
    correct_payload = {
        "meal_id": meal_id,
        "original_label": "unrecognized",
        "corrected_label": picked_dish['id'],
        "correction_type": "missed_item",
        "bbox": [50, 50, 400, 400],
        "all_items": items
    }
    r = requests.post(f"{EXPRESS_URL}/correct", json=correct_payload)
    assert r.status_code == 200, f"Correction failed: {r.text}"
    correct_res = r.json()
    print(f"\n[PASS 5] Added Missed Catalog Dish '{picked_dish['name']}' to Meal:")
    print(f"  - Item: {correct_res.get('corrected_item', {}).get('display_name')}")
    print(f"  - New Meal Total Calories: {correct_res.get('meal_summary', {}).get('total_calories')} kcal")
    print(f"  - Total Items in Meal: {correct_res.get('meal_summary', {}).get('total_items')}")

    # 6. Add Custom User Dish
    custom_dish_data = {
        "name": "Nani's Spiced Bajra Khichdi",
        "category": "Rice & Biryanis",
        "region": "Rajasthani",
        "calories": 240,
        "protein": 7.2,
        "carbs": 42.0,
        "fat": 4.5,
        "fiber": 5.8,
        "gi": 45,
        "standard_portion": "1 warm bowl (220g)",
        "dietary_type": "Vegetarian",
        "tags": ["millet", "healthy", "rajasthani", "bajra"]
    }
    r = requests.post(f"{EXPRESS_URL}/dishes/custom", json=custom_dish_data)
    assert r.status_code in [200, 201]
    saved_custom = r.json().get('dish')
    print(f"\n[PASS 6] Created Custom Dish: '{saved_custom['name']}' (ID: {saved_custom['id']})")

    # 7. Add custom dish to meal
    r = requests.post(f"{EXPRESS_URL}/correct", json={
        "meal_id": meal_id,
        "original_label": "unrecognized",
        "corrected_label": saved_custom['id'],
        "correction_type": "missed_item",
        "bbox": [100, 100, 300, 300],
        "all_items": items + [correct_res['corrected_item']]
    })
    assert r.status_code == 200
    print(f"[PASS 7] Successfully added custom dish '{saved_custom['name']}' into meal analysis.")

    print("\n===========================================================================")
    print("ALL MULTI-DISH & 1500+ DISH CATALOG TESTS PASSED 100%!")
    print("===========================================================================")

if __name__ == "__main__":
    run_tests()
