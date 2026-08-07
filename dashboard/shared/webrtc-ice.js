const CANDIDATE_FIELDS = ['candidate', 'sdpMid', 'sdpMLineIndex', 'usernameFragment'];

function normalizeCandidate(value) {
  const source = typeof value?.toJSON === 'function' ? value.toJSON() : value;
  if (!source || typeof source.candidate !== 'string' || !source.candidate) return null;
  const candidate = {};
  CANDIDATE_FIELDS.forEach(field => { if (source[field] !== undefined && source[field] !== null) candidate[field] = source[field]; });
  return candidate;
}
function candidateKey(candidate) { return `${candidate.candidate}|${candidate.sdpMid ?? ''}|${candidate.sdpMLineIndex ?? ''}|${candidate.usernameFragment ?? ''}`; }
function candidateType(candidate) { return /(?:^|\s)typ\s+(host|srflx|relay)(?:\s|$)/.exec(candidate.candidate)?.[1] || null; }
function safeServer(url) {
  if (typeof url !== 'string') return null;
  const match = /^(?:stun|turns?):([^/:?#]+)/i.exec(url);
  return match?.[1] || null;
}
function safeErrorText(value) {
  return String(value)
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[address]')
    .replace(/(?:^|\s|\[)[0-9a-f]{0,4}(?::[0-9a-f]{0,4}){2,}(?:%[\w.-]+)?(?=$|\s|\])/gi, ' [address]')
    .replace(/\b(?:candidate|ufrag|pwd)\s*[:=]\s*\S+/gi, '$1=[redacted]')
    .slice(0, 160);
}

export class NoIceCandidatesError extends Error {
  constructor(diagnostics) { super('This device could not establish a WebRTC network route.'); this.name = 'NoIceCandidatesError'; this.diagnostics = diagnostics; }
}

export function describeBrowserEnvironment(scope = globalThis) {
  const userAgent = scope.navigator?.userAgent || '';
  const standalone = scope.matchMedia?.('(display-mode: standalone)').matches || scope.navigator?.standalone === true;
  if (/iPhone/i.test(userAgent)) return standalone ? 'iPhone PWA' : 'iPhone Safari';
  if (/iPad/i.test(userAgent) || (/Macintosh/i.test(userAgent) && Number(scope.navigator?.maxTouchPoints) > 1)) return standalone ? 'iPad PWA' : 'iPad Safari';
  if (/Chrome|CriOS/i.test(userAgent) && !/Edg|OPR/i.test(userAgent)) return 'Chrome';
  if (/Safari/i.test(userAgent) && !/Chrome|Chromium|CriOS|Android/i.test(userAgent)) return 'Desktop Safari';
  return 'WebRTC browser';
}

export function collectIceCandidates(peer, { quietPeriodMs = 1250, maximumWaitMs = 8000, signal, onProgress, startGathering } = {}) {
  return new Promise((resolve, reject) => {
    const candidates = [], keys = new Set(), types = new Set(), stunErrors = [];
    let quietTimer = null, maximumTimer = null, settled = false;
    const diagnostics = () => ({ gatheredCandidateCount: candidates.length, candidateTypes: [...types], iceGatheringState: peer.iceGatheringState, stunErrors: stunErrors.map(item => ({ ...item })) });
    const cleanup = () => {
      clearTimeout(quietTimer); clearTimeout(maximumTimer);
      peer.removeEventListener('icecandidate', onCandidate);
      peer.removeEventListener('icecandidateerror', onCandidateError);
      peer.removeEventListener('icegatheringstatechange', onStateChange);
      signal?.removeEventListener('abort', onAbort);
    };
    const finish = completed => { if (settled) return; settled = true; cleanup(); const current = diagnostics(); if (!candidates.length) reject(new NoIceCandidatesError(current)); else resolve({ candidates, completed, gatheringState: peer.iceGatheringState, diagnostics: current }); };
    const scheduleQuietFinish = () => { clearTimeout(quietTimer); quietTimer = setTimeout(() => finish(false), quietPeriodMs); };
    function onCandidate(event) {
      if (!event.candidate) { finish(true); return; }
      const candidate = normalizeCandidate(event.candidate); if (!candidate) return;
      const key = candidateKey(candidate); if (keys.has(key)) return;
      keys.add(key); candidates.push(candidate); const type = candidateType(candidate); if (type) types.add(type);
      onProgress?.({ count: candidates.length, diagnostics: diagnostics() }); scheduleQuietFinish();
    }
    function onCandidateError(event) {
      const diagnostic = {};
      if (Number.isSafeInteger(event.errorCode)) diagnostic.errorCode = event.errorCode;
      if (typeof event.errorText === 'string' && event.errorText) diagnostic.errorText = safeErrorText(event.errorText);
      const server = safeServer(event.url); if (server) diagnostic.server = server;
      stunErrors.push(diagnostic);
    }
    function onStateChange() { if (peer.iceGatheringState === 'complete') finish(true); }
    function onAbort() { if (settled) return; settled = true; cleanup(); reject(new DOMException('Pairing attempt was superseded.', 'AbortError')); }
    peer.addEventListener('icecandidate', onCandidate);
    peer.addEventListener('icecandidateerror', onCandidateError);
    peer.addEventListener('icegatheringstatechange', onStateChange);
    if (signal?.aborted) { onAbort(); return; }
    signal?.addEventListener('abort', onAbort, { once: true });
    maximumTimer = setTimeout(() => finish(false), maximumWaitMs);
    Promise.resolve().then(() => settled ? undefined : startGathering?.()).then(() => {
      if (peer.iceGatheringState === 'complete') finish(true);
    }).catch(error => { if (!settled) { settled = true; cleanup(); reject(error); } });
  });
}

export async function addRemoteIceCandidates(peer, candidates = [], remoteSdp = '') {
  const embedded = new Set(String(remoteSdp).split(/\r?\n/).filter(line => line.startsWith('a=candidate:')).map(line => line.slice(2).trim()));
  const added = new Set();
  for (const source of candidates) {
    const candidate = normalizeCandidate(source); if (!candidate) continue;
    const key = candidateKey(candidate); if (added.has(key) || embedded.has(candidate.candidate.trim())) continue;
    added.add(key);
    try { await peer.addIceCandidate(candidate); } catch (error) {
      if (error?.name !== 'OperationError' && error?.name !== 'InvalidStateError') throw error;
    }
  }
}
