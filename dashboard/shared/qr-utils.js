let encoderPromise;
function loadScript(path) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script'); script.src = path; script.onload = resolve; script.onerror = reject; document.head.append(script);
  });
}
async function encoder() {
  if (!globalThis.TombWorldQRCode) encoderPromise ||= loadScript(new URL('../vendor/qrcode-generator.js', import.meta.url));
  await encoderPromise;
  return globalThis.TombWorldQRCode;
}
export async function renderQrCode(container, text, label) {
  const QRCode = await encoder();
  const qr = new QRCode(-1, 1); // error correction level L
  qr.addData(text); qr.make();
  const count = qr.getModuleCount(), quiet = 4, size = count + quiet * 2;
  let path = '';
  for (let row = 0; row < count; row++) for (let column = 0; column < count; column++) if (qr.isDark(row, column)) path += `M${column + quiet} ${row + quiet}h1v1h-1z`;
  container.innerHTML = `<svg class="pairing-qr" viewBox="0 0 ${size} ${size}" role="img" aria-label="${label}"><rect width="100%" height="100%" fill="#fff"/><path d="${path}" fill="#000"/></svg><p class="qr-alternative">${label}</p>`;
}

let decoderPromise;
async function ensureFallbackDecoder() {
  if (!globalThis.jsQR) await (decoderPromise ||= loadScript(new URL('../vendor/jsQR.js', import.meta.url)));
  if (!globalThis.TombWorldQrDecoder) await loadScript(new URL('../vendor/qr-decoder.js', import.meta.url));
  if (!globalThis.TombWorldQrDecoder?.supported) throw new Error('Local QR scanning is unavailable. Paste the response instead.');
  return globalThis.TombWorldQrDecoder;
}

async function nativeQrDetector() {
  if (typeof globalThis.BarcodeDetector !== 'function') return null;
  try {
    const formats = typeof BarcodeDetector.getSupportedFormats === 'function' ? await BarcodeDetector.getSupportedFormats() : [];
    if (!formats.includes('qr_code')) return null;
    return new BarcodeDetector({ formats: ['qr_code'] });
  } catch { return null; }
}

function imageDataFrom(source, canvas, context) {
  canvas.width = source.videoWidth || source.naturalWidth || source.width;
  canvas.height = source.videoHeight || source.naturalHeight || source.height;
  if (!canvas.width || !canvas.height) return null;
  context.drawImage(source, 0, 0, canvas.width, canvas.height);
  return context.getImageData(0, 0, canvas.width, canvas.height);
}

export async function scanQrCode({ onResult, onStop, onCleanupReady, videoHost }) {
  if (!navigator.mediaDevices?.getUserMedia) {
    const error = new Error('Live QR scanning is not supported by this browser.'); error.name = 'NotSupportedError'; throw error;
  }
  let stream = null, video = null, stopped = false, timer = null, frameRequest = null;
  const stop = () => {
    if (stopped) return;
    stopped = true; clearTimeout(timer); if (frameRequest !== null) cancelAnimationFrame(frameRequest);
    stream?.getTracks().forEach(track => track.stop()); if (video) { video.pause(); video.srcObject = null; video.remove(); } onStop?.();
  };
  onCleanupReady?.(stop);
  // Keep this first awaited operation in the click path so iOS retains the user activation.
  stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
  if (stopped) { stream.getTracks().forEach(track => track.stop()); return stop; }
  video = document.createElement('video');
  video.setAttribute('playsinline', ''); video.setAttribute('autoplay', ''); video.setAttribute('muted', '');
  video.playsInline = true; video.autoplay = true; video.muted = true; video.srcObject = stream;
  videoHost.replaceChildren(video);
  let detectorFailures = 0;
  const canvas = document.createElement('canvas'), context = canvas.getContext('2d', { willReadFrequently: true });
  try { await video.play(); } catch (error) { stop(); throw error; }
  let detector, fallback;
  try { detector = await nativeQrDetector(); fallback = detector ? null : await ensureFallbackDecoder(); }
  catch (error) { stop(); throw error; }
  const decode = async () => {
    if (stopped) return;
    if (!video.videoWidth || !video.videoHeight) { frameRequest = requestAnimationFrame(decode); return; }
    let value = null;
    if (detector) {
      try { value = (await detector.detect(video))[0]?.rawValue || null; detectorFailures = 0; }
      catch {
        if (++detectorFailures >= 3) {
          detector = null;
          try { fallback = await ensureFallbackDecoder(); } catch { stop(); return; }
        }
      }
    } else {
      const imageData = imageDataFrom(video, canvas, context);
      if (imageData) value = fallback.decode(imageData);
    }
    if (value) {
      try { if (await onResult(value)) { stop(); return; } } catch { /* Invalid pairing payloads keep the scanner active. */ }
    }
    timer = setTimeout(decode, 80);
  };
  decode();
  return stop;
}

export async function scanQrPhoto({ onResult, onCleanupReady }) {
  const input = document.createElement('input'); input.type = 'file'; input.accept = 'image/*'; input.capture = 'environment'; input.hidden = true;
  document.body.append(input);
  let resolveSelection, cleaned = false;
  const cleanup = () => { if (cleaned) return; cleaned = true; input.remove(); resolveSelection?.(null); };
  onCleanupReady?.(cleanup);
  try {
    const file = await new Promise(resolve => { resolveSelection = resolve; input.onchange = () => resolve(input.files?.[0] || null); input.click(); });
    if (!file) return false;
    const decoder = await ensureFallbackDecoder();
    const image = new Image(), url = URL.createObjectURL(file);
    try {
      await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject; image.src = url; });
      const canvas = document.createElement('canvas'), context = canvas.getContext('2d', { willReadFrequently: true });
      const value = decoder.decode(imageDataFrom(image, canvas, context));
      return value ? Boolean(await onResult(value)) : false;
    } finally { URL.revokeObjectURL(url); image.src = ''; }
  } finally { cleanup(); }
}
