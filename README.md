# 🔐 Secure Video Streaming - Hybrid Cryptosystem Demo

Đây là một hệ thống demo mã hóa video sử dụng **kết hợp Chaotic keystream và AES-256-GCM** nhằm nâng cao tính bảo mật và xác thực khi truyền tải nội dung đa phương tiện (video). Client có thể giải mã và phát video ngay trong trình duyệt bằng WebCrypto API và WebAssembly (WASM). Ngoài ra, hệ thống đã bổ sung một lớp mã hóa RSA-OAEP tại tầng ứng dụng để bảo vệ key AES khi truyền từ server đến client.

## 🎯 Mục tiêu

* Mã hóa video sử dụng `Chaotic keystream XOR` và `AES-256-GCM`
* Bảo vệ key AES bằng RSA-OAEP: server mã hóa key với public key client, client giải mã bằng private key
* Cung cấp key từ server Flask qua API `/get_key_rsa` có token và RSA-encrypted
* Giải mã tại client bằng `crypto.subtle` (RSA + AES) và WASM để phát lại video
* Trình diễn tính khả thi và đánh giá hiệu suất của giải pháp hybrid

---

## 📁 Cấu trúc thư mục

```
secure_video_streamming/
├─ ChaoticCryptology/            # C++ library & build config
│   ├─ include/
│   ├─ src/
│   └─ output/                   # Chaotic_Cryptology.dll
├─ scripts/
│   └─ encrypt_video.py         # Encrypt file via DLL
├─ attacker_sniffer.py           # MITM/sniffer simulation
├─ requirements.txt              # Python deps (Flask, cryptography)
├─ static/
│   ├─ js/
│   │   └─ script.js            # Decrypt+play logic + benchmarks
│   ├─ wasm/
│   ├─ keys/                     # sample1.key
│   ├─ pubkeys/                  # client public keys
│   ├─ encrypted_segments/       # sample1.enc
│   └─ video/                    # sample1.mp4
├─ templates/
│   └─ index.html                # Demo page
└─ server.py                     # Flask server with RSA and segment APIs
```

---

## 🔐 Quy trình mã hóa (Server)

1. Sinh **AES-256 key** ngẫu nhiên, lưu `static/keys/sample1.key`.
2. Mã hóa video:

   * **Chaotic XOR** (logistic map seed=0.5, r=3.9)
   * **AES-256-GCM** với IV ngẫu nhiên
   * Xuất file `sample1.enc` chứa `[IV||TAG||CIPHERTEXT]`
3. Bảo vệ key AES bằng **RSA-OAEP** cấp ứng dụng:

   * Client **sinh cặp RSA** (public/private) bằng WebCrypto, gửi public key PEM lên `/register_pubkey/sample1`.
   * Khi client gọi `/get_key_rsa/sample1?token=abc123`, server đọc AES-key, mã hóa bằng public key client, trả về Base64.

👉 Chạy encrypt và đo thời gian mã hóa:

```bash
python scripts/encrypt_video.py video/sample1.mp4
```

Console sẽ in chi tiết benchmark:

```
[Benchmark] DLL load: 0.36s
[Benchmark] File read: 0.02s
[Benchmark] Encryption: 0.04s
[Benchmark] File write: 0.007s
Total pipeline: 0.43s
```

---

## 🔓 Quy trình giải mã (Client)

1. Đăng ký public key:

   ```js
   await registerPubKey('sample1');
   ```
2. Lấy key RSA-encrypted và giải:

   ```js
   const aesKey = await fetchAndDecryptKey('sample1');
   ```
3. Tải segment:

   ```js
   const buf = await fetch('/segment/sample1.enc').then(r=>r.arrayBuffer());
   ```
4. Giải mã **AES-GCM** + **Chaotic XOR** qua WASM
5. Tạo `Blob` và `video.play()`

---

## 🕒 Kết quả đo hiệu năng (720p, 6s, \~520KB)

| Bước                               | Thời gian |
| ---------------------------------- | --------: |
| RSA keygen + register              |  82.50 ms |
| Fetch+RSA-decrypt+import AES key   |  52.60 ms |
| Fetch segment                      |  33.00 ms |
| AES-GCM decrypt                    |   4.30 ms |
| Chaotic XOR                        |   5.50 ms |
| **Decrypt pipeline**               |  10.90 ms |
| **End-to-end từ fetch→play()**     | 307.00 ms |
| **Server-side pipeline (encrypt)** | 430.00 ms |

* **Throughput network** \~16 MB/s trên localhost.
* **Decrypt pipeline** \~520 KB trong 11 ms ⇒ \~48 MB/s.
* **Latency end-to-end** \~307 ms < 0.5s, đáp ứng nhanh cho playback.

---

## 🗂️ Luồng hoạt động chi tiết

Dưới đây là diễn giải từng bước xuyên suốt từ lúc client truy cập trang đến khi video được phát:

```plaintext
1) CLIENT tải trang demo:
   • GET / → server trả về templates/index.html
   • Browser tải index.html, parse và thực thi script:

2) TẢI ASSET (Client-side):
   • GET /static/js/script.js → tải logic decrypt + play
   • GET /static/wasm/chaotic_wasm.js → tải wrapper WASM
   • GET /static/wasm/chaotic_wasm.wasm → tải binary WASM

3) KHỞI TẠO RSA (Client-side):
   • script.js gọi registerPubKey('sample1') → sinh cặp RSA-OAEP
   • Client POST public key PEM → /register_pubkey/sample1
   • Server nhận → lưu file static/pubkeys/sample1.pem

4) LẤY AES-KEY (Client-side):
   • Client GET /get_key_rsa/sample1?token=abc123
   • Server:
     - Đọc public key PEM của client
     - Đọc raw AES-key từ static/keys/sample1.key
     - Mã hóa AES-key bằng RSA-OAEP (SHA-256)
     - Trả JSON { key_rsa_b64 }
   • Client nhận Base64, giải RSA decrypt → raw AES-key
   • Client importKey → CryptoKey AES-GCM

5) TẢI VÀ GIẢI MÃ SEGMENT (Client-side):
   • Client GET /segment/sample1.enc
   • Server trả file .enc (gồm IV||TAG||CIPHERTEXT)
   • Client đọc ArrayBuffer:
     - AES-GCM decrypt bằng crypto.subtle
     - Sinh keystream chaotic từ WASM
     - XOR với plaintext để phục hồi video gốc

6) PHÁT VIDEO (Client-side):
   • Tạo Blob URL từ Uint8Array output
   • Gán vào <video.src> và gọi video.play()

```

---

## ▶️ Chạy thử demo

1. Cài yêu cầu:

```bash
pip install flask cryptography scapy
```

2. Biên dịch WASM:

```bash
emcc chaotic_xor.cpp -O3 -s MODULARIZE=1 \
  -s EXPORT_NAME="ChaoticModule" \
  -s EXPORTED_FUNCTIONS="['_generate_chaotic_keystream','_free_buffer']" \
  -s EXPORTED_RUNTIME_METHODS="['cwrap','HEAPU8']" \
  -o static/wasm/chaotic_wasm.js
```

3. Khởi động server:

```bash
python server.py
```

4. Mở [http://127.0.0.1:9000](http://127.0.0.1:9000)

---

## 🧑‍💻 Tác giả

Nhóm 23520564 – 23520648 – 23520394
Môn học: **Cryptography and Security**

```
```
