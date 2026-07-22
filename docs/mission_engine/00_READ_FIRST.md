# READ FIRST — Tomb World Solo Guide v6.0.0 Mission Objective Engine

## Purpose

This folder is a Codex work package for implementing the v6.0.0 Mission Objective Engine in the Tomb World Solo Guide repository.

Codex must read this file and every numbered work package before changing code. Implement the work packages in order. Do not skip ahead. Do not combine unrelated work. Do not refactor unrelated features.

## Core outcome

Build a reusable, data-driven Mission Objective Engine that:

- stores mission definitions in individual JSON files;
- uses a generic JavaScript engine rather than mission-specific logic scattered through the app;
- loads the selected mission definition at runtime;
- supports mission counters, mission actions, timing hooks, conditions, animated dice, history, completion state, HUD summaries, dialogs, save/load, and migration;
- implements Mission 04, Destroy Sarcophagus, as the reference mission;
- allows future missions that use supported engine operations to be added primarily by adding a new JSON file;
- preserves all existing gameplay behavior unless a work package explicitly changes it.

## Non-negotiable rules

1. Do not place executable JavaScript inside JSON.
2. Do not duplicate the app's existing dice animation logic. Reuse or adapt the shared dice implementation.
3. Do not automatically treat mission-objective completion as battle victory.
4. Do not add permanent large mission tracker cards to gameplay screens.
5. Do not hard-code Mission 04 behavior across unrelated rendering or phase functions.
6. Do not change unrelated styling, navigation, combat, deployment, roster, activation, or AI behavior.
7. Do not remove existing features unless this package explicitly requests removal.
8. Do not silently ignore malformed mission JSON. Fail gracefully and log a clear error.
9. Do not corrupt or discard an existing saved game because mission state is absent or invalid.
10. Keep the implementation mobile-first and accessible.

## Implementation workflow

For each work package:

1. Inspect the current repository before coding.
2. Identify the existing files and functions that already handle:
   - mission selection;
   - current mission data;
   - strategy phase;
   - activation flow;
   - game menu;
   - HUD;
   - dialogs/modals;
   - dice rendering and animation;
   - save/load;
   - versioning and service-worker caching.
3. Prefer extending existing patterns over creating a second competing framework.
4. Implement only the current work package.
5. Add or update tests.
6. Run all available automated tests and any relevant lint/build checks.
7. Report:
   - files changed;
   - behavior implemented;
   - tests executed;
   - known limitations;
   - any ambiguity discovered.
8. Stop after the work package is complete.

## Recommended PR sequence

- PR 1: Work Packages 01–02, foundation and JSON system
- PR 2: Work Package 03, Mission 04 behavior
- PR 3: Work Package 04, HUD and dialogs
- PR 4: Work Package 05, lifecycle hooks and event execution
- PR 5: Work Package 06, persistence and migration
- PR 6: Work Package 07, validation, resilience, and accessibility
- PR 7: Work Package 08, testing and final acceptance

Codex may adjust file names to fit the current repository, but must preserve the specified responsibilities and public behavior.

## Version

The final integrated release is v6.0.0. Do not create two competing visible versions. Update every authoritative version location consistently only when the final integration package requests it.
