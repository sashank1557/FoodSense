# FoodSense: AI-Powered Indian Food Recognition & Nutrition Intelligence

[![Vite](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61dafb.svg)](https://vitejs.dev/)
[![Express](https://img.shields.io/badge/Relay-Express.js%20(Node%20v20)-green.svg)](https://expressjs.com/)
[![Flask](https://img.shields.io/badge/Inference-Flask%20%2B%20PyTorch-orange.svg)](https://pytorch.org/)
[![YOLOv8](https://img.shields.io/badge/Detection-YOLOv8n-00FFFF.svg)](https://ultralytics.com/)
[![Accuracy](https://img.shields.io/badge/Top--1%20Accuracy-85.55%25-brightgreen.svg)]()

FoodSense is an end-to-end computer vision and nutritional intelligence application designed specifically for Indian cuisine. Users upload or capture a photo of a meal (single dish or complex multi-item thalis), and FoodSense automatically localizes every individual item via **YOLOv8**, classifies each dish using a transfer-learned **MobileNetV2 CNN (85.55% Top-1 Accuracy)**, looks up comprehensive macronutrients & glycemic indices, and recommends healthier dietary alternatives using a **6-Dimensional K-Nearest Neighbors (KNN)** optimization engine in normalized nutrient space.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REACT 18 + VITE FRONTEND                          │
│  - Drag & Drop / Mobile Camera Capture (getUserMedia + Canvas)             │
│  - Responsive Bounding Box Canvas (Letterbox-Aware Dynamic Scaling)         │
│  - Interactive Portion Scaling (0.5x - 3.0x) & Real-time Alternative Swaps  │
│  - Server Cold-Start Countdown & Health Monitoring                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP Multipart Form-Data (image/file)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXPRESS GATEWAY RELAY (Node.js)                      │
│  - Memory-buffered Multer uploads (15MB limit, strict MIME filter)          │
│  - In-Memory Rate Limiting (30 analyses / 15 min per IP)                    │
│  - Unified Upstream Health Check Proxy (/api/health)                        │
│  - 45s Generous Cold-Start Upstream Timeout (503 Handshake)                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP Proxy (/analyze)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLASK AI INFERENCE ENGINE (PyTorch)                     │
│                                                                             │
│  1. [YOLOv8n Meal Localizer]                                               │
│     - Detects food bowls, breads, snacks with IoU Deduplication & Padding   │
│                                                                             │
│  2. [MobileNetV2 20-Class CNN Classifier] (85.55% Validation Top-1 Acc)    │
│     - Softmax confidence prediction over 20 Indian culinary categories      │
│                                                                             │
│  3. [Nutritional Registry & Macro Calculator]                              │
│     - Calories, Protein, Carbs, Fat, Fiber, Glycemic Index (GI), Servings   │
│                                                                             │
│  4. [6D KNN Recommendation Engine]                                         │
│     - Feature space: [Calories, Protein, Carbs, Fat, Fiber, GI]            │
│     - Category-constrained Euclidean distance with dynamic delta reasons    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🍛 Supported Food Classes (20 Categories)

Trained and validated on **6,271 images** from the Hugging Face `rajistics/indian_food_images` benchmark dataset:

| # | Class Name | Category | Standard Portion | Baseline Calories | Glycemic Index (GI) |
|---|:---|:---|:---|:---|:---|
| 1 | `burger` | Snacks | 1 burger (150g) | 295 kcal | 65 (Medium) |
| 2 | `butter_naan` | Breads | 1 naan (90g) | 260 kcal | 71 (High) |
| 3 | `chai` | Beverages | 1 cup (150ml) | 90 kcal | 60 (Medium) |
| 4 | `chapati` | Breads | 1 piece (40g) | 120 kcal | 62 (Medium) |
| 5 | `chole_bhature` | Curries & Breads | 2 bhature + chole (300g)| 450 kcal | 68 (Medium) |
| 6 | `dal_makhani` | Lentils | 1 bowl (200g) | 280 kcal | 48 (Low) |
| 7 | `dhokla` | Breakfast | 4 pieces (120g) | 160 kcal | 35 (Low) |
| 8 | `fried_rice` | Rice Dishes | 1 plate (250g) | 330 kcal | 68 (Medium) |
| 9 | `idli` | Breakfast | 2 pieces (100g) | 130 kcal | 53 (Low) |
| 10 | `jalebi` | Sweets | 3 pieces (100g) | 360 kcal | 75 (High) |
| 11 | `kaathi_rolls` | Snacks | 1 roll (180g) | 380 kcal | 68 (Medium) |
| 12 | `kadai_paneer` | Curries | 1 bowl (200g) | 320 kcal | 45 (Low) |
| 13 | `kulfi` | Sweets | 1 stick (80g) | 190 kcal | 60 (Medium) |
| 14 | `masala_dosa` | Breakfast | 1 dosa + aloo (200g) | 250 kcal | 55 (Low) |
| 15 | `momos` | Snacks | 6 pieces (150g) | 210 kcal | 58 (Medium) |
| 16 | `paani_puri` | Snacks | 6 puris (120g) | 180 kcal | 60 (Medium) |
| 17 | `pakode` | Snacks | 1 plate (100g) | 310 kcal | 68 (Medium) |
| 18 | `pav_bhaji` | Curries & Breads | 2 pav + bhaji (250g) | 390 kcal | 65 (Medium) |
| 19 | `pizza` | Snacks | 2 slices (160g) | 410 kcal | 70 (High) |
| 20 | `samosa` | Snacks | 2 pieces (100g) | 260 kcal | 68 (Medium) |

---

## 🎯 Model Training & Evaluation Metrics

### 1. MobileNetV2 20-Class CNN Classifier
- **Architecture**: Pretrained `MobileNetV2` with Custom Head (`Dropout(0.3) -> Linear(1280, 256) -> ReLU -> BatchNorm -> Dropout(0.2) -> Linear(256, 20)`).
- **Training Strategy**: 2-stage transfer learning (Feature extraction head @ `lr=1e-3`, followed by fine-tuning top-30 layers @ `lr=1e-4` with cosine annealing).
- **Data Augmentation**: Color jitter (brightness/contrast $\pm 20\%$), random affine rotations ($\pm 15^\circ$), horizontal flips, and zoom crops.
- **Validation Accuracy**: **`85.55% Top-1 Accuracy`** on 941 held-out test images.
- **Weight Size**: `10.8 MB` (`food_classifier_mobilenet_20class.pt`).

### 2. YOLOv8n Meal Object Detector
- **Architecture**: Ultralytics YOLOv8 Nano (`3.2M` parameters).
- **Dataset**: 960 synthesized multi-dish scenes with realistic thali/tabletop backgrounds and IoU bounding box annotations.
- **Bounding Box Loss**: **`0.261`** after 25 epochs.
- **Inference Latency**: **`~45ms`** on standard x86 CPU.
- **Weight Size**: `6.2 MB` (`food_detector_yolov8n.pt`).

### 3. 6D KNN Recommendation Engine
- **Feature Space**: $\mathbf{x} = [\text{Calories}, \text{Protein}, \text{Carbs}, \text{Fat}, \text{Fiber}, \text{Glycemic Index}] \in \mathbb{R}^6$.
- **Database**: 53 indexed authentic culinary dishes across 9 categories (`Breads`, `Curries`, `Lentils`, `Breakfast`, `Snacks`, `Sweets`, `Rice Dishes`, `Beverages`).
- **Algorithm**: Min-Max feature normalized Euclidean distance constrained by target culinary category and calorie reduction filter ($\text{Cal}_{\text{candidate}} \le \text{Cal}_{\text{base}}$).
- **Dynamic Reasoning**: Real-time delta sentence generator computing percentage calorie cuts, fat reductions, fiber multipliers, and glycemic improvements.

---

## 🚀 Live Production Deployment

| Service | Platform | Environment URL | Purpose |
|:---|:---|:---|:---|
| **Frontend** | Vercel | `https://foodsense-ai.vercel.app` | React SPA UI & Camera Scanner |
| **Relay Gateway** | Railway | `https://foodsense-relay.up.railway.app` | Express Proxy, Multer, Rate Limiting |
| **Inference Engine**| Railway | `https://foodsense-inference.up.railway.app` | PyTorch YOLO + CNN + KNN Backend |

### ⚡ Free-Tier Cold-Start Handling
Railway free-tier containers hibernate after 15 minutes of inactivity. FoodSense implements a robust resilience strategy:
1. **Express Upstream Timeout**: Set to **45 seconds** to prevent premature gateway drops during container spin-up.
2. **Cold-Start Error Handshake**: If Flask is starting, Express catches connection refusals and returns `503 INFERENCE_BACKEND_COLD_START`.
3. **Frontend Awareness**: If an inference request exceeds 3 seconds, the UI transitions to an informative *"Waking up AI Inference Engine (PyTorch & ML models loading into memory)..."* progress indicator with a real-time elapsed timer and instant retry action.
4. **Measured Real Cold-Start Duration**: **14 to 22 seconds** on first request; subsequent requests execute in **~180ms**.

---

## 💻 Local Setup & Development Guide

### Prerequisites
- Node.js `v18+` or `v20+`
- Python `3.10+` or `3.11+`
- Git

### 1. Clone Repository
```bash
git clone https://github.com/your-username/foodsense.git
cd foodsense
```

### 2. Start Flask Inference Backend
```bash
cd backend-inference
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Server runs on http://127.0.0.1:5000
```

### 3. Start Express Relay Layer
```bash
cd ../backend-express
npm install
npm start
# Server runs on http://127.0.0.1:3001
```

### 4. Start React Frontend
```bash
cd ../frontend
npm install
npm run dev
# App opens on http://localhost:5173
```

---

## 🧪 Comprehensive Test Suites

FoodSense includes standalone test suites for each architecture layer:

```bash
# 1. Test standalone CNN single-image classification + KNN recommendation
python backend-inference/test_predict.py data/test_224/pizza/test_00033.jpg

# 2. Test YOLO detection + multi-dish cropping + classification
python backend-inference/test_detect_and_classify.py data/yolo_dataset/images/val/meal_val_00010.jpg

# 3. Test Flask HTTP endpoints (GET /health, GET /classes, POST /analyze)
python backend-inference/test_flask_api.py

# 4. Test Express Relay Gateway end-to-end (Client -> Express -> Flask -> Client)
python backend-express/test_express_relay.py
```

---

## 📜 Standardized Response Contract

```json
{
  "status": "success",
  "meal_id": "meal_3f88844d",
  "items": [
    {
      "label": "pakode",
      "display_name": "Pakode (Vegetable Pakora)",
      "confidence": 0.9931,
      "bbox": [333, 52, 557, 277],
      "portion": "1 plate (100g)",
      "macros": {
        "calories": 310.0,
        "protein": 6.0,
        "carbs": 26.0,
        "fat": 20.0,
        "fiber": 3.0,
        "gi": 68
      },
      "healthy_alternative": {
        "name": "Baked Whole Wheat & Sweet Potato Samosa",
        "macros": {
          "calories": 135.0,
          "protein": 4.8,
          "carbs": 23.0,
          "fat": 3.0,
          "fiber": 4.2,
          "gi": 50
        },
        "reason": "Saves 175 kcal (56% fewer calories), cuts fat by 17.0g (85% reduction), significantly lower gi of 50 (vs 68) for steady blood glucose."
      }
    }
  ],
  "meal_summary": {
    "total_items": 1,
    "total_calories": 310.0,
    "total_protein": 6.0,
    "total_carbs": 26.0,
    "total_fat": 20.0,
    "total_fiber": 3.0,
    "average_gi": 68.0,
    "dietary_note": "High-fat dish. Balance with steamed grains or fresh salad."
  },
  "processing_time_ms": 178.4
}
```

---

## 🛡️ License
MIT License. Developed for intelligent health, dietary awareness, and computer vision research.
