from flask import Flask, jsonify, send_file, render_template
import os

app = Flask(__name__)

# Thư mục chứa segment đã mã hóa
SEGMENT_FOLDER = "static/encrypted_segments"
# Thư mục chứa video gốc (chỉ để tham khảo, client không dùng trực tiếp)
VIDEO_FOLDER = "static/video"

# Route 1: Trả về trang index.html (client sẽ load JS để xử lý)
@app.route("/")
def index():
    return render_template("index.html")

# Route 2: Trả về danh sách segments (file .bin) dưới dạng JSON
@app.route("/segments")
def list_segments():
    files = sorted(f for f in os.listdir(SEGMENT_FOLDER) if f.endswith(".bin"))
    return jsonify({"segments": files})

# Route 3: Trả về nội dung segment cụ thể
@app.route("/segment/<name>")
def get_segment(name):
    path = os.path.join(SEGMENT_FOLDER, name)
    if not os.path.exists(path):
        return "Not Found", 404
    # Trả về binary data (nonce | tag | ciphertext)
    return send_file(path, mimetype="application/octet-stream")

if __name__ == "__main__":
    app.run(port=8000, debug=True)
