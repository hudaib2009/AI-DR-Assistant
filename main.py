import os
from fastapi import FastAPI, UploadFile, File
import uvicorn
import numpy as np
import tensorflow as tf
from tensorflow import keras
from PIL import Image
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMAGE SIZE
IMG_SIZE = 128

# ---------------------------------------------
# ✅ Load Keras 3 Model Safely (Render Compatible)
# ---------------------------------------------
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(script_dir, "LCDT_converted.keras")

    print(f"🔍 Looking for model at: {model_path}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    model = keras.models.load_model(model_path)

    print("🔥 Model loaded successfully: LCDT_converted.keras")

except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    model = None


# ---------------------------------------------
# IMAGE PREPROCESSING
# ---------------------------------------------
def preprocess_image(image):
    image = image.convert("L")  # grayscale
    image = image.resize((IMG_SIZE, IMG_SIZE))
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=(0, -1))
    return image_array


# ---------------------------------------------
# HEALTH CHECK (Render needs this!)
# ---------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


# ---------------------------------------------
# PREDICTION ENDPOINT
# ---------------------------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded"}

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    img_array = preprocess_image(image)

    pred = model.predict(img_array)
    prediction = float(pred.squeeze())

    result = "Positive" if prediction > 0.5 else "Negative"

    return {
        "prediction": result,
        "raw_value": prediction,
    }


# ---------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------
@app.get("/")
def root():
    return {"message": "AI DR Assistant API is running with LCDT_converted.keras"}


# ---------------------------------------------
# LOCAL DEVELOPMENT SERVER
# ---------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
