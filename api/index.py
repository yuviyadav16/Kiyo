from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS allow karta hai ki tumhara Flutter WebView is API ko bina block hue call kar sake
CORS(app)

# TERE VIP USERS KI LIST (Sab lower case mein rakhna safe rehta hai)
VIP_USERS = {
    "sonaliyadav468": True,
    "singing5181": True,
    "radhe_riya098": True
}

# Base route check karne ke liye ki API chal rahi hai ya nahi
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "active", 
        "message": "Private Instagram Backend is Running!",
        "version": "1.0"
    })

# Main API jisko tumhari JavaScript baar-baar call karegi
@app.route('/api/check_rule', methods=['GET', 'POST'])
def check_rule():
    # Username GET (URL) ya POST (JSON body) dono se nikalne ka robust tarika
    if request.method == 'POST':
        data = request.get_json()
        raw_username = data.get('username', '')
    else:
        raw_username = request.args.get('username', '')

    # Username clean karna (space hatana aur chote letters me karna taaki error na aaye)
    username = raw_username.strip().lower()

    if not username:
        return jsonify({"error": "Bhai, username bhejna zaroori hai!"}), 400

    # AGAR USER VIP LIST MEIN HAI
    if username in VIP_USERS:
        return jsonify({
            "username": username,
            "is_vip": True,
            "rules": {
                "allow_comment": True,
                "allow_dm": True,
                "allow_follow": True,
                "allow_like": True,
                "show_close_friends_story": True
            },
            "command": "NATIVE_ACTION" # WebView ko signal: Asli IG wala kaam hone do
        }), 200

    # AGAR USER VIP LIST MEIN NAHI HAI
    else:
        return jsonify({
            "username": username,
            "is_vip": False,
            "rules": {
                "allow_comment": False,
                "allow_dm": False,
                "allow_follow": False,
                "allow_like": False,
                "show_close_friends_story": False
            },
            "command": "FAKE_UI" # WebView ko signal: Click block karo aur Fake box dikhao
        }), 200

# Ye line local testing ke liye hai, Vercel isko ignore kar dega
if __name__ == '__main__':
    app.run(debug=True, port=5000)
