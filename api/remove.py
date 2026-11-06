# api/remove.py
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from _core import remove_friend

class handler(BaseHTTPRequestHandler):
    def _send(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        uid = (qs.get("uid") or qs.get("player_id") or [""])[0].strip()

        if not uid or not uid.isdigit():
            return self._send(400, {"success": False, "message": "Missing or invalid 'uid'"})

        result = remove_friend(uid)
        return self._send(200 if result["success"] else 400, result)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        uid = str(data.get("uid") or data.get("player_id") or "").strip()
        if not uid.isdigit():
            return self._send(400, {"success": False, "message": "Missing or invalid 'uid'"})

        result = remove_friend(uid)
        return self._send(200 if result["success"] else 400, result)