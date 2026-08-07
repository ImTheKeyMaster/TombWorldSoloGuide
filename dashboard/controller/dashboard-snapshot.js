import { DASHBOARD_PROTOCOL_VERSION, DASHBOARD_SNAPSHOT_SCHEMA_VERSION, validateDashboardSnapshot } from '../shared/dashboard-protocol.js';

const text = value => typeof value === 'string' ? value : null;
const number = value => value !== null && value !== '' && Number.isFinite(Number(value)) ? Number(value) : null;
const list = value => Array.isArray(value) ? value : [];
const operative = value => ({
  id: text(value?.id), name: text(value?.name), number: number(value?.number),
  wounds: number(value?.wounds), maximumWounds: number(value?.maximumWounds),
  status: text(value?.status) || 'unavailable', order: text(value?.order),
  currentActivation: value?.currentActivation === true
});
const objective = value => ({
  id: text(value?.id), name: text(value?.name), progress: number(value?.progress), target: number(value?.target)
});
const event = value => ({ id: text(value?.id), title: text(value?.title), summary: text(value?.summary) });
const activation = value => value ? {
  side: text(value.side), operativeId: text(value.operativeId), name: text(value.name),
  wounds: number(value.wounds), maximumWounds: number(value.maximumWounds), apl: number(value.apl),
  apRemaining: number(value.apRemaining), order: text(value.order), weaponName: text(value.weaponName)
} : null;
function deepFreeze(value) {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
  Object.values(value).forEach(deepFreeze);
  return Object.freeze(value);
}

export function createDashboardSnapshot(source, revision, updatedAt = Date.now()) {
  const snapshot = {
    schemaVersion: DASHBOARD_SNAPSHOT_SCHEMA_VERSION,
    protocolVersion: DASHBOARD_PROTOCOL_VERSION,
    revision,
    updatedAt,
    app: { version: text(source?.app?.version) || 'unavailable' },
    battle: {
      status: text(source?.battle?.status) || 'unavailable', result: text(source?.battle?.result),
      turningPoint: number(source?.battle?.turningPoint), maximumTurningPoints: number(source?.battle?.maximumTurningPoints),
      phase: text(source?.battle?.phase), elapsedSeconds: number(source?.battle?.elapsedSeconds)
    },
    threat: { level: number(source?.threat?.level), name: text(source?.threat?.name), grade: number(source?.threat?.grade), gradeDescription: text(source?.threat?.gradeDescription) },
    readiness: { playerReady: number(source?.readiness?.playerReady), playerTotal: number(source?.readiness?.playerTotal), npoReady: number(source?.readiness?.npoReady), npoTotal: number(source?.readiness?.npoTotal) },
    mission: { id: text(source?.mission?.id), number: text(source?.mission?.number), name: text(source?.mission?.name), summary: text(source?.mission?.summary), progress: number(source?.mission?.progress), target: number(source?.mission?.target), objectives: list(source?.mission?.objectives).map(objective) },
    currentActivation: activation(source?.currentActivation),
    currentDirection: source?.currentDirection ? { type: text(source.currentDirection.type), title: text(source.currentDirection.title), summary: text(source.currentDirection.summary) } : null,
    activeEvents: list(source?.activeEvents).map(event),
    playerOperatives: list(source?.playerOperatives).map(operative),
    npoOperatives: list(source?.npoOperatives).map(operative),
    recentActivity: list(source?.recentActivity).slice(0, 10).map(item => ({ timestamp: text(item?.timestamp), sequence: number(item?.sequence), category: text(item?.category) || 'battle', text: text(item?.text) || '', severity: text(item?.severity) })),
    narrativeFeed: []
  };
  if (!validateDashboardSnapshot(snapshot).valid) throw new Error('Dashboard snapshot validation failed.');
  return deepFreeze(snapshot);
}

export function comparableDashboardSnapshot(snapshot) {
  const { revision, updatedAt, ...content } = snapshot;
  return JSON.stringify(content);
}
