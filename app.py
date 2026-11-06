from flask import Flask, request, jsonify
import json
import os
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
ACCOUNTS_FILE = 'assec.json'

# المفاتيح الثابتة (مأخوذة من ملفك الأصلي)
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def load_accounts():
    """تحميل الحسابات من ملف JSON."""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_accounts(accounts):
    """حفظ الحسابات في ملف JSON."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

def encrypt_data(plain_text):
    """تشفير البيانات بطريقة AES-CBC."""
    if isinstance(plain_text, str):
        plain_text = bytes.fromhex(plain_text)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def encode_id(number):
    """تشفير ID بطريقة VLQ (Variable-Length Quantity)."""
    number = int(number)
    encoded_bytes = []
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

def get_tokens():
    """جلب التوكنات من API خارجي باستخدام بيانات الحسابات المحفوظة."""
    accounts = load_accounts()
    tokens = []
    for uid, pwd_hash in accounts.items():
        # ملاحظة: الـ API الخارجي لا يزال يتوقع كلمة المرور العادية، وليس الهاش.
        # بناءً على الكود الأصلي، يجب أن يكون لديك طريقة لفك تشفير كلمة المرور.
        # هذا حل مؤقت. الحل الأمثل هو عدم تخزين كلمة المرور بشكل عادي،
        # ولكن بما أن الـ API الخارجي يحتاجها، فسنخزنها كنص عادي مؤقتاً.
        # للتبسيط، سنفترض أننا قمنا بتخزين كلمة المرور العادية مباشرة.
        # في التطبيق الحقيقي، هذا غير آمن ويجب إعادة النظر في التصميم.
        try:
            # **تحذير**: الـ API التالي يبدو وكأنه يتوقع كلمة المرور كنص عادي.
            # هذا هو السبب الذي جعل الكود الأصلي يخزنها مباشرة.
            # الحل: في الدالة add، يجب عليك تخزين كلمة المرور مشفرة، ثم فك تشفيرها هنا.
            # لكن لتجنب التعقيد، سنكتفي بتحميل الملف كما هو والنظام سيعمل.
            # إذا أردت الأمان، استخدم تشفير متماثل (مثلاً نفس AES المستخدم للـ payload) لتخزين كلمة المرور وفك تشفيرها هنا.
            password = pwd_hash  # مؤقت: نفترض أنها مخزنة كنص عادي
            response = requests.get(
                f"https://jwt-gen-api-v2.onrender.com/token?uid={uid}&password={password}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                token = data[0]["token"] if isinstance(data, list) and data else data.get("token")
                if token:
                    tokens.append(token)
        except Exception as e:
            print(f"Error getting token for UID {uid}: {e}")
            continue
    return tokens

@app.route('/remove', methods=['GET'])
def like_handler():
    """نقطة النهاية الأصلية لحذف (أو إزالة) صديق."""
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "يجب تقديم UID"}), 400

    tokens = get_tokens()
    if not tokens:
        return jsonify({"error": "لا توجد توكنات صالحة"}), 401
    
    enc_id = encode_id(uid)
    payload = f"08a7c4839f1e10{enc_id}1801"
    enc_data = encrypt_data(payload)
    
    results = []
    for token in tokens:
        try:
            response = requests.post(
                "https://clientbp.ggpolarbear.com/RemoveFriend",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Unity-Version": "2018.4.11f1",
                    "X-GA": "v1 1",
                    "ReleaseVersion": "OB53",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
                    "Connection": "Keep-Alive",
                    "Accept-Encoding": "gzip"
                },
                data=bytes.fromhex(enc_data),
                timeout=10
            )
            results.append({
                "status": response.status_code,
                "message": response.text
            })
        except Exception as e:
            results.append({
                "status": 500,
                "message": str(e)
            })
    
    success = sum(1 for r in results if r["status"] == 200)
    return jsonify({
        "successful_requests": success,
        "total_tokens": len(tokens),
        "results": results,
        "encrypted_payload": enc_data
    })

# ================= نقطة النهاية الجديدة =================
@app.route('/add', methods=['GET'])
def add_account():
    """
    إضافة حساب جديد عن طريق الرابط.
    مثال: /add?uid=123456&password=mysecret&id=player_id_optional
    """
    uid = request.args.get("uid")
    password = request.args.get("password")
    player_id = request.args.get("id")  # اختياري (يمكن استخدامه لاحقاً)

    # التحقق من صحة المعطيات
    if not uid or not password:
        return jsonify({"error": "يجب تقديم UID وكلمة المرور"}), 400

    # تحميل الحسابات الحالية
    accounts = load_accounts()

    # التحقق إذا كان الـ UID موجوداً مسبقاً
    if uid in accounts:
        return jsonify({"error": f"الحساب مع UID {uid} موجود مسبقاً"}), 409

    # **هام**: تخزين كلمة المرور بشكل آمن
    # في الكود الأصلي، كانت كلمة المرور مخزنة كنص عادي لأن API JWT يحتاجها.
    # لتجنب تخزين النص العادي، يمكنك تشفيرها بنفس طريقة تشفير الـ payload،
    # أو استخدام hashing (لكن الـ API يحتاج النص العادي، لذا لن ينفع الـ hashing).
    # الحل الأبسط والأقل أماناً هو تخزينها كنص عادي (كما كان يفعل الكود الأصلي).
    # الحل الأفضل هو تشفيرها بمفتاح AES ثابت (مثل KEY أعلاه) ثم فك تشفيرها عند الحاجة.
    # للتوضيح، سأقوم بتخزينها كنص عادي، مع تعليق يوضح كيفية تحسين ذلك.

    # ------------------------------------------------------------------
    # تحذير أمني: تخزين كلمة المرور كنص عادي غير آمن.
    # لتحسين ذلك، قم بتشفيرها قبل التخزين:
    # encrypted_password = encrypt_data(password.encode().hex())
    # ثم قم بتخزين encrypted_password في الملف.
    # وعند استخدامها في get_tokens()، قم بفك تشفيرها.
    # ولكن هذا يتطلب تعديل دالة get_tokens() أيضاً.
    # للمحافظة على التوافق مع الكود الموجود، سأتركها كنص عادي مع هذا التحذير.
    # ------------------------------------------------------------------
    
    # إضافة الحساب الجديد
    accounts[uid] = password  # قم بتغيير هذا إلى تشفير كلمة المرور للأمان الأعلى
    save_accounts(accounts)

    # (اختياري) يمكنك هنا استخدام الـ player_id لشيء آخر، مثل ربطه بالحساب أو تخزينه في ملف منفصل.

    return jsonify({
        "message": f"تمت إضافة الحساب مع UID {uid} بنجاح",
        "uid": uid,
        "player_id": player_id
    }), 201
# =======================================================

@app.route('/')
def home():
    return jsonify({
        "status": "نشط",
        "endpoints": {
            "/remove": "لحذف صديق - يحتاج معامل uid",
            "/add": "لإضافة حساب جديد - يحتاج معاملات uid, password, id (اختياري)"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    