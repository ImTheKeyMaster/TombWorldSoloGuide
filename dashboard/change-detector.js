const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);
const operativeKey = operative => operative.id || `${operative.name || ''}:${operative.number ?? ''}`;
const eventKey = event => event.id || event.title || JSON.stringify(event);

export function detectDashboardChanges(previous, current) {
  if (!previous || !current) return [];
  const changes = [];
  const add = (type, panel, detail = {}) => changes.push({ type, panel, ...detail });
  if (previous.battle.turningPoint !== current.battle.turningPoint) add('turningPoint', 'status', { current: current.battle.turningPoint });
  if (previous.threat.level !== current.threat.level) add('threat', 'status', { current: current.threat.level, direction: current.threat.level > previous.threat.level ? 'increased' : 'decreased' });
  if (previous.threat.grade !== current.threat.grade) add('grade', 'status', { current: current.threat.grade });
  if (!same([previous.mission.progress, previous.mission.objectives], [current.mission.progress, current.mission.objectives])) add('mission', 'mission');
  const activationIdentity = activation => activation && [activation.side, activation.operativeId, activation.name, activation.number];
  if (!same(activationIdentity(previous.currentActivation), activationIdentity(current.currentActivation))) add('activation', 'activation', { name: current.currentActivation?.name || null });
  for (const group of ['playerOperatives', 'npoOperatives']) {
    const oldById = new Map(previous[group].map(item => [operativeKey(item), item]));
    current[group].forEach(operative => {
      const old = oldById.get(operativeKey(operative));
      if (!old) return;
      if (old.wounds !== operative.wounds) add('wounds', 'roster', { name: operative.name, group, current: operative.wounds });
      if (old.status !== 'incapacitated' && operative.status === 'incapacitated') add('incapacitated', 'roster', { name: operative.name, group });
    });
  }
  for (const [field, type] of [['playerReady', 'playerReadiness'], ['npoReady', 'npoReadiness']]) {
    if (previous.readiness[field] !== current.readiness[field]) add(type, 'roster', { current: current.readiness[field], direction: current.readiness[field] > previous.readiness[field] ? 'increased' : 'decreased' });
  }
  const oldEvents = new Map(previous.activeEvents.map(event => [eventKey(event), event]));
  const newEvents = new Map(current.activeEvents.map(event => [eventKey(event), event]));
  newEvents.forEach((event, key) => { if (!oldEvents.has(key)) add('eventAdded', 'events', { key, name: event.title }); });
  oldEvents.forEach((event, key) => { if (!newEvents.has(key)) add('eventRemoved', 'events', { key, name: event.title }); });
  if (!previous.battle.result && current.battle.result) add('battleComplete', 'activation', { result: current.battle.result });
  return changes;
}

export function activityKey(entry) {
  return entry.sequence ?? `${entry.timestamp || ''}:${entry.category || ''}:${entry.text || ''}`;
}
