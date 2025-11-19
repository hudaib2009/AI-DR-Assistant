# donation_api.py

import os
import smtplib
from email.mime.text import MIMEText
import stripe
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, EmailStr, PositiveInt
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# To configure the settings, create a .env file in the same directory
# with the following content:
#
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
# EMAIL_USER=your_gmail_username@gmail.com
# EMAIL_PASSWORD=your_gmail_app_password
# DOMAIN=http://localhost:8000  # Or your frontend domain

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")
RECIPIENT_EMAIL = "team@jmi.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

stripe.api_key = STRIPE_SECRET_KEY

# --- FastAPI App Initialization ---
app = FastAPI(
    title="JMI Donation API",
    description="Handles donations via Stripe.",
    version="1.0.0",
)

# --- CORS Middleware ---
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# --- Pydantic Data Models ---
class Donation(BaseModel):
    name: str
    email: EmailStr
    amount: PositiveInt  # Amount in cents

# --- Helper Function for Sending Email ---
def send_confirmation_email(to_email: str, subject: str, body: str):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("ERROR: Email credentials are not set.")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"ERROR: Failed to send email to {to_email}. {e}")

# --- API Endpoints ---
@app.post("/create-checkout-session")
async def create_checkout_session(donation: Donation):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Donation to JMI Team',
                        },
                        'unit_amount': donation.amount * 100, # convert dollars to cents
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"{DOMAIN}/donation-success.html",
            cancel_url=f"{DOMAIN}/donation-cancel.html",
            customer_email=donation.email,
            metadata={
                'donor_name': donation.name,
            }
        )
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook is not configured.")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=stripe_signature, secret=STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        donor_name = session.get('metadata', {}).get('donor_name', 'Anonymous')
        amount_total = session.get('amount_total', 0) / 100  # in dollars

        if customer_email:
            # Send confirmation email to the donor
            donor_subject = "Thank you for your donation to JMI Team!"
            donor_body = f"Dear {donor_name},\n\nThank you for your generous donation of ${amount_total:.2f}.\n\nSincerely,\nThe JMI Team"
            send_confirmation_email(customer_email, donor_subject, donor_body)

        # Send notification email to the team
        team_subject = f"New Donation Received from {donor_name}"
        team_body = f"A new donation of ${amount_total:.2f} was received from {donor_name} ({customer_email})."
        send_confirmation_email(RECIPIENT_EMAIL, team_subject, team_body)

    return {"status": "success"}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the JMI Donation API"}

# To run this backend:
# 1. Install dependencies: pip install -r donation_requirements.txt
# 2. Create a .env file with your Stripe and email credentials.
# 3. Run the server: uvicorn donation_api:app --reload
