"""
FoodSense — standalone prediction test script.

Loads the trained CNN, predicts the class of a single food image,
looks up its nutrition info, and prints the result.

This is a proof-of-concept for single-item images ONLY — it does not
do multi-item detection (that's YOLO's job, added in a later phase).

Usage:
    python test_predict.py path/to/food_image.jpg
"""

import sys
import os
import json
import numpy as np
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Locate base directories whether run from F:\FoodSense or F:\FoodSense\backend-inference
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) if os.path.basename(SCRIPT_DIR) == "backend-inference" else SCRIPT_DIR

# ---- Config: paths matching project structure ----
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "weights", "food_classifier_mobilenet_20class.pt")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "weights", "food_classifier_mobilenet.pt")

NUTRITION_PATH = os.path.join(PROJECT_ROOT, "data", "nutrition_table.json")
CLASS_NAMES_PATH = os.path.join(PROJECT_ROOT, "data", "class_names.json")
IMAGE_SIZE = (224, 224)

# ImageNet normalization parameters used during training
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_image(image_path):
    """
    Must match EXACTLY what was used during training:
    1. RGB conversion
    2. Resize to 224x224 (Bilinear)
    3. Scale to [0.0, 1.0] float32
    4. Normalize with ImageNet mean and std
    5. Convert to tensor shape (1, 3, 224, 224)
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0  # scale to [0, 1]
    
    # ImageNet normalization: (x - mean) / std
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    
    # Transpose from (H, W, C) to (C, H, W) for PyTorch
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, axis=0)  # shape: (1, 3, 224, 224)
    return arr


def load_class_names(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # expects a list, index-aligned with model output


def load_nutrition_table(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # expects { "class_name": {"calories": ..., "protein": ..., ...} }


def load_pytorch_model(model_path, num_classes):
    import torch
    import torch.nn as nn
    from torchvision import models
    
    weights = None
    base_mobilenet = models.mobilenet_v2(weights=weights)
    in_features = base_mobilenet.classifier[1].in_features  # 1280
    
    # Custom head architecture matching training
    base_mobilenet.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, num_classes)
    )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state_dict = torch.load(model_path, map_location=device)
    base_mobilenet.load_state_dict(state_dict)
    base_mobilenet.to(device)
    base_mobilenet.eval()
    return base_mobilenet, device


def predict(image_path):
    class_names = load_class_names(CLASS_NAMES_PATH)
    nutrition_table = load_nutrition_table(NUTRITION_PATH)
    num_classes = len(class_names)

    print(f"Loading model from {MODEL_PATH} ...")
    
    # Try PyTorch loader
    try:
        import torch
        model, device = load_pytorch_model(MODEL_PATH, num_classes)
        is_pytorch = True
    except Exception as e:
        # Fallback to TensorFlow if available
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(MODEL_PATH)
            is_pytorch = False
        except Exception:
            raise RuntimeError(f"Could not load model from {MODEL_PATH}: {e}")

    print(f"Preprocessing image: {image_path}")
    input_arr = preprocess_image(image_path)

    print("Running prediction...")
    if is_pytorch:
        import torch
        with torch.no_grad():
            tensor = torch.from_numpy(input_arr).float().to(device)
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]
    else:
        # TensorFlow model prediction
        tf_input = np.transpose(input_arr, (0, 2, 3, 1))  # (1, 224, 224, 3)
        probabilities = model.predict(tf_input)[0]

    top_index = int(np.argmax(probabilities))
    predicted_class = class_names[top_index]
    confidence = float(probabilities[top_index])

    print("\n--- Prediction ---")
    print(f"Predicted class: {predicted_class}")
    print(f"Confidence: {confidence:.2%}")

    nutrition = nutrition_table.get(predicted_class)
    if nutrition is None:
        print(f"\nWARNING: No nutrition entry found for '{predicted_class}'. "
              f"Check that class names match exactly between the model, "
              f"class_names.json, and nutrition_table.json.")
    else:
        print("\n--- Nutrition Info ---")
        for key, value in nutrition.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_k, sub_v in value.items():
                    print(f"    {sub_k}: {sub_v}")
            else:
                print(f"  {key}: {value}")

    # Dynamic KNN Recommendation
    try:
        from pipeline.knn_recommender import FoodSenseKNNRecommender
        knn_engine = FoodSenseKNNRecommender()
        knn_swaps = knn_engine.recommend(predicted_class, k=2)
        if knn_swaps:
            print("\n--- KNN Healthy Alternatives (Dynamic 6D Distance) ---")
            for rank, swap in enumerate(knn_swaps, 1):
                print(f"Option #{rank}: {swap['name']}")
                print(f"  * Macros: {swap['calories']:.0f} kcal | {swap['protein']:.1f}g Protein | {swap['carbs']:.1f}g Carbs | {swap['fat']:.1f}g Fat | GI: {swap['glycemic_index']}")
                print(f"  * Dynamic Reason: {swap['reason']}")
    except Exception as e:
        print(f"[Note] KNN engine lookup: {e}")

    # Show top 3 predictions for a sanity check on confusable classes
    top3_idx = np.argsort(probabilities)[-3:][::-1]
    print("\n--- Top 3 Predictions ---")
    for idx in top3_idx:
        print(f"  {class_names[idx]}: {probabilities[idx]:.2%}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_predict.py path/to/food_image.jpg")
        sys.exit(1)

    predict(sys.argv[1])
