from Crypto.Cipher import AES
from chaotic import logistic_map

KEY = b'sixteenbytekey12'  # Mặc định AES-128 (nếu bạn muốn AES-256, sửa KEY thành 32 bytes)
SEED = 0.5
R = 3.9

def decrypt_video(encrypted_data: bytes) -> bytes:
    """
    Giải mã dữ liệu đã được mã hóa Chaotic+AES-GCM.
    Args:
        encrypted_data (bytes): nonce(16) + tag(16) + ciphertext
    Returns:
        bytes: Dữ liệu gốc.
    """
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)
    decrypted = cipher.decrypt_and_verify(ciphertext, tag)

    chaotic_stream = logistic_map(SEED, R, len(decrypted))
    original = bytes([a ^ b for a, b in zip(decrypted, chaotic_stream)])
    return original
