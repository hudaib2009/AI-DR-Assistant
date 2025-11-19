import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image, ImageOps
import os

IMG_SIZE = 128

st.title("JMI Project - LCDT(X-b)")

script_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(script_dir, 'h.h5')
model = tf.keras.models.load_model(model_path, compile=False)

st.write("Upload a chest X-ray image (JPEG/PNG) for classification.")

uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert('L')
    image = image.resize((IMG_SIZE, IMG_SIZE))
    st.image(image, caption='Uploaded X-ray', width=300)

    img_array = np.array(image) / 255.0
    img_array = img_array.reshape(1, IMG_SIZE, IMG_SIZE, 1)

    prediction = model.predict(img_array)[0][0]

    if prediction > 0.5:
        st.error(f"Prediction: **Danger Detected** (Confidence: {prediction:.2f})")
    else:
        st.success(f"Prediction: **Normal** (Confidence: {1 - prediction:.2f})")

