import os
import base64
from flask import Flask, request, jsonify, send_from_directory, render_template, abort
from flask_cors import CORS

# Thư mục project
BASE_DIR     = os.path.abspath(os.path.dirname(__file__))
TEMPLATES    = os.path.join(BASE_DIR, "templates")
STATIC       = os.path.join(BASE_DIR, "static")
KEYS_DIR     = os.path.join(STATIC, "keys")
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
    """Phục vụ file .enc hoặc .bin trong static/encrypted_segments/"""
    if not (filename.endswith(".enc") or filename.endswith(".bin")):
        abort(404)
    # filename có thể là "sample1.enc" hoặc bất kỳ tên gì
    return send_from_directory(SEGMENT_DIR, filename)

@app.route("/get_key/<video_id>")
def get_key(video_id):
    """
    GET /get_key/<video_id>?token=abc123
    Trả về key AES-256 tương ứng video_id (đã lưu thành static/keys/<video_id>.key)
    """
    token = request.args.get("token", "")
    if token != VALID_TOKEN:
        return jsonify(error="Token không hợp lệ"), 403

    key_path = os.path.join(KEYS_DIR, f"{video_id}.key")
    if not os.path.isfile(key_path):
        return jsonify(error=f"Không tìm thấy key cho video '{video_id}'"), 404

    raw_key = open(key_path, "rb").read()
    key_b64 = base64.b64encode(raw_key).decode("ascii")
    return jsonify(key_b64=key_b64)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 9000))
    # Chỉ lắng nghe trên localhost
    app.run(host="127.0.0.1", port=port, debug=True)
