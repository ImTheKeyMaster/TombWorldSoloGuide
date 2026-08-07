import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';

let lastAvailability = false;
let shouldRecheckAvailability = () => false;
const availabilitySubscribers = new Set();
function publishAvailability() { availabilitySubscribers.forEach(listener => listener(lastAvailability)); }

export function setDashboardOnlineEligibility(eligibilityCheck) {
  shouldRecheckAvailability = typeof eligibilityCheck === 'function' ? eligibilityCheck : () => false;
}

export async function checkDashboardOnline() {
  if (!navigator.onLine) {
    lastAvailability = false;
    publishAvailability();
    return false;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DASHBOARD_CONFIG.onlineProbeTimeoutMs);
  try {
    const probeUrl = new URL(DASHBOARD_CONFIG.onlineProbePath, document.baseURI);
    probeUrl.searchParams.set('_dashboard_probe', Date.now().toString());
    const response = await fetch(probeUrl, {
      cache: 'no-store',
      signal: controller.signal
    });
    lastAvailability = response.ok;
    publishAvailability();
    return lastAvailability;
  } catch {
    lastAvailability = false;
    publishAvailability();
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

export function getLastDashboardAvailability() {
  return lastAvailability;
}

export function subscribeDashboardAvailability(listener) {
  availabilitySubscribers.add(listener);
  listener(lastAvailability);
  return () => availabilitySubscribers.delete(listener);
}

function recheckRequestedAvailability() {
  if (shouldRecheckAvailability()) void checkDashboardOnline();
}

window.addEventListener('online', recheckRequestedAvailability);
window.addEventListener('offline', recheckRequestedAvailability);
