
# Tài liệu tổng quan dự án `secure_video_streamming`

Dưới đây là mô tả chi tiết về cấu trúc thư mục, các thành phần chính và luồng hoạt động tổng thể của hệ thống streaming video bảo mật (giống Netflix).

---

## 1. Giới thiệu chung

Hệ thống này mô phỏng quy trình truyền phát video bảo mật tương tự Netflix, với backend được xây dựng bằng **Django** và frontend là ứng dụng web chạy trong trình duyệt. Các thành phần chính bao gồm:

- **Server (Django)**
  - Quản lý nội dung video gốc, chia thành các segment (định dạng nhị phân).
  - Thực hiện trao đổi khóa ECDH và sinh khóa phiên (session key) AES-256.
  - Mã hóa mỗi segment (Chaotic XOR + AES-256-GCM) ngay trước khi phục vụ cho client.
  - Cung cấp các API endpoints để client lấy public key, gửi public key của client và tải segment mã hóa.

- **Client Web (trong trình duyệt)**
  - Sử dụng **WebCrypto API** hoặc **WebAssembly** để thực hiện ECDH (P-256) và giải mã segment.
  - Nhận session key, decrypt segment (AES-GCM + Chaotic XOR ngược), sau đó đẩy plaintext vào **Media Source Extensions** (MSE) hoặc **WebCodecs** để decode và hiển thị video.

Mục tiêu:
- Bảo mật luồng video, đảm bảo nội dung gốc không thể lộ nếu không có khóa.
- Thêm lớp Chaotic XOR để phá pattern dữ liệu, nâng cao bảo mật.
- Khả năng hoạt động trên trình duyệt bằng WebAssembly hoặc WebCrypto.

---

## 2. Kiến trúc Tổng quan

### 2.1. Thành phần chính

1. **Django Server**
   - Một hoặc nhiều App Django (ví dụ `video_app`, `security`).
   - Models (nếu cần) quản lý metadata và session key.
   - Views/REST API endpoints để:
     1. Trả public key ECDH server.
     2. Nhận public key client, derive session_key.
     3. Phục vụ segment mã hóa.
   - Middleware (nếu cần) để xác thực request.

2. **Client Web**
   - Trang HTML/JavaScript (ví dụ `index.html`).
   - Sử dụng **WebCrypto API** để ECDH và AES-GCM decrypt.
   - Sử dụng **WebAssembly** (nếu compile code C++).
   - Sử dụng **Media Source Extensions** hoặc **WebCodecs** để decode và hiển thị video.

3. **WebAssembly (WASM)**
   - Biên dịch `ChaoticCryptology` (C++ Chaotic XOR + AES-GCM) sang WASM.
   - Khai báo hàm `chaotic_aes_encrypt` và `chaotic_aes_decrypt` cho client.

---

## 3. Cấu trúc Thư mục

```
secure_video_streamming/
├─ ChaoticCryptology/
│   ├─ include/
│   │   ├─ chaotic.h
│   │   └─ crypto.h
│   ├─ src/
│   │   ├─ chaotic.cpp
│   │   ├─ crypto.cpp
│   │   └─ main.cpp
│   ├─ .vscode/
│   │   └─ tasks.json
├─ attacker_sniffer.py
├─ chaotic.py
├─ decrypt_utils.py
├─ encrypt_segments.py
├─ encrypt_video.py
├─ requirements.txt
├─ server.py
├─ static/
│   ├─ js/
│   │   └─ script.js
│   ├─ keys/
│   │   └─ (tạo file aes_256.key khi chạy encrypt_segments.py)
│   ├─ encrypted_segments/
│   │   └─ (các file .bin tạo khi chạy encrypt_segments.py)
│   └─ video/
│       └─ sample.mp4
└─ templates/
    └─ index.html
```

### Giải thích

- **ChaoticCryptology/**
  - `include/`: Header Chaotic XOR và AES-GCM.
  - `src/`: Code C++ cho Chaotic và Crypto.
  - `tasks.json`: Cấu hình build DLL/WASM.

- **attacker_sniffer.py**
  Mô phỏng sniffer chặn gói mạng.

- **chaotic.py**
  Wrappers Python Chaotic XOR + AES-GCM (dùng `cryptography`).

- **decrypt_utils.py**
  Giải mã offline, kiểm thử segment.

- **encrypt_segments.py**
  Chia `static/video/sample.mp4` thành segment, mã hóa mỗi segment (Chaotic + AES-GCM).

- **encrypt_video.py**
  Mã hóa toàn file video (dùng khi không chia segment).

- **requirements.txt**
  Liệt kê thư viện Python (`cryptography`, `Django`, v.v.).

- **server.py**
  Ứng dụng web chính (Flask/Django): trao đổi public key, phục vụ segment.

- **static/**
  - `js/script.js`: JavaScript client (WebCrypto/WASM, MSE).
  - `keys/`: Lưu `aes_256.key` (khóa dùng offline).
  - `encrypted_segments/`: Segment đã mã hóa.
  - `video/sample.mp4`: Video gốc.

- **templates/index.html**
  Giao diện HTML chứa `<video>` và load `script.js`.

---

## 4. Quá trình Triển khai

### 4.1. Chuẩn bị (Offline)

1. **Cài đặt thư viện Python**
   ```bash
   pip install -r requirements.txt
   ```

2. **Biên dịch ChaoticCryptology**
   - Vào `ChaoticCryptology/`, chạy task build. Kết quả có DLL hoặc WASM.
   - Nếu dùng WASM, copy `chaotic_wasm.js` + `chaotic_wasm.wasm` vào `static/wasm/`.

3. **Chạy `encrypt_segments.py`**
   ```bash
   python encrypt_segments.py
   ```
   - Chia `static/video/sample.mp4` thành segment.
   - Sinh khóa AES-256 (`static/keys/aes_256.key`).
   - Mã hóa mỗi segment, lưu vào `static/encrypted_segments/`.

### 4.2. Khởi động Server

1. **Chạy Server Python**:
   - Flask: `python server.py`.
   - Django: `python manage.py runserver`.
   - Đảm bảo chạy dưới HTTPS.

2. **Server tạo ECDH key pair** (curve P-256) bằng OpenSSL.

### 4.3. Client khởi tạo Phiên

1. **Tải `index.html`**
   - Browser request `/` → Django trả `index.html`.
   - `index.html` load `script.js`.

2. **Fetch public key server**
   ```js
   fetch("/api/get_server_pubkey/")
     .then(res => res.arrayBuffer())
     .then(serverPubDER => { ... });
   ```

3. **Client tạo cặp khóa ECDH**
   ```js
   crypto.subtle.generateKey(
     { name: "ECDH", namedCurve: "P-256" },
     true,
     ["deriveKey", "deriveBits"]
   );
   ```

4. **Client derive session_key**
   ```js
   const serverPubKey = await crypto.subtle.importKey(
     "spki", serverPubDER, { name: "ECDH", namedCurve: "P-256" }, false, []
   );
   const rawShared = await crypto.subtle.deriveBits(
     { name: "ECDH", public: serverPubKey },
     clientPrivateKey,
     256
   );
   const sessionKeyBytes = new Uint8Array(
     await crypto.subtle.digest("SHA-256", rawShared)
   );
   const aesCryptoKey = await crypto.subtle.importKey(
     "raw", sessionKeyBytes,
     { name: "AES-GCM" },
     false, ["encrypt", "decrypt"]
   );
   ```

5. **Client gửi public key**
   ```js
   const clientPubDER = await crypto.subtle.exportKey("spki", clientPublicKey);
   fetch("/api/post_client_pubkey/", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ client_pubkey: arrayBufferToBase64(clientPubDER) })
   });
   ```

6. **Server nhận và derive**
   - Import public key client, compute rawShared, derive session_key, lưu vào session.

### 4.4. Streaming Segment

1. **Khởi tạo MediaSource & SourceBuffer**
   ```js
   const videoElem = document.getElementById("video");
   const mediaSource = new MediaSource();
   videoElem.src = URL.createObjectURL(mediaSource);
   mediaSource.addEventListener("sourceopen", onSourceOpen);
   ```

2. **Hàm `loadSegment(idx)`**
   ```js
   async function loadSegment(idx) {
     const res = await fetch(`/segments/1/${idx}.enc`);
     const encBuf = await res.arrayBuffer();
     const view = new DataView(encBuf);
     const seed = view.getFloat64(0, true);
     const iv = new Uint8Array(encBuf, 8, 12);
     const cipherTag = new Uint8Array(encBuf, 8 + 12);
     const preAesBuf = await crypto.subtle.decrypt(
       { name: "AES-GCM", iv: iv, tagLength: 128 },
       aesCryptoKey,
       cipherTag.buffer
     );
     const preAes = new Uint8Array(preAesBuf);
     const N = preAes.length;
     const keystream = generateChaoticKeystream(seed, 3.9, N);
     const plaintext = new Uint8Array(N);
     for (let i = 0; i < N; i++) {
       plaintext[i] = preAes[i] ^ keystream[i];
     }
     sourceBuffer.appendBuffer(plaintext);
   }
   ```

3. **Lặp load liên tục**
   ```js
   let currentIndex = 1;
   sourceBuffer.addEventListener("updateend", () => {
     if (currentIndex < totalSegments) {
       currentIndex++;
       loadSegment(currentIndex);
     } else {
       mediaSource.endOfStream();
     }
   });
   loadSegment(currentIndex);
   ```

4. **Nếu dùng WebAssembly** thay bước decrypt/AES XOR bằng gọi hàm WASM.

### 4.5. Kết thúc

- Video phát xong, client gọi `mediaSource.endOfStream()`.
- Server giữ session_key đến khi timeout hoặc client logout.

---

## 5. Endpoint và Flow API

1. **GET `/api/get_server_pubkey/`**
   - Trả raw DER (SPKI) public key server.

2. **POST `/api/post_client_pubkey/`**
   - Body JSON: `{ "client_pubkey": "<Base64 DER SPKI>" }`
   - Server derive session_key, lưu vào session.

3. **GET `/api/get_metadata/`** (tùy chọn)
   - Trả JSON: `{"totalSegments": 100, "segmentSize": 65536}`.

4. **GET `/segments/<videoId>/<idx>.enc`**
   - Kiểm tra session_key, trả file segment mã hóa.

5. **GET `/`** hoặc `/index.html`
   - Trả `templates/index.html`, chứa cấu hình client.

---

## 6. Bảo mật và Lưu ý

- **HTTPS/TLS**: Bắt buộc.
- **Session quản lý**: Lưu `session_key` trong Django session.
- **Rotate khóa**: Có thể thực hiện rotate ECDH.
- **Seed Chaotic**: Sinh ngẫu nhiên mỗi segment.
- **IV AES-GCM**: Ngẫu nhiên, 12 byte, không tái sử dụng với cùng khóa.
- **Integrity**: GCM tag bảo vệ chống giả mạo.
- **CORS/CSRF**: Cấu hình cho API POST.
- **Cache**: Segment mã hóa phụ thuộc session_key, không cache chung.
- **Attacker Sniffer**: `attacker_sniffer.py` để kiểm thử.
