import os
import base64
from flask import Flask, request, jsonify, send_from_directory, render_template, abort
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Thư mục project
BASE_DIR    = os.path.abspath(os.path.dirname(__file__))
STATIC      = os.path.join(BASE_DIR, "static")
KEYS_DIR    = os.path.join(STATIC, "keys")
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
    """
    Client gửi public key PEM (PKCS#8) lên để server mã hóa AES-key sau này.
    """
    pem_data = request.get_data()
    pub_path = os.path.join(PUBKEY_DIR, f"{video_id}.pem")
    with open(pub_path, "wb") as f:
        f.write(pem_data)
    return "", 204

@app.route("/get_key_rsa/<video_id>")
def get_key_rsa(video_id):
    """
    Đọc AES key, mã hóa bằng public key của client (RSA-OAEP), trả về Base64.
    """
    token = request.args.get("token", "")
    if token != VALID_TOKEN:
        return jsonify(error="Token không hợp lệ"), 403

    # Load public key client
    pub_path = os.path.join(PUBKEY_DIR, f"{video_id}.pem")
    if not os.path.isfile(pub_path):
        return jsonify(error="Public key không tồn tại"), 404
    pub_pem = open(pub_path, "rb").read()
    client_pub = load_pem_public_key(pub_pem)

    # Load AES key
    key_path = os.path.join(KEYS_DIR, f"{video_id}.key")
    if not os.path.isfile(key_path):
        return jsonify(error="AES key không tồn tại"), 404
    raw_key = open(key_path, "rb").read()

    # Mã hóa key bằng RSA-OAEP SHA-256
    cipherkey = client_pub.encrypt(
        raw_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    b64 = base64.b64encode(cipherkey).decode('ascii')
    return jsonify(key_rsa_b64=b64)

@app.route("/segment/<path:filename>")
def serve_segment(filename):
    if not filename.endswith(('.enc','.bin')):
        abort(404)
    return send_from_directory(SEGMENT_DIR, filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 9000)), debug=True)
