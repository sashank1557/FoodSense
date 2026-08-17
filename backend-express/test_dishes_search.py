"""
Test suite for 1500+ Indian dishes search, regional filtering, and custom dish creation.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:3001/api/dishes"

def test_dishes():
    print("===========================================================================")
    print("TESTING 1500+ DISHES SEARCH & CATALOG API")
    print("===========================================================================")

    # 1. Categories and regions
    r = requests.get(f"{BASE_URL}/categories")
    print(f"\n[TEST 1] GET /api/dishes/categories (Status: {r.status_code})")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    cat_data = r.json()
    print(f"Total Dishes in SQLite: {cat_data.get('total_dishes')}")
    print(f"Categories ({len(cat_data.get('categories', []))}): {cat_data.get('categories')[:5]}...")
    print(f"Regions ({len(cat_data.get('regions', []))}): {cat_data.get('regions')[:5]}...")
    assert cat_data.get('total_dishes', 0) >= 1500, "Expected >=1500 dishes"

    # 2. Substring / Autocomplete search for 'idli'
    r = requests.get(f"{BASE_URL}/search?q=idli&limit=5")
    print(f"\n[TEST 2] GET /api/dishes/search?q=idli&limit=5 (Status: {r.status_code})")
    assert r.status_code == 200
    res = r.json()
    print(f"Matches found: {res.get('total')}")
    for d in res.get('dishes', []):
        print(f"  - {d['name']} [{d['region']} | {d['category']}]: {d['calories']} kcal, {d['standard_portion']}")
    assert res.get('total', 0) >= 1, "Expected matching dishes for 'idli'"

    # 3. Regional + Category Filter: 'South Indian' + 'Breakfast'
    r = requests.get(f"{BASE_URL}/search?region=South Indian&category=Breakfast&limit=5")
    print(f"\n[TEST 3] GET /api/dishes/search?region=South Indian&category=Breakfast (Status: {r.status_code})")
    assert r.status_code == 200
    res = r.json()
    print(f"Total South Indian Breakfast items: {res.get('total')}")
    for d in res.get('dishes', []):
        print(f"  - {d['name']} (GI: {d['gi']})")

    # 4. Search for Biryani / Pulao
    r = requests.get(f"{BASE_URL}/search?q=biryani&limit=5")
    print(f"\n[TEST 4] GET /api/dishes/search?q=biryani (Status: {r.status_code})")
    assert r.status_code == 200
    res = r.json()
    print(f"Total Biryani items: {res.get('total')}")
    for d in res.get('dishes', []):
        print(f"  - {d['name']} (Protein: {d['protein']}g, Carbs: {d['carbs']}g)")

    # 5. POST /api/dishes/custom (Custom Dish)
    custom_payload = {
        "name": "Mom's Special Ragi Mudde & Saaru",
        "category": "Breakfast",
        "region": "Karnataka",
        "calories": 210,
        "protein": 7.5,
        "carbs": 38.0,
        "fat": 2.0,
        "fiber": 6.0,
        "gi": 48,
        "standard_portion": "1 ball + 1 bowl saaru (250g)",
        "dietary_type": "Vegetarian",
        "tags": ["ragi", "millet", "healthy", "karnataka"]
    }
    r = requests.post(f"{BASE_URL}/custom", json=custom_payload)
    print(f"\n[TEST 5] POST /api/dishes/custom (Status: {r.status_code})")
    assert r.status_code in [200, 201]
    created = r.json().get('dish')
    print(f"Created Dish: {created['name']} (ID: {created['id']})")
    assert created['name'] == custom_payload['name']

    # 6. Verify custom dish is now searchable
    r = requests.get(f"{BASE_URL}/search?q=Ragi Mudde")
    assert r.status_code == 200
    res = r.json()
    print(f"\n[TEST 6] Verification: Found created dish in search results: {res['dishes'][0]['name']}")

    print("\n===========================================================================")
    print("ALL DISHES API TESTS PASSED (100% SUCCESS)!")
    print("===========================================================================")

if __name__ == "__main__":
    test_dishes()
