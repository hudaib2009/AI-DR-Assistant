# feedback_api.py

import os
import logging
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, constr
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# To configure the email settings, create a .env file in the same directory
# with the following content:
#
# EMAIL_USER=your_gmail_username@gmail.com
# EMAIL_PASSWORD=your_gmail_app_password
#
# For Gmail, you'll need to generate an "App Password".
# 1. Go to your Google Account settings.
# 2. Navigate to "Security".
# 3. Under "Signing in to Google", enable 2-Step Verification.
# 4. After enabling it, go to "App passwords", generate a new password for "Mail" on "Other (Custom name)",
#    and use the generated 16-character password in your .env file.

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "team@jmi.com")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="JMI Feedback API",
    description="Handles user feedback submission and sends it to the JMI team.",
    version="1.0.0",
)

# --- CORS Middleware ---
# Configure CORS to allow the frontend to communicate with this API.
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "null",  # Allow requests from local files (file://)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],  # Include OPTIONS for preflight requests
    allow_headers=["*"],
)

# --- Pydantic Data Model with Validation ---
class Feedback(BaseModel):
    name: constr(strip_whitespace=True, min_length=2, max_length=50)
    email: EmailStr
    message: constr(strip_whitespace=True, min_length=10, max_length=1000)

# --- Helper Function for Sending Email ---
def send_feedback_email(name: str, email: str, message: str) -> None:
    """
    Sends the feedback email using secure SMTP (runs in background).
    This function should be called via BackgroundTasks to avoid blocking the response.
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Email service misconfigured: EMAIL_USER or EMAIL_PASSWORD not set.")
        return

    try:
        # Create the email message
        email_subject = f"New Feedback from {name}"
        email_body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        
        msg = MIMEText(email_body)
        msg["Subject"] = email_subject
        msg["From"] = EMAIL_USER
        msg["To"] = RECIPIENT_EMAIL

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Feedback email sent from {name} ({email})")
            
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check EMAIL_USER and EMAIL_PASSWORD.")
    except Exception as e:
        logger.error(f"Failed to send feedback email: {type(e).__name__} - {str(e)}")

# --- API Endpoint ---
@app.post("/feedback")
async def submit_feedback(feedback: Feedback, background_tasks: BackgroundTasks):
    """
    Receives feedback from the user, validates it, and sends it as an email in the background.
    Returns immediately to the client while email is sent asynchronously.
    """
    try:
        # Add email sending task to background queue
        background_tasks.add_task(
            send_feedback_email,
            feedback.name,
            feedback.email,
            feedback.message
        )
        logger.info(f"Feedback received from {feedback.name} ({feedback.email}). Email will be sent in background.")
        return {
            "status": "success",
            "message": "Feedback received successfully. Thank you for your input!"
        }
    except Exception as e:
        logger.error(f"Unexpected error processing feedback: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your feedback. Please try again later."
        )

# --- Root Endpoint for Health Check ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the JMI Feedback API"}

# To run this backend:
# 1. Install the required packages: pip install fastapi uvicorn python-dotenv
# 2. Create a .env file with your email credentials (see instructions above).
# 3. Run the server: uvicorn feedback_api:app --reload
