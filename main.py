@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded"}

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    img_array = preprocess_image(image)

    # Keras 3 / TFSMLayer safe inference
    pred = model(img_array, training=False).numpy()
    prediction = float(pred.squeeze())

    result = "Positive" if prediction > 0.5 else "Negative"

    return {
        "prediction": result,
        "raw_value": prediction,
    }
