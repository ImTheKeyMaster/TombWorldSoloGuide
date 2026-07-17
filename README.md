# Tomb World Solo Guide v1.1.6

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
