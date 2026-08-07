export const DASHBOARD_FEATURE_ENABLED = true;

export const DASHBOARD_CONFIG = Object.freeze({
  featureEnabled: DASHBOARD_FEATURE_ENABLED,
  protocolVersion: 1,
  pagePath: 'dashboard/index.html',
  pairingLifetimeMs: 10 * 60 * 1000,
  connectionTimeoutMs: 8000,
  iceCandidateQuietPeriodMs: 1250,
  disconnectGraceMs: 8000,
  maximumProtocolViolations: 3,
  onlineProbeTimeoutMs: 3000,
  maximumPayloadSize: 65536,
  maximumEncodedPayloadSize: 100000,
  // STUN is used only for WebRTC route discovery; no game state is sent to these servers.
  iceServers: Object.freeze([{ urls: Object.freeze([
    'stun:stun.cloudflare.com:3478',
    'stun:stun.cloudflare.com:53'
  ]) }, { urls: Object.freeze(['stun:stun.l.google.com:19302']) }]),
  onlineProbePath: 'dashboard/online-check.txt'
});
