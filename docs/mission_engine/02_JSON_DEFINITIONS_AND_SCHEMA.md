# Work Package 02 — Mission JSON Definitions, Schema, and Registry

## Goal

Create the data contract that allows missions to be added as content rather than hard-coded JavaScript.

## Directory structure

Create a dedicated mission directory compatible with the repository's asset conventions:

```text
/Missions/
  manifest.js or manifest.json
  mission.schema.json
  04-Destroy-Sarcophagus.json
  README.md
```

Use lowercase names instead only if that matches the repository. Do not scatter mission JSON across multiple unrelated folders.

## Mission definition contract

A mission definition must be declarative and self-contained enough for the generic engine and UI to interpret.

Recommended top-level shape:

```json
{
  "$schema": "./mission.schema.json",
  "schemaVersion": 1,
  "id": "04",
  "slug": "destroy-sarcophagus",
  "name": "Destroy Sarcophagus",
  "briefing": "...",
  "objectiveSummary": "...",
  "objectives": [],
  "actions": [],
  "hooks": {},
  "completion": {},
  "hud": {},
  "dialogs": {},
  "presentation": {}
}
```

## Required top-level fields

### `schemaVersion`

Integer. Required.

Used to evolve mission definition files independently from save-game schema versions.

### `id`

String. Required. Unique.

Preserve leading zeroes where mission numbering uses them.

### `slug`

Lowercase stable identifier using letters, numbers, and hyphens.

### `name`

Human-readable mission name.

### `briefing`

Full mission rule summary or concise app-specific briefing. Keep this distinct from the short HUD text.

### `objectiveSummary`

Short sentence shown in Mission Details.

## Objectives

Each objective must include:

```json
{
  "id": "destructionPoints",
  "type": "counter",
  "label": "Destruction Points",
  "initial": 0,
  "minimum": 0,
  "maximum": 20,
  "target": 20,
  "lockOnComplete": true,
  "completion": {
    "operator": ">=",
    "value": 20
  }
}
```

Supported initial objective types:

- `counter`
- `boolean`

Do not invent complex objective types in this release.

## Actions

Mission actions are manually initiated by the user from an approved gameplay location.

Action shape:

```json
{
  "id": "breachSarcophagus",
  "label": "Breach Sarcophagus",
  "description": "Roll 2D6 and add the result to Destruction Points.",
  "availability": {
    "all": [
      { "path": "mission.objectives.destructionPoints.completed", "operator": "==", "value": false }
    ]
  },
  "confirmation": {
    "required": true,
    "title": "Breach Sarcophagus?",
    "message": "Confirm that the operative can perform the mission action."
  },
  "operations": [
    {
      "type": "requestDiceRoll",
      "id": "breachRoll",
      "dice": { "count": 2, "sides": 6 },
      "label": "Breach Sarcophagus"
    },
    {
      "type": "addCounter",
      "objectiveId": "destructionPoints",
      "valueFrom": "results.breachRoll.total"
    }
  ]
}
```

The exact tabletop eligibility remains a player decision unless the app already tracks every required condition. The app should confirm that the player has determined the action is legal, rather than pretending to verify tabletop geometry it cannot know.

## Hooks

Hooks are events fired by the app lifecycle.

Initial supported hook names:

- `onMissionInitialized`
- `onStrategyPhaseReadyStep`
- `onPlayerActivationStarted`
- `onPlayerActivationCompleted`
- `onNpoActivationStarted`
- `onNpoActivationCompleted`
- `onTurningPointEnded`
- `onBattleEnded`

Mission 04 primarily requires `onStrategyPhaseReadyStep`.

Hook entries may include:

- id;
- label;
- availability/condition;
- once-per scope;
- operations;
- result dialog metadata;
- history metadata.

## Dice definitions

Use structured dice rather than strings internally:

```json
{
  "count": 2,
  "sides": 6
}
```

The loader may normalize `"2D6"` if convenient, but the canonical JSON should be structured.

Only use dice types supported by the shared dice renderer. This release requires D6.

## Numeric input

Some future missions may require the player to provide a count known only from the tabletop.

Generic operation:

```json
{
  "type": "requestNumericInput",
  "id": "controllingPlayerOperatives",
  "label": "Player operatives controlling the Sarcophagus",
  "minimum": 0,
  "maximum": 20,
  "default": 0,
  "integer": true
}
```

Do not hard-code the input field into Mission 04 JavaScript. The JSON requests the input and the generic engine/dialog system renders it.

## Derived values

Support simple arithmetic declaratively without `eval`.

Recommended expression format:

```json
{
  "operation": "max",
  "arguments": [
    0,
    {
      "operation": "subtract",
      "arguments": [
        { "path": "results.repairRoll.total" },
        { "path": "inputs.controllingPlayerOperatives" }
      ]
    }
  ]
}
```

Minimum arithmetic operations:

- add
- subtract
- multiply
- min
- max

Division is not required unless the existing mission rules need it.

## Completion

Mission completion must distinguish objective completion from battle victory.

```json
{
  "objectiveId": "destructionPoints",
  "operator": ">=",
  "value": 20,
  "endsBattle": false,
  "dialogId": "objectiveComplete"
}
```

`endsBattle` must default to false when omitted.

## HUD configuration

Example:

```json
{
  "label": "MISSION",
  "inProgress": {
    "format": "{value} / {target}"
  },
  "complete": {
    "format": "✓ COMPLETE"
  }
}
```

The engine should provide resolved values to the UI. Avoid a general-purpose templating engine; support a small documented token set.

## Dialog definitions

Keep reusable labels in JSON:

- Mission Details title;
- progress label;
- objective complete title/message;
- mission roll result title;
- Close/Continue labels only if the app does not already standardize them.

The engine/UI should own dialog structure and accessibility.

## Presentation metadata

May include:

- icon key;
- history display count;
- whether the HUD cell is visible;
- descriptive text.

Do not allow arbitrary HTML in JSON. Render all text safely.

## JSON schema

Create `mission.schema.json` that validates:

- required fields;
- field types;
- allowed objective types;
- allowed operation types;
- allowed hook names;
- allowed condition operators;
- numeric limits;
- unique objective/action IDs within a mission where possible;
- no additional properties where strictness is beneficial.

JSON Schema alone cannot reliably detect duplicate mission IDs across files. The registry must perform that check.

## Missions README

Create `/Missions/README.md` explaining:

1. how to copy the template;
2. how to assign a unique ID and slug;
3. how to add the path to the manifest;
4. what operations are supported;
5. how to validate the file;
6. when an engine enhancement is required;
7. that executable code is prohibited.

## Example and template files

Create:

- `04-Destroy-Sarcophagus.json`
- `MissionTemplate.json` or an example in README
- one test fixture representing a future mission that uses only existing operations

The future fixture does not need to appear in production mission selection.

## Tests

Add tests for:

- valid Mission 04 JSON;
- missing required fields;
- unknown operation;
- unknown hook;
- duplicate objective IDs;
- duplicate action IDs;
- duplicate mission IDs in registry;
- unsafe text rendered as text, not HTML;
- default `endsBattle: false`;
- future mission fixture loading without engine changes.
