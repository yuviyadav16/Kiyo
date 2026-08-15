from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import os, random, smtplib
from email.mime.text import MIMEText
import firebase_admin
from firebase_admin import credentials, db

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize Firebase (Ensure you have your service account JSON file in root)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': os.getenv("FIREBASE_URL")})

otp_storage = {}

@app.post("/api/check-email")
async def check_email(request: Request):
    data = await request.json()
    email = data.get("email").replace(".", "_")
    if db.reference(f'users/{email}').get(): return {"exists": True}
    return {"exists": False}

@app.post("/api/send-otp")
async def send_otp(request: Request):
    data = await request.json()
    email = data.get("email")
    otp = str(random.randint(100000, 999900))
    otp_storage[email] = otp
    
    msg = MIMEText(f"Your Kiyo AI verification code is {otp}", "html")
    msg["Subject"] = "Kiyo AI Secure Login"
    msg["From"] = os.getenv("SMTP_EMAIL")
    msg["To"] = email
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_PASSWORD"))
        server.sendmail(os.getenv("SMTP_EMAIL"), email, msg.as_string())
    return {"status": "success"}

@app.post("/api/verify-otp")
async def verify_otp(request: Request):
    data = await request.json()
    if otp_storage.get(data.get("email")) == data.get("otp"):
        db.reference(f'users/{data.get("email").replace(".", "_")}').set({"verified": True})
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Invalid OTP")
