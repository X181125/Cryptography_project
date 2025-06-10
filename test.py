import ctypes
from ctypes import c_uint8, c_int, POINTER

# 1. Load DLL (điều chỉnh đường dẫn cho đúng vị trí của bạn)
#    nếu chạy trên Windows, dùng WinDLL; trên Linux .so thì dùng CDLL
dll = ctypes.WinDLL(r"D:\Visual_Studio_Code_Workspace\secure_video_streamming\ChaoticCryptology\output\Chaotic_Cryptology.dll")

# 2. Khai báo prototype cho hai hàm
#    int chaotic_aes_encrypt(
#        const uint8_t* plaintext, int plaintext_len,
#        const uint8_t* aes_key, int key_len,
#        uint8_t* out_buf, int* out_len
#    );
dll.chaotic_aes_encrypt.argtypes = [
    POINTER(c_uint8), c_int,
    POINTER(c_uint8), c_int,
    POINTER(c_uint8), POINTER(c_int)
]
dll.chaotic_aes_encrypt.restype = c_int

#    int chaotic_aes_decrypt(
#        const uint8_t* in_buf, int in_len,
#        const uint8_t* aes_key, int key_len,
#        uint8_t* out_plain, int* out_plain_len
#    );
dll.chaotic_aes_decrypt.argtypes = [
    POINTER(c_uint8), c_int,
    POINTER(c_uint8), c_int,
    POINTER(c_uint8), POINTER(c_int)
]
dll.chaotic_aes_decrypt.restype = c_int

# 3. Chuẩn bị dữ liệu
plaintext = b"Hello, Chaotic!"
pt_len = len(plaintext)

# Demo key (phải giống DEMO_KEY trong DLL)
demo_key = bytes([
    0x60,0x3d,0xeb,0x10,0x15,0xca,0x71,0xbe,
    0x2b,0x73,0xae,0xf0,0x85,0x7d,0x77,0x81,
    0x1f,0x35,0x2c,0x07,0x3b,0x61,0x08,0xd7,
    0x2d,0x98,0x10,0xa3,0x09,0x14,0xdf,0xf4
])

# Chuyển sang buffer ctypes
plain_buf = (c_uint8 * pt_len).from_buffer_copy(plaintext)
key_buf   = (c_uint8 * len(demo_key)).from_buffer_copy(demo_key)

# Output buffers
enc_buf   = (c_uint8 * (pt_len + 12 + 16))()
enc_len   = c_int()

# 4. Gọi hàm encrypt
ret = dll.chaotic_aes_encrypt(
    plain_buf, pt_len,
    key_buf,   len(demo_key),
    enc_buf,   ctypes.byref(enc_len)
)
if ret != 0:
    raise RuntimeError(f"Encrypt failed (code={ret})")

print("Encrypted length:", enc_len.value)

# 5. Gọi hàm decrypt
dec_buf   = (c_uint8 * pt_len)()
dec_len   = c_int()

ret = dll.chaotic_aes_decrypt(
    enc_buf, enc_len.value,
    key_buf, len(demo_key),
    dec_buf, ctypes.byref(dec_len)
)
if ret != 0:
    raise RuntimeError(f"Decrypt failed (code={ret})")

# 6. Lấy về kết quả plaintext
decrypted = bytes(dec_buf[:dec_len.value])
print("Decrypted text:", decrypted.decode())
