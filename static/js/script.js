let Module = null;

async function initWasm() {
  if (!Module) {
    if (!window.ChaoticModulePromise) {
      throw new Error("WASM chưa load xong");
    }
    Module = await window.ChaoticModulePromise;

    // Đợi onRuntimeInitialized nếu có (tránh race condition)
    if (!Module.calledRun && typeof Module.onRuntimeInitialized === 'function') {
      await new Promise((resolve) => {
        const orig = Module.onRuntimeInitialized;
        Module.onRuntimeInitialized = function () {
          orig();
          resolve();
        };
      });
    }
  }
  return Module;
}

async function fetchKey(videoId) {
  const token = 'abc123';
  const res = await fetch(`/get_key/${videoId}?token=${token}`);
  if (!res.ok) throw new Error(`Lấy key lỗi: ${res.status}`);
  const { key_b64 } = await res.json();
  return key_b64;
}

async function importKeyFromB64(b64) {
  const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  if (raw.length !== 32) throw new Error('Key phải có 32 bytes');
  return crypto.subtle.importKey('raw', raw, { name: 'AES-GCM' }, false, ['decrypt']);
}

async function decryptChaotic(segmentBuffer, aesKey) {
  const wasm = await initWasm();
  const view = new Uint8Array(segmentBuffer);
  if (view.length < 28) throw new Error('Segment quá nhỏ');

  const iv = view.subarray(0, 12);
  const tag = view.subarray(12, 28);
  const ciphertext = view.subarray(28);

  const ctAndTag = new Uint8Array(ciphertext.length + tag.length);
  ctAndTag.set(ciphertext, 0);
  ctAndTag.set(tag, ciphertext.length);

  let plainBuf;
  try {
    plainBuf = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv, tagLength: 128 },
      aesKey,
      ctAndTag
    );
  } catch (e) {
    console.error('AES-GCM decrypt error:', e);
    throw e;
  }

  const pre = new Uint8Array(plainBuf);
  const ptr = Module._generate_chaotic_keystream(0.5, 3.9, pre.length);

  const heapu8 = Module.HEAPU8;
  if (!heapu8 || !heapu8.buffer) {
    throw new Error("Module.HEAPU8 chưa sẵn sàng hoặc không hợp lệ.");
  }

  const ks = new Uint8Array(heapu8.buffer, ptr, pre.length);
  const out = new Uint8Array(pre.length);
  for (let i = 0; i < pre.length; i++) out[i] = pre[i] ^ ks[i];

  Module._free_buffer(ptr);
  return out;
}

async function streamAndPlaySingle() {
  try {
    const videoId = 'sample1';
    const key_b64 = await fetchKey(videoId);
    const aesKey = await importKeyFromB64(key_b64);

    const segRes = await fetch(`/segment/${videoId}.enc`);
    if (!segRes.ok) throw new Error(`Tải segment lỗi: ${segRes.status}`);
    const segBuf = await segRes.arrayBuffer();

    const original = await decryptChaotic(segBuf, aesKey);
    const blobUrl = URL.createObjectURL(new Blob([original], { type: 'video/mp4' }));

    const video = document.getElementById('videoPlayer');
    video.src = blobUrl;
    await video.play();
  } catch (err) {
    console.error('Error in streamAndPlaySingle():', err);
  }
}

document.addEventListener('DOMContentLoaded', streamAndPlaySingle);
