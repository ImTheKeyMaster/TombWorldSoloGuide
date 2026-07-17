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
