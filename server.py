import os
import base64
import json
from flask import Flask, request, jsonify, abort, render_template, send_from_directory
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Thư mục project
BASE_DIR    = os.path.abspath(os.path.dirname(__file__))
STATIC      = os.path.join(BASE_DIR, "static")
KEYS_DIR    = os.path.join(STATIC, "keys")
META_DIR    = KEYS_DIR    # meta file cùng thư mục với key
PUBKEY_DIR  = os.path.join(STATIC, "pubkeys")
SEGMENT_DIR = os.path.join(STATIC, "encrypted_segments")
VALID_TOKEN = os.getenv("DRM_TOKEN", "abc123")

os.makedirs(PUBKEY_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC, template_folder=os.path.join(BASE_DIR, "templates"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register_pubkey/<video_id>", methods=["POST"])
def register_pubkey(video_id):
    # Kiểm tra token: có thể gửi qua query hoặc header Authorization
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != VALID_TOKEN:
        return jsonify(error="Token không hợp lệ"), 403

    pem_data = request.get_data()
    pub_path = os.path.join(PUBKEY_DIR, f"{video_id}.pem")
    with open(pub_path, "wb") as f:
        f.write(pem_data)
    return "", 204


@app.route("/get_key_rsa/<video_id>")
def get_key_rsa(video_id):
    token = request.args.get("token", "")
    if token != VALID_TOKEN:
        return jsonify(error="Token không hợp lệ"), 403

    # Load public key của client
    pub_path = os.path.join(PUBKEY_DIR, f"{video_id}.pem")
    if not os.path.isfile(pub_path):
        return jsonify(error="Public key không tồn tại"), 404
    with open(pub_path, "rb") as f:
        pub_pem = f.read()
    client_pub = load_pem_public_key(pub_pem)

    # Load AES key
    key_path = os.path.join(KEYS_DIR, f"{video_id}.key")
    if not os.path.isfile(key_path):
        return jsonify(error="AES key không tồn tại"), 404
    with open(key_path, "rb") as f:
        raw_key = f.read()

    # Load metadata (seed & r)
    meta_path = os.path.join(META_DIR, f"{video_id}.meta")
    if not os.path.isfile(meta_path):
        return jsonify(error="Meta file không tồn tại"), 404
    with open(meta_path, "r") as f:
        meta = json.load(f)
    seed = meta.get("seed")
    r     = meta.get("r")

    # Tạo payload JSON
    payload = {
        "aes_key": base64.b64encode(raw_key).decode("ascii"),
        "seed":    seed,
        "r":       r
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    # RSA-OAEP encrypt payload
    cipher = client_pub.encrypt(
        payload_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    b64_cipher = base64.b64encode(cipher).decode("ascii")
    return jsonify(data_b64=b64_cipher)

@app.route("/segment/<path:filename>")
def serve_segment(filename):
    if not filename.endswith((".enc", ".bin")):
        abort(404)
    return send_from_directory(SEGMENT_DIR, filename)

if __name__ == "__main__":
    app.run(
        host="127.0.0.1", port=9000, debug=True
    )
