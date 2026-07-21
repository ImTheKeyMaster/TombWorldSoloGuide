# Official Rules Compliance Remediation Plan

## Purpose

This document turns the independently reviewed compliance findings into a staged implementation plan. It plans corrections only for findings classified **Confirmed** or **Partially Confirmed** in `docs/OFFICIAL_RULES_COMPLIANCE_AUDIT_REVIEW.md`, using the official mission pack as rules authority. It makes no application change. Findings classified Incorrect are excluded; Unable to Verify items are isolated under Human Decisions Required and are not approved implementation work.

## Authoritative Sources

- `Assets/Tomb-World-Mission-Pack.pdf` (22-page *Joint Ops: Tomb World Mission Pack*) is the rules authority. Viewer PDF page numbers are used throughout because printed pagination is not consistently extractable.
- `docs/OFFICIAL_RULES_COMPLIANCE_AUDIT_REVIEW.md` is the authoritative finding/status list and corrected scope.
- Current behavior and likely change points were inspected in `app.js`, `index.html`, `styles.css`, `Missions/manifest.json`, `Missions/01-shifting-labyrinth.json` through `Missions/06-regroup.json`, and `Player_Operatives/*.json`.
- `docs/OFFICIAL_RULES_COMPLIANCE_AUDIT.md` supplies historical context only; it must not override the review or PDF.

## Implementation Principles

Future implementation PRs must:

1. Use the official PDF as the rules authority and cite the exact viewer page/rule in code-review notes and tests.
2. Make the smallest necessary change; avoid unrelated cleanup, formatting, architectural changes, frameworks, dependencies, and refactoring.
3. Preserve localStorage key `tombWorldSoloGuide.v1` and saved-game compatibility where practical. Add defaults/migrations in `normalizeState()` rather than clearing user data.
4. Avoid duplicate rule logic. One typed page-5 NPO roll table must serve setup and reinforcement; one Threat mutation path and one mission evaluator layer must serve all screens.
5. Centralize shared calculations when setup, Strategy, activation, combat, mission, and end-of-turn screens depend on the same value.
6. Keep mission-specific rules data-driven where practical, but do not force genuinely procedural mission behavior into an opaque generic abstraction.
7. Preserve mobile-first usability at approximately 390px: no horizontal overflow, clipped dialogs, hidden controls, or undersized touch targets; long rule workflows must scroll internally.
8. Preserve existing functionality not contradicted by the PDF, including six-mission inventory, Turning Point 1 start/initiative, Threat bounds/grades, default Hatch/Breach Threat triggers, Grade-sized reinforcement quantity, and the supported ten-NPO limit.
9. Clearly distinguish automation from tabletop confirmation. Manual geometry is acceptable; missing rules inputs or state required by later automation are not.
10. Add tests before removing fallbacks, and never convert an Unable to Verify item into code without the additional authority or human decision identified below.

## Dependency Analysis

- **Rules data is foundational.** Complete NPO datacards, weapon variants, event instances, and the single page-5 roll table must exist before behavior, combat, or reinforcement consumers can be reliable.
- **Strategy timing owns cross-system order.** Ready hooks, event lifecycle, reinforcements, dormancy, and initiative must expose staged transitions rather than mutate all results in `startTurningPoint()`.
- **Threat is transaction-sensitive.** Shoot/Fight changes belong at confirmed action completion, not recommendation; mission/event exceptions must call the same `setThreat()` path.
- **Activation selection and decision behavior are one dependency cluster.** `nextNpo()`, `priority()`, `npoQuestions`, `nextNpoQuestionKey()`, `chooseNpoDecision()`, and `resolveNpo()` must use the same printed priorities and delay expenditure until confirmation.
- **Mission state is the authority for mission completion.** Typed state/evaluators must replace `state.tracker` and universal elimination in `checkGameEnd()`, while `renderMission()` and end-turn UI become views of that state.
- **Persistence follows domain state.** Event lifecycle and mission state migrations belong in their owning PRs, not a later schema rewrite.
- **Placement remains partly physical.** Reinforcement/event/mission flows should store only the hatch, room, order, and confirmation needed by later rules; they should not attempt a geometry engine.
- **Overlapping IDs are not duplicate work.** HR-02 is delivered by official NPO behavior plus mission completion; ABS-01–04 are acceptance boundaries for those same engines; PER-01/02 are persistence requirements within mission/event work.

## Proposed Pull Request Sequence

### PR 1 — Mission setup, roster scope, and delegated resources

- **Purpose:** Establish accurate solo setup guidance and explicit automation boundaries without changing game-engine architecture.
- **Findings addressed:** SET-01, SET-02, SET-03, STR-05, plus the review's additional initial-resource issue.
- **Likely files changed:** `app.js`, `Missions/*.json`, and only if needed existing setup markup/styles in `index.html`/`styles.css`; supported-team JSON only after external team-rule verification.
- **Implementation order:** preserve six-mission/TP1 baselines; decide roster-legality scope; add or explicitly delegate four equipment options and 2CP; update setup confirmation.
- **Acceptance criteria:** six missions still load; TP1 begins with player initiative; UI cannot imply unverified full roster legality; 2CP/equipment responsibility is visible or stored; existing saves normalize safely.
- **Regression tests:** all six setup flows, every supported team, cancellation/reload, and 390px setup/dialog checks.
- **Dependencies on earlier PRs:** None. External team rules and product decision are required before enforcement beyond current verified data.

### PR 2 — Official NPO data and shared generation table

- **Purpose:** Create one accurate source for complete NPO identities, datacards, weapons, and 2D6 results.
- **Findings addressed:** SET-05, DAT-02, COM-02/04 data prerequisites, REI-01 data prerequisite, and starting Conceal/weapon attributes.
- **Likely files changed:** `app.js` (or a small existing-pattern static data file only if approved), with consumers kept vanilla and build-free.
- **Implementation order:** transcribe PDF pages 5–7; encode physical weapon variants; replace both generation arrays with one lookup; store starting Conceal and weapon selection; normalize old NPO saves.
- **Acceptance criteria:** totals 2–12 match all printed rows; setup and reinforcement use identical mappings; totals 5/6/12 and 4/10 are corrected; every created NPO retains type, selected weapon, order, and complete sourced profile.
- **Regression tests:** deterministic boundary/table tests, old-save normalization, all NPO render/combat paths, and mobile roster display.
- **Dependencies on earlier PRs:** PR 1 only for any setup-state shape decision.

### PR 3 — Strategy sequencing, dormancy, initiative, and import integrity

- **Purpose:** Turn Strategy into explicit rules-ordered stages and implement Threat-0 dormancy/initiative without yet adding the full event deck.
- **Findings addressed:** STR-02, STR-04, THR-01/02/06, ABS-04, and additional Dormant NPO state.
- **Likely files changed:** `app.js`; `Missions/04-destroy-sarcophagus.json` only if typed timing metadata is required.
- **Implementation order:** normalize Threat; add derived dormancy and zero/nonzero transitions; stage Ready and Mission 4 repair; preserve an event hook before reinforcement; derive first-turn/Threat-0 initiative; label manual override as correction.
- **Acceptance criteria:** Threat 0 NPOs remain expended and cannot ready; leaving Threat 0 readies them; player automatically has initiative at Threat 0 and TP1; repair occurs in Ready; later stages cannot mutate before confirmation.
- **Regression tests:** Threat transitions 0↔1, TP1 and later initiative, malformed imports, cancel/reload at every Strategy stage, and existing Grade boundaries.
- **Dependencies on earlier PRs:** PR 2 for normalized NPO state.

### PR 4 — Activation selection and official NPO decision behavior

- **Purpose:** Replace invented generic heuristics with printed operative behavior and Threat Principle, while retaining manual tabletop geometry.
- **Findings addressed:** ACT-01/03/05, NPO-01/02/03/04, ABS-01, and the behavior half of HR-02.
- **Likely files changed:** `app.js`; `styles.css` only for mobile-safe question flow if unavoidable.
- **Implementation order:** typed behavior lists; selection priority; exact ordered questions/fallbacks; target/tie resolver; confirmation-before-expenditure; retain alternation baseline.
- **Acceptance criteria:** each NPO follows its own printed list; required legality predicates are asked in rule order; ties use Threat Principle; backing out does not expend or increment activation; manual geometry remains clear.
- **Regression tests:** branch table per NPO/action/fallback, target ties, no-legal-action, cancel/reopen, alternating exhaustion, save/reload mid-question, and 390px dialogs.
- **Dependencies on earlier PRs:** PR 2 data and PR 3 dormancy/readiness.

### PR 5 — NPO weapons, combat effects, and transactional Threat

- **Purpose:** Apply the mission-pack-defined NPO weapon distinctions/rules and commit Threat at the actual action boundary.
- **Findings addressed:** COM-02, COM-04, THR-03/05, ABS-03; THR-04's mission switch is completed in PR 7.
- **Likely files changed:** `app.js`; styles only if existing combat dialogs cannot fit complete profiles.
- **Implementation order:** consume PR 2 profiles; expose ranged/melee choice; implement pack-defined weapon rules; move Shoot/Fight Threat commits; add Silent and printed Fight exceptions; retain existing Hatch/Breach behavior.
- **Acceptance criteria:** correct weapon/profile reaches resolution; each pack-defined rule changes the stated calculation; canceled attacks do not change Threat; completed qualifying actions change it exactly once; default Hatch/Breach is unchanged.
- **Regression tests:** each weapon/rule, ranged vs melee, cancel/retry, Silent Shoot, both Fight outcomes, NPO vs player triggers, and mobile combat dialogs.
- **Dependencies on earlier PRs:** PRs 2–4. Core Fight, cover, save-cancellation, and player-datacard claims remain excluded.

### PR 6 — Tomb World event deck and lifecycle

- **Purpose:** Implement the physical deck, correct draw count/timing, exact effect branches, placement, persistence, expiry, and redraws.
- **Findings addressed:** STR-03, EVT-01/02/03/04/06, REI-05, PER-02, and the omitted-card/duplicate-weighting issue.
- **Likely files changed:** `app.js`; `styles.css` only for existing event-card/dialog patterns.
- **Implementation order:** encode each physical instance; deck/used/active state; eligibility/count; draw without replacement; exact effects and placement confirmation; impossible-effect redraw; end-TP expiry/next-Ready recycling.
- **Acceptance criteria:** no TP1 draw; Grade-3 TP2+ draw; exactly one extra card when either qualifying condition applies; duplicates have printed weight; effects resolve in draw order before reinforcement; duration and reload behavior are correct.
- **Regression tests:** deterministic deck exhaustion/duplicate weighting, both second-draw conditions together/separately, Threat 15 branches, cap/impossible redraws, every card effect, end/Ready lifecycle, old saves, and 390px scrolling.
- **Dependencies on earlier PRs:** PR 2 data, PR 3 staged Strategy, PR 4 behavior state, and PR 5 combat hooks.

### PR 7 — Mission-specific state, actions, objectives, and completion

- **Purpose:** Make all six missions playable from typed state and remove universal NPO-elimination victory.
- **Findings addressed:** MIS-01/02/03, PER-01, ABS-02, THR-04 and Scout Room portion of THR-05, REI-02, mission half of HR-02.
- **Likely files changed:** `app.js`, all six `Missions/*.json`, and `styles.css` only for existing mission/action controls.
- **Implementation order:** define compatible `missionState`; implement missions one-by-one (escape; seven feature identities/open state; transponder sites/carrier/escape; Destruction/repair; room awakening/scouting/Threat; phasing/regroup end check); replace `checkGameEnd()` authority; migrate tracker display.
- **Acceptance criteria:** all six printed victory/defeat predicates work at exact timing; zero NPOs never grants victory by itself; mission state survives reload; Mission 5 suppresses Hatch Threat and performs Scout reduction; room awakening occurs only on first eligible opening/entry.
- **Regression tests:** positive/negative/boundary scenario per mission, all-incapacitated loss, empty-NPO Mission 5, repeated room/hatch actions, repair floor, end-TP timing, reload and 390px mission controls.
- **Dependencies on earlier PRs:** PRs 1–6, especially staged Ready, shared generation, event/Threat hooks.

### PR 8 — Standard reinforcements and battlefield placement

- **Purpose:** Complete standard reinforcement timing, mapping, order, placement, and ten-NPO behavior after events.
- **Findings addressed:** REI-01/03/04; ACT-04 is retained as a verified boundary, not an unsupported readiness change.
- **Likely files changed:** `app.js`; existing mission data only if hatch identifiers are needed.
- **Implementation order:** call shared table after events; create pending reinforcement records; randomly select/confirm legal hatch/placement; store Conceal; mark deployed only after confirmation; preserve Grade count and cap.
- **Acceptance criteria:** exactly Grade arrive after TP1 subject to cap; page-5 rows/weapons match; event-modified Grade is used; every placed model has Conceal and confirmed placement; readiness is not changed without authority.
- **Regression tests:** Grades 0–3, table totals, cap at 9/10, cancel/reload pending placement, all hatch choices, event-before-reinforcement integration.
- **Dependencies on earlier PRs:** PRs 2, 3, and 6; human clarification for standard readiness if implementation would alter it.

### PR 9 — Terminology, briefing text, regression suite, and final verification

- **Purpose:** Reconcile concise guidance with automated behavior and perform a final audit without new rules invention.
- **Findings addressed:** MIS-04 and final verification of all Confirmed/Partially Confirmed informational baselines.
- **Likely files changed:** `app.js`, `Missions/*.json`, existing tests if present, and styles only for verified mobile defects.
- **Implementation order:** compare all summaries to pages 9–14; label delegated rules; remove misleading invented wording where consumers remain; run full matrices; re-audit PDF pages 1–22.
- **Acceptance criteria:** summaries do not omit decision-changing conditions; delegated steps point users to the official mission page; no Incorrect/Unable-to-Verify claim has slipped into behavior; no regressions in compliant baselines.
- **Regression tests:** full setup-to-completion run for six missions, all cards/NPOs/table totals, old-save fixtures, offline static load, console/syntax checks, and 390px plus desktop smoke tests.
- **Dependencies on earlier PRs:** All earlier PRs.

## Finding Implementation Matrix

### SET-01 — Six missions and killzone layouts

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 1, “Missions”; PDF page 8, “Game Sequence — Set Up the Battle”; PDF pages 9–14, Missions 1–6; PDF pages 17–19, “Mission Maps.”

**Current application behavior:**
The pack directly says there are six missions and six maps and permits selecting or randomizing each. The manifest has six missions and the setup UI requires map confirmation. This confirms only inventory/workflow, not geometric accuracy. Verified locations: `Missions/manifest.json`; `loadMissionPack()` and setup checklist rendering in `app.js`.

**Required behavior:**
The finding is correct; no compliance defect is established (Informational). Required correction: None for this finding; map accuracy remains separately reviewable.

**Likely implementation locations:**
`Missions/manifest.json`; `loadMissionPack()` and setup checklist rendering in `app.js`. The owning shared flow is identified in PR 1; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: None for this finding; map accuracy remains separately reviewable.

**Dependencies:**
None for baseline setup; SET-05 shares PR 2 generation data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for SET-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 1.

### SET-02 — Beginning at Turning Point 1

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 8, “Play the Battle,” which directly gives the players initiative in the first turning point; PDF page 2, event timing “after the first.”

**Current application behavior:**
The pack assumes the standard turning-point sequence and explicitly defines first-turn initiative. The app enters Turning Point 1 consistently. Verified locations: Setup stores `turningPoint: 0`; `startTurningPoint()` increments it; `rollInitiative()` assigns the player in Turning Point 1.

**Required behavior:**
Confirmed; no defect (Informational).

**Likely implementation locations:**
Setup stores `turningPoint: 0`; `startTurningPoint()` increments it; `rollInitiative()` assigns the player in Turning Point 1. The owning shared flow is identified in PR 1; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: None.

**Dependencies:**
None for baseline setup; SET-05 shares PR 2 generation data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for SET-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 1.

### SET-03 — Player kill-team selection

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 1, “Kill Team Selection”; PDF page 8, “Select Operatives.” The direct rule is: solo selects a kill team normally; co-op may split one team or take half of separate teams. Team legality is delegated to each kill team's own rules.

**Current application behavior:**
The application is a solo guide, so the original emphasis on an unimplemented co-op adjustment overstates the relevant scope. The PDF does confirm normal legal selection, but it does not contain Death Korps, Deathwatch, or Kasrkin selection requirements, so it cannot prove every claimed enforcement gap. Verified locations: `playerRosterLimits`, `autoSelectRequiredPlayerOperatives()`, setup selection handlers in `app.js`, and `Player_Operatives/*.json` selection data.

**Required behavior:**
Normal team legality remains only partially automated; co-op half-team selection is outside the app's stated solo scope. Medium severity for any supported illegal solo roster, otherwise Informational. Required correction: Audit each supported team's external official selection rules separately and clearly scope co-op as unsupported.

**Likely implementation locations:**
`playerRosterLimits`, `autoSelectRequiredPlayerOperatives()`, setup selection handlers in `app.js`, and `Player_Operatives/*.json` selection data. The owning shared flow is identified in PR 1; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Audit each supported team's external official selection rules separately and clearly scope co-op as unsupported.

**Dependencies:**
None for baseline setup; SET-05 shares PR 2 generation data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for SET-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 1.

### SET-05 — Starting NPO generation table

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 5, “NPO Datacards,” 2D6 NPO table and “use the next row” substitution rule; PDF page 8, “Set Up Operatives.”

**Current application behavior:**
The conclusion that verification was impossible is obsolete: the official table is present. It assigns 2–3 to a Canoptek Scarab Swarm, 4–6 to a Canoptek Macrocyte with one ranged weapon, 7–9 to a Necron Warrior with one ranged weapon, 10–11 to a Canoptek Tomb Crawler with twin gauss reapers, and 12 to a Canoptek Tomb Crawler with a transdimensional isolator. `generateRoster()` instead returns a Warrior on totals 5, 6, and 12, so those are base-table NPO type errors; total 12 is not a fallback. The code also collapses the printed weapon variants. The PDF's separate “use the next row” instruction applies only when the required miniature is unavailable and does not excuse any of these base mappings. Verified locations: `generateRoster()` in `app.js`, especially its 11-element `table`.

**Required behavior:**
The starting table is materially non-compliant: totals 5 and 6 generate a Warrior instead of a Macrocyte, total 12 generates a Warrior instead of a Tomb Crawler, and all weapon-option identity is lost. This is a High compliance issue that changes generated rosters. Required correction: Correct the base 2D6 mapping to the five printed rows, retain each printed weapon option, and treat the unavailable-miniature “next row” substitution as a separate tabletop contingency.

**Likely implementation locations:**
`generateRoster()` in `app.js`, especially its 11-element `table`. The owning shared flow is identified in PR 2; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Correct the base 2D6 mapping to the five printed rows, retain each printed weapon option, and treat the unavailable-miniature “next row” substitution as a separate tabletop contingency.

**Dependencies:**
None for baseline setup; SET-05 shares PR 2 generation data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for SET-05's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 2.

### STR-02 — Ordered Strategy phase and mission hooks

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2, “Tomb World Event Cards”; PDF page 3, “NPO Reinforcements”; PDF page 12, Mission 4 “Nanoscarab Repair.”

**Current application behavior:**
The pack directly sequences event-card gambits before reinforcement gambits and places repair in the Ready step. The app immediately generates reinforcements, applies an event afterward, and has no repair dispatch. Verified locations: `startTurningPoint()` in `app.js`; Mission 4 JSON `Nanoscarab Repair` prose.

**Required behavior:**
Confirmed High issue; the exact code order is the reverse of the printed event/reinforcement order, in addition to missing mission timing. Required correction: Stage Ready, event gambit(s), reinforcements, and initiative-facing UI in printed order, with Mission 4 repair at Ready.

**Likely implementation locations:**
`startTurningPoint()` in `app.js`; Mission 4 JSON `Nanoscarab Repair` prose. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Stage Ready, event gambit(s), reinforcements, and initiative-facing UI in printed order, with Mission 4 repair at Ready.

**Dependencies:**
PR 2 typed data where events/NPOs are involved; preserve the staged Strategy flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for STR-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### STR-03 — Event duration and cleanup

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2, “Tomb World Event Cards” (ongoing cards last until end of turning point and used cards return in the next Ready step); PDF pages 20–22, including Countertemporal Shifting and Reanimation Protocols.

**Current application behavior:**
This is direct pack text. The app stores only the drawn event in transient strategy summary and has no active-effect/expiry/discard model. Verified locations: `events`, `initialState()`, `applyStrategyEvent()`, and `startTurningPoint()` in `app.js`.

**Required behavior:**
Confirmed High issue. Required correction: Persist active and used cards, apply printed duration, expire at end of turning point, and recycle used cards in the next Ready step.

**Likely implementation locations:**
`events`, `initialState()`, `applyStrategyEvent()`, and `startTurningPoint()` in `app.js`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Persist active and used cards, apply printed duration, expire at end of turning point, and recycle used cards in the next Ready step.

**Dependencies:**
PR 2 typed data where events/NPOs are involved; preserve the staged Strategy flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for STR-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### STR-04 — Initiative roll and overrides

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 2, “Strategy Phase” (NPOs choose initiative when they win); PDF page 3, “Dormant NPOs” (players automatically have initiative at Threat 0); PDF page 8 (players have first-turn initiative). The PDF does not state the core tie procedure.

**Current application behavior:**
The PDF confirms two special cases the app only partly handles: first turn is correct, but Threat 0 automatic player initiative is missing after Turn 1. It does not establish tie or reroll rules, so those parts cannot be certified from this source. Verified locations: `rollInitiative()`, initiative summary UI, reroll and override handlers in `app.js`.

**Required behavior:**
Confirmed Medium Tomb World defect for Threat 0; tie/reroll claims remain Unable to Verify from this PDF. Required correction: Force player initiative while Threat is 0; separately verify tie/reroll behavior against the Core Book.

**Likely implementation locations:**
`rollInitiative()`, initiative summary UI, reroll and override handlers in `app.js`. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Force player initiative while Threat is 0; separately verify tie/reroll behavior against the Core Book.

**Dependencies:**
PR 2 typed data where events/NPOs are involved; preserve the staged Strategy flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for STR-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### STR-05 — CP, equipment, ploys, and abilities

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 8, “Select Operatives”: players select up to four equipment options and gain 2CP total; PDF page 2: NPOs gain no CP but use required Strategic Gambits.

**Current application behavior:**
The pack directly confirms the initial 2CP and four-equipment rules, which the app does not track. It does not require a guide to automate all player ploys, so lack of state is a compliance issue only where the app claims to resolve affected outcomes. Verified locations: Strategy checklist and absence of CP/equipment state in `initialState()` in `app.js`.

**Required behavior:**
Partially confirmed; Low if clearly tabletop-delegated, Medium where automated calculations ignore selected effects. Required correction: State the delegation clearly or track CP/equipment choices that affect automated results.

**Likely implementation locations:**
Strategy checklist and absence of CP/equipment state in `initialState()` in `app.js`. The owning shared flow is identified in PR 1; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: State the delegation clearly or track CP/equipment choices that affect automated results.

**Dependencies:**
PR 2 typed data where events/NPOs are involved; preserve the staged Strategy flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for STR-05's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 1.

### EVT-01 — Event eligibility, timing, and count

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2, “Tomb World Event Cards.” Directly: only after the first turning point at Grade 3; draw twice if NPOs lack initiative or Threat is 15.

**Current application behavior:**
The original issue is real. It should have stated the exact rule: the app can draw on Turning Point 1, never draws twice, and draws before initiative is chosen while failing to use the relevant initiative state. Verified locations: `events` and `startTurningPoint()` (`if (grade===3)` one selection) in `app.js`.

**Required behavior:**
Confirmed High issue with broader exact scope than originally stated. Required correction: Gate to Turning Point 2+, implement the two independent second-draw conditions as a single additional draw, and sequence against initiative as the pack requires.

**Likely implementation locations:**
`events` and `startTurningPoint()` (`if (grade===3)` one selection) in `app.js`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Gate to Turning Point 2+, implement the two independent second-draw conditions as a single additional draw, and sequence against initiative as the pack requires.

**Dependencies:**
PR 3 Strategy sequencing and PR 2 typed NPO/card data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for EVT-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### EVT-02 — Completeness of event effects

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 20–22, all event cards, especially The Maze Reforms, Countertemporal Shifting, A Chittering Drone, and Living Metal Flux.

**Current application behavior:**
The represented effects are indeed incomplete, but the audit understated scope: the official sheets include additional cards absent from code, such as Subjugation Glyphs, Transdimensional Relocation, My Will Be Done, Reanimation Protocols, and Dark of the Tomb. Some app summaries also omit redraw conditions and exact placement. Verified locations: `events`, `applyStrategyEvent()`, `resolveStrategyNpoEvent()` in `app.js`.

**Required behavior:**
Partially confirmed; High severity because multiple event outcomes materially change combat, APL, positioning, and activation. Required correction: Inventory every printed card and implement or explicitly delegate every operative consequence and redraw condition.

**Likely implementation locations:**
`events`, `applyStrategyEvent()`, `resolveStrategyNpoEvent()` in `app.js`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Inventory every printed card and implement or explicitly delegate every operative consequence and redraw condition.

**Dependencies:**
PR 3 Strategy sequencing and PR 2 typed NPO/card data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for EVT-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### EVT-03 — Complete deck and weighting

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 20–22, physical event-card sheets; PDF page 2, shuffle/draw/reuse procedure. “Awakened Warrior” is printed more than once, establishing duplicate weighting.

**Current application behavior:**
The official source establishes a larger physical deck with additional titles and duplicate weighting. The app is not a complete representation. Verified locations: Six unique entries in `events`; random array sampling in `startTurningPoint()`; no deck/discard state.

**Required behavior:**
Confirmed High issue; no longer merely “missing pending verification.” Required correction: Represent every physical card instance (including duplicates) and deck/discard state.

**Likely implementation locations:**
Six unique entries in `events`; random array sampling in `startTurningPoint()`; no deck/discard state. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Represent every physical card instance (including duplicates) and deck/discard state.

**Dependencies:**
PR 3 Strategy sequencing and PR 2 typed NPO/card data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for EVT-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### EVT-04 — Event placement, readiness, and blocked outcomes

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 21–22, A Chittering Drone and Awakened Warrior. Both directly specify ready/Conceal placement; Awakened Warrior and other cards require drawing another card when impossible.

**Current application behavior:**
Ready state is correct for those two cards, but `deployed:true` without the printed spatial constraints is insufficient, and Awakened Warrior silently does nothing at the limit rather than redrawing. Chittering Drone's printed branch depends on whether a swarm exists and is wounded, not a free user choice between add and heal. Verified locations: `createNpo()`, `applyStrategyEvent()`, and `resolveStrategyNpoEvent()` in `app.js`.

**Required behavior:**
Confirmed High issue, but the original suspicion about readiness itself was wrong; placement, branching, and redraw are the defects. Required correction: Use source-specific mandatory branching, collect printed placement confirmation, and redraw when instructed.

**Likely implementation locations:**
`createNpo()`, `applyStrategyEvent()`, and `resolveStrategyNpoEvent()` in `app.js`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Use source-specific mandatory branching, collect printed placement confirmation, and redraw when instructed.

**Dependencies:**
PR 3 Strategy sequencing and PR 2 typed NPO/card data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for EVT-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### EVT-06 — Reuse and reshuffle

**Audit status:**
Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 2, “Tomb World Event Cards”: used cards return to the deck in the Ready step of the following Strategy phase.

**Current application behavior:**
The pack directly forbids immediate replacement within the turning point. This matters when two cards are drawn. Verified locations: `events[roll(events.length)-1]`; no deck, used-card, or discard state in `initialState()`.

**Required behavior:**
Confirmed Medium defect; original “unverifiable/low” assessment was too weak. Required correction: Draw without replacement during a turning point and reshuffle used cards at the next Ready step.

**Likely implementation locations:**
`events[roll(events.length)-1]`; no deck, used-card, or discard state in `initialState()`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Draw without replacement during a turning point and reshuffle used cards at the next Ready step.

**Dependencies:**
PR 3 Strategy sequencing and PR 2 typed NPO/card data.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for EVT-06's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### THR-01 — Threat starts at 0 and is bounded 0–15

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 2, “Threat Level.”

**Current application behavior:**
The PDF states this directly and the code initializes/clamps accordingly. Verified locations: `initialState()` and `setThreat()` in `app.js`.

**Required behavior:**
Confirmed; no defect. Required correction: None, aside from import validation covered by THR-06.

**Likely implementation locations:**
`initialState()` and `setThreat()` in `app.js`. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: None, aside from import validation covered by THR-06.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### THR-02 — Grade thresholds

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 2, Threat Level/Grade table.

**Current application behavior:**
The table and function agree. Verified locations: `threatGrade()` in `app.js`.

**Required behavior:**
Confirmed; no defect.

**Likely implementation locations:**
`threatGrade()` in `app.js`. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: None.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### THR-03 — Timing and causes of Threat increases

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2, “Threat Level”: increase when an NPO performs Shoot/Fight and under enumerated player-action conditions.

**Current application behavior:**
The direct wording uses performance of the action, not selection of a recommendation. Exiting the later combat flow leaves the premature increase. Verified locations: `chooseNpoDecision()` and `resolveNpo()` call `setThreat()` before attack target/combat completion.

**Required behavior:**
Confirmed High defect. Required correction: Commit Threat only when the relevant action is actually performed; implement all printed player-action exceptions.

**Likely implementation locations:**
`chooseNpoDecision()` and `resolveNpo()` call `setThreat()` before attack target/combat completion. The owning shared flow is identified in PR 5; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Commit Threat only when the relevant action is actually performed; implement all printed player-action exceptions.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 5.

### THR-04 — Scout Sub-Crypt Dormant exception

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 13, Mission 5 “Dormant”; PDF page 2, default Operate Hatch Threat roll.

**Current application behavior:**
The mission exception is direct and the generic app path does not branch on mission. Verified locations: Mission 5 JSON and player activation Threat handling in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Suppress the default Operate Hatch Threat roll in Mission 5.

**Likely implementation locations:**
Mission 5 JSON and player activation Threat handling in `app.js`. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Suppress the default Operate Hatch Threat roll in Mission 5.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### THR-05 — Complete increases/decreases and Scout Room

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2, complete default Threat triggers; PDF page 13, Mission 5 “Scout Room.”

**Current application behavior:**
The original finding overstates the gap. The app already implements the default 4+ Operate Hatch roll and both Breach increases. It does not implement the Silent exception for Shoot, the conditional exception when a player Fight incapacitates its NPO without the player operative remaining visible to another enemy, or Scout Room's reduction to the highest Threat level of the grade below. THR-04 separately covers suppressing the otherwise-correct Hatch roll in Mission 5. Verified locations: `completePlayerActivation()` in `app.js` rolls the default 4+ Operate Hatch increase and applies both the automatic and 4+ Breach increases. The same function increments Threat for every recorded Shoot and Fight without checking the printed exceptions. Mission 5's Scout Room rule remains prose in `Missions/05-scout-sub-crypt.json`.

**Required behavior:**
Partially confirmed High issue: the default Hatch and Breach triggers are implemented, while the Shoot/Fight exceptions and Scout Room reduction remain missing. Required correction: Preserve the existing Hatch and Breach logic; add the Silent and conditional Fight exceptions plus the Mission 5 Scout Room reduction. Keep manual adjustment only as a labeled correction.

**Likely implementation locations:**
`completePlayerActivation()` in `app.js` rolls the default 4+ Operate Hatch increase and applies both the automatic and 4+ Breach increases. The same function increments Threat for every recorded Shoot and Fight without checking the printed exceptions. Mission 5's Scout Room rule remains prose in `Missions/05-scout-sub-crypt.json`. The owning shared flow is identified in PR 5; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Preserve the existing Hatch and Breach logic; add the Silent and conditional Fight exceptions plus the Mission 5 Scout Room reduction. Keep manual adjustment only as a labeled correction.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-05's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 5.

### THR-06 — Threat import normalization

**Audit status:**
Partially Confirmed

**Severity:**
Low

**Official rule reference:**
PDF page 2, valid Threat range and Grade table. The PDF says nothing about imports or persistence.

**Current application behavior:**
The official range makes nonnumeric/out-of-range state invalid, and current normalization is weak. The import mechanism is implementation-specific, not a printed rules requirement. Verified locations: `normalizeState()`, import handlers, `threatGrade()`, and HUD calculation in `app.js`.

**Required behavior:**
Confirmed Low integrity issue with potential Medium rules impact after malformed import. Required correction: Coerce and clamp imported/restored Threat before deriving Grade.

**Likely implementation locations:**
`normalizeState()`, import handlers, `threatGrade()`, and HUD calculation in `app.js`. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Coerce and clamp imported/restored Threat before deriving Grade.

**Dependencies:**
Shared `setThreat()` trigger semantics; mission exceptions depend on PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for THR-06's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### ACT-01 — Alternating activations

**Audit status:**
Partially Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 8, Game Sequence, plus PDF page 3, Dormant NPOs. Detailed alternating activation rules are delegated to the Core Book.

**Current application behavior:**
The scheduling shape is plausible, but the mission pack does not restate the full alternation rule. Moreover, dormant NPOs should not enter the queue at Threat 0. Verified locations: `setNextActivation()` and `advanceAfterActivation()` in `app.js`.

**Required behavior:**
Scheduler compliance is Unable to Verify from this PDF in general; its inclusion of readied Threat-0 NPOs is a confirmed High Tomb World defect already captured by STR-01. Required correction: Apply dormant eligibility, then verify generic alternation against the Core Book.

**Likely implementation locations:**
`setNextActivation()` and `advanceAfterActivation()` in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: Apply dormant eligibility, then verify generic alternation against the Core Book.

**Dependencies:**
PR 2 official NPO data; activation commitment and selection must be corrected together.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ACT-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### ACT-03 — Premature NPO activation commitment

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 3, “Behaviour” (perform the first action it can); PDF pages 6–7, ordered operative behaviors; PDF page 2, Threat increases when Shoot/Fight is performed.

**Current application behavior:**
The mission pack ties activation to actually performing the ordered actions. The application can exit after commitment but before the mandatory attack. Verified locations: `resolveNpo()` clears readiness, advances scheduling, and changes Threat before `showNpoAttackWizard()` completes.

**Required behavior:**
Confirmed High defect. Required correction: Stage the activation and atomically commit readiness, Threat, combat, and history after mandatory actions resolve.

**Likely implementation locations:**
`resolveNpo()` clears readiness, advances scheduling, and changes Threat before `showNpoAttackWizard()` completes. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Stage the activation and atomically commit readiness, Threat, combat, and history after mandatory actions resolve.

**Dependencies:**
PR 2 official NPO data; activation commitment and selection must be corrected together.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ACT-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### ACT-04 — Arrival readiness

**Audit status:**
Partially Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 3 standard Joint Ops reinforcements specify Conceal placement but do not explicitly say “ready”; PDF pages 21–22 explicitly say ready for Chittering Drone and Awakened Warrior.

**Current application behavior:**
Event readiness is supported for the named spawn cards. Standard reinforcement readiness is not explicit enough in this PDF to certify the app's assumption; dormant Threat 0 is not relevant because standard reinforcements require Grade above 0. Verified locations: `startTurningPoint()`, `createNpo()`, and manual restoration in `app.js`.

**Required behavior:**
Event portion is correct; standard arrival readiness is Unable to Verify. The original broad concern is overstated (Informational pending clarification). Required correction: Preserve explicit event readiness and seek an official clarification/Core interaction for standard reinforcement readiness.

**Likely implementation locations:**
`startTurningPoint()`, `createNpo()`, and manual restoration in `app.js`. The owning shared flow is identified in PR 8; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: Preserve explicit event readiness and seek an official clarification/Core interaction for standard reinforcement readiness.

**Dependencies:**
PR 2 official NPO data; activation commitment and selection must be corrected together.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ACT-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 8.

### ACT-05 — NPO activation selection priority

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 4, “Threat Principle — Activation Priority”: first ability/threat to Shoot or Fight, then not in cover, then proximity; unresolved decisions are random.

**Current application behavior:**
The official priority is now available and conflicts with the app's fixed Marksman/Brawler/Sentinel/Guardian ranking, which are not the pack's behavior names. Verified locations: `nextNpo()`/`priority()` in `app.js` use behavior rank plus low-wound penalty.

**Required behavior:**
Confirmed High defect. Required correction: Prompt/resolve the printed ordered criteria and randomize only unresolved ties.

**Likely implementation locations:**
`nextNpo()`/`priority()` in `app.js` use behavior rank plus low-wound penalty. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Prompt/resolve the printed ordered criteria and randomize only unresolved ties.

**Dependencies:**
PR 2 official NPO data; activation commitment and selection must be corrected together.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ACT-05's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### NPO-01 — Operative-specific behavior tables

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 3, “Behaviour”; PDF pages 6–7, ordered behavior lists for Scarab Swarm, Necron Warrior, Tomb Crawler, and Macrocyte.

**Current application behavior:**
The PDF directly provides different ordered action lists. The app's labels and shared heuristic do not implement them. Verified locations: `profiles`, `npoQuestions`, `chooseNpoDecision()` in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Data-drive each printed behavior and its order/order-selection conditions.

**Likely implementation locations:**
`profiles`, `npoQuestions`, `chooseNpoDecision()` in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Data-drive each printed behavior and its order/order-selection conditions.

**Dependencies:**
PR 2 complete datacards and shared behavior data; ACT-03/05 share the same flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for NPO-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### NPO-02 — Printed action priority and fallbacks

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 3, first legal action in behavior; PDF pages 6–7, exact ordered lists.

**Current application behavior:**
For example, a Warrior's list begins Fall Back, Shoot, Reposition, Dash, Fight, while a Scarab begins Fight then Charge. The app universally prioritizes engaged Fight and often Charge, contradicting those lists. Verified locations: `nextNpoQuestionKey()` and `chooseNpoDecision()` in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Evaluate each profile's printed list top-to-bottom and stop at the first legal action.

**Likely implementation locations:**
`nextNpoQuestionKey()` and `chooseNpoDecision()` in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Evaluate each profile's printed list top-to-bottom and stop at the first legal action.

**Dependencies:**
PR 2 complete datacards and shared behavior data; ACT-03/05 share the same flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for NPO-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### NPO-03 — Action legality inputs

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 3–7 repeatedly condition behavior on legal actions, valid targets, obscuring, cover, control range, and movement. Definitions are delegated to the Core Book.

**Current application behavior:**
The pack supports the need to establish these predicates, and the current prompts omit several printed distinctions (e.g., Warrior Fall Back and valid target not obscured). Exact generic legality cannot be fully audited without the Core Book. Verified locations: `npoQuestions` and wizard branching in `app.js`.

**Required behavior:**
Confirmed High gap for predicates expressly used by the pack; remaining core-legality scope is Unable to Verify. Required correction: Ask every predicate required by the selected printed behavior and require tabletop confirmation for Core Book legality.

**Likely implementation locations:**
`npoQuestions` and wizard branching in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Ask every predicate required by the selected printed behavior and require tabletop confirmation for Core Book legality.

**Dependencies:**
PR 2 complete datacards and shared behavior data; ACT-03/05 share the same flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for NPO-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### NPO-04 — Target priority and ties

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 4, Threat Principle, Fight target priority, Shoot target priority, and random final tie.

**Current application behavior:**
The official lists prioritize likelihood to incapacitate, mission impact, obscuring, cover, distance, and readiness in action-specific orders. “Largest cluster” is not the generic printed tie-break. Verified locations: `chooseNpoDecision()` and target-selection UI in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Collect candidates and apply the action-specific ordered list, then randomize unresolved choices.

**Likely implementation locations:**
`chooseNpoDecision()` and target-selection UI in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Collect candidates and apply the action-specific ordered list, then randomize unresolved choices.

**Dependencies:**
PR 2 complete datacards and shared behavior data; ACT-03/05 share the same flow.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for NPO-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### COM-02 — Weapon special rules

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 6–7, NPO weapons/abilities explicitly include Piercing 1, Punishing, Torrent 1, Brutal, Blast 2, and profile-selection conditions. Rule definitions are external.

**Current application behavior:**
For Tomb World NPOs, the app stores none of the printed special rules and only one generic attack per type, so omission is directly confirmed. The broader list of player weapon rules and their mechanics is not verifiable from this PDF. Verified locations: `profiles`, `playerWeaponProfile()`, `weaponPiercingValue()`, `rollAttack()` in `app.js`.

**Required behavior:**
Confirmed High for printed NPO rules/profiles; external player-team scope remains Unable to Verify. Required correction: Implement or clearly delegate every NPO weapon rule printed on pages 6–7; audit player weapons against their own official documents.

**Likely implementation locations:**
`profiles`, `playerWeaponProfile()`, `weaponPiercingValue()`, `rollAttack()` in `app.js`. The owning shared flow is identified in PR 5; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Implement or clearly delegate every NPO weapon rule printed on pages 6–7; audit player weapons against their own official documents.

**Dependencies:**
PR 2 weapon profiles; preserve Core Book mechanics excluded as Unable to Verify.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for COM-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 5.

### COM-04 — Distinct NPO ranged/melee weapon profiles

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 6–7, NPO Datacards: Warriors, Macrocytes, and Tomb Crawlers have distinct named ranged and melee profiles; some have multiple ranged profiles/options.

**Current application behavior:**
The official datacards directly contradict a single profile used for both actions. Verified locations: `profiles[type].attack` and NPO attack wizard in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Store exact weapon option/profile and select the correct ranged or melee weapon for the action.

**Likely implementation locations:**
`profiles[type].attack` and NPO attack wizard in `app.js`. The owning shared flow is identified in PR 5; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Store exact weapon option/profile and select the correct ranged or melee weapon for the action.

**Dependencies:**
PR 2 weapon profiles; preserve Core Book mechanics excluded as Unable to Verify.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for COM-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 5.

### REI-01 — Reinforcement timing, quantity, and table

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 3, “NPO Reinforcements”; PDF page 5, shared NPO 2D6 table.

**Current application behavior:**
The pack directly confirms exactly Grade reinforcements after the first turning point, after events, and directs use of the same page-5 NPO table. Quantity is correct, but code order is wrong. Against the printed rows, `randomReinforcement()` incorrectly returns a Scarab on total 4 instead of a Macrocyte and a Warrior on total 10 instead of a Tomb Crawler; it also loses every printed weapon option. Separately, `generateRoster()` is wrong on totals 5, 6, and 12 as detailed in SET-05. The two code mappings therefore disagree with each other and neither fully matches the official table. Verified locations: `startTurningPoint()`, `randomReinforcement()`, and `generateRoster()` in `app.js`.

**Required behavior:**
High defect for event/reinforcement order and 2D6 result mapping; the Grade-based quantity itself is compliant. Required correction: Use one authoritative page-5 result table for setup and reinforcements, preserving weapon variants, after event resolution.

**Likely implementation locations:**
`startTurningPoint()`, `randomReinforcement()`, and `generateRoster()` in `app.js`. The owning shared flow is identified in PR 8; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Use one authoritative page-5 result table for setup and reinforcements, preserving weapon variants, after event resolution.

**Dependencies:**
PR 2 shared page-5 generator and PR 3 event-before-reinforcement sequencing.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for REI-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 8.

### REI-02 — Mission 5 room awakening

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 13, Mission 5 “NPOs.”

**Current application behavior:**
The direct mission rule matches the original finding. Verified locations: Mission 5 JSON contains prose; no room-open/entry dispatch exists in `app.js`.

**Required behavior:**
Confirmed High defect. Required correction: Track first opening/entry per eligible room and perform the printed constrained placement.

**Likely implementation locations:**
Mission 5 JSON contains prose; no room-open/entry dispatch exists in `app.js`. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Track first opening/entry per eligible room and perform the printed constrained placement.

**Dependencies:**
PR 2 shared page-5 generator and PR 3 event-before-reinforcement sequencing.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for REI-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### REI-03 — Ten-NPO limit and placement confirmation

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF pages 3 and 5, “NPO Limit,” state a recommendation to limit NPOs to ten and not set up excess; PDF page 3 specifies hatchway placement.

**Current application behavior:**
The pack recommends a ten-NPO limit and immediately instructs players not to set up NPOs that would exceed it, so enforcing that default is not a compliance defect. The confirmed problem is that each reinforcement is marked `deployed:true` before its random hatchway and printed placement constraint have been determined and confirmed. Verified locations: `MAX_NPOS`, `startTurningPoint()`, `reinforcementEntry`, and `deployed:true` in `app.js`.

**Required behavior:**
Medium defect limited to incomplete reinforcement placement; the enforced ten-NPO default is supported by the official pack. Required correction: Preserve the ten-NPO limit and confirm each random hatchway and printed placement constraint before marking a reinforcement deployed.

**Likely implementation locations:**
`MAX_NPOS`, `startTurningPoint()`, `reinforcementEntry`, and `deployed:true` in `app.js`. The owning shared flow is identified in PR 8; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Preserve the ten-NPO limit and confirm each random hatchway and printed placement constraint before marking a reinforcement deployed.

**Dependencies:**
PR 2 shared page-5 generator and PR 3 event-before-reinforcement sequencing.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for REI-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 8.

### REI-04 — Standard reinforcement order/readiness

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 3 requires a Conceal order and exact hatchway placement; it does not explicitly say “ready” for standard Joint Ops reinforcements.

**Current application behavior:**
The missing Conceal-order representation is confirmed. Readiness remains Unable to Verify from the direct text. Verified locations: Reinforcement objects use `ready:true,deployed:true` and have no order field.

**Required behavior:**
Medium confirmed defect for missing order/placement; readiness unresolved. Required correction: Store Conceal order and seek authoritative clarification for readiness.

**Likely implementation locations:**
Reinforcement objects use `ready:true,deployed:true` and have no order field. The owning shared flow is identified in PR 8; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Store Conceal order and seek authoritative clarification for readiness.

**Dependencies:**
PR 2 shared page-5 generator and PR 3 event-before-reinforcement sequencing.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for REI-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 8.

### REI-05 — Ten-NPO maximum scope

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF pages 3 and 5 call ten a recommendation; event cards on pages 21–22 use inability/limit redraw instructions.

**Current application behavior:**
The pack's recommendation is followed immediately by an instruction not to set up NPOs above ten, so the app's enforced default is supported. The compliance defect is card-specific: event cards such as Awakened Warrior and A Chittering Drone require another card to be drawn when their NPO cannot be set up or their alternative effect cannot resolve, while the app can silently stop at the limit. Verified locations: `MAX_NPOS=10` applies to reinforcements, events, and manual additions.

**Required behavior:**
The ten-NPO cap is compliant; silent event blocking instead of the printed redraw is a Medium card-resolution defect already related to EVT-04. Required correction: Preserve the ten-NPO limit and implement each event card's printed redraw instruction when its effect cannot resolve.

**Likely implementation locations:**
`MAX_NPOS=10` applies to reinforcements, events, and manual additions. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Preserve the ten-NPO limit and implement each event card's printed redraw instruction when its effect cannot resolve.

**Dependencies:**
PR 2 shared page-5 generator and PR 3 event-before-reinforcement sequencing.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for REI-05's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### MIS-01 — Universal all-NPOs-dead victory

**Audit status:**
Confirmed

**Severity:**
Critical

**Official rule reference:**
PDF page 8, “End the Battle”; PDF pages 9–14, each mission's “Victory.”

**Current application behavior:**
None of the six missions uses “all NPOs incapacitated” as its player-win condition. Some can legitimately have no NPOs temporarily (especially Mission 5), making the universal rule fundamentally wrong. Verified locations: `checkGameEnd()` declares victory when the generated roster has no living NPO.

**Required behavior:**
Confirmed Critical defect. Required correction: Remove universal elimination victory and implement each printed end condition.

**Likely implementation locations:**
`checkGameEnd()` declares victory when the generated roster has no living NPO. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Remove universal elimination victory and implement each printed end condition.

**Dependencies:**
PR 1 verified mission data shape; shared mission-state schema/evaluators in PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for MIS-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### MIS-02 — Mission-specific rules are display-only

**Audit status:**
Confirmed

**Severity:**
Critical

**Official rule reference:**
PDF pages 9–14, all six mission-rule panels.

**Current application behavior:**
Direct comparison confirms missing Escape movement/state, permanent sabotage state, transponder search/carriage, repair/destruction, room spawn/scouting, and phasing/regroup checks. Verified locations: Mission JSON `rules`; `renderMission()` displays summaries; no mission-rule dispatch in Strategy/activation/end handling.

**Required behavior:**
Confirmed Critical as a combined gap because it prevents correct automated mission play. Required correction: Implement typed mission state and exact timing one mission at a time, while clearly delegating physical placement.

**Likely implementation locations:**
Mission JSON `rules`; `renderMission()` displays summaries; no mission-rule dispatch in Strategy/activation/end handling. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Implement typed mission state and exact timing one mission at a time, while clearly delegating physical placement.

**Dependencies:**
PR 1 verified mission data shape; shared mission-state schema/evaluators in PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for MIS-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### MIS-03 — Generic numeric tracker

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 9–14, mission-specific Victory and mission actions.

**Current application behavior:**
The six missions require distinct state: escaped operatives, seven individually sabotaged/open features, carried marker escape, repairable destruction, eligible scouted rooms, and per-operative end-of-turn regroup predicates. Verified locations: `state.tracker`, `missionTrackerMax()`, generic tracker UI, and unused `completed` in `app.js`.

**Required behavior:**
Confirmed High defect; a scalar may display progress but cannot decide most outcomes. Required correction: Replace the scalar as authority with mission-specific state/evaluators.

**Likely implementation locations:**
`state.tracker`, `missionTrackerMax()`, generic tracker UI, and unused `completed` in `app.js`. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Replace the scalar as authority with mission-specific state/evaluators.

**Dependencies:**
PR 1 verified mission data shape; shared mission-state schema/evaluators in PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for MIS-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### MIS-04 — Mission briefing content

**Audit status:**
Partially Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF pages 9–14, Missions 1–6.

**Current application behavior:**
The PDF now permits verification. Broad summaries are recognizable, but a summary is not sufficient when omitted conditions affect play; Mission 5's Scout action, Mission 6 phasing, and exact victory predicates are examples. Verified locations: `Missions/*.json` and `renderMission()`.

**Required behavior:**
Confirmed Low presentation issue where full official page remains the tabletop authority; High only where the app uses the summary to calculate an outcome. Required correction: Verify every concise summary and label non-automated rules as requiring the official mission page.

**Likely implementation locations:**
`Missions/*.json` and `renderMission()`. The owning shared flow is identified in PR 9; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Verify every concise summary and label non-automated rules as requiring the official mission page.

**Dependencies:**
PR 1 verified mission data shape; shared mission-state schema/evaluators in PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for MIS-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 9.

### DAT-02 — Tomb World NPO datacard completeness

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 5–7, NPO table and datacards.

**Current application behavior:**
The PDF shows Movement, APL, wounds, save, multiple weapon options/profiles, weapon rules, named abilities, orders, and full behavior lists. The exact gap is now directly verifiable. Verified locations: `profiles` in `app.js` has only behavior label, wounds, save, and one attack.

**Required behavior:**
Confirmed High defect. Required correction: Transcribe complete sourced NPO records and declare which fields the guide automates.

**Likely implementation locations:**
`profiles` in `app.js` has only behavior label, wounds, save, and one attack. The owning shared flow is identified in PR 2; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Transcribe complete sourced NPO records and declare which fields the guide automates.

**Dependencies:**
Must precede activation, combat, event, and reinforcement consumers.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for DAT-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 2.

### PER-01 — Permanent state survives reload

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 9–14 require persistent mission state throughout a battle (e.g., sabotaged hatches, carrier, Destruction, scouted rooms). The PDF has no software-save rule.

**Current application behavior:**
The rules establish state that must remain true during play, and the app does not represent it. Reload semantics are an application promise rather than direct rule text. Verified locations: `initialState()`, `save()`, `load()`, `normalizeState()`, and scalar `tracker` in `app.js`.

**Required behavior:**
Confirmed High underlying mission-state gap; persistence architecture itself is Informational until those states exist. Required correction: When mission state is implemented, include it in compatible saves.

**Likely implementation locations:**
`initialState()`, `save()`, `load()`, `normalizeState()`, and scalar `tracker` in `app.js`. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: When mission state is implemented, include it in compatible saves.

**Dependencies:**
The state introduced by the owning mission/event PR; backward-compatible normalization is required.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for PER-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### PER-02 — Temporary effects and combat persistence

**Audit status:**
Partially Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 2 and pages 20–22 establish event durations; no software transaction rule is provided.

**Current application behavior:**
Missing durable event duration is directly relevant and confirmed. The transaction-ID recommendation is engineering design, not a rule conclusion supported by the PDF. Verified locations: No active-event state in `initialState()`; pending attack drafts and commit handlers in `app.js`.

**Required behavior:**
High for absent event-effect persistence/expiry; attack idempotence remains Unable to Verify without behavioral testing. Required correction: Persist active event effects and expiry; separately test combat commits.

**Likely implementation locations:**
No active-event state in `initialState()`; pending attack drafts and commit handlers in `app.js`. The owning shared flow is identified in PR 6; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Persist active event effects and expiry; separately test combat commits.

**Dependencies:**
The state introduced by the owning mission/event PR; backward-compatible normalization is required.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for PER-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 6.

### ABS-01 — Manual geometry predicates

**Audit status:**
Partially Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 4, Threat Principle priorities; PDF pages 6–7, behaviors requiring cover, valid target, obscuring, distance, and control range.

**Current application behavior:**
Manual tabletop input is compatible with the pack, but current prompts do not gather every predicate in the correct action-specific order. Verified locations: `npoQuestions` in `app.js`.

**Required behavior:**
The abstraction is acceptable; its incomplete questionnaire contributes to confirmed NPO-03/04 (High), not a separate defect. Required correction: Retain manual geometry but align questions exactly to the printed decision being resolved.

**Likely implementation locations:**
`npoQuestions` in `app.js`. The owning shared flow is identified in PR 4; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Retain manual geometry but align questions exactly to the printed decision being resolved.

**Dependencies:**
Owning rules engine (activation, Threat, mission, or initiative); do not build a parallel rules path.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ABS-01's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4.

### ABS-02 — Manual terrain/cleanup confirmation

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF pages 9–14 mission terrain/state rules; PDF page 22, The Maze Reforms.

**Current application behavior:**
The interpretation is sound: manual manipulation can preserve play, but the app cannot later evaluate Demolition Protocol or Maze effects without confirmed state. Verified locations: Mission confirmation UI and lack of hatch/breach state in `app.js`.

**Required behavior:**
Confirmed as an Informational design boundary; related mission/event omissions carry the severity. Required correction: Either persist only state needed by later automation or explicitly delegate the later outcome too.

**Likely implementation locations:**
Mission confirmation UI and lack of hatch/breach state in `app.js`. The owning shared flow is identified in PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: Either persist only state needed by later automation or explicitly delegate the later outcome too.

**Dependencies:**
Owning rules engine (activation, Threat, mission, or initiative); do not build a parallel rules path.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ABS-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 7.

### ABS-03 — Manual Threat adjustment

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF page 2, Threat Level; PDF page 13, Scout Room reduction.

**Current application behavior:**
A correction control does not itself contradict the rules, but repeated -1 cannot conveniently implement every printed reduction and is not a substitute for official triggers. Verified locations: Threat HUD buttons call `setThreat(±1, 'Manual adjustment')`.

**Required behavior:**
No standalone compliance defect (Informational); missing automated triggers remain THR-03–05. Required correction: Label as correction and preserve a reason log.

**Likely implementation locations:**
Threat HUD buttons call `setThreat(±1, 'Manual adjustment')`. The owning shared flow is identified in PR 5; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: Label as correction and preserve a reason log.

**Dependencies:**
Owning rules engine (activation, Threat, mission, or initiative); do not build a parallel rules path.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ABS-03's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 5.

### ABS-04 — Manual initiative override

**Audit status:**
Confirmed

**Severity:**
Informational

**Official rule reference:**
PDF pages 2, 3, and 8 specify NPO win choice, Threat-0 automatic initiative, and first-turn player initiative.

**Current application behavior:**
Manual correction is not prohibited, but it must not replace the direct Tomb World cases. Verified locations: Initiative override controls in `app.js`.

**Required behavior:**
Informational; implement the direct cases and label override as correction. Required correction: Keep only as a clearly labeled correction after rules-derived suggestion.

**Likely implementation locations:**
Initiative override controls in `app.js`. The owning shared flow is identified in PR 3; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Preserve the compliant or acceptable behavior as a regression baseline. Do not create an independent rules feature; apply only the scoped integration/labeling noted by the review: Keep only as a clearly labeled correction after rules-derived suggestion.

**Dependencies:**
Owning rules engine (activation, Threat, mission, or initiative); do not build a parallel rules path.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for ABS-04's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 3.

### HR-02 — Generic heuristic and universal elimination win

**Audit status:**
Confirmed

**Severity:**
Critical

**Official rule reference:**
PDF pages 3–7, NPO behavior/Threat Principle; PDF pages 8–14, mission endings.

**Current application behavior:**
Both conflict directly with printed rules. Calling them “house rules” risks understating that the UI does not clearly opt users into alternatives. Verified locations: `chooseNpoDecision()` and `checkGameEnd()` in `app.js`.

**Required behavior:**
Confirmed; Critical for universal victory and High for the behavior heuristic. Required correction: Replace with official logic or explicitly separate an optional house-rule mode from official play.

**Likely implementation locations:**
`chooseNpoDecision()` and `checkGameEnd()` in `app.js`. The owning shared flow is identified in PR 4 and PR 7; state additions must pass through `initialState()`, `normalizeState()`, `save()`, and `load()` when persistence is relevant.

**Implementation approach:**
Make the smallest correction in the existing flow: Replace with official logic or explicitly separate an optional house-rule mode from official play.

**Dependencies:**
The official behavior work in PR 4 and mission-end work in PR 7.

**Regression risks:**
Preserve saved games, all already-compliant portions identified above, cancellation behavior, and the existing mobile interaction pattern; do not implement any excluded Core Book inference.

**Required tests:**
Add a deterministic test or reproducible harness scenario for HR-02's corrected scope; add a negative case proving excluded/unaffected behavior is unchanged; manually exercise the owning flow before and after reload at approximately 390px.

**Recommended pull request:**
PR 4 and PR 7.

### Additional — Dormant NPO state is entirely absent

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 3, “Dormant NPOs.”

**Current application behavior:**
`startTurningPoint()` readies every living NPO regardless of Threat, `setThreat()` has no zero/nonzero transition, and later turns roll initiative at Threat 0.

**Required behavior:**
At Threat 0, all NPOs are dormant, expended, cannot be readied, and players automatically have initiative; when Threat ceases to be 0, all NPOs ready.

**Likely implementation locations:**
`app.js`: `initialState()`, `normalizeState()`, `setThreat()`, `activeNpos()`, `readyNpos()`, `startTurningPoint()`, `rollInitiative()`, `strategyCard()`, and activation scheduling.

**Implementation approach:**
Derive dormancy from Threat rather than duplicating a flag; centralize zero/nonzero transition effects in `setThreat()` and make Ready/initiative consumers honor it.

**Dependencies:**
PR 2 normalized NPO records and PR 3 staged Strategy.

**Regression risks:**
Do not expend player operatives, alter TP1 initiative, or suppress readiness once Threat becomes nonzero.

**Required tests:**
Threat 0 Ready step; attempted NPO activation at zero; automatic initiative; 0→1 readiness; 1→0 expenditure; reload in both states.

**Recommended pull request:**
PR 3.

### Additional — Event deck omissions and duplicate physical weighting

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF pages 20–22, including Subjugation Glyphs, Transdimensional Relocation, My Will Be Done, Reanimation Protocols, Dark of the Tomb, and repeated Awakened Warrior.

**Current application behavior:**
The six-object `events` array omits printed cards, collapses physical instances to unique titles, and samples uniformly with replacement.

**Required behavior:**
Represent every printed physical card instance, including duplicates, and resolve each full effect/redraw condition through the page-2 deck lifecycle.

**Likely implementation locations:**
`app.js`: `events`, `initialState()`, `normalizeState()`, `startTurningPoint()`, `strategyEventHtml()`, `applyStrategyEvent()`, and `resolveStrategyNpoEvent()`.

**Implementation approach:**
Give physical instances stable IDs and typed effect metadata, then use the shared deck/used/active state planned for EVT-03/06.

**Dependencies:**
EVT-01–06 and PR 3 Strategy staging.

**Regression risks:**
Preserve duplicate probability, order of two draws, exact conditional redraws, and old saves containing legacy event objects.

**Required tests:**
Inventory count/title comparison against pages 20–22; duplicate-weight test; every omitted card branch; legacy-save normalization; no replacement within a turning point.

**Recommended pull request:**
PR 6.

### Additional — Starting Conceal orders and printed weapon variants

**Audit status:**
Confirmed

**Severity:**
High

**Official rule reference:**
PDF page 8, “Set Up Operatives”; PDF page 5, NPO table; PDF pages 6–7, datacards.

**Current application behavior:**
`generateRoster()` creates NPOs without an `order` or selected-weapon field and copies one generic `attack` from each broad `profiles` entry.

**Required behavior:**
Every starting NPO is set up with Conceal and retains the exact weapon option specified by its page-5 result.

**Likely implementation locations:**
`app.js`: `profiles`, `generateRoster()`, NPO object normalization, roster rendering, behavior/combat profile selection.

**Implementation approach:**
Extend the shared typed NPO result record with `order` and weapon ID; migrate legacy records without changing their wounds/identity.

**Dependencies:**
SET-05, DAT-02, COM-04, and PR 2.

**Regression risks:**
Do not reroll or replace already-saved NPOs, conflate Engage/Conceal with ready/expended, or break display names.

**Required tests:**
All page-5 rows create the printed weapon and Conceal; saved legacy NPOs normalize; roster, activation, and combat use the selected weapon.

**Recommended pull request:**
PR 2.

### Additional — Explicit initial resources are omitted

**Audit status:**
Confirmed

**Severity:**
Medium

**Official rule reference:**
PDF page 8, “Select Operatives”: up to four equipment options total and 2CP total.

**Current application behavior:**
Setup and `initialState()` have no CP or equipment-selection state; the Strategy checklist only delegates later CP/ploy handling generically.

**Required behavior:**
The guide must either track the explicit starting resources needed by its automated outcomes or clearly require players to establish them on the tabletop before battle.

**Likely implementation locations:**
`app.js`: `initialState()`, `normalizeState()`, setup render/handlers, Strategy guidance; `index.html`/`styles.css` only if the existing dialog pattern needs fields.

**Implementation approach:**
After the PR 1 product decision, prefer explicit delegation if no automated consumer exists; otherwise add minimal compatible fields rather than a full ploy engine.

**Dependencies:**
STR-05 and the human decision about automation scope.

**Regression risks:**
Do not claim to validate team-specific equipment rules, change roster selection, or reset existing games.

**Required tests:**
New and restored setup flows show or retain 2CP/equipment responsibility; zero-to-four selection boundary if tracked; 390px dialog and cancellation checks.

**Recommended pull request:**
PR 1.

## Regression-Test Requirements

Every implementation PR must provide a traceability table from finding ID to official page, changed function/data, and passing test. At minimum, the combined suite must cover:

- **Static/data checks:** every page-5 total; every NPO/weapon/rule on pages 5–7; all physical event instances on pages 20–22; all six missions and maps.
- **State-machine checks:** Strategy stage order, cancel/reload at each stage, Ready/event/reinforcement/initiative ordering, end-of-turn expiry, and next-Ready recycling.
- **Threat checks:** 0–15 bounds, all grades, dormancy transitions, exact default triggers/exceptions, Mission 5 rules, event changes, and malformed imports.
- **Activation/behavior checks:** alternation, official selection priority, each operative behavior branch/fallback, required manual predicates, target ties, and no premature expenditure.
- **Combat checks:** every NPO ranged/melee profile and mission-pack weapon rule, with canceled/committed action boundaries. Do not treat Core Fight/cover/save claims as certified.
- **Reinforcement checks:** after-first-turn gate, event-first Grade, Grade quantity, shared table, ten-NPO cap, Conceal/placement, and Mission 5 room awakenings.
- **Mission checks:** at least one win, one continuing state, and every printed loss/boundary for each mission; verify an empty NPO roster never wins by itself.
- **Persistence checks:** fixtures from the current state shape plus new event/mission states; no localStorage clearing; no duplicate effect/action after reload.
- **UI checks:** approximately 390px and desktop; no horizontal scrolling, clipped dialogs, hidden actions, overlap, or unusable touch targets; internal scrolling for long event/behavior flows.
- **Application checks:** JavaScript syntax, no browser-console errors, setup/dialog/event handlers, static GitHub Pages loading, and full setup-to-completion smoke runs.

## Final Compliance Verification

After PR 9, a reviewer must independently:

1. Re-enumerate the audit review and confirm every Confirmed finding and every corrected Partially Confirmed scope has a matrix entry and test result.
2. Confirm all Incorrect findings remain excluded: SET-06, STR-01, STR-06, EVT-05, NPO-05, NPO-06, MIS-05, DAT-03, and PER-03 are not independent approved changes even where their narrative overlaps a separately approved finding.
3. Confirm all Unable to Verify findings remain unimplemented unless separately authorized: ACT-02, COM-01/03/05/06/07, DAT-01, HR-01, plus unresolved portions of STR-04, ACT-04, REI-04, and PER-02.
4. Compare each implemented change directly to its cited PDF page, including exact timing, prerequisites, exceptions, card multiplicity, redraw, placement, and mission end conditions.
5. Trace each rule to one authoritative calculation/data source; reject duplicate tables or screen-local versions.
6. Exercise all acceptance and regression tests above, inspect browser console output, and perform complete runs of all six missions.
7. Load pre-remediation saves and verify compatibility without silent data loss.
8. Verify 390px mobile and desktop usability for every changed dialog/flow.
9. Review the final diff of every PR for unrelated changes and confirm version/cache work occurs only when a future numbered release explicitly requires it.
10. Produce a final residual-risk list containing only externally sourced, consciously delegated, or Human Decisions Required items.

## Human Decisions Required

These decisions block only their stated scope; they are not permission to guess beyond the PDF.

### Supported solo roster legality (SET-03 / DAT-01 boundary)

- **Official requirement:** PDF pages 1 and 8 say a solo player selects a kill team normally; team legality is delegated to each kill team's rules.
- **Current behavior:** `playerRosterLimits()` and `autoSelectRequiredPlayerOperatives()` enforce only local JSON constraints for three teams.
- **Choices:** (1) explicitly delegate legality to the player; or (2) obtain and version current official team publications, audit each supported team, and automate only verified constraints.
- **Decision needed:** Which teams/rules revisions are supported and whether the guide promises validation. Co-op half-team selection remains outside this solo app unless product scope changes.

### CP and equipment automation (STR-05 / additional resources)

- **Official requirement:** PDF page 8 grants 2CP total and permits up to four equipment options; page 2 says NPOs gain no CP.
- **Current behavior:** no CP/equipment state exists; generic checklist text delegates Strategy activity.
- **Choices:** (1) clearly delegate resources to tabletop play; (2) track only totals/selections affecting existing automation; or (3) build broader resource automation in a separately approved scope backed by team rules.
- **Decision needed:** Whether the guide is a reminder or an authority for these resources. Do not build a ploy engine merely for completeness.

### Standard reinforcement readiness (ACT-04 / REI-04 unresolved portion)

- **Official requirement:** PDF page 3 expressly requires Conceal and placement but does not explicitly state ready/expended for standard reinforcements; specified event arrivals on pages 21–22 do state ready.
- **Current behavior:** standard reinforcement objects are created `ready:true,deployed:true` with no order.
- **Choices:** (1) preserve readiness while correcting confirmed order/placement only; or (2) change readiness after an authoritative Core Book/FAQ source is supplied.
- **Decision needed:** No readiness change is approved from this PDF alone.

### Manual tabletop delegation boundary (ABS-01/02)

- **Official requirement:** pages 4 and 6–7 require spatial predicates; pages 9–14 and 22 require physical terrain state that later rules may consume.
- **Current behavior:** users answer some geometry prompts and confirm terrain generally, but the app later calculates outcomes without all required predicates/state.
- **Choices:** (1) collect and persist the minimum confirmations later automation needs; or (2) explicitly delegate both the physical step and dependent outcome to the player.
- **Decision needed:** Per rule, decide where automation ends. A split in which the app omits input but claims the outcome is not acceptable.

### Core Book and external-publication questions

The following are **not approved corrections**: ACT-02; COM-01, COM-03, COM-05, COM-06, COM-07; DAT-01; HR-01; generic initiative tie/reroll behavior in STR-04; attack idempotence in PER-02. Obtain the applicable Core Book, current team rules, FAQ/errata, or behavioral reproduction, then conduct a separate review. Until then, preserve behavior or clearly label a control as manual correction; do not claim official compliance.
