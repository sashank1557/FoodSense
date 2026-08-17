"""
FoodSense - Hugging Face Dataset Integration & Preprocessing Pipeline
Dataset: rajistics/indian_food_images
"""

import os
import sys
import io
import json
from collections import Counter
from PIL import Image
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

BASE_DIR = r"F:\FoodSense"
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_PARQUET_DIR = os.path.join(DATA_DIR, "raw_parquet")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
TEST_DIR = os.path.join(DATA_DIR, "test")
TRAIN_224_DIR = os.path.join(DATA_DIR, "train_224")
TEST_224_DIR = os.path.join(DATA_DIR, "test_224")

for d in [DATA_DIR, RAW_PARQUET_DIR, TRAIN_DIR, TEST_DIR, TRAIN_224_DIR, TEST_224_DIR]:
    os.makedirs(d, exist_ok=True)

# Exact 20 class names defined in rajistics/indian_food_images dataset_infos.json
CLASS_NAMES_20 = [
    "burger",
    "butter_naan",
    "chai",
    "chapati",
    "chole_bhature",
    "dal_makhani",
    "dhokla",
    "fried_rice",
    "idli",
    "jalebi",
    "kaathi_rolls",
    "kadai_paneer",
    "kulfi",
    "masala_dosa",
    "momos",
    "paani_puri",
    "pakode",
    "pav_bhaji",
    "pizza",
    "samosa"
]

def step2_load_dataset():
    print("\n" + "="*70)
    print("STEP 2: Loading 'rajistics/indian_food_images' from Hugging Face")
    print("="*70)
    
    print("Downloading train parquet file...")
    train_parquet_path = hf_hub_download(
        "rajistics/indian_food_images",
        filename="data/train-00000-of-00001-dbae6752a5d31c49.parquet",
        repo_type="dataset",
        local_dir=RAW_PARQUET_DIR
    )
    
    print("Downloading test parquet file...")
    test_parquet_path = hf_hub_download(
        "rajistics/indian_food_images",
        filename="data/test-00000-of-00001-899c7c7e401d279b.parquet",
        repo_type="dataset",
        local_dir=RAW_PARQUET_DIR
    )
    
    train_pf = pq.ParquetFile(train_parquet_path)
    test_pf = pq.ParquetFile(test_parquet_path)
    
    train_count = train_pf.metadata.num_rows
    test_count = test_pf.metadata.num_rows
    total_count = train_count + test_count
    
    print(f"[Step 2 Result] Train Split Row Count: {train_count} rows (Expected ~5.33k)")
    print(f"[Step 2 Result] Test Split Row Count:  {test_count} rows (Expected 941)")
    print(f"[Step 2 Result] Total Row Count:       {total_count} rows (Expected 6.27k)")
    print(f"[Step 2 Result] 20 Class Names:        {CLASS_NAMES_20}")
    
    assert train_count == 5328, f"Expected 5328 train rows, got {train_count}"
    assert test_count == 941, f"Expected 941 test rows, got {test_count}"
    assert len(CLASS_NAMES_20) == 20, f"Expected 20 classes, got {len(CLASS_NAMES_20)}"
    
    print("[Step 2 Confirmation] Verified: Train = 5,328 (5.33k) | Test = 941 | Total = 6,269 (6.27k) | 20 Classes")
    return train_parquet_path, test_parquet_path


def step3_export_to_folders(train_path, test_path):
    print("\n" + "="*70)
    print("STEP 3: Exporting dataset to raw folder structure")
    print("  Destination: data/train/<class_name>/<id>.jpg")
    print("  Destination: data/test/<class_name>/<id>.jpg")
    print("="*70)
    
    splits = [
        ("test", test_path, TEST_DIR),
        ("train", train_path, TRAIN_DIR)
    ]
    
    for split_name, parquet_path, target_dir in splits:
        pf = pq.ParquetFile(parquet_path)
        total_rows = pf.metadata.num_rows
        print(f"Processing '{split_name}' split ({total_rows} images) via streaming batches...")
        
        exported_count = 0
        for batch in pf.iter_batches(batch_size=64):
            # Batch has columns: 'image' (struct with 'bytes' and 'path') and 'label' (int64)
            pydict = batch.to_pydict()
            images_raw = pydict["image"]
            labels = pydict["label"]
            
            for img_dict, label_idx in zip(images_raw, labels):
                class_name = CLASS_NAMES_20[label_idx]
                class_folder = os.path.join(target_dir, class_name)
                os.makedirs(class_folder, exist_ok=True)
                
                img_bytes = img_dict.get("bytes")
                if not img_bytes:
                    continue
                    
                # Open image with PIL, convert mode to RGB
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                        
                    img_filename = f"{split_name}_{exported_count:05d}.jpg"
                    img_save_path = os.path.join(class_folder, img_filename)
                    img.save(img_save_path, "JPEG", quality=95)
                    exported_count += 1
                except Exception as e:
                    print(f"Warning: could not process image {exported_count} in {split_name}: {e}")
                    
            if exported_count % 1000 == 0 or exported_count == total_rows:
                print(f"  Exported {exported_count}/{total_rows} {split_name} images...")
                
        print(f"[Step 3 Result] Finished '{split_name}' export: {exported_count} images saved.")
        
    print("[Step 3 Confirmation] Export to folder structure completed successfully!")


def step4_check_class_balance():
    print("\n" + "="*70)
    print("STEP 4: Checking Class Balance across Train and Test sets")
    print("="*70)
    
    train_counts = {}
    test_counts = {}
    total_counts = {}
    
    for c in CLASS_NAMES_20:
        c_train_dir = os.path.join(TRAIN_DIR, c)
        c_test_dir = os.path.join(TEST_DIR, c)
        
        tr = len([f for f in os.listdir(c_train_dir) if f.endswith(".jpg")]) if os.path.exists(c_train_dir) else 0
        te = len([f for f in os.listdir(c_test_dir) if f.endswith(".jpg")]) if os.path.exists(c_test_dir) else 0
        
        train_counts[c] = tr
        test_counts[c] = te
        total_counts[c] = tr + te
        
    grand_total = sum(total_counts.values())
    avg_per_class = grand_total / len(CLASS_NAMES_20)
    
    print(f"{'Class Name':<20} | {'Train':>6} | {'Test':>6} | {'Total':>6} | {'% of Dataset':>12} | {'Balance Status'}")
    print("-" * 80)
    
    low_classes = []
    for c in sorted(CLASS_NAMES_20, key=lambda x: total_counts[x], reverse=True):
        tr = train_counts[c]
        te = test_counts[c]
        tot = total_counts[c]
        pct = (tot / grand_total) * 100 if grand_total > 0 else 0
        
        # Check if significantly low (< 60% of average)
        if tot < (0.65 * avg_per_class):
            status = "[FLAGGED LOW COUNT]"
            low_classes.append((c, tot))
        elif tot > (1.35 * avg_per_class):
            status = "High Count"
        else:
            status = "Balanced"
            
        print(f"{c:<20} | {tr:>6} | {te:>6} | {tot:>6} | {pct:>11.1f}% | {status}")
        
    print("-" * 80)
    print(f"Total 20 Classes    | {sum(train_counts.values()):>6} | {sum(test_counts.values()):>6} | {grand_total:>6} | {'100.0%':>12} | Avg: {avg_per_class:.1f}/class")
    
    if low_classes:
        print("\nFlagged Low-Count Classes:")
        for c, count in low_classes:
            print(f"  * '{c}': {count} images ({avg_per_class - count:.1f} below average)")
            
    print("\n[Step 4 Confirmation] Class balance analysis complete!")
    return train_counts, test_counts, total_counts, low_classes


def step5_resize_and_standardize():
    print("\n" + "="*70)
    print("STEP 5: Resizing and Standardizing all images to 224x224")
    print("  -> Raw export preserved in: data/train and data/test")
    print("  -> Preprocessed 224x224 saved in: data/train_224 and data/test_224")
    print("="*70)
    
    splits = [
        ("test", TEST_DIR, TEST_224_DIR),
        ("train", TRAIN_DIR, TRAIN_224_DIR)
    ]
    
    for split_name, src_dir, dst_dir in splits:
        total_resized = 0
        classes = sorted(os.listdir(src_dir))
        for c in classes:
            c_src = os.path.join(src_dir, c)
            c_dst = os.path.join(dst_dir, c)
            os.makedirs(c_dst, exist_ok=True)
            
            for fname in os.listdir(c_src):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                src_file = os.path.join(c_src, fname)
                dst_file = os.path.join(c_dst, fname)
                
                with Image.open(src_file) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    resized = img.resize((224, 224), Image.Resampling.BILINEAR)
                    resized.save(dst_file, "JPEG", quality=95)
                    total_resized += 1
                    
        print(f"[Step 5 Result] Successfully resized {total_resized} images to 224x224 in '{split_name}_224'")
        
    print("[Step 5 Confirmation] Resizing and standardization to 224x224 completed!")


def step6_build_nutrition_mapping():
    print("\n" + "="*70)
    print("STEP 6: Building Nutrition Lookup Table Keyed on Exact Dataset Class Strings")
    print("="*70)
    
    # Nutrition profile dictionary keyed on exact dataset class names
    nutrition_lookup = {
        "burger": {
            "display_name": "Veg Burger (Aloo Tikki Burger)",
            "category": "Fast Food",
            "serving_size": "1 burger (150g)",
            "serving_weight_g": 150,
            "calories": 320.0, "protein": 7.5, "carbs": 44.0, "fat": 13.0, "fiber": 3.0, "glycemic_index": 70,
            "description": "Spiced potato patty inside a toasted bun with mayo and lettuce.",
            "healthy_alternative": {
                "name": "Whole Wheat Paneer / Soya Patty Burger",
                "calories": 240.0, "protein": 14.0, "carbs": 28.0, "fat": 6.0, "fiber": 5.5, "glycemic_index": 48,
                "reason": "Uses whole grain bun and grilled protein patty cutting calories and saturated fats."
            }
        },
        "butter_naan": {
            "display_name": "Butter Naan",
            "category": "Breads",
            "serving_size": "1 piece (90g)",
            "serving_weight_g": 90,
            "calories": 260.0, "protein": 7.0, "carbs": 45.0, "fat": 5.5, "fiber": 1.5, "glycemic_index": 75,
            "description": "Leavened tandoor-baked maida flatbread brushed with butter.",
            "healthy_alternative": {
                "name": "Tandoori Whole Wheat Roti",
                "calories": 130.0, "protein": 4.5, "carbs": 24.0, "fat": 1.8, "fiber": 3.8, "glycemic_index": 55,
                "reason": "Saves 130 kcal and 21g refined carbs; baked with unrefined whole wheat."
            }
        },
        "chai": {
            "display_name": "Masala Chai (with Milk & Sugar)",
            "category": "Beverages",
            "serving_size": "1 cup (150ml)",
            "serving_weight_g": 150,
            "calories": 90.0, "protein": 3.0, "carbs": 12.0, "fat": 3.5, "fiber": 0.0, "glycemic_index": 60,
            "description": "Black tea brewed with milk, cardamom, ginger, and sugar.",
            "healthy_alternative": {
                "name": "Unsweetened Spiced Green Tea / Herbal Tulsi Chai",
                "calories": 15.0, "protein": 0.5, "carbs": 2.0, "fat": 0.2, "fiber": 0.0, "glycemic_index": 15,
                "reason": "High antioxidant herbal blend without refined sugar or dairy fats."
            }
        },
        "chapati": {
            "display_name": "Chapati (Roti)",
            "category": "Breads",
            "serving_size": "1 piece (40g)",
            "serving_weight_g": 40,
            "calories": 120.0, "protein": 3.5, "carbs": 22.0, "fat": 1.5, "fiber": 3.0, "glycemic_index": 62,
            "description": "Whole wheat unleavened flatbread cooked on a griddle.",
            "healthy_alternative": {
                "name": "Jowar / Bajra Millet Roti",
                "calories": 95.0, "protein": 3.8, "carbs": 18.0, "fat": 1.0, "fiber": 4.5, "glycemic_index": 48,
                "reason": "Gluten-free millet bread with 50% more fiber and lower glycemic response."
            }
        },
        "chole_bhature": {
            "display_name": "Chole Bhature",
            "category": "Curries & Fried Breads",
            "serving_size": "1 bhatura (80g) + 150g chole",
            "serving_weight_g": 230,
            "calories": 520.0, "protein": 15.0, "carbs": 62.0, "fat": 24.0, "fiber": 8.0, "glycemic_index": 72,
            "description": "Spiced chickpea curry paired with deep-fried leavened sourdough bread.",
            "healthy_alternative": {
                "name": "Boiled Kala Chana Masala + Missi Roti",
                "calories": 280.0, "protein": 16.0, "carbs": 38.0, "fat": 5.0, "fiber": 10.0, "glycemic_index": 35,
                "reason": "Eliminates deep-fried maida bhatura while boosting fiber and gut health."
            }
        },
        "dal_makhani": {
            "display_name": "Dal Makhani",
            "category": "Lentils",
            "serving_size": "1 cup (200g)",
            "serving_weight_g": 200,
            "calories": 310.0, "protein": 11.0, "carbs": 28.0, "fat": 17.0, "fiber": 7.5, "glycemic_index": 42,
            "description": "Slow-cooked black lentils (urad) and kidney beans enriched with butter and cream.",
            "healthy_alternative": {
                "name": "Yellow Dal Tadka / Sprouted Moong Dal",
                "calories": 160.0, "protein": 9.5, "carbs": 22.0, "fat": 4.0, "fiber": 6.5, "glycemic_index": 32,
                "reason": "Low saturated fat preparation delivering clean plant protein."
            }
        },
        "dhokla": {
            "display_name": "Khaman Dhokla",
            "category": "Breakfast & Snacks",
            "serving_size": "2 pieces (100g)",
            "serving_weight_g": 100,
            "calories": 160.0, "protein": 6.5, "carbs": 26.0, "fat": 3.0, "fiber": 3.5, "glycemic_index": 45,
            "description": "Steamed savory fermented gram flour sponge tempered with mustard seeds.",
            "healthy_alternative": {
                "name": "Sprouted Moong & Spinach Dhokla",
                "calories": 125.0, "protein": 8.0, "carbs": 18.0, "fat": 1.5, "fiber": 5.0, "glycemic_index": 32,
                "reason": "Sprouting increases bioavailability of folate, iron, and dietary fiber."
            }
        },
        "fried_rice": {
            "display_name": "Veg Fried Rice",
            "category": "Rice Dishes",
            "serving_size": "1 plate (250g)",
            "serving_weight_g": 250,
            "calories": 340.0, "protein": 6.5, "carbs": 52.0, "fat": 12.0, "fiber": 3.0, "glycemic_index": 68,
            "description": "Wok-tossed rice with shredded vegetables, soy sauce, and oil.",
            "healthy_alternative": {
                "name": "Cauliflower / Brown Rice Stir-Fry",
                "calories": 180.0, "protein": 7.0, "carbs": 24.0, "fat": 4.5, "fiber": 6.0, "glycemic_index": 40,
                "reason": "Replaces refined white rice with high-fiber cauliflower or unpolished brown grain."
            }
        },
        "idli": {
            "display_name": "Steamed Idli",
            "category": "Breakfast",
            "serving_size": "2 pieces (100g)",
            "serving_weight_g": 100,
            "calories": 130.0, "protein": 5.0, "carbs": 26.0, "fat": 0.5, "fiber": 2.5, "glycemic_index": 35,
            "description": "Steamed savory cakes made from fermented rice and black lentil batter.",
            "healthy_alternative": {
                "name": "Oats & Ragi Idli",
                "calories": 115.0, "protein": 6.0, "carbs": 20.0, "fat": 1.0, "fiber": 4.5, "glycemic_index": 28,
                "reason": "Enriched with beta-glucan and calcium for optimal metabolic health."
            }
        },
        "jalebi": {
            "display_name": "Jalebi",
            "category": "Sweets",
            "serving_size": "3 pieces (75g)",
            "serving_weight_g": 75,
            "calories": 290.0, "protein": 2.0, "carbs": 56.0, "fat": 7.0, "fiber": 0.2, "glycemic_index": 82,
            "description": "Deep-fried spiral maida flour coils soaked in concentrated saffron sugar syrup.",
            "healthy_alternative": {
                "name": "Dates & Fig Delight (No Refined Sugar)",
                "calories": 100.0, "protein": 2.5, "carbs": 20.0, "fat": 1.0, "fiber": 3.5, "glycemic_index": 40,
                "reason": "Natural fruit sweetness rich in potassium and micronutrients."
            }
        },
        "kaathi_rolls": {
            "display_name": "Kathi Roll (Paneer / Veg Roll)",
            "category": "Street Food",
            "serving_size": "1 roll (180g)",
            "serving_weight_g": 180,
            "calories": 380.0, "protein": 12.0, "carbs": 42.0, "fat": 18.0, "fiber": 3.5, "glycemic_index": 65,
            "description": "Paratha flatbread rolled with spiced vegetables or paneer filling.",
            "healthy_alternative": {
                "name": "Whole Wheat Tofu & Crunchy Veg Wrap",
                "calories": 220.0, "protein": 15.0, "carbs": 26.0, "fat": 5.5, "fiber": 6.0, "glycemic_index": 42,
                "reason": "Oil-free whole wheat wrap with high plant-based protein."
            }
        },
        "kadai_paneer": {
            "display_name": "Kadai Paneer",
            "category": "Curries",
            "serving_size": "1 cup (200g)",
            "serving_weight_g": 200,
            "calories": 320.0, "protein": 15.0, "carbs": 12.0, "fat": 24.0, "fiber": 3.5, "glycemic_index": 40,
            "description": "Cottage cheese cubes and bell peppers tossed in a freshly ground coriander-spice gravy.",
            "healthy_alternative": {
                "name": "Kadai Tofu with Tri-Color Peppers",
                "calories": 180.0, "protein": 16.0, "carbs": 10.0, "fat": 8.0, "fiber": 4.5, "glycemic_index": 30,
                "reason": "Reduces saturated fat by 65% while providing complete plant protein."
            }
        },
        "kulfi": {
            "display_name": "Malai Kulfi",
            "category": "Sweets & Desserts",
            "serving_size": "1 kulfi (80g)",
            "serving_weight_g": 80,
            "calories": 220.0, "protein": 5.0, "carbs": 24.0, "fat": 12.0, "fiber": 0.2, "glycemic_index": 68,
            "description": "Dense frozen dairy dessert flavored with cardamom, saffron, and pistachios.",
            "healthy_alternative": {
                "name": "Almond Milk Frozen Fruit Popsicle",
                "calories": 85.0, "protein": 2.5, "carbs": 14.0, "fat": 2.0, "fiber": 2.0, "glycemic_index": 38,
                "reason": "Dairy-free, vitamin E rich treat with 60% fewer calories."
            }
        },
        "masala_dosa": {
            "display_name": "Masala Dosa",
            "category": "Breakfast",
            "serving_size": "1 dosa with potato masala (140g)",
            "serving_weight_g": 140,
            "calories": 250.0, "protein": 5.5, "carbs": 40.0, "fat": 8.0, "fiber": 2.8, "glycemic_index": 60,
            "description": "Crisp fermented rice-lentil crepe filled with spiced mashed potatoes.",
            "healthy_alternative": {
                "name": "Moong Dal Pesarattu with Vegetable Upma Filling",
                "calories": 180.0, "protein": 11.0, "carbs": 26.0, "fat": 3.5, "fiber": 5.5, "glycemic_index": 38,
                "reason": "Doubles protein content and prevents sudden postprandial glucose spikes."
            }
        },
        "momos": {
            "display_name": "Steamed Veg Momos",
            "category": "Snacks & Appetizers",
            "serving_size": "6 pieces (150g)",
            "serving_weight_g": 150,
            "calories": 210.0, "protein": 6.0, "carbs": 36.0, "fat": 4.5, "fiber": 2.5, "glycemic_index": 58,
            "description": "Steamed flour dumplings filled with finely chopped cabbage, carrots, and onions.",
            "healthy_alternative": {
                "name": "Whole Wheat Veggie Dimsums",
                "calories": 160.0, "protein": 7.0, "carbs": 28.0, "fat": 1.5, "fiber": 4.5, "glycemic_index": 45,
                "reason": "100% steamed whole wheat skin packed with fiber and antioxidant vegetables."
            }
        },
        "paani_puri": {
            "display_name": "Pani Puri (Gol Gappa)",
            "category": "Street Food",
            "serving_size": "6 puris (120g)",
            "serving_weight_g": 120,
            "calories": 180.0, "protein": 3.5, "carbs": 30.0, "fat": 5.5, "fiber": 2.0, "glycemic_index": 65,
            "description": "Crisp fried hollow puris stuffed with boiled potato, chickpeas, and mint-tamarind water.",
            "healthy_alternative": {
                "name": "Air-Baked Puris with Sprouted Moong Filling",
                "calories": 110.0, "protein": 6.0, "carbs": 20.0, "fat": 1.0, "fiber": 4.5, "glycemic_index": 42,
                "reason": "Non-fried puris with live sprouts for higher micronutrient density."
            }
        },
        "pakode": {
            "display_name": "Pakode (Vegetable Pakora)",
            "category": "Snacks",
            "serving_size": "1 plate (100g)",
            "serving_weight_g": 100,
            "calories": 310.0, "protein": 6.0, "carbs": 26.0, "fat": 20.0, "fiber": 3.0, "glycemic_index": 68,
            "description": "Onions and vegetables coated in spiced chickpea batter and deep-fried.",
            "healthy_alternative": {
                "name": "Air-Fried Cabbage & Onion Fritters",
                "calories": 140.0, "protein": 6.5, "carbs": 20.0, "fat": 4.0, "fiber": 4.5, "glycemic_index": 48,
                "reason": "Retains crisp texture with 80% less oil absorption."
            }
        },
        "pav_bhaji": {
            "display_name": "Pav Bhaji",
            "category": "Street Food & Curries",
            "serving_size": "2 pavs + 180g spiced bhaji",
            "serving_weight_g": 250,
            "calories": 440.0, "protein": 9.0, "carbs": 58.0, "fat": 19.0, "fiber": 6.5, "glycemic_index": 68,
            "description": "Mashed vegetable curry cooked with tomatoes, butter, and pav bhaji masala, served with buttered buns.",
            "healthy_alternative": {
                "name": "Whole Wheat Pav with Extra Cauliflower Bhaji (Low Butter)",
                "calories": 260.0, "protein": 9.5, "carbs": 42.0, "fat": 6.0, "fiber": 8.5, "glycemic_index": 48,
                "reason": "Cuts 180 kcal of butter and replaces refined pav with high-fiber whole wheat."
            }
        },
        "pizza": {
            "display_name": "Veg Pizza (Indian Style)",
            "category": "Fast Food",
            "serving_size": "2 slices (160g)",
            "serving_weight_g": 160,
            "calories": 410.0, "protein": 14.0, "carbs": 48.0, "fat": 18.0, "fiber": 2.5, "glycemic_index": 70,
            "description": "Baked flat dough topped with tomato sauce, mozzarella cheese, capsicum, and onions.",
            "healthy_alternative": {
                "name": "Oats / Whole Wheat Thin Crust Veggie Pizza",
                "calories": 240.0, "protein": 12.0, "carbs": 30.0, "fat": 7.5, "fiber": 5.0, "glycemic_index": 45,
                "reason": "Uses thin oat crust and fresh low-fat cottage cheese."
            }
        },
        "samosa": {
            "display_name": "Samosa",
            "category": "Snacks",
            "serving_size": "1 piece (80g)",
            "serving_weight_g": 80,
            "calories": 260.0, "protein": 4.0, "carbs": 28.0, "fat": 15.0, "fiber": 2.0, "glycemic_index": 72,
            "description": "Crispy fried maida pastry stuffed with spiced potatoes and green peas.",
            "healthy_alternative": {
                "name": "Air-Fried Paneer & Pea Samosa",
                "calories": 140.0, "protein": 8.0, "carbs": 18.0, "fat": 4.5, "fiber": 3.2, "glycemic_index": 52,
                "reason": "Air frying eliminates 70% of fat while paneer doubles protein."
            }
        }
    }
    
    # Save the exact mapping to JSON
    json_path = os.path.join(DATA_DIR, "rajistics_20_nutrition_table.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(nutrition_lookup, f, indent=2)
        
    print(f"{'Exact Class String':<16} | {'Display Name':<28} | {'Category':<20} | {'Cal':>5} | {'Prot':>5} | {'Carb':>5} | {'Fat':>5} | {'GI':>3}")
    print("-" * 100)
    for c in sorted(CLASS_NAMES_20):
        data = nutrition_lookup[c]
        print(f"{c:<16} | {data['display_name']:<28} | {data['category']:<20} | {data['calories']:>5.0f} | {data['protein']:>4.1f}g | {data['carbs']:>4.1f}g | {data['fat']:>4.1f}g | {data['glycemic_index']:>3}")
        
    print("-" * 100)
    print(f"[Step 6 Confirmation] Exact-keyed nutrition mapping created & saved to: {json_path}")
    return nutrition_lookup


def step7_finalize_class_list(total_counts, low_classes):
    print("\n" + "="*70)
    print("STEP 7: Finalizing Class List (19 vs 20 Decision Analysis)")
    print("="*70)
    
    sorted_by_count = sorted([(c, total_counts[c]) for c in CLASS_NAMES_20], key=lambda x: x[1])
    
    print("All 20 dataset classes ranked by image count (lowest to highest):")
    for rank, (c, count) in enumerate(sorted_by_count, 1):
        print(f"  {rank:2d}. {c:<16} : {count:>4} images")
        
    weakest_class, weakest_count = sorted_by_count[0]
    
    print("\nDecision Options for 19 vs 20 Classes:")
    print(f"1. Option A (Weakest Count): Drop '{weakest_class}' with only {weakest_count} images.")
    print("2. Option B (Out-of-Scope / Non-Traditional): Drop 'pizza' (Western fast food) or 'burger' (Western fast food) or 'chai' (Beverage, not meal dish).")
    print("3. Option C (Keep All 20): Use all 20 classes as provided by the Hugging Face dataset.")
    
    final_19_weakest = [c for c, _ in sorted_by_count if c != weakest_class]
    
    class_config = {
        "dataset_name": "rajistics/indian_food_images",
        "dataset_total_classes": 20,
        "all_classes_exact": CLASS_NAMES_20,
        "counts_per_class": total_counts,
        "weakest_class": weakest_class,
        "weakest_count": weakest_count,
        "candidate_19_classes_drop_weakest": sorted(final_19_weakest),
        "candidate_19_classes_drop_non_traditional": sorted([c for c in CLASS_NAMES_20 if c != "pizza"]),
        "candidate_19_classes_drop_beverage": sorted([c for c in CLASS_NAMES_20 if c != "chai"])
    }
    
    config_path = os.path.join(DATA_DIR, "class_selection_decision.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(class_config, f, indent=2)
        
    print(f"\n[Step 7 Confirmation] Class selection decision exported to: {config_path}")
    return class_config


if __name__ == "__main__":
    train_path, test_path = step2_load_dataset()
    step3_export_to_folders(train_path, test_path)
    train_counts, test_counts, total_counts, low_classes = step4_check_class_balance()
    step5_resize_and_standardize()
    step6_build_nutrition_mapping()
    step7_finalize_class_list(total_counts, low_classes)
