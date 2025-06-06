// static/js/script.js

/**
 * Import AES-256 key từ Base64 (DRM server)
 */
async function importKeyFromB64(b64) {
  try {
    console.log("📌 [importKey] Nhận key Base64:", b64);
    const rawKey = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    console.log("📌 [importKey] rawKey (32 bytes):", rawKey);
    const aesKey = await crypto.subtle.importKey(
      "raw",
      rawKey,
      "AES-GCM",
      false,
      ["decrypt"]
    );
    console.log("✅ [importKey] Import thành công CryptoKey:", aesKey);
    return aesKey;
  } catch (err) {
    console.error("❌ [importKey] importKeyFromB64 failed:", err);
    throw err;
  }
}

/**
 * Decrypt Chaotic XOR + AES-GCM cho một ArrayBuffer segment.
 * Trả về Uint8Array decryptedChaoticXor.
 */
async function decryptChaoticAES(segmentBuffer, aesKeyCrypto) {
  try {
    const view = new Uint8Array(segmentBuffer);
    if (view.byteLength < 28) {
      throw new Error("❌ [decrypt] Segment buffer quá nhỏ (<28 bytes)");
    }

    const nonce = view.slice(0, 12);
    const tag = view.slice(12, 28);
    const ciphertext = view.slice(28);
    console.log("📌 [decrypt] Nonce:", nonce);
    console.log("📌 [decrypt] Tag:", tag);
    console.log("📌 [decrypt] Ciphertext length:", ciphertext.length);

    // Ghép ciphertext+tag để WebCrypto decrypt
    const combined = new Uint8Array(ciphertext.length + tag.length);
    combined.set(ciphertext, 0);
    combined.set(tag, ciphertext.length);

    const decryptedArrayBuffer = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: nonce, tagLength: 128 },
      aesKeyCrypto,
      combined
    );
    console.log("✅ [decrypt] AES-GCM decrypt thành công, length:", decryptedArrayBuffer.byteLength);

    return new Uint8Array(decryptedArrayBuffer);
  } catch (err) {
    console.error("❌ [decrypt] decryptChaoticAES failed:", err);
    throw err;
  }
}

/**
 * Tạo keystream Chaotic (logistic map) với seed, r, độ dài length.
 */
function chaoticKeystream(seed, r, length) {
  console.log(`📌 [chaotic] seed=${seed}, r=${r}, length=${length}`);
  let x = seed;
  const out = new Uint8Array(length);
  for (let i = 0; i < length; i++) {
    x = r * x * (1 - x);
    out[i] = Math.floor(x * 256) % 256;
  }
  return out;
}

/**
 * Hàm chính: tải sample1.bin, decrypt Chaotic+AES rồi tạo Blob URL.
 * XONG thì gán vào video.src và phát.
 */
async function streamAndPlaySingle() {
  try {
    console.log("[*] Bắt đầu streamAndPlaySingle()");

    // 1. Lấy key từ DRM server
    const token = "abc123";
    console.log("[*] POST /get_key với token =", token);
    const keyResp = await fetch("http://localhost:9000/get_key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (!keyResp.ok) {
      throw new Error(`[streamAndPlaySingle] get_key status: ${keyResp.status}`);
    }
    const { key_b64 } = await keyResp.json();
    console.log("[+] Received key_b64:", key_b64);

    // Import key
    const aesKeyCrypto = await importKeyFromB64(key_b64);

    // 2. Lấy segment duy nhất: "sample1.bin"
    const segName = "sample1.bin";
    console.log("[*] Fetching /segment/" + segName);
    const segRes = await fetch(`/segment/${segName}`);
    if (!segRes.ok) {
      throw new Error(`[streamAndPlaySingle] /segment/${segName} status: ${segRes.status}`);
    }
    const segBuffer = await segRes.arrayBuffer();
    console.log("[+] Fetched", segName, "byteLength =", segBuffer.byteLength);

    // 3. Decrypt Chaotic + AES
    const decryptedChaoticXor = await decryptChaoticAES(segBuffer, aesKeyCrypto);

    // 4. Tạo keystream Chaotic
    const length = decryptedChaoticXor.byteLength;
    const keystream = chaoticKeystream(0.5, 3.9, length);

    // 5. XOR ngược để lấy data gốc của MP4
    const originalBytes = new Uint8Array(length);
    for (let i = 0; i < length; i++) {
      originalBytes[i] = decryptedChaoticXor[i] ^ keystream[i];
    }
    console.log("[+] OriginalBytes header (8 bytes):", originalBytes.slice(0, 8));
    // 8 byte đầu phải là [0,0,0,xx,102,116,121,112] (ftyp)

    // 6. Tạo Blob từ originalBytes và gán vào video.src
    const blob = new Blob([originalBytes], { type: "video/mp4" });
    const url = URL.createObjectURL(blob);
    const videoElem = document.getElementById("videoPlayer");
    videoElem.src = url;
    videoElem.load();
    videoElem.play().catch(err => console.warn("[!] play() failed:", err));

    console.log("✅ [streamAndPlaySingle] Đã tạo Blob URL và set video.src");
  } catch (err) {
    console.error("❌ [streamAndPlaySingle] Lỗi:", err);
  }
}

// Khi DOMContentLoaded, gọi streamAndPlaySingle()
document.addEventListener("DOMContentLoaded", () => {
  console.log("[*] DOMContentLoaded → streamAndPlaySingle");
  streamAndPlaySingle();
});
