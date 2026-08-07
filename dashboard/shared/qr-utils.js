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
export async function scanQrCode({ onResult, onStop, videoHost }) {
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
  const video = document.createElement('video'); video.setAttribute('playsinline', ''); video.muted = true; videoHost.replaceChildren(video); video.srcObject = stream; await video.play();
  let stopped = false, detector;
  if ('BarcodeDetector' in globalThis) detector = new BarcodeDetector({ formats: ['qr_code'] });
  const canvas = document.createElement('canvas'), context = canvas.getContext('2d', { willReadFrequently: true });
  const stop = () => { if (stopped) return; stopped = true; stream.getTracks().forEach(track => track.stop()); video.srcObject = null; video.remove(); onStop?.(); };
  const frame = async () => {
    if (stopped) return;
    try {
      let value = null;
      if (detector) value = (await detector.detect(video))[0]?.rawValue;
      else {
        await ensureFallbackDecoder(); canvas.width = video.videoWidth; canvas.height = video.videoHeight; context.drawImage(video, 0, 0);
        value = globalThis.TombWorldQrDecoder?.decode(context.getImageData(0, 0, canvas.width, canvas.height)) || null;
      }
      if (value) { stop(); onResult(value); return; }
    } catch { /* A transient frame failure should not end scanning. */ }
    requestAnimationFrame(frame);
  };
  frame(); return stop;
}
let decoderPromise;
async function ensureFallbackDecoder() {
  if (!globalThis.TombWorldQrDecoder) decoderPromise ||= loadScript(new URL('../vendor/qr-decoder.js', import.meta.url));
  return decoderPromise;
}
