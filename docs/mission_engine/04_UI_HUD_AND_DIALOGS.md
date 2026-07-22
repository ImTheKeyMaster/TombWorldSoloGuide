# Work Package 04 — Mission HUD, Mission Details, and Result Dialogs

## Goal

Expose mission progress clearly without making gameplay screens longer or adding permanent large tracker cards.

## Mission HUD cell

Add one compact Mission cell to the existing HUD.

### In-progress appearance

```text
MISSION
11 / 20
```

### Complete appearance

```text
MISSION
✓ COMPLETE
```

### Behavior

- The entire cell is clickable/tappable.
- Use a semantic button or equivalent accessible control.
- It opens the Mission Details dialog.
- It must work with mouse, touch, Enter, and Space.
- It must not cause page navigation.
- It must match the existing HUD's visual language.
- It must fit on mobile without forcing excessive wrapping.
- The value must update immediately after mission events.
- Do not create duplicate Mission cells during re-rendering.
- Hide or show a neutral state when the selected mission has no automated definition, based on the best fit with current UX.

Recommended neutral behavior:

```text
MISSION
DETAILS
```

This can open the existing mission information if available. Do not imply automated progress for unsupported missions.

## Mission Details dialog

Create one reusable dialog, not a Mission 04-specific modal.

### Required contents

For Mission 04 while active:

```text
MISSION DETAILS

Destroy Sarcophagus

Objective
Accumulate 20 Destruction Points.

Progress
11 / 20

Recent Activity
• Breach Sarcophagus: +9
• Nanoscarab Repair: -3

[Close]
```

For completed state:

```text
MISSION STATUS

Destroy Sarcophagus

✓ Objective Complete

Completed during
Turning Point 3

Final Progress
20 / 20

Recent Activity
...
```

### Game Menu integration

Add a `Mission Details` entry to the existing Game Menu. It opens the same dialog as the HUD cell.

Do not duplicate separate dialog implementations.

### History

Show a short recent history list, such as the latest five entries.

- Newest first is preferred.
- If no events occurred, show a concise empty state.
- Do not expose internal IDs.
- Avoid overly technical timestamps.
- Include Turning Point where useful.

### Accessibility

The dialog must:

- use the app's existing accessible modal pattern if one exists;
- have an accessible name;
- trap focus while open;
- focus the title or first meaningful control on open;
- close with Escape unless a dice roll or state-changing operation is actively resolving;
- restore focus to the control that opened it;
- prevent background interaction;
- use semantic headings;
- use buttons rather than clickable divs;
- not rely on color alone.

### Mobile behavior

- Fit within the viewport.
- Allow dialog-body scrolling without nested page-scroll problems.
- Keep Close accessible.
- Avoid horizontal scrolling.
- Avoid full-width oversized empty spacing.
- Respect device safe areas where the current app already does so.

## Generic confirmation dialog

Mission actions may request confirmation.

Build or reuse a generic dialog that receives definition-driven:

- title;
- message;
- confirm label;
- cancel label.

For Breach Sarcophagus, confirmation occurs before dice are rolled.

Cancel returns to the previous screen/state and does not change mission state.

## Numeric input dialog

Build a generic numeric input dialog for mission-defined inputs.

Requirements:

- clear label;
- native numeric input where appropriate;
- plus/minus controls only if consistent with the app;
- integer validation;
- min/max validation;
- inline error message;
- Confirm disabled for invalid values;
- Cancel leaves the event unresolved;
- preserve the entered value only while the dialog remains open.

## Shared mission roll dialog

Mission rolls must use the shared animated dice system.

A generic roll flow should support:

1. title;
2. rule summary;
3. animated dice;
4. individual dice values;
5. total;
6. modifier inputs/results;
7. final effect;
8. resulting objective progress;
9. Continue.

Do not build a separate dice renderer exclusively for missions.

## Completion dialog

Use the exact behavioral distinction:

- title: `MISSION OBJECTIVE COMPLETE`
- identify the objective;
- show final progress;
- say `Continue the battle.`;
- Continue closes the dialog and returns to normal gameplay;
- do not show Victory controls;
- do not end the current activation unless official flow requires it.

## Rendering safety

- Treat all JSON text as plain text.
- Do not inject JSON content with unsanitized `innerHTML`.
- Keep icons controlled by known keys, not arbitrary markup.

## Visual density

The user has repeatedly preferred compact screens.

Therefore:

- no permanent mission tracker card;
- no redundant explanatory card when the dialog already explains the roll;
- concise headings;
- compact vertical spacing;
- avoid repeating mission name in every card;
- do not add `Next:` cards;
- do not add redundant banners.

## UI tests

Test:

- HUD renders active progress;
- HUD renders complete state;
- HUD opens dialog;
- Game Menu opens the same dialog;
- dialog focus and Escape behavior;
- recent history empty state;
- result dialog values;
- completion dialog does not navigate to Victory;
- small mobile viewport;
- long mission/objective text wrapping;
- repeated re-render does not duplicate event listeners.
