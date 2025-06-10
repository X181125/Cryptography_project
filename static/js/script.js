// static/js/script.js
import ChaoticModule from '/static/wasm/chaotic_wasm.js';

let Module = null;

/**
 * Khởi tạo WebAssembly module.
 */
async function initWasm() {
  if (Module) return;
  Module = await ChaoticModule({
    locateFile(path) {
      // cho loader tìm *.wasm trong /static/wasm
      return `/static/wasm/${path}`;
    }
  });
}

/**
 * Nhập AES-GCM key từ Base64.
 */
async function importKeyFromB64(b64) {
  const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  if (raw.length !== 32) throw new Error('Key phải có 32 bytes');
  return crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['decrypt']);
}

/**
 * Giải mã một segment đã mã hóa:
 *  - AES-GCM decrypt (WebCrypto)
 *  - Chaotic-XOR (WASM)
 */
async function decryptChaotic(segmentBuffer, aesKey) {
  await initWasm();

  const view = new Uint8Array(segmentBuffer);
  if (view.length < 28) throw new Error('Segment quá nhỏ');

  // Tách IV + TAG + CIPHERTEXT
  const iv         = view.slice(0,12);
  const tag        = view.slice(12,28);
  const ciphertext = view.slice(28);

  // Ghép ciphertext + tag
  const ctPlusTag = new Uint8Array(ciphertext.length + tag.length);
  ctPlusTag.set(ciphertext, 0);
  ctPlusTag.set(tag, ciphertext.length);

  // AES-GCM decrypt
  const plainBuf = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv, tagLength: 128 },
    aesKey,
    ctPlusTag.buffer
  );
  const pre = new Uint8Array(plainBuf);

  // Sinh keystream Chaotic từ WASM
  // Lưu ý: hàm bạn export là _generate_chaotic_keystream
  const ptr = Module._generate_chaotic_keystream(0.5, 3.9, pre.length);
  const ks  = Module.HEAPU8.slice(ptr, ptr + pre.length);

  // XOR để thu hồi dữ liệu gốc
  const out = new Uint8Array(pre.length);
  for (let i = 0; i < pre.length; i++) {
    out[i] = pre[i] ^ ks[i];
  }

  // Giải phóng bộ nhớ WASM (hàm bạn export là _free_buffer)
  Module._free_buffer(ptr);

  return out;
}

/**
 * Fetch + decrypt segment đầu tiên rồi play
 */
async function streamAndPlaySingle() {
  try {
    const video = document.getElementById('videoPlayer');

    // 1) Lấy key từ server
    const keyRes = await fetch('/get_key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: 'abc123' })
    });
    if (!keyRes.ok) throw new Error(`Lấy key lỗi: ${keyRes.status}`);
    const { key_b64 } = await keyRes.json();
    const aesKey      = await importKeyFromB64(key_b64);

    // 2) Tải segment sample1.enc
    const segRes = await fetch('/segment/sample1.enc');
    if (!segRes.ok) throw new Error(`Tải segment lỗi: ${segRes.status}`);
    const segBuf = await segRes.arrayBuffer();

    // 3) Giải mã
    const original = await decryptChaotic(segBuf, aesKey);

    // 4) Tạo Blob URL và play
    const url = URL.createObjectURL(
      new Blob([original], { type: 'video/mp4' })
    );
    video.src = url;
    await video.play();
  } catch (err) {
    console.error('Error in streamAndPlaySingle():', err);
  }
}

document.addEventListener('DOMContentLoaded', streamAndPlaySingle);
