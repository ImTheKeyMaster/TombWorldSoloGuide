# Tomb World Solo Guide v3.2.5

A separate, mobile-first guided-play application for solo Kill Team missions in a Necron tomb world. This project does not replace Tomb World Solo Command.

## v1.1.6 additions

- Mission maps now scroll horizontally on portrait phones without widening the page.
- Added a swipe hint and visible horizontal scrollbar on mobile.
- Desktop maps still scale to the available width.


- Two-step guided Strategy Phase
- Automatic Turning Point preparation
- Threat meter with grade labels and manual correction controls
- Automatic NPO readying and Player reset
- Mission-aware reinforcement generation after Turning Point 1
- Visual 2D6 reinforcement rolls with pip dice
- Ten-NPO battlefield limit handling
- Reinforcement entry-point recording
- Grade 3 Tomb World event checks and supported automatic effects
- Guided initiative rolls, rerolls, and manual override
- Persistent activation tracker for Player operatives and individual NPOs
- Automatic alternation between Player and NPO activations
- Automatic transition to end-of-Turning-Point scoring
- Backward-compatible migration of v1 saved games

## Existing v1 foundation

- New Game setup wizard
- Six mission briefings and schematic board layouts
- Mission-specific starting NPO roster generation
- Guided NPO and Player deployment
- Persistent Play dashboard showing the next required action
- Guided NPO decision wizard and visual attack dice
- Editable NPO roster, Battle Journal, import/export, and PWA support

## Publish with GitHub Pages

1. Create a new repository or use a separate branch such as `feature/tomb-world-solo-guide`.
2. Upload the contents of this folder to the repository root.
3. In GitHub, open **Settings → Pages**.
4. Publish from the selected branch and `/ (root)` folder.

No build step or server is required.

## Important

This is an unofficial play aid. Use the official Kill Team and Tomb World publications for authoritative rules, mission wording, terrain placement, and datacards.


## v1.1.6
- Restyled all six generated mission maps to match the darker, higher-contrast Solo Command presentation.
- Added grid, framed canvas, glowing hatchways, stronger walls, and differentiated mission markers.
- Preserved the Guide map geometry and guided-play workflow.
- Standardized the asset directory name to `Assets`.


## v1.1.6

- Bundles the official Games Workshop Tomb World mission-pack PDF in `Assets/`.
- Displays a cropped extract of the appropriate official mission map directly inside the Guide.
- Shows only the selected mission map rather than both maps printed on the PDF page.
- Keeps all map content local and available from GitHub Pages without linking out.

Official source PDF: Games Workshop, *Joint Ops: Tomb World Mission Pack*.
The application includes the PDF locally and uses pre-rendered crops of pages 17-19 so each mission displays only its own map reliably on mobile browsers.


## GitHub Pages deployment

Upload the **contents of this folder while preserving the folder structure**. In particular:

- `index.html`, `app.js`, `styles.css`, and `manifest.webmanifest` must remain at the repository root.
- `Assets/icon.svg` must remain inside `Assets`.
- All six map files must remain inside `Assets/Maps`.
- `Assets/Tomb-World-Mission-Pack.pdf` must remain inside `Assets`.

Do not rename files or flatten the `Assets/Maps` folder. The included `.nojekyll` file tells GitHub Pages to publish the static files as-is.


## v1.3.0 AI release

- Guided one-question-at-a-time NPO activation wizard
- Behavior-aware decision tree for Fight, Charge, Shoot, Operate Hatch, contesting objectives, and repositioning
- Explicit target-priority selection
- Decision-path explanation for each recommendation
- Animated visual NPO attack dice with critical, normal-hit, and miss results
- Activation history records the recommended action


## v1.3.0 Combat

- Guided Player attack wizard targeting an NPO
- Guided NPO attack save and damage wizard
- Visual attack and save dice with pips
- Critical and normal save cancellation
- AP, cover retention, configurable defense dice, saves, and damage profiles
- Damage preview before confirmation
- Confirmed Player damage automatically updates NPO wounds
- NPO damage is recorded for application to the Player operative on the tabletop


## v1.3.1 Guided-flow refinements

- `Begin Turning Point 1` now proceeds directly into Turning Point preparation and initiative.
- Removed the redundant intermediate `Start Turning Point 1` screen from initial setup.
- Added Move, Dash, Charge, Fall Back, Mission Action, and Pass options to Player activation recording.
- Movement actions are recorded without changing Threat.
- Completing an activation with no selected actions now requires explicit confirmation.
- Player activation history and Journal entries now summarize the recorded actions.


## v1.3.2 Player activation combat flow

- Grouped Player activation actions into Movement, Combat, Battlefield, and Pass sections.
- Renamed the Fight-facing UI to Melee while retaining the underlying Kill Team Fight action meaning.
- Checking Shoot reveals Resolve Shooting Attack.
- Checking Melee reveals Resolve Melee Attack.
- Removed the separate Did the Player attack an NPO section.
- Shooting and Melee attacks can be resolved independently in the same activation.


## v1.3.3 Setup and combat safeguards

- Attack Wizard target selection now starts blank.
- All attack profile controls remain disabled until a Target NPO is selected.
- Added **Check All** to the Build the Killzone setup step.
- Added **Place All** to the Deploy NPOs setup step.
- Player activations cannot be completed while Shoot or Melee is checked but unresolved.
- Players can either resolve the checked attack or return and uncheck the action.


## v1.3.5 Guided navigation cleanup

- Removed the permanent bottom navigation bar.
- Added a single **Game Menu** button to the header during an active game.
- Mission, Roster, Journal, and Help are now optional reference screens and do not alter the current guided-play state.
- Added **Return to Guided Play** at the top of every reference screen.
- Added an always-available **Start New Game** command to the Game Menu.
- Export and Import Save are also available from the Game Menu.
- Removed duplicate session controls from the Mission reference screen.


## v1.3.5b activation tracker fix

- Corrected the Player operative indicator layout class mismatch.
- Replaced malformed bars with numbered circular indicators.
- Activated operatives use a green circle and check badge.
- Operatives that still need to activate use a neutral outlined circle.
- Added live Activated and Remaining counts.


## v1.3.6 Map update

- Replaced all six mission maps with newly cropped 767×661 PNG files.
- Preserved existing paths and gameplay behavior.


## v1.3.7 Mobile deployment polish

- Standardized every **Mark Placed** / **Placed** button to the same width on iOS and other mobile browsers.
- Separated each NPO name from its operative type.
- NPO names stay on one line and truncate cleanly if necessary.
- Operative type now appears on its own line beneath the name.


## v1.3.7b
- Prevented the step indicator (e.g. 3/6) from wrapping on narrow mobile screens.


## v1.3.8 Step navigation

- Moving to a different setup or gameplay step now returns the page to the top.
- The scroll reset only occurs when the guided step changes.
- Toggling controls within the same step does not reset the scroll position.
- Includes an iOS-compatible top reset after the new content renders.


## v1.3.9 Alternating activations

- Player and NPO operatives now alternate one activation at a time.
- Initiative determines which side activates first.
- After a Player activation, an NPO activates next when one is ready.
- After an NPO activation, a Player operative activates next when one remains.
- If one side runs out of ready operatives, the other side completes its remaining activations consecutively.
- When neither side has ready operatives, the Guide automatically enters End of Turning Point.
- Added a prominent **Next Activation** banner to Guided Play.
- At Threat 0, NPOs remain dormant, so the Player correctly completes all Player activations.


## v1.3.9a Turning Point initiative fix

- Automatic Player initiative now applies only during Turning Point 1.
- NPO dormancy now applies only during Turning Point 1.
- Beginning with Turning Point 2, surviving NPOs are readied even if Threat is still 0.
- Initiative is rolled normally from Turning Point 2 onward.
- Corrected the Strategy Phase explanation so it no longer implies that Threat 0 permanently prevents NPO activation.


## v1.3.9b Initiative button emphasis

- The side that wins the initiative roll now receives the highlighted primary action button.
- The other side remains available as a secondary override.
- During Turning Point 1, Player initiative remains automatic and the NPO option stays disabled.


## v1.3.9d Player activation transaction fix

- A specific remaining Player operative must be selected before recording an activation.
- Activated Player operatives cannot be selected again during the same Turning Point.
- Shoot and Melee are resolved only after **Complete Activation** is pressed.
- Attack damage remains pending and does not change NPO wounds until **Confirm Activation**.
- Canceling an attack returns to the Player activation screen with no damage applied.
- Going back from final confirmation allows actions to be changed or unchecked safely.
- Activation tracker circles now reflect the exact Player operative numbers already activated.


## v1.3.9e APL enforcement

- Added an APL selector to each Player activation, defaulting to 3.
- Added a live **AP used / APL** display.
- Action costs are enforced:
  - Move, Dash, Charge, Shoot, Melee, Operate Hatch, Breach, mission actions, and other damaging actions cost 1 AP.
  - Fall Back costs 2 AP.
- Unselected actions that would exceed the operative's remaining AP are disabled.
- Invalid action combinations are blocked:
  - Charge cannot be combined with Move, Dash, or Fall Back.
  - Fall Back cannot be combined with Move or Charge.
  - Pass cannot be combined with another action.
- Shoot and Melee may both be selected when the combined AP cost is legal.


## v1.4.0 Initial documentation update

- Expanded Home → How It Works into a full onboarding guide.
- Added game flow, Player activation, APL, Threat, and terminology guidance.
- Added a detailed NPO AI decision explanation based on the Solo Command logic.
- Added the same AI guidance and quick-reference terminology to Game Menu → Help.
- No gameplay logic changed in this initial v1.4.0 release.


## v1.4.0b Game Flow layout fix

- Confirmed that the numbered circle, title, and description were being treated as three separate grid items inside a two-column layout.
- Assigned the title and description to the full-width second column.
- Made the numbered circle span both text rows.
- Prevented the Game Flow description from collapsing into a one-word-wide column on mobile.


## v1.4.0c iOS How It Works scrolling fix

- Confirmed that iOS could scroll both the long dialog and the page behind it.
- Locks background-page scrolling while **How It Works** is open.
- Makes the dialog content the only vertical scrolling region.
- Uses dynamic viewport height and safe-area spacing for iPhone.
- Removes the scroll lock whenever the dialog closes.

v1.4.0d: Dialog scroll simplification.


## v1.4.1

- Replaced the Home **How It Works** dialog with a dedicated in-app screen.
- Added Back and Back to Home controls.
- Removed the long-content dependency on the native `<dialog>` element.
- The screen now uses normal document scrolling, eliminating nested iOS scroll regions.
- The visible version badge is set from the same `APP_VERSION` constant used by the build.
- Gameplay logic is unchanged.


v1.4.2: Expanded Strategy Phase guidance and renamed 'Turning Point 1 Prepared' to 'Complete the Strategy Phase'.

## v1.4.3

- Updated the actual **Turning Point prepared** Strategy Phase screen.
- Replaced the status-only heading with **Complete the Strategy Phase**.
- Added clear instructions for CP, Strategic Ploys, Strategy Phase abilities, mission rules, and reviewing Guide results.
- Renamed the action button to **Strategy Phase Complete · Continue to Initiative**.


v1.4.4: Correct initiative message grammar (wins vs win).


## v1.4.5

- Added the same rolling-dice animation used by **Roll Attack & Saves** to **Determine initiative**.
- Both Player and NPO dice animate simultaneously on the initial initiative reveal.
- **Reroll Both** now repeats the animation before revealing the new values.
- The initiative winner and activation controls remain hidden or disabled until the 700 ms roll animation settles.


## v1.4.6
- Updated the Threat label to 'Threat Level: <Grade>' on the Strategy Phase and Activation Phase screens while leaving the +/- controls in their existing positions.


## v1.4.7
- Threat strip now displays 'Threat Level: <state>'.
- HUD labels updated to THREAT LEVEL and GRADE LEVEL.
- Removed numeric Threat value from HUD.


## v1.4.8

- Fixed the HUD so it displays **THREAT LEVEL** with the current numeric Threat value beneath it.
- Updated the Threat controls heading to **THREAT LEVEL: Dormant/Stirring/Awakened/Overrun**.
- Corrected the threat-state names to Dormant, Stirring, Awakened, and Overrun.


## v1.4.9

- Fixed the Strategy Phase Guide so **GRADE LEVEL** updates live whenever Threat crosses a grade threshold.
- The Strategy Phase Guide and HUD now both use the current `threatGrade()` value.


## v1.5.0

- Added a Turning Point completion summary showing Threat, Grade, NPO losses, and Player casualties.
- Added prominent Grade escalation milestone banners when Threat crosses into a new Grade.
- Added persistent Player casualty tracking. Player operative indicators can now be selected to mark an operative eliminated or restore it.
- Eliminated Player operatives are visually grayed out, excluded from Player Ready counts, and remain eliminated across Turning Points.


## v1.5.1

- NPO activations that include an attack can no longer be completed before the attack is resolved.
- **Activation Complete** remains disabled until the NPO Attack Wizard is confirmed.
- Canceling the attack wizard returns to the activation result with completion still disabled.
- After confirming the attack result, the activation screen returns with **Activation Complete** enabled.


## v1.5.2
- Initiative roll now highlights only the winning die in green. Losing dice use the same gray styling as misses on Attack Rolls.


## v1.5.3
- NPO attacks with zero hits or critical hits are automatically considered resolved. The app displays 'Attack missed. No saves or damage required.' and immediately enables Activation Complete without opening the attack wizard.


## v1.5.4

- Corrected the dedicated initiative dice renderer.
- The winning initiative die remains green.
- The losing initiative die now uses the same gray styling as an Attack Roll miss.
- If the displayed initiative dice are tied, both remain green.
- The styling is applied both on the initial result and after reroll animations.


## v1.5.5

- Canceling the Resolve NPO Attack dialog now returns to the activation result with the exact same stored attack dice.
- The attack dice no longer replay their rolling animation after canceling, which previously made them appear to be rerolled.
- Reopening Resolve NPO Attack continues to use the original stored dice.


## v2.0.0

Major player-roster update:

- Added `Player_Operatives/DeathWatch.json` as the external source for Deathwatch operative data.
- Added all 11 official Deathwatch operative choices:
  Sergeant, Aegis, Breacher, Blademaster, Marksman, Demolisher, Horde-Slayer, Headtaker, Gunner, Bombard, and Disruptor.
- Added official APL, Move, Save, Wounds, base size, weapon profiles, weapon rules, and named abilities.
- Replaced the manual Player operative count with a Deathwatch roster builder.
- Enforced the official roster rules: exactly five unique operatives and no more than one Gravis operative.
- Player operative names now appear in setup, activation selection, activation history, casualty controls, and the activation tracker.
- The data-loading structure supports adding more team JSON files to `Player_Operatives` later.


## v2.0.1

- Deathwatch operatives now use the same compact card grid and visual structure as NPO operatives.
- Both sides display the operative name on the left and status on the right.
- Removed the activation-state key/legend because status is now written directly on every operative card.
- Player cards remain selectable for eliminating or restoring an operative.


## v2.0.2

- Standardized activation terminology across both sides.
- Player operatives and NPOs now both use `READY` before acting and `ACTIVATED` after acting.
- Removed the visible `EXPENDED` status from the NPO activation tracker.


## v2.1.0

- Added `Player_Operatives/manifest.json`.
- Player Kill Teams are discovered from the manifest instead of being hardcoded.
- Added a Kill Team selection screen when the manifest contains two or more teams.
- When the manifest contains exactly one team, that team loads automatically and the selection screen is skipped.
- Save data now stores `playerTeamId`; the manifest resolves the matching JSON filename.
- Additional teams can be supported by adding a JSON file and manifest entry without changing application code.


## v2.1.1

- Fixed Turning Point 1 NPO readiness.
- All active NPOs now begin every Turning Point as `READY`.
- Beginning the Turning Point 1 Firefight Phase no longer marks the entire NPO force as activated.
- Shifting Labyrinth still begins Turning Point 1 with the Player, but both forces remain ready and alternate normally.
- Updated the Turning Point 1 guidance text to match the corrected behavior.


## v2.2.0

- Added `Missions/manifest.json` and one external JSON file for each of the six official Joint Ops: Tomb World missions.
- Removed embedded mission definitions and map data from `app.js`.
- Mission selection, starting NPO formula, deployment instructions, Turning Point 1 initiative, progress tracker, mission rules, victory conditions, and maps are now loaded from mission JSON.
- All six official missions specify Player initiative in Turning Point 1, as required by the common Joint Ops game sequence.
- Both Player operatives and NPOs begin every Turning Point ready.
- Future missions can be added by creating a mission JSON file and adding it to the mission manifest, without changing application code.


## v2.2.1

- Corrected `Enemy Save Dice` to `Player Save Dice`.
- Added a required `Target Player Operative` selection to the NPO Attack Wizard.
- The selector lists all rostered Player operatives that have not been eliminated.
- Selecting an operative automatically loads its Save and starting Wounds values.
- The selected target persists if the wizard is canceled and reopened.
- Combat results and the journal now identify the targeted Player operative by name.


## v2.2.2

- Moved Player operative selection to the `Target Priority` section.
- `Resolve NPO Attack` remains disabled until a living Player operative is selected.
- Removed target selection from the NPO Attack Wizard; the selected target is shown read-only.
- After `Roll Saves & Preview Damage`, the defense controls and target are locked unless the wizard is canceled.
- Removed the `Review NPO Attack` button after resolution.
- Target selection resets for each new NPO activation and clears when the activation is completed.


## v2.2.3

- NPO attack dice are no longer rolled before target priority is resolved.
- The Player operative is selected in the Target Priority section and locked with `Confirm Target`.
- Confirming the target immediately rolls the NPO attack dice and disables the target selector.
- The next action is now `Roll Player Saves`.
- After saves are rolled, the final action is `Apply Damage`.
- Canceling the save workflow returns to Target Priority, unlocks the target, and discards the previous attack roll so a new target can be confirmed and rolled correctly.
- The obsolete `Review NPO Attack` action remains removed.


## v2.2.4

- Added a permanent, non-collapsible `NPO Attack Summary` to the Recommended Activation screen after damage is applied.
- The summary shows the targeted Player operative, Player save roll, unsaved normal and critical hits, damage, and wounds before and after.
- The Player save roll now appears immediately after the NPO attack roll.
- The attack summary remains visible until the NPO activation is completed.
- Renamed `Activation Complete` to `Complete Activation`.


## v2.2.5

- In phone portrait orientation, every HUD heading uses the same two-line layout so all values align.
- Landscape and desktop HUD headings remain on one line when space allows.
- The Threat Level adjuster is hidden by default.
- Tap the Threat Level HUD cell to show or hide the manual Threat controls.


## v2.2.6

- Removed sticky positioning from the HUD so it scrolls normally with the page.
- Kept the title bar and Game Menu sticky at the top.


## v2.2.7

- Removed the redundant `Next Activation` banner from the Activations screen.
- The existing Firefight Phase activation card remains the single source of next-action guidance.


## v2.2.8

- Replaced the editable Player defense controls in the NPO Attack Wizard with a read-only defense profile.
- Removed the plus/minus buttons and editable fields for Defense Dice, Save, NPO AP, and Current Wounds.
- Defense Dice is fixed at 3; Save and Wounds come from the selected Player operative; NPO AP comes from the attacking profile and defaults to 0.
- Cover remains the only defense option the user selects before rolling Player saves.


## v2.2.9
- Removed normal success toast after NPO attack resolution.
- Firefight header now shows ACTIVATION X OF Y.
- Total activations are calculated at the start of each Turning Point.


## v2.2.9b

- Fixed the activation card headers so both Player and NPO activation screens display `ACTIVATION X OF Y`.
- Added a shared activation-progress formatter to keep activation titles consistent.
- Corrected the Turning Point total to count all active NPOs, regardless of their previous ready state.
- Removed routine success toasts while retaining validation and error messages.


## v2.2.9c

- Corrected the activation total to equal the number of living operatives currently in the game.
- The total is calculated as all Player operatives not listed as casualties plus all NPO operatives with wounds remaining.
- Activated status and ready status no longer affect the denominator.


## v2.2.9d

- Added persistent live wound tracking for Player operatives.
- The NPO Attack Wizard now loads the selected operative's current wounds rather than the starting wounds from the team JSON.
- Applying damage writes the new wound value back to game state immediately.
- Player operatives reduced to 0 wounds are automatically marked as casualties.
- Restoring an operative restores its full starting wounds.


## v2.2.9e

- Removed the redundant `No Player Operatives Ready` button.
- The Guide now relies entirely on tracked Player readiness.
- When no Player operatives remain ready, the activation flow automatically advances to an NPO, or to End Turning Point when neither side has operatives left to activate.


## v2.2.9f

- Removed the remaining routine gameplay toast notifications for Operate Hatch and Breach results.
- Threat changes from those actions still apply normally and remain recorded in the Battle Journal.
- Validation and error toasts remain available.


## v2.2.9g

- Fixed the Player operative dropdown on iPhone by removing the disabled fieldset overlay that could intercept taps when the activation dialog first opened.
- Player activation controls remain visually inactive and non-interactive until an operative is selected.


## v2.2.9h

- Added a Player Roster reference screen to the Game Menu.
- Shows each selected Player operative's role, APL, Move, Save, current wounds, activation status, and weapons.
- Player status can be reviewed and updated directly from the roster screen.


## v2.2.9k

- Corrected Player Roster wound display to show current wounds over the operative's original maximum wounds.
- Example: a Headtaker reduced to 8 wounds now displays `8/13`, not `8/8`.


## v2.3.0

- Removed the editable plus/minus controls from the Resolve Shooting Attack and Resolve Melee Attack screens.
- Player attack values now come directly from the selected operative's roster weapon profile.
- Added a weapon selector because many operatives have more than one ranged or melee weapon.
- NPO Defense Dice is fixed at 3, while the target Save comes from the selected NPO.
- NPO names are numbered only when multiple operatives of the same type exist.


## v2.3.1

- Corrected NPO names in the Activation Tracker to use duplicate-only numbering.
- Duplicate NPOs are now numbered sequentially by operative type, such as `Necron Warrior 1`, `Necron Warrior 2`, and `Necron Warrior 3`.
- The Activation Tracker now lists eliminated NPOs instead of hiding them.
- Eliminated Player operatives remain visible and are labeled `ELIMINATED`.
- Eliminated NPOs are labeled `ELIMINATED`.


## v2.3.2

- Centralized all NPO display naming in one `npoName()` function.
- Every screen now uses the same naming rule, including setup deployment, activation cards, attack screens, the Activation Tracker, the NPO Roster, summaries, logs, and battle history.
- A number is shown only when more than one NPO of the same type exists.
- Removed the need for localized NPO naming fixes in individual screens.


## v2.3.3

- Added one global operative-sorting function used before every render.
- Player team definitions, selected Player operatives, and the complete NPO roster are now alphabetized from their authoritative data arrays.
- All screens inherit the same order automatically, including setup, deployment, selectors, Activation Tracker, Player Roster, NPO Roster, and attack target lists.
- Duplicate NPO numbering remains consistent because it is assigned after the globally sorted NPO order is established.


## v2.3.4

- The Resolve Shooting Attack and Resolve Melee Attack dialogs now open scrolled to the top on mobile.
- Target NPO selection now appears above weapon selection.
- When an operative has only one eligible weapon, it is shown as a read-only value instead of an unnecessary dropdown.
- NPO target options now use the label `Wounds` instead of `projected wounds`.
- `NPO Defense Dice` and `NPO Save` were moved out of the Player Attack Profile into a separate `NPO DEFENSE PROFILE`.
- Renamed `Target Save` to `NPO Save`.
- The cover option is now grouped with the NPO Defense Profile.


## v2.3.5

- Removed the separate APL field from the Resolve Player Activation dialog.
- AP Used now provides the complete AP display, such as `0 / 3`.
- The operative's APL is read directly from the Player roster and is no longer editable.
- Removed the white fieldset border around the Player activation controls.


## v2.3.6

- Removed the redundant instructions `Confirm the target before rolling the NPO attack.` and `Complete the attack before finishing this activation.`
- Confirm Target now opens the NPO Attack Wizard immediately.
- The NPO attack roll no longer appears on the Recommended Activation screen.
- NPO attack dice animate inside the NPO Attack Wizard.
- Roll Player Saves becomes available after the attack-dice animation completes.


## v2.3.7

- Fixed an intermittent iOS Safari issue where the Player Operative dropdown could not be opened immediately after selecting Resolve Player Activation.
- Modal launch now clears focus from the button that opened it.
- The dialog container receives focus instead of Safari automatically focusing or trapping another control.
- The Resolve Player Activation dialog is reset to the top before the Player Operative dropdown becomes interactive.


## v2.3.8

- Added a prominent NPO Eliminated banner to the Confirm Player Activation dialog when an attack reduces an NPO to 0 wounds.
- Reworked attack results into structured cards showing attack type, target, damage, and wound change.
- Added a red elimination badge, highlighted card, and emphasized 0-wound result for lethal attacks.
- Added eliminated NPO names to the Actions summary.


## v2.3.9

- Kept Player activations planned as a single low-interruption workflow rather than converting them to action-by-action entry.
- When a Shoot attack eliminates an NPO before a selected Melee action, the Melee wizard now clearly asks for another target or offers Skip Melee.
- If no NPO targets remain after Shooting, Melee is skipped automatically without another prompt or click.
- Replaced the fixed eight-question NPO activation sequence with an adaptive question flow.
- Irrelevant NPO questions are skipped once the Guide already has enough information to choose the activation.
- Adaptive NPO prompts retain Back navigation.


## v2.4.0

- Starting NPO rosters now generate automatically when the roster setup step opens; Regenerate Roster remains available.
- NPO cards now use the same visual system as Player roster cards, with behavior, attack, hit, save, wounds, and status.
- Added focusable/hoverable tooltips to Threat Level, Grade Level, NPOs Ready, and Reinforcements on the Strategy Phase screen.
- Renamed the Strategy Phase completion button to Strategy Phase Complete.
- The mission now ends after Turning Point 4 is completed.
- Renamed the Player activation screen to Player Activation and its button to Activate an Operative.
- NPO activation screens now use NPO Activation: [name], remove the repeated operative type, and use Activate NPO.


## v2.4.1

- Removed the internal labels “QUESTION”, “ADAPTIVE”, and “NPO PERSPECTIVE” from the NPO decision dialog.
- Renamed the dialog’s Cancel button to “Exit Guide”.
- Kept the Back button and adaptive decision flow unchanged.

## v2.4.2
- Removed redundant Player/NPO activation labels.
- Retained a subtle “Activation X of Y” line.
- Shortened the Player and NPO next-step instructions.


## v3.0.0 — Phase 1

- Reordered New Game Setup to define the Player team and roster before generating NPOs.
- New setup order: Mission, Killzone, Player Kill Team (when needed), Player Roster, NPO Roster, Deploy Kill Teams, Ready.
- The Player Kill Team step is automatically omitted when only one team is installed.
- Setup progress and step totals are calculated dynamically.
- Combined Player and NPO deployment into one setup step.


## v3.0.1 — Deployment cleanup

- Simplified the Deploy Kill Teams screen to two confirmations.
- Player deployment remains a single checkbox.
- Necron deployment is now also a single checkbox.
- Removed individual NPO deployment rows and the Place All NPOs button.
- Deployment Complete remains disabled until both sides are confirmed.


## v3.0.3

- Removed the mission map from the Ready to Begin screen.
- Corrected all displayed and runtime version numbers to v3.0.3.
- Updated asset cache keys so browsers load the latest JavaScript and CSS.


## v3.0.4

- Simplified the Ready to Begin screen.
- Removed Player and NPO operative summaries.
- Retained only Mission, Objective, and Special Rules.
- Corrected the displayed application version and cache-busting keys.


## v3.0.5

- Renamed the final setup panel to Mission Briefing.
- Combined Mission, Objective, and Special Rules into one briefing card.
- Displayed each mission special rule as its own scannable section.
- Updated visible and internal version numbers to v3.0.5.


## v3.0.6

- Improved the Generate NPO Roster step for missions with zero starting NPOs.
- Hidden the Regenerate Roster button when the mission starts with no deployed NPOs.
- Replaced the low-emphasis empty state with a prominent deployment message.
- Added reinforcement guidance explaining when the first NPOs enter play.
- Updated visible, internal, and cache-busting version numbers to v3.0.6.


v3.0.7: Kasrkin roster choices updated.


## v3.0.8

- Rebuilt Kasrkin Gunner choices as five distinct selectable operatives with only their correct weapon profiles.
- Gunner choices are displayed as Flamer, Grenade Launcher, Volley Gun, Meltagun, and Plasma Gun.
- Added three independently selectable Kasrkin Trooper entries that all display simply as “Trooper” during roster selection.
- Selected duplicate Troopers are automatically labeled Trooper 1, Trooper 2, and Trooper 3 during gameplay, wound tracking, activation, and targeting.
- Enforced the Kasrkin maximum of four Gunners in the roster builder.
- Updated visible, internal, and cache-busting versions to v3.0.8.


## v3.1.3

- Expanded Death Korps roster choices to support a legal 14-operative roster.
- Split the generic Gunner into Flamer, Grenade Launcher, Meltagun, and Plasma Gun choices.
- Added four separately selectable Trooper positions, displayed simply as “Trooper” during roster selection.
- Duplicate Troopers are numbered automatically during gameplay for activations, wounds, and targeting.
- Added Death Korps validation for four required Troopers, the Watchmaster leader, and a maximum of four Gunners.
- Updated visible, internal, and cache-busting versions to v3.1.3.


## v3.2.0

- Added an operative-style checkmark to the selected Kill Team.
- Increased toast contrast so notifications stand out from game screens.
- Moved activation tracker operative details into a collapsible section titled with the completed activation count.
- Updated visible, internal, and cache-busting versions to v3.2.0.


## v3.2.1

- Removed the iOS focus outline from open dialogs.
- Removed plus signs only from unselected Kill Team cards while retaining plus signs on unselected operative cards and the selected checkmark on both card types.
- Updated visible, internal, and cache-busting versions to v3.2.1.


## v3.2.2

- Added immediate Victory and Defeat detection when every operative on one side is eliminated.
- Added dedicated game-end pages that reuse the existing Start New Game confirmation flow.
- Updated visible, internal, and cache-busting versions to v3.2.2.

## v3.2.3

- Added themed artwork to the Victory and Defeat screens and removed their redundant text headings.
- Styled the result artwork with the app's green border and rounded corners.
- Updated visible, internal, and cache-busting versions to v3.2.3.

## v3.2.4

- Displayed the sole eligible NPO target as a read-only field in Player shooting and melee attack dialogs.
- Automatically prepared the combat controls and profiles when only one eligible target remains.
- Updated visible, internal, and cache-busting versions to v3.2.4.

## v3.2.5

- Added the existing Kill Team selection checkmark treatment to the selected mission card.
- Updated visible, internal, and cache-busting versions to v3.2.5.
