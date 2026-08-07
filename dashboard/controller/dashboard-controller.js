import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_MESSAGE_TYPES, safeParseDashboardJson, isReadOnlyDashboardMessage } from '../shared/dashboard-protocol.js';
import { serializePairingData, decodePairingData } from '../shared/pairing-codec.js';
import { collectIceCandidates, addRemoteIceCandidates, describeBrowserEnvironment } from '../shared/webrtc-ice.js';

const STATUS_TEXT = Object.freeze({ idle: 'Not connected', creating: 'Creating link', offer: 'Waiting for dashboard', response: 'Waiting for response', connecting: 'Connecting', connected: 'Dashboard Connected', interrupted: 'Connection Interrupted', failed: 'Connection Interrupted' });
const activeChannels = new Set(); // Broadcast boundary kept collection-based for future multi-viewer support.
const subscribers = new Set(), messageSubscribers = new Set();
const sessionStore = globalThis.sessionStorage;
function readLinkedSession() { try { return sessionStore?.getItem('tomb-world-dashboard-linked') === '1'; } catch { return false; } }
function writeLinkedSession(linked) { try { if (linked) sessionStore?.setItem('tomb-world-dashboard-linked', '1'); else sessionStore?.removeItem('tomb-world-dashboard-linked'); } catch { /* Connection state remains authoritative. */ } }
let peer = null, channel = null, session = null, status = readLinkedSession() ? 'interrupted' : 'idle';
let heartbeatTimer = null, disconnectTimer = null, generation = 0, violationCount = 0, iceAbortController = null, pairingDiagnostics = null;
function notify(listener, detail) { try { listener(detail); } catch (error) { console.warn('[Dashboard] Listener failed.', error); } }
function detail() { return { status, text: STATUS_TEXT[status], verificationCode: session?.verificationCode || null, hasAttempt: status !== 'idle' || Boolean(session), diagnostics: pairingDiagnostics }; }
function update(next) { status = next; subscribers.forEach(listener => notify(listener, detail())); }
function randomNonce() { const bytes = new Uint8Array(16); globalThis.crypto.getRandomValues(bytes); return [...bytes].map(value => value.toString(16).padStart(2, '0')).join(''); }
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
    if (data.type === DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY) { dataChannel.send(message(DASHBOARD_MESSAGE_TYPES.HELLO)); writeLinkedSession(true); update('connected'); }
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
    else if (next === 'disconnected') { update('interrupted'); disconnectTimer = setTimeout(() => { if (current() && connection.connectionState === 'disconnected') cleanupDashboardConnection({ preserveAttempt: true, nextStatus: 'failed' }); }, DASHBOARD_CONFIG.disconnectGraceMs); }
    else if (next === 'failed') cleanupDashboardConnection({ preserveAttempt: true, nextStatus: 'failed' });
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
export async function createDashboardOffer(label = 'Tomb World battle', { onProgress } = {}) {
  cleanupDashboardConnection({ preserveAttempt: true });
  if (!isWebRtcSupported()) throw new Error('WebRTC is not supported on this device.');
  const token = generation, now = Date.now(), nonce = randomNonce(); update('creating');
  onProgress?.('Creating WebRTC session...');
  peer = new RTCPeerConnection({ iceServers: DASHBOARD_CONFIG.iceServers });
  channel = peer.createDataChannel('tomb-world-dashboard', { ordered: true }); bindConnection(peer, channel, token);
  session = { nonce, createdAt: now, expiresAt: now + DASHBOARD_CONFIG.pairingLifetimeMs, verificationCode: await verificationCode(nonce), responseApplied: false };
  await peer.setLocalDescription(await peer.createOffer());
  onProgress?.('Discovering network route...');
  iceAbortController = new AbortController();
  let gathered;
  try { gathered = await collectIceCandidates(peer, { maximumWaitMs: DASHBOARD_CONFIG.connectionTimeoutMs, quietPeriodMs: DASHBOARD_CONFIG.iceCandidateQuietPeriodMs, signal: iceAbortController.signal, onProgress: progress => onProgress?.(`${progress.count} network route${progress.count === 1 ? '' : 's'} found...`) }); }
  catch (error) { pairingDiagnostics = { browser: describeBrowserEnvironment(), ...(error.diagnostics || {}) }; error.diagnostics = pairingDiagnostics; throw error; }
  pairingDiagnostics = { browser: describeBrowserEnvironment(), ...gathered.diagnostics };
  if (token !== generation) throw new Error('Pairing attempt was superseded.');
  onProgress?.('Generating pairing code...');
  const payload = { protocolVersion: DASHBOARD_PROTOCOL_VERSION, type: 'offer', nonce, createdAt: now, expiresAt: session.expiresAt, sdpType: 'offer', sdp: peer.localDescription.sdp, candidates: gathered.candidates, label };
  const encodedOffer = await serializePairingData(payload); update('offer');
  return { encodedOffer, expiresAt: session.expiresAt, verificationCode: session.verificationCode };
}
export async function applyDashboardResponse(encoded) {
  if (!peer || !session) throw new Error('Create a dashboard link first.');
  if (session.responseApplied) throw new Error('Dashboard response was already applied.');
  session.responseApplied = true;
  try { const answer = await decodePairingData(encoded, { expectedType: 'answer', expectedNonce: session.nonce, expectedSdpType: 'answer' }); update('connecting'); await peer.setRemoteDescription({ type: answer.sdpType, sdp: answer.sdp }); await addRemoteIceCandidates(peer, answer.candidates, answer.sdp); }
  catch (error) { session.responseApplied = false; throw error; }
}
export function markWaitingForResponse() { if (session) update('response'); }
export function cleanupDashboardConnection({ preserveAttempt = false, nextStatus = preserveAttempt ? 'interrupted' : 'idle' } = {}) {
  generation += 1; iceAbortController?.abort(); iceAbortController = null; pairingDiagnostics = null; stopTimers(); activeChannels.forEach(activeChannel => activeChannel.close()); activeChannels.clear();
  if (channel) { channel.onopen = channel.onmessage = channel.onclose = null; }
  if (peer) peer.onconnectionstatechange = null;
  channel?.close(); peer?.close(); channel = peer = session = null; violationCount = 0;
  if (!preserveAttempt) writeLinkedSession(false);
  update(nextStatus);
}
