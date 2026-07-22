# Mission content

The existing numbered mission files contain the mission-pack content used by the current application. Generic Mission Objective Engine definitions use the `definition-*.json` prefix and are listed in the `definitions` array in `manifest.json`.

## Architecture and lifecycle

`manifest.json` is the static registry used by GitHub Pages. `mission-engine.js` loads and validates a registered definition before creating its small runtime state; `app.js` supplies lifecycle context, dice/input services, HUD and dialogs; and `persistence.js` preserves that runtime with the rest of the save. Definitions remain declarative: JSON contains data and supported operation names, never executable code.

The application initializes a selected automated mission once, then calls named hooks at gameplay boundaries. An event is validated before execution, runs its operations transactionally, records history and any execution key, updates the derived HUD/details models, and is saved through the normal save path. Mission-objective completion is idempotent and does not end the battle through the Mission Engine.

## Validation and migration

Loading parses JSON, checks schema version 1 and required fields, validates objective/action/event uniqueness, supported hooks and operations, objective/dialog/event-result references, and registry-wide mission ID uniqueness. A failure raises a structured `MissionEngineError` with a code, source path and reason. The integration boundary logs a concise `[MissionEngine]` error, disables automation, and leaves tabletop play and unrelated game state available.

Unknown additional properties are retained for forward-compatible descriptive metadata, but unknown hooks, operations, schema versions, and references are rejected because they could change behavior. Empty objective, action, event, and dialog collections are valid.

Save migration first preserves and normalizes the whole game state. The engine then rebuilds a runtime from the current definition, restores matching known objectives with current clamping rules, retains completion markers, history and idempotency keys, and ignores invalid objective values without discarding unrelated saved data. A missing, mismatched, or unusable mission runtime is initialized safely from definition defaults.

## Add a definition

1. Copy `MissionTemplate.json` to a lowercase, stable `definition-*.json` name.
2. Assign a unique string `id` (retain leading zeroes) and lowercase hyphenated `slug`.
3. Add its path to the `definitions` array in `manifest.json`. The registry rejects duplicate IDs after loading all registered definitions.
4. Describe objectives, actions, hooks, and presentation using data only. Executable JavaScript, HTML, `eval`, and function bodies are prohibited.
5. Validate the JSON syntax and contract against `mission.schema.json`, then run `python -m unittest discover -s tests -p 'test_*.py'`.
6. Confirm every referenced objective, dialog, input and result exists earlier in its event; keep action IDs unique among actions and lifecycle-event IDs unique across hooks.
7. Verify keyboard/dialog behavior, a 390px viewport, save/resume, lifecycle idempotency, and that objective completion continues the battle.

The initial engine supports counter and boolean objectives; safe `all`, `any`, and `not` conditions; comparisons; the `add`, `subtract`, `multiply`, `min`, and `max` expressions; and these operations:

- `setCounter`, `addCounter`, `subtractCounter`
- `setFlag`, `clearFlag`, `completeObjective`, `appendHistory`
- `requestDiceRoll`, `requestNumericInput`, `showDialog`

D6 is the only supported die. The application must supply UI services for request operations when later lifecycle packages integrate a definition. Add an engine capability before authoring content that needs another objective type, hook, expression, die, or operation. Do not encode unsupported behavior in display text or create mission-specific JavaScript.

`fixtures/future-mission.json` is test-only proof that another mission using existing operations requires no engine change. It is intentionally absent from the production definition registry and mission selection.

## Testing strategy

Automated tests execute the engine with deterministic services and cover loading/validation, counters and completion, rollback and lifecycle idempotency, HUD/details models, persistence/migration, Ready Step and Strategy Phase integration, reinforcement regression, repeated rendering, invalid/missing data, and forward-compatible properties. Manual acceptance plays Mission 04 from initialization through all Turning Points, refreshing and resuming at each point, then completes the objective and confirms the battle remains active. Browser QA also checks console output, focus trap/restoration, Enter/Space/Escape, announcements, reduced motion, tap targets and narrow/mobile layouts.
