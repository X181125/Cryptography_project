#!/usr/bin/env python3
import os
import sys
import ctypes
import secrets
import json
from ctypes import c_uint8, c_int, POINTER

# Tham số chaotic (bí mật, chỉ lưu server-side)
SEED = 0.5
R    = 3.9

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_video>")
        sys.exit(1)

    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

    # Kiểm tra input
    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"[!] File không tồn tại: {input_path}")
        sys.exit(1)

    base, _ = os.path.splitext(os.path.basename(input_path))
    keys_dir = os.path.join(project_root, "static", "keys")
    enc_dir  = os.path.join(project_root, "static", "encrypted_segments")
    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(enc_dir, exist_ok=True)

    # 1) Sinh AES-256 key và lưu
    key_bytes = secrets.token_bytes(32)
    key_path  = os.path.join(keys_dir, f"{base}.key")
    with open(key_path, "wb") as kf:
        kf.write(key_bytes)
    print(f"[+] AES-256 key saved to: {key_path}")

    # 2) Lưu metadata (seed + r) thành JSON
    meta = {"seed": SEED, "r": R}
    meta_path = os.path.join(keys_dir, f"{base}.meta")
    with open(meta_path, "w") as mf:
        json.dump(meta, mf)
    print(f"[+] Chaotic params saved to: {meta_path}")

    # 3) Load DLL Chaotic + AES-GCM
    dll_path = os.path.join(project_root, "ChaoticCryptology", "output", "Chaotic_Cryptology.dll")
    try:
        dll = ctypes.WinDLL(dll_path)
    except Exception as e:
        print(f"[!] Không thể load DLL: {dll_path}\n{e}")
        sys.exit(1)
    dll.chaotic_aes_encrypt.argtypes = [
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), POINTER(c_int)
    ]
    dll.chaotic_aes_encrypt.restype = c_int

    # 4) Đọc plaintext
    with open(input_path, "rb") as f:
        plaintext = f.read()
    plen = len(plaintext)
    print(f"[+] Read '{input_path}' ({plen} bytes)")

    plain_buf = (c_uint8 * plen).from_buffer_copy(plaintext)
    enc_buf   = (c_uint8 * (plen + 12 + 16))()
    enc_len   = c_int()

    # 5) Mã hóa: Chaotic XOR + AES-GCM
    ret = dll.chaotic_aes_encrypt(
        plain_buf, plen,
        (c_uint8 * len(key_bytes)).from_buffer_copy(key_bytes), len(key_bytes),
        enc_buf, ctypes.byref(enc_len)
    )
    if ret != 0:
        print(f"[!] Encryption failed (code={ret})")
        sys.exit(1)

    # 6) Ghi .enc
    output_path = os.path.join(enc_dir, f"{base}.enc")
    with open(output_path, "wb") as out:
        out.write(bytes(enc_buf[:enc_len.value]))
    print(f"[+] Encrypted to '{output_path}' ({enc_len.value} bytes)")

if __name__ == "__main__":
    main()
