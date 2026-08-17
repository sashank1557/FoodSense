"""
FoodSense — KNN Recommendation Engine Builder & Evaluator
Step 1: Constructs full 6D feature space (calories, protein, carbs, fat, fiber, GI)
Step 2: Assigns strict culinary category tags
Step 3: Compares Euclidean vs Cosine distance metrics
Step 4: Implements dynamic delta-based reason generator
Step 5: Exports scaler parameters to data/knn_feature_scaler.json
"""

import sys
import os
import json
import numpy as np

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) if os.path.basename(SCRIPT_DIR) == "backend-inference" else SCRIPT_DIR
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCALER_PATH = os.path.join(DATA_DIR, "knn_feature_scaler.json")
CANDIDATES_DB_PATH = os.path.join(DATA_DIR, "knn_candidates_db.json")

# 6-dimensional feature specification
FEATURE_KEYS = ["calories", "protein", "carbs", "fat", "fiber", "glycemic_index"]

# Master Candidates & Alternatives Nutrition Database with Category Tags
CANDIDATES_DATA = [
    # --- 1. Breads & Staples ---
    {
        "id": "butter_naan",
        "name": "Butter Naan",
        "category": "Breads & Staples",
        "is_base_class": True,
        "serving_size": "1 piece (90g)",
        "serving_weight_g": 90,
        "calories": 260.0,
        "protein": 7.0,
        "carbs": 45.0,
        "fat": 5.5,
        "fiber": 1.5,
        "glycemic_index": 75
    },
    {
        "id": "chapati",
        "name": "Chapati (Phulka)",
        "category": "Breads & Staples",
        "is_base_class": True,
        "serving_size": "1 piece (40g)",
        "serving_weight_g": 40,
        "calories": 120.0,
        "protein": 3.5,
        "carbs": 22.0,
        "fat": 1.5,
        "fiber": 3.0,
        "glycemic_index": 62
    },
    {
        "id": "tandoori_whole_wheat_roti",
        "name": "Tandoori Whole Wheat Roti",
        "category": "Breads & Staples",
        "is_base_class": False,
        "serving_size": "1 piece (60g)",
        "serving_weight_g": 60,
        "calories": 130.0,
        "protein": 4.5,
        "carbs": 24.0,
        "fat": 1.8,
        "fiber": 3.8,
        "glycemic_index": 55
    },
    {
        "id": "jowar_bajra_millet_roti",
        "name": "Jowar & Bajra Millet Roti",
        "category": "Breads & Staples",
        "is_base_class": False,
        "serving_size": "1 piece (50g)",
        "serving_weight_g": 50,
        "calories": 95.0,
        "protein": 3.8,
        "carbs": 18.0,
        "fat": 1.2,
        "fiber": 4.5,
        "glycemic_index": 48
    },
    {
        "id": "missi_roti_besan",
        "name": "Missi Roti (Besan & Wheat)",
        "category": "Breads & Staples",
        "is_base_class": False,
        "serving_size": "1 piece (55g)",
        "serving_weight_g": 55,
        "calories": 135.0,
        "protein": 6.2,
        "carbs": 20.0,
        "fat": 3.0,
        "fiber": 4.2,
        "glycemic_index": 50
    },
    {
        "id": "ragi_roti",
        "name": "Ragi (Finger Millet) Roti",
        "category": "Breads & Staples",
        "is_base_class": False,
        "serving_size": "1 piece (50g)",
        "serving_weight_g": 50,
        "calories": 105.0,
        "protein": 3.2,
        "carbs": 21.0,
        "fat": 0.8,
        "fiber": 4.0,
        "glycemic_index": 52
    },

    # --- 2. Rice & Grain Dishes ---
    {
        "id": "fried_rice",
        "name": "Veg Fried Rice",
        "category": "Rice & Grain Dishes",
        "is_base_class": True,
        "serving_size": "1 bowl (200g)",
        "serving_weight_g": 200,
        "calories": 330.0,
        "protein": 5.5,
        "carbs": 52.0,
        "fat": 11.0,
        "fiber": 2.5,
        "glycemic_index": 73
    },
    {
        "id": "brown_rice_veggie_pulao",
        "name": "Brown Rice & Veggie Pulao",
        "category": "Rice & Grain Dishes",
        "is_base_class": False,
        "serving_size": "1 bowl (200g)",
        "serving_weight_g": 200,
        "calories": 210.0,
        "protein": 5.8,
        "carbs": 40.0,
        "fat": 3.5,
        "fiber": 5.5,
        "glycemic_index": 55
    },
    {
        "id": "foxtail_millet_fried_rice",
        "name": "Foxtail Millet Veggie Stir-Fry",
        "category": "Rice & Grain Dishes",
        "is_base_class": False,
        "serving_size": "1 bowl (200g)",
        "serving_weight_g": 200,
        "calories": 190.0,
        "protein": 7.0,
        "carbs": 34.0,
        "fat": 3.0,
        "fiber": 6.2,
        "glycemic_index": 50
    },
    {
        "id": "cauliflower_rice_stir_fry",
        "name": "Cauliflower Rice Asian Stir-Fry",
        "category": "Rice & Grain Dishes",
        "is_base_class": False,
        "serving_size": "1 bowl (200g)",
        "serving_weight_g": 200,
        "calories": 110.0,
        "protein": 4.5,
        "carbs": 12.0,
        "fat": 4.0,
        "fiber": 5.0,
        "glycemic_index": 25
    },
    {
        "id": "quinoa_vegetable_khichdi",
        "name": "Quinoa & Moong Dal Khichdi",
        "category": "Rice & Grain Dishes",
        "is_base_class": False,
        "serving_size": "1 bowl (200g)",
        "serving_weight_g": 200,
        "calories": 185.0,
        "protein": 8.5,
        "carbs": 31.0,
        "fat": 2.8,
        "fiber": 5.8,
        "glycemic_index": 45
    },

    # --- 3. Curries & Dal Gravies ---
    {
        "id": "dal_makhani",
        "name": "Dal Makhani (Black Lentils in Cream)",
        "category": "Curries & Dal Gravies",
        "is_base_class": True,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 280.0,
        "protein": 9.0,
        "carbs": 26.0,
        "fat": 15.0,
        "fiber": 6.0,
        "glycemic_index": 48
    },
    {
        "id": "kadai_paneer",
        "name": "Kadai Paneer",
        "category": "Curries & Dal Gravies",
        "is_base_class": True,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 310.0,
        "protein": 14.0,
        "carbs": 12.0,
        "fat": 23.0,
        "fiber": 3.0,
        "glycemic_index": 42
    },
    {
        "id": "yellow_moong_dal_tadka",
        "name": "Yellow Moong Dal Tadka (Light Ghee)",
        "category": "Curries & Dal Gravies",
        "is_base_class": False,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 140.0,
        "protein": 8.5,
        "carbs": 20.0,
        "fat": 3.0,
        "fiber": 5.5,
        "glycemic_index": 38
    },
    {
        "id": "sprouted_moong_curry",
        "name": "Sprouted Green Gram (Moong) Curry",
        "category": "Curries & Dal Gravies",
        "is_base_class": False,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 130.0,
        "protein": 10.0,
        "carbs": 18.0,
        "fat": 2.2,
        "fiber": 6.8,
        "glycemic_index": 32
    },
    {
        "id": "kadai_tofu_bell_peppers",
        "name": "Kadai Tofu & Bell Pepper Stir-Gravy",
        "category": "Curries & Dal Gravies",
        "is_base_class": False,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 175.0,
        "protein": 15.5,
        "carbs": 9.0,
        "fat": 8.0,
        "fiber": 4.0,
        "glycemic_index": 35
    },
    {
        "id": "palak_paneer_low_fat",
        "name": "Low-Fat Palak Paneer (Pureed Spinach)",
        "category": "Curries & Dal Gravies",
        "is_base_class": False,
        "serving_size": "1 katori (150g)",
        "serving_weight_g": 150,
        "calories": 185.0,
        "protein": 13.0,
        "carbs": 8.0,
        "fat": 10.5,
        "fiber": 4.5,
        "glycemic_index": 30
    },

    # --- 4. Fast Food & Street Snacks ---
    {
        "id": "burger",
        "name": "Veg Burger (Aloo Tikki)",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "1 burger (150g)",
        "serving_weight_g": 150,
        "calories": 320.0,
        "protein": 7.5,
        "carbs": 44.0,
        "fat": 13.0,
        "fiber": 3.0,
        "glycemic_index": 70
    },
    {
        "id": "chole_bhature",
        "name": "Chole Bhature",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "1 bhatura + 150g chole",
        "serving_weight_g": 230,
        "calories": 520.0,
        "protein": 15.0,
        "carbs": 62.0,
        "fat": 24.0,
        "fiber": 8.0,
        "glycemic_index": 72
    },
    {
        "id": "kaathi_rolls",
        "name": "Veg Paneer Kaathi Roll",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "1 roll (180g)",
        "serving_weight_g": 180,
        "calories": 380.0,
        "protein": 12.0,
        "carbs": 46.0,
        "fat": 16.0,
        "fiber": 3.5,
        "glycemic_index": 68
    },
    {
        "id": "paani_puri",
        "name": "Paani Puri / Golgappa",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "6 pieces (120g)",
        "serving_weight_g": 120,
        "calories": 180.0,
        "protein": 3.5,
        "carbs": 28.0,
        "fat": 6.5,
        "fiber": 2.0,
        "glycemic_index": 65
    },
    {
        "id": "pav_bhaji",
        "name": "Pav Bhaji (Butter Pav & Spiced Mash)",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "2 pav + 150g bhaji",
        "serving_weight_g": 230,
        "calories": 420.0,
        "protein": 8.0,
        "carbs": 58.0,
        "fat": 18.0,
        "fiber": 5.0,
        "glycemic_index": 74
    },
    {
        "id": "pizza",
        "name": "Veg Pizza (Indian Thin/Regular)",
        "category": "Fast Food & Street Snacks",
        "is_base_class": True,
        "serving_size": "2 slices (160g)",
        "serving_weight_g": 160,
        "calories": 410.0,
        "protein": 14.0,
        "carbs": 48.0,
        "fat": 18.0,
        "fiber": 2.5,
        "glycemic_index": 70
    },
    {
        "id": "whole_wheat_paneer_burger",
        "name": "Whole Wheat Grilled Paneer Burger",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "1 burger (150g)",
        "serving_weight_g": 150,
        "calories": 240.0,
        "protein": 14.0,
        "carbs": 28.0,
        "fat": 6.0,
        "fiber": 5.5,
        "glycemic_index": 48
    },
    {
        "id": "boiled_chana_missi_roti_meal",
        "name": "Boiled Kala Chana Masala + Missi Roti",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "1 plate (200g)",
        "serving_weight_g": 200,
        "calories": 280.0,
        "protein": 16.5,
        "carbs": 42.0,
        "fat": 4.5,
        "fiber": 11.0,
        "glycemic_index": 42
    },
    {
        "id": "whole_wheat_tofu_roll",
        "name": "Whole Wheat Tofu & Mint Kaathi Roll",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "1 roll (170g)",
        "serving_weight_g": 170,
        "calories": 230.0,
        "protein": 14.0,
        "carbs": 29.0,
        "fat": 6.5,
        "fiber": 5.8,
        "glycemic_index": 46
    },
    {
        "id": "air_baked_sprouted_moong_puri",
        "name": "Air-Baked Moong Sprout Paani Puri",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "6 pieces (120g)",
        "serving_weight_g": 120,
        "calories": 110.0,
        "protein": 5.5,
        "carbs": 19.0,
        "fat": 1.5,
        "fiber": 4.0,
        "glycemic_index": 40
    },
    {
        "id": "whole_wheat_pav_cauliflower_bhaji",
        "name": "Whole Wheat Pav + Cauliflower-Rich Bhaji (Light Olive Oil)",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "2 pav + 150g bhaji",
        "serving_weight_g": 230,
        "calories": 250.0,
        "protein": 9.5,
        "carbs": 42.0,
        "fat": 5.0,
        "fiber": 8.5,
        "glycemic_index": 50
    },
    {
        "id": "oats_thin_crust_veggie_pizza",
        "name": "Oats & Whole Wheat Thin Crust Veggie Pizza",
        "category": "Fast Food & Street Snacks",
        "is_base_class": False,
        "serving_size": "2 slices (160g)",
        "serving_weight_g": 160,
        "calories": 240.0,
        "protein": 15.0,
        "carbs": 30.0,
        "fat": 7.0,
        "fiber": 5.5,
        "glycemic_index": 48
    },

    # --- 5. Breakfast & Steamed Snacks ---
    {
        "id": "dhokla",
        "name": "Khaman Dhokla",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": True,
        "serving_size": "2 pieces (100g)",
        "serving_weight_g": 100,
        "calories": 160.0,
        "protein": 6.5,
        "carbs": 26.0,
        "fat": 3.0,
        "fiber": 3.5,
        "glycemic_index": 45
    },
    {
        "id": "idli",
        "name": "Steamed Rice Idli",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": True,
        "serving_size": "2 pieces (100g)",
        "serving_weight_g": 100,
        "calories": 130.0,
        "protein": 4.0,
        "carbs": 26.0,
        "fat": 0.8,
        "fiber": 2.0,
        "glycemic_index": 68
    },
    {
        "id": "masala_dosa",
        "name": "Masala Dosa with Potato Filling",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": True,
        "serving_size": "1 dosa (150g)",
        "serving_weight_g": 150,
        "calories": 310.0,
        "protein": 6.0,
        "carbs": 48.0,
        "fat": 10.5,
        "fiber": 3.5,
        "glycemic_index": 70
    },
    {
        "id": "sprouted_moong_spinach_dhokla",
        "name": "Sprouted Moong & Spinach Dhokla",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": False,
        "serving_size": "2 pieces (100g)",
        "serving_weight_g": 100,
        "calories": 125.0,
        "protein": 8.5,
        "carbs": 18.0,
        "fat": 1.5,
        "fiber": 5.0,
        "glycemic_index": 35
    },
    {
        "id": "ragi_oats_steamed_idli",
        "name": "Ragi & Oats Steamed Idli",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": False,
        "serving_size": "2 pieces (100g)",
        "serving_weight_g": 100,
        "calories": 115.0,
        "protein": 5.5,
        "carbs": 20.0,
        "fat": 1.0,
        "fiber": 4.2,
        "glycemic_index": 45
    },
    {
        "id": "pesarattu_green_gram_dosa",
        "name": "Pesarattu (Whole Green Moong Dosa with Paneer)",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": False,
        "serving_size": "1 dosa (140g)",
        "serving_weight_g": 140,
        "calories": 190.0,
        "protein": 11.0,
        "carbs": 25.0,
        "fat": 4.5,
        "fiber": 6.0,
        "glycemic_index": 42
    },
    {
        "id": "oats_flaxseed_chilla",
        "name": "Oats, Besan & Flaxseed Veggie Chilla",
        "category": "Breakfast & Steamed Snacks",
        "is_base_class": False,
        "serving_size": "1 chilla (120g)",
        "serving_weight_g": 120,
        "calories": 150.0,
        "protein": 7.5,
        "carbs": 20.0,
        "fat": 3.8,
        "fiber": 4.8,
        "glycemic_index": 38
    },

    # --- 6. Fried Snacks & Appetizers ---
    {
        "id": "pakode",
        "name": "Vegetable Pakode (Fried Fritters)",
        "category": "Fried Snacks & Appetizers",
        "is_base_class": True,
        "serving_size": "1 plate (100g)",
        "serving_weight_g": 100,
        "calories": 310.0,
        "protein": 6.0,
        "carbs": 26.0,
        "fat": 20.0,
        "fiber": 3.0,
        "glycemic_index": 68
    },
    {
        "id": "samosa",
        "name": "Potato Samosa (Fried)",
        "category": "Fried Snacks & Appetizers",
        "is_base_class": True,
        "serving_size": "1 piece (80g)",
        "serving_weight_g": 80,
        "calories": 260.0,
        "protein": 4.5,
        "carbs": 30.0,
        "fat": 14.0,
        "fiber": 2.0,
        "glycemic_index": 72
    },
    {
        "id": "air_fried_vegetable_pakora",
        "name": "Air-Fried Cabbage, Palak & Onion Pakora",
        "category": "Fried Snacks & Appetizers",
        "is_base_class": False,
        "serving_size": "1 plate (100g)",
        "serving_weight_g": 100,
        "calories": 140.0,
        "protein": 7.2,
        "carbs": 21.0,
        "fat": 3.5,
        "fiber": 5.0,
        "glycemic_index": 45
    },
    {
        "id": "baked_sweet_potato_samosa",
        "name": "Baked Whole Wheat & Sweet Potato Samosa",
        "category": "Fried Snacks & Appetizers",
        "is_base_class": False,
        "serving_size": "1 piece (80g)",
        "serving_weight_g": 80,
        "calories": 135.0,
        "protein": 4.8,
        "carbs": 23.0,
        "fat": 3.0,
        "fiber": 4.2,
        "glycemic_index": 50
    },
    {
        "id": "roasted_spiced_makhana",
        "name": "Roasted Spiced Foxnuts (Makhana)",
        "category": "Fried Snacks & Appetizers",
        "is_base_class": False,
        "serving_size": "1 bowl (50g)",
        "serving_weight_g": 50,
        "calories": 160.0,
        "protein": 5.0,
        "carbs": 30.0,
        "fat": 2.2,
        "fiber": 4.0,
        "glycemic_index": 42
    },

    # --- 7. Steamed & Pan-Fried Appetizers ---
    {
        "id": "momos",
        "name": "Steamed Veg Momos",
        "category": "Steamed & Pan-Fried Appetizers",
        "is_base_class": True,
        "serving_size": "6 pieces (150g)",
        "serving_weight_g": 150,
        "calories": 210.0,
        "protein": 6.0,
        "carbs": 36.0,
        "fat": 4.5,
        "fiber": 2.5,
        "glycemic_index": 58
    },
    {
        "id": "whole_wheat_veggie_dimsums",
        "name": "100% Whole Wheat Veggie Dimsums",
        "category": "Steamed & Pan-Fried Appetizers",
        "is_base_class": False,
        "serving_size": "6 pieces (150g)",
        "serving_weight_g": 150,
        "calories": 160.0,
        "protein": 7.5,
        "carbs": 27.0,
        "fat": 2.0,
        "fiber": 5.0,
        "glycemic_index": 44
    },
    {
        "id": "tofu_cabbage_crystal_dumplings",
        "name": "Tofu, Mushroom & Cabbage Steamed Dumplings",
        "category": "Steamed & Pan-Fried Appetizers",
        "is_base_class": False,
        "serving_size": "6 pieces (150g)",
        "serving_weight_g": 150,
        "calories": 145.0,
        "protein": 10.5,
        "carbs": 18.0,
        "fat": 3.0,
        "fiber": 4.2,
        "glycemic_index": 38
    },

    # --- 8. Desserts & Sweets ---
    {
        "id": "jalebi",
        "name": "Jalebi (Fried Sugar-Soaked)",
        "category": "Desserts & Sweets",
        "is_base_class": True,
        "serving_size": "3 pieces (80g)",
        "serving_weight_g": 80,
        "calories": 300.0,
        "protein": 2.0,
        "carbs": 58.0,
        "fat": 7.5,
        "fiber": 0.5,
        "glycemic_index": 82
    },
    {
        "id": "kulfi",
        "name": "Malai Kulfi",
        "category": "Desserts & Sweets",
        "is_base_class": True,
        "serving_size": "1 kulfi stick (80g)",
        "serving_weight_g": 80,
        "calories": 220.0,
        "protein": 5.0,
        "carbs": 24.0,
        "fat": 12.0,
        "fiber": 0.2,
        "glycemic_index": 62
    },
    {
        "id": "dates_nuts_energy_bites",
        "name": "Dates, Pistachio & Fig Raw Energy Delight",
        "category": "Desserts & Sweets",
        "is_base_class": False,
        "serving_size": "2 bites (60g)",
        "serving_weight_g": 60,
        "calories": 140.0,
        "protein": 3.8,
        "carbs": 26.0,
        "fat": 3.2,
        "fiber": 4.5,
        "glycemic_index": 45
    },
    {
        "id": "almond_milk_sugarfree_kulfi",
        "name": "Stevia Almond Milk & Cardamom Kulfi",
        "category": "Desserts & Sweets",
        "is_base_class": False,
        "serving_size": "1 kulfi stick (80g)",
        "serving_weight_g": 80,
        "calories": 95.0,
        "protein": 4.5,
        "carbs": 8.0,
        "fat": 4.5,
        "fiber": 2.0,
        "glycemic_index": 28
    },
    {
        "id": "chia_seed_mango_pudding",
        "name": "Coconut Milk & Chia Seed Mango Pudding",
        "category": "Desserts & Sweets",
        "is_base_class": False,
        "serving_size": "1 cup (120g)",
        "serving_weight_g": 120,
        "calories": 130.0,
        "protein": 4.0,
        "carbs": 16.0,
        "fat": 5.0,
        "fiber": 6.0,
        "glycemic_index": 35
    },

    # --- 9. Beverages ---
    {
        "id": "chai",
        "name": "Masala Chai (with Whole Milk & Sugar)",
        "category": "Beverages",
        "is_base_class": True,
        "serving_size": "1 cup (150ml)",
        "serving_weight_g": 150,
        "calories": 90.0,
        "protein": 3.0,
        "carbs": 12.0,
        "fat": 3.5,
        "fiber": 0.0,
        "glycemic_index": 60
    },
    {
        "id": "unsweetened_tulsi_green_tea",
        "name": "Unsweetened Spiced Tulsi & Ginger Green Tea",
        "category": "Beverages",
        "is_base_class": False,
        "serving_size": "1 cup (200ml)",
        "serving_weight_g": 200,
        "calories": 12.0,
        "protein": 0.5,
        "carbs": 2.0,
        "fat": 0.1,
        "fiber": 0.5,
        "glycemic_index": 10
    },
    {
        "id": "jaggery_spiced_almond_chai",
        "name": "Almond Milk Cardamom Chai (Organic Jaggery / Stevia)",
        "category": "Beverages",
        "is_base_class": False,
        "serving_size": "1 cup (150ml)",
        "serving_weight_g": 150,
        "calories": 42.0,
        "protein": 1.8,
        "carbs": 5.5,
        "fat": 1.5,
        "fiber": 0.8,
        "glycemic_index": 35
    },
    {
        "id": "spiced_salted_buttermilk_chaas",
        "name": "Roasted Cumin & Mint Chaas (Spiced Buttermilk)",
        "category": "Beverages",
        "is_base_class": False,
        "serving_size": "1 glass (200ml)",
        "serving_weight_g": 200,
        "calories": 38.0,
        "protein": 3.2,
        "carbs": 4.0,
        "fat": 1.0,
        "fiber": 0.5,
        "glycemic_index": 25
    }
]


def calculate_feature_scalers(items):
    """Compute Min, Max, Mean, Std for all 6 features to save in knn_feature_scaler.json."""
    scalers = {}
    for key in FEATURE_KEYS:
        vals = [float(item[key]) for item in items]
        scalers[key] = {
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)) + 1e-6
        }
    return scalers


def normalize_vector(item, scalers, method="minmax"):
    """Normalize a 6D nutrition vector."""
    vec = []
    for key in FEATURE_KEYS:
        val = float(item[key])
        s = scalers[key]
        if method == "minmax":
            norm = (val - s["min"]) / (s["max"] - s["min"] + 1e-6)
        else: # zscore
            norm = (val - s["mean"]) / s["std"]
        vec.append(norm)
    return np.array(vec, dtype=np.float32)


def compute_euclidean_distance(vec_a, vec_b, weights=None):
    if weights is None:
        return float(np.linalg.norm(vec_a - vec_b))
    diff = (vec_a - vec_b) * weights
    return float(np.sqrt(np.sum(diff ** 2)))


def compute_cosine_distance(vec_a, vec_b):
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    cosine_sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
    return float(1.0 - cosine_sim)


def generate_dynamic_reason(base_item, candidate_item):
    """
    Generate accurate, human-readable reason text dynamically from exact computed deltas.
    e.g. 'Saves 170 kcal (53% fewer calories), cuts fat by 15.5g (-78%), and increases fiber by 2.2x with lower GI.'
    """
    cal_delta = candidate_item["calories"] - base_item["calories"]
    cal_pct = (cal_delta / base_item["calories"]) * 100 if base_item["calories"] > 0 else 0

    fat_delta = candidate_item["fat"] - base_item["fat"]
    fat_pct = (fat_delta / base_item["fat"]) * 100 if base_item["fat"] > 0 else 0

    prot_delta = candidate_item["protein"] - base_item["protein"]
    prot_pct = (prot_delta / base_item["protein"]) * 100 if base_item["protein"] > 0 else 0

    fiber_delta = candidate_item["fiber"] - base_item["fiber"]
    fiber_mult = candidate_item["fiber"] / max(0.5, base_item["fiber"])

    gi_delta = candidate_item["glycemic_index"] - base_item["glycemic_index"]

    clauses = []

    # Calorie change
    if cal_delta <= -20:
        clauses.append(f"Saves {abs(cal_delta):.0f} kcal ({abs(cal_pct):.0f}% fewer calories)")
    elif cal_delta < 0:
        clauses.append(f"{abs(cal_delta):.0f} kcal lower")

    # Fat change
    if fat_delta <= -2.0:
        clauses.append(f"cuts fat by {abs(fat_delta):.1f}g ({abs(fat_pct):.0f}% reduction)")
    elif fat_delta < 0:
        clauses.append(f"{abs(fat_delta):.1f}g less fat")

    # Protein change
    if prot_delta >= 2.0:
        clauses.append(f"+{prot_delta:.1f}g more protein (+{prot_pct:.0f}%)")

    # Fiber change
    if fiber_delta >= 1.5:
        if fiber_mult >= 1.5:
            clauses.append(f"{fiber_mult:.1f}x higher fiber (+{fiber_delta:.1f}g)")
        else:
            clauses.append(f"+{fiber_delta:.1f}g fiber boost")

    # Glycemic index change
    if gi_delta <= -10:
        clauses.append(f"significantly lower GI of {candidate_item['glycemic_index']:.0f} (vs {base_item['glycemic_index']:.0f}) for steady blood sugar")
    elif gi_delta < 0:
        clauses.append(f"lower GI ({candidate_item['glycemic_index']:.0f} vs {base_item['glycemic_index']:.0f})")

    if not clauses:
        return "Balanced macro profile with lower refined carb density."

    return ", ".join(clauses).capitalize() + "."


def find_knn_recommendations(base_id, candidates, scalers, k=3, metric="euclidean"):
    """Find top-k healthier alternatives in the exact same culinary category."""
    base_item = next((item for item in candidates if item["id"] == base_id), None)
    if not base_item:
        return []

    base_cat = base_item["category"]
    base_vec = normalize_vector(base_item, scalers, method="minmax")

    # Filter candidates: strictly same category, not identical id, and must satisfy health improvement
    qualified = []
    for cand in candidates:
        if cand["id"] == base_id:
            continue
        if cand["category"] != base_cat:
            continue

        # Health Filter: Must offer nutritional improvement (lower cal, lower fat, or higher protein/fiber with lower GI)
        cal_diff = cand["calories"] - base_item["calories"]
        fat_diff = cand["fat"] - base_item["fat"]
        prot_diff = cand["protein"] - base_item["protein"]
        fiber_diff = cand["fiber"] - base_item["fiber"]
        gi_diff = cand["glycemic_index"] - base_item["glycemic_index"]

        is_healthier = (
            (cal_diff <= 0 and (fat_diff <= 0 or fiber_diff > 0 or gi_diff < 0)) or
            (fat_diff < -1.0) or
            (gi_diff <= -15 and cal_diff <= 10) or
            (prot_diff >= 3.0 and fat_diff <= 0)
        )

        if not is_healthier:
            continue

        cand_vec = normalize_vector(cand, scalers, method="minmax")

        if metric == "euclidean":
            # Nutrient parity weights: equal balance
            dist = compute_euclidean_distance(base_vec, cand_vec)
        elif metric == "cosine":
            dist = compute_cosine_distance(base_vec, cand_vec)
        else:
            # Weighted Euclidean
            weights = np.array([1.2, 1.0, 1.0, 1.2, 1.0, 1.1], dtype=np.float32)
            dist = compute_euclidean_distance(base_vec, cand_vec, weights=weights)

        reason = generate_dynamic_reason(base_item, cand)

        qualified.append({
            "candidate": cand,
            "distance": dist,
            "cal_savings": -cal_diff,
            "reason": reason
        })

    # Sort by distance
    qualified.sort(key=lambda x: x["distance"])
    return qualified[:k]


def build_and_export_knn():
    print("="*75)
    print("BUILDING FOODSENSE TRUE KNN RECOMMENDATION ENGINE")
    print("="*75)

    # 1. Export Candidates DB
    with open(CANDIDATES_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(CANDIDATES_DATA, f, indent=2)
    print(f"[Export OK] Saved {len(CANDIDATES_DATA)} food items to {CANDIDATES_DB_PATH}")

    # 2. Calculate Feature Scalers
    scalers = calculate_feature_scalers(CANDIDATES_DATA)
    scaler_payload = {
        "features": FEATURE_KEYS,
        "num_items": len(CANDIDATES_DATA),
        "scaling_method": "minmax",
        "scalers": scalers
    }
    with open(SCALER_PATH, "w", encoding="utf-8") as f:
        json.dump(scaler_payload, f, indent=2)
    print(f"[Export OK] Saved feature normalization parameters to {SCALER_PATH}")

    # 3. Benchmark Euclidean vs Cosine on Key Dishes
    test_dishes = ["fried_rice", "pizza", "chai", "pakode", "butter_naan", "dal_makhani"]

    print("\n" + "-"*75)
    print("DISTANCE METRIC BENCHMARK (Euclidean vs Cosine vs Weighted Euclidean)")
    print("-"*75)

    for dish in test_dishes:
        print(f"\nTarget Dish: [{dish.upper()}]")
        for m in ["euclidean", "cosine"]:
            recs = find_knn_recommendations(dish, CANDIDATES_DATA, scalers, k=2, metric=m)
            rec_names = [f"{r['candidate']['name']} (dist={r['distance']:.3f})" for r in recs]
            print(f"  * {m.capitalize():<10}: {' | '.join(rec_names)}")

    print("\n" + "="*75)
    print("DETAILED KNN RESULTS WITH DYNAMIC REASON GENERATION (Euclidean)")
    print("="*75)

    for dish in test_dishes:
        base = next(item for item in CANDIDATES_DATA if item["id"] == dish)
        recs = find_knn_recommendations(dish, CANDIDATES_DATA, scalers, k=2, metric="euclidean")
        print(f"\n[Detected: {base['name']} ({base['category']})]")
        print(f"  Macros: {base['calories']:.0f} kcal | {base['protein']:.1f}g P | {base['carbs']:.1f}g C | {base['fat']:.1f}g F | {base['fiber']:.1f}g Fib | GI: {base['glycemic_index']}")
        for rank, r in enumerate(recs, 1):
            c = r["candidate"]
            print(f"  -> Top #{rank} KNN Swap: {c['name']} (Dist: {r['distance']:.3f})")
            print(f"     Macros: {c['calories']:.0f} kcal | {c['protein']:.1f}g P | {c['carbs']:.1f}g C | {c['fat']:.1f}g F | {c['fiber']:.1f}g Fib | GI: {c['glycemic_index']}")
            print(f"     Dynamic Reason: \"{r['reason']}\"")


if __name__ == "__main__":
    build_and_export_knn()
