"""
FoodSense — Manual Classification Correction & Retraining Export Test Suite
Tests:
  1. POST /api/correct invalid class rejection (400)
  2. POST /api/correct as GUEST (recalculates item & logs correction with user_id=null)
  3. POST /api/correct as AUTHENTICATED USER (recalculates meal & updates stored meal_history record)
  4. POST /api/correct with missed_item addition (adds missed dish to meal analysis)
  5. GET /api/corrections/export (retrieves full logged corrections dataset)
"""

import os
import sys
import time
import json
import requests

BASE_URL = "http://127.0.0.1:3001"


def run_corrections_test():
    print("="*75)
    print("FOODSENSE MANUAL CORRECTION & DATASET EXPORT TEST SUITE")
    print(f"Target Gateway: {BASE_URL}")
    print("="*75)

    all_passed = True

    # 1. Test invalid class rejection
    print("\n[TEST 1] POST /api/correct with invalid class (Expect 400 Bad Request)")
    try:
        r = requests.post(f"{BASE_URL}/api/correct", json={
            "meal_id": "meal_test_01",
            "original_label": "pakode",
            "corrected_label": "invalid_tacos"
        }, timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert r.json().get("error") == "INVALID_CLASS", "Expected INVALID_CLASS error"
        print("-> [PASS] Invalid class properly rejected with 400 Bad Request!")
    except Exception as e:
        print(f"-> [FAIL] Invalid class test failed: {e}")
        all_passed = False

    # 2. Test Guest Correction
    print("\n[TEST 2] POST /api/correct as GUEST (pakode -> dhokla)")
    try:
        r = requests.post(f"{BASE_URL}/api/correct", json={
            "meal_id": "meal_guest_99",
            "original_label": "pakode",
            "corrected_label": "dhokla",
            "bbox": [100, 100, 300, 300]
        }, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("status") == "success", "Expected success status"
        corrected = data.get("corrected_item", {})
        assert corrected.get("label") == "dhokla", "Label mismatch"
        assert corrected.get("macros", {}).get("calories") == 160.0, "Calories mismatch"
        assert corrected.get("healthy_alternative") is not None, "Missing KNN healthy alternative"
        assert data.get("logged_correction", {}).get("user_id") is None, "Guest user_id should be null"
        print("-> [PASS] Guest correction succeeded with recalculated nutrition & KNN alternative!")
    except Exception as e:
        print(f"-> [FAIL] Guest correction failed: {e}")
        all_passed = False

    # 3. Test Authenticated User Correction & History Update
    user_email = f"correct_user_{int(time.time())}@foodsense.ai"
    print(f"\n[TEST 3] Authenticated Correction & History Update (User: {user_email})")
    try:
        # Signup user
        signup_res = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "name": "Correction Tester",
            "email": user_email,
            "password": "Password123!"
        }, timeout=5).json()
        token = signup_res["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Analyze a meal with JWT to auto-save in history
        img_path = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00010.jpg"
        with open(img_path, "rb") as f:
            files = {"image": (os.path.basename(img_path), f, "image/jpeg")}
            analyze_res = requests.post(f"{BASE_URL}/api/analyze", files=files, headers=headers, timeout=15).json()

        meal_id = analyze_res["meal_id"]
        original_items = analyze_res["items"]
        original_cal = analyze_res["meal_summary"]["total_calories"]
        print(f"Original Meal Analyzed: ID={meal_id}, Items={len(original_items)}, Calories={original_cal} kcal")

        # Now correct the first item from 'pakode' to 'idli'
        target_item = original_items[0]
        correct_payload = {
            "meal_id": meal_id,
            "original_label": target_item["label"],
            "corrected_label": "idli",
            "bbox": target_item["bbox"],
            "all_items": original_items
        }

        correct_res = requests.post(f"{BASE_URL}/api/correct", json=correct_payload, headers=headers, timeout=5).json()
        print(f"Correction Result:")
        print(f"  Status: {correct_res.get('status')}")
        print(f"  New Item: {correct_res.get('corrected_item', {}).get('display_name')} ({correct_res.get('corrected_item', {}).get('macros', {}).get('calories')} kcal)")
        print(f"  New Meal Calories: {correct_res.get('meal_summary', {}).get('total_calories')} kcal")

        assert correct_res.get("status") == "success", "Expected success status"
        new_cal = correct_res["meal_summary"]["total_calories"]
        assert new_cal < original_cal, f"Expected calories to drop from {original_cal} when switching pakode (310) to idli (130)"

        # Verify stored history record was updated!
        history_res = requests.get(f"{BASE_URL}/api/history", headers=headers, timeout=5).json()
        saved_meal = history_res["history"][0]
        saved_labels = [it["label"] for it in saved_meal["items"]]
        print(f"Updated Stored History Record: Labels={saved_labels}, Calories={saved_meal['meal_summary']['total_calories']} kcal")
        assert "idli" in saved_labels, "Expected 'idli' in updated history record"
        assert saved_meal["meal_summary"]["total_calories"] == new_cal, "History record meal_summary mismatch"

        print("-> [PASS] Authenticated correction seamlessly updated the stored history record!")
    except Exception as e:
        print(f"-> [FAIL] Authenticated correction failed: {e}")
        all_passed = False

    # 4. Test Missed Item Addition (Add Masala Dosa)
    print("\n[TEST 4] POST /api/correct with missed_item (Adding 'masala_dosa')")
    try:
        missed_payload = {
            "meal_id": meal_id,
            "original_label": "unrecognized",
            "corrected_label": "masala_dosa",
            "correction_type": "missed_item",
            "bbox": [50, 100, 580, 450],
            "all_items": saved_meal["items"]
        }
        add_res = requests.post(f"{BASE_URL}/api/correct", json=missed_payload, headers=headers, timeout=5).json()
        print(f"Missed Item Addition Result:")
        print(f"  Status: {add_res.get('status')}")
        print(f"  Added Item: {add_res.get('corrected_item', {}).get('display_name')} ({add_res.get('corrected_item', {}).get('macros', {}).get('calories')} kcal)")
        print(f"  Total Items Now: {add_res.get('meal_summary', {}).get('total_items')}")
        print(f"  New Meal Calories: {add_res.get('meal_summary', {}).get('total_calories')} kcal")

        assert add_res.get("status") == "success", "Expected success status"
        assert add_res["meal_summary"]["total_items"] == len(saved_meal["items"]) + 1, "Item count should increase"
        assert add_res["logged_correction"]["correction_type"] == "missed_item", "Correction type should be missed_item"

        print("-> [PASS] Missed item added and integrated into whole-meal summary!")
    except Exception as e:
        print(f"-> [FAIL] Missed item addition failed: {e}")
        all_passed = False

    # 5. Test Export Corrections Dataset
    print("\n[TEST 5] GET /api/corrections/export (Exporting Logged Retraining Dataset)")
    try:
        r = requests.get(f"{BASE_URL}/api/corrections/export", timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Total Corrections Logged: {data.get('total_count')}")
        print(f"Sample Export Record: {json.dumps(data.get('corrections', [])[0] if data.get('corrections') else {}, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("total_count", 0) >= 3, "Expected at least 3 logged corrections"
        assert "export_timestamp" in data, "Missing export timestamp"
        print("-> [PASS] Corrections dataset exported successfully!")
    except Exception as e:
        print(f"-> [FAIL] Export corrections failed: {e}")
        all_passed = False

    print("\n" + "="*75)
    if all_passed:
        print("ALL CORRECTION & RECALL TESTS PASSED (100% SUCCESS)!")
    else:
        print("SOME TESTS FAILED! CHECK OUTPUT ABOVE.")
    print("="*75)
    return all_passed


if __name__ == "__main__":
    run_corrections_test()
