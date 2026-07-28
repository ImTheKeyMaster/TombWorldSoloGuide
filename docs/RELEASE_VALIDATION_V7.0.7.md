# v7.0.7 Release Validation

## Scope and result

Version 7.0.7 is the final v7 stabilization pass. The release keeps exactly seven active NPO types and the existing 21-model Tomb World inventory. It adds no NPO type, profile, loadout, mission, tactical rule, or player-operative behavior.

The pre-change suite completed with **307 passing tests and no failures**. The final suite completes with **314 passing tests and no failures**. The only reproduced release defect was the Home screen reading `missionId` and `screen` from the migration result wrapper instead of its validated `state`; this left **Continue Game** disabled for a valid saved battle. The fix uses the already migrated state for both availability and restoration.

## Catalog, inventory, roster, and ordering

- The active catalog contains Geomancer, Canoptek Tomb Crawler, Canoptek Macrocyte Warrior, Canoptek Macrocyte Accelerator, Canoptek Macrocyte Reanimator, Necron Warrior, and Canoptek Scarab Swarm.
- The catalog is the single source for canonical IDs, profiles, loadouts, and physical quantities: 1, 2, 3, 1, 1, 10, and 3 respectively, totaling 21 models.
- Starting generation, setup editing, ordinary reinforcements, and A Ceaseless Scuttling continue through centralized creation and inventory validation. Tests cover unique instance IDs, legal loadouts, the single-isolator restriction, removal/regeneration, reserve reuse, eliminated allocation, and the special Scuttling exception.
- User-facing NPO presentation uses the centralized stable, case-insensitive, natural-number sorting helper on copied arrays. Deployment, roster, target, support, event, reinforcement, and selector tests preserve placeholders and verify that activation/history/gameplay chronology is not reordered.

## Profiles, deployment, activation, combat, and rules

- Profile tests verify the current APL, Move, Save, Wounds, weapon data, modes, ranges, and structured rules for the five Canoptek Circle operatives. Necron Warrior and Canoptek Scarab Swarm remain in the shared profile, activation, combat, threat, and history paths.
- Mission and setup tests cover all six supported missions, generated deployment counts, deployed/reserve partitioning, duplicate prevention, setup navigation, and the absence of an Obelisk Node step.
- Activation and combat tests cover effective APL, legality before ranking, loadout-dependent attacks, pending/completed combat restoration, one-time damage commitment, cancellation, automatic dice restoration, generic rule display/resolution, incapacitation, Reanimate, and Aggressive Defence.
- Rule tests cover Canoptek Control, Molecular Breach, Geomantic Disturbance, Dimensional Banishment, Aggressive Defence, A Ceaseless Scuttling, Overcharge, Cranial Overload, Reanimate, and Nanoscarab Beam, including once-per-turning-point and temporary-effect persistence/expiry behavior.
- Strategy and reinforcement tests cover reserve-first allocation, physical limits, unique identities, placement confirmation, history, and the isolated A Ceaseless Scuttling new-instance behavior. Existing threat and grade bounds and transitions remain unchanged and tested.

## Persistence, migration, import, export, and history

- Current saves migrate as current; normalized current exports round-trip idempotently without duplicate IDs, effects, or history.
- Legacy migration tests cover the evidenced `Canoptek Macrocyte` alias, loadout defaults, stable-ID creation/repair, profile normalization, wound clamping, portrait/Matrix-field removal, deterministic repeated migration, and future-schema rejection.
- Unsupported active NPO data takes the explicit regeneration path. Cancel leaves the stored/imported source unchanged; confirmation retains the mission, player roster, settings, preferences, and completed history while resetting unsafe active-battle state.
- Failed imports and invalid JSON retain the current game. Current serialization excludes obsolete portrait and Obelisk Node Matrix state. Historical names remain ordinary journal text and never enter catalog, inventory, or rule processing.

## Documentation and help

- README release history now documents v7.0.7 and gives practical player guidance for the Tomb World box pool, physical-model roster, alphabetical presentation, per-instance loadouts, text-only NPO UI, unsupported Obelisk Node Matrix, and legacy regeneration flow.
- Home **How It Works** and in-game **Help** now provide the same current NPO scope and save guidance without copying official rules text or exposing implementation details.

## Cleanup and retained references

- No obsolete production code or asset was found that could be safely removed beyond the corrected stale persistence-result assumption. No speculative cleanup was performed.
- No NPO portrait directory, fallback, image builder, UI container, request, or service-worker entry remains. Player-operative portraits, mission maps, the app icon, victory/defeat art, and the eliminated-NPO skull remain because current Player, mission, navigation, outcome, and accessible status UI use them.
- `Canoptek Macrocyte` remains only where it identifies the canonical active Warrior, documents historical audit findings, or implements/tests the evidenced migration alias. The unknown retired-type fixture remains to test safe regeneration and completed-history preservation.
- Remaining `obelisk` and `matrix` matches are migration cleanup keys, v7.0.5/v7.0.6/v7.0.7 historical documentation, and regression fixtures/assertions proving the feature remains absent. Generic mission data structures do not represent the Obelisk Node Matrix.
- Historical release versions remain in their correct README entries and migration fixtures. Active application, cache, asset-query, and test expectations use 7.0.7.

## Responsive layout and accessibility

- Existing automated viewport guards cover phone layouts at approximately 390px, wider responsive grids, modal height/scroll behavior, wrapped operative identities, attack layouts, HUD behavior, sticky navigation, and touch targets. The v7.0.7 help addition reuses the existing responsive help section and introduces no new layout pattern.
- Existing accessibility guards cover semantic dialog naming, initial dialog focus, focus trapping and return, keyboard dismissal, accessible numeric errors, disabled controls, visible focus behavior, and text-based operative status. Eliminated NPOs retain the `ELIMINATED` status text and wounds value in addition to the red border and skull overlay; no NPO image or obsolete alt text was added.
- A graphical browser/screenshot tool is not installed in the validation environment, so fresh interactive screenshots and device emulation could not be captured. This is an environment limitation rather than a known application defect; responsive and accessibility conclusions are based on the complete repository regression suite and focused source validation.

## Offline, PWA, console, and network

- JavaScript syntax checks pass for the app, persistence layer, mission engine, and service worker.
- Every literal service-worker precache path exists. Local HTTP checks return 200 for the app shell, versioned app script, service worker, manifest, mission manifest, representative map, and eliminated-NPO icon.
- Service-worker tests cover installation precaching, versioned cache naming, activation cleanup, required mission/player assets, and absence of removed portrait/Matrix asset requests. Version 7.0.7 changes the cache name according to the existing update convention.
- No runtime browser is installed in the validation environment, so an interactive browser-console inspection and DevTools offline toggle were not available. Automated syntax, asset, service-worker, accessibility, state-transition, and network-path tests reported no exceptions or missing required assets.

## Commands and results

```text
pytest -q
307 passed in 4.11s (before changes)

python3 -m unittest discover -s tests -v
314 tests passed (after changes)

node --check app.js
node --check persistence.js
node --check mission-engine.js
node --check service-worker.js
all passed

python3 -m http.server 8765
curl checks for shell, scripts, manifest, mission data, map, and status icon
all returned HTTP 200
```

## Release confirmations and limitations

- Exactly seven NPO types remain active; retired or unknown types cannot enter new active gameplay.
- User-facing NPO lists remain alphabetical with natural instance-number ordering.
- NPO portraits remain removed; player-operative portraits are unchanged.
- The Obelisk Node Matrix remains unsupported and has no active rule, UI, serialized state, or asset request.
- Legacy migration remains deterministic, cancelable, and idempotent. Player-operative behavior is unchanged.
- The application, cache, visible badge, and asset query strings display version 7.0.7.
- No gameplay feature is deferred. Interactive device screenshots, real-browser console inspection, and a DevTools-controlled offline launch remain manual release checks because this environment has no graphical browser tooling.
