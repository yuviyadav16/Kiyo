from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import smtplib
from email.mime.text import MIMEText
import requests

app = FastAPI(title="Kiyo AI Secure Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables from Vercel
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FIREBASE_URL = os.getenv("FIREBASE_URL")

# Temporary memory store for generated OTPs
otp_storage = {}

@app.post("/api/send-otp")
async def send_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999900))
    otp_storage[email] = otp
    
    # Send Email via SMTP
    try:
        msg = MIMEText(f"Your Kiyo AI Verification OTP is: {otp}. Valid for 5 minutes.")
        msg["Subject"] = "Kiyo AI - Email Verification OTP"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            
        return {"status": "success", "message": f"OTP sent to {email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/api/verify-otp")
async def verify_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    user_otp = data.get("otp")
    
    if otp_storage.get(email) == user_otp:
        return {"status": "success", "message": "OTP Verified Successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")
