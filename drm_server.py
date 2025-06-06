# drm_server.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
import os

app = Flask(__name__)
CORS(app)  # Cho phép mọi origin

# Token hợp lệ (giả lập)
VALID_TOKEN = "abc123"
# File chứa key AES-256 (32 bytes) mà encrypt_segments.py đã tạo
KEY_PATH = "static/keys/aes_256.key"

@app.route("/get_key", methods=["POST"])
def get_key():
    """
    Khi client POST {"token":"abc123"}:
    - Nếu token không khớp, trả về 403
    - Nếu hợp lệ, đọc 32 byte key, encode Base64 rồi trả về JSON
    Flask-CORS sẽ tự động xử lý OPTIONS và thêm Access-Control-Allow-Origin
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    token = data.get("token")
    if token != VALID_TOKEN:
        return jsonify({"error": "Invalid token"}), 403

    # Đọc key AES-256
    if not os.path.exists(KEY_PATH):
        return jsonify({"error": "Key file not found"}), 500

    with open(KEY_PATH, "rb") as f:
        raw_key = f.read()

    key_b64 = base64.b64encode(raw_key).decode()
    return jsonify({"key_b64": key_b64})

if __name__ == "__main__":
    app.run(port=9000, debug=True)
