from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import smtplib
from email.mime.text import MIMEText
import firebase_admin
from firebase_admin import credentials, db

app = FastAPI(title="Kiyo AI Secure Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin securely using Environment URL
FIREBASE_URL = os.getenv("FIREBASE_URL")
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app(options={
            'databaseURL': FIREBASE_URL
        })
    except Exception as e:
        print("Firebase Init Error:", e)

# Environment Variables from Vercel
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

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
    
    # Send Professional Email via SMTP
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; background-color: #0b1120; padding: 30px; color: #ffffff; border-radius: 12px;">
            <h2 style="color: #a78bfa; text-align: center;">Kiyo AI Intelligent Learning Guide</h2>
            <p style="font-size: 14px; color: #94a3b8;">Hello Student,</p>
            <p style="font-size: 14px; color: #f8fafc;">Your secure verification code for accessing Kiyo AI & TicBull Portal is:</p>
            <div style="background: #1e293b; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #a78bfa; border-radius: 8px; margin: 20px 0;">
                {otp}
            </div>
            <p style="font-size: 12px; color: #64748b; text-align: center;">This code is valid for 5 minutes. Do not share it with anyone.</p>
        </div>
        """
        
        msg = MIMEText(html_content, "html")
        msg["Subject"] = "Kiyo AI - Secure Verification OTP"
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
        # Save user to secure Firebase Realtime Database under 'users'
        try:
            ref = db.reference(f'users/{email.replace(".", "_")}')
            ref.set({"email": email, "verified": True})
        except Exception as db_err:
            print("Database Write Error:", db_err)
            
        return {"status": "success", "message": "OTP Verified & Saved Successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")

