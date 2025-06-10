# server.py

import os
import base64
from flask import Flask, request, jsonify, send_from_directory, render_template, abort
from flask_cors import CORS

# Xác định thư mục gốc của project (1 cấp lên so với file này)
BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES    = os.path.join(BASE_DIR, "templates")
STATIC       = os.path.join(BASE_DIR, "static")
KEY_FILE     = os.path.join(STATIC, "keys", "aes_256.key")
SEGMENT_DIR  = os.path.join(STATIC, "encrypted_segments")
VALID_TOKEN  = os.getenv("DRM_TOKEN", "abc123")

app = Flask(
    __name__,
    static_folder=STATIC,
    template_folder=TEMPLATES
)
CORS(app)  # Cho phép mọi origin gọi API

@app.route("/")
def index():
    """Trả về trang index.html từ templates/"""
    return render_template("index.html")

@app.route("/segment/<path:filename>")
def serve_segment(filename):
    """Phục vụ các file .enc hoặc .bin trong static/encrypted_segments/"""
    if not (filename.endswith(".enc") or filename.endswith(".bin")):
        abort(404)
    return send_from_directory(SEGMENT_DIR, filename)

@app.route("/get_key", methods=["POST"])
def get_key():
    """
    Client POST {"token":"..."} để lấy key AES-256 (Base64)
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if token != VALID_TOKEN:
        return jsonify(error="Token không hợp lệ"), 403

    if not os.path.isfile(KEY_FILE):
        return jsonify(error="Không tìm thấy file key"), 500

    raw_key = open(KEY_FILE, "rb").read()
    key_b64 = base64.b64encode(raw_key).decode("ascii")
    return jsonify(key_b64=key_b64)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 9000))
    # Chỉ lắng nghe trên localhost
    app.run(host="127.0.0.1", port=port, debug=True)
