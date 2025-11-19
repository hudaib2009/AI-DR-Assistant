from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from PIL import Image, ImageOps
import io
import base64
import os

app = FastAPI(title="JMI LCDT API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model
IMG_SIZE = 128
model = None
try:
    from tensorflow.keras.utils import custom_object_scope
    with custom_object_scope({'Chest_XRay_CNN_CBAM': tf.keras.layers.Layer}):
        model = tf.keras.models.load_model('h.h5')
    print(f"Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def process_and_predict(image_bytes: bytes) -> dict:
    """Processes image bytes, runs prediction, and returns results."""
    if not model:
        raise HTTPException(status_code=503, detail="Model is not available")

    image = Image.open(io.BytesIO(image_bytes)).convert('L')
    image = image.resize((IMG_SIZE, IMG_SIZE))
    
    # Convert to array and normalize
    img_array = np.array(image) / 255.0
    img_array = img_array.reshape(1, IMG_SIZE, IMG_SIZE, 1)
    
    # Make prediction
    prediction = model.predict(img_array)[0][0]
    
    # Determine result
    if prediction > 0.5:
        result = "Danger Detected"
        confidence = prediction
    else:
        result = "Normal"
        confidence = 1 - prediction
    return {"result": result, "confidence": float(confidence), "prediction_score": float(prediction)}

@app.get("/")
async def root():
    return {"message": "JMI LCDT API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and process the image
        contents = await file.read()
        prediction_data = process_and_predict(contents)

        status = "danger" if prediction_data["result"] == "Danger Detected" else "normal"
        message = f"Prediction: {prediction_data['result']} (Confidence: {prediction_data['confidence']:.2f})"
        
        return JSONResponse({
            "result": prediction_data["result"],
            "confidence": prediction_data["confidence"],
            "prediction_score": prediction_data["prediction_score"],
            "status": status,
            "message": message
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/predict-base64")
async def predict_base64_image(image_data: dict):
    """Alternative endpoint that accepts base64 encoded images"""
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data["image"].split(",")[1])
        prediction_data = process_and_predict(image_bytes)

        status = "danger" if prediction_data["result"] == "Danger Detected" else "normal"
        message = f"Prediction: {prediction_data['result']} (Confidence: {prediction_data['confidence']:.2f})"
        
        return JSONResponse({
            "result": prediction_data["result"],
            "confidence": prediction_data["confidence"],
            "prediction_score": prediction_data["prediction_score"],
            "status": status,
            "message": message
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
