# Mission content

The existing numbered mission files contain the mission-pack content used by the current application. Generic Mission Objective Engine definitions use the `definition-*.json` prefix and are listed in the `definitions` array in `manifest.json`.

## Add a definition

1. Copy `MissionTemplate.json` to a lowercase, stable `definition-*.json` name.
2. Assign a unique string `id` (retain leading zeroes) and lowercase hyphenated `slug`.
3. Add its path to the `definitions` array in `manifest.json`. The registry rejects duplicate IDs after loading all registered definitions.
4. Describe objectives, actions, hooks, and presentation using data only. Executable JavaScript, HTML, `eval`, and function bodies are prohibited.
5. Validate the JSON syntax and contract against `mission.schema.json`, then run `python -m unittest discover -s tests -p 'test_*.py'`.

The initial engine supports counter and boolean objectives; safe `all`, `any`, and `not` conditions; comparisons; the `add`, `subtract`, `multiply`, `min`, and `max` expressions; and these operations:

- `setCounter`, `addCounter`, `subtractCounter`
- `setFlag`, `clearFlag`, `completeObjective`, `appendHistory`
- `requestDiceRoll`, `requestNumericInput`, `showDialog`

D6 is the only supported die. The application must supply UI services for request operations when later lifecycle packages integrate a definition. Add an engine capability before authoring content that needs another objective type, hook, expression, die, or operation. Do not encode unsupported behavior in display text or create mission-specific JavaScript.

`fixtures/future-mission.json` is test-only proof that another mission using existing operations requires no engine change. It is intentionally absent from the production definition registry and mission selection.
