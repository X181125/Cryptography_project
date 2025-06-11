// 🧠 Biến toàn cục lưu instance WASM
let Module = null;

// 🧩 Khởi tạo WebAssembly module chaotic
async function initWasm() {
  if (!Module) {
    if (!window.ChaoticModulePromise) throw new Error("WASM chưa load xong");
    Module = await window.ChaoticModulePromise;

    // Đợi WASM runtime khởi tạo xong nếu cần
    if (!Module.calledRun && typeof Module.onRuntimeInitialized === 'function') {
      await new Promise(resolve => {
        const orig = Module.onRuntimeInitialized;
        Module.onRuntimeInitialized = () => { orig(); resolve(); };
      });
    }
  }
  return Module;
}

// 🔐 Sinh cặp khóa RSA và gửi public key lên server
async function registerPubKey(videoId) {
  const kp = await crypto.subtle.generateKey(
    {
      name: 'RSA-OAEP',
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256'
    },
    false, ['encrypt', 'decrypt']
  );

  const spki = await crypto.subtle.exportKey('spki', kp.publicKey);
  const b64 = btoa(String.fromCharCode(...new Uint8Array(spki)));
  const pem = `-----BEGIN PUBLIC KEY-----\n${b64}\n-----END PUBLIC KEY-----`;

  const token = 'abc123'; // hoặc lấy từ biến môi trường frontend

  await fetch(`/register_pubkey/${videoId}?token=${encodeURIComponent(token)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/octet-stream',
      'Authorization': `Bearer ${token}` // nếu backend cần header nữa
    },
    body: new TextEncoder().encode(pem)
  });

  return kp;
}

// 🗝️ Nhận payload mã hoá và giải mã ra AES key + tham số chaotic
async function fetchDecryptMetadata(videoId) {
  const kp = await registerPubKey(videoId); // Gửi khóa trước

  const res = await fetch(`/get_key_rsa/${videoId}?token=abc123`);
  const { data_b64 } = await res.json(); // Payload đã mã hoá bằng RSA
  const cipher = Uint8Array.from(atob(data_b64), c => c.charCodeAt(0));

  // Giải mã payload bằng private key
  const raw = await crypto.subtle.decrypt(
    { name: 'RSA-OAEP' },
    kp.privateKey,
    cipher
  );

  // Parse JSON chứa aes_key (base64), seed, r
  const jsonStr = new TextDecoder().decode(raw);
  const { aes_key: aes_b64, seed, r } = JSON.parse(jsonStr);

  // Import AES-GCM key từ base64
  const rawAes = Uint8Array.from(atob(aes_b64), c => c.charCodeAt(0));
  const aesKey = await crypto.subtle.importKey(
    'raw', rawAes, { name: 'AES-GCM' }, false, ['decrypt']
  );

  return { aesKey, seed, r, kp };
}

// 🔓 Giải mã segment: AES-GCM + chaotic XOR
async function decryptChaotic(segmentBuffer, aesKey, seed, r) {
  const wasm = await initWasm();
  const view = new Uint8Array(segmentBuffer);
  const iv = view.subarray(0, 12);        // IV (nonce) 12 bytes
  const tag = view.subarray(12, 28);      // Auth tag 16 bytes
  const cipher = view.subarray(28);       // Dữ liệu mã hoá

  // Nối ciphertext và tag lại
  const ctAndTag = new Uint8Array(cipher.length + tag.length);
  ctAndTag.set(cipher, 0);
  ctAndTag.set(tag, cipher.length);

  // Giải mã AES-GCM
  const plainBuf = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv, tagLength: 128 },
    aesKey,
    ctAndTag
  );

  // XOR với keystream chaotic
  const pre = new Uint8Array(plainBuf);
  const ptr = Module._generate_chaotic_keystream(seed, r, pre.length);
  const ks = new Uint8Array(Module.HEAPU8.buffer, ptr, pre.length);
  const out = new Uint8Array(pre.length);
  for (let i = 0; i < pre.length; i++) out[i] = pre[i] ^ ks[i];
  Module._free_buffer(ptr); // Giải phóng bộ nhớ WASM

  return out;
}

// ▶️ Hàm chính: tải, giải mã, phát video
async function streamAndPlaySingle() {
  try {
    const videoId = 'sample1';

    // B1: Nhận AES key + chaotic params
    const { aesKey, seed, r, kp } = await fetchDecryptMetadata(videoId);

    // B2: Tải segment video đã mã hoá
    const res = await fetch(`/segment/${videoId}.enc`);
    const buf = await res.arrayBuffer();

    // B3: Giải mã hoàn toàn
    const decrypted = await decryptChaotic(buf, aesKey, seed, r);

    // B4: Phát video
    const video = document.getElementById('videoPlayer');
    const blobUrl = URL.createObjectURL(new Blob([decrypted], { type: 'video/mp4' }));
    video.setAttribute('src', blobUrl);

    // B5: Ẩn src khỏi DevTools
    Object.defineProperty(video, 'src', {
      get: () => {
        console.warn("🚫 src đã bị ẩn bởi hệ thống bảo vệ.");
        return null;
      },
      set: function (val) {
        HTMLMediaElement.prototype.__lookupSetter__('src').call(this, val);
      },
      configurable: true
    });

    // B6: Play ngay sau khi set src
    video.play().then(() => {
      // B7: Sau khi play, xoá key khỏi bộ nhớ
      setTimeout(() => {
        try {
          aesKey = null;
          kp = null;
        } catch (_) {}
        if (typeof window.gc === 'function') window.gc(); // Gọi garbage collector nếu có
      }, 500);
    });

    // B8: Chặn chuột trái để tránh context menu
    video.addEventListener('mousedown', e => {
      if (e.button === 0) e.preventDefault();
    });

  } catch (err) {
    console.error("❌ Lỗi phát video:", err);
  }
}

// 🚀 Khởi động sau khi DOM load xong
document.addEventListener('DOMContentLoaded', streamAndPlaySingle);
