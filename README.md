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
                            ┌─────────────────────────┐
                            │ 1. Trình duyệt truy cập │
                            │    → GET /              │
                            └────────────┬────────────┘
                                         │
                     ┌───────────────────▼─────────────────────┐
                     │ 2. Trả về index.html + script.js + wasm │
                     └────────────┬────────────────────────────┘
                                  │
        ┌─────────────────────────▼────────────────────────────┐
        │ 3. JS chạy:                                          │
        │    → Sinh RSA key pair (clientKeyPair)               │
        │    → Export publicKey (PEM format)                   │
        │    → POST /register_pubkey/<videoId>?token=abc123    │
        └─────────────────────────┬────────────────────────────┘
                                  │
                     ┌────────────▼─────────────┐
                     │ 4. Server nhận và lưu PEM│
                     └────────────┬─────────────┘
                                  │
    ┌─────────────────────────────▼──────────────────────────────┐
    │ 5. Client gửi GET /get_key_rsa/<videoId>?token=abc123      │
    └─────────────────────────────┬──────────────────────────────┘
                                  │
           ┌──────────────────────▼────────────────────────┐
           │ 6. Server đọc AES key + seed + r từ file      │
           │    → Gói lại vào JSON                         │
           │    → Mã hoá RSA với public key của client     │
           │    → Trả về JSON { data_b64: ... }            │
           └──────────────────────┬────────────────────────┘
                                  │
         ┌────────────────────────▼────────────────────────┐
         │ 7. Client decrypt payload bằng privateKey       │
         │    → Lấy aesKey, seed, r                        │
         └────────────────────────┬────────────────────────┘
                                  │
              ┌───────────────────▼───────────────────┐
              │ 8. Fetch segment .enc từ server       │
              │    → /segment/<videoId>.enc           │
              └───────────────────┬───────────────────┘
                                  │
      ┌───────────────────────────▼────────────────────────────┐
      │ 9. Giải mã segment:                                    │
      │    - AES-GCM giải mã với aesKey                        │
      │    - Chaotic XOR sử dụng seed + r từ WASM keystream    │
      └───────────────────────────┬────────────────────────────┘
                                  │
     ┌────────────────────────────▼─────────────────────────────┐
     │ 10. Tạo blob từ video đã giải mã                         │
     │     → Gán `video.src = blobURL`                          │
     │     → Ẩn `video.src` với Object.defineProperty           │
     │     → Xoá biến `aesKey`, `clientKeyPair` khỏi scope      │
     │     → Bắt đầu phát video (`video.play()`)                │
     └────────────────────────────┬─────────────────────────────┘
                                  │
                   ┌─────────────▼────────────┐
                   │ 🎬Video phát ra màn hình │
                   └──────────────────────────┘


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
