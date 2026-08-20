from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
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
        # CLEAN & SPAM-FREE HTML TEMPLATE (No External Links or Images)
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #4338ca; text-align: center; margin-top: 0; letter-spacing: 1px;">Kiyo AI</h2>
            <p style="color: #0f172a; font-size: 15px; font-weight: bold; text-align: center;">Intelligent Learning Guide</p>
            
            <p style="color: #334155; font-size: 14px; margin-top: 30px;">Hello,</p>
            <p style="color: #334155; font-size: 14px;">Your secure verification code to join Kiyo AI is:</p>
            
            <div style="background-color: #f8fafc; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; color: #10b981; border-radius: 8px; margin: 25px 0; border: 2px dashed #e2e8f0; letter-spacing: 5px;">
                {otp}
            </div>
            
            <p style="color: #64748b; font-size: 12px; text-align: center;">This OTP is valid for 10 minutes. Please do not share it with anyone.</p>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
            <p style="color: #94a3b8; font-size: 11px; text-align: center; margin: 0; text-transform: uppercase; font-weight: bold;">Powered By TicBull Academy</p>
        </div>
        """
        
        msg = MIMEMultipart('alternative')
        msg["Subject"] = "Kiyo AI - Secure Verification OTP"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            
        return {"status": "success", "message": "OTP sent successfully"}
    except Exception as e:
        print(f"SMTP EXCEPTION: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email.")

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

