from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from PIL import Image, ImageOps
import io
import base64

app = FastAPI(title="JMI LCDT API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
# ...
# Load the model
IMG_SIZE = 128
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(script_dir, 'LCDT_converted.keras')
    model = tf.keras.models.load_model(model_path, compile=False)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

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
        image = Image.open(io.BytesIO(contents)).convert('L')
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
            status = "danger"
        else:
            result = "Normal"
            confidence = 1 - prediction
            status = "normal"
        
        # Convert image to base64 for frontend display
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return JSONResponse({
            "result": result,
            "confidence": float(confidence),
            "prediction_score": float(prediction),
            "status": status,
            "image_base64": img_base64,
            "message": f"Prediction: {result} (Confidence: {confidence:.2f})"
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
            status = "danger"
        else:
            result = "Normal"
            confidence = 1 - prediction
            status = "normal"
        
        return JSONResponse({
            "result": result,
            "confidence": float(confidence),
            "prediction_score": float(prediction),
            "status": status,
            "message": f"Prediction: {result} (Confidence: {confidence:.2f})"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)