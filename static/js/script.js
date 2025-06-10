let Module = null;

async function initWasm() {
  if (!Module) {
    if (!window.ChaoticModulePromise) throw new Error("WASM chưa load xong");
    Module = await window.ChaoticModulePromise;
    if (!Module.calledRun && typeof Module.onRuntimeInitialized === 'function') {
      await new Promise(resolve => {
        const orig = Module.onRuntimeInitialized;
        Module.onRuntimeInitialized = () => { orig(); resolve(); };
      });
    }
  }
  return Module;
}

// 1) Sinh + đăng ký public RSA key
async function registerPubKey(videoId) {
  const t0 = performance.now();
  const kp = await crypto.subtle.generateKey(
    { name: 'RSA-OAEP', modulusLength: 2048,
      publicExponent: new Uint8Array([1,0,1]), hash: 'SHA-256' },
    true, ['encrypt','decrypt']
  );
  window.clientKeyPair = kp;

  const spki = await crypto.subtle.exportKey('spki', kp.publicKey);
  const b64 = btoa(String.fromCharCode(...new Uint8Array(spki)));
  const pem = `-----BEGIN PUBLIC KEY-----\n${b64}\n-----END PUBLIC KEY-----`;

  await fetch(`/register_pubkey/${videoId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: new TextEncoder().encode(pem)
  });
  const t1 = performance.now();
  console.log(`[Benchmark] RSA keygen + register: ${(t1 - t0).toFixed(2)} ms`);
}

// 2) Fetch + RSA-decrypt AES key + importKey
async function fetchAndDecryptKey(videoId) {
  await registerPubKey(videoId);
  const t2 = performance.now();
  const res = await fetch(`/get_key_rsa/${videoId}?token=abc123`);
  const { key_rsa_b64 } = await res.json();
  const cipher = Uint8Array.from(atob(key_rsa_b64), c=>c.charCodeAt(0));

  const raw = await crypto.subtle.decrypt(
    { name: 'RSA-OAEP' },
    window.clientKeyPair.privateKey,
    cipher
  );
  const aesKey = await crypto.subtle.importKey(
    'raw', new Uint8Array(raw),
    { name: 'AES-GCM' }, false, ['decrypt']
  );
  const t3 = performance.now();
  console.log(`[Benchmark] Fetch+RSA-decrypt+import AES key: ${(t3 - t2).toFixed(2)} ms`);
  return aesKey;
}

// 3) DECRYPT AES-GCM + Chaotic XOR (trong chung)
async function decryptChaotic(segmentBuffer, aesKey) {
  const wasm = await initWasm();
  const view = new Uint8Array(segmentBuffer);
  const iv = view.subarray(0,12);
  const tag = view.subarray(12,28);
  const cipher = view.subarray(28);
  const ctAndTag = new Uint8Array(cipher.length + tag.length);
  ctAndTag.set(cipher, 0);
  ctAndTag.set(tag, cipher.length);

  // AES-GCM decrypt benchmark
  const t0 = performance.now();
  const plainBuf = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv, tagLength: 128 },
    aesKey,
    ctAndTag
  );
  const t1 = performance.now();
  console.log(`[Benchmark] AES-GCM decrypt: ${(t1 - t0).toFixed(2)} ms`);

  const pre = new Uint8Array(plainBuf);

  // Chaotic XOR benchmark
  const t2 = performance.now();
  const ptr = Module._generate_chaotic_keystream(0.5, 3.9, pre.length);
  const ks  = new Uint8Array(Module.HEAPU8.buffer, ptr, pre.length);
  const out = new Uint8Array(pre.length);
  for (let i = 0; i < pre.length; i++) out[i] = pre[i] ^ ks[i];
  Module._free_buffer(ptr);
  const t3 = performance.now();
  console.log(`[Benchmark] Chaotic XOR: ${(t3 - t2).toFixed(2)} ms`);

  return out;
}

// 4) Toàn bộ từ fetch key → play video
async function streamAndPlaySingle() {
  const start = performance.now();
  try {
    const videoId = 'sample1';
    const aesKey = await fetchAndDecryptKey(videoId);

    const t4 = performance.now();
    const segRes = await fetch(`/segment/${videoId}.enc`);
    const buf = await segRes.arrayBuffer();
    console.log(`[Benchmark] Fetch segment: ${(performance.now() - t4).toFixed(2)} ms`);

    const decryptStart = performance.now();
    const orig = await decryptChaotic(buf, aesKey);
    console.log(`[Benchmark] Total decrypt pipeline: ${(performance.now() - decryptStart).toFixed(2)} ms`);

    const blobUrl = URL.createObjectURL(new Blob([orig], { type: 'video/mp4' }));
    const vid = document.getElementById('videoPlayer');
    vid.src = blobUrl;
    await vid.play();

    console.log(`[Benchmark] End-to-end from start to play(): ${(performance.now() - start).toFixed(2)} ms`);
  } catch (e) {
    console.error('Error in streamAndPlaySingle():', e);
  }
}

document.addEventListener('DOMContentLoaded', streamAndPlaySingle);
