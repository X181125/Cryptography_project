from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from chaotic import logistic_map

# Nếu muốn AES-256, thay KEY bằng 32 bytes, ví dụ: get_random_bytes(32)
KEY = b'sixteenbytekey12'  # 16 bytes → AES-128-GCM
SEED = 0.5
R = 3.9

with open("static/video/sample.mp4", "rb") as f:
    raw_data = f.read()

# Chaotic XOR
chaotic_stream = logistic_map(SEED, R, len(raw_data))
xor_encrypted = bytes([a ^ b for a, b in zip(raw_data, chaotic_stream)])

# AES-GCM
cipher = AES.new(KEY, AES.MODE_GCM)
ciphertext, tag = cipher.encrypt_and_digest(xor_encrypted)

with open("encrypted_video.bin", "wb") as f:
    f.write(cipher.nonce + tag + ciphertext)

print("[+] Video đã được mã hóa và lưu tại encrypted_video.bin")
