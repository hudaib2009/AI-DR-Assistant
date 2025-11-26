# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import tensorflow as tf
import os
from fastapi.responses import FileResponse

# -----------------------------
# App Initialization
# -----------------------------
app = FastAPI(title="AI DR Assistant API")

# Enable CORS (if frontend calls from another domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html at the root
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# -----------------------------
# Model Loading
# -----------------------------
MODEL_PATH = "LCDT_converted.keras"
model = None

if os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print("🔥 Model loaded successfully:", MODEL_PATH)
    except Exception as e:
        print("❌ Failed to load model:", e)
else:
    print("❌ Model not found at:", MODEL_PATH)

# -----------------------------
# Utility: Image Preprocessing
# -----------------------------
def preprocess_image(image: Image.Image):
    # Resize to your model input size
    image = image.resize((128, 128))
    img_array = tf.keras.utils.img_to_array(image)
    img_array = tf.expand_dims(img_array, 0)  # Add batch dimension
    img_array = img_array / 255.0  # Normalize if needed
    return img_array

# -----------------------------
# Health Check
# -----------------------------
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}

# -----------------------------
# Prediction Endpoint
# -----------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global model
    if model is None:
        return {"error": "Model not loaded"}

    try:
        # Read and preprocess image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = preprocess_image(image)

        # Keras 3 / TFSMLayer safe inference
        pred = model(img_array, training=False).numpy()
        prediction = float(pred.squeeze())

        # Interpret result
        result = "Positive" if prediction > 0.5 else "Negative"

        return {
            "prediction": result,
            "raw_value": prediction,
        }
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Main Uvicorn entry (optional for local testing)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
