export const COGITATOR_TEMPLATES = Object.freeze({
  turningPoint: change => [`Turning Point ${change.current} initiated.`],
  threat: change => [change.direction === 'increased' ? 'Tomb systems are awakening.' : 'Threat telemetry has receded.'],
  grade: change => [`Threat grade ${change.current} confirmed.`],
  mission: () => ['Mission objective state has advanced.'],
  activation: change => [change.name ? `${change.name} activation registered.` : 'Activation state updated.'],
  wounds: change => [`${change.name || 'Operative'} combat integrity updated.`],
  incapacitated: change => [`Operative loss recorded: ${change.name || 'unknown operative'}.`],
  playerReadiness: () => ['Player readiness state updated.'],
  npoReadiness: change => [change.direction === 'increased' ? 'Reinforcement protocols are engaged.' : 'Enemy assets retain combat integrity.'],
  eventAdded: change => [`Tomb World event active: ${change.name || 'unnamed event'}.`],
  eventRemoved: change => [`Tomb World event ended: ${change.name || 'unnamed event'}.`],
  battleComplete: change => [`Battle result confirmed: ${change.result}.`],
  connection: change => [`Noosphere link ${change.current.toLowerCase()}.`]
});

export function cogitatorLinesFor(change) {
  const template = COGITATOR_TEMPLATES[change.type];
  return template ? template(change).slice(0, 2) : [];
}
