import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_MESSAGE_TYPES, safeParseDashboardJson, isReadOnlyDashboardMessage } from '../shared/dashboard-protocol.js';
import { serializePairingData, decodePairingData } from '../shared/pairing-codec.js';

const STATUS_TEXT = Object.freeze({ idle: 'Not connected', creating: 'Creating link', offer: 'Waiting for dashboard', response: 'Waiting for response', connecting: 'Connecting', connected: 'Connected', interrupted: 'Connection interrupted' });
let peer = null, channel = null, session = null, status = 'idle';
let heartbeatTimer = null;
const subscribers = new Set();
const messageSubscribers = new Set();
function notify(listener, detail) { try { listener(detail); } catch (error) { console.warn('[Dashboard] Listener failed.', error); } }
function update(next) { status = next; const detail = { status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null }; subscribers.forEach(listener => notify(listener, detail)); }
function randomNonce() { const bytes = new Uint8Array(16); globalThis.crypto.getRandomValues(bytes); return [...bytes].map(value => value.toString(16).padStart(2, '0')).join(''); }
function waitForIce(connection) { if (connection.iceGatheringState === 'complete') return Promise.resolve(); return new Promise((resolve, reject) => { const timer = setTimeout(() => reject(new Error('ICE gathering timed out.')), DASHBOARD_CONFIG.connectionTimeoutMs); const change = () => { if (connection.iceGatheringState === 'complete') { clearTimeout(timer); connection.removeEventListener('icegatheringstatechange', change); resolve(); } }; connection.addEventListener('icegatheringstatechange', change); }); }
async function verificationCode(nonce) { const digest = new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(`tomb-world-dashboard:${nonce}`))); const number = ((digest[0] << 16) | (digest[1] << 8) | digest[2]) % 1000000; return number.toString().padStart(6, '0').replace(/(\d{3})(\d{3})/, '$1 $2'); }
function message(type, detail = {}) { return JSON.stringify({ protocolVersion: DASHBOARD_PROTOCOL_VERSION, type, ...detail }); }
function sendHeartbeat(dataChannel) {
  if (dataChannel.readyState === 'open') dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.PING, { sentAt: Date.now() }));
}
function bindConnection(connection, dataChannel) {
  dataChannel.onopen = () => { update('connecting'); sendHeartbeat(dataChannel); heartbeatTimer = setInterval(() => sendHeartbeat(dataChannel), 5000); };
  dataChannel.onmessage = event => { const data = safeParseDashboardJson(event.data); if (!isReadOnlyDashboardMessage(data)) return; if (data.type === DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY) { dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.HELLO)); update('connected'); } else if (data.type === DASHBOARD_MESSAGE_TYPES.PING) dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.PONG, { sentAt: data.sentAt, receivedAt: Date.now() })); else if (data.type === DASHBOARD_MESSAGE_TYPES.DISCONNECT) cleanupDashboardConnection(); messageSubscribers.forEach(listener => notify(listener, data)); };
  dataChannel.onclose = () => { if (status !== 'idle') update('interrupted'); };
  connection.onconnectionstatechange = () => { if (['failed', 'disconnected'].includes(connection.connectionState)) update('interrupted'); };
}
export function isWebRtcSupported() { return Boolean(globalThis.RTCPeerConnection && globalThis.crypto?.getRandomValues && globalThis.crypto?.subtle); }
export function subscribeDashboardStatus(listener) { subscribers.add(listener); listener({ status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null }); return () => subscribers.delete(listener); }
export function getDashboardStatus() { return { status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null, hasAttempt: Boolean(session) }; }
export function subscribeDashboardMessages(listener) { messageSubscribers.add(listener); return () => messageSubscribers.delete(listener); }
export function sendDashboardSnapshot(serializedMessage) {
  if (status !== 'connected' || channel?.readyState !== 'open') return false;
  channel.send(serializedMessage);
  return true;
}
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
export function cleanupDashboardConnection() { clearInterval(heartbeatTimer); heartbeatTimer = null; channel?.close(); peer?.close(); channel = null; peer = null; session = null; update('idle'); }
