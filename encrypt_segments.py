# encrypt_segments.py
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from chaotic import logistic_map

SEGMENT_FOLDER = "static/video"
OUTPUT_FOLDER = "static/encrypted_segments"
KEY_FILE = "static/keys/aes_256.key"

# Đảm bảo thư mục tồn tại
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs("static/keys", exist_ok=True)

# 1) Tạo khóa AES-256 (32 bytes) và lưu vào KEY_FILE
key = get_random_bytes(32)
with open(KEY_FILE, "wb") as f:
    f.write(key)
print("[+] AES-256 key generated and saved to:", KEY_FILE)

# 2) Đọc param Chaotic
SEED = 0.5
R = 3.9

# 3) Mã hóa từng file .mp4 trong static/video/
for filename in os.listdir(SEGMENT_FOLDER):
    if not filename.endswith(".mp4"):
        continue

    filepath = os.path.join(SEGMENT_FOLDER, filename)
    with open(filepath, "rb") as f:
        plaintext = f.read()

    # 3.1) Tạo keystream Chaotic (cùng seed và r) rồi XOR với dữ liệu gốc
    stream_length = len(plaintext)
    chaotic_stream = logistic_map(SEED, R, stream_length)
    xor_encrypted = bytes([plaintext[i] ^ chaotic_stream[i] for i in range(stream_length)])

    # 3.2) Đưa dữ liệu đã Chaotic-XOR vào AES-256-GCM
    nonce = get_random_bytes(12)                # Tạo nonce 12 byte
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(xor_encrypted)


    # 3.3) Ghi file .bin chứa [nonce (12B) || tag (16B) || ciphertext]
    outname = filename.replace(".mp4", ".bin")
    outpath = os.path.join(OUTPUT_FOLDER, outname)
    with open(outpath, "wb") as out:
        out.write(cipher.nonce + tag + ciphertext)

    print(f"[+] Encrypted {filename} → {outpath}")
