"""
FoodSense - MobileNetV2 Transfer Learning & Fine-Tuning Pipeline
Trained on rajistics/indian_food_images dataset (20 classes, 6,269 images)
"""

import os
import sys
import time
import json
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import classification_report, confusion_matrix

BASE_DIR = r"F:\FoodSense"
DATA_DIR = os.path.join(BASE_DIR, "data")
TRAIN_DIR = os.path.join(DATA_DIR, "train_224")
TEST_DIR = os.path.join(DATA_DIR, "test_224")
WEIGHTS_DIR = os.path.join(BASE_DIR, "backend-inference", "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# ImageNet Standard Preprocessing Parameters (Must be matched at inference)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_data_loaders(batch_size=32):
    """Step 1: Build training and test data loaders with augmentation."""
    print("\n" + "="*70)
    print("STEP 1: Setting up Data Loaders & Augmentation Pipeline")
    print("="*70)

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.RandomAffine(degrees=0, scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_transform)
    test_dataset = datasets.ImageFolder(TEST_DIR, transform=test_transform)

    class_names = train_dataset.classes
    num_classes = len(class_names)

    print(f"Loaded Train Dataset: {len(train_dataset)} images across {num_classes} classes")
    print(f"Loaded Test Dataset:  {len(test_dataset)} images across {num_classes} classes")
    print(f"Class list ({num_classes}): {class_names}")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, test_loader, class_names, train_dataset, test_dataset


def build_model(num_classes=20):
    """Step 2: Load MobileNetV2 pretrained backbone & attach custom 20-class head."""
    print("\n" + "="*70)
    print(f"STEP 2: Building MobileNetV2 Architecture with {num_classes}-Class Head")
    print("="*70)

    weights = models.MobileNet_V2_Weights.DEFAULT
    model = models.mobilenet_v2(weights=weights)

    in_features = model.classifier[1].in_features  # 1280

    # Custom classification head
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, num_classes)
    )

    print(f"Model Initialized: MobileNetV2 Backbone (1280 features) -> Linear(512) -> BN -> ReLU -> Linear({num_classes})")
    return model


def train_frozen_head(model, train_loader, test_loader, device, epochs=4):
    """Step 3: Train only classification head with frozen backbone."""
    print("\n" + "="*70)
    print("STEP 3: Training Classification Head (Backbone Frozen)")
    print("="*70)

    # Freeze backbone
    for param in model.features.parameters():
        param.requires_grad = False

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)

    model.to(device)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        t0 = time.time()

        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

            if (batch_idx + 1) % 40 == 0 or (batch_idx + 1) == len(train_loader):
                print(f"  [Epoch {epoch}/{epochs}] Batch {batch_idx+1}/{len(train_loader)} - Loss: {running_loss/total:.4f} - Acc: {(correct/total)*100:.1f}%")

        train_loss = running_loss / total
        train_acc = (correct / total) * 100
        elapsed = round(time.time() - t0, 1)

        # Quick validation on test set
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100
        print(f"-> Epoch {epoch}/{epochs} Done ({elapsed}s) | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.1f}% | Val Acc: {val_acc:.1f}%\n")

    return model


def fine_tune_top_layers(model, train_loader, test_loader, device, epochs=3):
    """Step 4: Unfreeze top layers and fine-tune with low learning rate."""
    print("\n" + "="*70)
    print("STEP 4: Fine-Tuning Top Backbone Layers (Unfreezing Layers 14-18)")
    print("="*70)

    # Unfreeze top feature layers (blocks 14 to 18)
    for idx, block in enumerate(model.features):
        if idx >= 14:
            for param in block.parameters():
                param.requires_grad = True

    # Differential learning rates: smaller for backbone, moderate for head
    backbone_params = [p for idx, block in enumerate(model.features) if idx >= 14 for p in block.parameters()]
    head_params = list(model.classifier.parameters())

    optimizer = optim.AdamW([
        {'params': backbone_params, 'lr': 1e-4},
        {'params': head_params, 'lr': 5e-4}
    ], weight_decay=1e-4)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        t0 = time.time()

        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

        scheduler.step()
        train_loss = running_loss / total
        train_acc = (correct / total) * 100
        elapsed = round(time.time() - t0, 1)

        # Validate
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100
        print(f"-> Fine-Tune Epoch {epoch}/{epochs} ({elapsed}s) | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.1f}% | Val Acc: {val_acc:.1f}%")

    return model


def evaluate_test_set(model, test_loader, class_names, device):
    """Step 5 & 6: Detailed test set evaluation, confusion matrix & per-class metrics."""
    print("\n" + "="*70)
    print("STEP 5 & 6: Test Set Evaluation & Per-Class Performance")
    print("="*70)

    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    overall_acc = (np.sum(all_preds == all_labels) / len(all_labels)) * 100
    print(f"\n==================================================")
    print(f"FINAL TEST SET ACCURACY: {overall_acc:.2f}% ({np.sum(all_preds == all_labels)}/{len(all_labels)} correct)")
    print(f"==================================================")

    # Classification Report
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)

    print(f"\n{'Class Name':<18} | {'Precision':>9} | {'Recall':>8} | {'F1-Score':>8} | {'Support':>7} | {'Status'}")
    print("-" * 75)

    weak_classes = []
    for c in class_names:
        metrics = report[c]
        prec = metrics["precision"] * 100
        rec = metrics["recall"] * 100
        f1 = metrics["f1-score"] * 100
        sup = int(metrics["support"])

        status = "Good"
        if f1 < 65.0 or rec < 60.0:
            status = "WEAK / LOW F1"
            weak_classes.append((c, f1, sup))

        print(f"{c:<18} | {prec:>8.1f}% | {rec:>7.1f}% | {f1:>7.1f}% | {sup:>7d} | {status}")

    print("-" * 75)

    # Confusion Matrix Analysis
    cm = confusion_matrix(all_labels, all_preds)
    
    # Identify top confusions (non-diagonal pairs)
    confusions = []
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            if i != j and cm[i][j] > 0:
                confusions.append((class_names[i], class_names[j], int(cm[i][j])))

    confusions.sort(key=lambda x: x[2], reverse=True)

    print("\nTop Confusable Class Pairs (True Label -> Predicted As):")
    for true_cls, pred_cls, count in confusions[:10]:
        print(f"  * {true_cls:<16} misclassified as -> {pred_cls:<16} ({count} instances)")

    if weak_classes:
        print("\nFlagged Weak / Low-Performance Classes:")
        for c, f1, sup in weak_classes:
            print(f"  * '{c}': F1-Score = {f1:.1f}%, Test Samples = {sup}")

    return overall_acc, report, cm, confusions, weak_classes


def export_and_document(model, class_names, overall_acc, report, confusions, weak_classes):
    """Step 7 & 8: Export model weights and document results."""
    print("\n" + "="*70)
    print("STEP 7 & 8: Exporting Model & Documentation")
    print("="*70)

    # Save weights
    export_path_20 = os.path.join(WEIGHTS_DIR, "food_classifier_mobilenet_20class.pt")
    export_path_main = os.path.join(WEIGHTS_DIR, "food_classifier_mobilenet.pt")

    torch.save(model.state_dict(), export_path_20)
    torch.save(model.state_dict(), export_path_main)
    print(f"[Export OK] Saved 20-class model weights to: {export_path_20}")
    print(f"[Export OK] Updated active model weights at:  {export_path_main}")

    # Summary payload
    summary = {
        "architecture": "MobileNetV2 Transfer Learning",
        "num_classes": len(class_names),
        "classes": class_names,
        "test_accuracy_pct": round(overall_acc, 2),
        "total_test_samples": 941,
        "preprocessing_pipeline": {
            "resize_dimensions": [224, 224],
            "interpolation": "BILINEAR",
            "channel_format": "RGB",
            "tensor_range": [0.0, 1.0],
            "normalization_mean": IMAGENET_MEAN,
            "normalization_std": IMAGENET_STD
        },
        "weak_classes": [{"class": c, "f1_score": round(f1, 2), "support": sup} for c, f1, sup in weak_classes],
        "top_confusions": [{"true_class": t, "predicted_class": p, "count": cnt} for t, p, cnt in confusions[:10]],
        "weights_file": export_path_20
    }

    summary_file = os.path.join(DATA_DIR, "training_evaluation_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[Documentation OK] Full evaluation summary saved to: {summary_file}")
    print("\n" + "="*70)
    print("FOODSENSE CLASSIFIER TRAINING & EVALUATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    return summary


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute Device: {device}")

    # Step 1: Data loaders
    train_loader, test_loader, class_names, train_ds, test_ds = get_data_loaders(batch_size=32)

    # Step 2: Build model
    model = build_model(num_classes=len(class_names))

    # Step 3: Train head (frozen backbone) - 4 epochs
    model = train_frozen_head(model, train_loader, test_loader, device, epochs=4)

    # Step 4: Fine-tune top layers - 3 epochs
    model = fine_tune_top_layers(model, train_loader, test_loader, device, epochs=3)

    # Step 5 & 6: Evaluate on test set
    overall_acc, report, cm, confusions, weak_classes = evaluate_test_set(model, test_loader, class_names, device)

    # Step 7 & 8: Export & document
    export_and_document(model, class_names, overall_acc, report, confusions, weak_classes)


if __name__ == "__main__":
    main()
