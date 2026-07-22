# Work Package 05 — Gameplay Lifecycle Hooks and Integration

## Goal

Connect the generic Mission Objective Engine to the existing game lifecycle without creating duplicate phase flows or unrelated regressions.

## Integration principle

The mission engine listens to lifecycle events. Existing gameplay code should not contain Mission 04-specific calculations.

Preferred pattern:

```js
await missionEngine.executeHook("onStrategyPhaseReadyStep", context);
```

Avoid:

```js
if (missionId === "04") {
  // repair calculation here
}
```

A registry lookup or engine availability check at integration boundaries is acceptable. Mission-specific mechanics belong in JSON and generic operations.

## Mission initialization

When a new game starts and the mission is selected:

1. load the selected mission definition;
2. validate it;
3. initialize runtime;
4. execute `onMissionInitialized`;
5. render/update HUD;
6. include runtime in normal save state.

Do not initialize twice when returning to the mission-selection confirmation screen.

If the mission does not have an automation JSON definition:

- allow the game to continue;
- preserve existing mission text/behavior;
- do not crash;
- log or display a non-disruptive message only where appropriate.

## Strategy Phase / Ready step

Locate the actual Ready-step entry in the current app.

For Mission 04:

- run the repair hook at the correct point;
- do not create a second Strategy Phase screen solely for mission repair;
- do not run before the user has entered the relevant phase;
- do not run twice due to re-render;
- complete the event before advancing if the event is required and active;
- if the user cancels the controlling-operatives input, remain in the current flow and allow retry.

## Turning Point context

The engine must receive a stable Turning Point value from game state.

Use it in:

- once-per-Turning-Point execution keys;
- history;
- completion metadata;
- save/load;
- Mission Details.

Do not infer the Turning Point from displayed text.

## Activation integration

Mission actions should appear only in a context where the player can select them without breaking the existing Player activation flow.

Preferred behavior:

- expose `Breach Sarcophagus` as a mission action within the appropriate Player activation action selection or mission-action area;
- only show it for the selected mission;
- only show it while incomplete;
- do not consume or alter APL unless the official app flow already records mission-action APL;
- do not let the app claim tabletop eligibility it cannot determine;
- after resolving, return the user to the activation flow;
- prevent re-resolution from stacking duplicate points through Back/Forward navigation.

If the current app has a generic action checklist, integrate carefully and preserve existing APL/action constraints.

## Completion integration

When completion occurs:

- update mission runtime;
- show completion dialog;
- return to the same gameplay flow;
- do not mark the battle complete;
- do not show Victory;
- do not auto-complete the current activation unless required by the existing action flow;
- do not reset initiative, threat, grade, rosters, or phase state.

## Event execution locks

During any mission event:

- disable the initiating control;
- prevent double taps;
- avoid multiple dice animations;
- use a pending/resolving flag;
- clear the flag after success, cancellation, or handled error;
- persist only committed outcomes.

## Back navigation

The app has had prior issues with repeated attack resolution and duplicated outcomes.

Apply the same protection here:

- once a manual mission action has committed, returning to the prior screen must show the resolved state or remove the action;
- do not allow the same action UI instance to commit again;
- use stable action resolution IDs if needed;
- navigation cancellation before commitment must not modify state.

## Save and resume during lifecycle

On resume:

- load mission runtime before rendering the HUD;
- do not replay already-resolved automatic hooks;
- do not display stale pending dialogs unless the save model explicitly supports resumable events;
- if an event was not committed, allow it to run again safely.

## Unsupported mission behavior

For missions without JSON automation:

- continue existing flow;
- provide mission information through current mechanisms;
- do not render broken counters;
- hide mission actions not defined by the mission;
- keep the Mission HUD neutral or omit it according to Work Package 04.

## Integration tests

Test:

- new game initializes runtime once;
- mission selection change resets mission runtime appropriately;
- Ready-step hook runs once;
- resumed save does not rerun repair;
- Back navigation does not duplicate breach points;
- completion leaves gameplay active;
- unsupported mission continues normally;
- mission load error does not prevent starting or resuming the rest of the game;
- normal combat and activation tests still pass.
