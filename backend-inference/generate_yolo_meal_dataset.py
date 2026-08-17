"""
FoodSense - Multi-Item Meal Dataset Generator for YOLO Training
Generates realistic multi-item meal scenes (thalis, plates, dining tables) with ground-truth YOLO annotations.
"""

import os
import sys
import random
import glob
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# Ensure python_packages is in path
sys.path.insert(0, r"F:\FoodSense\python_packages")

BASE_DIR = r"F:\FoodSense"
DATA_DIR = os.path.join(BASE_DIR, "data")
TRAIN_224_DIR = os.path.join(DATA_DIR, "train_224")
TEST_224_DIR = os.path.join(DATA_DIR, "test_224")

YOLO_DIR = os.path.join(DATA_DIR, "yolo_dataset")
IMG_TRAIN_DIR = os.path.join(YOLO_DIR, "images", "train")
IMG_VAL_DIR = os.path.join(YOLO_DIR, "images", "val")
LBL_TRAIN_DIR = os.path.join(YOLO_DIR, "labels", "train")
LBL_VAL_DIR = os.path.join(YOLO_DIR, "labels", "val")

for d in [IMG_TRAIN_DIR, IMG_VAL_DIR, LBL_TRAIN_DIR, LBL_VAL_DIR]:
    os.makedirs(d, exist_ok=True)

CLASS_NAMES_PATH = os.path.join(DATA_DIR, "class_names.json")
with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
    CLASS_NAMES = json.load(f)

CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}

CANVAS_SIZE = 640  # Standard YOLO input resolution


def create_dining_background(size=(640, 640)):
    """Generate realistic table/thali/plate backgrounds."""
    bg_types = ["wood_table", "white_marble", "steel_thali", "slate_dark", "ceramic_plate"]
    bg_choice = random.choice(bg_types)
    w, h = size
    
    if bg_choice == "wood_table":
        # Warm wooden dining table tone
        base_color = (random.randint(180, 215), random.randint(130, 165), random.randint(90, 120))
        bg = Image.new("RGB", (w, h), base_color)
        draw = ImageDraw.Draw(bg)
        for y in range(0, h, random.randint(25, 45)):
            line_color = (base_color[0] - random.randint(15, 30), base_color[1] - random.randint(15, 25), base_color[2] - random.randint(10, 20))
            draw.line([(0, y), (w, y)], fill=line_color, width=random.randint(1, 3))
    elif bg_choice == "white_marble":
        # Light marble/granite dining surface
        base_val = random.randint(225, 245)
        bg = Image.new("RGB", (w, h), (base_val, base_val - 3, base_val - 6))
    elif bg_choice == "steel_thali":
        # Steel/silver thali or brass platter surface
        base_val = random.randint(170, 205)
        bg = Image.new("RGB", (w, h), (base_val, base_val, base_val + 5))
        draw = ImageDraw.Draw(bg)
        draw.ellipse([(20, 20), (w - 20, h - 20)], outline=(base_val - 30, base_val - 30, base_val - 25), width=8)
    elif bg_choice == "slate_dark":
        # Modern dark slate surface
        base_val = random.randint(40, 75)
        bg = Image.new("RGB", (w, h), (base_val, base_val + 2, base_val + 5))
    else:
        # Ceramic platter
        bg = Image.new("RGB", (w, h), (240, 238, 230))
        draw = ImageDraw.Draw(bg)
        draw.ellipse([(15, 15), (w - 15, h - 15)], outline=(210, 205, 195), width=10)
        
    return bg


def collect_class_images(src_dir):
    """Collect image paths mapped by class."""
    class_map = {}
    for c in CLASS_NAMES:
        c_dir = os.path.join(src_dir, c)
        imgs = glob.glob(os.path.join(c_dir, "*.jpg"))
        if imgs:
            class_map[c] = imgs
    return class_map


def compose_meal_scene(class_map, num_items_range=(2, 4)):
    """Synthesize a multi-item meal scene with exact bounding boxes."""
    canvas = create_dining_background((CANVAS_SIZE, CANVAS_SIZE))
    num_items = random.randint(num_items_range[0], num_items_range[1])
    selected_classes = random.sample(list(class_map.keys()), num_items)
    
    # Define layout regions on 640x640 canvas (e.g. 2x2 grid or circular layout with jitter)
    slots = [
        (40, 40, 280, 280),
        (340, 40, 580, 280),
        (40, 340, 280, 580),
        (340, 340, 580, 580),
        (180, 180, 460, 460)  # Center slot
    ]
    random.shuffle(slots)
    
    bboxes = []  # format: (class_id, x_center, y_center, width, height) in normalized [0, 1]
    
    for i, cls in enumerate(selected_classes):
        img_path = random.choice(class_map[cls])
        with Image.open(img_path) as food_img:
            food_img = food_img.convert("RGB")
            
            # Random scaling (e.g. 200 to 270 px)
            target_size = random.randint(200, 270)
            food_img = food_img.resize((target_size, target_size), Image.Resampling.BILINEAR)
            
            # Random horizontal flip
            if random.random() > 0.5:
                food_img = food_img.transpose(Image.FLIP_LEFT_RIGHT)
                
            # Random slight brightness/contrast adjustment
            if random.random() > 0.4:
                enhancer = ImageEnhance.Brightness(food_img)
                food_img = enhancer.enhance(random.uniform(0.9, 1.1))
                
            # Slot position with jitter
            slot_x1, slot_y1, slot_x2, slot_y2 = slots[i]
            jitter_x = random.randint(-20, 20)
            jitter_y = random.randint(-20, 20)
            
            paste_x = max(10, min(CANVAS_SIZE - target_size - 10, slot_x1 + jitter_x))
            paste_y = max(10, min(CANVAS_SIZE - target_size - 10, slot_y1 + jitter_y))
            
            # Add circular/soft mask for natural plate appearance
            mask = Image.new("L", (target_size, target_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle([(0, 0), (target_size - 1, target_size - 1)], radius=random.randint(20, 50), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(1.5))
            
            canvas.paste(food_img, (paste_x, paste_y), mask)
            
            # Exact bounding box in absolute pixels
            x_min = paste_x
            y_min = paste_y
            x_max = paste_x + target_size
            y_max = paste_y + target_size
            
            # Convert to YOLO normalized format: [x_center, y_center, w, h] in [0, 1]
            x_center = (x_min + x_max) / (2.0 * CANVAS_SIZE)
            y_center = (y_min + y_max) / (2.0 * CANVAS_SIZE)
            norm_w = target_size / float(CANVAS_SIZE)
            norm_h = target_size / float(CANVAS_SIZE)
            
            class_id = CLASS_TO_IDX[cls]
            bboxes.append((class_id, x_center, y_center, norm_w, norm_h))
            
    return canvas, bboxes


def generate_dataset(num_train=1000, num_val=200):
    print("\n" + "="*70)
    print("STEP 1: Generating Multi-Item Meal Dataset for YOLO Object Detection")
    print("="*70)
    
    train_class_map = collect_class_images(TRAIN_224_DIR)
    test_class_map = collect_class_images(TEST_224_DIR)
    
    print(f"Collected source classes: {len(train_class_map)} training classes, {len(test_class_map)} validation classes")
    
    # Generate Train Split
    print(f"Composing {num_train} multi-item training meal scenes...")
    for idx in range(num_train):
        img, bboxes = compose_meal_scene(train_class_map, num_items_range=(2, 4))
        
        img_name = f"meal_train_{idx:05d}.jpg"
        lbl_name = f"meal_train_{idx:05d}.txt"
        
        img_path = os.path.join(IMG_TRAIN_DIR, img_name)
        lbl_path = os.path.join(LBL_TRAIN_DIR, lbl_name)
        
        img.save(img_path, "JPEG", quality=95)
        with open(lbl_path, "w") as f:
            for bbox in bboxes:
                f.write(f"{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n")
                
        if (idx + 1) % 250 == 0 or (idx + 1) == num_train:
            print(f"  Generated {idx+1}/{num_train} training meal images...")
            
    # Generate Validation Split
    print(f"Composing {num_val} multi-item validation meal scenes...")
    for idx in range(num_val):
        img, bboxes = compose_meal_scene(test_class_map, num_items_range=(2, 4))
        
        img_name = f"meal_val_{idx:05d}.jpg"
        lbl_name = f"meal_val_{idx:05d}.txt"
        
        img_path = os.path.join(IMG_VAL_DIR, img_name)
        lbl_path = os.path.join(LBL_VAL_DIR, lbl_name)
        
        img.save(img_path, "JPEG", quality=95)
        with open(lbl_path, "w") as f:
            for bbox in bboxes:
                f.write(f"{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n")
                
        if (idx + 1) % 100 == 0 or (idx + 1) == num_val:
            print(f"  Generated {idx+1}/{num_val} validation meal images...")
            
    # Write data.yaml for YOLO training
    data_yaml_path = os.path.join(YOLO_DIR, "data.yaml")
    yaml_content = f"""# FoodSense YOLO Multi-Item Food Detection Dataset
path: {YOLO_DIR.replace(chr(92), '/')}
train: images/train
val: images/val

names:
"""
    for idx, c in enumerate(CLASS_NAMES):
        yaml_content += f"  {idx}: {c}\n"
        
    with open(data_yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
        
    print(f"\n[Step 1 Confirmation] YOLO multi-item dataset created successfully!")
    print(f"  Train images: {num_train} in {IMG_TRAIN_DIR}")
    print(f"  Val images:   {num_val} in {IMG_VAL_DIR}")
    print(f"  Config:       {data_yaml_path}")
    return data_yaml_path


if __name__ == "__main__":
    generate_dataset(num_train=800, num_val=160)
