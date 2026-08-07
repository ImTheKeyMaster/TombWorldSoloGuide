import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import {
  checkDashboardOnline,
  getLastDashboardAvailability,
  setDashboardOnlineEligibility
} from './dashboard-online.js';

export function isDashboardFeatureEnabled() {
  return DASHBOARD_CONFIG.featureEnabled;
}

export async function requestDashboardAvailability({
  hasResumableGame = false,
  gameMenuOpen = false,
  activeGame = false,
  isEligible
} = {}) {
  if (!DASHBOARD_CONFIG.featureEnabled) return false;
  const checkEligibility = typeof isEligible === 'function'
    ? isEligible
    : () => hasResumableGame || (gameMenuOpen && activeGame);
  setDashboardOnlineEligibility(checkEligibility);
  if (!checkEligibility()) return false;
  return checkDashboardOnline();
}

export function getDashboardAvailability() {
  return DASHBOARD_CONFIG.featureEnabled && getLastDashboardAvailability();
}

export function getDashboardPagePath() {
  return DASHBOARD_CONFIG.pagePath;
}

export function isDashboardWebRtcSupported() {
  return Boolean(globalThis.RTCPeerConnection && globalThis.crypto?.getRandomValues && globalThis.crypto?.subtle);
}
