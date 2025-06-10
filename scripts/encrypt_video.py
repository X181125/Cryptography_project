#!/usr/bin/env python3
import os
import sys
import ctypes
import secrets
import time
from ctypes import c_uint8, c_int, POINTER

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_video>")
        sys.exit(1)

    # Xác định project_root
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"[!] File không tồn tại: {input_path}")
        sys.exit(1)

    base, _ = os.path.splitext(os.path.basename(input_path))
    keys_dir = os.path.join(project_root, "static", "keys")
    enc_dir  = os.path.join(project_root, "static", "encrypted_segments")
    os.makedirs(keys_dir, exist_ok=True)
    os.makedirs(enc_dir, exist_ok=True)

    # Sinh và lưu AES-256 key
    key_bytes = secrets.token_bytes(32)
    key_path  = os.path.join(keys_dir, f"{base}.key")
    with open(key_path, "wb") as kf:
        kf.write(key_bytes)
    print(f"[+] AES-256 key saved to: {key_path}")

    # Bắt đầu đo tổng pipeline
    t_start = time.perf_counter()

    # Load DLL
    dll_path = os.path.join(project_root, "ChaoticCryptology", "output", "Chaotic_Cryptology.dll")
    t0 = time.perf_counter()
    try:
        dll = ctypes.WinDLL(dll_path)
    except Exception as e:
        print(f"[!] Không thể load DLL: {dll_path}\n{e}")
        sys.exit(1)
    t1 = time.perf_counter()
    print(f"[Benchmark] DLL load took {t1 - t0:.4f} s")

    # Định nghĩa prototype
    dll.chaotic_aes_encrypt.argtypes = [
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), c_int,
        POINTER(c_uint8), POINTER(c_int)
    ]
    dll.chaotic_aes_encrypt.restype = c_int

    # Đọc input file
    t2 = time.perf_counter()
    with open(input_path, "rb") as f:
        data = f.read()
    plen = len(data)
    print(f"[+] Read input video ({plen} bytes)")
    t3 = time.perf_counter()
    print(f"[Benchmark] File read took {t3 - t2:.4f} s")

    # Chuẩn bị buffer
    plain_buf = (c_uint8 * plen).from_buffer_copy(data)
    enc_buf   = (c_uint8 * (plen + 12 + 16))()
    enc_len   = c_int()

    # Thực hiện mã hóa
    t4 = time.perf_counter()
    ret = dll.chaotic_aes_encrypt(
        plain_buf, plen,
        (c_uint8 * len(key_bytes)).from_buffer_copy(key_bytes), len(key_bytes),
        enc_buf, ctypes.byref(enc_len)
    )
    t5 = time.perf_counter()
    if ret != 0:
        print(f"[!] Encryption failed (code={ret})")
        sys.exit(1)
    print(f"[Benchmark] Encryption took {t5 - t4:.4f} s")

    # Ghi kết quả
    output_path = os.path.join(enc_dir, f"{base}.enc")
    t6 = time.perf_counter()
    with open(output_path, "wb") as out:
        out.write(bytes(enc_buf[:enc_len.value]))
    t7 = time.perf_counter()
    print(f"[+] Encrypted to '{output_path}' ({enc_len.value} bytes)")
    print(f"[Benchmark] File write took {t7 - t6:.4f} s")

    # Tổng thời gian
    t_end = time.perf_counter()
    print(f"[Benchmark] Total pipeline took {t_end - t_start:.4f} s")

if __name__ == "__main__":
    main()
