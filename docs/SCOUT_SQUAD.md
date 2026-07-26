# Scout Squad Player Kill Team

## Authoritative sources

The implementation uses only the repository PDFs `Scout Squad - Datacards.pdf`, `Scout Squad - Faction Rules.pdf`, and `Scout Squad - Operative Selection.pdf`. All 7 datacard pages, all 5 faction-rule pages, and the single operative-selection page were reviewed.

## Team definition and roster rules

`Player_Operatives/ScoutSquad.json` uses stable IDs for the team, operatives, weapons, abilities, faction rules, and Strategic Gambits. A legal roster contains exactly nine operatives: exactly one Scout Sergeant plus eight selections from Heavy Gunner, Hunter, Sniper, Tracker, and Warrior. Hunter, Sniper, and Tracker are unique. The Heavy Gunner's heavy-bolter and missile-launcher choices are mutually exclusive. Eight numbered Warrior slots permit the only repeated operative type, and each slot permits exactly one of its shotgun, boltgun, or bolt-pistol-and-combat-blade loadouts. The Sergeant similarly permits exactly one of its three official loadouts.

Distinct datacard profiles remain distinct weapon entries. Heavy bolter focused/sweeping, missile launcher frag/krak, and sniper rifle mobile/stationary therefore use the generic multi-profile selector. Blast and Torrent profiles use the existing manual tabletop-resolution guidance and tell the player to record affected wounds or elimination in the appropriate roster.

## Faction rules and operative guidance

Forward Scouting and each option are definition metadata with official selection maxima and timing. Tactical Manoeuvre and Diversion appear as Strategy Phase reminders with twice-per-battle and once-per-battle usage metadata. Trip Alarm includes its Turning Point 3 removal reminder. Position-, range-, terrain-, visibility-, control-range-, marker-, enemy-, and CP-dependent decisions remain manual tabletop guidance because the Guide does not know those battlefield facts.

Every operative ability and unique action is shown on its Player Roster card. Guidance and Experience, Adaptive Equipment, Tactical Manoeuvre, and Diversion retain their usage-limit metadata. The app does not add interactive action controls because it does not track Player AP, orders, CP, exact positions, targets, terrain, universal equipment, or marker placement; a checkbox would imply enforcement the engine cannot reliably provide.

## Save and restoration

The existing persistence layer stores the selected team/file, stable roster IDs, wounds, casualties, activation IDs, off-board state, and in-progress combat state. Scout Squad uses those same fields without a save-schema change. Definition metadata is reloaded deterministically, so derived stats, profiles, rule text, and usage declarations are not duplicated into saves. Existing saves for Deathwatch, Tempestus Aquilons, and Spectre Squad remain compatible.

## Engine Enhancements

**Engine Enhancements: None.**

Scout Squad is fully represented by the established category requirements, category maxima, selection groups, stable-ID validation, ranged/melee filtering, multi-profile selection, manual multi-target guidance, roster state, and persistence capabilities. No team-name branch or Scout-Squad-specific gameplay handler was required.

## Known limitations

The Guide presents but does not simulate Forward Scouting choice accounting, marker position/removal, CP changes, APL modifiers, orders, control range, visibility, obscuring, cover, terrain movement, grenade actions, or attack-die re-roll eligibility. Players resolve those rules on the tabletop and update wounds or elimination in the Player or NPO Roster. Limited-use metadata survives because it is authoritative definition data; the app does not maintain a separate usage counter where it cannot validate the tabletop trigger.
