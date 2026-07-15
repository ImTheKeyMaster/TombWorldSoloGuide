# Tomb World Solo Guide v1.1.6

A separate, mobile-first guided-play application for solo Kill Team missions in a Necron tomb world. This project does not replace Tomb World Solo Command.

## v1.1.6 additions

- Mission maps now scroll horizontally on portrait phones without widening the page.
- Added a swipe hint and visible horizontal scrollbar on mobile.
- Desktop maps still scale to the available width.


- Two-step guided Strategy Phase
- Automatic Turning Point preparation
- Threat meter with grade labels and manual correction controls
- Automatic NPO readying and Enemy reset
- Mission-aware reinforcement generation after Turning Point 1
- Visual 2D6 reinforcement rolls with pip dice
- Ten-NPO battlefield limit handling
- Reinforcement entry-point recording
- Grade 3 Tomb World event checks and supported automatic effects
- Guided initiative rolls, rerolls, and manual override
- Persistent activation tracker for Enemy operatives and individual NPOs
- Automatic alternation between Enemy and NPO activations
- Automatic transition to end-of-Turning-Point scoring
- Backward-compatible migration of v1 saved games

## Existing v1 foundation

- New Game setup wizard
- Six mission briefings and schematic board layouts
- Mission-specific starting NPO roster generation
- Guided NPO and Enemy deployment
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

- Guided Enemy attack wizard targeting an NPO
- Guided NPO attack save and damage wizard
- Visual attack and save dice with pips
- Critical and normal save cancellation
- AP, cover retention, configurable defense dice, saves, and damage profiles
- Damage preview before confirmation
- Confirmed Enemy damage automatically updates NPO wounds
- NPO damage is recorded for application to the Enemy operative on the tabletop


## v1.3.1 Guided-flow refinements

- `Begin Turning Point 1` now proceeds directly into Turning Point preparation and initiative.
- Removed the redundant intermediate `Start Turning Point 1` screen from initial setup.
- Added Move, Dash, Charge, Fall Back, Mission Action, and Pass options to Enemy activation recording.
- Movement actions are recorded without changing Threat.
- Completing an activation with no selected actions now requires explicit confirmation.
- Enemy activation history and Journal entries now summarize the recorded actions.


## v1.3.2 Enemy activation combat flow

- Grouped Enemy activation actions into Movement, Combat, Battlefield, and Pass sections.
- Renamed the Fight-facing UI to Melee while retaining the underlying Kill Team Fight action meaning.
- Checking Shoot reveals Resolve Shooting Attack.
- Checking Melee reveals Resolve Melee Attack.
- Removed the separate Did the Enemy attack an NPO section.
- Shooting and Melee attacks can be resolved independently in the same activation.


## v1.3.3 Setup and combat safeguards

- Attack Wizard target selection now starts blank.
- All attack profile controls remain disabled until a Target NPO is selected.
- Added **Check All** to the Build the Killzone setup step.
- Added **Place All** to the Deploy NPOs setup step.
- Enemy activations cannot be completed while Shoot or Melee is checked but unresolved.
- Players can either resolve the checked attack or return and uncheck the action.


## v1.3.4 Guided navigation cleanup

- Removed the permanent bottom navigation bar.
- Added a single **Game Menu** button to the header during an active game.
- Mission, Roster, Journal, and Help are now optional reference screens and do not alter the current guided-play state.
- Added **Return to Guided Play** at the top of every reference screen.
- Added an always-available **Start New Game** command to the Game Menu.
- Export and Import Save are also available from the Game Menu.
- Removed duplicate session controls from the Mission reference screen.
