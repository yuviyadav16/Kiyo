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

# Initialize Firebase with Service Account Key
FIREBASE_URL = os.getenv("FIREBASE_URL")
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
    except Exception as e:
        print("Firebase Init Error:", e)

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

otp_storage = {}

@app.post("/api/check-user")
async def check_user(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    mode = data.get("mode")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
        
    formatted_email = email.replace(".", "_")
    ref = db.reference(f'users/{formatted_email}')
    user_data = ref.get()
    
    if mode == "signup":
        if user_data:
            return {"status": "exists", "message": "Account already exists! Please Sign In."}
        return {"status": "available", "message": "Email available"}
        
    elif mode == "signin":
        if not user_data:
            return {"status": "not_found", "message": "Account not found! Please Sign Up first."}
        if user_data.get("password") != password:
            return {"status": "wrong_password", "message": "Incorrect password! Please try again."}
        return {"status": "success", "message": "Login successful"}

@app.post("/api/send-otp")
async def send_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    fullName = data.get("fullName", "")
    dob = data.get("dob", "")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    otp = str(random.randint(100000, 999900))
    otp_storage[email] = {"otp": otp, "password": password, "fullName": fullName, "dob": dob}
    
    try:
        # Professional Email Template with Social Icons & TicBull Branding
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                
                <!-- Premium Dark Header -->
                <div style="background-color: #0B101E; padding: 30px 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; letter-spacing: 1px;">Kiyo AI</h1>
                    <p style="color: #6366f1; font-size: 11px; margin: 5px 0 0 0; text-transform: uppercase; letter-spacing: 2px;">Intelligent Learning Guide</p>
                </div>
                
                <!-- Content Body -->
                <div style="padding: 30px; text-align: center; color: #334155;">
                    <h2 style="margin-top:0; font-size: 20px; color: #0f172a;">Verify Your Email</h2>
                    <p style="font-size: 14px; line-height: 1.5; color: #475569;">Hi there, you are almost ready to start learning! Use the secure OTP below to verify your account.</p>
                    
                    <div style="background-color: #f8fafc; border: 2px dashed #6366f1; padding: 15px; font-size: 36px; font-weight: 800; letter-spacing: 10px; color: #6366f1; border-radius: 12px; margin: 25px 0;">
                        {otp}
                    </div>
                    
                    <p style="font-size: 12px; color: #94a3b8; margin: 0;">This OTP is valid for 10 minutes. Do not share it with anyone.</p>
                </div>
                
                <!-- Footer with TicBull & Socials -->
                <div style="background-color: #f8fafc; padding: 25px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <div style="font-size: 10px; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px;">Powered By TicBull</div>
                    
                    <div style="margin-bottom: 15px;">
                        <a href="https://youtube.com/@mryuviyadav" style="display: inline-block; margin: 0 6px; text-decoration: none; font-weight: 700; color: #64748b; font-size: 12px;">YouTube</a> | 
                        <a href="https://www.instagram.com/mryuvi_yadav" style="display: inline-block; margin: 0 6px; text-decoration: none; font-weight: 700; color: #64748b; font-size: 12px;">Instagram</a> | 
                        <a href="https://facebook.com/mryuviyadav" style="display: inline-block; margin: 0 6px; text-decoration: none; font-weight: 700; color: #64748b; font-size: 12px;">Facebook</a> | 
                        <a href="https://x.com/mryuviyadav" style="display: inline-block; margin: 0 6px; text-decoration: none; font-weight: 700; color: #64748b; font-size: 12px;">X</a> | 
                        <a href="https://t.me/mryuviyadav" style="display: inline-block; margin: 0 6px; text-decoration: none; font-weight: 700; color: #64748b; font-size: 12px;">Telegram</a>
                    </div>
                    
                    <p style="font-size: 10px; color: #cbd5e1; margin: 0;">&copy; 2026 TicBull & Mr. Yuvi Yadav. All rights reserved.</p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        msg = MIMEText(html_content, "html")
        msg["Subject"] = "Kiyo AI - Secure Verification OTP"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            
        return {"status": "success", "message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/api/verify-otp")
async def verify_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    user_otp = data.get("otp")
    
    stored = otp_storage.get(email)
    if stored and stored["otp"] == user_otp:
        try:
            formatted_email = email.replace(".", "_")
            ref = db.reference(f'users/{formatted_email}')
            ref.set({
                "email": email,
                "password": stored["password"],
                "fullName": stored["fullName"],
                "dob": stored["dob"],
                "verified": True
            })
        except Exception as db_err:
            print("DB Error:", db_err)
            
        return {"status": "success", "message": "Verified successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/api/reset-password")
async def reset_password(request: Request):
    data = await request.json()
    email = data.get("email")
    new_password = data.get("newPassword")
    
    formatted_email = email.replace(".", "_")
    ref = db.reference(f'users/{formatted_email}')
    user_data = ref.get()
    
    if not user_data:
        raise HTTPException(status_code=404, detail="Email not registered!")
        
    ref.update({"password": new_password})
    return {"status": "success", "message": "Password updated successfully"}

