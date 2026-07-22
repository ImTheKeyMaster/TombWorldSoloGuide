# Work Package 03 — Implement Mission 04: Destroy Sarcophagus

## Goal

Implement Mission 04 entirely through its JSON definition and the generic Mission Objective Engine.

Mission 04 must be the reference proving that future missions can use existing engine capabilities without mission-specific application code.

## Objective

Track **Destruction Points** from 0 to 20.

- Initial value: 0
- Minimum: 0
- Maximum: 20
- Target: 20
- Lock at 20 after completion
- Display 20 as complete
- Objective completion does not automatically end the battle

## Breach Sarcophagus action

### Availability

The mission action is available only while the objective is incomplete.

Do not display or enable it after completion.

The app cannot reliably know tabletop geometry or every legal-action condition unless that information is already tracked. Present the action as a tabletop-confirmed mission action.

Recommended UI wording:

```text
Breach Sarcophagus
Confirm that the operative can perform this mission action, then roll 2D6.
```

### Execution

When the user confirms Breach Sarcophagus:

1. prevent duplicate taps while the action is resolving;
2. use the shared animated dice implementation to roll two D6;
3. show both individual dice and the total;
4. add the total to Destruction Points;
5. clamp the resulting value at 20;
6. evaluate objective completion;
7. add a mission history entry;
8. update the Mission HUD immediately;
9. show a result dialog;
10. save the updated mission runtime through the normal persistence flow.

Example result:

```text
BREACH SARCOPHAGUS

Dice: 5 + 4
Destruction Points added: 9

Progress: 11 / 20
```

Do not require the user to manually enter the dice result.

### Completion during breach

When the breach roll reaches or exceeds 20:

1. set Destruction Points to exactly 20;
2. mark the objective complete;
3. record the current Turning Point;
4. record a timestamp or sequence marker;
5. lock the objective from later subtraction;
6. stop future Nanoscarab Repair events;
7. remove or disable Breach Sarcophagus;
8. change the HUD to `✓ COMPLETE`;
9. show the completion dialog;
10. continue normal gameplay.

Completion dialog:

```text
MISSION OBJECTIVE COMPLETE

Destroy Sarcophagus

20 / 20 Destruction Points

Continue the battle.
```

Do not navigate to Victory.

## Nanoscarab Repair

### Timing

Run at the Mission 04 Ready-step timing specified by the mission rules. Integrate it into the existing Strategy Phase flow without adding a redundant permanent screen.

The event must execute once per Turning Point at most.

If the Strategy Phase screen re-renders, the browser refreshes, or the user navigates backward and forward, do not roll again for the same Turning Point.

### Availability

Skip the repair event when:

- Destruction Points are 0;
- the objective is complete;
- the event already resolved for the current Turning Point.

A skipped event should not display a disruptive dialog. It may be logged only when useful for debugging.

### Controller input

Before rolling, request the number of Player operatives controlling the Sarcophagus, because the app cannot determine tabletop control range automatically.

Use a compact generic numeric input dialog.

Requirements:

- integer only;
- minimum 0;
- reasonable maximum based on Player roster size or a safe fixed maximum;
- default 0;
- Cancel must not mark the event resolved;
- confirmation proceeds to the dice animation.

Suggested wording:

```text
NANOSCARAB REPAIR

How many Player operatives currently control the Sarcophagus?
```

### Repair calculation

1. Roll one animated D6.
2. Read the number of controlling Player operatives.
3. Calculate:

```text
Repair amount = max(0, D6 roll - controlling Player operatives)
```

4. Subtract the repair amount from Destruction Points.
5. Clamp at 0.
6. Add a history entry.
7. Mark this repair event resolved for the current Turning Point.
8. update HUD and mission details immediately;
9. save state;
10. show the result dialog.

Example:

```text
NANOSCARAB REPAIR

Repair roll: 5
Player operatives controlling: 2
Destruction Points repaired: 3

Progress: 8 / 20
```

If the calculated repair amount is 0, use clear language such as:

```text
No Destruction Points repaired.
```

Do not use ambiguous wording like `No damage inflicted`.

### Repair after completion

Never reduce the counter after completion. Once complete, Mission 04 stays complete.

## Mission history

Use concise entries such as:

- `Breach Sarcophagus: rolled 9; progress increased from 2 to 11.`
- `Nanoscarab Repair: rolled 5, minus 2 controlling operatives; progress decreased from 11 to 8.`
- `Objective completed during Turning Point 3.`

Store structured details, but render readable summaries.

## Edge cases

Handle all of the following:

- Breach action tapped repeatedly.
- User closes or cancels confirmation before rolling.
- Page refresh occurs after dice are shown but before state persistence.
- Counter is 18 and a 7 is rolled: store 20, not 25.
- Repair would reduce below zero: store 0.
- Controller count exceeds roll: repair amount is 0.
- Completion occurs during a resumed save.
- Old save has mission ID 04 but no mission runtime.
- Repair hook fires twice in the same Turning Point.
- Mission definition fails to load.
- Dice animation is unavailable due to a recoverable rendering error.

For a recoverable dice rendering failure, do not silently invent a result. Display a clear error and allow retry.

## No automatic victory

This is mandatory:

```text
Objective complete != battle won
```

Only the app's official battle-end flow may show Victory or Loss. The mission definition field `endsBattle` is false.

## Tests

Add deterministic tests for:

- breach roll 2 + 3 adds 5;
- breach clamps at 20;
- completion triggers once;
- completion does not trigger Victory;
- repair 5 minus 2 subtracts 3;
- repair 2 minus 4 subtracts 0;
- repair clamps at zero;
- repair runs once per Turning Point;
- repair skipped at zero;
- repair skipped after completion;
- action unavailable after completion;
- history entries contain correct before/after values.
