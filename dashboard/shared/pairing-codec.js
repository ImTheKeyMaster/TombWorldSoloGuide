import { DASHBOARD_CONFIG } from './dashboard-config.js';
import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_PAIRING_PAYLOAD_TYPES } from './dashboard-protocol.js';

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const validTypes = new Set(Object.values(DASHBOARD_PAIRING_PAYLOAD_TYPES));
const maximumCandidates = 32;
const maximumCandidateLength = 2048;

function validateCandidates(candidates) {
  if (candidates === undefined) return;
  if (!Array.isArray(candidates) || candidates.length > maximumCandidates) throw new Error('Unsupported or corrupt pairing payload.');
  candidates.forEach(candidate => {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) throw new Error('Unsupported or corrupt pairing payload.');
    if (typeof candidate.candidate !== 'string' || !candidate.candidate || candidate.candidate.length > maximumCandidateLength) throw new Error('Unsupported or corrupt pairing payload.');
    if (candidate.sdpMid !== undefined && candidate.sdpMid !== null && (typeof candidate.sdpMid !== 'string' || candidate.sdpMid.length > 64 || /[\r\n]/.test(candidate.sdpMid))) throw new Error('Unsupported or corrupt pairing payload.');
    if (candidate.sdpMLineIndex !== undefined && candidate.sdpMLineIndex !== null && (!Number.isSafeInteger(candidate.sdpMLineIndex) || candidate.sdpMLineIndex < 0 || candidate.sdpMLineIndex > 65535)) throw new Error('Unsupported or corrupt pairing payload.');
    if (candidate.usernameFragment !== undefined && (typeof candidate.usernameFragment !== 'string' || candidate.usernameFragment.length > 256 || /[\r\n]/.test(candidate.usernameFragment))) throw new Error('Unsupported or corrupt pairing payload.');
    if (Object.keys(candidate).some(key => !['candidate', 'sdpMid', 'sdpMLineIndex', 'usernameFragment'].includes(key))) throw new Error('Unsupported or corrupt pairing payload.');
  });
}

function base64Url(bytes) {
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 0x8000) binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function fromBase64Url(value) {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error('Unsupported or corrupt pairing payload.');
  const binary = atob(value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '='));
  return Uint8Array.from(binary, character => character.charCodeAt(0));
}
async function transform(bytes, format, mode) {
  const Stream = mode === 'compress' ? globalThis.CompressionStream : globalThis.DecompressionStream;
  if (!Stream) return null;
  const stream = new Blob([bytes]).stream().pipeThrough(new Stream(format));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}
export async function serializePairingData(data) {
  validatePairingData(data, { expectedType: data.type, expectedSdpType: data.sdpType, allowExpired: true });
  const plain = encoder.encode(JSON.stringify(data));
  if (plain.byteLength > DASHBOARD_CONFIG.maximumPayloadSize) throw new Error('Pairing payload is too large.');
  const compressed = await transform(plain, 'deflate-raw', 'compress').catch(() => null);
  return `${compressed && compressed.length < plain.length ? 'z' : 'j'}.${base64Url(compressed && compressed.length < plain.length ? compressed : plain)}`;
}
export async function decodePairingData(encoded, expectations = {}) {
  try {
    if (typeof encoded !== 'string' || encoded.length > DASHBOARD_CONFIG.maximumEncodedPayloadSize) throw new Error();
    const [format, value, extra] = encoded.split('.');
    if (extra || !['j', 'z'].includes(format)) throw new Error();
    let bytes = fromBase64Url(value);
    if (format === 'z') {
      bytes = await transform(bytes, 'deflate-raw', 'decompress');
      if (!bytes) throw new Error();
    }
    if (bytes.byteLength > DASHBOARD_CONFIG.maximumPayloadSize) throw new Error();
    const data = JSON.parse(decoder.decode(bytes));
    validatePairingData(data, expectations);
    return data;
  } catch (error) {
    if (/expired|nonce|protocol|type/i.test(error?.message || '')) throw error;
    throw new Error('Unsupported or corrupt pairing payload.');
  }
}
export function validatePairingData(data, { expectedType, expectedNonce, expectedSdpType, allowExpired = false } = {}) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('Unsupported or corrupt pairing payload.');
  if (data.protocolVersion !== DASHBOARD_PROTOCOL_VERSION) throw new Error('Unsupported pairing protocol version.');
  if (!validTypes.has(data.type) || (expectedType && data.type !== expectedType)) throw new Error('Unexpected pairing payload type.');
  if (!/^[a-f0-9]{32}$/.test(data.nonce) || (expectedNonce && data.nonce !== expectedNonce)) throw new Error('Pairing response nonce does not match.');
  if (!Number.isSafeInteger(data.createdAt) || !Number.isSafeInteger(data.expiresAt) || data.expiresAt <= data.createdAt) throw new Error('Unsupported or corrupt pairing payload.');
  if (!allowExpired && Date.now() > data.expiresAt) throw new Error('Pairing payload has expired.');
  if (!['offer', 'answer'].includes(data.sdpType) || (expectedSdpType && data.sdpType !== expectedSdpType)) throw new Error('Unexpected SDP type.');
  if (typeof data.sdp !== 'string' || !data.sdp || encoder.encode(data.sdp).byteLength > DASHBOARD_CONFIG.maximumPayloadSize) throw new Error('Pairing payload is too large.');
  validateCandidates(data.candidates);
  if (data.label !== undefined && (typeof data.label !== 'string' || data.label.length > 80)) throw new Error('Unsupported or corrupt pairing payload.');
  return data;
}
export function readPairingFragment(hash = location.hash, key = 'offer') {
  const match = new RegExp(`(?:^#|&)${key}=([^&]+)`).exec(hash);
  return match ? decodeURIComponent(match[1]) : null;
}
export function clearPairingFragment() { history.replaceState(null, '', `${location.pathname}${location.search}`); }
