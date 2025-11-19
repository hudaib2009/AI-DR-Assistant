# Project: AI DR Assistant

## Project Overview

This project is a multi-functional web application called "AI DR Assistant" developed by "Team JMI". It provides several AI-powered and informational features, including:

*   **Chest X-ray Analysis:** A core feature that allows users to upload chest X-ray images and receive an AI-based analysis indicating whether the image is "Normal" or shows "Danger Detected". This is powered by a TensorFlow model served via a FastAPI backend.
*   **AI Chatbot:** A powerful, multi-modal generative AI assistant using Google's Gemini model. It can process not only text but also images, PDFs, and DOCX files.
*   **Donation System:** A Stripe-based donation system.
*   **Feedback System:** A system for users to provide feedback.
*   **Informational Sections:** The application also includes a blog, project updates, and information about the development team.

The frontend is a single-page application built with HTML, CSS, and vanilla JavaScript. The backend is composed of several microservices built with FastAPI, each with its own set of dependencies.

## Building and Running

The project uses multiple Python virtual environments and shell scripts to manage its different components. The easiest way to run the entire application is to use the `run.sh` script:

```bash
./scripts/run.sh
```

This will start all the necessary backend services and open the main frontend page in your default browser.

### 1. Running the X-Ray Analysis Backend

This service uses the `lcdtx_env` virtual environment. You can run it manually using the `LCDTX.sh` script:

```bash
./scripts/LCDTX.sh
```

Alternatively, you can activate the virtual environment and run the server directly:

```bash
# Activate the virtual environment (using fish shell)
source ./lcdtx_env/bin/activate.fish

# Run the backend server
python3 backend/api_backend.py
```

The API will be available at `http://localhost:8000`.

### 2. Running the Chatbot Backend

This service uses the `main_env` virtual environment.

```bash
# Activate the virtual environment (using fish shell)
source ./main_env/bin/activate.fish

# Set the Google API key
export GOOGLE_API_KEY="YOUR_API_KEY"

# Run the chatbot backend
python3 backend/back_end_chatbot.py
```

The API will be available at `http://localhost:8002`.

### 3. Launching the Frontend

The main entry point for the frontend is `web_v1.2.html`. The `web.sh` script is provided to automate the process of setting up the environment and opening the main page.

```bash
./scripts/web.sh
```

This will open `web_v1.2.html` in the default browser.

## Development Conventions

*   **Backend:** The backend is built with FastAPI. The code is modular, with different functionalities separated into different files (`api_backend.py`, `back_end_chatbot.py`, `donation_api.py`, `feedback_api.py`). The X-ray analysis and chatbot components are now independent microservices.
*   **Frontend:** The frontend is a single-page application using vanilla JavaScript for dynamic features. It makes API calls to the various backend services.
*   **Dependencies:** Python dependencies are managed using `requirements.txt` files for each component. The chatbot requires additional dependencies for its new capabilities, which can be found in `requirements/chatbot_requirements.txt`. These include:
    *   `google-generativeai`
    *   `PyMuPDF`
    *   `python-docx`
*   **Testing:** A `test_api_backend.py` file exists, suggesting that `pytest` is used for testing the API backend.
*   **Virtual Environments:** The project uses at least two different virtual environments, `main_env` and `lcdtx_env`, to isolate dependencies for different components.
