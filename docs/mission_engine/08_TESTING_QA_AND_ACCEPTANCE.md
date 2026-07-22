# Work Package 08 — Automated Testing, Manual QA, and Final Acceptance

## Goal

Prove the engine is generic, Mission 04 is correct, and existing gameplay remains stable.

## Test strategy

Use the repository's existing test framework. Do not introduce a second test framework without necessity.

Inject deterministic dice results. Do not write flaky tests depending on random rolls or animation timing.

## Unit tests

### Registry and loader

- known mission resolves;
- unknown mission returns controlled error;
- duplicate mission IDs rejected;
- malformed file rejected;
- schema version enforced;
- future mission fixture loads.

### Conditions

- all;
- any;
- not;
- numeric comparisons;
- equality;
- invalid path;
- invalid operator;
- no arbitrary global access.

### Expressions

- add;
- subtract;
- multiply;
- min;
- max;
- result paths;
- input paths;
- invalid operand.

### Counters

- initialize;
- add;
- subtract;
- set;
- clamp min;
- clamp max;
- lock after completion;
- reject invalid numeric values.

### Event execution

- operations run in order;
- event rollback on failure;
- history generated once;
- once-per-game;
- once-per-turning-point;
- once-per-activation;
- cancellation leaves unresolved.

## Mission 04 integration tests

1. Start new Mission 04 game:
   - runtime = 0/20;
   - HUD = 0/20;
   - Breach available.

2. Breach roll 4 and 5:
   - adds 9;
   - HUD = 9/20;
   - history correct;
   - result dialog correct.

3. Repeat navigation:
   - no duplicate +9.

4. Repair with roll 5 and 2 controllers:
   - subtracts 3;
   - HUD = 6/20;
   - event marked resolved for Turning Point.

5. Re-enter Strategy Phase in same Turning Point:
   - no second repair roll.

6. Repair with roll 2 and 4 controllers:
   - subtracts 0;
   - wording says no points repaired.

7. Breach from 18 with roll 7:
   - clamps 20;
   - completion once;
   - HUD complete;
   - action removed;
   - no Victory.

8. After completion:
   - repair skipped;
   - progress remains 20;
   - save/load remains complete.

## Persistence tests

- new-format round trip;
- old save migration;
- malformed mission section recovery;
- no duplicate history after resume;
- no rerun of completed repair hook;
- changing mission resets mission runtime;
- unrelated save fields unchanged.

## UI tests

- HUD button accessible;
- HUD opens details;
- Game Menu opens same details;
- focus trap;
- focus restoration;
- Escape;
- mobile width;
- long history;
- empty history;
- reduced motion;
- result announcement.

## Regression tests

Run all existing tests covering:

- mission selection;
- deployment;
- Player and NPO rosters;
- initiative;
- strategy phase;
- activation alternation;
- APL limits;
- shooting;
- melee;
- attack resolution;
- save/load;
- game menu;
- victory/loss.

No existing behavior should change unless explicitly required.

## Manual QA checklist

### Fresh game

- Clear storage/cache as appropriate.
- Start Mission 04.
- Verify no console errors.
- Verify HUD.
- Open details from HUD.
- Open details from Game Menu.
- Resolve multiple breach actions.
- Verify exact dice/progress.
- Enter Ready step.
- Resolve repair.
- Refresh and resume.
- Complete objective.
- Continue battle.

### Mobile

- iPhone-size portrait.
- Android-size portrait.
- Landscape.
- Dialog scroll.
- Keyboard opening for numeric input.
- Rapid taps.
- Back navigation.
- No horizontal overflow.

### PWA/update

- Load previous deployed version.
- Deploy/update v6.
- Verify update notification.
- Verify new JSON is fetched/cached.
- Verify one visible version.
- Verify offline behavior where supported.

## Final acceptance criteria

The release is acceptable only when all are true:

- Mission definitions live in individual JSON files.
- Mission 04 behavior is not scattered through phase/render code.
- Generic Mission Objective Engine exists.
- Future fixture loads without engine change.
- Shared animated dice are used.
- Mission HUD is compact and clickable.
- Mission Details is reusable.
- Repair runs once per Turning Point.
- Completion locks at 20.
- Completion does not trigger Victory.
- Save/load and migration work.
- Unsupported missions remain playable.
- No blank screen or duplicate version display.
- All available automated tests pass.
- Manual QA is documented.

## Required Codex final report

Codex must include:

- summary;
- architecture notes;
- exact files changed;
- exact tests run and results;
- screenshots or descriptions of key UI states if supported;
- known limitations;
- confirmation that objective completion does not end the battle;
- confirmation that Mission 04 rules are JSON-driven.
