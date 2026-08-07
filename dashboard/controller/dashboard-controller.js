import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_MESSAGE_TYPES, safeParseDashboardJson, validateDashboardMessage } from '../shared/dashboard-protocol.js';
import { serializePairingData, decodePairingData } from '../shared/pairing-codec.js';

const STATUS_TEXT = Object.freeze({ idle: 'Not connected', creating: 'Creating link', offer: 'Waiting for dashboard', response: 'Waiting for response', connecting: 'Connecting', connected: 'Connected', interrupted: 'Connection interrupted' });
let peer = null, channel = null, session = null, status = 'idle';
const subscribers = new Set();
function update(next) { status = next; subscribers.forEach(listener => listener({ status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null })); }
function randomNonce() { const bytes = new Uint8Array(16); crypto.getRandomValues(bytes); return [...bytes].map(value => value.toString(16).padStart(2, '0')).join(''); }
function waitForIce(connection) { if (connection.iceGatheringState === 'complete') return Promise.resolve(); return new Promise((resolve, reject) => { const timer = setTimeout(() => reject(new Error('ICE gathering timed out.')), DASHBOARD_CONFIG.connectionTimeoutMs); const change = () => { if (connection.iceGatheringState === 'complete') { clearTimeout(timer); connection.removeEventListener('icegatheringstatechange', change); resolve(); } }; connection.addEventListener('icegatheringstatechange', change); }); }
async function verificationCode(nonce) { const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`tomb-world-dashboard:${nonce}`))); const number = ((digest[0] << 16) | (digest[1] << 8) | digest[2]) % 1000000; return number.toString().padStart(6, '0').replace(/(\d{3})(\d{3})/, '$1 $2'); }
function message(type) { return JSON.stringify({ protocolVersion: DASHBOARD_PROTOCOL_VERSION, type }); }
function bindConnection(connection, dataChannel) {
  dataChannel.onopen = () => update('connecting');
  dataChannel.onmessage = event => { const data = safeParseDashboardJson(event.data), validation = validateDashboardMessage(data); if (!validation.valid) return; if (data.type === DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY) dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.HELLO)); else if (data.type === 'hello-ack') update('connected'); };
  dataChannel.onclose = () => { if (status !== 'idle') update('interrupted'); };
  connection.onconnectionstatechange = () => { if (['failed', 'disconnected'].includes(connection.connectionState)) update('interrupted'); };
}
export function isWebRtcSupported() { return Boolean(globalThis.RTCPeerConnection && crypto?.getRandomValues && crypto?.subtle); }
export function subscribeDashboardStatus(listener) { subscribers.add(listener); listener({ status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null }); return () => subscribers.delete(listener); }
export function getDashboardStatus() { return { status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null, hasAttempt: Boolean(session) }; }
export async function createDashboardOffer(label = 'Tomb World battle') {
  cleanupDashboardConnection();
  if (!isWebRtcSupported()) throw new Error('WebRTC is not supported on this device.');
  update('creating');
  const now = Date.now(), nonce = randomNonce();
  peer = new RTCPeerConnection({ iceServers: DASHBOARD_CONFIG.iceServers });
  channel = peer.createDataChannel('tomb-world-dashboard', { ordered: true }); bindConnection(peer, channel);
  session = { nonce, createdAt: now, expiresAt: now + DASHBOARD_CONFIG.pairingLifetimeMs, verificationCode: await verificationCode(nonce) };
  await peer.setLocalDescription(await peer.createOffer()); await waitForIce(peer);
  const payload = { protocolVersion: DASHBOARD_PROTOCOL_VERSION, type: 'offer', nonce, createdAt: now, expiresAt: session.expiresAt, sdpType: 'offer', sdp: peer.localDescription.sdp, label };
  const encodedOffer = await serializePairingData(payload); update('offer');
  return { encodedOffer, expiresAt: session.expiresAt, verificationCode: session.verificationCode };
}
export async function applyDashboardResponse(encoded) {
  if (!peer || !session) throw new Error('Create a dashboard link first.');
  const answer = await decodePairingData(encoded, { expectedType: 'answer', expectedNonce: session.nonce, expectedSdpType: 'answer' });
  update('connecting'); await peer.setRemoteDescription({ type: answer.sdpType, sdp: answer.sdp });
}
export function markWaitingForResponse() { if (session) update('response'); }
export function cleanupDashboardConnection() { channel?.close(); peer?.close(); channel = null; peer = null; session = null; update('idle'); }
