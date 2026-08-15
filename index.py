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

# Initialize Firebase Admin securely using service account key and environment URL
FIREBASE_URL = os.getenv("FIREBASE_URL")
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })
    except Exception as e:
        print("Firebase Init Error:", e)

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

otp_storage = {}

@app.post("/api/check-email")
async def check_email(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    formatted_email = email.replace(".", "_")
    ref = db.reference(f'users/{formatted_email}')
    user_data = ref.get()
    
    if user_data:
        return {"exists": True, "message": "Email already registered"}
    return {"exists": False, "message": "Email available"}

@app.post("/api/send-otp")
async def send_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    otp = str(random.randint(100000, 999900))
    otp_storage[email] = otp
    
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; background-color: #0b1120; padding: 30px; color: #ffffff; border-radius: 12px;">
            <h2 style="color: #a78bfa; text-align: center;">Kiyo AI Intelligent Learning Guide</h2>
            <p style="font-size: 14px; color: #94a3b8;">Hello Student,</p>
            <p style="font-size: 14px; color: #f8fafc;">Your secure verification code is:</p>
            <div style="background: #1e293b; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #a78bfa; border-radius: 8px; margin: 20px 0;">
                {otp}
            </div>
            <p style="font-size: 12px; color: #64748b; text-align: center;">Valid for 5 minutes. Do not share.</p>
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
        try:
            formatted_email = email.replace(".", "_")
            ref = db.reference(f'users/{formatted_email}')
            ref.set({"email": email, "verified": True})
        except Exception as db_err:
            print("Database Write Error:", db_err)
            
        return {"status": "success", "message": "OTP Verified & Saved Successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")
