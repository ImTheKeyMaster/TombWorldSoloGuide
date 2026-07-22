# Work Package 06 — Persistence, Migration, and Versioning

## Goal

Persist mission runtime safely across refresh, save/load, app updates, and older saves.

## Save-state shape

Add a dedicated mission section to the existing saved game object.

Suggested:

```js
mission: {
  definitionSchemaVersion: 1,
  runtimeSchemaVersion: 1,
  missionId: "04",
  objectives: {
    destructionPoints: {
      value: 11,
      completed: false,
      completedAt: null
    }
  },
  flags: {},
  eventExecutions: {
    "nanoscarabRepair:TP2": {
      completed: true,
      completedAt: "ISO timestamp"
    }
  },
  history: [],
  lastUpdatedAt: "ISO timestamp"
}
```

Adapt to existing save conventions.

## Single source of truth

Do not separately save the same Destruction Points value in unrelated top-level properties.

The mission runtime is authoritative.

HUD and dialogs derive from runtime.

## Autosave timing

Save after:

- mission initialization;
- committed breach result;
- committed repair result;
- objective completion;
- any mission-defined flag/counter update;
- event execution marker update.

Do not save partial state before a roll result is committed unless the existing app has a robust pending-transaction system.

## Older saves

Older saves may have:

- no `mission` property;
- mission ID 04 but no mission runtime;
- legacy mission fields;
- missing history;
- missing event execution markers.

Migration must:

1. detect missing mission state;
2. initialize from the selected mission definition;
3. preserve all unrelated game state;
4. use the safest known default;
5. not invent prior Destruction Points unless a reliable legacy value exists;
6. log migration details for debugging;
7. save in the new format at the next normal save.

For Mission 04 with no legacy progress, default to 0 and explain only if a user-facing migration notice is truly needed. Avoid disruptive notices for normal upgrades.

## Definition updates

The mission definition may evolve after a save is created.

On load:

- match runtime to `missionId`;
- use current definition for labels and rules;
- preserve runtime objective values;
- clamp values to current valid ranges;
- add missing runtime fields with defaults;
- retain completed status if still valid;
- do not reopen completed objectives due solely to a JSON text change.

## Mission change/reset

When the user changes mission or starts a new game:

- discard the previous mission runtime only as part of the existing confirmed reset/new-game behavior;
- initialize the newly selected mission;
- do not carry Destruction Points into another mission.

## Corrupted mission state

If mission runtime is malformed:

- isolate the error;
- preserve the rest of the saved game;
- attempt normalization;
- if normalization is impossible, reinitialize only the mission section;
- log a clear console warning/error;
- do not blank the app.

## Event idempotency after load

Persist event execution keys so:

- Nanoscarab Repair does not rerun for a completed Turning Point;
- objective-completion dialog is not repeatedly treated as a new completion event;
- history does not duplicate on every resume.

It is acceptable for the user to reopen Mission Details and see completion status. It is not acceptable to replay completion as a new state change repeatedly.

## History persistence

- Persist structured entries.
- Cap entries at a documented maximum.
- Do not save large HTML fragments.
- Escape/render safely.
- Keep the newest entries when pruning.

## App version v6.0.0

Once all work packages are integrated, update all authoritative version references consistently.

Inspect for:

- visible version on home/menu screens;
- version constants;
- manifest;
- service worker cache name;
- update notification/version comparison;
- tests;
- release notes;
- any generated asset map.

Avoid the prior failure mode where two version values appear and the app renders blank.

## Service worker/cache

If the app is a PWA or uses a service worker:

- add new mission JSON files to the appropriate cache strategy;
- ensure old caches do not prevent loading v6 assets;
- do not assume wildcard caching works offline;
- verify first load and update behavior;
- ensure JSON fetch failure has a graceful online/offline message.

## Persistence tests

Test:

- new save contains mission runtime;
- save/load preserves progress;
- save/load preserves completion;
- save/load preserves event execution markers;
- old save with no mission field migrates;
- malformed mission field does not blank app;
- changing mission resets runtime;
- service worker version references are consistent;
- no duplicate visible versions;
- cached older app updates successfully.
