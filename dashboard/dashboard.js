import { DASHBOARD_CONFIG } from './shared/dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_MESSAGE_TYPES, DASHBOARD_SNAPSHOT_SCHEMA_VERSION, safeParseDashboardJson, validateDashboardMessage, validateDashboardSnapshot } from './shared/dashboard-protocol.js';
import { readPairingFragment, clearPairingFragment, decodePairingData, serializePairingData } from './shared/pairing-codec.js';
import { renderQrCode } from './shared/qr-utils.js';
import { detectDashboardChanges, activityKey } from './change-detector.js';
import { cogitatorLinesFor } from './data/cogitator-templates.js';
import { addLatencySample, averageLatency, linkState } from './link-telemetry.js';

const shell = document.querySelector('.dashboard-shell');
const status = document.querySelector('[data-dashboard-status]');
const pairing = document.querySelector('[data-dashboard-pairing]');
const responseOutput = document.querySelector('[data-response-output]');
const verification = document.querySelector('[data-verification]');
let currentRevision = 0;
let connectedAt = null;
let previousSnapshot = null;
let heartbeatAt = null;
let latencySamples = [];
let heartbeatTimer = null;
let currentLinkState = 'LINK INTERRUPTED';
const cogitatorFeed = [];

function setStatus(value, state = shell.dataset.dashboardState) { status.textContent = value; shell.dataset.dashboardState = state; }
function setText(selector, value, fallback = '—') { document.querySelector(selector).textContent = value ?? fallback; }
function displayNumber(value) { return value ?? '—'; }
function formatDuration(seconds) { const safe = Math.max(0, Number(seconds) || 0); return [Math.floor(safe / 3600), Math.floor(safe / 60) % 60, safe % 60].map(value => String(value).padStart(2, '0')).join(':'); }
function replaceWithEmpty(container, message, tag = 'li') { container.replaceChildren(); const item = document.createElement(tag); item.className = 'empty-state'; item.textContent = message; container.append(item); }
function addTextElement(parent, tag, value, className) { const element = document.createElement(tag); if (className) element.className = className; element.textContent = value; parent.append(element); return element; }
function message(type, detail = {}) { return JSON.stringify({ protocolVersion: DASHBOARD_PROTOCOL_VERSION, type, ...detail }); }
function panelFor(name) { return document.querySelector(name === 'status' ? '.status-strip' : `.${name}-panel`); }
function reactToChanges(changes) {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  new Set(changes.map(change => change.panel)).forEach(name => {
    const panel = panelFor(name); if (!panel) return;
    panel.querySelector('.change-marker')?.remove();
    const marker = addTextElement(panel, 'span', 'UPDATED', 'change-marker'); marker.setAttribute('aria-hidden', 'true');
    panel.classList.remove('data-changed'); if (!reducedMotion) void panel.offsetWidth; panel.classList.add('data-changed');
  });
  if (!reducedMotion) changes.forEach(change => {
    const selector = { turningPoint: '[data-turning-point]', threat: '[data-threat-level]', grade: '[data-grade]', mission: '[data-progress-label]', wounds: '[data-wounds]', playerReadiness: '[data-player-ready]', npoReadiness: '[data-npo-ready]', battleComplete: '[data-result-value]' }[change.type];
    const value = selector && document.querySelector(selector); if (value) { value.classList.remove('value-changed'); void value.offsetWidth; value.classList.add('value-changed'); }
  });
}
function addCogitatorChanges(changes) {
  changes.flatMap(cogitatorLinesFor).forEach(text => {
    const key = `${currentRevision}:${text}`;
    if (cogitatorFeed.some(entry => entry.key === key)) return;
    cogitatorFeed.unshift({ key, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), text });
  });
  cogitatorFeed.splice(10);
}

function renderMission(mission) {
  setText('[data-mission-name]', mission.name ? `${mission.number ? `Mission ${mission.number} // ` : ''}${mission.name}` : 'Mission unavailable');
  setText('[data-mission-summary]', mission.summary, 'No mission summary received.');
  const progress = document.querySelector('[data-objective-progress]');
  const hasProgress = mission.progress !== null && mission.target !== null && mission.target > 0;
  progress.hidden = !hasProgress;
  if (hasProgress) { setText('[data-progress-label]', `${mission.progress} / ${mission.target}`); const bar = document.querySelector('[data-progress-bar]'); bar.max = mission.target; bar.value = Math.min(mission.progress, mission.target); bar.textContent = `${mission.progress} of ${mission.target}`; }
  const objectives = document.querySelector('[data-objectives]');
  if (!mission.objectives.length) return replaceWithEmpty(objectives, 'No objective data received');
  objectives.replaceChildren();
  mission.objectives.forEach(objective => { const complete = objective.target !== null && objective.progress !== null && objective.progress >= objective.target; const label = objective.name || 'Unnamed objective'; const detail = objective.progress !== null && objective.target !== null ? ` — ${objective.progress} / ${objective.target}` : ''; addTextElement(objectives, 'li', `${label}${detail}`, complete ? 'complete' : 'incomplete'); });
}

function renderActivation(snapshot) {
  const activation = snapshot.currentActivation;
  const result = snapshot.battle.result;
  document.querySelector('[data-tactical-question]').hidden = Boolean(result);
  document.querySelector('[data-battle-result]').hidden = !result;
  if (result) setText('[data-result-value]', result);
  setText('[data-activation-side]', activation ? `${activation.side || 'Unknown side'} activation` : 'No Current Activation');
  setText('[data-operative-name]', activation?.name, 'Awaiting operative data');
  setText('[data-operative-number]', activation?.number !== null && activation?.number !== undefined ? `Unit ${activation.number}` : 'Unit —');
  setText('[data-operative-order]', activation?.order ? `${activation.order} order` : 'Order unavailable');
  setText('[data-wounds]', activation ? `${displayNumber(activation.wounds)} / ${displayNumber(activation.maximumWounds)}` : '— / —');
  setText('[data-apl]', displayNumber(activation?.apl)); setText('[data-ap]', displayNumber(activation?.apRemaining)); setText('[data-weapon]', activation?.weaponName, 'Unavailable');
  setText('[data-direction-title]', snapshot.currentDirection?.title, 'No tactical direction');
  setText('[data-direction-summary]', snapshot.currentDirection?.summary, 'Standing by for activation instructions.');
}

function renderEvents(events, added = new Set()) {
  const container = document.querySelector('[data-events]');
  if (!events.length) { container.replaceChildren(); const item = document.createElement('li'); item.className = 'empty-state'; addTextElement(item, 'b', 'All channels nominal'); addTextElement(item, 'span', 'No active events detected'); container.append(item); return; }
  container.replaceChildren();
  events.forEach(event => { const item = document.createElement('li'); item.className = event.category === 'critical' || event.severity === 'critical' ? 'critical' : 'warning'; if (added.has(event.id || event.title || JSON.stringify(event))) item.classList.add('new-entry'); addTextElement(item, 'b', `⚠ ${event.title || 'Active event'}`); addTextElement(item, 'span', event.summary || 'No event description received.'); if (event.effect) addTextElement(item, 'span', `Effect: ${event.effect}`); container.append(item); });
}

function renderActivity(entries, previousKeys = new Set()) {
  const container = document.querySelector('[data-activity]');
  if (!entries.length) return replaceWithEmpty(container, 'No battle activity recorded');
  container.replaceChildren();
  entries.slice(0, 10).forEach(entry => { const item = document.createElement('li'); item.className = entry.severity || entry.category || 'battle'; if (previousKeys.size && !previousKeys.has(activityKey(entry))) item.classList.add('new-entry'); addTextElement(item, 'time', entry.timestamp || (entry.sequence !== null ? `#${entry.sequence}` : 'LOG')); addTextElement(item, 'span', entry.text || 'Activity recorded'); container.append(item); });
}

function renderRoster(selector, summarySelector, operatives) {
  const container = document.querySelector(selector);
  if (!operatives.length) { setText(summarySelector, 'No roster data'); return replaceWithEmpty(container, 'No roster data', 'p'); }
  const counts = operatives.reduce((summary, operative) => { const state = operative.currentActivation ? 'active' : operative.status; summary[state] = (summary[state] || 0) + 1; return summary; }, {});
  const states = ['ready', 'active', 'activated', 'incapacitated', 'dormant', 'retired'];
  setText(summarySelector, states.filter(state => counts[state]).map(state => `${counts[state]} ${state}`).join(' · '));
  container.replaceChildren();
  operatives.forEach(operative => { const item = document.createElement('div'); const state = operative.currentActivation ? 'active' : operative.status; item.className = `roster-entry ${state || 'unavailable'}`; addTextElement(item, 'span', operative.name || 'Unknown operative'); addTextElement(item, 'small', operative.currentActivation ? 'Active' : (operative.status || 'Unavailable')); if (operative.wounds !== null) addTextElement(item, 'b', `${operative.wounds}/${displayNumber(operative.maximumWounds)}`); container.append(item); });
}

function renderNarrative(entries) {
  const container = document.querySelector('[data-narrative]'); container.replaceChildren();
  if (!entries.length) { const item = document.createElement('li'); addTextElement(item, 'time', 'SYS'); addTextElement(item, 'span', 'Cogitator online. Awaiting meaningful tactical changes.'); container.append(item); return; }
  entries.forEach((entry, index) => { const item = document.createElement('li'); addTextElement(item, 'time', entry.timestamp || `N${String(index + 1).padStart(2, '0')}`); addTextElement(item, 'span', entry.text || entry.summary || 'System notice'); container.append(item); });
}

export function acceptDashboardSnapshot(snapshot) {
  if (snapshot?.schemaVersion !== DASHBOARD_SNAPSHOT_SCHEMA_VERSION) { setStatus(`Incompatible game-state schema (received ${snapshot?.schemaVersion ?? 'unknown'})`, 'incompatible'); return false; }
  if (!validateDashboardSnapshot(snapshot).valid || snapshot.revision <= currentRevision || previousSnapshot?.battle.result) return false;
  const changes = detectDashboardChanges(previousSnapshot, snapshot);
  const previousActivity = new Set((previousSnapshot?.recentActivity || []).map(activityKey));
  currentRevision = snapshot.revision; shell.dataset.dashboardState = snapshot.battle.result ? 'complete' : 'connected';
  setText('[data-updated]', `Updated ${new Date(snapshot.updatedAt).toLocaleTimeString()}`);
  setText('[data-turning-point]', displayNumber(snapshot.battle.turningPoint));
  setText('[data-turning-state]', snapshot.battle.maximumTurningPoints !== null ? `of ${snapshot.battle.maximumTurningPoints}` : 'Current round');
  setText('[data-threat-level]', displayNumber(snapshot.threat.level)); setText('[data-threat-name]', snapshot.threat.name, 'Unavailable');
  setText('[data-grade]', displayNumber(snapshot.threat.grade)); setText('[data-grade-description]', snapshot.threat.gradeDescription, 'Unavailable');
  setText('[data-player-ready]', `${displayNumber(snapshot.readiness.playerReady)} / ${displayNumber(snapshot.readiness.playerTotal)}`); setText('[data-player-state]', `${displayNumber(snapshot.readiness.playerReady)} operatives ready`);
  setText('[data-npo-ready]', `${displayNumber(snapshot.readiness.npoReady)} / ${displayNumber(snapshot.readiness.npoTotal)}`); setText('[data-npo-state]', `${displayNumber(snapshot.readiness.npoReady)} hostiles ready`);
  setText('[data-battle-status]', snapshot.battle.result || snapshot.battle.status, 'Standby'); setText('[data-battle-phase]', snapshot.battle.phase, snapshot.battle.result ? 'Battle complete' : 'Phase unavailable');
  if (snapshot.battle.elapsedSeconds !== null) setText('[data-session-duration]', formatDuration(snapshot.battle.elapsedSeconds));
  const addedEvents = new Set(changes.filter(change => change.type === 'eventAdded').map(change => change.key));
  renderMission(snapshot.mission); renderActivation(snapshot); renderEvents(snapshot.activeEvents, addedEvents); renderActivity(snapshot.recentActivity, previousActivity); renderRoster('[data-player-roster]', '[data-player-summary]', snapshot.playerOperatives); renderRoster('[data-npo-roster]', '[data-npo-summary]', snapshot.npoOperatives);
  addCogitatorChanges(changes); renderNarrative(cogitatorFeed); reactToChanges(changes); previousSnapshot = snapshot;
  return true;
}

function waitForIce(peer) { if (peer.iceGatheringState === 'complete') return Promise.resolve(); return new Promise((resolve, reject) => { const timer = setTimeout(() => reject(new Error('ICE gathering timed out.')), DASHBOARD_CONFIG.connectionTimeoutMs); peer.addEventListener('icegatheringstatechange', function change() { if (peer.iceGatheringState === 'complete') { clearTimeout(timer); peer.removeEventListener('icegatheringstatechange', change); resolve(); } }); }); }
async function codeFor(nonce) { const bytes = new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(`tomb-world-dashboard:${nonce}`))); return (((bytes[0] << 16) | (bytes[1] << 8) | bytes[2]) % 1000000).toString().padStart(6, '0').replace(/(\d{3})(\d{3})/, '$1 $2'); }
function updateLinkTelemetry(now = Date.now()) {
  const next = linkState(heartbeatAt, now);
  setText('[data-link-quality]', next);
  if (next !== currentLinkState && heartbeatAt) { addCogitatorChanges([{ type: 'connection', current: next }]); renderNarrative(cogitatorFeed); currentLinkState = next; }
  const latency = averageLatency(latencySamples); setText('[data-latency]', latency === null ? 'Unavailable' : `~${latency} ms`);
  if (next === 'LINK INTERRUPTED' && connectedAt) { setStatus('Nexus link: connection interrupted', 'interrupted'); }
  else if (next === 'LINK DEGRADED') setStatus('Nexus link: delayed heartbeat', 'degraded');
  else if (next === 'LIVE' && connectedAt) setStatus('Nexus link: active', previousSnapshot?.battle.result ? 'complete' : 'connected');
}
async function pair() {
  const encoded = readPairingFragment(location.hash, 'offer');
  if (!encoded) { setStatus('Nexus link: waiting for pairing', 'waiting'); return; }
  try {
    setStatus('Nexus link: negotiating', 'connecting'); const offer = await decodePairingData(encoded, { expectedType: 'offer', expectedSdpType: 'offer' }); clearPairingFragment();
    const peer = new RTCPeerConnection({ iceServers: DASHBOARD_CONFIG.iceServers });
    peer.ondatachannel = event => { const channel = event.channel; if (channel.label !== 'tomb-world-dashboard') { channel.close(); return; } const send = (type, detail) => channel.send(message(type, detail)); channel.onopen = () => send(DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY); channel.onmessage = messageEvent => { const incoming = safeParseDashboardJson(messageEvent.data); if (!validateDashboardMessage(incoming).valid) return; heartbeatAt = Date.now(); if (incoming.type === DASHBOARD_MESSAGE_TYPES.HELLO) { send(DASHBOARD_MESSAGE_TYPES.HELLO_ACK); send(DASHBOARD_MESSAGE_TYPES.REQUEST_SNAPSHOT); connectedAt = Date.now(); currentLinkState = 'LIVE'; setStatus('Nexus link: active', 'connected'); setText('[data-link-quality]', 'LIVE'); pairing.hidden = true; verification.hidden = false; clearInterval(heartbeatTimer); heartbeatTimer = setInterval(() => send(DASHBOARD_MESSAGE_TYPES.PING, { sentAt: Date.now() }), 5000); send(DASHBOARD_MESSAGE_TYPES.PING, { sentAt: Date.now() }); } else if (incoming.type === DASHBOARD_MESSAGE_TYPES.SNAPSHOT) acceptDashboardSnapshot(incoming.snapshot); else if (incoming.type === DASHBOARD_MESSAGE_TYPES.PING) send(DASHBOARD_MESSAGE_TYPES.PONG, { sentAt: incoming.sentAt, receivedAt: Date.now() }); else if (incoming.type === DASHBOARD_MESSAGE_TYPES.PONG) latencySamples = addLatencySample(latencySamples, incoming.sentAt, Date.now()); updateLinkTelemetry(); }; channel.onclose = () => { clearInterval(heartbeatTimer); setStatus('Nexus link: connection interrupted', 'interrupted'); setText('[data-link-quality]', 'LINK INTERRUPTED'); }; };
    await peer.setRemoteDescription({ type: offer.sdpType, sdp: offer.sdp }); await peer.setLocalDescription(await peer.createAnswer()); await waitForIce(peer); const answerCreatedAt = Date.now(); if (answerCreatedAt >= offer.expiresAt) throw new Error('Pairing payload has expired.');
    const answer = await serializePairingData({ protocolVersion: DASHBOARD_PROTOCOL_VERSION, type: 'answer', nonce: offer.nonce, createdAt: answerCreatedAt, expiresAt: offer.expiresAt, sdpType: 'answer', sdp: peer.localDescription.sdp, label: offer.label }); responseOutput.value = answer; await renderQrCode(document.querySelector('[data-response-qr]'), answer, 'Scan this response QR code with the game device.'); pairing.hidden = false; const sessionCode = await codeFor(offer.nonce); verification.querySelector('strong').textContent = sessionCode; setText('[data-session-id]', sessionCode); document.querySelector('[data-copy-response]').onclick = async () => { await navigator.clipboard.writeText(answer); setStatus('Response copied: return to game device', 'connecting'); }; setStatus('Nexus link: awaiting response scan', 'connecting');
  } catch (error) { setStatus(error.message || 'Nexus link: pairing failed', 'interrupted'); }
}
setInterval(() => { if (connectedAt) setText('[data-session-duration]', formatDuration(Math.floor((Date.now() - connectedAt) / 1000))); }, 1000);
setInterval(() => updateLinkTelemetry(), 2000);
pair();
