"""
FoodSense — Real & Multi-Scale Large-Dish Dataset Generator
Generates realistic large-format scenes (60-90% frame coverage for dosas, naans, chapatis, pizzas, thalis)
and directly incorporates real cropped dish images into YOLO training.
"""

import os
import sys
import glob
import random
import json
import shutil
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

sys.path.insert(0, r"F:\FoodSense\python_packages")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

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

LARGE_FORMAT_CLASSES = [
    "masala_dosa",
    "butter_naan",
    "chapati",
    "pizza",
    "chole_bhature",
    "pav_bhaji"
]

CANVAS_SIZE = 640


def create_table_background(size=(640, 640)):
    """Generate realistic table/thali/cloth background textures."""
    bg_types = ["wood", "marble", "dark_slate", "granite", "steel_plate"]
    choice = random.choice(bg_types)
    w, h = size

    if choice == "wood":
        base = (random.randint(185, 215), random.randint(140, 165), random.randint(95, 120))
        img = Image.new("RGB", (w, h), base)
        draw = ImageDraw.Draw(img)
        for y in range(0, h, random.randint(25, 45)):
            c = (base[0] - random.randint(15, 25), base[1] - random.randint(15, 20), base[2] - 10)
            draw.line([(0, y), (w, y)], fill=c, width=random.randint(1, 3))
        return img
    elif choice == "marble":
        v = random.randint(230, 248)
        return Image.new("RGB", (w, h), (v, v - 3, v - 6))
    elif choice == "dark_slate":
        v = random.randint(45, 75)
        return Image.new("RGB", (w, h), (v, v + 2, v + 4))
    elif choice == "steel_plate":
        v = random.randint(180, 210)
        img = Image.new("RGB", (w, h), (v, v, v + 5))
        draw = ImageDraw.Draw(img)
        draw.ellipse([(15, 15), (w - 15, h - 15)], outline=(v - 30, v - 30, v - 25), width=6)
        return img
    else:
        v = random.randint(215, 235)
        return Image.new("RGB", (w, h), (v, v - 5, v - 10))


def collect_images_by_class(src_dir):
    class_map = {}
    for c in CLASS_NAMES:
        c_dir = os.path.join(src_dir, c)
        imgs = glob.glob(os.path.join(c_dir, "*.jpg"))
        if imgs:
            class_map[c] = imgs
    return class_map


def compose_large_dish_hero_scene(class_map, hero_class):
    """
    Compose a dining scene where a large dish (e.g. Masala Dosa) takes 60-90% of the canvas,
    accompanied by 1-2 smaller side items (chai, bowls, etc.).
    """
    canvas = create_table_background((CANVAS_SIZE, CANVAS_SIZE))
    bboxes = []

    hero_img_path = random.choice(class_map[hero_class])
    with Image.open(hero_img_path) as hero_img:
        hero_img = hero_img.convert("RGB")
        if random.random() > 0.5:
            hero_img = hero_img.transpose(Image.FLIP_LEFT_RIGHT)

        # Scale hero dish to span 60% to 90% of the canvas (380 to 570 px)
        hero_w = random.randint(420, 580)
        hero_h = random.randint(280, 480)
        hero_resized = hero_img.resize((hero_w, hero_h), Image.Resampling.BILINEAR)

        # Center or lower-center position
        hero_x = (CANVAS_SIZE - hero_w) // 2 + random.randint(-20, 20)
        hero_y = CANVAS_SIZE - hero_h - random.randint(15, 60)
        hero_x = max(10, min(CANVAS_SIZE - hero_w - 10, hero_x))
        hero_y = max(10, min(CANVAS_SIZE - hero_h - 10, hero_y))

        # Soft mask
        mask = Image.new("L", (hero_w, hero_h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), (hero_w - 1, hero_h - 1)], radius=random.randint(25, 60), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(2))

        canvas.paste(hero_resized, (hero_x, hero_y), mask)

        # Hero Bounding Box
        x_center = (hero_x + hero_w / 2.0) / CANVAS_SIZE
        y_center = (hero_y + hero_h / 2.0) / CANVAS_SIZE
        norm_w = hero_w / float(CANVAS_SIZE)
        norm_h = hero_h / float(CANVAS_SIZE)
        bboxes.append((CLASS_TO_IDX[hero_class], x_center, y_center, norm_w, norm_h))

    # Add 1-2 small side bowls or chai in top regions
    side_candidates = [c for c in ["chai", "pav_bhaji", "dal_makhani", "kadai_paneer", "dhokla", "idli", "pakode"] if c in class_map]
    num_sides = random.randint(1, 2)
    selected_sides = random.sample(side_candidates, min(num_sides, len(side_candidates)))

    top_slots = [(40, 25, 200, 185), (CANVAS_SIZE - 220, 25, CANVAS_SIZE - 40, 185)]
    random.shuffle(top_slots)

    for i, side_cls in enumerate(selected_sides):
        side_img_path = random.choice(class_map[side_cls])
        with Image.open(side_img_path) as side_img:
            side_img = side_img.convert("RGB")
            side_size = random.randint(130, 175)
            side_resized = side_img.resize((side_size, side_size), Image.Resampling.BILINEAR)

            slot_x1, slot_y1, slot_x2, slot_y2 = top_slots[i]
            paste_x = slot_x1 + random.randint(0, max(0, (slot_x2 - slot_x1) - side_size))
            paste_y = slot_y1 + random.randint(0, max(0, (slot_y2 - slot_y1) - side_size))

            side_mask = Image.new("L", (side_size, side_size), 0)
            draw_side = ImageDraw.Draw(side_mask)
            draw_side.rounded_rectangle([(0, 0), (side_size - 1, side_size - 1)], radius=random.randint(15, 35), fill=255)
            side_mask = side_mask.filter(ImageFilter.GaussianBlur(1.5))

            canvas.paste(side_resized, (paste_x, paste_y), side_mask)

            sx_center = (paste_x + side_size / 2.0) / CANVAS_SIZE
            sy_center = (paste_y + side_size / 2.0) / CANVAS_SIZE
            snorm_w = side_size / float(CANVAS_SIZE)
            snorm_h = side_size / float(CANVAS_SIZE)
            bboxes.append((CLASS_TO_IDX[side_cls], sx_center, sy_center, snorm_w, snorm_h))

    return canvas, bboxes


def add_real_single_item_annotations(class_map, img_dir, lbl_dir, split="train", multiplier=2):
    """
    Directly annotate real photos as full-frame single dish detections.
    Dish occupies 80-96% of the frame.
    """
    count = 0
    for cls in LARGE_FORMAT_CLASSES:
        if cls not in class_map:
            continue
        imgs = class_map[cls]
        for img_path in imgs:
            for rep in range(multiplier):
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    w, h = img.size

                    # Random slight zoom/crop
                    margin_pct = random.uniform(0.02, 0.08)
                    x1 = int(w * margin_pct)
                    y1 = int(h * margin_pct)
                    x2 = int(w * (1 - margin_pct))
                    y2 = int(h * (1 - margin_pct))

                    box_w = (x2 - x1) / float(w)
                    box_h = (y2 - y1) / float(h)
                    x_c = (x1 + x2) / (2.0 * w)
                    y_c = (y1 + y2) / (2.0 * h)

                    out_img_name = f"real_large_{cls}_{split}_{count:05d}.jpg"
                    out_lbl_name = f"real_large_{cls}_{split}_{count:05d}.txt"

                    img.resize((640, 640), Image.Resampling.BILINEAR).save(os.path.join(img_dir, out_img_name), "JPEG", quality=95)

                    with open(os.path.join(lbl_dir, out_lbl_name), "w") as f:
                        f.write(f"{CLASS_TO_IDX[cls]} {x_c:.6f} {y_c:.6f} {box_w:.6f} {box_h:.6f}\n")

                    count += 1
    return count


def build_enhanced_yolo_dataset():
    print("="*75)
    print("BUILDING ENHANCED YOLO TRAINING DATASET WITH REAL & LARGE-DISH SCENES")
    print("="*75)

    train_map = collect_images_by_class(TRAIN_224_DIR)
    test_map = collect_images_by_class(TEST_224_DIR)

    # 1. Add real full-frame single dish annotations
    print("\nAdding real single-dish annotated images for large-format classes...")
    n_real_train = add_real_single_item_annotations(train_map, IMG_TRAIN_DIR, LBL_TRAIN_DIR, split="train", multiplier=2)
    n_real_val = add_real_single_item_annotations(test_map, IMG_VAL_DIR, LBL_VAL_DIR, split="val", multiplier=1)
    print(f"  * Added {n_real_train} real training images for large dishes")
    print(f"  * Added {n_real_val} real validation images for large dishes")

    # 2. Add hero large-dish composite dining scenes
    print("\nSynthesizing hero large-dish dining table scenes (60-90% frame span)...")
    num_hero_train = 400
    for i in range(num_hero_train):
        hero_cls = random.choice(LARGE_FORMAT_CLASSES)
        scene_img, bboxes = compose_large_dish_hero_scene(train_map, hero_cls)

        name = f"hero_large_train_{i:05d}"
        scene_img.save(os.path.join(IMG_TRAIN_DIR, f"{name}.jpg"), "JPEG", quality=95)
        with open(os.path.join(LBL_TRAIN_DIR, f"{name}.txt"), "w") as f:
            for bbox in bboxes:
                f.write(f"{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n")

    num_hero_val = 80
    for i in range(num_hero_val):
        hero_cls = random.choice(LARGE_FORMAT_CLASSES)
        scene_img, bboxes = compose_large_dish_hero_scene(test_map, hero_cls)

        name = f"hero_large_val_{i:05d}"
        scene_img.save(os.path.join(IMG_VAL_DIR, f"{name}.jpg"), "JPEG", quality=95)
        with open(os.path.join(LBL_VAL_DIR, f"{name}.txt"), "w") as f:
            for bbox in bboxes:
                f.write(f"{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n")

    print(f"  * Added {num_hero_train} hero large-dish training scenes")
    print(f"  * Added {num_hero_val} hero large-dish validation scenes")

    # Count total images in training & validation sets
    tot_train = len(glob.glob(os.path.join(IMG_TRAIN_DIR, "*.jpg")))
    tot_val = len(glob.glob(os.path.join(IMG_VAL_DIR, "*.jpg")))

    print("\n" + "="*75)
    print(f"DATASET PREPARATION COMPLETE:")
    print(f"  * Total Training Images:   {tot_train}")
    print(f"  * Total Validation Images: {tot_val}")
    print("="*75)


if __name__ == "__main__":
    build_enhanced_yolo_dataset()
