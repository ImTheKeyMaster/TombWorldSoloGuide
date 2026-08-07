import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import {
  checkDashboardOnline,
  getLastDashboardAvailability,
  setDashboardOnlineEligibility
} from './dashboard-online.js';
import { DASHBOARD_MESSAGE_TYPES } from '../shared/dashboard-protocol.js';
import { createDashboardPublisher } from './dashboard-publisher.js';

let controller = null;
let publisher = null;

async function getController() {
  controller ||= await import('./dashboard-controller.js');
  return controller;
}

export async function setup({ getSnapshotSource } = {}) {
  if (publisher || typeof getSnapshotSource !== 'function') return;
  const dashboardController = await getController();
  publisher = createDashboardPublisher({ controller: dashboardController, getSnapshotSource });
  dashboardController.subscribeDashboardStatus(detail => {
    if (detail.status === 'connected') publisher?.publishImmediately();
  });
  dashboardController.subscribeDashboardMessages(message => {
    if (message.type === DASHBOARD_MESSAGE_TYPES.REQUEST_SNAPSHOT) publisher?.publishImmediately();
  });
}

export async function reestablish() { (await getController()).cleanupDashboardConnection(); }
export async function disconnect() { const value = await getController(); value.cleanupDashboardConnection(); }
export function schedulePublish(reason) { publisher?.schedulePublish(reason); }
export function getStatus() { return controller?.getDashboardStatus() || { status: 'idle', text: 'Not connected', verificationCode: null, hasAttempt: false }; }
export function subscribeStatus(listener) { return controller ? controller.subscribeDashboardStatus(listener) : () => {}; }
export async function createDashboardOffer(label) { return (await getController()).createDashboardOffer(label); }
export async function applyDashboardResponse(encoded) { return (await getController()).applyDashboardResponse(encoded); }
export async function markWaitingForResponse() { return (await getController()).markWaitingForResponse(); }

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
