"""
FoodSense - Hugging Face Dataset Integration Pipeline (rajistics/indian_food_images)
Implements Steps 2 through 7:
- Step 2: Load dataset splits and verify row counts (5.33k train / 941 test)
- Step 3: Export to folder structure: data/train/<class>/<id>.jpg & data/test/<class>/<id>.jpg
- Step 4: Compute class balance summary table & flag low-count classes
- Step 5: Resize to 224x224 and save in data/train_224 & data/test_224 (preserving raw export)
- Step 6: Build exact-keyed nutrition mapping for all classes
- Step 7: Evaluate and finalize 19 vs 20 class list
"""

import os
import sys
import json
import shutil
from collections import Counter
from PIL import Image

# Force Hugging Face cache and temp directories to F: drive
BASE_DIR = r"F:\FoodSense"
CACHE_DIR = os.path.join(BASE_DIR, "hf_cache")
DATA_DIR = os.path.join(BASE_DIR, "data")
TMP_DIR = os.path.join(CACHE_DIR, "tmp")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

os.environ["HF_HOME"] = CACHE_DIR
os.environ["HF_DATASETS_CACHE"] = os.path.join(CACHE_DIR, "datasets")
os.environ["TMPDIR"] = TMP_DIR
os.environ["TEMP"] = TMP_DIR
os.environ["TMP"] = TMP_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import datasets

def step2_load_dataset():
    print("\n" + "="*60)
    print("STEP 2: Loading 'rajistics/indian_food_images' from Hugging Face...")
    print("="*60)
    
    ds = datasets.load_dataset("rajistics/indian_food_images", cache_dir=os.path.join(CACHE_DIR, "datasets"))
    
    train_count = len(ds["train"])
    test_count = len(ds["test"])
    total_count = train_count + test_count
    
    print(f"[Step 2 Result] Train split count: {train_count} rows")
    print(f"[Step 2 Result] Test split count:  {test_count} rows")
    print(f"[Step 2 Result] Total dataset rows: {total_count} rows")
    print(f"[Step 2 Result] Features: {ds['train'].features}")
    
    # Verify label names
    label_feature = ds["train"].features["label"]
    if hasattr(label_feature, "names"):
        class_names = label_feature.names
    else:
        # If ClassLabel not typed, extract unique values
        class_names = sorted(list(set(ds["train"]["label"])))
        
    print(f"[Step 2 Result] Total classes ({len(class_names)}): {class_names}")
    
    assert train_count > 5000, f"Expected ~5.33k train rows, got {train_count}"
    assert test_count > 900, f"Expected ~941 test rows, got {test_count}"
    print("[Step 2 Confirmation] Train and test splits verified successfully!")
    return ds, class_names


def step3_export_folders(ds, class_names):
    print("\n" + "="*60)
    print("STEP 3: Exporting dataset to raw folder structure...")
    print("  -> F:\\FoodSense\\data\\train\\<class_name>\\<id>.jpg")
    print("  -> F:\\FoodSense\\data\\test\\<class_name>\\<id>.jpg")
    print("="*60)
    
    label_names = ds["train"].features["label"].names if hasattr(ds["train"].features["label"], "names") else None
    
    for split_name in ["train", "test"]:
        split_data = ds[split_name]
        split_dir = os.path.join(DATA_DIR, split_name)
        os.makedirs(split_dir, exist_ok=True)
        
        print(f"Exporting {len(split_data)} images for '{split_name}' split...")
        for idx, item in enumerate(split_data):
            # Extract label string
            raw_label = item["label"]
            if label_names and isinstance(raw_label, int):
                class_str = label_names[raw_label]
            else:
                class_str = str(raw_label)
                
            # Clean class folder name
            class_folder = os.path.join(split_dir, class_str)
            os.makedirs(class_folder, exist_ok=True)
            
            # Extract and convert image to RGB
            img = item["image"]
            if isinstance(img, Image.Image):
                if img.mode != "RGB":
                    img = img.convert("RGB")
            else:
                img = Image.open(img).convert("RGB")
                
            img_path = os.path.join(class_folder, f"{split_name}_{idx:05d}.jpg")
            img.save(img_path, "JPEG", quality=95)
            
            if (idx + 1) % 1000 == 0 or (idx + 1) == len(split_data):
                print(f"  Exported {idx + 1}/{len(split_data)} {split_name} images...")
                
    print("[Step 3 Confirmation] Export to raw folder structure complete!")


def step4_check_class_balance():
    print("\n" + "="*60)
    print("STEP 4: Checking Class Balance across Train and Test sets...")
    print("="*60)
    
    train_dir = os.path.join(DATA_DIR, "train")
    test_dir = os.path.join(DATA_DIR, "test")
    
    train_classes = sorted(os.listdir(train_dir))
    test_classes = sorted(os.listdir(test_dir))
    
    train_counts = {}
    test_counts = {}
    total_counts = {}
    
    for c in train_classes:
        c_path = os.path.join(train_dir, c)
        if os.path.isdir(c_path):
            train_counts[c] = len([f for f in os.listdir(c_path) if f.endswith(".jpg")])
            
    for c in test_classes:
        c_path = os.path.join(test_dir, c)
        if os.path.isdir(c_path):
            test_counts[c] = len([f for f in os.listdir(c_path) if f.endswith(".jpg")])
            
    all_classes = sorted(list(set(list(train_counts.keys()) + list(test_counts.keys()))))
    
    for c in all_classes:
        tr = train_counts.get(c, 0)
        te = test_counts.get(c, 0)
        total_counts[c] = tr + te
        
    avg_count = sum(total_counts.values()) / len(total_counts) if total_counts else 0
    
    print(f"\n{'Class Name':<28} | {'Train':>6} | {'Test':>6} | {'Total':>6} | {'% of Dataset':>12} | {'Balance Status'}")
    print("-" * 85)
    
    low_classes = []
    for c in all_classes:
        tr = train_counts.get(c, 0)
        te = test_counts.get(c, 0)
        tot = total_counts.get(c, 0)
        pct = (tot / sum(total_counts.values())) * 100 if sum(total_counts.values()) > 0 else 0
        
        status = "Balanced"
        if tot < (0.6 * avg_count):
            status = "LOW COUNT (Flagged)"
            low_classes.append((c, tot))
        elif tot > (1.5 * avg_count):
            status = "High Count"
            
        print(f"{c:<28} | {tr:>6} | {te:>6} | {tot:>6} | {pct:>11.1f}% | {status}")
        
    print("-" * 85)
    print(f"Total: {len(all_classes)} classes | Train: {sum(train_counts.values())} | Test: {sum(test_counts.values())} | Grand Total: {sum(total_counts.values())}")
    print(f"Average images per class: {avg_count:.1f}")
    
    if low_classes:
        print("\n[Flagged Low-Count Classes for Step 7 Review]:")
        for c, count in low_classes:
            print(f"  * '{c}': {count} total images ({avg_count - count:.1f} below average)")
            
    print("[Step 4 Confirmation] Class balance evaluation complete!")
    return all_classes, train_counts, test_counts, total_counts, low_classes


def step5_resize_and_standardize():
    print("\n" + "="*60)
    print("STEP 5: Resizing & standardizing images to 224x224...")
    print("  -> Raw images preserved in: data/train and data/test")
    print("  -> Resized images saved in: data/train_224 and data/test_224")
    print("="*60)
    
    for split_name in ["train", "test"]:
        src_split_dir = os.path.join(DATA_DIR, split_name)
        dst_split_dir = os.path.join(DATA_DIR, f"{split_name}_224")
        os.makedirs(dst_split_dir, exist_ok=True)
        
        classes = sorted(os.listdir(src_split_dir))
        total_resized = 0
        
        for c in classes:
            src_class_dir = os.path.join(src_split_dir, c)
            if not os.path.isdir(src_class_dir):
                continue
            dst_class_dir = os.path.join(dst_split_dir, c)
            os.makedirs(dst_class_dir, exist_ok=True)
            
            for fname in os.listdir(src_class_dir):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                src_path = os.path.join(src_class_dir, fname)
                dst_path = os.path.join(dst_class_dir, fname)
                
                with Image.open(src_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    # Standard bilinear / bicubic 224x224 resize
                    resized_img = img.resize((224, 224), Image.Resampling.BILINEAR)
                    resized_img.save(dst_path, "JPEG", quality=95)
                    total_resized += 1
                    
        print(f"[Step 5 Result] Successfully resized {total_resized} images to 224x224 in '{dst_split_dir}'")
        
    print("[Step 5 Confirmation] Resizing and standardization complete!")


def step6_build_nutrition_mapping(all_classes):
    print("\n" + "="*60)
    print("STEP 6: Building exact-keyed nutrition mapping for dataset classes...")
    print("="*60)
    
    # Exact lookup dictionary keyed directly on the dataset class strings
    # Providing calories, protein, carbs, fats, fiber, and glycemic index
    dataset_nutrition_table = {
        "biryani": {
            "display_name": "Biryani",
            "category": "Rice Dishes",
            "serving_size": "1 plate (300g)",
            "calories": 450.0, "protein": 14.0, "carbs": 55.0, "fat": 18.0, "fiber": 3.5, "glycemic_index": 65,
            "healthy_alternative": "Quinoa / Brown Rice Biryani"
        },
        "butter_naan": {
            "display_name": "Butter Naan",
            "category": "Breads",
            "serving_size": "1 piece (90g)",
            "calories": 260.0, "protein": 7.0, "carbs": 45.0, "fat": 5.5, "fiber": 1.5, "glycemic_index": 75,
            "healthy_alternative": "Tandoori Whole Wheat Roti"
        },
        "chaat": {
            "display_name": "Chaat (Sev Puri / Papdi)",
            "category": "Snacks",
            "serving_size": "1 plate (150g)",
            "calories": 280.0, "protein": 6.0, "carbs": 38.0, "fat": 12.0, "fiber": 4.0, "glycemic_index": 62,
            "healthy_alternative": "Sprouted Moong Chaat"
        },
        "chappati": {
            "display_name": "Chappati (Roti)",
            "category": "Breads",
            "serving_size": "1 piece (40g)",
            "calories": 120.0, "protein": 3.5, "carbs": 22.0, "fat": 1.5, "fiber": 3.0, "glycemic_index": 62,
            "healthy_alternative": "Jowar / Bajra Phulka"
        },
        "chole_bhature": {
            "display_name": "Chole Bhature",
            "category": "Curries & Breads",
            "serving_size": "1 plate (1 bhatura + 150g chole)",
            "calories": 520.0, "protein": 15.0, "carbs": 62.0, "fat": 24.0, "fiber": 8.0, "glycemic_index": 72,
            "healthy_alternative": "Kala Chana with Missi Roti"
        },
        "dal_makhani": {
            "display_name": "Dal Makhani",
            "category": "Lentils",
            "serving_size": "1 cup (200g)",
            "calories": 310.0, "protein": 11.0, "carbs": 28.0, "fat": 17.0, "fiber": 7.5, "glycemic_index": 42,
            "healthy_alternative": "Yellow Tadka Dal / Sprouted Dal"
        },
        "dhokla": {
            "display_name": "Khaman Dhokla",
            "category": "Breakfast & Snacks",
            "serving_size": "2 pieces (100g)",
            "calories": 160.0, "protein": 6.5, "carbs": 26.0, "fat": 3.0, "fiber": 3.5, "glycemic_index": 45,
            "healthy_alternative": "Steamed Moong Dhokla"
        },
        "fried_rice": {
            "display_name": "Veg Fried Rice",
            "category": "Rice Dishes",
            "serving_size": "1 plate (250g)",
            "calories": 340.0, "protein": 6.5, "carbs": 52.0, "fat": 12.0, "fiber": 3.0, "glycemic_index": 68,
            "healthy_alternative": "Cauliflower Rice / Brown Rice Fried Rice"
        },
        "gulab_jamun": {
            "display_name": "Gulab Jamun",
            "category": "Sweets",
            "serving_size": "2 pieces (80g)",
            "calories": 300.0, "protein": 4.0, "carbs": 48.0, "fat": 10.5, "fiber": 0.5, "glycemic_index": 80,
            "healthy_alternative": "Steamed Sandesh / Fruit Chaat"
        },
        "halwa": {
            "display_name": "Gajar / Sooji Halwa",
            "category": "Sweets",
            "serving_size": "1 bowl (120g)",
            "calories": 330.0, "protein": 4.5, "carbs": 44.0, "fat": 15.0, "fiber": 2.0, "glycemic_index": 72,
            "healthy_alternative": "Lauki (Bottle Gourd) Halwa with Jaggery"
        },
        "idli": {
            "display_name": "Steamed Idli",
            "category": "Breakfast",
            "serving_size": "2 pieces (100g)",
            "calories": 130.0, "protein": 5.0, "carbs": 26.0, "fat": 0.5, "fiber": 2.5, "glycemic_index": 35,
            "healthy_alternative": "Oats / Ragi Idli"
        },
        "jalebi": {
            "display_name": "Jalebi",
            "category": "Sweets",
            "serving_size": "3 pieces (75g)",
            "calories": 290.0, "protein": 2.0, "carbs": 56.0, "fat": 7.0, "fiber": 0.2, "glycemic_index": 82,
            "healthy_alternative": "Dates & Nut Roll"
        },
        "kaathi_rolls": {
            "display_name": "Kathi Roll (Paneer/Veg)",
            "category": "Street Food",
            "serving_size": "1 roll (180g)",
            "calories": 380.0, "protein": 12.0, "carbs": 42.0, "fat": 18.0, "fiber": 3.5, "glycemic_index": 65,
            "healthy_alternative": "Whole Wheat Lettuce Paneer Wrap"
        },
        "kadai_paneer": {
            "display_name": "Kadai Paneer",
            "category": "Curries",
            "serving_size": "1 cup (200g)",
            "calories": 320.0, "protein": 15.0, "carbs": 12.0, "fat": 24.0, "fiber": 3.5, "glycemic_index": 40,
            "healthy_alternative": "Tofu & Bell Pepper Stir-Fry"
        },
        "kulfi": {
            "display_name": "Malai Kulfi",
            "category": "Sweets & Desserts",
            "serving_size": "1 kulfi (80g)",
            "calories": 220.0, "protein": 5.0, "carbs": 24.0, "fat": 12.0, "fiber": 0.2, "glycemic_index": 68,
            "healthy_alternative": "Almond Milk Berry Popsicle"
        },
        "masala_dosa": {
            "display_name": "Masala Dosa",
            "category": "Breakfast",
            "serving_size": "1 piece (140g)",
            "calories": 250.0, "protein": 5.5, "carbs": 40.0, "fat": 8.0, "fiber": 2.8, "glycemic_index": 60,
            "healthy_alternative": "Ragi / Pesarattu Moong Dosa"
        },
        "momos": {
            "display_name": "Veg Steamed Momos",
            "category": "Snacks & Appetizers",
            "serving_size": "6 pieces (150g)",
            "calories": 210.0, "protein": 6.0, "carbs": 36.0, "fat": 4.5, "fiber": 2.5, "glycemic_index": 58,
            "healthy_alternative": "Whole Wheat Steamed Veggie Dimsums"
        },
        "paani_puri": {
            "display_name": "Pani Puri (Gol Gappa)",
            "category": "Street Food & Snacks",
            "serving_size": "6 puris (120g)",
            "calories": 180.0, "protein": 3.5, "carbs": 30.0, "fat": 5.5, "fiber": 2.0, "glycemic_index": 65,
            "healthy_alternative": "Baked Puri Sprout Water Chaat"
        },
        "pakora": {
            "display_name": "Pakora (Bhajiya)",
            "category": "Snacks",
            "serving_size": "1 plate (100g)",
            "calories": 310.0, "protein": 6.0, "carbs": 26.0, "fat": 20.0, "fiber": 3.0, "glycemic_index": 68,
            "healthy_alternative": "Air-Fried Cabbage & Onion Bhaji"
        },
        "pav_bhaji": {
            "display_name": "Pav Bhaji",
            "category": "Street Food & Curries",
            "serving_size": "1 plate (2 pav + 180g bhaji)",
            "calories": 440.0, "protein": 9.0, "carbs": 58.0, "fat": 19.0, "fiber": 6.5, "glycemic_index": 68,
            "healthy_alternative": "Whole Wheat Pav with Low-Butter Veg Bhaji"
        },
        "samosa": {
            "display_name": "Samosa",
            "category": "Snacks",
            "serving_size": "1 piece (80g)",
            "calories": 260.0, "protein": 4.0, "carbs": 28.0, "fat": 15.0, "fiber": 2.0, "glycemic_index": 72,
            "healthy_alternative": "Air-Fried / Baked Paneer Samosa"
        }
    }
    
    # Save the exact nutrition mapping to JSON
    json_path = os.path.join(DATA_DIR, "dataset_nutrition_mapping.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset_nutrition_table, f, indent=2)
        
    print(f"\n{'Dataset Class Key':<20} | {'Display Name':<26} | {'Category':<18} | {'Calories':>8} | {'Protein':>7} | {'Carbs':>6} | {'Fat':>5} | {'GI':>3}")
    print("-" * 105)
    for c in sorted(all_classes):
        if c in dataset_nutrition_table:
            info = dataset_nutrition_table[c]
            print(f"{c:<20} | {info['display_name']:<26} | {info['category']:<18} | {info['calories']:>7.1f}k | {info['protein']:>6.1f}g | {info['carbs']:>5.1f}g | {info['fat']:>4.1f}g | {info['glycemic_index']:>3}")
        else:
            print(f"{c:<20} | [FLAGGED MISSING NUTRITION DATA]")
            
    print(f"\n[Step 6 Confirmation] Nutrition mapping saved to: {json_path}")
    return dataset_nutrition_table


def step7_finalize_class_list(all_classes, total_counts, low_classes):
    print("\n" + "="*60)
    print("STEP 7: Finalizing Class List (19 vs 20 Classes Selection)")
    print("="*60)
    
    # Sort classes by count ascending
    sorted_by_count = sorted([(c, total_counts.get(c, 0)) for c in all_classes], key=lambda x: x[1])
    
    print(f"Total classes found in dataset: {len(all_classes)}")
    print("\nClasses ranked by representation (lowest to highest):")
    for rank, (c, count) in enumerate(sorted_by_count, 1):
        print(f"  {rank:2d}. {c:<22} ({count} images)")
        
    weakest_class, weakest_count = sorted_by_count[0]
    
    # Check if there is an out-of-scope class or if weakest class should be dropped
    print(f"\nAnalysis for 19-class targeting:")
    print(f"  * Default candidate to drop (weakest represented): '{weakest_class}' ({weakest_count} images)")
    
    # Non-traditional Indian or redundant class check:
    # 'fried_rice' is Indo-Chinese, but widely eaten; 'momos' is Tibetan/Indo-Tibetan; 
    # 'kulfi' vs sweets.
    print(f"  * The lowest representation in dataset is '{weakest_class}' with only {weakest_count} images.")
    
    final_19_classes = [c for c, _ in sorted_by_count if c != weakest_class]
    
    print(f"\nRecommended Final 19-Class List (dropping '{weakest_class}'):")
    for idx, c in enumerate(sorted(final_19_classes), 1):
        print(f"  {idx:2d}. {c} ({total_counts.get(c, 0)} images)")
        
    config_output = {
        "all_20_classes": all_classes,
        "recommended_dropped_class": weakest_class,
        "final_19_classes": sorted(final_19_classes),
        "total_images_19_classes": sum(total_counts[c] for c in final_19_classes)
    }
    
    config_path = os.path.join(DATA_DIR, "class_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_output, f, indent=2)
        
    print(f"\n[Step 7 Confirmation] Class configuration exported to: {config_path}")
    return config_output


if __name__ == "__main__":
    # Run Step 2
    ds, class_names = step2_load_dataset()
    
    # Run Step 3
    step3_export_folders(ds, class_names)
    
    # Run Step 4
    all_classes, train_counts, test_counts, total_counts, low_classes = step4_check_class_balance()
    
    # Run Step 5
    step5_resize_and_standardize()
    
    # Run Step 6
    step6_build_nutrition_mapping(all_classes)
    
    # Run Step 7
    step7_finalize_class_list(all_classes, total_counts, low_classes)
