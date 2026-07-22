# Work Package 07 — Validation, Error Handling, Accessibility, and Resilience

## Goal

Make the mission system safe, understandable, and robust under invalid data, interrupted flows, and mobile usage.

## Definition validation

Validation must occur before mission runtime initialization.

Produce structured errors with:

- mission path;
- mission ID when available;
- failing property;
- reason;
- unsupported value.

Console example:

```text
Mission definition validation failed:
Missions/04-Destroy-Sarcophagus.json
actions[0].operations[1].type: unsupported operation "addPoints"
```

Do not expose stack traces in ordinary user dialogs.

## User-facing load failure

If a selected mission definition cannot load:

- do not blank the app;
- do not trap the user on a spinner;
- allow gameplay to continue without automation when safe;
- show a concise message through the app's standard notification/dialog pattern.

Suggested:

```text
MISSION AUTOMATION UNAVAILABLE

The mission rules could not be loaded. You can continue the game, but mission progress will need to be tracked manually.
```

Provide Retry only if retry is meaningful.

## Dice errors

If shared dice animation fails:

- do not fabricate a roll;
- do not commit mission state;
- clear resolving lock;
- show a retryable error;
- avoid duplicate commits if the visual animation fails after a result was already finalized.

Structure dice service so result generation and display have a clear transaction boundary.

## Numeric input validation

- integer-only where specified;
- no blank confirmation;
- enforce min/max;
- prevent scientific notation if inappropriate;
- trim pasted input;
- do not coerce invalid text to 0 silently;
- use an inline accessible error.

## Accessibility

### HUD

- semantic button;
- accessible name including mission and status;
- visible focus state;
- no color-only completion indicator.

Example accessible label:

```text
Mission details, Destroy Sarcophagus, 11 of 20 Destruction Points
```

### Dialogs

- `role="dialog"` or native dialog pattern consistent with the app;
- `aria-modal="true"` where applicable;
- labelled by visible title;
- focus trapped;
- focus restored;
- Escape behavior;
- background inert/disabled;
- screen reader announcement after dice and progress update.

### Dice animation

Respect `prefers-reduced-motion`.

Reduced-motion mode may show a short static transition, but must still reveal the dice values clearly.

Do not make the user wait through a long animation.

### Touch

- controls meet reasonable touch target size;
- avoid adjacent destructive/confirm buttons too close together;
- prevent double-tap duplicate submission;
- test iOS Safari and narrow portrait layout.

## Error boundaries

A mission-engine error should not destroy:

- roster;
- activation state;
- Turning Point;
- combat state;
- threat/grade;
- deployment state;
- save data.

Wrap mission hook execution at integration boundaries.

## Logging

Use concise prefixed logging, for example:

```text
[MissionEngine]
```

Avoid verbose logs in production unless debug mode exists.

Never log sensitive data; none is expected here.

## Fallback behavior

When mission automation is unavailable:

- hide automated mission actions;
- show neutral mission information;
- avoid fake 0/20 progress that could be mistaken for real saved state;
- permit manual tabletop play.

## Accessibility and resilience tests

Test:

- keyboard-only HUD/dialog use;
- Escape;
- focus restoration;
- reduced motion;
- invalid numeric input;
- rapid double tap;
- failed JSON fetch;
- invalid JSON;
- unsupported operation;
- dice rendering failure;
- mission error while rest of app remains usable;
- narrow mobile viewport;
- orientation change.
