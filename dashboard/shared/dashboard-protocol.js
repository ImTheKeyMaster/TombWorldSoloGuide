import { DASHBOARD_CONFIG } from './dashboard-config.js';

export const DASHBOARD_PROTOCOL_VERSION = 1;
export const DASHBOARD_SNAPSHOT_SCHEMA_VERSION = 1;
export const MAXIMUM_ACCEPTED_MESSAGE_SIZE = DASHBOARD_CONFIG.maximumPayloadSize;

export const DASHBOARD_MESSAGE_TYPES = Object.freeze({
  HELLO: 'hello',
  DASHBOARD_READY: 'dashboard-ready',
  HELLO_ACK: 'hello-ack',
  SNAPSHOT: 'snapshot',
  REQUEST_SNAPSHOT: 'request-snapshot',
  PING: 'ping',
  PONG: 'pong',
  DISCONNECT: 'disconnect',
  PROTOCOL_ERROR: 'protocol-error'
});

export const DASHBOARD_CONNECTION_STATUSES = Object.freeze({
  OFFLINE: 'offline',
  AVAILABLE: 'available',
  AWAITING_LINK: 'awaiting-link',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
});

export const DASHBOARD_PAIRING_PAYLOAD_TYPES = Object.freeze({
  OFFER: 'offer',
  ANSWER: 'answer'
});

const KNOWN_MESSAGE_TYPES = new Set(Object.values(DASHBOARD_MESSAGE_TYPES));
const READ_ONLY_INBOUND_TYPES = new Set([
  DASHBOARD_MESSAGE_TYPES.DASHBOARD_READY,
  DASHBOARD_MESSAGE_TYPES.REQUEST_SNAPSHOT,
  DASHBOARD_MESSAGE_TYPES.PING,
  DASHBOARD_MESSAGE_TYPES.PONG,
  DASHBOARD_MESSAGE_TYPES.DISCONNECT
]);

export function safeParseDashboardJson(value) {
  if (typeof value !== 'string' || new TextEncoder().encode(value).byteLength > MAXIMUM_ACCEPTED_MESSAGE_SIZE) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

export function isDashboardMessage(value) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value)
    && value.protocolVersion === DASHBOARD_PROTOCOL_VERSION
    && typeof value.type === 'string');
}

export function isKnownDashboardMessage(value) {
  return isDashboardMessage(value) && KNOWN_MESSAGE_TYPES.has(value.type);
}

export function validateDashboardMessage(value) {
  if (!isDashboardMessage(value)) return { valid: false, reason: 'invalid-schema' };
  if (!KNOWN_MESSAGE_TYPES.has(value.type)) return { valid: false, ignored: true, reason: 'unknown-message-type' };
  return { valid: true };
}

export function isReadOnlyDashboardMessage(value) {
  return validateDashboardMessage(value).valid && READ_ONLY_INBOUND_TYPES.has(value.type);
}

export function validateDashboardSnapshot(value) {
  const valid = Boolean(value && typeof value === 'object' && !Array.isArray(value)
    && value.schemaVersion === DASHBOARD_SNAPSHOT_SCHEMA_VERSION
    && value.protocolVersion === DASHBOARD_PROTOCOL_VERSION
    && Number.isSafeInteger(value.revision) && value.revision > 0
    && Number.isFinite(value.updatedAt)
    && value.app && typeof value.app.version === 'string'
    && value.battle && value.threat && value.readiness && value.mission
    && Array.isArray(value.activeEvents)
    && Array.isArray(value.playerOperatives)
    && Array.isArray(value.npoOperatives)
    && Array.isArray(value.recentActivity)
    && Array.isArray(value.narrativeFeed));
  return valid ? { valid: true } : { valid: false, reason: 'invalid-snapshot-schema' };
}

export function isPairingPayload(value) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value)
    && value.protocolVersion === DASHBOARD_PROTOCOL_VERSION
    && Object.values(DASHBOARD_PAIRING_PAYLOAD_TYPES).includes(value.type)
    && typeof value.payload === 'string'
    && new TextEncoder().encode(value.payload).byteLength <= MAXIMUM_ACCEPTED_MESSAGE_SIZE);
}
