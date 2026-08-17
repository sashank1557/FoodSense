"""
FoodSense - Indian Food Nutrition Database (19 Classes)
Comprehensive nutrition profiles, categories, GI indexes, and healthy alternative profiles.
"""

from typing import Dict, List, Any, Optional
import json
import os

INDIAN_FOOD_CLASSES = [
    "roti",
    "naan",
    "poori",
    "steamed_rice",
    "biryani",
    "dal_tadka",
    "paneer_butter_masala",
    "chole",
    "rajma",
    "samosa",
    "pakora",
    "dosa",
    "idli",
    "medu_vada",
    "poha",
    "upma",
    "gulab_jamun",
    "jalebi",
    "rasgulla"
]

NUTRITION_DB: Dict[str, Dict[str, Any]] = {
    "roti": {
        "class_id": "roti",
        "display_name": "Roti (Chapati)",
        "category": "Breads",
        "serving_size": "1 piece (40g)",
        "serving_weight_g": 40,
        "calories": 120.0,
        "protein": 3.5,
        "carbs": 22.0,
        "fat": 1.5,
        "fiber": 3.0,
        "glycemic_index": 62,
        "sodium_mg": 110,
        "description": "Traditional whole wheat unleavened flatbread cooked on a tawa.",
        "tags": ["staple", "vegetarian", "whole_grain", "low_fat"],
        "healthy_alternatives": [
            {
                "name": "Jowar / Bajra Roti",
                "category": "Breads",
                "serving_size": "1 piece (45g)",
                "calories": 95.0,
                "protein": 3.8,
                "carbs": 18.0,
                "fat": 1.0,
                "fiber": 4.5,
                "glycemic_index": 48,
                "reason": "Gluten-free millet bread with 50% more fiber and significantly lower GI for blood sugar stability."
            },
            {
                "name": "Multigrain Phulka (Oil-free)",
                "category": "Breads",
                "serving_size": "1 piece (35g)",
                "calories": 90.0,
                "protein": 4.2,
                "carbs": 17.0,
                "fat": 0.8,
                "fiber": 4.0,
                "glycemic_index": 52,
                "reason": "Enriched with oats, flaxseed, and ragi flour for higher protein and dietary fiber."
            }
        ]
    },
    "naan": {
        "class_id": "naan",
        "display_name": "Butter Naan",
        "category": "Breads",
        "serving_size": "1 piece (90g)",
        "serving_weight_g": 90,
        "calories": 260.0,
        "protein": 7.0,
        "carbs": 45.0,
        "fat": 5.5,
        "fiber": 1.5,
        "glycemic_index": 75,
        "sodium_mg": 380,
        "description": "Leavened tandoor-baked flatbread made with refined flour (maida) and brushed with butter.",
        "tags": ["refined_flour", "high_gi", "vegetarian"],
        "healthy_alternatives": [
            {
                "name": "Tandoori Whole Wheat Roti",
                "category": "Breads",
                "serving_size": "1 piece (50g)",
                "calories": 130.0,
                "protein": 4.5,
                "carbs": 24.0,
                "fat": 1.8,
                "fiber": 3.8,
                "glycemic_index": 55,
                "reason": "Saves 130 kcal and 21g refined carbs per serving; baked with unrefined whole wheat flour."
            },
            {
                "name": "Missi Roti (Gram Flour)",
                "category": "Breads",
                "serving_size": "1 piece (60g)",
                "calories": 150.0,
                "protein": 6.5,
                "carbs": 22.0,
                "fat": 3.0,
                "fiber": 5.0,
                "glycemic_index": 45,
                "reason": "High protein chickpea flour flatbread with low glycemic index and gut-friendly fiber."
            }
        ]
    },
    "poori": {
        "class_id": "poori",
        "display_name": "Poori",
        "category": "Breads",
        "serving_size": "1 piece (35g)",
        "serving_weight_g": 35,
        "calories": 140.0,
        "protein": 2.0,
        "carbs": 16.0,
        "fat": 8.0,
        "fiber": 1.0,
        "glycemic_index": 70,
        "sodium_mg": 95,
        "description": "Deep-fried puffed unleavened bread made of whole wheat or semolina.",
        "tags": ["deep_fried", "high_fat", "vegetarian"],
        "healthy_alternatives": [
            {
                "name": "Oil-Free Phulka",
                "category": "Breads",
                "serving_size": "1 piece (35g)",
                "calories": 85.0,
                "protein": 3.0,
                "carbs": 17.0,
                "fat": 0.5,
                "fiber": 2.8,
                "glycemic_index": 58,
                "reason": "Reduces saturated fat by 90% and calories by 40% while preserving authentic roti texture."
            },
            {
                "name": "Baked Millet Poori",
                "category": "Breads",
                "serving_size": "1 piece (35g)",
                "calories": 95.0,
                "protein": 2.8,
                "carbs": 16.0,
                "fat": 2.0,
                "fiber": 3.5,
                "glycemic_index": 50,
                "reason": "Air-fried or oven-baked using bajra/ragi dough for minimal oil absorption."
            }
        ]
    },
    "steamed_rice": {
        "class_id": "steamed_rice",
        "display_name": "Steamed White Rice",
        "category": "Grains",
        "serving_size": "1 cup cooked (150g)",
        "serving_weight_g": 150,
        "calories": 195.0,
        "protein": 4.0,
        "carbs": 44.0,
        "fat": 0.5,
        "fiber": 0.6,
        "glycemic_index": 73,
        "sodium_mg": 5,
        "description": "Polished white basmati or sona masoori rice boiled in water.",
        "tags": ["refined_grain", "gluten_free", "high_gi", "vegan"],
        "healthy_alternatives": [
            {
                "name": "Foxtail / Little Millet Rice",
                "category": "Grains",
                "serving_size": "1 cup cooked (150g)",
                "calories": 160.0,
                "protein": 5.5,
                "carbs": 32.0,
                "fat": 1.2,
                "fiber": 6.0,
                "glycemic_index": 50,
                "reason": "10x higher dietary fiber and complex carbohydrates that prevent insulin spikes."
            },
            {
                "name": "Brown Basmati Rice",
                "category": "Grains",
                "serving_size": "1 cup cooked (150g)",
                "calories": 175.0,
                "protein": 4.5,
                "carbs": 36.0,
                "fat": 1.5,
                "fiber": 3.5,
                "glycemic_index": 55,
                "reason": "Retains bran and germ layers providing magnesium, B-vitamins, and slow-release energy."
            }
        ]
    },
    "biryani": {
        "class_id": "biryani",
        "display_name": "Hyderabadi Veg/Dum Biryani",
        "category": "Rice Dishes",
        "serving_size": "1 plate (300g)",
        "serving_weight_g": 300,
        "calories": 450.0,
        "protein": 14.0,
        "carbs": 55.0,
        "fat": 18.0,
        "fiber": 3.5,
        "glycemic_index": 65,
        "sodium_mg": 680,
        "description": "Aromatic layered rice cooked with spices, ghee, saffron, and vegetables or paneer.",
        "tags": ["calorie_dense", "rich", "spiced"],
        "healthy_alternatives": [
            {
                "name": "Quinoa & Soya Chunks Biryani",
                "category": "Rice Dishes",
                "serving_size": "1 plate (280g)",
                "calories": 310.0,
                "protein": 22.0,
                "carbs": 38.0,
                "fat": 7.0,
                "fiber": 8.0,
                "glycemic_index": 46,
                "reason": "Boosts protein to 22g while cutting fat by over 60% using plant proteins."
            },
            {
                "name": "Brown Rice Vegetable Dum Biryani (Low Ghee)",
                "category": "Rice Dishes",
                "serving_size": "1 plate (280g)",
                "calories": 330.0,
                "protein": 12.0,
                "carbs": 48.0,
                "fat": 8.5,
                "fiber": 6.5,
                "glycemic_index": 52,
                "reason": "Prepares the classic dum aroma with brown rice and heart-healthy olive or cold-pressed oil."
            }
        ]
    },
    "dal_tadka": {
        "class_id": "dal_tadka",
        "display_name": "Dal Tadka",
        "category": "Lentils",
        "serving_size": "1 cup (200g)",
        "serving_weight_g": 200,
        "calories": 180.0,
        "protein": 9.0,
        "carbs": 24.0,
        "fat": 6.0,
        "fiber": 5.5,
        "glycemic_index": 38,
        "sodium_mg": 460,
        "description": "Yellow pigeon pea (toor) or moong lentils tempered with cumin, garlic, ghee, and tomatoes.",
        "tags": ["lentils", "vegetarian", "low_gi", "protein_source"],
        "healthy_alternatives": [
            {
                "name": "Moong Dal & Spinach Khichdi Soup",
                "category": "Lentils",
                "serving_size": "1 cup (200g)",
                "calories": 130.0,
                "protein": 8.5,
                "carbs": 18.0,
                "fat": 2.5,
                "fiber": 6.0,
                "glycemic_index": 32,
                "reason": "Lower fat preparation boosted with iron and folate from fresh spinach leaves."
            },
            {
                "name": "Sprouted Moong Dal Tadka",
                "category": "Lentils",
                "serving_size": "1 cup (200g)",
                "calories": 145.0,
                "protein": 11.0,
                "carbs": 20.0,
                "fat": 3.0,
                "fiber": 7.5,
                "glycemic_index": 28,
                "reason": "Sprouting increases protein bioavailability, enhances enzymatic absorption, and reduces flatulence."
            }
        ]
    },
    "paneer_butter_masala": {
        "class_id": "paneer_butter_masala",
        "display_name": "Paneer Butter Masala",
        "category": "Curries",
        "serving_size": "1 cup (200g)",
        "serving_weight_g": 200,
        "calories": 380.0,
        "protein": 12.0,
        "carbs": 14.0,
        "fat": 30.0,
        "fiber": 2.0,
        "glycemic_index": 45,
        "sodium_mg": 580,
        "description": "Cottage cheese cubes in a rich tomato, cashew cream, and butter gravy.",
        "tags": ["high_fat", "dairy", "rich_curry"],
        "healthy_alternatives": [
            {
                "name": "Tofu Makhani (Low Fat)",
                "category": "Curries",
                "serving_size": "1 cup (200g)",
                "calories": 190.0,
                "protein": 16.0,
                "carbs": 12.0,
                "fat": 9.0,
                "fiber": 4.0,
                "glycemic_index": 35,
                "reason": "Saves 190 kcal and reduces saturated fat by 70% while raising plant protein to 16g."
            },
            {
                "name": "Palak Paneer (Low-Fat Paneer)",
                "category": "Curries",
                "serving_size": "1 cup (200g)",
                "calories": 210.0,
                "protein": 15.0,
                "carbs": 8.0,
                "fat": 12.0,
                "fiber": 5.0,
                "glycemic_index": 30,
                "reason": "Spinach base adds lutein, vitamins A & C, and cut fat content by more than half."
            }
        ]
    },
    "chole": {
        "class_id": "chole",
        "display_name": "Chole (Punjabi Chickpeas)",
        "category": "Legumes",
        "serving_size": "1 cup (200g)",
        "serving_weight_g": 200,
        "calories": 270.0,
        "protein": 12.5,
        "carbs": 38.0,
        "fat": 7.5,
        "fiber": 9.0,
        "glycemic_index": 35,
        "sodium_mg": 520,
        "description": "Kabuli chickpeas simmered in a spiced onion, tomato, and pomegranate powder gravy.",
        "tags": ["high_fiber", "legume", "low_gi", "vegan"],
        "healthy_alternatives": [
            {
                "name": "Boiled Chickpea & Cucumber Salad",
                "category": "Legumes",
                "serving_size": "1 bowl (180g)",
                "calories": 180.0,
                "protein": 10.0,
                "carbs": 28.0,
                "fat": 3.0,
                "fiber": 8.0,
                "glycemic_index": 28,
                "reason": "Light, oil-free preparation rich in micronutrients, lemon antioxidants, and crunchy fiber."
            },
            {
                "name": "Kala Chana Masala (Black Chickpeas)",
                "category": "Legumes",
                "serving_size": "1 cup (200g)",
                "calories": 220.0,
                "protein": 14.0,
                "carbs": 32.0,
                "fat": 4.0,
                "fiber": 11.0,
                "glycemic_index": 30,
                "reason": "Higher fiber density and complex resistant starch promoting healthy gut microbiome."
            }
        ]
    },
    "rajma": {
        "class_id": "rajma",
        "display_name": "Rajma Masala (Kidney Beans)",
        "category": "Legumes",
        "serving_size": "1 cup (200g)",
        "serving_weight_g": 200,
        "calories": 240.0,
        "protein": 13.0,
        "carbs": 36.0,
        "fat": 5.0,
        "fiber": 10.0,
        "glycemic_index": 30,
        "sodium_mg": 480,
        "description": "Red kidney beans cooked in a hearty ginger-garlic and spiced tomato gravy.",
        "tags": ["high_fiber", "high_protein", "low_gi", "vegan"],
        "healthy_alternatives": [
            {
                "name": "Low-Oil Rajma with Sprouted Mung",
                "category": "Legumes",
                "serving_size": "1 cup (200g)",
                "calories": 190.0,
                "protein": 15.0,
                "carbs": 30.0,
                "fat": 2.5,
                "fiber": 11.5,
                "glycemic_index": 26,
                "reason": "Enhanced with sprouted mung for broader amino acid profile and reduced oil tempering."
            },
            {
                "name": "Three-Bean Medley Salad",
                "category": "Legumes",
                "serving_size": "1 bowl (180g)",
                "calories": 170.0,
                "protein": 12.0,
                "carbs": 26.0,
                "fat": 2.0,
                "fiber": 9.0,
                "glycemic_index": 27,
                "reason": "Light dressing with lime and mint, providing sustained energy without heavy gravies."
            }
        ]
    },
    "samosa": {
        "class_id": "samosa",
        "display_name": "Potato Samosa",
        "category": "Snacks",
        "serving_size": "1 piece (80g)",
        "serving_weight_g": 80,
        "calories": 260.0,
        "protein": 4.0,
        "carbs": 28.0,
        "fat": 15.0,
        "fiber": 2.0,
        "glycemic_index": 72,
        "sodium_mg": 320,
        "description": "Crispy fried pastry cone stuffed with spiced potatoes, peas, and coriander.",
        "tags": ["deep_fried", "high_fat", "snack"],
        "healthy_alternatives": [
            {
                "name": "Air-Fried Paneer & Pea Samosa",
                "category": "Snacks",
                "serving_size": "1 piece (75g)",
                "calories": 140.0,
                "protein": 8.0,
                "carbs": 18.0,
                "fat": 4.5,
                "fiber": 3.2,
                "glycemic_index": 52,
                "reason": "Cuts 120 kcal and 70% fat by using air-frying, with double protein from paneer/peas."
            },
            {
                "name": "Sprouts Bhel Chaat",
                "category": "Snacks",
                "serving_size": "1 bowl (120g)",
                "calories": 130.0,
                "protein": 7.0,
                "carbs": 22.0,
                "fat": 2.0,
                "fiber": 5.5,
                "glycemic_index": 40,
                "reason": "Crunchy savory afternoon snack with zero trans-fats and high vitamin C."
            }
        ]
    },
    "pakora": {
        "class_id": "pakora",
        "display_name": "Vegetable Pakora (Bhajiya)",
        "category": "Snacks",
        "serving_size": "1 plate (100g)",
        "serving_weight_g": 100,
        "calories": 310.0,
        "protein": 6.0,
        "carbs": 26.0,
        "fat": 20.0,
        "fiber": 3.0,
        "glycemic_index": 68,
        "sodium_mg": 390,
        "description": "Vegetables dipped in spiced besan (gram flour) batter and deep-fried until crisp.",
        "tags": ["deep_fried", "high_fat", "snack"],
        "healthy_alternatives": [
            {
                "name": "Air-Fried Onion & Cabbage Fritters",
                "category": "Snacks",
                "serving_size": "1 plate (100g)",
                "calories": 140.0,
                "protein": 6.5,
                "carbs": 20.0,
                "fat": 4.0,
                "fiber": 4.5,
                "glycemic_index": 48,
                "reason": "Retains crispy chickpea flour crunch with only 4g fat instead of 20g."
            },
            {
                "name": "Roasted Masala Makhana (Foxnuts)",
                "category": "Snacks",
                "serving_size": "1 bowl (40g)",
                "calories": 145.0,
                "protein": 4.5,
                "carbs": 24.0,
                "fat": 3.5,
                "fiber": 4.0,
                "glycemic_index": 45,
                "reason": "Antioxidant-dense crunchy snack rich in magnesium, potassium, and calcium."
            }
        ]
    },
    "dosa": {
        "class_id": "dosa",
        "display_name": "Plain / Masala Dosa",
        "category": "Breakfast",
        "serving_size": "1 piece (100g)",
        "serving_weight_g": 100,
        "calories": 170.0,
        "protein": 4.0,
        "carbs": 28.0,
        "fat": 4.5,
        "fiber": 1.5,
        "glycemic_index": 60,
        "sodium_mg": 280,
        "description": "Thin fermented crepe made from rice and urad dal batter, crisped on a griddle.",
        "tags": ["fermented", "south_indian", "breakfast"],
        "healthy_alternatives": [
            {
                "name": "Ragi (Finger Millet) Dosa",
                "category": "Breakfast",
                "serving_size": "1 piece (90g)",
                "calories": 125.0,
                "protein": 4.2,
                "carbs": 22.0,
                "fat": 2.0,
                "fiber": 4.5,
                "glycemic_index": 44,
                "reason": "Exceptionally rich in calcium, iron, and slow-burning complex carbohydrates."
            },
            {
                "name": "Oats & Moong Dal Pesarattu",
                "category": "Breakfast",
                "serving_size": "1 piece (95g)",
                "calories": 135.0,
                "protein": 7.5,
                "carbs": 20.0,
                "fat": 2.5,
                "fiber": 5.0,
                "glycemic_index": 38,
                "reason": "Nearly double the protein and enriched with beta-glucan fiber for cardiovascular health."
            }
        ]
    },
    "idli": {
        "class_id": "idli",
        "display_name": "Steamed Idli",
        "category": "Breakfast",
        "serving_size": "2 pieces (100g)",
        "serving_weight_g": 100,
        "calories": 130.0,
        "protein": 5.0,
        "carbs": 26.0,
        "fat": 0.5,
        "fiber": 2.5,
        "glycemic_index": 35,
        "sodium_mg": 180,
        "description": "Steamed savory cakes made from fermented black lentils and rice batter.",
        "tags": ["steamed", "fermented", "low_fat", "south_indian"],
        "healthy_alternatives": [
            {
                "name": "Oats & Carrot Idli",
                "category": "Breakfast",
                "serving_size": "2 pieces (100g)",
                "calories": 115.0,
                "protein": 5.8,
                "carbs": 20.0,
                "fat": 1.2,
                "fiber": 4.2,
                "glycemic_index": 30,
                "reason": "Enhanced with soluble fiber and beta-carotene while maintaining traditional fluffiness."
            },
            {
                "name": "Ragi & Sprouted Moong Idli",
                "category": "Breakfast",
                "serving_size": "2 pieces (100g)",
                "calories": 120.0,
                "protein": 6.5,
                "carbs": 21.0,
                "fat": 1.0,
                "fiber": 4.8,
                "glycemic_index": 28,
                "reason": "Nutrient-dense variation delivering calcium, polyphenols, and low glycemic load."
            }
        ]
    },
    "medu_vada": {
        "class_id": "medu_vada",
        "display_name": "Medu Vada",
        "category": "Breakfast",
        "serving_size": "1 piece (60g)",
        "serving_weight_g": 60,
        "calories": 195.0,
        "protein": 5.5,
        "carbs": 18.0,
        "fat": 12.0,
        "fiber": 2.0,
        "glycemic_index": 65,
        "sodium_mg": 240,
        "description": "Doughnut-shaped fritter made of spiced urad dal batter and deep-fried crisp.",
        "tags": ["deep_fried", "high_fat", "south_indian"],
        "healthy_alternatives": [
            {
                "name": "Air-Fried Medu Vada (Appe Pan)",
                "category": "Breakfast",
                "serving_size": "1 piece (50g)",
                "calories": 95.0,
                "protein": 5.5,
                "carbs": 15.0,
                "fat": 1.8,
                "fiber": 2.5,
                "glycemic_index": 48,
                "reason": "Cuts 100 kcal and 85% fat while preserving identical urad dal protein and crisp exterior."
            },
            {
                "name": "Steamed Dal Dhokla",
                "category": "Breakfast",
                "serving_size": "2 pieces (80g)",
                "calories": 110.0,
                "protein": 6.0,
                "carbs": 18.0,
                "fat": 1.5,
                "fiber": 3.0,
                "glycemic_index": 40,
                "reason": "100% steamed legume snack delivering tangy flavor with virtually no added oil."
            }
        ]
    },
    "poha": {
        "class_id": "poha",
        "display_name": "Kanda / Batata Poha",
        "category": "Breakfast",
        "serving_size": "1 cup (150g)",
        "serving_weight_g": 150,
        "calories": 210.0,
        "protein": 4.0,
        "carbs": 38.0,
        "fat": 5.0,
        "fiber": 3.5,
        "glycemic_index": 55,
        "sodium_mg": 320,
        "description": "Flattened rice tempered with mustard seeds, turmeric, green chilies, peanuts, and onions.",
        "tags": ["breakfast", "flattened_rice", "quick_meal"],
        "healthy_alternatives": [
            {
                "name": "Red Rice / Brown Poha with Veggies",
                "category": "Breakfast",
                "serving_size": "1 cup (150g)",
                "calories": 170.0,
                "protein": 5.0,
                "carbs": 30.0,
                "fat": 3.5,
                "fiber": 5.5,
                "glycemic_index": 45,
                "reason": "Unpolished red rice flakes provide anthocyanin antioxidants and 60% more fiber."
            },
            {
                "name": "Quinoa Upma / Poha Style",
                "category": "Breakfast",
                "serving_size": "1 cup (150g)",
                "calories": 160.0,
                "protein": 7.0,
                "carbs": 26.0,
                "fat": 3.0,
                "fiber": 4.5,
                "glycemic_index": 42,
                "reason": "Complete protein containing all 9 essential amino acids and a low glycemic response."
            }
        ]
    },
    "upma": {
        "class_id": "upma",
        "display_name": "Rava Upma",
        "category": "Breakfast",
        "serving_size": "1 cup (150g)",
        "serving_weight_g": 150,
        "calories": 220.0,
        "protein": 5.0,
        "carbs": 35.0,
        "fat": 7.0,
        "fiber": 3.0,
        "glycemic_index": 65,
        "sodium_mg": 350,
        "description": "Thick porridge cooked from dry-roasted semolina (rava) spiced with ginger, mustard, and vegetables.",
        "tags": ["breakfast", "semolina", "vegetarian"],
        "healthy_alternatives": [
            {
                "name": "Broken Wheat (Dalia) Vegetable Upma",
                "category": "Breakfast",
                "serving_size": "1 cup (150g)",
                "calories": 155.0,
                "protein": 6.5,
                "carbs": 28.0,
                "fat": 2.5,
                "fiber": 6.0,
                "glycemic_index": 48,
                "reason": "Unrefined wheat bulgur doubles the fiber and keeps satiety levels high until lunch."
            },
            {
                "name": "Barnyard Millet Upma",
                "category": "Breakfast",
                "serving_size": "1 cup (150g)",
                "calories": 140.0,
                "protein": 5.5,
                "carbs": 25.0,
                "fat": 2.0,
                "fiber": 5.5,
                "glycemic_index": 42,
                "reason": "Low carb, rich in iron, and digests gradually for steady daytime energy."
            }
        ]
    },
    "gulab_jamun": {
        "class_id": "gulab_jamun",
        "display_name": "Gulab Jamun",
        "category": "Sweets",
        "serving_size": "2 pieces (80g)",
        "serving_weight_g": 80,
        "calories": 300.0,
        "protein": 4.0,
        "carbs": 48.0,
        "fat": 10.5,
        "fiber": 0.5,
        "glycemic_index": 80,
        "sodium_mg": 85,
        "description": "Deep-fried khoya/milk-solid dumplings soaked in rose and cardamom flavored sugar syrup.",
        "tags": ["sweet", "deep_fried", "sugar_syrup", "high_calorie"],
        "healthy_alternatives": [
            {
                "name": "Steamed Sandesh (Stevia/Jaggery)",
                "category": "Sweets",
                "serving_size": "2 pieces (60g)",
                "calories": 120.0,
                "protein": 6.5,
                "carbs": 14.0,
                "fat": 4.0,
                "fiber": 0.5,
                "glycemic_index": 45,
                "reason": "Non-fried fresh paneer sweet cutting 180 kcal and 34g sugar."
            },
            {
                "name": "Dates & Mixed Nut Ladoo",
                "category": "Sweets",
                "serving_size": "1 piece (35g)",
                "calories": 110.0,
                "protein": 3.5,
                "carbs": 16.0,
                "fat": 4.5,
                "fiber": 2.5,
                "glycemic_index": 42,
                "reason": "Zero added refined sugar; naturally sweetened by dates packed with potassium and minerals."
            }
        ]
    },
    "jalebi": {
        "class_id": "jalebi",
        "display_name": "Jalebi",
        "category": "Sweets",
        "serving_size": "3 pieces (75g)",
        "serving_weight_g": 75,
        "calories": 290.0,
        "protein": 2.0,
        "carbs": 56.0,
        "fat": 7.0,
        "fiber": 0.2,
        "glycemic_index": 82,
        "sodium_mg": 65,
        "description": "Deep-fried spiral maida flour coils soaked in concentrated saffron sugar syrup.",
        "tags": ["sweet", "deep_fried", "sugar_dense", "high_gi"],
        "healthy_alternatives": [
            {
                "name": "Fresh Pomegranate & Fig Chaat",
                "category": "Sweets",
                "serving_size": "1 bowl (120g)",
                "calories": 95.0,
                "protein": 1.5,
                "carbs": 22.0,
                "fat": 0.3,
                "fiber": 4.0,
                "glycemic_index": 40,
                "reason": "Natural polyphenols, vitamin C, and fiber providing natural sweetness without sugar crashes."
            },
            {
                "name": "Apple Slices with Cinnamon & Honey",
                "category": "Sweets",
                "serving_size": "1 cup (120g)",
                "calories": 80.0,
                "protein": 0.5,
                "carbs": 20.0,
                "fat": 0.2,
                "fiber": 3.0,
                "glycemic_index": 38,
                "reason": "Cinnamon helps regulate blood sugar while crisp fruit provides satisfying dessert flavor."
            }
        ]
    },
    "rasgulla": {
        "class_id": "rasgulla",
        "display_name": "Rasgulla",
        "category": "Sweets",
        "serving_size": "2 pieces (90g)",
        "serving_weight_g": 90,
        "calories": 210.0,
        "protein": 4.5,
        "carbs": 42.0,
        "fat": 2.0,
        "fiber": 0.2,
        "glycemic_index": 70,
        "sodium_mg": 70,
        "description": "Spongy cottage cheese (chhena) balls boiled in light sugar syrup.",
        "tags": ["sweet", "chhena", "boiled_syrup"],
        "healthy_alternatives": [
            {
                "name": "Squeezed Rasgulla in Almond Milk",
                "category": "Sweets",
                "serving_size": "2 pieces (80g)",
                "calories": 110.0,
                "protein": 5.5,
                "carbs": 12.0,
                "fat": 4.0,
                "fiber": 1.0,
                "glycemic_index": 45,
                "reason": "Squeezing out sugar syrup removes 70% of refined sugar; almond milk adds vitamin E."
            },
            {
                "name": "Greek Yogurt with Mango Pulp & Chia",
                "category": "Sweets",
                "serving_size": "1 cup (140g)",
                "calories": 125.0,
                "protein": 10.0,
                "carbs": 15.0,
                "fat": 2.5,
                "fiber": 3.0,
                "glycemic_index": 35,
                "reason": "High protein dessert with probiotics that aid digestion and promote gut health."
            }
        ]
    }
}


def get_item_nutrition(class_id: str, portion_multiplier: float = 1.0) -> Optional[Dict[str, Any]]:
    """Retrieve item nutrition scaled by portion multiplier."""
    item = NUTRITION_DB.get(class_id.lower().strip())
    if not item:
        return None
    
    scaled = dict(item)
    scaled["portion_multiplier"] = portion_multiplier
    scaled["calories"] = round(item["calories"] * portion_multiplier, 1)
    scaled["protein"] = round(item["protein"] * portion_multiplier, 1)
    scaled["carbs"] = round(item["carbs"] * portion_multiplier, 1)
    scaled["fat"] = round(item["fat"] * portion_multiplier, 1)
    scaled["fiber"] = round(item["fiber"] * portion_multiplier, 1)
    scaled["sodium_mg"] = round(item["sodium_mg"] * portion_multiplier, 1)
    return scaled


def calculate_meal_totals(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate total calories, macros, fiber, and calculate macro distribution percentages."""
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
        "item_count": len(detections)
    }
    
    for det in detections:
        portion = det.get("portion_multiplier", 1.0)
        nutrition = det.get("nutrition")
        if not nutrition and "class_id" in det:
            nutrition = get_item_nutrition(det["class_id"], portion)
        
        if nutrition:
            totals["calories"] += nutrition.get("calories", 0.0)
            totals["protein"] += nutrition.get("protein", 0.0)
            totals["carbs"] += nutrition.get("carbs", 0.0)
            totals["fat"] += nutrition.get("fat", 0.0)
            totals["fiber"] += nutrition.get("fiber", 0.0)
    
    totals["calories"] = round(totals["calories"], 1)
    totals["protein"] = round(totals["protein"], 1)
    totals["carbs"] = round(totals["carbs"], 1)
    totals["fat"] = round(totals["fat"], 1)
    totals["fiber"] = round(totals["fiber"], 1)
    
    # Calculate macro calorie percentages
    protein_cal = totals["protein"] * 4
    carbs_cal = totals["carbs"] * 4
    fat_cal = totals["fat"] * 9
    total_macro_cal = protein_cal + carbs_cal + fat_cal
    
    if total_macro_cal > 0:
        totals["protein_pct"] = round((protein_cal / total_macro_cal) * 100, 1)
        totals["carbs_pct"] = round((carbs_cal / total_macro_cal) * 100, 1)
        totals["fat_pct"] = round((fat_cal / total_macro_cal) * 100, 1)
    else:
        totals["protein_pct"] = 0.0
        totals["carbs_pct"] = 0.0
        totals["fat_pct"] = 0.0
        
    return totals


def get_all_classes() -> List[str]:
    """Return ordered list of supported class IDs."""
    return INDIAN_FOOD_CLASSES


def export_seed_json(output_path: str) -> None:
    """Export nutrition database as JSON seed file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(NUTRITION_DB, f, indent=2)
