# Tomb World Solo Guide v5.7.8

## v5.7.8

**Version 5.7.8 - NPO Attack Profile Summaries**

- Added the shared Attack profile card to NPO shooting and melee combat resolution screens.
- Kept the displayed dice and hit requirement synchronized with the selected NPO weapon profile used to roll the attack.
- Preserved existing defense summaries and all combat resolution, damage, wound, and saved-game behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.8.

## v5.7.7

**Version 5.7.7 - Shooting Attack Profile Summary**

- Added an Attack card to the Resolve Shooting Attack screen using the selected weapon's attack dice and hit characteristics.
- Positioned the Attack card immediately before Defense while preserving the existing responsive combat profile layout.
- Preserved all combat resolution, damage, wound, and saved-game behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.7.

## v5.7.6

**Version 5.7.6 - Simplified NPO Activation Screen**

- Removed redundant initiative messaging from the NPO Activation screen.
- Updated the instruction to focus on identifying the next ready NPO using the Threat Principle.
- Preserved the existing NPO activation workflow and gameplay logic.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.6.

## v5.7.5

**Version 5.7.5 - Dormant and Deployed NPO State**

- Separates battlefield presence from dormancy when creating, loading, and deploying NPOs.
- Limits NPO activation to deployed, Ready, awakened operatives and removes contradictory dormancy prompts.
- Keeps Reserve NPOs non-dormant and applies the current Threat state when reinforcements deploy.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.5.

## v5.7.4

**Version 5.7.4 - Mobile Strategy Phase Tooltips**

- Removed Strategy Phase stat tooltips and their info indicators on mobile while preserving desktop tooltip behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.4.

## v5.7.3

**Version 5.7.3 - Strategy Phase Reinforcement Reporting**

- Lists the exact Reserve NPOs entering play and marks them Deployed when reinforcements are generated.
- Reports battlefield-limit blocks separately while leaving those NPOs in Reserve.
- Replaces the floating reinforcement tooltip with a compact, in-flow card that is hidden when empty.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.3.

A separate, mobile-first guided-play application for solo Kill Team missions in a Necron tomb world. This project does not replace Tomb World Solo Command.


## v5.7.2

**Version 5.7.2 - Simplified Strategy Phase**

- Removed the obsolete Strategy Phase step indicator and closing instruction.
- Hidden empty reinforcement and Tomb World Event result sections.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.2.

## v5.7.1

**Version 5.7.1 - Compact Deployment Rosters**

- Consolidated each selected roster into its corresponding deployment confirmation card.
- Removed redundant deployment summary and confirmation cards and tightened deployment spacing.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.1.

## v5.7.0

**Version 5.7.0 - Battlefield NPO States**

- Automatically selects and persists the specific starting NPOs deployed from the available roster.
- Tracks reserve, deployed, and out-of-action NPOs and filters battlefield activation and Player targeting accordingly.
- Uses matching reserve NPOs for reinforcements before generating new roster entries.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.0.

## v5.6.1

**Version 5.6.1 - Deployment Mission Roll**

- Integrated the persisted starting NPO mission roll and shared dice animation into Deploy Kill Teams.
- Replaced the manual roll checklist wording with dynamic deployment instructions, including capped-pool transparency.
- Removed the redundant Starting NPO Generation setup step and updated setup progress.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.6.1.

## v5.6.0

**Version 5.6.0 - Starting NPO Generation Animation**

- Presents the mission's starting NPO count as a shared animated dice roll.
- Shows the original mission calculation and caps deployment to the available NPO pool.
- Automatically continues to deployment while persisting the roll and one-time transition state.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.6.0.

## v5.5.3

**Version 5.5.3 - Aggressive Defense Construct Animation**

- Integrated the Macrocyte's D3 retaliation into the shared combat dice sequence.
- Stored the D3 outcome before animation so restored combat displays it without rerolling or replaying.
- Kept Continue disabled until the retaliation result settles and renders.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.5.3.

## v5.5.2

**Version 5.5.2 - Direct Initiative Activation**

- Removed the redundant automatic-initiative confirmation screen and its begin-side controls.
- Strategy completion now routes directly to the side selected by the resolved initiative result.
- Added a lightweight initiative status message to activation screens, including the Turning Point 1 Dormant NPO reminder.
- Preserved existing initiative rolls, Strategy processing, Tomb World events, reinforcements, activation alternation, and save compatibility.


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

## Local PWA testing

Service workers do not run when `index.html` is opened directly with a `file://` URL. From the repository root, start a local HTTP server with either:

```sh
python -m http.server 8000
```

or on Windows:

```sh
py -m http.server 8000
```

Then open `http://localhost:8000`. Load the app once while online so its local gameplay resources can be cached. Browser developer tools can then be used to switch the network offline and reload the page to verify offline operation. Service workers are supported on localhost for development and on the production HTTPS GitHub Pages URL.

## Automated testing

Run the focused rules-engine, mission, combat, event, reinforcement, and save-compatibility regression suite from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The Guide preserves the existing `tombWorldSoloGuide.v1` browser-storage key. Current, legacy, and partially upgraded saves are normalized on load; malformed optional fields fall back to safe defaults without clearing the stored game.

### Installing the app

- **iPhone or iPad:** Open the production site in Safari, tap **Share**, then **Add to Home Screen**.
- **Android or supported desktop browser:** Open the browser's install prompt or menu and choose **Install app** or **Add to Home screen**.

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

- `index.html`, `app.js`, `styles.css`, `service-worker.js`, and `manifest.webmanifest` must remain at the repository root.
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
- After saves are rolled, the final action is `Apply Damage & Complete Activation`, or `Complete Activation` when no damage was inflicted.
- Canceling the save workflow returns to the resolved NPO attack step without applying damage, completing the activation, or rerolling the original attack dice.
- The obsolete `Review NPO Attack` action remains removed.


## v2.2.4

- The non-collapsible `NPO Attack Summary` remains available on the Recommended Activation screen for flows that have not completed through the final Player Save Roll action.
- The summary shows the targeted Player operative, Player save roll, unsaved normal and critical hits, damage, and wounds before and after.
- The Player save roll now appears immediately after the NPO attack roll.
- Resolving the final Player Save Roll applies any wounds and completes the NPO activation in one action instead of returning to the NPO Attack Summary screen.
- Completing the final Player Save Roll advances directly to the next game-flow screen; it does not return to the attack summary solely to complete the activation.
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

## v3.2.6

- Allowed Kill Teams to define minimum and maximum roster sizes while preserving exact-size behavior for existing team data.
- Updated the Death Korps roster builder to accept between 11 and 14 operatives.
- Updated visible, internal, and cache-busting versions to v3.2.6.


## v3.3.0

- Organized Player Roster Selection into data-driven, collapsible operative categories with selected counts.
- Added roster category metadata and operative category membership to every supported Player Kill Team.
- Preserved existing roster validation, duplicate operative naming, and setup navigation behavior.
- Updated visible, internal, and cache-busting versions to v3.3.0.

## v3.3.1

- Presented Player Roster rules as an accessible checklist with immediate satisfied and incomplete states.
- Kept maximum-only requirements satisfied below their limits and placed the overall roster total last.
- Expanded all roster categories when the screen first opens while preserving user toggles as selections change.
- Updated visible, internal, and cache-busting versions to v3.3.1.

## v3.3.2

- Corrected minimum roster requirements so Gravis remains incomplete until one is selected.
- Removed status icons from roster requirements and clarified the overall Total Required line.
- Collapsed all roster categories by default while preserving independent expansion state during setup.
- Updated visible, internal, and cache-busting versions to v3.3.2.

## v3.3.3

- Kept New Game Setup navigation visible in a safe-area-aware mobile footer while setup content scrolls.
- Preserved the existing desktop setup layout and all setup button labels, states, and behavior.
- Updated visible, internal, and cache-busting versions to v3.3.3.

## v3.3.4

- Targeted the existing New Game Setup wizard structure directly for mobile footer positioning and content clearance.
- Removed the unnecessary setup-only wrapper class while preserving setup navigation behavior and desktop layout.
- Updated visible, internal, and cache-busting versions to v3.3.4.

## v3.3.5

- Simplified Roster Requirements into a neutrally styled reference while preserving dynamic requirement text and roster validation.
- Removed obsolete completed and incomplete visual states from requirement rows.
- Updated visible, internal, and cache-busting versions to v3.3.5.

## v3.3.6

- Clarified roster requirement labels for leaders, required categories, maximum-only categories, and overall operative totals.
- Preserved neutral requirement styling and existing roster validation behavior.
- Updated visible, internal, and cache-busting versions to v3.3.6.

## v3.3.7

- Automatically selected required roster categories when their eligible operatives exactly match the required count.
- Left maximum-only categories and required categories with multiple choices unselected.
- Updated visible, internal, and cache-busting versions to v3.3.7.

## v3.4.0

- Added installable Progressive Web App metadata using the existing SVG icon.
- Added versioned offline caching for the app shell, missions, Kill Teams, operatives, maps, images, and local reference PDF.
- Added a non-blocking update notice; a waiting update activates and reloads only after **Update App** is pressed.
- Added localhost service-worker and offline test instructions.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.4.0.

## v3.4.1

- Treated HTTP error responses as network failures so cached navigation and data remain available during transient server or captive-network errors.
- Limited the app-shell fallback to navigation requests while preserving exact cached fallbacks for JavaScript, CSS, JSON, and manifest requests.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.4.1.

## v3.4.2

- Included every required Leader in the Roster Requirements summary, including automatically selected Leaders.
- Alphabetized operative section headers while preserving the operative order within each section.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.4.2.

## v3.4.3

- Required category-based Leaders, including the Deathwatch Sergeant, for roster validation as well as the Roster Requirements summary.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.4.3.

## v3.5.1

- Redesigned the NPO Activation questions as an icon-led active card with compact answered-question history.
- Kept the active question in a consistent position with reduced-motion-aware modal scrolling and preserved Back behavior.
- Presented the determined action in a distinct result card without exposing the underlying decision path.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.1.

## v3.5.2

- Combined the NPO action recommendation and target priority into one compact Activation Plan card.
- Shortened the target-selection placeholder while preserving the existing selection and confirmation flow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.2.

## v3.5.3

- Removed the pre-roll informational card from the Roll Player Saves screen while preserving the defense profile, cover control, and post-roll results.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.3.

## v3.5.4

- Simplified the NPO Activation heading and removed the redundant next-step information card.
- Kept operative names readable on one line at iPhone portrait widths and tightened the spacing before the activation button.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.4.

## v3.5.5

- Removed the redundant Recommended Activation label and Engage status badge from the NPO Activation recommendation screen.
- Tightened the operative heading spacing while preserving the Activation Plan, targeting, and activation workflow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.5.

## v3.5.6

- Swapped the NPO Activation wizard navigation so Back appears on the left and Exit Guide appears on the right.
- Replaced the control-range icon with a radar sweep and refined the Charge icon's movement curve and target approach.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.6.

## v3.5.7

- Replaced the NPO Activation hatch question icon with a reinforced, front-facing hatch and locking wheel that remains clear in active and answered states.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.7.

## v3.5.8

- Replaced the NPO Activation control-range icon with a detailed tactical radar display that remains clear in active and answered states.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.8.

## v3.5.9

- Made every SVG icon inherit the muted question text color after its question is answered while keeping active-question icons green.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.5.9.

## v3.6.0

- Replaced the NPO Activation Charge question icon with two operative markers and an edge-to-edge directional Charge arrow that remains clear in active and answered states.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.6.0.

## v3.7.0

- Added a persistent inline Strategy Phase action for A Chittering Drone, allowing one eligible Scarab Swarm to be fully healed or one new swarm to be added within the battlefield limit.
- Added direct NPO Roster access without changing the current Strategy Phase results.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.7.0.

## v3.7.1

- Migrated legacy saved Strategy Phase event arrays to their stable event definitions so in-progress A Chittering Drone events expose the inline roster action after updating.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.7.1.

## v3.8.0

- Redesigned every Tomb World Event card with green hazard stripes, the anomaly icon, a permanent event header, and a clearer title-and-effect hierarchy.
- Preserved inline event actions inside the redesigned card and added semantic event metadata without changing event generation or resolution behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.0.

## v3.8.1

- Hid the Add Scarab Swarm button when the battlefield NPO limit makes that event option unavailable.
- Kept the existing explanation and NPO Roster access visible so players can understand or resolve the blocked event.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.1.

## v3.8.2

- Indented and bulleted the contextual messages displayed below Tomb World event descriptions.
- Hid the NPO Roster button when an event has no valid roster change available.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.2.

## v3.8.3

- Hid the reinforcement entry-point control when the battlefield NPO limit prevents adding more reinforcements.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.3.

## v3.8.4

- Kept the reinforcement entry-point control available when a successful reinforcement fills the final battlefield slot.
- Continued hiding the control when no reinforcements arrive.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.4.

## v3.8.5

- Made the Strategy Phase reinforcement summary, generated results, entry-point controls, and placement count use the reinforcement total remaining after the battlefield limit is applied.
- Kept the battlefield-limit explanation visible when some or all reinforcements are blocked.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.5.

## v3.8.6

- Preserved successfully created reinforcements when loading legacy Strategy Phase saves that also recorded blocked arrivals.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.6.

## v3.8.7

- Generalized the elimination banner and attack summary so newly eliminated Player and NPO operatives share the same presentation.
- Added Player elimination feedback to completed NPO attacks, including the operative name, attack type, damage, wounds, eliminated badge, and action summary.
- Kept the final Player casualty summary visible until the NPO activation is completed, then transitioned to the defeat screen.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.7.

## v3.8.8

- Automatically selected the Player operative when only one eligible operative remains and displayed its name in the existing read-only selection control.
- Preserved the existing unselected dropdown when multiple Player operatives remain eligible and the existing Turning Point progression when none remain.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.8.

## v3.8.9

- Removed the iOS/WebKit tap highlight from custom decision and action buttons while preserving a visible keyboard focus indicator.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.9.

## v3.8.10

- Combined the final Player Save Roll action so it applies any damage and completes the NPO activation without returning to the NPO Attack Summary screen.
- Preserved Player elimination feedback after the activation completes and retained the original NPO attack roll when the save wizard is cancelled.
- Prevented repeated final-action taps from applying damage or completing the activation more than once.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.10.

## v3.8.11

- Restored the Roll Player Saves action after cancelling the NPO Attack Wizard while retaining the original target and attack dice.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.11.

## v3.8.12

- Preserved the Player elimination and wounds-before/after confirmation when an NPO attack eliminates the final living Player operative, before continuing to the defeat screen.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.12.

## v3.8.13

- Suppressed custom decision and action button focus rings on coarse-pointer touch devices while retaining their existing pressed, active, disabled, and hover states.
- Preserved the visible custom button focus indicator for keyboard navigation on fine-pointer devices without changing native form control focus treatment.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.13.

## v3.8.14

- Removed the redundant `Next: Player` / `Next: NPO` badge from the Activation Tracker because the primary activation card already identifies the current side.
- Preserved the completed activation count, compact tracker header, and expand/collapse control.
- Updated visible, internal, cache-busting, and service-worker cache versions to v3.8.14.


## v4.0.0

- Unified Player Shoot, Player Melee, NPO Shoot, and NPO Melee resolution around one shared combat engine and summary layout.
- Presented attack dice, save dice, retained saves, unsaved hits, damage, wounds, and elimination status together on one combat screen.
- Removed the separate NPO save and post-attack summary steps so NPO combat now completes its activation directly from combat resolution.
- Preserved selected targets and rolled combat dice when canceling and returning to combat.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.0.0.

## v4.0.1

- Removed the redundant pre-roll instruction from the Player attack dialog to reduce unnecessary vertical space.
- Preserved the target-selection prompt when multiple NPO targets are available and none is selected.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.0.1.


## v4.0.2

- Added official mission-specific tabletop setup confirmations for all six missions, including deployment, marker, room-allocation, and starting Conceal-order requirements.
- Clarified that complete kill-team roster legality and cooperative team splitting are outside the Guide’s validation scope.
- Delegated the initial 2CP and up-to-four equipment choices to recorded tabletop play without adding resource engines.
- Migrated setup confirmations to stable mission checklist IDs while preserving existing saved games and Turning Point 1 behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.0.2.


## v4.0.3

- Kept map, terrain, marker, and deployment-area confirmations in the killzone step.
- Moved operative placement, starting Conceal orders, and initial-resource confirmations after Player and NPO roster generation.
- Reset placement confirmations whenever the starting NPO roster is regenerated.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.0.3.

## v4.1.0

- Added one canonical source for all official Tomb World NPO characteristics, weapons, abilities, and printed behavior data.
- Corrected setup and reinforcement generation to consume the same official 2D6 table, including total 12 and printed weapon variants.
- Stored generated NPO weapon identities and starting Conceal orders, with automatic normalization for legacy saved rosters.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.1.0.

## v4.1.1

- Corrected the official NPO generation boundary so a 2D6 total of 10 generates a Necron Warrior and only total 11 generates a twin-gauss Tomb Crawler.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.1.1.


## v4.2.0

- Refactored Strategy processing into ordered Ready, mission hook, initiative, event, and reinforcement stages while preserving the existing two-step Strategy UI.
- Moved Mission 4 Nanoscarab Repair into the Ready step and recorded its result in persisted Strategy data.
- Added persisted Dormant NPO state, Threat 0 Expended behavior, normal readiness restoration when Threat rises, and automatic Player initiative during Turning Point 1 and at Threat 0.
- Clamped malformed imported Threat values and migrated legacy saves with the new Strategy and Dormant fields.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.2.0.


## v4.3.0

- Implemented Remediation Plan PR 4 with the official per-operative NPO behavior lists and first-legal-action question order.
- Replaced heuristic activation and target selection with the Threat Principle and action-specific printed priorities while retaining manual tabletop geometry.
- Staged NPO recommendations so exiting the guide consumes nothing; readiness, activation progress, history, and Threat commit only when the activation is completed.
- Removed invented behavior labels from the NPO activation workflow and continued using the canonical NPO definitions introduced in v4.1.0.
- Preserved the existing mobile activation dialogs and intentionally deferred combat, weapon, reinforcement, event, and mission-engine changes.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.3.0.


## v4.4.0

- Implemented Remediation PR 5 with the complete physical Tomb World Event deck, duplicate card weighting, official draw timing, and draw-without-replacement lifecycle.
- Integrated queued event execution into the existing Strategy pipeline before reinforcements, including tabletop confirmations and printed redraw conditions.
- Persisted the event deck, used cards, active effects, duration, and resolution metadata with backward-compatible save normalization.
- Added focused event-engine regression coverage and preserved the existing mobile-first inline event-card workflow.
- Intentionally deferred reinforcements, combat changes, and mission objective logic to later remediation PRs.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.4.0.


## v4.4.1

- Kept ongoing Tomb World event effects visible throughout the remainder of their Turning Point.
- Corrected impossible-event redraw ordering so replacement cards resolve before later pre-drawn cards.
- Added the printed D3 result and impossible-effect redraw control for The Maze Reforms.
- Required selection when A Chittering Drone finds multiple wounded Scarab Swarms, while preserving its mandatory heal branch.
- Normalized legacy in-progress event queues without invalidating existing saves.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.4.1.


## v4.5.0

- Implemented official Grade-sized NPO reinforcements after Tomb World events in the Strategy pipeline.
- Reused the canonical NPO generation table so reinforced operatives retain their official weapon variant and Conceal order.
- Added persisted, per-operative tabletop placement confirmation before reinforced operatives are marked deployed.
- Preserved the supported 10-NPO limit and clearly reports reinforcements that cannot be set up.
- Migrated legacy saves with default reinforcement state without invalidating existing games.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.5.0.


## v4.5.1

- Recalculated the current Grade after Tomb World events so reinforcement quantity uses the resulting Threat level.
- Invalidated placement confirmation whenever its recorded random hatchway changes and rejected confirmation without a hatchway.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.5.1.


## v4.6.0

- Implemented the combat remediation release as a tabletop-first rules assistant: players physically roll and resolve retained successes, then record damage and incapacitation.
- Reused canonical NPO weapon definitions for ranged and melee profile selection, including multi-profile weapons and printed profile guidance.
- Added ordered Shooting and Fight guidance, printed weapon-rule reminders, Dimensional Banishment and Aggressive Defence Construct follow-up prompts, and persisted combat drafts with legacy-save normalization.
- Preserved the existing combat dialogs, transactional activation workflow, mobile-first layout, and intentionally deferred mission victory, post-game, and campaign logic.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.6.0.


## v4.6.1

- Validated imported combat drafts, cleared canceled Player combat transactions, and corrected recorded-success labels.
- Resolved Dimensional Banishment from a recorded physical 2D6 result and applied Aggressive Defence Construct damage transactionally from its recorded D3 result.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.6.1.


## v4.7.0

- Replaced the retained-success plus/minus counters in Player Shooting and Melee resolution with the Guide's animated dice roller.
- Added an attack-first, defense-second roll sequence with tappable dice; players still choose which normal and critical successes to retain under the Core Rules.
- Automatically totals retained normal and critical attack successes while preserving the existing recorded-damage and transactional activation flow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.7.0.


## v4.7.1

- Removed the visible retained normal and critical success panels from the Player Attack Dice and Defense Dice sections.
- Automatically derives retained successes from selected dice, applies defense cancellations, and recalculates weapon damage while preserving manual damage adjustment.
- Preserved weapon profile rules, selectable dice, pending combat transactions, and the existing mobile-first resolver flow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.7.1.


## v4.8.0

- Replaced the generic mission tracker with persisted, mission-specific objective state and guided tabletop prompts for all six Tomb World missions.
- Implemented each mission’s official progression timing and binary victory or defeat conditions, including end-of-Turning-Point evaluation for Regroup.
- Preserved completed mission state and the existing Victory/Defeat artwork so outcomes can be reviewed without an automatic reset.
- Added legacy tracker migration and synchronized visible, internal, cache-busting, and service-worker cache versions to v4.8.0.


## v4.8.1

- Corrected mission progression boundaries for Escape, Transponder carriage, Scout Sub-Crypt awakening, and Regroup end-of-Turning-Point checks.
- Required Auspex Calibration before Strategy progression when applicable and suppressed Mission 5 Operate Hatch Threat increases.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.8.1.


## v4.9.0

- Consolidated save validation around shared record, integer, and identifier-list normalizers.
- Hardened current, legacy, partially upgraded, and malformed saves without changing the existing storage key or clearing browser data.
- Added defensive recovery for invalid Turning Point, Threat, NPO, event, reinforcement, combat, and mission state.
- Expanded focused regression coverage and documented the dependency-free test command.
- Updated visible, internal, cache-busting, and service-worker cache versions to v4.9.0.


## v5.5.1

**Version 5.5.1 - Shared Combat Review Fixes**

- Prevented stale defense-settlement callbacks after an automatic combat roll is cancelled or restarted.
- Removed the duplicate participant summary from final results on the shared Combat Resolution screen.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.5.1.

## v5.5.0

**Version 5.5.0 - Shared Combat Resolution**

- Routed Player and NPO attacks through one dedicated Combat Resolution screen and shared result renderer.
- Kept Continue disabled through attack, defense, settlement, and Aggressive Defense Construct animations while restoring resolved combats immediately.
- Preserved transactional damage application and direct return to the activation workflow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.5.0.

## v5.4.1

**Version 5.4.1 - Combat Animation Settlement Fix**

- Settled the sequential Defense dice animation before rendering the final Player combat result.
- Removed the duplicate simultaneous dice animation that previously ran after attack and Defense dice had already animated.
- Kept Continue disabled until shared dice settlement completes, while restored results remain immediately reviewable.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.4.1.

## v5.4.0

**Version 5.4.0 - Dedicated Player Combat Resolution**

- Moved Player shooting and melee dice animation to one compact, dedicated combat-resolution screen.
- Removed the obsolete Shooting Sequence and Fight Sequence panels and the redundant Player activation confirmation summary.
- Continued directly through the activation flow after combat review while preserving transactional, exactly-once damage and restored combat results.
- Kept Continue disabled until all new dice animations settle and preserved immediate continuation for restored results.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.4.0.

## v5.3.2

**Version 5.3.2 - Melee Workflow Cleanup**

- Removed the redundant Skip Melee action from automated Player melee resolution.
- Kept Cancel as the path for revising a selected Melee action and Continue as the path for accepting its automated result.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.3.2.

## v5.3.1

**Version 5.3.1 - Combat Animation Guard**

- Prevented the combat continuation handler from advancing until animated dice are visually complete, even if the handler is invoked directly.
- Cancelled the shared automatic dice timers when a Player skips a pending melee attack.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.3.1.

## v5.3.0

**Version 5.3.0 - Unified Player Combat Resolution**

- Unified Player shooting and melee attacks on the shared automatic attack-then-defense dice workflow and combat result layout.
- Kept Continue disabled for newly animated results until the final dice faces have visually settled, while restored results remain immediately available.
- Removed manual melee dice retention and damage bookkeeping without changing combat calculations or transactional wound application.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.3.0.

## v5.2.1

**Version 5.2.1 - Player Combat Continue Fix**

- Enabled Continue once an automatically resolved Player shooting result has been recorded, while retaining the disabled state during dice rolls.
- Preserved restored combat results, cancellation, and single-application wound handling.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.2.1.

## v5.2.0

**Version 5.2.0 - Automatic Player Shooting Resolution**

- Player shooting now uses the shared automatic attack-then-defense dice animation and combat resolution path used by NPO attacks.
- Shooting rolls, retained successes, damage, wounds, and incapacitation are persisted as one result and restored without rerolling or duplicate application.
- Removed manual Player shooting dice and outcome bookkeeping while preserving the existing Player melee workflow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.2.0.

## v5.1.0

**Version 5.1.0 - Automatic NPO Combat Resolution**

- Automatically rolls and animates NPO attack dice followed by Player defense dice.
- Automatically retains successes, resolves saves, and calculates damage without editable counters.
- Automatically rolls Aggressive Defense Construct when it triggers.
- Preserves persisted combat results and the existing combat wizard workflow.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.1.0.

## v5.0.1

**Version 5.0.1 - Aggressive Defense Construct Dice Roll**

- Replaced the manual Aggressive Defense Construct D3 entry with the existing animated dice experience.
- Automatically records and reports the D3 outcome, then applies any resulting damage when the Player activation is confirmed.
- Updated application UI terminology from “Defence” to “Defense.”
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.0.1.

## v5.0.0

**Version 5.0.0 - Official Rules Compliant Release**

- Updated application UI terminology from Player A and Player B to Player and NPO.
- Added Random Team generation for legal, editable Player rosters.
- Added Check All to streamline Kill Team deployment confirmation.
- Preserved the gameplay and official-rules behavior completed during remediation.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.0.0.
