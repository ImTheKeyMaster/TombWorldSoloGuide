# Spectre Squad Player Kill Team

## Authoritative repository sources

The implementation was transcribed from every page of `Spectre Squad - Datacards.pdf` (15 pages), `Spectre Squad - Faction Rules.pdf` (6 pages), and `Spectre Squad - Operative Selection.pdf` (2 pages). No external rules source was used.

## Team definition and roster rules

`Player_Operatives/SpectreSquad.json` defines the mandatory Veteran Sergeant and Vox-Relay Beacon, plus nine selections from the specialist and Trooper list. Every non-Trooper type is unique. The Gunner weapon options and each Lascarbine/Lasrifle loadout are mutually exclusive through stable `selectionGroup` metadata; nine numbered Trooper slots express the only repeatable operative type without losing stable save identifiers.

Operative entries contain stable IDs, printed characteristics, separately selectable ranged and melee profiles, weapon rules, abilities, unique actions, conditional restrictions, keywords, and faction guidance. Alternate profiles such as plasma, missile launcher, long-las, and autostubber profiles remain separate weapons in combat selection.

## Faction rules and operative guidance

Elite Fieldcraft is shown during the Strategy Phase and in team-rules views. Its Ready Step resource generation and end-of-turn discard are lifecycle reminders; interruption eligibility, positioning, target, order, movement, and point-blank restrictions remain explicit tabletop guidance because the Guide does not track geometry, visibility, control range, or orders. Camo Cloaks is manual combat guidance because cover and Vantage conditions require tabletop judgment.

Datacard abilities and actions are displayed on the appropriate operative cards. The Guide does not add AP buttons for purely informational rules. Medic!, Medikit, Melta Mine, Proximity Mine, Scout Terrain, Load Weapon, Signal, Issue Mission, Concealed Position, Cool-Headed, and related effects are resolved at the table, then wounds, elimination, or off-board state are recorded using existing roster controls. This avoids unreliable automation of visibility, ranges, orders, action history, and terrain.

## Save and restoration

Spectre Squad uses the existing Player Kill Team state: the selected variant IDs preserve roster and loadouts; wounds, casualties, activation, in-play state, and combat drafts persist through the established save/export/import pipeline. No migration is required. Missing maps normalize through existing state defaults, while derived operative statistics and weapons reload from the team definition.

## Engine Enhancements

### Mutually exclusive selection groups

Spectre Squad requires multiple official loadout choices for the same operative and two exclusive Gunner options. The generic `selectionGroup` plus `selectionGroupMax` metadata lets any team declare mutually exclusive roster entries. Validation, disabled setup choices, direct selection, and random roster generation all use the same metadata. Spectre Squad tests cover legal and conflicting groups independently of display names.

### Player team definition validation

The loader now rejects duplicate operative IDs, unknown roster categories, invalid weapon types, and duplicate declared weapon IDs. This is generic fail-visible protection for all team definitions and is covered by source-level and data validation tests.

### Multi-weapon placeholder

The generic combat picker now begins with “Select a weapon...” when multiple valid profiles exist. Continue remains disabled and no dice are rolled until a profile is selected. Single-profile automatic selection and rolling are unchanged.

## Known limitations

The Guide cannot determine battlefield position, visibility, cover, Vantage, control range, orders, terrain geometry, marker placement, or whether a physical action has already occurred. Elite Fieldcraft, Camo Cloaks, blast/torrent secondary targets, mines, grenades, healing dice, and limited-use datacard conditions therefore remain clear manual guidance. After multi-target or mine resolution, update every affected Player or NPO through the appropriate roster before resuming the activation.
