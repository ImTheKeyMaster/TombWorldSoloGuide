# Official Rules Compliance Audit Review

## Purpose

This document independently reviews the findings in `docs/OFFICIAL_RULES_COMPLIANCE_AUDIT.md` against the now-valid official *Joint Ops: Tomb World Mission Pack*. It is an audit of that audit: it recommends future corrections but changes no application behavior. Repeated “Critical findings” rows in the original are the same IDs later expanded in their subject sections, so each ID is reviewed once below rather than counted twice.

## Sources Reviewed

- `Assets/Tomb-World-Mission-Pack.pdf` — primary authority for Tomb World rules. It is a valid 22-page PDF, contrary to the original audit's obsolete statement that it was SVG markup. Viewer page references below are used because the rules pages do not show a consistently extractable printed page number. PDF pages 1–19 contain the mission-pack rules, datacards, missions, Adversary Ops rules, and maps; PDF pages 20–22 contain the Tomb World Event cards.
- `docs/OFFICIAL_RULES_COMPLIANCE_AUDIT.md` — every unique scorecard finding (57), the six abstraction/house-rule entries, the critical-summary duplicates, appendices, and remediation claims were reviewed.
- Current application evidence, where needed: `app.js`, `Missions/*.json`, `Player_Operatives/*.json`, `service-worker.js`, and the mission manifests/maps.

The PDF expressly refers some subjects to the separate Kill Team Core Book and individual kill-team rules. Where the mission pack does not state the underlying rule, this review does not use general Kill Team knowledge to fill the gap.

## Executive Summary

The original audit correctly identified many major application gaps, especially universal NPO-elimination victory, display-only mission rules, generic NPO behavior, incomplete combat profiles, and missing event effects. Its central evidence premise, however, is now false: the repository contains a valid official PDF. Direct review materially changes several conclusions.

Most importantly, the official pack specifies a deck and redraw procedure, not a uniform six-result table; contains substantially more event cards than the six represented in code; requires one event draw only after Turning Point 1 at Grade 3 and a second draw when the NPOs lack initiative or Threat is 15; resolves event cards before Grade-based reinforcements; makes Threat 0 NPOs dormant and gives the players automatic initiative; and provides operative-specific ordered behaviors. The app omits or contradicts each of those rules. Conversely, reinforcement quantity equal to Grade, use of the same 2D6 NPO table, a recommended ten-NPO limit, and ready event arrivals in specified cases are directly supported by the pack, so portions of the original reinforcement findings were overstated.

The original audit also treated some matters outside the mission pack—core Fight mechanics, generic cover rules, current team datacards, and cache integrity—as if the newly supplied PDF could certify them. Those remain **Unable to Verify** from this authoritative Tomb World source, even where the code concern appears plausible. This status does not declare the implementation correct; it means this PDF does not establish the rule.

## Review Method

1. Verified the asset signature and opened all 22 PDF pages, including the rules, all six mission pages, NPO datacards/behavior lists, maps, and event-card sheets.
2. Enumerated all unique finding IDs and all intentional-abstraction/house-rule entries in the original audit. Duplicate critical-summary rows were traced to their later identical IDs.
3. For each rules claim, identified whether the PDF states the rule directly, delegates it to another publication, or is silent.
4. Inspected the cited current code and data rather than relying on the original audit's application description.
5. Applied the requested statuses strictly. “Unable to Verify” is used where the mission pack is not sufficient, even if a separate Core Book or team publication could resolve the issue.
6. Reassessed severity using Critical/High/Medium/Low/Informational rather than preserving the original P0–P3 labels.

## Finding-by-Finding Review

### SET-01 — Six missions and killzone layouts

**Original audit conclusion:**
The app compliantly loads all six missions and requires a map/setup confirmation.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 1, “Missions”; PDF page 8, “Game Sequence — Set Up the Battle”; PDF pages 9–14, Missions 1–6; PDF pages 17–19, “Mission Maps.”

**Application evidence:**
`Missions/manifest.json`; `loadMissionPack()` and setup checklist rendering in `app.js`.

**Review:**
The pack directly says there are six missions and six maps and permits selecting or randomizing each. The manifest has six missions and the setup UI requires map confirmation. This confirms only inventory/workflow, not geometric accuracy.

**Corrected conclusion:**
The finding is correct; no compliance defect is established (Informational).

**Recommended action:**
None for this finding; map accuracy remains separately reviewable.

### SET-02 — Beginning at Turning Point 1

**Original audit conclusion:**
The app compliantly starts at Turning Point 1 after setup.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 8, “Play the Battle,” which directly gives the players initiative in the first turning point; PDF page 2, event timing “after the first.”

**Application evidence:**
Setup stores `turningPoint: 0`; `startTurningPoint()` increments it; `rollInitiative()` assigns the player in Turning Point 1.

**Review:**
The pack assumes the standard turning-point sequence and explicitly defines first-turn initiative. The app enters Turning Point 1 consistently.

**Corrected conclusion:**
Confirmed; no defect (Informational).

**Recommended action:**
None.

### SET-03 — Player kill-team selection

**Original audit conclusion:**
Selection is only partial because not all team selection rules or Joint Ops team-size adjustments are enforced.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 1, “Kill Team Selection”; PDF page 8, “Select Operatives.” The direct rule is: solo selects a kill team normally; co-op may split one team or take half of separate teams. Team legality is delegated to each kill team's own rules.

**Application evidence:**
`playerRosterLimits`, `autoSelectRequiredPlayerOperatives()`, setup selection handlers in `app.js`, and `Player_Operatives/*.json` selection data.

**Review:**
The application is a solo guide, so the original emphasis on an unimplemented co-op adjustment overstates the relevant scope. The PDF does confirm normal legal selection, but it does not contain Death Korps, Deathwatch, or Kasrkin selection requirements, so it cannot prove every claimed enforcement gap.

**Corrected conclusion:**
Normal team legality remains only partially automated; co-op half-team selection is outside the app's stated solo scope. Medium severity for any supported illegal solo roster, otherwise Informational.

**Recommended action:**
Audit each supported team's external official selection rules separately and clearly scope co-op as unsupported.

### SET-05 — Starting NPO generation table

**Original audit conclusion:**
The hard-coded 2D6 starting table was unverifiable.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 5, “NPO Datacards,” 2D6 NPO table and “use the next row” substitution rule; PDF page 8, “Set Up Operatives.”

**Application evidence:**
`generateRoster()` in `app.js`, especially its 11-element `table`.

**Review:**
The conclusion that verification was impossible is obsolete: the official table is present. The app distinguishes four broad types but does not retain the PDF's required ranged-weapon variant for Warriors, Macrocytes, and Tomb Crawlers. The code's total-12 fallback to Warrior also does not model “next row” substitution when a required miniature is unavailable. Exact row probabilities should be transcribed from the table rather than inferred from type names alone.

**Corrected conclusion:**
The table is now verifiable and the app's generated result lacks required weapon-variant identity; this is a High compliance issue. The original “unverifiable” classification was too weak.

**Recommended action:**
Encode every printed 2D6 row and its weapon option, plus the printed unavailable-miniature substitution.

### SET-06 — Mission setup precision and map geometry

**Original audit conclusion:**
Mission placement and geometry were unverifiable because the local PDF was allegedly invalid.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 9–14, each mission's “Mission Rules — NPOs/Objectives”; PDF pages 17–19, maps.

**Application evidence:**
`Missions/01-*.json` through `06-*.json`, `Assets/Maps/mission-*.png`, and the generic setup checklist in `app.js`.

**Review:**
The evidence limitation and recommendation to replace an invalid asset are false in the current repository. The official setup text and diagrams can be reviewed. The app summaries capture broad quantities, but generic confirmation does not enforce even distribution, room-specific placement, Conceal orders, or Mission 3 objective placement.

**Corrected conclusion:**
The source is valid; setup enforcement is partial, not unverifiable. Medium severity because tabletop confirmation can preserve correct play if the official page is consulted.

**Recommended action:**
Compare each map image and setup summary to PDF pages 9–14 and 17–19, and explicitly prompt all mission-specific placement conditions.

### STR-01 — Ready step

**Original audit conclusion:**
Living operatives are compliantly readied at Turning Point start, subject to reinforcement timing.

**Review status:**
Incorrect

**Official rule reference:**
PDF page 3, “Dormant NPOs”: at Threat 0 all NPOs are expended and cannot be readied; when Threat ceases to be 0, all are readied. PDF page 2 also places used-event-card recycling in the Ready step.

**Application evidence:**
`startTurningPoint()` calls `activeNpos().forEach(n => n.ready = true)` regardless of Threat and has no dormant rule.

**Review:**
The original overlooked a direct Tomb World exception. At the initial Threat 0, the app readies NPOs even though the pack forbids it.

**Corrected conclusion:**
Non-compliant; High severity because it changes who can activate.

**Recommended action:**
Implement dormant state and Threat-transition readiness exactly as PDF page 3 specifies.

### STR-02 — Ordered Strategy phase and mission hooks

**Original audit conclusion:**
The app mutates later Strategy results early and never resolves Mission 4 Nanoscarab Repair.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Tomb World Event Cards”; PDF page 3, “NPO Reinforcements”; PDF page 12, Mission 4 “Nanoscarab Repair.”

**Application evidence:**
`startTurningPoint()` in `app.js`; Mission 4 JSON `Nanoscarab Repair` prose.

**Review:**
The pack directly sequences event-card gambits before reinforcement gambits and places repair in the Ready step. The app immediately generates reinforcements, applies an event afterward, and has no repair dispatch.

**Corrected conclusion:**
Confirmed High issue; the exact code order is the reverse of the printed event/reinforcement order, in addition to missing mission timing.

**Recommended action:**
Stage Ready, event gambit(s), reinforcements, and initiative-facing UI in printed order, with Mission 4 repair at Ready.

### STR-03 — Event duration and cleanup

**Original audit conclusion:**
Temporary event state and expiry are missing.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Tomb World Event Cards” (ongoing cards last until end of turning point and used cards return in the next Ready step); PDF pages 20–22, including Countertemporal Shifting and Reanimation Protocols.

**Application evidence:**
`events`, `initialState()`, `applyStrategyEvent()`, and `startTurningPoint()` in `app.js`.

**Review:**
This is direct pack text. The app stores only the drawn event in transient strategy summary and has no active-effect/expiry/discard model.

**Corrected conclusion:**
Confirmed High issue.

**Recommended action:**
Persist active and used cards, apply printed duration, expire at end of turning point, and recycle used cards in the next Ready step.

### STR-04 — Initiative roll and overrides

**Original audit conclusion:**
The roll is partial because ties go to the player while unlimited rerolls and manual override are offered.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 2, “Strategy Phase” (NPOs choose initiative when they win); PDF page 3, “Dormant NPOs” (players automatically have initiative at Threat 0); PDF page 8 (players have first-turn initiative). The PDF does not state the core tie procedure.

**Application evidence:**
`rollInitiative()`, initiative summary UI, reroll and override handlers in `app.js`.

**Review:**
The PDF confirms two special cases the app only partly handles: first turn is correct, but Threat 0 automatic player initiative is missing after Turn 1. It does not establish tie or reroll rules, so those parts cannot be certified from this source.

**Corrected conclusion:**
Confirmed Medium Tomb World defect for Threat 0; tie/reroll claims remain Unable to Verify from this PDF.

**Recommended action:**
Force player initiative while Threat is 0; separately verify tie/reroll behavior against the Core Book.

### STR-05 — CP, equipment, ploys, and abilities

**Original audit conclusion:**
The app only provides a manual checklist and does not store CP or ploy state.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 8, “Select Operatives”: players select up to four equipment options and gain 2CP total; PDF page 2: NPOs gain no CP but use required Strategic Gambits.

**Application evidence:**
Strategy checklist and absence of CP/equipment state in `initialState()` in `app.js`.

**Review:**
The pack directly confirms the initial 2CP and four-equipment rules, which the app does not track. It does not require a guide to automate all player ploys, so lack of state is a compliance issue only where the app claims to resolve affected outcomes.

**Corrected conclusion:**
Partially confirmed; Low if clearly tabletop-delegated, Medium where automated calculations ignore selected effects.

**Recommended action:**
State the delegation clearly or track CP/equipment choices that affect automated results.

### STR-06 — Reinforcement/event order

**Original audit conclusion:**
The code order was unverifiable.

**Review status:**
Incorrect

**Official rule reference:**
PDF page 3, “NPO Reinforcements,” explicitly “after resolving Tomb World event cards”; PDF page 2, event Strategic Gambit.

**Application evidence:**
`startTurningPoint()` generates reinforcements before selecting/applying an event.

**Review:**
The source now directly resolves the uncertainty and shows the application order is wrong.

**Corrected conclusion:**
Confirmed High defect, not unverifiable.

**Recommended action:**
Resolve all required event draws first, then determine and place reinforcements using the resulting Threat/Grade.

### EVT-01 — Event eligibility, timing, and count

**Original audit conclusion:**
The app incorrectly makes one uniform Grade-3 draw every Strategy phase without full eligibility/timing.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Tomb World Event Cards.” Directly: only after the first turning point at Grade 3; draw twice if NPOs lack initiative or Threat is 15.

**Application evidence:**
`events` and `startTurningPoint()` (`if (grade===3)` one selection) in `app.js`.

**Review:**
The original issue is real. It should have stated the exact rule: the app can draw on Turning Point 1, never draws twice, and draws before initiative is chosen while failing to use the relevant initiative state.

**Corrected conclusion:**
Confirmed High issue with broader exact scope than originally stated.

**Recommended action:**
Gate to Turning Point 2+, implement the two independent second-draw conditions as a single additional draw, and sequence against initiative as the pack requires.

### EVT-02 — Completeness of event effects

**Original audit conclusion:**
Only some of six represented effects alter state; Maze and Countertemporal are text-only.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 20–22, all event cards, especially The Maze Reforms, Countertemporal Shifting, A Chittering Drone, and Living Metal Flux.

**Application evidence:**
`events`, `applyStrategyEvent()`, `resolveStrategyNpoEvent()` in `app.js`.

**Review:**
The represented effects are indeed incomplete, but the audit understated scope: the official sheets include additional cards absent from code, such as Subjugation Glyphs, Transdimensional Relocation, My Will Be Done, Reanimation Protocols, and Dark of the Tomb. Some app summaries also omit redraw conditions and exact placement.

**Corrected conclusion:**
Partially confirmed; High severity because multiple event outcomes materially change combat, APL, positioning, and activation.

**Recommended action:**
Inventory every printed card and implement or explicitly delegate every operative consequence and redraw condition.

### EVT-03 — Complete deck and weighting

**Original audit conclusion:**
The app's six unique objects might omit cards or weighting, but the official inventory was unavailable.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 20–22, physical event-card sheets; PDF page 2, shuffle/draw/reuse procedure. “Awakened Warrior” is printed more than once, establishing duplicate weighting.

**Application evidence:**
Six unique entries in `events`; random array sampling in `startTurningPoint()`; no deck/discard state.

**Review:**
The official source establishes a larger physical deck with additional titles and duplicate weighting. The app is not a complete representation.

**Corrected conclusion:**
Confirmed High issue; no longer merely “missing pending verification.”

**Recommended action:**
Represent every physical card instance (including duplicates) and deck/discard state.

### EVT-04 — Event placement, readiness, and blocked outcomes

**Original audit conclusion:**
Event NPOs are immediately ready/deployed without placement state; cap handling is incomplete.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 21–22, A Chittering Drone and Awakened Warrior. Both directly specify ready/Conceal placement; Awakened Warrior and other cards require drawing another card when impossible.

**Application evidence:**
`createNpo()`, `applyStrategyEvent()`, and `resolveStrategyNpoEvent()` in `app.js`.

**Review:**
Ready state is correct for those two cards, but `deployed:true` without the printed spatial constraints is insufficient, and Awakened Warrior silently does nothing at the limit rather than redrawing. Chittering Drone's printed branch depends on whether a swarm exists and is wounded, not a free user choice between add and heal.

**Corrected conclusion:**
Confirmed High issue, but the original suspicion about readiness itself was wrong; placement, branching, and redraw are the defects.

**Recommended action:**
Use source-specific mandatory branching, collect printed placement confirmation, and redraw when instructed.

### EVT-05 — Event titles and summarized effects

**Original audit conclusion:**
The six titles/effects were unverifiable.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 20–22, named event cards.

**Application evidence:**
`events` in `app.js`.

**Review:**
All six code titles appear in the official deck, but several summaries are materially incomplete: Stirrings has a Threat-15 alternative; Drone is conditional, not elective; Maze has a redraw condition; Awakened Warrior has exact placement/redraw rules; Countertemporal has a precise per-damage-die roll.

**Corrected conclusion:**
Titles are verified; effect summaries are partially compliant. Medium presentation/rule-guidance defect, rising to High where the app automates the wrong branch.

**Recommended action:**
Replace summaries with concise, complete paraphrases and typed effect metadata.

### EVT-06 — Reuse and reshuffle

**Original audit conclusion:**
Sampling with replacement might conflict with an unknown official mechanism.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Tomb World Event Cards”: used cards return to the deck in the Ready step of the following Strategy phase.

**Application evidence:**
`events[roll(events.length)-1]`; no deck, used-card, or discard state in `initialState()`.

**Review:**
The pack directly forbids immediate replacement within the turning point. This matters when two cards are drawn.

**Corrected conclusion:**
Confirmed Medium defect; original “unverifiable/low” assessment was too weak.

**Recommended action:**
Draw without replacement during a turning point and reshuffle used cards at the next Ready step.

### THR-01 — Threat starts at 0 and is bounded 0–15

**Original audit conclusion:**
Compliant.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Threat Level.”

**Application evidence:**
`initialState()` and `setThreat()` in `app.js`.

**Review:**
The PDF states this directly and the code initializes/clamps accordingly.

**Corrected conclusion:**
Confirmed; no defect.

**Recommended action:**
None, aside from import validation covered by THR-06.

### THR-02 — Grade thresholds

**Original audit conclusion:**
Threat 0 is Grade 0, 1–5 Grade 1, 6–10 Grade 2, and 11–15 Grade 3.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, Threat Level/Grade table.

**Application evidence:**
`threatGrade()` in `app.js`.

**Review:**
The table and function agree.

**Corrected conclusion:**
Confirmed; no defect.

**Recommended action:**
None.

### THR-03 — Timing and causes of Threat increases

**Original audit conclusion:**
Threat is incorrectly raised when an NPO recommendation is selected rather than when the Shoot/Fight action occurs.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, “Threat Level”: increase when an NPO performs Shoot/Fight and under enumerated player-action conditions.

**Application evidence:**
`chooseNpoDecision()` and `resolveNpo()` call `setThreat()` before attack target/combat completion.

**Review:**
The direct wording uses performance of the action, not selection of a recommendation. Exiting the later combat flow leaves the premature increase.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Commit Threat only when the relevant action is actually performed; implement all printed player-action exceptions.

### THR-04 — Scout Sub-Crypt Dormant exception

**Original audit conclusion:**
Mission 5 says Operate Hatch does not increase Threat, but the app assigns Hatch Threat without a mission check.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 13, Mission 5 “Dormant”; PDF page 2, default Operate Hatch Threat roll.

**Application evidence:**
Mission 5 JSON and player activation Threat handling in `app.js`.

**Review:**
The mission exception is direct and the generic app path does not branch on mission.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Suppress the default Operate Hatch Threat roll in Mission 5.

### THR-05 — Complete increases/decreases and Scout Room

**Original audit conclusion:**
Official Threat changes, including Scout Room reduction, are missing or only manually delegated.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 2, complete default Threat triggers; PDF page 13, Mission 5 “Scout Room.”

**Application evidence:**
`completePlayerActivation()` in `app.js` rolls the default 4+ Operate Hatch increase and applies both the automatic and 4+ Breach increases. The same function increments Threat for every recorded Shoot and Fight without checking the printed exceptions. Mission 5's Scout Room rule remains prose in `Missions/05-scout-sub-crypt.json`.

**Review:**
The original finding overstates the gap. The app already implements the default 4+ Operate Hatch roll and both Breach increases. It does not implement the Silent exception for Shoot, the conditional exception when a player Fight incapacitates its NPO without the player operative remaining visible to another enemy, or Scout Room's reduction to the highest Threat level of the grade below. THR-04 separately covers suppressing the otherwise-correct Hatch roll in Mission 5.

**Corrected conclusion:**
Partially confirmed High issue: the default Hatch and Breach triggers are implemented, while the Shoot/Fight exceptions and Scout Room reduction remain missing.

**Recommended action:**
Preserve the existing Hatch and Breach logic; add the Silent and conditional Fight exceptions plus the Mission 5 Scout Room reduction. Keep manual adjustment only as a labeled correction.

### THR-06 — Threat import normalization

**Original audit conclusion:**
Malformed imported Threat can yield invalid Grade/UI state.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 2, valid Threat range and Grade table. The PDF says nothing about imports or persistence.

**Application evidence:**
`normalizeState()`, import handlers, `threatGrade()`, and HUD calculation in `app.js`.

**Review:**
The official range makes nonnumeric/out-of-range state invalid, and current normalization is weak. The import mechanism is implementation-specific, not a printed rules requirement.

**Corrected conclusion:**
Confirmed Low integrity issue with potential Medium rules impact after malformed import.

**Recommended action:**
Coerce and clamp imported/restored Threat before deriving Grade.

### ACT-01 — Alternating activations

**Original audit conclusion:**
The scheduler compliantly alternates while both sides have ready operatives.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 8, Game Sequence, plus PDF page 3, Dormant NPOs. Detailed alternating activation rules are delegated to the Core Book.

**Application evidence:**
`setNextActivation()` and `advanceAfterActivation()` in `app.js`.

**Review:**
The scheduling shape is plausible, but the mission pack does not restate the full alternation rule. Moreover, dormant NPOs should not enter the queue at Threat 0.

**Corrected conclusion:**
Scheduler compliance is Unable to Verify from this PDF in general; its inclusion of readied Threat-0 NPOs is a confirmed High Tomb World defect already captured by STR-01.

**Recommended action:**
Apply dormant eligibility, then verify generic alternation against the Core Book.

### ACT-02 — No double activation/incapacitated activation

**Original audit conclusion:**
Compliant.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF page 3 uses ready/expended states and PDF pages 3–7 describe NPO behaviors, but detailed incapacitation/activation rules are delegated to the Core Book.

**Application evidence:**
Player activated-ID tracking, NPO `ready`, wound/casualty filters in `app.js`.

**Review:**
The code supports the conclusion, but the mission pack alone does not fully establish the generic rule asserted.

**Corrected conclusion:**
No Tomb World contradiction identified; formal compliance requires the Core Book.

**Recommended action:**
No Tomb World change; verify separately against the Core Book.

### ACT-03 — Premature NPO activation commitment

**Original audit conclusion:**
The app consumes an NPO activation and changes Threat before required attack resolution completes.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 3, “Behaviour” (perform the first action it can); PDF pages 6–7, ordered operative behaviors; PDF page 2, Threat increases when Shoot/Fight is performed.

**Application evidence:**
`resolveNpo()` clears readiness, advances scheduling, and changes Threat before `showNpoAttackWizard()` completes.

**Review:**
The mission pack ties activation to actually performing the ordered actions. The application can exit after commitment but before the mandatory attack.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Stage the activation and atomically commit readiness, Threat, combat, and history after mandatory actions resolve.

### ACT-04 — Arrival readiness

**Original audit conclusion:**
All reinforcement/event arrivals being immediately ready might be wrong.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 3 standard Joint Ops reinforcements specify Conceal placement but do not explicitly say “ready”; PDF pages 21–22 explicitly say ready for Chittering Drone and Awakened Warrior.

**Application evidence:**
`startTurningPoint()`, `createNpo()`, and manual restoration in `app.js`.

**Review:**
Event readiness is supported for the named spawn cards. Standard reinforcement readiness is not explicit enough in this PDF to certify the app's assumption; dormant Threat 0 is not relevant because standard reinforcements require Grade above 0.

**Corrected conclusion:**
Event portion is correct; standard arrival readiness is Unable to Verify. The original broad concern is overstated (Informational pending clarification).

**Recommended action:**
Preserve explicit event readiness and seek an official clarification/Core interaction for standard reinforcement readiness.

### ACT-05 — NPO activation selection priority

**Original audit conclusion:**
The app's behavior-rank/wounds/name sort was unverifiable.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 4, “Threat Principle — Activation Priority”: first ability/threat to Shoot or Fight, then not in cover, then proximity; unresolved decisions are random.

**Application evidence:**
`nextNpo()`/`priority()` in `app.js` use behavior rank plus low-wound penalty.

**Review:**
The official priority is now available and conflicts with the app's fixed Marksman/Brawler/Sentinel/Guardian ranking, which are not the pack's behavior names.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Prompt/resolve the printed ordered criteria and randomize only unresolved ties.

### NPO-01 — Operative-specific behavior tables

**Original audit conclusion:**
One generic heuristic replaces official operative-specific tables.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 3, “Behaviour”; PDF pages 6–7, ordered behavior lists for Scarab Swarm, Necron Warrior, Tomb Crawler, and Macrocyte.

**Application evidence:**
`profiles`, `npoQuestions`, `chooseNpoDecision()` in `app.js`.

**Review:**
The PDF directly provides different ordered action lists. The app's labels and shared heuristic do not implement them.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Data-drive each printed behavior and its order/order-selection conditions.

### NPO-02 — Printed action priority and fallbacks

**Original audit conclusion:**
The generic question sequence does not follow printed priorities or legal fallbacks.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 3, first legal action in behavior; PDF pages 6–7, exact ordered lists.

**Application evidence:**
`nextNpoQuestionKey()` and `chooseNpoDecision()` in `app.js`.

**Review:**
For example, a Warrior's list begins Fall Back, Shoot, Reposition, Dash, Fight, while a Scarab begins Fight then Charge. The app universally prioritizes engaged Fight and often Charge, contradicting those lists.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Evaluate each profile's printed list top-to-bottom and stop at the first legal action.

### NPO-03 — Action legality inputs

**Original audit conclusion:**
Broad yes/no prompts omit order, visibility, range, AP, and restrictions.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 3–7 repeatedly condition behavior on legal actions, valid targets, obscuring, cover, control range, and movement. Definitions are delegated to the Core Book.

**Application evidence:**
`npoQuestions` and wizard branching in `app.js`.

**Review:**
The pack supports the need to establish these predicates, and the current prompts omit several printed distinctions (e.g., Warrior Fall Back and valid target not obscured). Exact generic legality cannot be fully audited without the Core Book.

**Corrected conclusion:**
Confirmed High gap for predicates expressly used by the pack; remaining core-legality scope is Unable to Verify.

**Recommended action:**
Ask every predicate required by the selected printed behavior and require tabletop confirmation for Core Book legality.

### NPO-04 — Target priority and ties

**Original audit conclusion:**
Hard-coded wounded/objective/cluster/closest logic does not implement official criteria.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 4, Threat Principle, Fight target priority, Shoot target priority, and random final tie.

**Application evidence:**
`chooseNpoDecision()` and target-selection UI in `app.js`.

**Review:**
The official lists prioritize likelihood to incapacitate, mission impact, obscuring, cover, distance, and readiness in action-specific orders. “Largest cluster” is not the generic printed tie-break.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Collect candidates and apply the action-specific ordered list, then randomize unresolved choices.

### NPO-05 — Grade- and mission-dependent behavior

**Original audit conclusion:**
Behavior ignores Grade and mission ID, presumed missing official branches.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 3–7, NPO rules/datacards; PDF pages 9–14, mission rules.

**Application evidence:**
`chooseNpoDecision()` does not read Grade/mission.

**Review:**
The PDF does not print generic Grade-dependent operative behavior branches. Mission goals influence the Threat Principle, and Mission 5 changes spawn/Threat behavior, but that is not the same as a missing Grade branch in each datacard.

**Corrected conclusion:**
The asserted requirement is unsupported. Mission-aware “worst for the players” decisions belong under NPO-04/MIS-02; no separate defect is established.

**Recommended action:**
Do not invent Grade branches; implement only explicit mission effects and mission-impact priority.

### NPO-06 — Four labels/profiles correspond to official terms

**Original audit conclusion:**
Marksman, Brawler, Sentinel, and Guardian were unverifiable official labels.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 5–7, NPO Datacards. The official types are Necron Warrior, Canoptek Scarab Swarm, Canoptek Macrocyte, and Canoptek Tomb Crawler; each card prints prose behavior rather than those four labels.

**Application evidence:**
`profiles` in `app.js`.

**Review:**
The four type names are official. The four `behavior` labels are application inventions and, notably, “Sentinel” appears in the PDF as a Tomb Crawler ability, not Macrocyte behavior.

**Corrected conclusion:**
Type inventory is broadly correct but behavior terminology is non-official and misleading. Low severity itself; the resulting logic defect is High under NPO-01/02.

**Recommended action:**
Remove invented behavior labels from rules-facing logic/copy and store the printed ordered behaviors.

### COM-01 — Fight resolved as shooting defense

**Original audit conclusion:**
Fight incorrectly uses defense dice/cover instead of alternating strike/parry.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF pages 6–7 list melee weapon profiles and tell NPOs when to Fight, but the PDF delegates Fight resolution to the Kill Team Core Book.

**Application evidence:**
`resolveCombat()`/`resolveDefense()` and melee UI in `app.js` use save dice and cover.

**Review:**
The code observation is accurate, but this mission pack does not state the asserted generic Fight resolution. The original conclusion may be correct under the Core Book, but cannot be classified Confirmed using the requested primary source alone.

**Corrected conclusion:**
Unable to Verify from this PDF; requires a separate Core Book audit. Excluded from the corrected Tomb World priority list.

**Recommended action:**
Compare the combat engine directly with the current Core Book before implementation.

### COM-02 — Weapon special rules

**Original audit conclusion:**
Only basic damage and some Piercing/AP are parsed; many weapon rules are ignored.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 6–7, NPO weapons/abilities explicitly include Piercing 1, Punishing, Torrent 1, Brutal, Blast 2, and profile-selection conditions. Rule definitions are external.

**Application evidence:**
`profiles`, `playerWeaponProfile()`, `weaponPiercingValue()`, `rollAttack()` in `app.js`.

**Review:**
For Tomb World NPOs, the app stores none of the printed special rules and only one generic attack per type, so omission is directly confirmed. The broader list of player weapon rules and their mechanics is not verifiable from this PDF.

**Corrected conclusion:**
Confirmed High for printed NPO rules/profiles; external player-team scope remains Unable to Verify.

**Recommended action:**
Implement or clearly delegate every NPO weapon rule printed on pages 6–7; audit player weapons against their own official documents.

### COM-03 — Cover save dice construction

**Original audit conclusion:**
Cover is added as an extra save and is incorrectly offered for melee.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF pages 4 and 6 mention cover for decisions and the Tomb Crawler Sentinel ability, but do not define shooting defense dice or retained cover saves.

**Application evidence:**
`resolveDefense()` and combat dialogs in `app.js`.

**Review:**
The PDF is insufficient to establish the claimed generic cover algorithm.

**Corrected conclusion:**
Unable to Verify from the authoritative mission pack; excluded from this pack-only priority list.

**Recommended action:**
Audit against the current Core Book.

### COM-04 — Distinct NPO ranged/melee weapon profiles

**Original audit conclusion:**
Each NPO incorrectly uses one generic attack for Shoot and Fight.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 6–7, NPO Datacards: Warriors, Macrocytes, and Tomb Crawlers have distinct named ranged and melee profiles; some have multiple ranged profiles/options.

**Application evidence:**
`profiles[type].attack` and NPO attack wizard in `app.js`.

**Review:**
The official datacards directly contradict a single profile used for both actions.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Store exact weapon option/profile and select the correct ranged or melee weapon for the action.

### COM-05 — Save cancellation sequence

**Original audit conclusion:**
The cancellation core is partial but surrounding cover/AP logic is wrong.

**Review status:**
Unable to Verify

**Official rule reference:**
The mission pack does not define successful-save cancellation; it is a Core Book rule.

**Application evidence:**
`resolveDefense()` in `app.js`.

**Review:**
No conclusion about the generic sequence can be drawn from this PDF.

**Corrected conclusion:**
Unable to Verify; no pack-specific priority item.

**Recommended action:**
Test against the current Core Book.

### COM-06 — Damage transaction persistence

**Original audit conclusion:**
Damage can be reopened/recommitted because durable transaction IDs are absent.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF pages 20–22 include effects that react to damage/incapacitation, but prescribe no software persistence model.

**Application evidence:**
Pending combat state and commit handlers in `app.js`.

**Review:**
This is an implementation-integrity concern rather than a direct mission-pack rule. The PDF cannot establish the alleged reload defect without executing targeted scenarios.

**Corrected conclusion:**
Unable to Verify as a rules finding (Informational engineering risk).

**Recommended action:**
Test idempotence if combat automation is retained.

### COM-07 — Player datacard currency

**Original audit conclusion:**
Player attack values and balance changes were unverifiable.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF pages 1 and 8 delegate player kill-team selection/rules to each team's own publication.

**Application evidence:**
`Player_Operatives/*.json`.

**Review:**
The mission pack contains no Death Korps, Deathwatch, or Kasrkin datacards.

**Corrected conclusion:**
The original Unable to Verify status remains correct.

**Recommended action:**
Perform a separate comparison with current official team rules.

### REI-01 — Reinforcement timing, quantity, and table

**Original audit conclusion:**
Exactly Grade reinforcements and a distinct 2D6 mapping might be wrong; the rule was unverifiable.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 3, “NPO Reinforcements”; PDF page 5, shared NPO 2D6 table.

**Application evidence:**
`startTurningPoint()`, `randomReinforcement()`, and `generateRoster()` in `app.js`.

**Review:**
The pack directly confirms exactly Grade reinforcements after the first turning point, after events, and directs use of the same page-5 NPO table. Thus quantity is correct, but code order is wrong and `randomReinforcement()` cannot legitimately use a different mapping from setup. Both paths also lose printed weapon variants.

**Corrected conclusion:**
High defect for order/table identity; original suspicion that Grade quantity itself was wrong is incorrect.

**Recommended action:**
Use one authoritative page-5 result table for setup and reinforcements, preserving weapon variants, after event resolution.

### REI-02 — Mission 5 room awakening

**Original audit conclusion:**
The D3+Grade (max 5) room spawn is missing.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 13, Mission 5 “NPOs.”

**Application evidence:**
Mission 5 JSON contains prose; no room-open/entry dispatch exists in `app.js`.

**Review:**
The direct mission rule matches the original finding.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Track first opening/entry per eligible room and perform the printed constrained placement.

### REI-03 — Ten-NPO limit and placement confirmation

**Original audit conclusion:**
A global maximum and partial blocking exist, but placement is prematurely marked deployed.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 3 and 5, “NPO Limit,” state a recommendation to limit NPOs to ten and not set up excess; PDF page 3 specifies hatchway placement.

**Application evidence:**
`MAX_NPOS`, `startTurningPoint()`, `reinforcementEntry`, and `deployed:true` in `app.js`.

**Review:**
The cap is supported but expressly framed as a recommendation/difficulty choice, not an immutable universal law. The code enforces it globally, while failing to model each random hatchway and placement constraint.

**Corrected conclusion:**
Medium defect: placement is incomplete and the recommended cap is presented/enforced as mandatory without a difficulty option.

**Recommended action:**
Make the cap a default configurable difficulty rule and confirm each random hatchway/placement before deployment.

### REI-04 — Standard reinforcement order/readiness

**Original audit conclusion:**
Ready/order state was unverifiable.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 3 requires a Conceal order and exact hatchway placement; it does not explicitly say “ready” for standard Joint Ops reinforcements.

**Application evidence:**
Reinforcement objects use `ready:true,deployed:true` and have no order field.

**Review:**
The missing Conceal-order representation is confirmed. Readiness remains Unable to Verify from the direct text.

**Corrected conclusion:**
Medium confirmed defect for missing order/placement; readiness unresolved.

**Recommended action:**
Store Conceal order and seek authoritative clarification for readiness.

### REI-05 — Ten-NPO maximum scope

**Original audit conclusion:**
Whether ten applies universally was unverifiable.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 3 and 5 call ten a recommendation; event cards on pages 21–22 use inability/limit redraw instructions.

**Application evidence:**
`MAX_NPOS=10` applies to reinforcements, events, and manual additions.

**Review:**
Ten is the pack's recommended limit, but the Difficulty section permits changing setup/reinforcement quantities and the wording does not make the cap compulsory. Event “cannot set up” handling must redraw where stated.

**Corrected conclusion:**
The numeric default is supported; universal hard enforcement and silent event blocking are only partially compliant. Medium severity.

**Recommended action:**
Expose the recommendation as a difficulty setting and honor card-specific redraws.

### MIS-01 — Universal all-NPOs-dead victory

**Original audit conclusion:**
Universal elimination victory conflicts with all six mission-specific endings.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 8, “End the Battle”; PDF pages 9–14, each mission's “Victory.”

**Application evidence:**
`checkGameEnd()` declares victory when the generated roster has no living NPO.

**Review:**
None of the six missions uses “all NPOs incapacitated” as its player-win condition. Some can legitimately have no NPOs temporarily (especially Mission 5), making the universal rule fundamentally wrong.

**Corrected conclusion:**
Confirmed Critical defect.

**Recommended action:**
Remove universal elimination victory and implement each printed end condition.

### MIS-02 — Mission-specific rules are display-only

**Original audit conclusion:**
Mission gambits/actions/random results/state/end checks are prose without engine hooks.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 9–14, all six mission-rule panels.

**Application evidence:**
Mission JSON `rules`; `renderMission()` displays summaries; no mission-rule dispatch in Strategy/activation/end handling.

**Review:**
Direct comparison confirms missing Escape movement/state, permanent sabotage state, transponder search/carriage, repair/destruction, room spawn/scouting, and phasing/regroup checks.

**Corrected conclusion:**
Confirmed Critical as a combined gap because it prevents correct automated mission play.

**Recommended action:**
Implement typed mission state and exact timing one mission at a time, while clearly delegating physical placement.

### MIS-03 — Generic numeric tracker

**Original audit conclusion:**
A freely editable tracker cannot represent mission predicates/timing.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 9–14, mission-specific Victory and mission actions.

**Application evidence:**
`state.tracker`, `missionTrackerMax()`, generic tracker UI, and unused `completed` in `app.js`.

**Review:**
The six missions require distinct state: escaped operatives, seven individually sabotaged/open features, carried marker escape, repairable destruction, eligible scouted rooms, and per-operative end-of-turn regroup predicates.

**Corrected conclusion:**
Confirmed High defect; a scalar may display progress but cannot decide most outcomes.

**Recommended action:**
Replace the scalar as authority with mission-specific state/evaluators.

### MIS-04 — Mission briefing content

**Original audit conclusion:**
All six display summaries, but action costs/eligibility/random state may be lost and source accuracy was unverifiable.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 9–14, Missions 1–6.

**Application evidence:**
`Missions/*.json` and `renderMission()`.

**Review:**
The PDF now permits verification. Broad summaries are recognizable, but a summary is not sufficient when omitted conditions affect play; Mission 5's Scout action, Mission 6 phasing, and exact victory predicates are examples.

**Corrected conclusion:**
Confirmed Low presentation issue where full official page remains the tabletop authority; High only where the app uses the summary to calculate an outcome.

**Recommended action:**
Verify every concise summary and label non-automated rules as requiring the official mission page.

### MIS-05 — VP and tie conditions

**Original audit conclusion:**
VP/tie data was absent and unverifiable.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 9–14, each “Victory” section; PDF page 8, “End the Battle.”

**Application evidence:**
Mission JSON `victory` objects contain binary win/lose prose and no VP/tie schema.

**Review:**
The six Joint Ops missions use binary win/loss conditions; the PDF does not prescribe VP totals or tie conditions for them. Absence of VP/tie data is therefore correct.

**Corrected conclusion:**
No compliance defect. Exclude from remediation.

**Recommended action:**
Do not add VP/tie mechanics absent from the official missions.

### DAT-01 — Supported player-team data

**Original audit conclusion:**
Player-team profiles and abilities were unverifiable.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF pages 1 and 8 delegate player-team selection/datacards to each kill team's rules.

**Application evidence:**
`Player_Operatives/manifest.json` and team JSON files.

**Review:**
The mission pack cannot verify these teams' stats or balance revisions.

**Corrected conclusion:**
Original status remains correct; not a Tomb World PDF-supported defect.

**Recommended action:**
Use current official team publications in a separate audit.

### DAT-02 — Tomb World NPO datacard completeness

**Original audit conclusion:**
Four minimal profiles omit many fields/effects, but exact omissions were unverifiable.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 5–7, NPO table and datacards.

**Application evidence:**
`profiles` in `app.js` has only behavior label, wounds, save, and one attack.

**Review:**
The PDF shows Movement, APL, wounds, save, multiple weapon options/profiles, weapon rules, named abilities, orders, and full behavior lists. The exact gap is now directly verifiable.

**Corrected conclusion:**
Confirmed High defect.

**Recommended action:**
Transcribe complete sourced NPO records and declare which fields the guide automates.

### DAT-03 — Mission/event/reinforcement dataset currency

**Original audit conclusion:**
Completeness was unverifiable because the PDF was invalid.

**Review status:**
Incorrect

**Official rule reference:**
PDF pages 2–14 and 20–22.

**Application evidence:**
Mission manifest/JSON plus hard-coded `profiles`, `events`, and generation functions in `app.js`.

**Review:**
The source is valid and shows clear incompleteness: event deck and NPO profiles are incomplete, while missions are broadly inventoried. “Invalid PDF” provenance claims are stale.

**Corrected conclusion:**
Confirmed High data-completeness defect, not unverifiable.

**Recommended action:**
Record the PDF revision/hash and reconcile every structured rules entry to its page.

### PER-01 — Permanent state survives reload

**Original audit conclusion:**
Core state persists, but mission-specific state mostly does not exist.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF pages 9–14 require persistent mission state throughout a battle (e.g., sabotaged hatches, carrier, Destruction, scouted rooms). The PDF has no software-save rule.

**Application evidence:**
`initialState()`, `save()`, `load()`, `normalizeState()`, and scalar `tracker` in `app.js`.

**Review:**
The rules establish state that must remain true during play, and the app does not represent it. Reload semantics are an application promise rather than direct rule text.

**Corrected conclusion:**
Confirmed High underlying mission-state gap; persistence architecture itself is Informational until those states exist.

**Recommended action:**
When mission state is implemented, include it in compatible saves.

### PER-02 — Temporary effects and combat persistence

**Original audit conclusion:**
Temporary event state cannot survive/expire and attacks may commit more than once.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 2 and pages 20–22 establish event durations; no software transaction rule is provided.

**Application evidence:**
No active-event state in `initialState()`; pending attack drafts and commit handlers in `app.js`.

**Review:**
Missing durable event duration is directly relevant and confirmed. The transaction-ID recommendation is engineering design, not a rule conclusion supported by the PDF.

**Corrected conclusion:**
High for absent event-effect persistence/expiry; attack idempotence remains Unable to Verify without behavioral testing.

**Recommended action:**
Persist active event effects and expiry; separately test combat commits.

### PER-03 — Cache/data version coherence

**Original audit conclusion:**
Mixed code/data versions can occur and the allegedly invalid PDF is precached.

**Review status:**
Incorrect

**Official rule reference:**
The PDF contains no service-worker or cache requirements.

**Application evidence:**
`service-worker.js` caching strategies; the current asset is a valid PDF.

**Review:**
The invalid-PDF premise is false, and cache coherence is outside a rules-compliance audit. It may be a legitimate engineering concern, but it is not supported as a Tomb World rules discrepancy.

**Corrected conclusion:**
Exclude from the compliance priority list.

**Recommended action:**
Handle only in a separate offline/update integrity review.

### ABS-01 — Manual geometry predicates

**Original audit conclusion:**
Manual LOS/range/cover answers are acceptable only if every official predicate is collected.

**Review status:**
Partially Confirmed

**Official rule reference:**
PDF page 4, Threat Principle priorities; PDF pages 6–7, behaviors requiring cover, valid target, obscuring, distance, and control range.

**Application evidence:**
`npoQuestions` in `app.js`.

**Review:**
Manual tabletop input is compatible with the pack, but current prompts do not gather every predicate in the correct action-specific order.

**Corrected conclusion:**
The abstraction is acceptable; its incomplete questionnaire contributes to confirmed NPO-03/04 (High), not a separate defect.

**Recommended action:**
Retain manual geometry but align questions exactly to the printed decision being resolved.

### ABS-02 — Manual terrain/cleanup confirmation

**Original audit conclusion:**
Physical terrain delegation is safe only when later app state does not depend on it.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 9–14 mission terrain/state rules; PDF page 22, The Maze Reforms.

**Application evidence:**
Mission confirmation UI and lack of hatch/breach state in `app.js`.

**Review:**
The interpretation is sound: manual manipulation can preserve play, but the app cannot later evaluate Demolition Protocol or Maze effects without confirmed state.

**Corrected conclusion:**
Confirmed as an Informational design boundary; related mission/event omissions carry the severity.

**Recommended action:**
Either persist only state needed by later automation or explicitly delegate the later outcome too.

### ABS-03 — Manual Threat adjustment

**Original audit conclusion:**
Manual ± Threat is an acceptable correction abstraction but bypasses rule-trigger logging.

**Review status:**
Confirmed

**Official rule reference:**
PDF page 2, Threat Level; PDF page 13, Scout Room reduction.

**Application evidence:**
Threat HUD buttons call `setThreat(±1, 'Manual adjustment')`.

**Review:**
A correction control does not itself contradict the rules, but repeated -1 cannot conveniently implement every printed reduction and is not a substitute for official triggers.

**Corrected conclusion:**
No standalone compliance defect (Informational); missing automated triggers remain THR-03–05.

**Recommended action:**
Label as correction and preserve a reason log.

### ABS-04 — Manual initiative override

**Original audit conclusion:**
Override can correct external modifiers but should not look like the normal official path.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 2, 3, and 8 specify NPO win choice, Threat-0 automatic initiative, and first-turn player initiative.

**Application evidence:**
Initiative override controls in `app.js`.

**Review:**
Manual correction is not prohibited, but it must not replace the direct Tomb World cases.

**Corrected conclusion:**
Informational; implement the direct cases and label override as correction.

**Recommended action:**
Keep only as a clearly labeled correction after rules-derived suggestion.

### HR-01 — Unlimited initiative rerolls

**Original audit conclusion:**
Unlimited reroll is a house rule unless an official effect permits it.

**Review status:**
Unable to Verify

**Official rule reference:**
PDF page 2 specifies the NPO/player roll-off but does not state reroll permissions or tie resolution.

**Application evidence:**
Initiative UI reroll handler in `app.js`.

**Review:**
The mission pack does not authorize the control, but absence alone does not establish the complete Core Book rule.

**Corrected conclusion:**
Unable to Verify from this PDF; likely should be labeled manual correction rather than official resolution.

**Recommended action:**
Verify against the Core Book and remove or relabel if unsupported.

### HR-02 — Generic heuristic and universal elimination win

**Original audit conclusion:**
Both are outcome-changing house rules.

**Review status:**
Confirmed

**Official rule reference:**
PDF pages 3–7, NPO behavior/Threat Principle; PDF pages 8–14, mission endings.

**Application evidence:**
`chooseNpoDecision()` and `checkGameEnd()` in `app.js`.

**Review:**
Both conflict directly with printed rules. Calling them “house rules” risks understating that the UI does not clearly opt users into alternatives.

**Corrected conclusion:**
Confirmed; Critical for universal victory and High for the behavior heuristic.

**Recommended action:**
Replace with official logic or explicitly separate an optional house-rule mode from official play.

## Additional Issues Found

### Dormant NPO state is entirely absent

- **Severity:** High
- **Official PDF reference:** PDF page 3, “Dormant NPOs.”
- **Application evidence:** `startTurningPoint()` always readies every active NPO; `setThreat()` has no transition behavior; post-first-turn initiative still rolls at Threat 0.
- **Discrepancy:** At Threat 0, the pack directly makes all NPOs dormant, expended, and unable to ready, and gives players automatic initiative. When Threat becomes nonzero, all NPOs ready. The original audit missed this as a discrete rule and incorrectly marked ready handling compliant.
- **Recommended future correction:** Add dormant derivation and exact zero/nonzero transition behavior before activation scheduling.

### The event deck has omitted cards and duplicate physical weighting

- **Severity:** High
- **Official PDF reference:** PDF pages 20–22, event-card sheets, including Subjugation Glyphs, Transdimensional Relocation, My Will Be Done, Reanimation Protocols, Dark of the Tomb, and repeated Awakened Warrior.
- **Application evidence:** `events` contains only six unique entries and selects uniformly.
- **Discrepancy:** The original audit suspected an incomplete inventory but did not identify the concrete missing cards or the confirmed duplicate weighting. These effects change APL, positions, weapon accuracy, incapacitation/reanimation, and rerolls.
- **Recommended future correction:** Encode every printed card instance and its full effect/redraw condition.

### Starting operatives lack required Conceal orders and printed weapon variants

- **Severity:** High
- **Official PDF reference:** PDF page 8, “Set Up Operatives”; PDF page 5, NPO table; PDF pages 6–7, datacards.
- **Application evidence:** `generateRoster()` creates objects with no `order` or selected weapon field and only one generic `attack` per broad type.
- **Discrepancy:** The pack requires starting NPO setup with Conceal and uses table results that identify ranged weapon choices. The original audit discussed generic profile incompleteness but did not isolate setup loss of these required generated attributes.
- **Recommended future correction:** Store generated weapon option and Conceal order with each NPO from creation.

### Player setup omits the pack's explicit initial resources

- **Severity:** Medium
- **Official PDF reference:** PDF page 8, “Select Operatives”: up to four equipment options total and 2CP total.
- **Application evidence:** `initialState()` and setup UI have no CP or equipment-selection state.
- **Discrepancy:** STR-05 focused on the Strategy checklist but did not distinctly identify that initial mission setup has explicit resource values.
- **Recommended future correction:** Either track them or state clearly that the guide delegates both to tabletop play before battle start.

## Corrected Priority List

Only Confirmed and Partially Confirmed compliance issues appear below. Incorrect and Unable-to-Verify findings are excluded.

### Priority 1: Critical and High

- **Critical — MIS-01, universal all-NPOs-dead victory** — confirmed from the original audit.
- **Critical — MIS-02, mission rules/end conditions are display-only** — corrected upward from the original audit's broad P1 framing because the combined gap prevents correct mission play.
- **High — STR-01/additional dormant-state issue** — newly discovered during this review; the original compliant conclusion is reversed.
- **High — STR-02 and STR-06, exact Strategy order and mission Ready hooks** — confirmed/corrected from the original audit; event-before-reinforcement is now directly verified.
- **High — STR-03, EVT-01, EVT-02, EVT-03, and EVT-04, event timing/deck/effects/placement** — confirmed and corrected from the original audit with exact card inventory and rules.
- **High — THR-03, THR-04, and THR-05, Threat timing plus Shoot/Fight and Mission 5 exceptions** — corrected from the original audit; preserve the implemented default Hatch and Breach increases while adding only the missing exceptions and Scout Room reduction.
- **High — ACT-03, premature activation commitment** — confirmed from the original audit.
- **High — ACT-05 and NPO-01 through NPO-04, printed NPO selection/behavior/targets** — confirmed/corrected from the original audit using PDF pages 3–7.
- **High — COM-02 and COM-04, printed NPO weapons/rules and distinct profiles** — confirmed/corrected from the original audit; player/Core portions are excluded.
- **High — REI-01, one official generation table and event-before-reinforcement order** — corrected from the original audit; Grade quantity is not defective.
- **High — REI-02, Mission 5 room generation** — confirmed from the original audit.
- **High — MIS-03, mission-specific state rather than scalar tracking** — confirmed from the original audit.
- **High — DAT-02 and DAT-03, incomplete official NPO/event datasets** — corrected from the original audit now that the PDF is available.
- **High — PER-01/PER-02 underlying mission/event state** — corrected from the original audit; software transaction claims are excluded.
- **High — starting Conceal orders and generated weapon variants** — newly discovered during this review.
- **High — HR-02 generic heuristic portion** — confirmed from the original audit (the victory portion is Critical).

### Priority 2: Medium

- **Medium — SET-03, enforce supported solo roster legality** — corrected from the original audit; co-op scope is excluded.
- **Medium — SET-05/SET-06, exact generation rows and setup prompts/maps** — corrected from the original audit now that the PDF is valid.
- **Medium — STR-04, automatic player initiative at Threat 0** — corrected from the original audit; generic tie/reroll claims are excluded.
- **Medium — STR-05 and newly identified initial 2CP/four equipment delegation** — corrected/newly discovered during this review.
- **Medium — EVT-05/EVT-06, accurate summaries and draw-without-replacement lifecycle** — corrected from the original audit.
- **Medium — REI-03 through REI-05, printed placement/Conceal and recommended-cap semantics** — corrected from the original audit; unsupported readiness claims are excluded.
- **Medium — Mission briefing omissions that alter tabletop decisions** — corrected from MIS-04 in the original audit.

### Priority 3: Low and Informational

- **Low — THR-06, normalize imported Threat** — confirmed from the original audit as an implementation-integrity issue.
- **Low — NPO-06, invented behavior terminology** — corrected from the original audit; logic consequences are already High.
- **Low — EVT-05 wording where it does not automate an outcome** — corrected from the original audit.
- **Informational — ABS-01 through ABS-04** — confirmed/corrected from the original audit as acceptable boundaries only when clearly labeled and complete.
- **Informational — ACT-04 standard reinforcement readiness** — corrected from the original audit; the PDF is not explicit enough to demand a change.

## Conclusion

The prior audit was appropriately cautious when it lacked an authoritative local rules source, but many of its “unverifiable” conclusions and its claim that the PDF asset was SVG are no longer valid. Direct review of the 22-page official pack confirms the application's most serious mission, NPO, Threat, event, and data-completeness gaps; supplies exact corrections for event sequencing, deck behavior, dormancy, reinforcements, and mission outcomes; and disproves or narrows several findings.

The application should not currently be described as an official-rules implementation. The first future work should remove universal elimination victory, implement mission-specific state/end logic, implement dormancy and printed NPO behaviors, and replace the six-result event approximation with the actual deck and timing. Findings that depend only on the Core Book, team datacards, or software cache design should be handled in separate audits and should not be presented as established by the Tomb World Mission Pack.
