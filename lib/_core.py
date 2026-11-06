# api/_core.py
import os
import time
import json
import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====== قراءة الإعدادات من config.json ======
def _load_config():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(base, "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG ERROR] {e}")
        return {}

_cfg = _load_config()

BOT_UID      = str(_cfg.get("uid", ""))
BOT_PASSWORD = str(_cfg.get("password", ""))

CLIENT_URL    = "https://clientbp.ppmainecoonghj.com"
OB_VERSION    = "OB55"

KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ====== كاش التوكن ======
_token_cache = {"token": None, "ts": 0}
TOKEN_TTL = 3600 * 6  # 6 ساعات

# ====== التشفير ======
def xEncrypt(plain_text_hex, key=KEY, iv=IV):
    pt = bytes.fromhex(plain_text_hex)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(pt, AES.block_size)).hex()

def encrypt_api(plain_text_hex):
    return xEncrypt(plain_text_hex, KEY, IV)

def Encrypt_ID(number):
    x = int(number)
    dec = ['80','81','82','83','84','85','86','87','88','89','8a','8b','8c','8d','8e','8f',
           '90','91','92','93','94','95','96','97','98','99','9a','9b','9c','9d','9e','9f',
           'a0','a1','a2','a3','a4','a5','a6','a7','a8','a9','aa','ab','ac','ad','ae','af',
           'b0','b1','b2','b3','b4','b5','b6','b7','b8','b9','ba','bb','bc','bd','be','bf',
           'c0','c1','c2','c3','c4','c5','c6','c7','c8','c9','ca','cb','cc','cd','ce','cf',
           'd0','d1','d2','d3','d4','d5','d6','d7','d8','d9','da','db','dc','dd','de','df',
           'e0','e1','e2','e3','e4','e5','e6','e7','e8','e9','ea','eb','ec','ed','ee','ef',
           'f0','f1','f2','f3','f4','f5','f6','f7','f8','f9','fa','fb','fc','fd','fe','ff']
    xxx = ['1','01','02','03','04','05','06','07','08','09','0a','0b','0c','0d','0e','0f',
           '10','11','12','13','14','15','16','17','18','19','1a','1b','1c','1d','1e','1f',
           '20','21','22','23','24','25','26','27','28','29','2a','2b','2c','2d','2e','2f',
           '30','31','32','33','34','35','36','37','38','39','3a','3b','3c','3d','3e','3f',
           '40','41','42','43','44','45','46','47','48','49','4a','4b','4c','4d','4e','4f',
           '50','51','52','53','54','55','56','57','58','59','5a','5b','5c','5d','5e','5f',
           '60','61','62','63','64','65','66','67','68','69','6a','6b','6c','6d','6e','6f',
           '70','71','72','73','74','75','76','77','78','79','7a','7b','7c','7d','7e','7f']
    x = x / 128
    if x > 128:
        x = x / 128
        if x > 128:
            x = x / 128
            if x > 128:
                x = x / 128
                strx = int(x); y = (x - int(strx)) * 128; stry = str(int(y))
                z = (y - int(stry)) * 128; strz = str(int(z))
                n = (z - int(strz)) * 128; strn = str(int(n))
                m = (n - int(strn)) * 128
                return dec[int(m)] + dec[int(n)] + dec[int(z)] + dec[int(y)] + xxx[int(x)]
            else:
                strx = int(x); y = (x - int(strx)) * 128; stry = str(int(y))
                z = (y - int(stry)) * 128; strz = str(int(z))
                n = (z - int(strz)) * 128; strn = str(int(n))
                return dec[int(n)] + dec[int(z)] + dec[int(y)] + xxx[int(x)]
        else:
            strx = int(x); y = (x - int(strx)) * 128; stry = str(int(y))
            z = (y - int(stry)) * 128; strz = str(int(z))
            return dec[int(z)] + dec[int(y)] + xxx[int(x)]
    else:
        strx = int(x); y = (x - int(strx)) * 128; stry = str(int(y))
        return dec[int(y)] + xxx[int(x)]

# ====== جلب التوكن ======
def fetch_token():
    if not BOT_UID or not BOT_PASSWORD:
        print("[TOKEN] UID أو PASSWORD غير موجودين في config.json")
        return None
    url = f"https://api-jwt-fast-by-xalinas.vercel.app/get?uid={BOT_UID}&password={BOT_PASSWORD}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success" and "token" in data:
                return data["token"]
    except Exception as e:
        print(f"[TOKEN ERROR] {e}")
    return None

def get_token(force=False):
    now = time.time()
    if not force and _token_cache["token"] and (now - _token_cache["ts"] < TOKEN_TTL):
        return _token_cache["token"]
    tok = fetch_token()
    if tok:
        _token_cache["token"] = tok
        _token_cache["ts"] = now
    return tok

# ====== الهيدرز ======
def _headers(token):
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-GA": "v1 1",
        "ReleaseVersion": OB_VERSION,
        "Host": "clientbp.ppmainecoonghj.com",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Connection": "close",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.12f1",
        "Accept": "*/*",
        "X-GA-SV": str(int(time.time()))
    }

# ====== إضافة صديق ======
def add_friend(player_id):
    token = get_token()
    if not token:
        return {"success": False, "code": 500, "message": "Token unavailable (check config.json)"}

    enc_id = Encrypt_ID(player_id)
    payload_hex = "08c8b5cfea1810" + enc_id + "18012008"
    encrypted = encrypt_api(payload_hex)
    url = f"{CLIENT_URL}/RequestAddingFriend"

    try:
        r = requests.post(url, headers=_headers(token), data=bytes.fromhex(encrypted),
                          timeout=15, verify=False)
        body = r.text or ""

        if r.status_code == 401:
            token = get_token(force=True)
            if token:
                r = requests.post(url, headers=_headers(token), data=bytes.fromhex(encrypted),
                                  timeout=15, verify=False)
                body = r.text or ""

        if r.status_code == 200:
            if "BR_FRIEND_NOT_SAME_REGION" in body:
                return {"success": False, "code": 400,
                        "message": "Player is from a different region."}
            return {"success": True, "code": 200, "message": "Friend request sent successfully."}

        if r.status_code == 400:
            if "BR_FRIEND_NOT_SAME_REGION" in body:
                return {"success": False, "code": 400,
                        "message": "Player is from a different region."}
            return {"success": False, "code": 400,
                    "message": f"Bad Request: {body[:120] or 'check player ID/region'}"}

        if r.status_code == 404:
            return {"success": False, "code": 404, "message": "Player not found."}

        return {"success": False, "code": r.status_code,
                "message": f"Failed. Code: {r.status_code}"}
    except Exception as e:
        return {"success": False, "code": 500, "message": f"Error: {str(e)[:100]}"}

# ====== حذف صديق ======
def remove_friend(player_id):
    token = get_token()
    if not token:
        return {"success": False, "code": 500, "message": "Token unavailable (check config.json)"}

    enc_id = Encrypt_ID(player_id)
    payload_hex = "08c8b5cfea1810" + enc_id + "18022008"
    encrypted = encrypt_api(payload_hex)
    url = f"{CLIENT_URL}/RemoveFriend"

    try:
        r = requests.post(url, headers=_headers(token), data=bytes.fromhex(encrypted),
                          timeout=15, verify=False)
        body = r.text or ""

        if r.status_code == 401:
            token = get_token(force=True)
            if token:
                r = requests.post(url, headers=_headers(token), data=bytes.fromhex(encrypted),
                                  timeout=15, verify=False)
                body = r.text or ""

        if r.status_code == 200:
            return {"success": True, "code": 200, "message": "Removed successfully."}

        if r.status_code == 400:
            return {"success": False, "code": 400,
                    "message": f"Failed to remove: {body[:120] or 'Bad Request'}"}

        if r.status_code == 404:
            return {"success": False, "code": 404,
                    "message": "Player not found in friends list."}

        return {"success": False, "code": r.status_code,
                "message": f"Failed. Code: {r.status_code}"}
    except Exception as e:
        return {"success": False, "code": 500, "message": f"Error: {str(e)[:100]}"}