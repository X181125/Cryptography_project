#!/usr/bin/env python3
import os
import sys
import ctypes
import secrets
from ctypes import c_uint8, c_int, POINTER

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_video>")
        sys.exit(1)

    # 1. Tìm project_root (cấp trên của scripts/)
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

    # 2. Input video
    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"[!] File không tồn tại: {input_path}")
        sys.exit(1)

    base, _ = os.path.splitext(os.path.basename(input_path))

    # 3. Tạo thư mục static/keys & static/encrypted_segments dưới project_root
    keys_dir = os.path.join(project_root, "static", "keys")
    enc_dir  = os.path.join(project_root, "static", "encrypted_segments")
    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(enc_dir, exist_ok=True)

    # 4. Sinh key AES-256 và lưu thành project_root/static/keys/<base>.key
    key_bytes = secrets.token_bytes(32)
    key_path  = os.path.join(keys_dir, f"{base}.key")
    with open(key_path, "wb") as kf:
        kf.write(key_bytes)
    print(f"[+] AES-256 key generated and saved to: {key_path}")

    # 5. Chuẩn bị ctypes buffer cho key
    key_buf = (c_uint8 * len(key_bytes)).from_buffer_copy(key_bytes)

    # 6. Đường dẫn output .enc
    output_path = os.path.join(enc_dir, f"{base}.enc")

    # 7. (Tuỳ Windows) Load OpenSSL nếu cần
    openssl_bin = os.path.join(project_root, "openssl_library", "bin")
    if os.path.isdir(openssl_bin):
        os.add_dll_directory(openssl_bin)

    # 8. Load Chaotic_Cryptology.dll từ project_root/ChaoticCryptology/output
    dll_path = os.path.join(
        project_root, "ChaoticCryptology", "output", "Chaotic_Cryptology.dll"
    )
    try:
        dll = ctypes.WinDLL(dll_path)
    except Exception as e:
        print(f"[!] Không thể load DLL: {dll_path}\n{e}")
        sys.exit(1)

    # 9. Khai báo prototype hàm chaotic_aes_encrypt
    dll.chaotic_aes_encrypt.argtypes = [
        POINTER(c_uint8), c_int,      # plaintext + length
        POINTER(c_uint8), c_int,      # key + length
        POINTER(c_uint8), POINTER(c_int)  # out buffer + out length
    ]
    dll.chaotic_aes_encrypt.restype = c_int

    # 10. Đọc file input
    with open(input_path, "rb") as f:
        data = f.read()
    plen = len(data)
    print(f"[+] Read input video '{input_path}' ({plen} bytes)")

    # 11. Chuẩn bị buffer plaintext & output (đệm IV12 + TAG16)
    plain_buf = (c_uint8 * plen).from_buffer_copy(data)
    enc_buf   = (c_uint8 * (plen + 12 + 16))()
    enc_len   = c_int()

    # 12. Gọi hàm mã hoá
    ret = dll.chaotic_aes_encrypt(
        plain_buf, plen,
        key_buf,    len(key_bytes),
        enc_buf,    ctypes.byref(enc_len)
    )
    if ret != 0:
        print(f"[!] Encryption failed (code={ret})")
        sys.exit(1)

    # 13. Ghi kết quả vào static/encrypted_segments/<base>.enc
    with open(output_path, "wb") as out:
        out.write(bytes(enc_buf[:enc_len.value]))
    print(f"[+] Encrypted to '{output_path}' ({enc_len.value} bytes)")

if __name__ == "__main__":
    main()
