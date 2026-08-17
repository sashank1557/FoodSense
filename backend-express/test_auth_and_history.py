"""
FoodSense — Auth & Meal History Backend Test Suite
Tests:
  1. Signup (POST /api/auth/signup)
  2. Duplicate signup rejection (409 Conflict)
  3. Login (POST /api/auth/login)
  4. Bad login rejection (401 Unauthorized)
  5. Profile check (GET /api/auth/me)
  6. Guest Meal Analysis (POST /api/analyze without JWT) -> 200 OK (no history save)
  7. Authenticated Meal Analysis (POST /api/analyze with JWT) -> 200 OK (auto-saved to history)
  8. Meal History List (GET /api/history)
  9. Daily Totals Dashboard (GET /api/history/daily-totals)
  10. Delete Meal Entry (DELETE /api/history/:id)
"""

import os
import sys
import time
import json
import requests

BASE_URL = "http://127.0.0.1:3001"
TEST_USER = {
    "name": "FoodSense Tester",
    "email": f"tester_{int(time.time())}@foodsense.ai",
    "password": "Password123!"
}


def run_auth_history_tests():
    print("="*75)
    print("FOODSENSE AUTH & MEAL HISTORY TEST SUITE")
    print(f"Target Gateway: {BASE_URL}")
    print("="*75)

    all_passed = True
    token = None
    user_id = None

    # 1. Signup
    print(f"\n[TEST 1] POST /api/auth/signup (Email: {TEST_USER['email']})")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/signup", json=TEST_USER, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert r.status_code == 201, f"Expected 201, got {r.status_code}"
        assert "token" in data, "Token missing in signup response"
        token = data["token"]
        user_id = data["user"]["id"]
        print("-> [PASS] User signed up successfully!")
    except Exception as e:
        print(f"-> [FAIL] Signup failed: {e}")
        return False

    # 2. Duplicate Signup Rejection
    print("\n[TEST 2] POST /api/auth/signup (Duplicate Email Rejection - expect 409)")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/signup", json=TEST_USER, timeout=5)
        print(f"Status Code: {r.status_code}")
        assert r.status_code == 409, f"Expected 409, got {r.status_code}"
        print("-> [PASS] Duplicate email rejected with 409 Conflict!")
    except Exception as e:
        print(f"-> [FAIL] Duplicate rejection failed: {e}")
        all_passed = False

    # 3. Login
    print("\n[TEST 3] POST /api/auth/login (Valid Credentials)")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("status") == "success", "Expected success status"
        token = data["token"]
        print("-> [PASS] Login verified and fresh JWT token received!")
    except Exception as e:
        print(f"-> [FAIL] Login failed: {e}")
        all_passed = False

    # 4. Bad Password Rejection
    print("\n[TEST 4] POST /api/auth/login (Invalid Password - expect 401)")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": "WrongPassword!"
        }, timeout=5)
        print(f"Status Code: {r.status_code}")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("-> [PASS] Bad credentials rejected with 401 Unauthorized!")
    except Exception as e:
        print(f"-> [FAIL] Bad login rejection failed: {e}")
        all_passed = False

    # 5. Profile Check
    print("\n[TEST 5] GET /api/auth/me (Protected Route)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data["user"]["email"] == TEST_USER["email"].lower(), "Email mismatch"
        print("-> [PASS] Protected /me route returned authenticated user profile!")
    except Exception as e:
        print(f"-> [FAIL] /me check failed: {e}")
        all_passed = False

    # 6. Guest Meal Analysis (No Token)
    img_path = r"F:\FoodSense\data\yolo_dataset\images\val\meal_val_00010.jpg"
    print(f"\n[TEST 6] POST /api/analyze as GUEST (No Auth Header)")
    try:
        with open(img_path, "rb") as f:
            files = {"image": (os.path.basename(img_path), f, "image/jpeg")}
            r = requests.post(f"{BASE_URL}/api/analyze", files=files, timeout=15)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("saved_to_history") is not True, "Guest meal should not be saved"
        print("-> [PASS] Guest analysis succeeded seamlessly with zero auth requirement!")
    except Exception as e:
        print(f"-> [FAIL] Guest analysis failed: {e}")
        all_passed = False

    # 7. Authenticated Meal Analysis (With JWT Token)
    print(f"\n[TEST 7] POST /api/analyze with JWT (Auto-Save to User History)")
    history_id = None
    try:
        with open(img_path, "rb") as f:
            files = {"image": (os.path.basename(img_path), f, "image/jpeg")}
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.post(f"{BASE_URL}/api/analyze", files=files, headers=headers, timeout=15)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Response (saved_to_history: {data.get('saved_to_history')}, history_id: {data.get('history_id')})")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("saved_to_history") is True, "Expected meal to be auto-saved"
        history_id = data.get("history_id")
        print("-> [PASS] Authenticated meal analysis auto-saved to SQLite database!")
    except Exception as e:
        print(f"-> [FAIL] Authenticated analysis failed: {e}")
        all_passed = False

    # 8. Retrieve Meal History List
    print(f"\n[TEST 8] GET /api/history (Logged-In User History)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/history", headers=headers, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"History Count: {data.get('count')}")
        print(f"Sample History Entry: {json.dumps(data.get('history', [])[0] if data.get('history') else {}, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("count", 0) >= 1, "Expected at least 1 saved meal in history"
        print("-> [PASS] User meal history list retrieved and verified!")
    except Exception as e:
        print(f"-> [FAIL] History retrieval failed: {e}")
        all_passed = False

    # 9. Daily Totals Dashboard Aggregation
    today_str = time.strftime("%Y-%m-%d")
    print(f"\n[TEST 9] GET /api/history/daily-totals?date={today_str}")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/history/daily-totals?date={today_str}", headers=headers, timeout=5)
        print(f"Status Code: {r.status_code}")
        data = r.json()
        print(f"Daily Dashboard Response: {json.dumps(data, indent=2)}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert data.get("total_meals", 0) >= 1, "Expected at least 1 meal today"
        assert "totals" in data, "Missing daily totals aggregate"
        assert data["totals"]["total_calories"] > 0, "Expected positive daily calories"
        print("-> [PASS] Daily totals aggregation computed successfully!")
    except Exception as e:
        print(f"-> [FAIL] Daily totals check failed: {e}")
        all_passed = False

    # 10. Delete Meal Entry
    if history_id:
        print(f"\n[TEST 10] DELETE /api/history/{history_id}")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.delete(f"{BASE_URL}/api/history/{history_id}", headers=headers, timeout=5)
            print(f"Status Code: {r.status_code}")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            print("-> [PASS] Meal entry successfully deleted from history!")
        except Exception as e:
            print(f"-> [FAIL] Delete history failed: {e}")
            all_passed = False

    print("\n" + "="*75)
    if all_passed:
        print("ALL AUTH & MEAL HISTORY TESTS PASSED (100% SUCCESS)!")
    else:
        print("SOME TESTS FAILED! CHECK OUTPUT ABOVE.")
    print("="*75)
    return all_passed


if __name__ == "__main__":
    run_auth_history_tests()
