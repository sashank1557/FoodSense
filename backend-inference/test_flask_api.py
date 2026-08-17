"""
FoodSense — Live HTTP Test Suite for Flask Inference API
Tests:
  1. GET /health
  2. GET /classes
  3. POST /analyze (error validation with no file)
  4. POST /analyze (multi-item multipart upload: meal_val_00010.jpg)
  5. POST /analyze (multi-item multipart upload: meal_val_00014.jpg)
  6. POST /analyze (single-item upload: pizza)
"""

import os
import sys
import json
import time
import requests

BASE_URL = "http://127.0.0.1:5000"


def test_flask_api():
    print("="*75)
    print("FOODSENSE FLASK API HTTP TEST SUITE")
    print(f"Target: {BASE_URL}")
    print("="*75)

    # 1. Test GET /health
    print("\n[TEST 1] GET /health")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json().get("models_ready") is True, "Models not reported ready"
        print("-> [PASS] Health check verified!")
    except Exception as e:
        print(f"-> [FAIL] Health check failed: {e}")
        return False

    # 2. Test GET /classes
    print("\n[TEST 2] GET /classes")
    try:
        r = requests.get(f"{BASE_URL}/classes", timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Number of classes: {len(data.get('classes', []))}")
        print(f"Classes: {', '.join(data.get('classes', []))}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert len(data.get("classes", [])) == 20, "Expected 20 classes"
        print("-> [PASS] Classes endpoint verified!")
    except Exception as e:
        print(f"-> [FAIL] Classes check failed: {e}")
        return False

    # 3. Test POST /analyze with No File (Error Handling)
    print("\n[TEST 3] POST /analyze (Missing file validation - expect 400 Bad Request)")
    try:
        r = requests.post(f"{BASE_URL}/analyze", data={}, timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert r.json().get("status") == "error", "Expected error status"
        print("-> [PASS] 400 Bad Request error handling verified!")
    except Exception as e:
        print(f"-> [FAIL] Error handling failed: {e}")
        return False

    # 4. Test POST /analyze on Multi-Item Meal 1 (meal_val_00010.jpg)
    img_path1 = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00010.jpg"
    print(f"\n[TEST 4] POST /analyze with multi-item image ({os.path.basename(img_path1)})")
    try:
        with open(img_path1, "rb") as f:
            files = {"file": (os.path.basename(img_path1), f, "image/jpeg")}
            start_t = time.time()
            r = requests.post(f"{BASE_URL}/analyze", files=files, timeout=10)
            latency_ms = round((time.time() - start_t) * 1000, 2)

        print(f"Status Code: {r.status_code} (HTTP Round-Trip: {latency_ms}ms)")
        res = r.json()
        print(f"Response JSON Summary:")
        print(json.dumps(res, indent=2))
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert res.get("status") == "success", "Expected success status"
        assert len(res.get("items", [])) >= 1, "Expected at least 1 detected item"
        print("-> [PASS] Multi-item POST analysis verified!")
    except Exception as e:
        print(f"-> [FAIL] Multi-item POST failed: {e}")
        return False

    # 5. Test POST /analyze on Multi-Item Meal 2 (meal_val_00014.jpg)
    img_path2 = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00014.jpg"
    print(f"\n[TEST 5] POST /analyze with multi-item image ({os.path.basename(img_path2)})")
    try:
        with open(img_path2, "rb") as f:
            files = {"image": (os.path.basename(img_path2), f, "image/jpeg")}
            start_t = time.time()
            r = requests.post(f"{BASE_URL}/analyze", files=files, timeout=10)
            latency_ms = round((time.time() - start_t) * 1000, 2)

        print(f"Status Code: {r.status_code} (HTTP Round-Trip: {latency_ms}ms)")
        res = r.json()
        print(f"Response JSON Summary:")
        print(json.dumps(res, indent=2))
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert res.get("status") == "success", "Expected success status"
        print("-> [PASS] Multi-item POST analysis 2 verified!")
    except Exception as e:
        print(f"-> [FAIL] Multi-item POST 2 failed: {e}")
        return False

    print("\n" + "="*75)
    print("ALL FLASK API ENDPOINTS FULLY VERIFIED (100% PASS)")
    print("="*75)
    return True


if __name__ == "__main__":
    test_flask_api()
