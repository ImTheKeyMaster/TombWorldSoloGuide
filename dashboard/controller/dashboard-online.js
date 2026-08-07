import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';

let lastAvailability = false;
let shouldRecheckAvailability = () => false;

export function setDashboardOnlineEligibility(eligibilityCheck) {
  shouldRecheckAvailability = typeof eligibilityCheck === 'function' ? eligibilityCheck : () => false;
}

export async function checkDashboardOnline() {
  if (!navigator.onLine) {
    lastAvailability = false;
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
    return lastAvailability;
  } catch {
    lastAvailability = false;
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

export function getLastDashboardAvailability() {
  return lastAvailability;
}

function recheckRequestedAvailability() {
  if (shouldRecheckAvailability()) void checkDashboardOnline();
}

window.addEventListener('online', recheckRequestedAvailability);
window.addEventListener('offline', recheckRequestedAvailability);
