# Work Package 01 — Mission Engine Foundation

## Goal

Create the generic runtime foundation for mission automation without implementing Mission 04 behavior yet.

## Required repository inspection

Before coding, locate and document:

- where the currently selected mission is stored;
- how mission names and rules are currently represented;
- where the HUD is rendered;
- where gameplay screens are rendered;
- where the Strategy Phase and Ready step are entered;
- where Player and NPO activations begin and end;
- how dialogs are currently created;
- how dice are generated and animated;
- how the game state is serialized and restored.

Do not assume file names. Adapt to the current structure.

## Required modules or responsibilities

Create or identify equivalent modules with these responsibilities:

### Mission registry

Responsible for:

- listing registered mission definition files;
- resolving a mission ID to a JSON path;
- detecting duplicate mission IDs after loading definitions;
- returning a validated mission definition;
- keeping mission discovery in one central location.

Automatic runtime directory enumeration is not reliable on GitHub Pages. Prefer one central manifest such as:

```js
export const MISSION_DEFINITION_PATHS = [
  "./Missions/04-Destroy-Sarcophagus.json"
];
```

A future mission should require one JSON file plus one manifest entry unless the existing build system supports reliable automatic discovery.

### Mission definition loader

Provide a function equivalent to:

```js
async function loadMissionDefinition(missionId)
```

It must:

1. resolve the JSON file through the registry;
2. fetch or import the JSON using a method compatible with the existing static GitHub Pages deployment;
3. parse the definition;
4. validate it;
5. return a normalized definition;
6. throw or return a structured error that the caller can handle without crashing the app.

### Mission runtime state

Create a single runtime state object. Suggested shape:

```js
{
  schemaVersion: 1,
  missionId: "04",
  initialized: true,
  objectives: {
    destructionPoints: {
      value: 0,
      completed: false,
      completedAt: null
    }
  },
  flags: {},
  eventExecutions: {},
  history: [],
  lastUpdatedAt: "ISO timestamp"
}
```

Do not copy the full definition into every save unless there is a compelling repository-specific reason. Save the mission ID and runtime values.

### Mission engine

Provide a generic mission engine API. The implementation may use classes or plain functions, but the public responsibilities must be clear.

Minimum capabilities:

```js
initializeMissionRuntime(definition, context)
getMissionRuntime()
getMissionDefinition()
getObjectiveValue(objectiveId)
setObjectiveValue(objectiveId, value, metadata)
adjustObjectiveValue(objectiveId, delta, metadata)
evaluateMissionConditions(trigger, context)
executeMissionAction(actionId, context)
executeMissionHook(hookName, context)
evaluateObjectiveCompletion(context)
recordMissionHistory(entry)
getMissionHudModel()
getMissionDetailsModel()
```

Adapt names to project conventions if necessary.

## Counter behavior

The engine must support generic numeric counters.

Each counter must support:

- initial value;
- minimum value;
- maximum value;
- target value;
- clamping;
- add;
- subtract;
- set;
- completion evaluation;
- optional lock after completion.

The engine must prevent `NaN`, `Infinity`, strings where numbers are expected, and invalid negative values when the definition prohibits them.

## Conditions

Implement a safe declarative condition evaluator. Do not use `eval`, `new Function`, or executable code from JSON.

Support a limited condition structure such as:

```json
{
  "all": [
    { "path": "objectives.destructionPoints.value", "operator": ">", "value": 0 },
    { "path": "objectives.destructionPoints.completed", "operator": "==", "value": false }
  ]
}
```

Minimum operators:

- `==`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `in`
- `notIn`
- truthy/falsy checks

Support `all`, `any`, and `not`.

Paths must be read from an explicit safe context containing mission runtime and approved gameplay values. Do not allow arbitrary global object traversal.

## Generic operations

The engine must support declarative operations. Initial minimum set:

- `setCounter`
- `addCounter`
- `subtractCounter`
- `setFlag`
- `clearFlag`
- `completeObjective`
- `appendHistory`
- `requestDiceRoll`
- `requestNumericInput`
- `showDialog`

Operations can be extended in later work packages.

Unknown operations must produce a controlled error and must not partially apply later operations in the same event.

## Atomic event execution

When an event has multiple operations:

1. validate the entire event first;
2. execute in order;
3. preserve enough pre-event state to roll back if an operation fails unexpectedly;
4. do not write an incomplete event to save state;
5. add one clear history record for the final outcome.

A simpler transaction snapshot is acceptable for this app if it is reliable.

## Idempotency

Hooks can be reached more than once due to re-rendering, browser refresh, back navigation, or resumed saves.

Support an optional event execution key:

```json
{
  "oncePer": "turningPoint",
  "executionKey": "nanoscarabRepair"
}
```

The engine should use runtime `eventExecutions` to prevent accidental duplicate execution.

Support at least:

- once per game;
- once per turning point;
- once per activation;
- unlimited/manual.

## History

History entries should be structured internally:

```js
{
  id: "unique id",
  timestamp: "ISO timestamp",
  turningPoint: 2,
  phase: "strategy",
  eventId: "nanoscarabRepair",
  title: "Nanoscarab Repair",
  summary: "Rolled 4, minus 1 controlling operative: 3 Destruction Points repaired.",
  delta: -3,
  resultingValue: 8
}
```

Keep enough information for the Mission Details dialog without requiring the definition to reconstruct old events.

Bound the saved history length to a reasonable limit, such as 50 entries, while displaying only the most recent entries in the UI.

## Integration constraints

- Do not render new UI in this package beyond minimal error handling needed for testing.
- Do not execute Mission 04 rules yet.
- Do not modify victory behavior.
- Do not change combat or activation rules.
- Do not update the visible version yet unless repository policy requires every PR to bump a patch/build suffix.

## Tests

Add tests for:

- runtime initialization;
- counter clamping;
- supported conditions;
- unsupported condition operators;
- supported operations;
- unsupported operations;
- atomic rollback;
- once-per-turning-point idempotency;
- history creation;
- loading an unknown mission ID;
- malformed JSON handling.

## Completion report

At the end, report the exact module names used and explain how future JSON definitions will interact with the engine.
