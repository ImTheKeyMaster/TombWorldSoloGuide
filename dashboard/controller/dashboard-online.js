import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';

let availabilityRequested = false;
let lastAvailability = false;

export async function checkDashboardOnline() {
  availabilityRequested = true;
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
  if (availabilityRequested) void checkDashboardOnline();
}

window.addEventListener('online', recheckRequestedAvailability);
window.addEventListener('offline', recheckRequestedAvailability);
