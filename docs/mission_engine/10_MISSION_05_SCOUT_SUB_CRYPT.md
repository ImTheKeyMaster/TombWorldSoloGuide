# Mission 05 — Scout Sub-Crypt (v6.4.0)

## Rules authority

The implementation follows the repository's official `Assets/Tomb-World-Mission-Pack.pdf` (Games Workshop, Joint Ops: Tomb World Mission Pack, revision recorded in `Missions/manifest.json`) and the structured Mission 05 content in `Missions/05-scout-sub-crypt.json`.

## Definition and lifecycle

`Missions/definition-05-scout-sub-crypt.json` registers one authoritative `scoutedRooms` counter (0–5, target 3) and three actions:

- `awakenRoom` uses the shared animated D3 service. The existing, mission-configured Scout Sub-Crypt handler adds current Threat Grade, caps the result at five, creates Ready NPOs with Conceal orders, and requires placement confirmation. A room can awaken only once because its persisted room record removes the action.
- `recordScout` records one cleared eligible room after the player confirms the tabletop conditions for the 1AP Scout Room action. The handler applies the printed Threat reduction to the highest Threat level of the grade below.
- `correctScout` removes an incorrectly recorded room without replaying room awakening or reversing an already-resolved tabletop Threat change.

Mission 05 has no automatic lifecycle hooks. Its rules resolve during setup, first room opening/entry, and the Player operative action. Reaching three distinct scouted room IDs ends the battle with victory through the existing mission outcome flow. Total Player incapacitation remains the existing defeat path.

## State and restoration

The persisted `missionState` remains authoritative for named rooms (`awakenedRooms` and distinct `scoutedRoomIds`). The Mission Engine runtime is synchronized from the distinct room IDs when loaded, preventing its counter from drifting from named-room state. The runtime supplies HUD, Mission Details, history, completion metadata, and dice history. Pending uncommitted rolls are not serialized and safely retry after refresh; committed room and runtime state restore through the normal save path.

Room actions apply only to the five eligible non-drop-zone room records in mission configuration. NPO creation respects the existing battlefield maximum. Scout eligibility is confirmed by the player because the app cannot determine tabletop room boundaries or control automatically. Operative activation availability continues to use existing in-play, living, and Ready selectors; Mission 05 does not derive battlefield eligibility from the full selected roster.

## Engine Enhancements

Engine Enhancements: None.

Mission 05 uses the existing counter, animated D3, history, HUD/details, completion, validation, transaction, and restoration capabilities. Its already-isolated `scout` mission configuration owns the tabletop room and NPO placement workflow, so no generic Mission Engine behavior or schema changed.

## Verification scope

Automated coverage validates the definition, registry/offline registration, initialization, D3 range enforcement and rollback, counter bounds, correction, completion, HUD/details/history, restoration from malformed runtime values, lifecycle no-ops, and release version consistency. Missions 01–04 remain unchanged and are covered by their existing regression suites.
