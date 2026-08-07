import { DASHBOARD_CONFIG } from '../shared/dashboard-config.js';
import { DASHBOARD_MESSAGE_TYPES } from '../shared/dashboard-protocol.js';
import { createDashboardSnapshot, comparableDashboardSnapshot } from './dashboard-snapshot.js';

export function createDashboardPublisher({ controller, getSnapshotSource, debounceMs = 150 }) {
  let timer = null, revision = 0, lastContent = null;
  async function publish(force = false) {
    timer = null;
    if (controller.getDashboardStatus().status !== 'connected') return false;
    try {
      const candidate = createDashboardSnapshot(getSnapshotSource(), revision + 1);
      const content = comparableDashboardSnapshot(candidate);
      if (!force && content === lastContent) return false;
      const message = JSON.stringify({ protocolVersion: candidate.protocolVersion, type: DASHBOARD_MESSAGE_TYPES.SNAPSHOT, snapshot: candidate });
      if (new TextEncoder().encode(message).byteLength > DASHBOARD_CONFIG.maximumPayloadSize) {
        console.warn('[Dashboard] Snapshot exceeds the configured maximum payload size.');
        return false;
      }
      controller.sendDashboardSnapshot(message);
      revision += 1;
      lastContent = content;
      return true;
    } catch (error) {
      console.warn('[Dashboard] Snapshot could not be published.', error);
      return false;
    }
  }
  function schedulePublish(reason = 'state-change') {
    if (controller.getDashboardStatus().status !== 'connected') return;
    clearTimeout(timer);
    timer = setTimeout(() => publish(false), debounceMs);
  }
  function publishImmediately() { clearTimeout(timer); timer = null; return publish(true); }
  function dispose() { clearTimeout(timer); timer = null; }
  return { schedulePublish, publishImmediately, dispose };
}
