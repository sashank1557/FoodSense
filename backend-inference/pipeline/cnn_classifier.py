"""
FoodSense - CNN Classifier Module (Phase 2)
MobileNetV2-based 19-class fine-grained Indian food classifier on 224x224 cropped images.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from typing import Dict, List, Tuple, Any, Optional
import json
import numpy as np

from .nutrition_db import INDIAN_FOOD_CLASSES

# ImageNet standard normalization parameters
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Confusable pairs for heuristic refinement and validation
CONFUSABLE_CLASSES = [
    ("roti", "naan", "Both are flatbreads; naan typically has browner blistered spots and oblong shape."),
    ("poori", "bhatura", "Deep-fried breads; poori is smaller, made with whole wheat."),
    ("poha", "upma", "Breakfast dishes; poha has distinct yellow flattened flakes, upma has grainy semolina texture."),
    ("gulab_jamun", "medu_vada", "Brown spherical/torus items; gulab jamun has glossy syrup sheen, vada has center hole & savory crust."),
    ("dal_tadka", "chole", "Yellow/brown gravies; chole contains visible round chickpeas, dal has smooth/broken lentil texture."),
    ("paneer_butter_masala", "chole", "Rich gravies; paneer contains white cubic blocks.")
]


class FoodSenseCNN(nn.Module):
    """MobileNetV2 Transfer Learning Architecture for 19-Class Indian Food Classification."""
    def __init__(self, num_classes: int = len(INDIAN_FOOD_CLASSES), pretrained: bool = True):
        super(FoodSenseCNN, self).__init__()
        weights = models.MobileNet_V2_Weights.DEFAULT if pretrained else None
        base_mobilenet = models.mobilenet_v2(weights=weights)
        
        # Keep feature extractor backbone
        self.features = base_mobilenet.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Custom fine-tuned classification head for 19 classes
        in_features = base_mobilenet.classifier[1].in_features  # 1280
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(512, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract 1280-d feature embedding before classifier head."""
        x = self.features(x)
        x = self.avgpool(x)
        return torch.flatten(x, 1)


class IndianFoodClassifier:
    """Inference & Evaluation Engine for Food Classification."""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None, classes: Optional[List[str]] = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
            
        # Check if 20-class weights or config exists
        summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "training_evaluation_summary.json")
        if classes is None:
            if os.path.exists(summary_path):
                try:
                    with open(summary_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        self.classes = meta.get("classes", INDIAN_FOOD_CLASSES)
                except Exception:
                    self.classes = INDIAN_FOOD_CLASSES
            else:
                self.classes = INDIAN_FOOD_CLASSES
        else:
            self.classes = classes

        self.num_classes = len(self.classes)
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.idx_to_class = {idx: cls for idx, cls in enumerate(self.classes)}
        
        # Input transform: Resize to 224x224, Convert to Tensor, Normalize (ImageNet parameters)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
        
        # Initialize model
        self.model = FoodSenseCNN(num_classes=self.num_classes, pretrained=False)
        
        if model_path is None:
            weights_20 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "weights", "food_classifier_mobilenet_20class.pt")
            weights_main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "weights", "food_classifier_mobilenet.pt")
            if os.path.exists(weights_20):
                model_path = weights_20
            elif os.path.exists(weights_main):
                model_path = weights_main

        if model_path and os.path.exists(model_path):
            try:
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                print(f"[FoodClassifier] Successfully loaded {self.num_classes}-class weights from: {model_path}")
            except Exception as e:
                print(f"[FoodClassifier] Warning: Could not load weights from {model_path}: {e}")
        
        self.model.to(self.device)
        self.model.eval()

    def predict_crop(self, pil_image: Image.Image, top_k: int = 3) -> Dict[str, Any]:
        """
        Classify a single PIL image crop (224x224 or arbitrary size).
        Returns top prediction, confidence score, and top-k alternative predictions.
        """
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
            
        tensor_img = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensor_img)
            probabilities = torch.softmax(outputs, dim=1).squeeze(0)
            
        top_probs, top_indices = torch.topk(probabilities, min(top_k, self.num_classes))
        
        top_probs = top_probs.cpu().numpy().tolist()
        top_indices = top_indices.cpu().numpy().tolist()
        
        top_class_id = self.idx_to_class[top_indices[0]]
        top_confidence = round(float(top_probs[0]), 4)
        
        top_k_list = []
        for prob, idx in zip(top_probs, top_indices):
            top_k_list.append({
                "class_id": self.idx_to_class[idx],
                "confidence": round(float(prob), 4)
            })
            
        return {
            "class_id": top_class_id,
            "confidence": top_confidence,
            "top_k": top_k_list
        }

    def predict_batch(self, pil_images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Classify a list of cropped items in a single forward pass."""
        if not pil_images:
            return []
        return [self.predict_crop(img) for img in pil_images]

    def save_weights(self, save_path: str):
        """Save model state dictionary."""
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        torch.save(self.model.state_dict(), save_path)
        print(f"[FoodClassifier] Saved model weights to {save_path}")
