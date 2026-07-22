# Mission Objective Engine — Final Acceptance

## Release decision

**Release:** v6.0.0  
**Automated acceptance:** Pass  
**Recommendation:** Go for the tested static-web release, with the device/browser checks listed under *Intentionally deferred* completed as deployment smoke tests.

This report covers Work Packages 01–08. Mission 04, Destroy Sarcophagus, remains the only mission registered with the Mission Objective Engine. The other mission content continues to use the existing application rules and is not represented as engine automation.

## Delivered architecture

- `mission-engine.js` owns definition validation, registry loading, safe conditions and expressions, counter mutation, transactional event execution, idempotency, history, restoration, and UI view models.
- `Missions/manifest.json` is the production registry. Its `definitions` collection registers only `definition-04-destroy-sarcophagus.json`; its separate `missions` collection continues to provide the six existing mission briefings.
- `app.js` adapts the engine to the existing dice animation, dialogs, HUD, Strategy Phase, activation lifecycle, save flow, and error notifications. Mission calculations remain definition-driven.
- `persistence.js` performs sequential save-schema migration and defensive normalization before `app.js` restores the mission runtime.
- `service-worker.js` uses a versioned cache, network-first code and JSON requests, and precaches the manifest, schema, and Mission 04 definition needed by the engine.

## Lifecycle hooks

The supported, fixed hook list is:

1. `onMissionInitialized`
2. `onStrategyPhaseReadyStep`
3. `onPlayerActivationStarted`
4. `onPlayerActivationCompleted`
5. `onNpoActivationStarted`
6. `onNpoActivationCompleted`
7. `onTurningPointEnded`
8. `onBattleEnded`

Mission 04 uses only `onStrategyPhaseReadyStep` for Nanoscarab Repair. Execution markers persist once-per-Turning-Point results, while cancellation rolls back the event and leaves it available for retry.

## Save and migration behavior

- Saves retain the existing `tombWorldSoloGuide.v1` browser key and add the current integer `saveVersion` without deleting unknown harmless fields.
- Unversioned/schema-zero saves migrate sequentially to the current schema and normalization is idempotent.
- Missing `missionState`, `reinforcementState`, or `missionRuntime` values receive safe defaults. Invalid roster and reinforcement references are removed.
- A partial or malformed Mission 04 runtime is normalized against the current definition; unrecoverable mission data resets only mission automation rather than the whole game.
- Unsupported future save schemas and invalid imports are rejected before replacing current browser state. Storage failures are caught without blanking the application.
- Export uses the same persisted state, including mission progress, history, completion, and lifecycle execution markers; import migrates and normalizes before committing it.

## Mission 04 reference behavior

- The runtime starts at 0 of 20 Destruction Points.
- Breach Sarcophagus requests the shared animated 2D6 service and adds its total.
- Nanoscarab Repair requests the controlling-operative count, rolls the shared animated D6, and subtracts `max(0, roll - controllers)` during the Ready step once per Turning Point.
- Counter updates clamp to 0–20. At 20, completion is idempotent and `lockOnComplete` prevents later repair.
- The compact HUD and reusable Mission Details dialog derive progress and history from runtime state.
- Objective completion displays “Continue the battle.” It does not call or replace battle victory/defeat logic.

## Adding a future mission

1. Copy `Missions/MissionTemplate.json` and provide a unique ID and slug.
2. Use only the documented declarative objectives, conditions, expressions, operations, and lifecycle hooks. JSON must never contain executable code or HTML.
3. Add the definition to `Missions/manifest.json` only when it is ready for production selection.
4. Add the definition to the service-worker precache when offline automation is required.
5. Validate the JSON and schema, add deterministic behavioral tests, exercise cancellation and restoration, and run the complete regression suite.
6. Change `mission-engine.js` only when the mission genuinely needs a generic capability not already supported; do not add mission-specific calculations to lifecycle or rendering code.

## Validation and test commands

Run from the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --check app.js
node --check mission-engine.js
node --check persistence.js
node --check service-worker.js
python3 -m json.tool Missions/manifest.json >/dev/null
python3 -m json.tool Missions/mission.schema.json >/dev/null
find Missions Player_Operatives -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
git diff --check
```

There is no repository-provided lint or formatter configuration; no substitute framework or build tool was introduced.

## Traceable acceptance checklist

Status definitions: **Implemented** means present in production code; **Tested** means executed by an automated behavioral or validation check; **Manually verified** means directly inspected or exercised without claiming unavailable browser/device coverage; **Deferred** identifies an explicit remaining deployment check.

| Requirement | Implemented | Tested | Manually verified | Intentionally deferred |
| --- | --- | --- | --- | --- |
| Generic registry, loader, schema validation, conditions, expressions, counters, transactions, and history | Yes | Yes | Definition/manifest review | No |
| Mission 04 initialization, Breach, repair, 0–20 clamping, completion lock, and history | Yes | Yes, deterministic runtime playthrough | JSON/runtime result review | No |
| Ready-step once-per-Turning-Point and cancellation-safe retry | Yes | Yes | Integration flow review | Browser animation/cancel smoke test |
| Compact HUD, details/history, completed text, and repeated-render guards | Yes | Yes, code/integration regression | Markup/CSS review | Screen-reader and real-browser interaction |
| Objective completion remains independent of battle completion | Yes | Yes | Call-path and definition review | Full physical UI playthrough |
| Lifecycle hooks execute at stable boundaries without duplication | Yes | Yes | Integration call-path review | No |
| Save round trip, old-save migration, partial/malformed recovery, future-version rejection, and import safety | Yes | Yes | Persistence review | Browser refresh/export/import smoke test |
| Reinforcement checkboxes persist across rendering and block/unblock Strategy continuation | Yes | Yes, behavioral DOM harness | Source/CSS review | Touch-device smoke test |
| Unavailable/malformed/unsupported definition, canceled dialogs, missing services, and duplicate execution fail safely | Yes | Yes | Error-boundary review | Offline browser failure messaging |
| Keyboard dialog behavior, focus trap/return, accessible names, locked dice modal, text completion state, and duplicate-ID guards | Yes | Yes | Markup/event review | VoiceOver/NVDA session |
| 390px portrait, dialog scrolling, safe areas, touch targets, and landscape rules | Yes | Static regression checks | CSS review | Physical iPhone portrait/landscape and soft keyboard |
| Version/cache synchronization, update notice, fresh code/JSON, and saved-data survival | Yes | Yes | Cache strategy/asset review | Upgrade from deployed v5.8.1 in browser |
| Existing combat, AI, setup, rosters, Strategy Phase, activations, and battle-end behavior | Preserved | Yes, full regression suite | Diff review | Full tabletop battle UI playthrough |
| Another production mission using the engine | No | Not applicable | Not applicable | Deliberately out of scope |

## Acceptance scenarios executed

Automated tests cover current, unversioned, legacy pre-runtime, missing reinforcement state, missing mission state, partial runtime, malformed optional fields, unknown future fields, imported-save normalization paths, and runtime restoration. They verify retained progress, safe defaults, reference cleanup, sequential/idempotent migration, non-destructive failure, and clear future-version rejection.

A deterministic Mission 04 runtime playthrough covers initialization, Breach progress, Ready repair, repeat-hook suppression, HUD/details models, 20-point clamping, completion locking, history preservation, restoration, and continued non-victory semantics. Existing regression tests cover mission selection/setup, deployment rosters, Strategy Phase, reinforcements, activation, combat, battle outcomes, accessibility wiring, and rendering guards.

## Offline and cache acceptance

The application shell loads `mission-engine.js` before `app.js`. v6.0.0 is synchronized across visible, internal, query-string, test, and cache identifiers. Code, CSS, and JSON use network-first requests, so an online update does not remain pinned to stale cached application assets. The Mission 04 definition and schema are now explicitly precached with the manifest. Cache activation removes older application caches but does not touch localStorage, and the existing waiting-worker notification/reload flow remains unchanged.

## Defect discovered and fixed

The production manifest pointed to `Missions/definition-04-destroy-sarcophagus.json`, but that definition was absent from the service-worker precache. An offline session could therefore have the app shell and manifest but lack Mission 04 automation. v6.0.0 precaches the definition and schema, with a regression test that also prevents extra engine mission definitions from entering this release.

## Known limitations

- The application cannot infer tabletop geometry, operative control of the Sarcophagus, or mission-action legality; the player supplies or confirms those facts.
- Only Mission 04 is registered for Mission Objective Engine automation.
- Pending mission dialogs are transactional but are not serialized mid-dialog; an uncommitted event is safely retried after reload.
- Automated checks do not replace Safari, installed-PWA, screen-reader, soft-keyboard, or physical tabletop acceptance.

## Intentionally deferred

The execution environment contains no supported graphical browser or browser automation package. Consequently, no claim is made that a physical iPhone/landscape session, soft keyboard, VoiceOver/NVDA session, deployed service-worker upgrade, screenshot, or literal end-to-end UI click-through was manually verified here. Those checks are release smoke tests rather than code expansion and must be recorded against the deployed build.

## Scope confirmation

No Mission 05 (or other new automated mission), lifecycle hook, combat/AI/reinforcement rule, framework, package manager, or build tool was added. Existing non-engine mission content was not converted or claimed as engine-driven.
