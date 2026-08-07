import { DASHBOARD_CONNECTION_STATUSES } from './shared/dashboard-protocol.js';

const status = document.querySelector('[data-dashboard-status]');
if (status) {
  status.dataset.connectionStatus = DASHBOARD_CONNECTION_STATUSES.AWAITING_LINK;
}
