"""
Test and tune the composite KNN ranking formula across all 20 classes.
"""
import json
import numpy as np

with open(r"F:\FoodSense\data\knn_candidates_db.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

with open(r"F:\FoodSense\data\knn_feature_scaler.json", "r", encoding="utf-8") as f:
    scaler_info = json.load(f)
    scalers = scaler_info["scalers"]

FEATURE_KEYS = ["calories", "protein", "carbs", "fat", "fiber", "glycemic_index"]

def normalize(item):
    vec = []
    for k in FEATURE_KEYS:
        val = float(item[k])
        s = scalers[k]
        norm = (val - s["min"]) / (s["max"] - s["min"] + 1e-6)
        vec.append(np.clip(norm, 0.0, 1.0))
    return np.array(vec, dtype=np.float32)

items_by_id = {c["id"]: c for c in candidates}

test_classes = ["fried_rice", "pizza", "chai", "pakode", "butter_naan", "dal_makhani", "chole_bhature", "idli", "jalebi"]

print("="*80)
print("EVALUATING KNN RANKING FORMULA ACROSS 20 CLASSES")
print("="*80)

for cid in test_classes:
    base = items_by_id.get(cid)
    if not base:
        continue
    base_vec = normalize(base)
    base_cat = base["category"]
    
    pool = []
    for cand in candidates:
        if cand["id"] == cid or cand["category"] != base_cat:
            continue
        
        cal_diff = cand["calories"] - base["calories"]
        fat_diff = cand["fat"] - base["fat"]
        prot_diff = cand["protein"] - base["protein"]
        fiber_diff = cand["fiber"] - base["fiber"]
        gi_diff = cand["glycemic_index"] - base["glycemic_index"]
        
        # Health filter: must be healthier
        if not (cal_diff <= -15 or fat_diff <= -2.0 or gi_diff <= -10 or prot_diff >= 2.5):
            continue
            
        cand_vec = normalize(cand)
        dist = float(np.linalg.norm(base_vec - cand_vec))
        
        cal_save = max(0.0, -cal_diff / (base["calories"] + 1e-6))
        fat_save = max(0.0, -fat_diff / (base["fat"] + 1e-6))
        gi_save = max(0.0, -gi_diff / (base["glycemic_index"] + 1e-6))
        
        # Balance formula: distance + health reward
        rank_score = dist - (0.65 * cal_save + 0.50 * fat_save + 0.25 * gi_save)
        
        pool.append({
            "name": cand["name"],
            "calories": cand["calories"],
            "fat": cand["fat"],
            "gi": cand["glycemic_index"],
            "dist": dist,
            "score": rank_score
        })
    
    pool.sort(key=lambda x: x["score"])
    print(f"\nTarget: {base['name']} ({base['calories']:.0f} kcal, {base['fat']:.1f}g fat, GI: {base['glycemic_index']})")
    for i, r in enumerate(pool[:2], 1):
        print(f"  #{i} -> {r['name']:<50} | {r['calories']:.0f} kcal | {r['fat']:.1f}g fat | GI {r['gi']} (Score: {r['score']:.3f}, Dist: {r['dist']:.3f})")
