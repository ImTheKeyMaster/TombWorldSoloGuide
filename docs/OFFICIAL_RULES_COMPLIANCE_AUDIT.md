# Official Rules Compliance Audit

## Audit scope

This is a documentation-only, executable-behaviour audit of the repository at commit `b3b46c3` (21 July 2026). It covers setup, Strategy and Firefight sequencing, the six loaded missions, NPO generation and decisions, combat, Threat/Grade, events, reinforcement handling, player-team data, persistence, and service-worker caching. No statement in app copy, JSON `source` metadata, README history, or code comments was accepted as proof of a rule.

**Important evidence limitation.** The tracked file named `Assets/Tomb-World-Mission-Pack.pdf` is actually SVG icon markup, not a PDF. The audit environment also could not retrieve the current Games Workshop download catalogue. Consequently, this report separates (a) conclusions that can be compared to identifiable official rule headings from (b) content/profile completeness that cannot honestly be certified. An `UNVERIFIABLE` result means “do not claim compliance”, not “probably correct”. Page numbers are supplied only where the repository itself preserves a reliable page association (the mission maps are described as pages 17–19); otherwise “page unavailable” is explicit rather than guessed.

### Method

1. Enumerated every tracked HTML, JavaScript, JSON, manifest, service-worker, mission, and player-operative file.
2. Followed initialization, normalization, save/restore, setup, Turning Point, activation, attack, damage, mission tracker, and cache paths in `app.js` and `service-worker.js`.
3. Compared implementable behaviour with the official documents listed below, at the named rule/card/table level.
4. Counted each scorecard row from the findings in that section. Intentional abstractions and house rules are listed separately and are not silently counted as compliant.
5. Added a reproducible scenario for every P0, P1, and P2 finding.

## Authoritative sources

Only Games Workshop sources form the baseline:

| Key | Official document | Relevant location | Publication/revision used | Availability in this audit |
|---|---|---|---|---|
| TW | *Kill Team: Joint Ops — Tomb World Mission Pack* | Mission Pack Rules; Threat Level/Grade; Reinforcements; Tomb World Events; NPO datacards/behaviour tables; Missions 1–6 (maps associated with pp. 17–19) | Repository manifest identifies 19 Nov 2025; current revision could not be independently retrieved | The alleged local PDF is invalid SVG; rule/card page numbers unavailable except mission-map association |
| JO | *Kill Team: Joint Ops* | Joint Ops sequence, NPO selection/activation, behaviour priorities, reinforcement and solo/co-op team requirements | Current Games Workshop download as of audit date requested; revision date unavailable | First-party download unavailable in audit environment |
| CORE | *Kill Team Core Rules* | Approved Ops battle sequence; Strategy phase; initiative; Shoot, Fight, cover, incapacitation | Current 2024-edition rules plus current official updates; revision date unavailable | Rule headings identifiable; current first-party PDF unavailable |
| FAQ | *Kill Team Core Rules Updates and Errata* and *Kill Team Balance Dataslate* | Only provisions explicitly applying to the above rules/teams | Current as of 21 Jul 2026 requested; revision date unavailable | First-party files unavailable; no applicability claim made without text |
| DK/DW/KAS | Official *Death Korps*, *Deathwatch*, and *Kasrkin Kill Team Rules* | Operative Selection, datacards, weapon rules, abilities | JSON claims 28 Jan 2026 for DW/KAS; DK source metadata inspected but current source not independently available | Profiles therefore remain unverifiable rather than assumed current |

No community sources were used. Brief requirement summaries below avoid reproducing rule text.

## Executive summary

The app is a useful tabletop workflow aid, but it is **not currently demonstrable as an official-rules implementation**. The most consequential confirmed executable defect is that melee uses the shooting defence/save-cancellation algorithm. Mission completion is also globally replaced by “all NPOs dead = victory”, while every mission JSON describes a different objective. Several mission rules exist only as prose and are never executed. Events are drawn automatically whenever Grade is 3, with replacement, and only four of six listed event effects alter state; event duration/cleanup is not modelled.

The NPO “AI” is a generic seven-question heuristic, not per-operative official decision tables. It raises Threat on every selected Fight/Shoot recommendation before combat occurs. Reinforcement quantity is fixed to current Grade and type is selected from the starting 2D6 table, but current authoritative tables/timing could not be recovered, so those exact numbers are not certified. Persistence captures much state, including pending combat drafts, but temporary event state is absent and data/code versions can be mixed because JSON is network-first while images/PDF are cache-first and the purported PDF is not a PDF.

### Finding totals

* Severity: **P0 2**, **P1 23**, **P2 25**, **P3 1** (51 severity-rated findings; the seven compliant findings do not receive severity).
* Classification: **COMPLIANT 7**, **PARTIAL 16**, **NON-COMPLIANT 14**, **MISSING 7**, **UNVERIFIABLE 14**, **INTENTIONAL ABSTRACTION 4**, **HOUSE RULE 2** (64 total audited findings).
* The scorecard does not report a percentage: current official source unavailability prevents a closed, exhaustive denominator for event cards, NPO tables, errata and team datacards.

## Compliance scorecard

Counts below include only the five requested scorecard classes; abstraction/house-rule rows are separately inventoried.

| Category | Compliant | Partial | Non-compliant | Missing | Unverifiable |
|---|---:|---:|---:|---:|---:|
| Game setup | 2 | 2 | 0 | 0 | 2 |
| Strategy Phase | 1 | 2 | 2 | 0 | 1 |
| Tomb World Events | 0 | 2 | 1 | 1 | 2 |
| Threat and Grade | 2 | 1 | 2 | 1 | 0 |
| Initiative and activations | 2 | 1 | 1 | 0 | 1 |
| NPO decision engine | 0 | 1 | 2 | 2 | 1 |
| Combat resolution | 0 | 2 | 3 | 1 | 1 |
| Reinforcements | 0 | 1 | 1 | 1 | 2 |
| Missions and scoring | 0 | 1 | 2 | 1 | 1 |
| Data completeness | 0 | 0 | 0 | 0 | 3 |
| Persistence and caching | 0 | 3 | 0 | 0 | 0 |
| **Total** | **7** | **16** | **14** | **7** | **14** |

> The scorecard counts each of the 58 atomic compliance findings once in its primary category. The five critical rows repeat findings expanded in later sections and are not counted twice. The four intentional abstractions and two house rules are outside the five scorecard columns. No percentage is calculated because authoritative-source gaps prevent claiming that the 58 findings are an exhaustive rules denominator.

## Critical findings

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| COM-01 | P0 | NON-COMPLIANT | Fight resolves by alternating strike/parry choices with attack dice; it does not roll defence dice or retain cover saves. | `resolveCombat()` calls `resolveDefense()` for both `shoot` and `melee`; both Player and NPO melee screens offer cover and resolve saves. | `app.js:1537–1558` (`resolveCombat`); `app.js:1596–1604`; `app.js:2187–2208`; `app.js:2234–2245` | CORE, **Fight** action; **Resolve Attack Dice** (melee); page unavailable | Split Fight from Shoot resolution; implement both combatants’ melee pools and alternating strike/parry selection. |
| MIS-01 | P0 | NON-COMPLIANT | Each Tomb World mission ends only under its mission-specific victory/defeat conditions. | `checkGameEnd()` declares victory whenever any generated roster has no living NPO, regardless of mission objective; the `completed` field is never driven by mission rules. | `app.js:229–237` (`checkGameEnd`); `app.js:682`; `Missions/01…06` `victory` objects | TW, **Missions 1–6**, maps/rules pp. 17–19 association; rule pages unavailable | Add mission-specific end evaluators; do not treat clearing all NPOs as universal victory. |
| EVT-01 | P1 | NON-COMPLIANT | Tomb World Events occur only at their printed eligibility/timing and resolve their full card effect for the stated duration. | Every Strategy phase at Grade 3 draws one of six uniformly; no TP, initiative, Threat subrange, mission, “once”, or prior-card eligibility metadata exists. | `app.js:144–151` (`events`); `app.js:972–1000` (`startTurningPoint`) | TW, **Tomb World Events** rule and event table/cards; page unavailable | Encode explicit eligibility, roll/table mapping, timing and duration metadata from a verified pack. |
| NPO-01 | P1 | NON-COMPLIANT | NPOs use their official operative-specific behaviour/priority table in printed order. | Four profile labels feed one generic heuristic; Guardian has no distinct branch except Charge preference, and no official per-NPO priority data is stored. | `app.js:137–142` (`profiles`); `app.js:1688–1696` (`npoQuestions`); `app.js:1998–2071` | TW/JO, **NPO Datacards and Behaviour/Action Priorities**; page unavailable | Transcribe verified per-profile ordered decisions into structured data and test every branch. |
| MIS-02 | P1 | MISSING | Mission-specific Strategic Gambits, actions, random results, state changes and end checks must be resolved at printed timing. | Mission JSON is rendered as escaped prose. `startTurningPoint`, Player activation, and end-step code never dispatch on `missionId` or rule IDs. | `app.js:212–217`; `app.js:598–599`; `app.js:972–1023`; `app.js:1101–1499`; `app.js:2262–2268` | TW, **Missions 1–6** special rules; pages associated with pp. 17–19 | Add structured mission rule IDs and explicit state transitions after separate rules-fix PRs. |

## Game setup

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| SET-01 | — | COMPLIANT | Select one of the six Tomb World missions and use its killzone layout. | Manifest loads exactly six sorted mission definitions and setup requires map checklist confirmation. | `app.js:61–74` (`loadMissionPack`); `app.js:512–519`; `Missions/manifest.json:1–39` | TW, **Missions 1–6**, map layouts pp. 17–19 association | None. |
| SET-02 | — | COMPLIANT | Begin at Turning Point 1 after setup. | Setup stores TP 0, then `startTurningPoint()` increments to 1. | `app.js:647–650`; `app.js:972–973` | CORE, **Battle Sequence / Turning Points**; JO, **Set Up the Battle** | None. |
| SET-03 | P1 | PARTIAL | Build a legal Player kill team under the current selected team’s operative-selection rules and any Joint Ops player-count adjustment. | UI enforces roster bounds, one Gravis and max gunners, but many `selectionRules` fields are display/data only and Joint Ops team-size adjustment is not an explicit engine rule. | `app.js:119–123`; `app.js:169–184`; `app.js:499–582`; Player JSON `selectionRules` | JO, **Select Kill Team(s)**; DK/DW/KAS, **Operative Selection** | Validate every selection-rule field in code and encode Joint Ops solo/co-op adjustments. |
| SET-04 | P2 | PARTIAL | Starting NPO quantity, table, order and deployment must match the selected mission and battlefield maximum. | Formula and prose deployment are present, but generation can exceed the global ten-model limit and setup does not enforce Conceal orders in state. | `app.js:306–316`; `app.js:583–595`; mission JSON `startingNpos` | TW, **Determine NPOs / NPO Generation Table** and each mission **Setup** | Cap/resolve overflow exactly as printed and model orders, after verifying the table. |
| SET-05 | P2 | UNVERIFIABLE | Starting NPO type probabilities must use the official generation table. | A hard-coded 11-entry lookup indexed by 2D6 implements outcomes 2–12, but no official table is available to confirm every cell. | `app.js:310–314` (`table`) | TW, **NPO Generation Table**; page unavailable | Verify all 11 results against a first-party copy; move table to structured sourced data. |
| SET-06 | P2 | UNVERIFIABLE | Every mission’s precise placement, territory, marker, drop-zone and battlefield-limit instructions must match the pack. | JSON provides summaries/maps, but the tracked “PDF” cannot validate wording or geometry; setup uses four generic checks only. | `Missions/01…06`; `app.js:513–519`; `Assets/Tomb-World-Mission-Pack.pdf:1–42` (SVG markup) | TW, **Missions 1–6 Setup**, maps pp. 17–19 association | Replace invalid source asset only in a separately licensed/content PR; validate each map and instruction. |

### P1/P2 setup scenarios

* **SET-03 — integration test.** **Given** each supported team and every illegal selection described by its official Operative Selection rule, **when** setup attempts to continue, **then** continuation is blocked and the precise unmet rule is shown.
* **SET-04 — integration/manual mobile test.** **Given** a starting roll above the applicable battlefield allowance, **when** the NPO roster is generated at 390 px, **then** the official partial/blocked procedure is followed, all deployed NPOs have the correct order, and controls remain visible.
* **SET-05 — automated unit test.** **Given** each 2D6 result from 2 through 12, **when** the generation table is evaluated, **then** the official NPO type is returned.
* **SET-06 — manual tabletop test.** **Given** each official mission diagram, **when** the app setup map/checklist is followed, **then** every wall, hatch, marker, territory and drop zone matches.

## Strategy Phase

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| STR-01 | — | COMPLIANT | Ready eligible operatives at the Ready step before the Firefight phase. | Living NPOs and living Player operatives are reset at TP start; casualties remain excluded. | `app.js:972–981` (`startTurningPoint`); `app.js:249–253` | CORE, **Strategy Phase — Ready**; JO, **Ready NPOs** | None, subject to reinforcement timing correction. |
| STR-02 | P1 | NON-COMPLIANT | Resolve the official ordered Strategy phase, including mission rules at their exact sub-step. | Reinforcement/event state is mutated immediately on pressing Start TP, before the displayed CP/ploy/ability checklist; Destroy Sarcophagus repair is never executed. | `app.js:972–1000`; `app.js:709–717`; `Missions/04-destroy-sarcophagus.json:24–27` | CORE, **Strategy Phase**; TW, Mission 4 **Nanoscarab Repair** | Implement ordered sub-stages and mission hooks; do not mutate later-step results early. |
| STR-03 | P1 | NON-COMPLIANT | Event cleanup/expiry occurs when printed, and persistent effects remain only for their printed duration. | No active-event/effect state or cleanup exists; Countertemporal Shifting is text only. | `app.js:144–151`; `app.js:1025–1055`; `app.js:972–1023`; initial state `app.js:153–163` | TW, **Tomb World Events**, **Countertemporal Shifting** | Add typed temporary-effect state and deterministic expiry. |
| STR-04 | P2 | PARTIAL | Initiative follows the official roll and tie procedure after preceding Strategy steps. | Two D6 are rolled; ties are awarded to Player, but UI allows unlimited rerolls and arbitrary override without recording a rules source. | `app.js:709–717`; `app.js:944–970`; `app.js:1002–1023` | CORE, **Determine Initiative**; JO, initiative modification if any | Restrict official path; label override as correction/abstraction and log it. |
| STR-05 | P2 | PARTIAL | Strategy resources and ploys/abilities must be resolved, including current CP state where relevant. | App only gives a manual checklist and stores no CP, ploy, or strategy-ability state. | `app.js:709–715` | CORE, **Strategy Phase — Generate CP / Strategic Ploys** | Explicitly scope as tabletop-only or track rules-relevant choices that affect automation. |
| STR-06 | P2 | UNVERIFIABLE | Reinforcement and event order must match the current Tomb World sequence. | Code generates reinforcements, then an event, then initiative; authoritative pack sequence was unavailable. | `app.js:972–1023` | TW, **Strategy Phase / Reinforcements / Tomb World Events**; page unavailable | Verify sequence against current first-party pack before changing. |

### P1/P2 Strategy scenarios

* **STR-02 — integration test.** **Given** Mission 4 has Destruction points and the next Strategy phase begins, **when** the Ready step is resolved, **then** Nanoscarab Repair is prompted/calculated exactly at that step before later Strategy results.
* **STR-03 — saved-game restoration test.** **Given** a one-Turning-Point event is active, **when** the game is reloaded and later finishes that Turning Point, **then** the effect survives reload and expires exactly once.
* **STR-04 — automated/integration test.** **Given** tied initiative dice, **when** initiative is determined, **then** the printed tie rule is applied and no free reroll changes it.
* **STR-05 — integration test.** **Given** a ploy changes an automated attack or activation, **when** it is selected in Strategy, **then** the later calculation reflects it or the UI clearly delegates the complete calculation to tabletop play.
* **STR-06 — automated trace test.** **Given** a TP eligible for both reinforcement and event processing, **when** Strategy runs, **then** logged mutation order equals the official sequence.

## Tomb World Events

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| EVT-01 | P1 | NON-COMPLIANT | See Critical findings. | Uniform Grade-3 draw without card eligibility. | `app.js:144–151`; `app.js:993` | TW, **Tomb World Events** | Add verified metadata/table. |
| EVT-02 | P1 | PARTIAL | Every event’s complete immediate and ongoing effect must be resolved. | Awakened Warrior, Living Metal Flux and Stirrings mutate state; Chittering Drone has user-resolved state. Maze Reforms and Countertemporal Shifting are text only. | `app.js:1025–1055`; `app.js:725–845` | TW, six named **Tomb World Event** entries | Implement typed state/board prompts and cleanup for every automatable consequence. |
| EVT-03 | P1 | MISSING | The complete official deck/table, including duplicate weighting if printed, must be represented. | Exactly six unique objects exist; no official count, roll range, duplicate/weight or deck-exhaustion model exists. | `app.js:144–151` | TW, **Tomb World Events table/deck** | Re-inventory from a current first-party copy and encode weights/identifiers. |
| EVT-04 | P2 | PARTIAL | Event-generated NPO placement/readiness and battlefield cap follow the event text. | Added event NPOs are `ready:true,deployed:true` without entry-point state; cap is enforced, but Awakened Warrior silently does nothing at cap. | `app.js:988`; `app.js:1029`; `app.js:1048–1053`; `app.js:714` | TW, **Awakened Warrior** and **A Chittering Drone** | Store pending placement, show blocked/partial result, and apply exact printed readiness/order. |
| EVT-05 | P2 | UNVERIFIABLE | Titles and summarized effects must match the current official entries. | Six plausible titles/effects are present, but no accessible official card text exists in repo or audit environment. | `app.js:144–151` | TW, named event entries; page unavailable | Compare title, roll result, choices, quantity, timing and duration word-by-word in a licensed review. |
| EVT-06 | P3 | UNVERIFIABLE | Reuse/reshuffle follows the official event mechanism. | `roll(events.length)` samples with replacement; no deck/discard state exists. | `app.js:993`; initial state `app.js:153–163` | TW, **Tomb World Events — generating/reusing events**; page unavailable | Encode the printed mechanism once verified. |

### P1/P2 event scenarios

* **EVT-01 — automated unit test.** **Given** every boundary TP/Grade/Threat/initiative state, **when** event eligibility is evaluated, **then** only officially eligible results can occur.
* **EVT-02 — integration test.** **Given** each of the six events, **when** it resolves, **then** every immediate mutation, user choice, board prompt, duration and cleanup is represented once.
* **EVT-03 — automated data test.** **Given** the official event table/deck, **when** app IDs and weights are enumerated, **then** no official entry is missing or duplicated and no unofficial entry exists.
* **EVT-04 — integration/manual tabletop test.** **Given** nine and ten active NPOs, **when** either spawning event resolves, **then** placement, partial/block handling, order and Ready state match the card.
* **EVT-05 — manual content test.** **Given** the current first-party event page, **when** every field in Appendix A is checked, **then** titles, effects, choices and timings match without relying on summaries.

## Threat and Grade

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| THR-01 | — | COMPLIANT | Threat begins at zero and is bounded 0–15. | Initial state is 0; `setThreat` clamps to 0–15. | `app.js:153–160`; `app.js:293–303` | TW, **Threat Level** | None. |
| THR-02 | — | COMPLIANT | Grade thresholds are 0 at Threat 0, 1 at 1–5, 2 at 6–10 and 3 at 11–15. | `threatGrade` implements those thresholds; HUD calls the same function used by Strategy. | `app.js:289–291`; `app.js:673`; `app.js:980` | TW, **Grade Level** | None. |
| THR-03 | P1 | NON-COMPLIANT | Threat changes only when the printed triggering action/effect actually occurs and by its printed amount, including mission exceptions. | Threat increases when the NPO recommendation is chosen, before any Fight/Shoot is resolved; cancellation/missed/invalid attack does not undo it. | `app.js:2042–2084`; `app.js:2130–2149` | TW, **Threat Level — increasing/decreasing Threat** | Apply changes on confirmed triggering action resolution, using explicit trigger IDs. |
| THR-04 | P1 | NON-COMPLIANT | Mission exceptions modify standard Threat triggers. | Scout Sub-Crypt says Operate Hatch does not increase Threat, but Player activation always assigns Hatch 1 Threat; no mission check exists. | `Missions/05-scout-sub-crypt.json:24–30`; `app.js:1159–1187`; `app.js:1426–1439` | TW, Mission 5 **Dormant** | Route action Threat through mission-aware rules. |
| THR-05 | P1 | MISSING | All official increases and decreases—including Scout Room reduction—must be executable or unambiguously delegated. | A generic manual ± control exists, but Scout Room is only prose and no reason/target-grade calculation is implemented. | `app.js:673`; `app.js:1061–1075`; `Missions/05-scout-sub-crypt.json:28–30` | TW, **Threat Level**; Mission 5 **Scout Room** | Implement enumerated triggers/decreases; retain manual correction separately. |
| THR-06 | P2 | PARTIAL | Displayed and restored Threat/Grade must match engine state. | Both derive from persisted `state.threat`, but malformed imported nonnumeric Threat is not normalized; `NaN` can produce Grade 3 and invalid HUD width. | `app.js:186–210`; `app.js:289–297`; `app.js:673`; import `app.js:2390–2404` | TW, **Threat/Grade**; rules outcome must use valid level | Validate/clamp on normalize/import. |

### P1/P2 Threat scenarios

* **THR-03 — integration test.** **Given** an NPO is recommended to Shoot, **when** the user cancels before a legal attack occurs, **then** Threat does not change; after confirmed triggering resolution it changes exactly once.
* **THR-04 — integration test.** **Given** Scout Sub-Crypt, **when** a Player operative operates a hatch, **then** Threat remains unchanged.
* **THR-05 — integration test.** **Given** a legal Scout Room action at each Grade, **when** it resolves, **then** Threat becomes the official highest level of the grade below and never an arbitrary manual value.
* **THR-06 — saved-game restoration test.** **Given** imported Threat values `null`, `"x"`, `-1`, and `99`, **when** state normalizes, **then** engine/HUD contain a valid identical official level/grade.

## Initiative and activations

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| ACT-01 | — | COMPLIANT | Alternate sides while both have eligible ready operatives; if one side has none, the other continues. | `setNextActivation` implements exactly that scheduling shape. | `app.js:263–287`; `app.js:692–698` | CORE, **Firefight Phase / Activating Operatives**; JO, **NPO Activations** | None, subject to initiative/NPO-selection details. |
| ACT-02 | — | COMPLIANT | An operative cannot activate twice in one TP and incapacitated operatives cannot activate. | Player IDs are tracked; NPO `ready` is cleared; casualty/wound filters exclude both. | `app.js:222–253`; `app.js:1101–1121`; `app.js:2074–2084` | CORE, **Ready/Activated** and **Incapacitated** | None. |
| ACT-03 | P1 | NON-COMPLIANT | Activation is completed after its actions/mandatory resolution, not before an attack wizard is confirmed. | NPO is marked not ready, activation counters/history advanced, next side selected, and Threat changed before target/combat; exiting leaves the activation consumed and unresolved. | `app.js:2074–2086`; `app.js:2097–2150` | CORE, **Activate Operative**; JO, **NPO activation procedure** | Stage all changes and commit atomically only after required attack/mission effects complete. |
| ACT-04 | P2 | PARTIAL | Reinforcements/revived models receive the printed ready/activated state and enter the alternating queue accordingly. | All standard and event-generated NPOs are immediately ready; manually restored NPOs retain whatever toggled state the UI assigns. | `app.js:984–990`; `app.js:1029–1051`; `app.js:2270–2331` | TW/JO, **Reinforcements / returned NPOs** | Encode source-specific arrival readiness. |
| ACT-05 | P2 | UNVERIFIABLE | The first NPO chosen must follow the official NPO selection priority/tie-break. | `nextNpo()` sorts ready NPOs by behaviour rank then wounds/name; current official selection table unavailable. | `app.js:1500–1530` (`sortOperativesGlobally`, `nextNpo`) | JO/TW, **Select an NPO / tie-breakers**; page unavailable | Verify and data-drive selection priority and ties. |

### P1/P2 activation scenarios

* **ACT-03 — integration and reload test.** **Given** an NPO plan includes an attack, **when** the user exits or reloads before combat confirmation, **then** the NPO remains ready and no counters, Threat or next-side state commit; successful completion commits once.
* **ACT-04 — automated/integration test.** **Given** each source of a new/restored NPO, **when** it enters in each possible phase, **then** readiness and queue eligibility match the source rule.
* **ACT-05 — automated unit test.** **Given** every pair of eligible NPO profiles and every official tie, **when** `nextNpo` is selected, **then** the official priority/tie result is returned.

## NPO decision engine

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| NPO-01 | P1 | NON-COMPLIANT | See Critical findings. | Generic heuristic replaces profile tables. | `app.js:137–142`; `app.js:1998–2071` | TW/JO, **NPO behaviours** | Data-drive exact tables. |
| NPO-02 | P1 | NON-COMPLIANT | Evaluate official priorities in printed order, including valid action restrictions and fallback branches. | `nextNpoQuestionKey` asks objective before determining attack; the final resolver always prioritizes engaged Fight, then selective Charge, Shoot, hatch, objective. Branches collect `clustered`, but official tie logic and legal action/AP constraints are absent. | `app.js:1688–1696`; `app.js:1998–2011`; `app.js:2042–2071` | JO/TW, **NPO Action Priorities / Target Selection** | Model ordered predicates and explicit terminal actions per profile. |
| NPO-03 | P1 | MISSING | NPO action legality includes order, engagement, range/visibility, movement, AP and operative restrictions. | User answers broad Yes/No prompts; engine never calculates positions, LOS, order, AP or weapon restrictions. | `app.js:1688–1696`; `app.js:1993–2039` | CORE, **Valid Target**, **Engagement Range**, **Action restrictions**; JO, **NPO decisions** | Either collect every required fact precisely or label recommendations non-authoritative and require tabletop validation. |
| NPO-04 | P2 | PARTIAL | Target priority and ties follow printed criteria, with final ties resolved as instructed. | Objective, wounded, clustered, closest are hard-coded, but no distance values, multiple candidate ranking, stable official tie-break, or selected-target validation against the answered predicate exists. | `app.js:2044–2048`; `app.js:2097–2146` | JO/TW, **NPO Target Priority / ties** | Collect candidates and rank using structured criteria; explain tie resolution. |
| NPO-05 | P2 | MISSING | Grade- and mission-dependent NPO behaviour must be applied where printed. | Decision code never reads `threatGrade()` or `missionId`. | `app.js:1998–2084` | TW, **Grade effects**, mission NPO rules, NPO tables | Add explicit conditional branches after source verification. |
| NPO-06 | P2 | UNVERIFIABLE | Four supported NPO behaviour labels/profiles must correspond to official profiles and terms. | Marksman, Brawler, Sentinel and Guardian are present, but no official data source is bundled. | `app.js:137–142` | TW, **NPO datacards/behaviour tables**; page unavailable | Verify names, behaviour categories and every profile. |

### P1/P2 NPO scenarios

* **NPO-01 — table-driven unit tests.** **Given** every Yes/No node on every official NPO table, **when** its conditions are supplied, **then** the printed next node/action is reached.
* **NPO-02 — branch-coverage unit test.** **Given** Fight, Charge, Shoot, objective, hatch and fallback combinations, **when** priorities resolve, **then** no lower priority pre-empts a higher one and every printed branch is reachable.
* **NPO-03 — manual tabletop/integration test.** **Given** concealed, engaged, out-of-range and insufficient-AP states, **when** prompts are answered accurately, **then** the app cannot recommend an illegal action.
* **NPO-04 — integration test.** **Given** two or more legal targets spanning each priority and a tie, **when** target selection runs, **then** it picks the official target or prompts for the official favourable tie.
* **NPO-05 — unit test.** **Given** every Grade and each mission-specific modifier, **when** the same battlefield predicate set is evaluated, **then** only printed conditional changes occur.
* **NPO-06 — data snapshot test.** **Given** the official NPO cards, **when** app profiles are serialized, **then** every characteristic, weapon and behaviour ID matches.

## Combat resolution

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| COM-01 | P0 | NON-COMPLIANT | See Critical findings. | Shooting saves applied to melee. | `app.js:1537–1558`; `app.js:2187–2245` | CORE, **Fight** | Separate engines. |
| COM-02 | P1 | NON-COMPLIANT | Weapon special rules (e.g. Lethal, Piercing/Piercing Crits, Devastating, Brutal, Shock, Stun, Hot, Torrent/Blast) apply exactly as printed. | Parser only recognizes `AP`, `Piercing`, `Lethal` and `Devastating`; Piercing Crits is treated as unconditional AP by prefix matching, Devastating damage is not applied, and all other rules are ignored. | `app.js:1532–1558` (`parseDamage`, `weaponRuleValue`, `resolveCombat`); Player JSON `weapons[].rules` | CORE, **Weapon Rules**; team datacards | Implement a tested typed rule interpreter or explicitly delegate unsupported weapons. |
| COM-03 | P1 | NON-COMPLIANT | Retained cover saves replace a defence die result and remain subject to legal cover/order/weapon-rule conditions; AP changes defence dice as printed. | Cover adds a normal save after rolling `defenseDice - ap` dice, effectively producing an extra save; UI permits cover for melee and ignores Saturate/No Cover equivalents. | `app.js:2200–2208`; `app.js:2234–2245`; Player combat `app.js:1596–1604` | CORE, **Shoot — Roll Defence Dice / Cover** and **Piercing** | Correct retained-die pool construction and validate cover eligibility; never show it for Fight. |
| COM-04 | P1 | MISSING | NPO ranged and melee weapons use their distinct official profiles and rules. | Each NPO has one generic `attack` object used for both recommended Shoot and Fight. | `app.js:137–142`; `app.js:2141`; `app.js:2187–2208` | TW, **NPO Datacards — weapons** | Store and select separate official weapons by action/range. |
| COM-05 | P2 | PARTIAL | Critical and normal shooting saves cancel attack dice in the official sequence. | Critical saves cancel criticals then normals; normal saves cancel normals. However cover/AP pool errors and ignored rules make full resolution partial. | `app.js:2234–2245` | CORE, **Resolve Successful Saves** | Retain cancellation core, fix surrounding dice construction/rules and add vectors. |
| COM-06 | P2 | PARTIAL | Damage and incapacitation commit once and survive navigation/reload. | Player attacks stage damage until activation confirmation and NPO commit button has a local double-click guard. But an NPO combat draft can be reopened after reload and completion history lookup is not uniquely keyed. | `app.js:1404–1499`; `app.js:2152–2182`; `app.js:2184–2231` | CORE, **Inflict Damage / Incapacitated** | Add durable combat transaction IDs and committed status. |
| COM-07 | P2 | UNVERIFIABLE | Player datacard attack values and current balance changes must be current. | Data claims revisions, but no current official team documents were available to validate every characteristic and option. | `Player_Operatives/*.json` `source`, `operatives`, `weapons` | DK/DW/KAS datacards; FAQ/Balance Dataslate | Perform licensed field-by-field comparison and record source revision/hash. |

### P0/P1/P2 combat scenarios

* **COM-01 — automated integration test.** **Given** both combatants have melee dice, **when** Fight resolves, **then** no defence/cover dice are rolled and users alternate legal strike/parry choices until the Fight ends.
* **COM-02 — table-driven unit tests.** **Given** at least one weapon for every supported special rule and critical/noncritical roll patterns, **when** combat resolves, **then** official dice and damage transformations occur exactly once.
* **COM-03 — unit test.** **Given** 3 Defence, AP1 and one legally retained cover save, **when** defence resolves, **then** the total dice/results equal the official retained-plus-rolled pool—not three rolled plus a bonus—and illegal cover is unavailable.
* **COM-04 — integration test.** **Given** an NPO with different ranged/melee profiles, **when** it Shoots versus Fights, **then** the correct A/BS-or-WS/Damage/rules profile is used.
* **COM-05 — deterministic unit test.** **Given** fixed critical/normal attack and save arrays, **when** cancellation resolves, **then** remaining dice match official examples, including cover and AP variants.
* **COM-06 — saved-game restoration test.** **Given** a pending and a committed attack, **when** each is reloaded and buttons/navigation are repeated, **then** pending damage can commit once and committed damage cannot reapply.
* **COM-07 — data snapshot/manual source test.** **Given** current official team documents and balance update, **when** all supported loadouts are compared, **then** every automated characteristic is current.

## Reinforcements

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| REI-01 | P1 | NON-COMPLIANT | Reinforcements follow the printed timing/table/quantity and mission/event exceptions. | Every TP after first at Grade >0 requests exactly `grade` NPOs, each rolled on the same 2D6 type table. No Threat subrange/mission eligibility exists. | `app.js:972–993`; `app.js:306–316` | TW, **Reinforcements / NPO Generation Table** | Encode verified eligibility and quantity/table separately. |
| REI-02 | P1 | MISSING | Scout Sub-Crypt room awakening immediately generates D3 + Grade (max 5) NPOs when a room first opens/enters. | Rule is prose only; no room state or spawn action exists. | `Missions/05-scout-sub-crypt.json:18–30`; no mission dispatch in `app.js:972–2231` | TW, Mission 5 **Awaken Rooms** | Add room IDs, first-entry tracking, constrained generation and placement workflow. |
| REI-03 | P2 | PARTIAL | Battlefield maximum, partial arrivals, fully blocked arrivals and placement must follow the pack. | Global max 10 and partial/block counts exist. NPO objects are nevertheless `deployed:true` before the user selects/physically confirms an entry point; one shared string represents all entries. | `app.js:9`; `app.js:714`; `app.js:984–992`; `app.js:1009–1013` | TW, **Battlefield Limit / Reinforcement Entry Points** | Create pending arrivals and confirm each placement; preserve partial/full block messages. |
| REI-04 | P2 | UNVERIFIABLE | Standard reinforcement arrival order/readiness is as printed. | Arrivals are always Ready and have no order field. | `app.js:988` | TW, **Reinforcements**; page unavailable | Verify and store order/readiness. |
| REI-05 | P2 | UNVERIFIABLE | The battlefield maximum is ten in all supported situations or exceptions are applied. | `MAX_NPOS=10` is global for setup, standard and events (except starting generation does not enforce it). | `app.js:9`; `app.js:984–990`; `app.js:1029`; `app.js:2331` | TW, **Maximum NPOs on the battlefield**; page unavailable | Verify scope/exceptions, then centralize one capacity function. |

### P1/P2 reinforcement scenarios

* **REI-01 — table-driven integration test.** **Given** every TP/Threat/Grade/mission boundary, **when** reinforcement processing occurs, **then** eligibility, number and type rolls equal the official table.
* **REI-02 — integration/manual tabletop test.** **Given** each eligible room unopened at every Grade, **when** it is first opened or entered, **then** exactly D3+Grade up to five legal NPOs are prompted once and constrained by limits.
* **REI-03 — integration/mobile test.** **Given** 8, 9 and 10 active NPOs and multiple rolled arrivals, **when** reinforcement placement occurs at 390 px, **then** partial/full blocking and every entry placement are correct and no NPO is marked deployed prematurely.
* **REI-04 — integration test.** **Given** a new reinforcement, **when** Firefight begins, **then** order and Ready status match the printed arrival rule.
* **REI-05 — automated unit test.** **Given** setup, Strategy, event and room-spawn sources at capacity, **when** each requests NPOs, **then** one verified capacity rule consistently applies.

## Missions and scoring

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| MIS-01 | P0 | NON-COMPLIANT | See Critical findings. | Universal roster-cleared victory. | `app.js:229–237` | TW, **Missions 1–6 Victory** | Mission evaluators. |
| MIS-02 | P1 | MISSING | See Critical findings. | Mission prose never executes. | mission `rules`; `app.js:972–2231` | TW, **Missions 1–6** | Structured mission state. |
| MIS-03 | P1 | NON-COMPLIANT | Mission progress/end conditions use the printed condition and timing; some are not VP tracks. | One freely editable numeric tracker with a static maximum is used for all missions, and `completed` is never set from it. Regroup’s end-of-TP predicate and Shifting Labyrinth’s half-of-original-team result are not evaluated. | `app.js:214–215`; `app.js:685–690`; `app.js:682`; all mission `tracker`/`victory` objects | TW, each mission **Victory** and mission actions | Replace generic tracker with mission-specific typed state and exact timing. |
| MIS-04 | P2 | PARTIAL | Display setup, objective and special rules for each supported mission. | Six mission rows include setup, rule summaries and victory prose, but important action costs/eligibility/random state can be lost in summaries and nothing validates current source. | `Missions/01…06`; `app.js:2262–2268` | TW, **Missions 1–6** | Preserve briefing, but verify content and clearly identify tabletop-only rules. |
| MIS-05 | P2 | UNVERIFIABLE | VP values, maximum scores and tie conditions match official missions where those concepts apply. | JSON presents binary win/lose, not VP/tie data. Without the pack, it is unclear whether these six use binary outcomes exclusively. | all mission `victory` objects; absence of `vp`/`tie`; `app.js:2268` | TW, **Missions 1–6 Victory**; pages unavailable | Verify whether VP/ties exist; add only if printed. |

### P0/P1/P2 mission scenarios

* **MIS-01 — integration tests (six cases).** **Given** each mission with all NPOs eliminated but objective incomplete, **when** the last NPO is removed, **then** no false victory occurs; test each printed victory and defeat independently.
* **MIS-02 — integration tests.** **Given** each special rule in Appendix B, **when** its printed trigger occurs, **then** its prompt/state/random result happens at the exact timing and survives reload if ongoing.
* **MIS-03 — integration tests.** **Given** objective progress immediately below/at/above each mission threshold, **when** its scoring/end timing occurs, **then** the correct result is reached without free numeric editing.
* **MIS-04 — manual mobile content test.** **Given** each official mission page, **when** briefing/map is reviewed at 390 px, **then** every play-critical instruction is visible, accurate and unclipped.
* **MIS-05 — manual source/data test.** **Given** official Victory sections, **when** app schemas are compared, **then** every VP, cap, end and tie field that exists is represented.

## Data completeness

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| DAT-01 | P2 | UNVERIFIABLE | Supported Player teams/operatives, selection, APL, Move, Save, Wounds, weapons and abilities match current official rules. | Three teams are loaded; JSON has structured characteristics, weapons and named abilities, but many abilities are never automated and current first-party rules could not be checked. | `Player_Operatives/manifest.json`; `Player_Operatives/*.json`; `app.js:76–132` | DK/DW/KAS, **Operative Selection and Datacards**; FAQ | Obtain current first-party documents and produce field-level fixtures. |
| DAT-02 | P1 | UNVERIFIABLE | All official Tomb World NPO profiles, weapons, characteristics and special abilities supported by the mission pack are represented. | Four profiles are hard-coded with only wounds/save/one attack/behaviour; Move, APL, Defence, distinct weapons and abilities are absent. This is clearly incomplete as a general datacard, but exact missing fields/effects cannot be certified without source. | `app.js:137–142` | TW, **NPO Datacards** | Move complete verified profiles into structured data and declare automation coverage per field. |
| DAT-03 | P2 | UNVERIFIABLE | Mission/event/reinforcement datasets are complete and current. | Missions are JSON, while events, reinforcement probabilities and NPOs are hard-coded JS; manifest metadata is self-asserted and invalid local PDF prevents validation. | `Missions/manifest.json`; `app.js:137–151`; `app.js:306–316`; invalid `Assets/Tomb-World-Mission-Pack.pdf` | TW, complete pack; revision 19 Nov 2025 claimed only by repository | Add source revision/hash provenance after authoritative review; keep implementation evidence distinct from authority. |

### Supported-data inventory

* **Player teams:** Death Korps, Deathwatch, Kasrkin (`Player_Operatives/manifest.json`).
* **Player operatives:** every object in the three `operatives` arrays; the engine consumes Wounds, Save, APL, weapon A/hit/damage/rules and some selection flags. Move/base size and most abilities are display-only or unused.
* **NPOs:** Necron Warrior, Canoptek Scarab Swarm, Canoptek Macrocyte, Canoptek Tomb Crawler (`profiles`). Only Wounds, Save, one attack and behaviour are stored.
* **Missions:** the six rows in Appendix B.
* **Events:** the six candidate rows in Appendix A.
* **Hard-coded rules data:** `profiles`, `events`, starting/reinforcement 2D6 `table`, `MAX_NPOS`, Grade thresholds, Threat bounds and generic action costs in `app.js`.

### P1/P2 data scenarios

* **DAT-01 — source snapshot and unit tests.** **Given** each current official team document, **when** selection/profile/loadout fixtures are compared, **then** all consumed values and supported special rules match.
* **DAT-02 — source snapshot test.** **Given** every official Tomb World NPO datacard, **when** structured profiles are compared, **then** no profile/weapon/ability required by automated play is absent.
* **DAT-03 — schema/content test.** **Given** a verified pack revision, **when** missions/events/tables are inventoried, **then** counts, IDs, weights and source revision/hash are complete and consistent.

## Persistence and caching

| ID | Severity | Classification | Official requirement | Current app behavior | Evidence in repository | Official source | Recommended correction |
|---|---|---|---|---|---|---|---|
| PER-01 | P1 | PARTIAL | All rules-relevant permanent state (wounds, incapacitation, readiness, initiative, TP, mission state) survives reload consistently. | Core scalar/roster/activation state is saved and casualties restore, but mission-specific state mostly does not exist; normalization performs minimal validation. | `app.js:153–210`; save calls throughout; mission state limited to `tracker` | CORE/JO, **battle state and Turning Point sequence**; TW mission ongoing effects | Add schema version/migrations and typed mission state after rule implementation. |
| PER-02 | P1 | PARTIAL | Temporary effects and pending/committed attacks survive reload and expire/commit exactly once. | Combat drafts persist, but no durable transaction/commit ID exists; event temporary effects are text and cannot survive/expire. | `app.js:201–207`; `app.js:1404–1499`; `app.js:2097–2231`; no active-effect state in `initialState` | CORE, **Attack sequence**; TW, event durations | Add idempotent transactions and effect expiry metadata. |
| PER-03 | P2 | PARTIAL | Cache updates cannot combine obsolete rules data with current code. | JS/CSS/JSON are network-first under cache `4.0.1`, static images/PDF are cache-first; invalid “PDF” is precached. Update activation deletes old named caches, but an open client can use old controller/code while fetching new JSON network-first. | `service-worker.js:3–57`; `app.js:21–59`; `app.js:63–94` | This is implementation integrity, not a tabletop rule; authoritative baseline is the versioned TW/team documents above | Pin rules-data schema/revision to app compatibility; validate manifest version before use; repair licensed source asset separately. |

### P1/P2 persistence scenarios

* **PER-01 — saved-game restoration matrix.** **Given** each phase, each initiative side, eliminated/ready operatives and every mission state, **when** reloaded, **then** the same next legal action and outcome remain.
* **PER-02 — saved-game restoration test.** **Given** every pending/committed attack and temporary event immediately before/after expiry, **when** reloaded/repeated, **then** damage/effect applies or expires exactly once.
* **PER-03 — service-worker integration test.** **Given** an installed old app and a deployment with changed code plus JSON, **when** one asset request succeeds and another is offline, **then** the app refuses an incompatible mix and offers a coherent cached version.

## Intentional abstractions and house rules

| ID | Classification | Behaviour | Rules impact / evidence | Official source |
|---|---|---|---|---|
| ABS-01 | INTENTIONAL ABSTRACTION | User answers LOS, range, control, cover and movement questions rather than the app modelling geometry. | Equivalent only if prompts gather every fact required by the official decision; current broad prompts contribute to NPO-03. `app.js:1688–1696`. | CORE, measurement/visibility/cover; JO NPO procedure |
| ABS-02 | INTENTIONAL ABSTRACTION | Physical terrain manipulation and some mission cleanup are delegated to a confirmation checkbox. | Outcome-preserving only for effects the app does not later need; otherwise becomes missing state. `app.js:685–690`; mission prose. | TW, mission rules and event cleanup |
| ABS-03 | INTENTIONAL ABSTRACTION | Manual Threat ± buttons permit correction. | Outcome-preserving as a correction control, but it bypasses audit logging of an official trigger. `app.js:673`; `app.js:1061–1075`. | TW, **Threat Level** |
| ABS-04 | INTENTIONAL ABSTRACTION | Initiative can be manually overridden. | Can preserve outcome for an external modifier/correction, but must not be presented as the normal official option. `app.js:709–717`; `app.js:1015–1023`. | CORE, **Determine Initiative** |
| HR-01 | HOUSE RULE | Unlimited “Reroll Both” initiative button. | Changes outcome unless an official effect grants the reroll; no cost/eligibility is checked. `app.js:936–970`. | CORE, **Determine Initiative** |
| HR-02 | HOUSE RULE | Generic “most dangerous legal option” NPO heuristic and universal all-NPOs-dead win. | Both change official outcomes; evidenced by `chooseNpoDecision` and `checkGameEnd`. | JO/TW NPO priorities; TW Missions 1–6 victory |

## Unverifiable items

The following cannot be responsibly upgraded from `UNVERIFIABLE` until a current first-party copy is available:

1. Whether the official event inventory contains exactly the six named entries, their weights/duplicates, roll mechanism, eligibility and reuse.
2. Exact NPO generation and reinforcement tables, battlefield-cap scope, entry, order and ready state.
3. Exact Tomb World NPO characteristics, weapons, abilities, behaviours, priority branches and tie-breakers.
4. Exact current mission wording, map geometry, VP/tie clauses and errata. The `.pdf` asset is SVG, so it supplies no rules evidence.
5. All current Death Korps, Deathwatch and Kasrkin profile/loadout/selection values and balance changes.
6. Any later FAQ, erratum or balance update explicitly applying to Tomb World/Joint Ops after the manifest’s claimed 19 Nov 2025 revision.

This is why Appendix A records every **candidate official event evidenced by the app** but does not falsely certify that it is the complete official deck.

## Recommended remediation plan

No remediation is implemented by this audit. Proposed pull requests are deliberately separated:

### PR 1 — Critical rules-engine corrections

* **Scope:** remove universal elimination victory; stage NPO activation atomically; introduce mission end-dispatch interface without implementing all mission content.
* **Files:** `app.js`, mission JSON schema/readmes, tests (new dependency-free browser harness if adopted).
* **Dependencies:** authoritative victory text; transaction design.
* **Risks:** saved games at end/pending activation; altered game-over flow.
* **Tests:** MIS-01 and ACT-03 matrices, all six missions, reload/idempotency, 390 px manual flow.
* **Version impact:** **major** (changes regular outcomes and state contract).

### PR 2 — Tomb World Event completeness and timing

* **Scope:** verified full inventory, eligibility/table, choices, typed immediate/ongoing effects, reuse and cleanup.
* **Files:** preferably new static event JSON plus `app.js`, `service-worker.js`, documentation/tests.
* **Dependencies:** licensed current TW event rules; PR 1 transaction/state pattern.
* **Risks:** RNG/save compatibility; NPO capacity interactions.
* **Tests:** EVT-01…05, deterministic RNG, event reload/expiry.
* **Version impact:** **minor** if additive after critical fix; **major** if saved-state schema is incompatible.

### PR 3 — Threat, Grade, and reinforcement corrections

* **Scope:** typed Threat triggers/decreases, mission exceptions, verified generation/reinforcement tables, capacity and pending placement.
* **Files:** `app.js`, structured rules data, Mission 5 JSON, `service-worker.js`, tests.
* **Dependencies:** authoritative tables; PR 2 event spawn API.
* **Risks:** roster RNG, queue ordering, old saves.
* **Tests:** THR-03…06, REI-01…05, fixed RNG and capacity boundaries.
* **Version impact:** **major** because frequency/rosters/outcomes change.

### PR 4 — NPO decision-engine corrections

* **Scope:** all verified per-profile tables, selection priority, targets/ties, Grade/mission branches, clearer predicates.
* **Files:** new NPO JSON or `app.js`, relevant mission JSON, UI text, tests.
* **Dependencies:** official NPO cards/tables; PR 3 profile/Grade data.
* **Risks:** recommendation changes across almost every NPO activation.
* **Tests:** NPO-01…06 exhaustive table/branch fixtures plus manual tabletop validation.
* **Version impact:** **major**.

### PR 5 — Combat-rule corrections

* **Scope:** separate Shoot/Fight engines; correct cover/AP dice pool; distinct NPO weapons; supported special-rule interpreter; durable combat transaction.
* **Files:** `app.js`, NPO/player data, tests; minimal CSS/HTML only if alternating Fight controls require it.
* **Dependencies:** verified core/team/NPO rules; PR 1 transaction IDs.
* **Risks:** highest gameplay and UI regression surface; pending saves.
* **Tests:** COM-01…07 deterministic vectors, navigation/reload/double-tap, 390 px Fight UI.
* **Version impact:** **major**.

### PR 6 — Mission and scoring corrections

* **Scope:** each mission’s setup state, actions, Strategy/TP effects, random choices, scoring, end/tie checks.
* **Files:** six mission JSON files, `app.js`, tests; maps only if verified discrepancies exist.
* **Dependencies:** current mission pack; PRs 1 and 3 event/reinforcement/Threat hooks.
* **Risks:** six distinct state machines and save migration.
* **Tests:** Appendix B plus MIS-01…05 and all mission-specific Given/When/Then cases.
* **Version impact:** **major**.

### PR 7 — Persistence and cache migration

* **Scope:** explicit save schema, migrations, validation, transactional attacks/effects, compatible rules-data revision pinning, coherent service-worker update.
* **Files:** `app.js`, `service-worker.js`, manifests/data, tests.
* **Dependencies:** stable schemas from PRs 1–6.
* **Risks:** user saves/offline upgrades.
* **Tests:** PER-01…03 across at least the immediately preceding supported version and offline asset-failure combinations.
* **Version impact:** **minor** if backward compatible; **major** if migration cannot preserve outcomes.

### PR 8 — Wording and usability corrections

* **Scope:** distinguish “officially resolved”, “tabletop confirmation”, “manual correction” and unsupported rule; refine legal-target prompts; source/revision display.
* **Files:** `app.js`, `index.html`, possibly `styles.css`, docs.
* **Dependencies:** final behaviours from PRs 1–7.
* **Risks:** user misunderstanding; mobile dialog height.
* **Tests:** terminology/source review and 390 px manual dialog/accessibility checks.
* **Version impact:** **patch** if wording-only.

## Appendix A: Complete event inventory

Because the official event page was unavailable and the local `.pdf` is invalid, “complete” here means a complete row for every event the implementation claims belongs to the official set, plus an explicit unknown-official-entry row. It must be reconciled against the current first-party table before remediation.

| Candidate official event | Present | Title match | Effect | Timing | Duration | Choice/randomization | Automated roster/wounds | Cleanup | Status | Evidence / official source |
|---|---|---|---|---|---|---|---|---|---|---|
| Awakened Warrior | Yes | Unverifiable | Add one Warrior is automated; placement vague; cap silently blocks | Generic Grade-3 Strategy | Immediate assumed | Uniform random event; no internal choice | Adds full-wound Ready/deployed Warrior | None | PARTIAL | `app.js:145`, `1029`; TW **Awakened Warrior**, page unavailable |
| A Chittering Drone | Yes | Unverifiable | User chooses add or fully heal; cap/wounded filtering exists | Generic Grade-3 Strategy | Immediate assumed | Choice implemented; event selection uniformly random | Add/heal automated after button | Resolution marker persisted | PARTIAL | `app.js:146`, `725–845`, `1038–1055`; TW **A Chittering Drone**, page unavailable |
| Living Metal Flux | Yes | Unverifiable | Each wounded active NPO receives an independently rolled D3+2 | Generic Grade-3 Strategy | Immediate | Per-NPO D3 occurs invisibly | Wounds automated and capped | None required if immediate | UNVERIFIABLE | `app.js:147`, `1028`; TW **Living Metal Flux**, page unavailable |
| The Maze Reforms | Yes | Unverifiable | Text only; no hatch/breach state or D3 workflow | Generic Grade-3 Strategy | Immediate/board-persistent unclear | Printed D3 described but not rolled | None | None | PARTIAL | `app.js:148`, `822`; TW **The Maze Reforms**, page unavailable |
| Stirrings of Horror | Yes | Unverifiable | Threat +1 automated and clamped | Generic Grade-3 Strategy | Immediate | None beyond uniform event roll | Threat automated | None required if immediate | UNVERIFIABLE | `app.js:149`, `1027`; TW **Stirrings of Horror**, page unavailable |
| Countertemporal Shifting | Yes | Unverifiable | Text only; high-damage resistance never affects combat | Generic Grade-3 Strategy | Description says current TP; not tracked | No choice metadata | None | No TP cleanup | NON-COMPLIANT | `app.js:150`, `1025–1029`, `1537–1558`; TW **Countertemporal Shifting**, page unavailable |
| Any other official event / duplicated result | Unknown | Unknown | Absent if official | Absent | Absent | No weight/deck metadata | None | None | UNVERIFIABLE | Exactly six JS entries at `app.js:144–151`; TW **complete event table/deck**, unavailable |

**Duplicate/unofficial assessment:** IDs/titles are unique in code. No entry can be certified official or unofficial without the authoritative table. Selection relies on explicit IDs for current objects, but legacy save migration falls back to exact title+description text matching (`app.js:201–206`), which is fragile if wording changes.

## Appendix B: Mission-by-mission matrix

| Mission | Setup/starting NPO | Objective/actions | TP/Strategy effects | Scoring/end | NPO/event/reinforcement interaction | Overall | Evidence / official source |
|---|---|---|---|---|---|---|---|
| 01 Shifting Labyrinth | 2D3+3 and deployment prose; map shown | Escape and marker rule are prose only | Auspex Calibration D3 movement never runs | Editable escaped count; universal clear-NPO win conflicts | Generic only | NON-COMPLIANT | `Missions/01-shifting-labyrinth.json`; `app.js:306–316`, `685–690`, `229–237`; TW Mission 1 **Shifting Labyrinth**, mission map pp. 17–19 association |
| 02 Demolition Protocol | 2D3+3 and deployment prose | Breach can be selected as generic action; persistent seven-feature breached/open state absent | No mission hook | Editable count cannot prove both printed predicates; universal clear-NPO win | Maze Reforms can conflict with board-only breach state | PARTIAL | `Missions/02-demolition-protocol.json`; `app.js:1179–1185`, `1426–1439`; TW Mission 2 **Demolition Protocol**, pp. 17–19 association |
| 03 Recover Transponder | 2D3+3 and room deployment prose | Marker D3 search, carrier and escape state absent | None represented | Editable “sites” count is not carrier escape; universal clear-NPO win | Generic only | NON-COMPLIANT | `Missions/03-recover-transponder.json`; no mission dispatch; TW Mission 3 **Recover Transponder**, pp. 17–19 association |
| 04 Destroy Sarcophagus | D3+6 generation implemented | Generic Breach does not roll/add 2D6 destruction | Nanoscarab Repair never runs | Editable destruction up to 20; no automatic victory; universal clear-NPO win | Generic only | NON-COMPLIANT | `Missions/04-destroy-sarcophagus.json`; `app.js:306–316`, `972–1000`; TW Mission 4 **Destroy Sarcophagus**, pp. 17–19 association |
| 05 Scout Sub-Crypt | Zero starting NPO implemented | Scout action/eligibility and room state absent | Dormant Threat exception absent | Editable rooms count; no automatic victory | Awaken Rooms special reinforcement absent | NON-COMPLIANT | `Missions/05-scout-sub-crypt.json`; `app.js:583–595`, `972–993`; TW Mission 5 **Scout Sub-Crypt**, pp. 17–19 association |
| 06 Regroup | 2D3+3 and deployment prose | Access Denied and random phasing are prose only | End-of-TP condition not evaluated | Editable regrouped count cannot test zone/control/3-inch predicates | Generic only | NON-COMPLIANT | `Missions/06-regroup.json`; `app.js:685–690`; TW Mission 6 **Regroup**, pp. 17–19 association |

## Appendix C: Code trace index

| Rules area | Files | Functions/data structures | Notes |
|---|---|---|---|
| Boot/data loading | `app.js`, manifests | `loadMissionPack`, `loadPlayerManifest`, `loadPlayerTeamData` | Fetches JSON network-first through SW; no rules-revision compatibility check. |
| Save/restore | `app.js` | `initialState`, `save`, `load`, `normalizeState`; import/export handlers | Single legacy storage key; shallow normalization; mission/effect schemas absent. |
| Setup/team selection | `app.js`, `Player_Operatives/*.json` | `playerRosterLimits`, `autoSelectRequiredPlayerOperatives`, `renderSetup`, `bindSetup` | Some structured selection rules are not enforced. |
| Mission setup/data | `Missions/*.json`, `app.js` | `mission`, `missionSetup`, `missionTracker`, `missionSpecial`, `generateRoster` | Mission rules mostly display-only. |
| Starting NPO generation | `app.js` | `profiles`, `generateRoster`, local `table` | 2D6 lookup; no setup cap/order state. |
| Threat/Grade | `app.js` | `threatGrade`, `threatLabel`, `setThreat`, action Threat UI | Shared HUD/engine derivation; incomplete/wrong triggers. |
| Turning Point/Strategy | `app.js` | `startTurningPoint`, `strategyCard`, `bindStrategyCard` | Mutates reinforcement/event before checklist; no mission hooks. |
| Events | `app.js` | `events`, `strategyEventHtml`, `applyStrategyEvent`, `resolveStrategyEventAction` | Six hard-coded objects; partial automation; no eligibility/duration. |
| Initiative | `app.js` | `rollInitiative`, `animateInitiativeResult`, `chooseInitiative`, Strategy bindings | D6 vs D6, Player tie, unlimited reroll/override. |
| Activation scheduling | `app.js` | `setNextActivation`, `advanceAfterActivation`, `playerOperativesRemaining`, `readyNpos`, `nextStepCard` | Alternates/finishes remainder; NPO commits prematurely. |
| Player activation | `app.js` | `showPlayerActivation`, stage/pending attack helpers, confirmation handlers | APL/action collection; mission rules and many abilities delegated. |
| NPO selection | `app.js` | `sortOperativesGlobally`, `nextNpo` | Behaviour rank/wounds/name ordering; official priority unverified. |
| NPO decisions | `app.js` | `npoQuestions`, `nextNpoQuestionKey`, `runNpoPrompt`, `chooseNpoDecision`, `resolveNpo` | Generic heuristic, not per-profile table. |
| Attack profiles/rules | `app.js`, player JSON | `profiles[].attack`, player `weapons`, `parseDamage`, `weaponRuleValue` | NPO single profile; special-rule support incomplete. |
| Shared combat | `app.js` | `rollAttack`, `resolveCombat`, `resolveDefense`, render/settle helpers | Incorrectly shares shooting saves with melee. |
| Player→NPO damage | `app.js` | `showPlayerAttackWizard`, pending Shoot/Melee stages, activation commit | Pending until full activation; NPO Defence hard-coded 3. |
| NPO→Player damage | `app.js` | `renderNpoDecisionResult`, `showNpoAttackWizard`, `applyNpoAttackDamage`, `completeNpoActivation` | Draft persisted, but activation already consumed. |
| Wounds/elimination | `app.js` | `activeNpos`, `livingPlayerOperativeCount`, `adjustWounds`, `applyNpoAttackDamage`, status toggles | Persistent wounds/casualties; manual restoration possible. |
| Mission scoring/end | `app.js`, mission JSON | `tracker`, `missionTrackerMax`, `checkGameEnd`, end card | Generic free-number tracker; universal NPO-clear win. |
| Reinforcements | `app.js` | `startTurningPoint`, `actualReinforcementCount`, `reinforcementEntry`, `MAX_NPOS` | Grade count; immediately deployed/ready; one entry string. |
| Cache/update | `service-worker.js`, `app.js` | `CACHE_NAME`, `PRECACHE_ASSETS`, `networkFirst`, `cacheFirst`, SW registration | Old named caches deleted; mixed-version window remains; invalid PDF cached. |
