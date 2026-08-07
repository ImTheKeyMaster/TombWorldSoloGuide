export const DASHBOARD_FEATURE_ENABLED = true;

export const DASHBOARD_CONFIG = Object.freeze({
  featureEnabled: DASHBOARD_FEATURE_ENABLED,
  protocolVersion: 1,
  pagePath: 'dashboard/index.html',
  connectionTimeoutMs: 10000,
  onlineProbeTimeoutMs: 3000,
  heartbeatIntervalMs: 15000,
  heartbeatTimeoutMs: 45000,
  maximumPayloadSize: 65536,
  iceServers: Object.freeze([]),
  onlineProbePath: 'dashboard/online-check.txt'
});
