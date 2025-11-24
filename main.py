import io
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import tensorflow as tf

app = FastAPI()

# -------------------------------
# Load Keras 3 model safely
# -------------------------------
model = None
try:
    model = tf.keras.models.load_model("LCDT_converted.keras")
    print("✅ Model loaded successfully.")
except Exception as e:
    print("❌ Failed to load model:", e)


# -------------------------------
# Health check (fixes Render/Host 404 spam)
# -------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# -------------------------------
# Preprocess function
# -------------------------------
def preprocess_image(image):
    image = image.convert("L")                 # grayscale if model expects 1 channel
    image = image.resize((128, 128))           # resize to match training setup
    img_array = np.array(image).astype("float32") / 255.0
    img_array = np.expand_dims(img_array, axis=-1)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


# -------------------------------
# Prediction endpoint with
# complete ASGI-safe error handling
# -------------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # --- Model not loaded ---
    if model is None:
        return JSONResponse(
            {"error": "Model failed to load"},
            status_code=500
        )

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

    except Exception as e:
        return JSONResponse(
            {"error": f"Invalid image: {e}"},
            status_code=400
        )

    try:
        img_array = preprocess_image(image)

        # Keras 3 safe call
        pred_tensor = model(img_array, training=False)
        pred_value = float(pred_tensor.numpy().squeeze())

        result = "Positive" if pred_value > 0.5 else "Negative"

        return {
            "prediction": result,
            "raw_value": pred_value
        }

    except Exception as e:
        # Prevent ASGI crash
        return JSONResponse(
            {"error": f"Inference error: {e}"},
            status_code=500
        )


# -------------------------------
# Root endpoint
# -------------------------------
@app.get("/")
async def root():
    return {"message": "AI DR Assistant API is running"}
