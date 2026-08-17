"""
FoodSense — Express Relay Layer Live HTTP Test Suite
Verifies full chain: Client -> Express (Port 3001) -> Flask (Port 5000) -> Express -> Client

Tests:
  1. GET / (Root endpoint info)
  2. GET /api/health (Unified health relay)
  3. POST /api/analyze (400 validation: missing image)
  4. POST /api/analyze (400 validation: invalid file type)
  5. POST /api/analyze (Multipart upload with field 'image': meal_val_00010.jpg)
  6. POST /api/analyze (Multipart upload with field 'file': meal_val_00014.jpg)
  7. GET /api/analyze/classes (Metadata proxy)
"""

import os
import sys
import time
import json
import io
import requests

EXPRESS_URL = "http://127.0.0.1:3001"


def run_relay_tests():
    print("="*75)
    print("FOODSENSE: EXPRESS RELAY LAYER END-TO-END HTTP TEST SUITE")
    print(f"Target Express Gateway: {EXPRESS_URL}")
    print("="*75)

    all_passed = True

    # 1. Test GET /
    print("\n[TEST 1] GET / (Root Gateway Metadata)")
    try:
        r = requests.get(f"{EXPRESS_URL}/", timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json().get("status") == "online", "Expected status online"
        print("-> [PASS] Root endpoint online!")
    except Exception as e:
        print(f"-> [FAIL] Root check failed: {e}")
        all_passed = False

    # 2. Test GET /api/health
    print("\n[TEST 2] GET /api/health (Unified Express + Flask Health Check)")
    try:
        start_t = time.time()
        r = requests.get(f"{EXPRESS_URL}/api/health", timeout=5)
        latency_ms = round((time.time() - start_t) * 1000, 2)
        print(f"Status Code: {r.status_code} (Latency: {latency_ms}ms)")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("status") == "healthy", "Expected healthy status"
        assert data.get("upstream_flask", {}).get("status") == "healthy", "Flask upstream not healthy"
        print("-> [PASS] Unified health relay verified!")
    except Exception as e:
        print(f"-> [FAIL] Health check relay failed: {e}")
        all_passed = False

    # 3. Test POST /api/analyze (No file provided)
    print("\n[TEST 3] POST /api/analyze (Missing Image Error Handling)")
    try:
        r = requests.post(f"{EXPRESS_URL}/api/analyze", data={}, timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert r.json().get("status") == "error", "Expected error status"
        print("-> [PASS] Missing image error response verified (400 Bad Request)!")
    except Exception as e:
        print(f"-> [FAIL] Missing image validation failed: {e}")
        all_passed = False

    # 4. Test POST /api/analyze (Invalid file type rejection)
    print("\n[TEST 4] POST /api/analyze (Invalid File Type Error Handling)")
    try:
        dummy_txt = io.BytesIO(b"This is not a food image file.")
        files = {"image": ("test_doc.txt", dummy_txt, "text/plain")}
        r = requests.post(f"{EXPRESS_URL}/api/analyze", files=files, timeout=5)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        print("-> [PASS] Non-image rejection verified (400 Bad Request)!")
    except Exception as e:
        print(f"-> [FAIL] Invalid file type validation failed: {e}")
        all_passed = False

    # 5. Test POST /api/analyze with multi-item meal (field: 'image')
    img1_path = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00010.jpg"
    print(f"\n[TEST 5] POST /api/analyze (Multipart 'image' field with {os.path.basename(img1_path)})")
    try:
        with open(img1_path, "rb") as f:
            files = {"image": (os.path.basename(img1_path), f, "image/jpeg")}
            start_t = time.time()
            r = requests.post(f"{EXPRESS_URL}/api/analyze", files=files, timeout=15)
            roundtrip_ms = round((time.time() - start_t) * 1000, 2)

        print(f"Status Code: {r.status_code} (End-to-End Roundtrip: {roundtrip_ms}ms)")
        res = r.json()
        print(f"Relayed Response JSON:")
        print(json.dumps(res, indent=2))
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert res.get("status") == "success", "Expected success status"
        assert len(res.get("items", [])) >= 1, "Expected at least 1 detected item"
        assert "meal_summary" in res, "Missing meal_summary"
        print("-> [PASS] Full Client -> Express -> Flask -> Client relay verified!")
    except Exception as e:
        print(f"-> [FAIL] End-to-end relay test 5 failed: {e}")
        all_passed = False

    # 6. Test POST /api/analyze with multi-item meal (field: 'file')
    img2_path = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00014.jpg"
    print(f"\n[TEST 6] POST /api/analyze (Multipart 'file' field with {os.path.basename(img2_path)})")
    try:
        with open(img2_path, "rb") as f:
            files = {"file": (os.path.basename(img2_path), f, "image/jpeg")}
            start_t = time.time()
            r = requests.post(f"{EXPRESS_URL}/api/analyze", files=files, timeout=15)
            roundtrip_ms = round((time.time() - start_t) * 1000, 2)

        print(f"Status Code: {r.status_code} (End-to-End Roundtrip: {roundtrip_ms}ms)")
        res = r.json()
        print(f"Relayed Response JSON:")
        print(json.dumps(res, indent=2))
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert res.get("status") == "success", "Expected success status"
        assert "meal_summary" in res, "Missing meal_summary"
        print("-> [PASS] Alternate field upload relay verified!")
    except Exception as e:
        print(f"-> [FAIL] End-to-end relay test 6 failed: {e}")
        all_passed = False

    # 7. Test GET /api/analyze/classes
    print("\n[TEST 7] GET /api/analyze/classes (Metadata Proxy)")
    try:
        r = requests.get(f"{EXPRESS_URL}/api/analyze/classes", timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Supported classes count: {len(data.get('classes', []))}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert len(data.get("classes", [])) == 20, "Expected 20 classes"
        print("-> [PASS] Classes proxy verified!")
    except Exception as e:
        print(f"-> [FAIL] Classes proxy failed: {e}")
        all_passed = False

    print("\n" + "="*75)
    if all_passed:
        print("ALL EXPRESS RELAY TESTS PASSED (100% SUCCESS)!")
    else:
        print("SOME TESTS FAILED! CHECK OUTPUT ABOVE.")
    print("="*75)
    return all_passed


if __name__ == "__main__":
    run_relay_tests()
