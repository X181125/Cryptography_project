#!/usr/bin/env python3
import os
import sys
import ctypes
import secrets
from ctypes import c_uint8, c_int, POINTER

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_video> <output_file_or_directory>")
        sys.exit(1)

    # Đường dẫn làm việc
    workspace   = os.path.dirname(os.path.abspath(__file__))
    input_path  = sys.argv[1]
    output_arg  = sys.argv[2]

    # Thư mục lưu key
    keys_dir    = os.path.join(workspace, "static", "keys")
    os.makedirs(keys_dir, exist_ok=True)
    key_path    = os.path.join(keys_dir, "secret_key.key")

    # 1) Sinh AES-256 key (32 bytes) và lưu vào key_path
    key_bytes = secrets.token_bytes(32)
    with open(key_path, "wb") as kf:
        kf.write(key_bytes)
    print(f"[+] AES-256 key generated and saved to: {key_path}")

    # Chuẩn bị buffer key ctypes
    key_buf = (c_uint8 * len(key_bytes)).from_buffer_copy(key_bytes)

    # Nếu output_arg là thư mục, đặt tên file .enc bên trong
    if os.path.isdir(output_arg):
        base, _ = os.path.splitext(os.path.basename(input_path))
        output_path = os.path.join(output_arg, f"{base}.enc")
    else:
        output_path = output_arg

    # Thêm OpenSSL bin vào PATH nếu cần (Windows)
    openssl_bin = os.path.join(workspace, "openssl_library", "bin")
    if os.path.isdir(openssl_bin):
        os.add_dll_directory(openssl_bin)

    # Load DLL
    dll_path = os.path.join(
        workspace, "ChaoticCryptology", "output", "Chaotic_Cryptology.dll"
    )
    dll = ctypes.WinDLL(dll_path)

    # Khai báo prototype hàm encrypt
    dll.chaotic_aes_encrypt.argtypes = [
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), POINTER(c_int)
    ]
    dll.chaotic_aes_encrypt.restype = c_int

    # Đọc video input
    with open(input_path, "rb") as f:
        data = f.read()
    plen = len(data)
    print(f"[+] Read input video '{input_path}' ({plen} bytes)")

    # Chuẩn bị buffer plaintext và buffer output
    plain_buf = (c_uint8 * plen).from_buffer_copy(data)
    enc_buf   = (c_uint8 * (plen + 12 + 16))()  # IV(12) + TAG(16) + ciphertext
    enc_len   = c_int()

    # Thực thi encrypt
    ret = dll.chaotic_aes_encrypt(
        plain_buf, plen,
        key_buf,   len(key_bytes),
        enc_buf,   ctypes.byref(enc_len)
    )
    if ret != 0:
        print(f"[!] Encryption failed (code={ret})")
        sys.exit(1)

    # Ghi kết quả ra file .enc
    with open(output_path, "wb") as out:
        out.write(bytes(enc_buf[:enc_len.value]))
    print(f"[+] Encrypted to '{output_path}' ({enc_len.value} bytes)")

if __name__ == "__main__":
    main()
