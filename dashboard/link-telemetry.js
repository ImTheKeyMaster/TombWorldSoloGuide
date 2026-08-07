export const LINK_DEGRADED_AFTER_MS = 12000;
export const LINK_INTERRUPTED_AFTER_MS = 30000;

export function addLatencySample(samples, sentAt, receivedAt = Date.now(), maximum = 5) {
  const latency = receivedAt - Number(sentAt);
  if (!Number.isFinite(latency) || latency < 0 || latency > 120000) return samples.slice(-maximum);
  return [...samples, latency].slice(-maximum);
}

export function averageLatency(samples) {
  if (!samples.length) return null;
  return Math.round(samples.reduce((sum, sample) => sum + sample, 0) / samples.length);
}

export function linkState(lastHeartbeatAt, now = Date.now()) {
  if (!lastHeartbeatAt || now - lastHeartbeatAt >= LINK_INTERRUPTED_AFTER_MS) return 'LINK INTERRUPTED';
  if (now - lastHeartbeatAt >= LINK_DEGRADED_AFTER_MS) return 'LINK DEGRADED';
  return 'LIVE';
}
