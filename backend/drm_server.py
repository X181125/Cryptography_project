from flask import Flask, jsonify, request
from flask_cors import CORS
import base64, os, logging

app = Flask(__name__)
CORS(app)

# Bạn có thể lấy token/key từ env var hoặc DB thay vì constant
VALID_TOKEN = os.getenv("DRM_TOKEN", "abc123")
KEY_PATH    = os.getenv("AES_KEY_PATH", "static/keys/aes_256.key")

logging.basicConfig(level=logging.INFO)

@app.route("/get_key", methods=["POST"])
def get_key():
    data = request.get_json(silent=True)
    token = data.get("token") if data else None
    if token != VALID_TOKEN:
        logging.warning("Invalid token: %s", token)
        return jsonify(error="Invalid token"), 403

    if not os.path.exists(KEY_PATH):
        logging.error("Key file missing: %s", KEY_PATH)
        return jsonify(error="Key file not found"), 500

    raw = open(KEY_PATH,"rb").read()
    b64 = base64.b64encode(raw).decode()
    return jsonify(key_b64=b64)

if __name__ == "__main__":
    app.run(port=9000, debug=True)
