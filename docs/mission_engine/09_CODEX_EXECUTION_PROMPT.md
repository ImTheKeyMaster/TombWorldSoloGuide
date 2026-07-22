# Codex Execution Prompt

Read `00_READ_FIRST.md` and every numbered work package in this directory before editing code.

Implement the v6.0.0 Mission Objective Engine exactly as specified.

## Execution rules

- Inspect the current repository and adapt file names to its architecture.
- Preserve existing behavior and styling unless a package explicitly changes it.
- Do not implement unrelated improvements.
- Do not hard-code Mission 04 calculations across unrelated files.
- Do not put executable code in JSON.
- Reuse the existing animated dice implementation.
- Do not treat objective completion as battle victory.
- Keep gameplay screens compact.
- Add tests as work is implemented.
- Run all available tests before opening a pull request.
- If the repository conflicts with a requirement, stop and explain the conflict rather than silently changing the intended behavior.

## Recommended implementation order

1. Work Package 01 — Mission Engine Foundation
2. Work Package 02 — JSON Definitions and Schema
3. Work Package 03 — Mission 04
4. Work Package 04 — HUD and Dialogs
5. Work Package 05 — Lifecycle Integration
6. Work Package 06 — Persistence and Versioning
7. Work Package 07 — Validation and Accessibility
8. Work Package 08 — Testing and Acceptance

For a single PR, implement all packages and keep commits logically separated.

For phased PRs, implement only the assigned package(s) and do not begin later packages.

## Pull request title

```text
v6.0.0: Add data-driven Mission Objective Engine
```

## Pull request summary

```text
Introduce a reusable data-driven Mission Objective Engine with JSON mission definitions, generic counters and lifecycle hooks, shared animated dice integration, a compact Mission HUD, reusable Mission Details and result dialogs, save/load migration, validation, and automated tests. Mission 04 (Destroy Sarcophagus) is implemented as the reference mission. Objective completion is tracked independently from battle victory.
```
