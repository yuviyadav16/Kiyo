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

# Storages for different OTP operations
otp_storage = {}
delete_otp_storage = {} 
pass_change_otp_storage = {} # Z+ Password Change ke liye
email_change_otp_storage = {} # Z+ Email Change ke liye

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
        msg["From"] = f"TicBull <{SMTP_EMAIL}>"
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
        formatted_email = email.replace(".", "_")
        ref = db.reference(f'users/{formatted_email}')
        ref.set({
            "email": email,
            "password": stored["password"],
            "fullName": stored["fullName"],
            "dob": stored["dob"],
            "verified": True
        })
        return {"status": "success", "message": "Verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/api/reset-password")
async def reset_password(request: Request):
    # Used for forgot password from Login page
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


# ---------------- DASHBOARD APIS ---------------- #

@app.post("/api/update-profile")
async def update_profile(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
        
    formatted_email = email.replace(".", "_")
    ref = db.reference(f'users/{formatted_email}')
    
    updates = {}
    if "fullName" in data: updates["fullName"] = data["fullName"]
    if "city" in data: updates["city"] = data["city"]
    if "state" in data: updates["state"] = data["state"]
    # User want full details update, you can append anything dynamically if sent from frontend
    
    ref.update(updates)
    return {"status": "success", "message": "Profile updated!"}

@app.post("/api/send-delete-otp")
async def send_delete_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
        
    otp = str(random.randint(100000, 999900))
    delete_otp_storage[email] = otp
    
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #ef4444; text-align: center; margin-top: 0; letter-spacing: 1px;">WARNING: Account Deletion</h2>
            <p style="color: #334155; font-size: 14px; margin-top: 30px;">Hello,</p>
            <p style="color: #334155; font-size: 14px;">We received a request to permanently delete your Kiyo AI account. Use this OTP to confirm. This action cannot be undone.</p>
            <div style="background-color: #fef2f2; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; color: #ef4444; border-radius: 8px; margin: 25px 0; border: 2px dashed #fca5a5; letter-spacing: 5px;">
                {otp}
            </div>
            <p style="color: #64748b; font-size: 12px; text-align: center;">If you didn't request this, ignore this email. Your account is safe.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
            <p style="color: #94a3b8; font-size: 11px; text-align: center; margin: 0; text-transform: uppercase; font-weight: bold;">Powered By TicBull Academy</p>
        </div>
        """
        msg = MIMEMultipart('alternative')
        msg["Subject"] = "Kiyo AI - Account Deletion Verification"
        msg["From"] = f"TicBull <{SMTP_EMAIL}>"
        msg["To"] = email
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            
        return {"status": "success", "message": "Delete OTP sent"}
    except Exception as e:
        print(f"SMTP EXCEPTION: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email.")

@app.post("/api/delete-account")
async def delete_account(request: Request):
    data = await request.json()
    email = data.get("email")
    user_otp = data.get("otp")
    
    stored_otp = delete_otp_storage.get(email)
    if stored_otp and stored_otp == user_otp:
        formatted_email = email.replace(".", "_")
        ref = db.reference(f'users/{formatted_email}')
        ref.delete()
        del delete_otp_storage[email]
        return {"status": "success", "message": "Account deleted permanently"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")


# ---------------- NEW Z+ SECURITY APIS ---------------- #

@app.post("/api/send-pass-change-otp")
async def send_pass_change_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
        
    otp = str(random.randint(100000, 999900))
    pass_change_otp_storage[email] = otp
    
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #6366f1; text-align: center; margin-top: 0; letter-spacing: 1px;">Z+ Security Alert</h2>
            <p style="color: #334155; font-size: 14px; margin-top: 30px;">Hello,</p>
            <p style="color: #334155; font-size: 14px;">We received a request to change your Kiyo AI password. Use this OTP to confirm.</p>
            <div style="background-color: #f8fafc; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; color: #10b981; border-radius: 8px; margin: 25px 0; border: 2px dashed #e2e8f0; letter-spacing: 5px;">
                {otp}
            </div>
            <p style="color: #64748b; font-size: 12px; text-align: center;">If you didn't request this, change your password immediately.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
            <p style="color: #94a3b8; font-size: 11px; text-align: center; margin: 0; text-transform: uppercase; font-weight: bold;">Powered By TicBull Academy</p>
        </div>
        """
        msg = MIMEMultipart('alternative')
        msg["Subject"] = "Kiyo AI - Password Change Request"
        msg["From"] = f"TicBull <{SMTP_EMAIL}>"
        msg["To"] = email
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            
        return {"status": "success", "message": "OTP sent for password change"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send email.")

@app.post("/api/verify-pass-change")
async def verify_pass_change(request: Request):
    data = await request.json()
    email = data.get("email")
    user_otp = data.get("otp")
    new_password = data.get("newPassword")
    
    stored_otp = pass_change_otp_storage.get(email)
    if stored_otp and stored_otp == user_otp:
        formatted_email = email.replace(".", "_")
        ref = db.reference(f'users/{formatted_email}')
        ref.update({"password": new_password}) # Update in Firebase
        del pass_change_otp_storage[email]
        return {"status": "success", "message": "Password changed successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/api/send-email-change-otp")
async def send_email_change_otp(request: Request):
    data = await request.json()
    old_email = data.get("oldEmail")
    new_email = data.get("newEmail")
    
    if not new_email:
        raise HTTPException(status_code=400, detail="New Email required")
        
    # Check if new email is already registered
    formatted_new_email = new_email.replace(".", "_")
    check_ref = db.reference(f'users/{formatted_new_email}')
    if check_ref.get():
        return {"status": "exists", "message": "This email is already registered to another account."}
        
    otp = str(random.randint(100000, 999900))
    email_change_otp_storage[old_email] = {"otp": otp, "new_email": new_email}
    
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #6366f1; text-align: center; margin-top: 0; letter-spacing: 1px;">Update Email Address</h2>
            <p style="color: #334155; font-size: 14px; margin-top: 30px;">Hello,</p>
            <p style="color: #334155; font-size: 14px;">Please verify your new email address for Kiyo AI using this OTP:</p>
            <div style="background-color: #f8fafc; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; color: #10b981; border-radius: 8px; margin: 25px 0; border: 2px dashed #e2e8f0; letter-spacing: 5px;">
                {otp}
            </div>
            <p style="color: #64748b; font-size: 12px; text-align: center;">If you didn't request this, please contact support.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
            <p style="color: #94a3b8; font-size: 11px; text-align: center; margin: 0; text-transform: uppercase; font-weight: bold;">Powered By TicBull Academy</p>
        </div>
        """
        msg = MIMEMultipart('alternative')
        msg["Subject"] = "Kiyo AI - Verify New Email"
        msg["From"] = f"TicBull <{SMTP_EMAIL}>"
        msg["To"] = new_email # OTP goes to NEW email
        
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, new_email, msg.as_string())
            
        return {"status": "success", "message": "OTP sent to NEW email"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send email.")

@app.post("/api/verify-email-change")
async def verify_email_change(request: Request):
    data = await request.json()
    old_email = data.get("oldEmail")
    user_otp = data.get("otp")
    
    stored = email_change_otp_storage.get(old_email)
    if stored and stored["otp"] == user_otp:
        new_email = stored["new_email"]
        
        formatted_old = old_email.replace(".", "_")
        formatted_new = new_email.replace(".", "_")
        
        old_ref = db.reference(f'users/{formatted_old}')
        user_data = old_ref.get()
        
        if user_data:
            user_data["email"] = new_email # Update email inside data
            
            # Transfer data to new node
            new_ref = db.reference(f'users/{formatted_new}')
            new_ref.set(user_data)
            
            # Delete old node
            old_ref.delete()
            
            del email_change_otp_storage[old_email]
            return {"status": "success", "message": "Email updated successfully!", "newEmail": new_email}
            
    raise HTTPException(status_code=400, detail="Invalid OTP")
