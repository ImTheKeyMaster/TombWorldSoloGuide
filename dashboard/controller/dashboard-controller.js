import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_MESSAGE_TYPES, safeParseDashboardJson, isReadOnlyDashboardMessage } from '../shared/dashboard-protocol.js';
import { serializePairingData, decodePairingData } from '../shared/pairing-codec.js';

const STATUS_TEXT = Object.freeze({ idle: 'Not connected', creating: 'Creating link', offer: 'Waiting for dashboard', response: 'Waiting for response', connecting: 'Connecting', connected: 'Dashboard Connected', interrupted: 'Connection Interrupted', failed: 'Connection Interrupted' });
const activeChannels = new Set(); // Broadcast boundary kept collection-based for future multi-viewer support.
const subscribers = new Set(), messageSubscribers = new Set();
const sessionStore = globalThis.sessionStorage;
let peer = null, channel = null, session = null, status = sessionStore?.getItem('tomb-world-dashboard-linked') ? 'interrupted' : 'idle';
let heartbeatTimer = null, disconnectTimer = null, generation = 0, violationCount = 0;
function notify(listener, detail) { try { listener(detail); } catch (error) { console.warn('[Dashboard] Listener failed.', error); } }
function detail() { return { status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null, hasAttempt: status !== 'idle' || Boolean(session) }; }
function update(next) { status = next; subscribers.forEach(listener => notify(listener, detail())); }
function randomNonce() { const bytes = new Uint8Array(16); globalThis.crypto.getRandomValues(bytes); return [...bytes].map(value => value.toString(16).padStart(2, '0')).join(''); }
function waitForIce(connection, token) { if (connection.iceGatheringState === 'complete') return Promise.resolve(); return new Promise((resolve, reject) => { const timer = setTimeout(() => reject(new Error('ICE gathering timed out.')), DASHBOARD_CONFIG.connectionTimeoutMs); const change = () => { if (token !== generation) return reject(new Error('Pairing attempt was superseded.')); if (connection.iceGatheringState === 'complete') { clearTimeout(timer); connection.removeEventListener('icegatheringstatechange', change); resolve(); } }; connection.addEventListener('icegatheringstatechange', change); }); }
async function verificationCode(nonce) { const digest = new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(`tomb-world-dashboard:${nonce}`))); const number = ((digest[0] << 16) | (digest[1] << 8) | digest[2]) % 1000000; return number.toString().padStart(6, '0').replace(/(\d{3})(\d{3})/, '$1 $2'); }
function message(type, values = {}) { return JSON.stringify({ protocolVersion: DASHBOARD_PROTOCOL_VERSION, type, ...values }); }
function sendHeartbeat(dataChannel) { if (dataChannel.readyState === 'open') dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.PING, { sentAt: Date.now() })); }
function stopTimers() { clearInterval(heartbeatTimer); clearTimeout(disconnectTimer); heartbeatTimer = disconnectTimer = null; }
function protocolViolation(dataChannel) { violationCount += 1; if (violationCount >= DASHBOARD_CONFIG.maximumProtocolViolations) dataChannel.close(); }
function bindConnection(connection, dataChannel, token) {
  const current = () => token === generation && connection === peer;
  dataChannel.onopen = () => { if (!current()) return dataChannel.close(); activeChannels.add(dataChannel); update('connecting'); sendHeartbeat(dataChannel); heartbeatTimer = setInterval(() => sendHeartbeat(dataChannel), 5000); };
  dataChannel.onmessage = event => {
    if (!current()) return;
    const data = safeParseDashboardJson(event.data);
    if (!isReadOnlyDashboardMessage(data)) { protocolViolation(dataChannel); return; }
    violationCount = 0;
    if (data.type === DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY) { dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.HELLO)); sessionStore?.setItem('tomb-world-dashboard-linked', '1'); update('connected'); }
    else if (data.type === DASHBOARD_MESSAGE_TYPES.PING) dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.PONG, { sentAt: data.sentAt, receivedAt: Date.now() }));
    else if (data.type === DASHBOARD_MESSAGE_TYPES.DISCONNECT) cleanupDashboardConnection();
    messageSubscribers.forEach(listener => notify(listener, data));
  };
  dataChannel.onclose = () => { activeChannels.delete(dataChannel); stopTimers(); if (current() && status !== 'idle') update('interrupted'); };
  connection.onconnectionstatechange = () => {
    if (!current()) return;
    clearTimeout(disconnectTimer);
    const next = connection.connectionState;
    if (next === 'new' || next === 'connecting') update('connecting');
    else if (next === 'connected') update('connected');
    else if (next === 'disconnected') { update('interrupted'); disconnectTimer = setTimeout(() => { if (current() && connection.connectionState === 'disconnected') update('failed'); }, DASHBOARD_CONFIG.disconnectGraceMs); }
    else if (next === 'failed') { update('failed'); dataChannel.close(); connection.close(); }
    else if (next === 'closed' && status !== 'idle') update('interrupted');
  };
}
export function isWebRtcSupported() { return Boolean(globalThis.RTCPeerConnection && globalThis.crypto?.getRandomValues && globalThis.crypto?.subtle); }
export function subscribeDashboardStatus(listener) { subscribers.add(listener); listener(detail()); return () => subscribers.delete(listener); }
export function getDashboardStatus() { return detail(); }
export function subscribeDashboardMessages(listener) { messageSubscribers.add(listener); return () => messageSubscribers.delete(listener); }
export function sendDashboardSnapshot(serializedMessage) {
  let sent = false;
  activeChannels.forEach(activeChannel => { if (activeChannel.readyState === 'open') { activeChannel.send(serializedMessage); sent = true; } });
  return sent;
}
export async function createDashboardOffer(label = 'Tomb World battle') {
  cleanupDashboardConnection({ preserveAttempt: true });
  if (!isWebRtcSupported()) throw new Error('WebRTC is not supported on this device.');
  const token = generation, now = Date.now(), nonce = randomNonce(); update('creating');
  peer = new RTCPeerConnection({ iceServers: DASHBOARD_CONFIG.iceServers });
  channel = peer.createDataChannel('tomb-world-dashboard', { ordered: true }); bindConnection(peer, channel, token);
  session = { nonce, createdAt: now, expiresAt: now + DASHBOARD_CONFIG.pairingLifetimeMs, verificationCode: await verificationCode(nonce), responseApplied: false };
  await peer.setLocalDescription(await peer.createOffer()); await waitForIce(peer, token);
  if (token !== generation) throw new Error('Pairing attempt was superseded.');
  const payload = { protocolVersion: DASHBOARD_PROTOCOL_VERSION, type: 'offer', nonce, createdAt: now, expiresAt: session.expiresAt, sdpType: 'offer', sdp: peer.localDescription.sdp, label };
  const encodedOffer = await serializePairingData(payload); update('offer');
  return { encodedOffer, expiresAt: session.expiresAt, verificationCode: session.verificationCode };
}
export async function applyDashboardResponse(encoded) {
  if (!peer || !session) throw new Error('Create a dashboard link first.');
  if (session.responseApplied) throw new Error('Dashboard response was already applied.');
  session.responseApplied = true;
  try { const answer = await decodePairingData(encoded, { expectedType: 'answer', expectedNonce: session.nonce, expectedSdpType: 'answer' }); update('connecting'); await peer.setRemoteDescription({ type: answer.sdpType, sdp: answer.sdp }); }
  catch (error) { session.responseApplied = false; throw error; }
}
export function markWaitingForResponse() { if (session) update('response'); }
export function cleanupDashboardConnection({ preserveAttempt = false } = {}) {
  generation += 1; stopTimers(); activeChannels.forEach(activeChannel => activeChannel.close()); activeChannels.clear();
  if (channel) { channel.onopen = channel.onmessage = channel.onclose = null; }
  if (peer) peer.onconnectionstatechange = null;
  channel?.close(); peer?.close(); channel = peer = session = null; violationCount = 0;
  if (!preserveAttempt) sessionStore?.removeItem('tomb-world-dashboard-linked');
  update(preserveAttempt ? 'interrupted' : 'idle');
}
