# Tomb World Solo Guide v8.6.94

## v8.6.94

**Version 8.6.94 - Reliable iOS Narration and Honest Volume Controls**

- Restores narration priming directly from mission selection so iPhone/PWA Mission Intro playback does not require a speaker cycle or unrelated follow-up click.
- Keeps the desktop master-volume slider while replacing it on iPhone and iPad with device-volume guidance, preserving the stored desktop preference.
- Avoids ineffective production-media volume writes and ambient volume ramps on iOS while preserving HTML audio playback, master mute/unmute, offline caching, and save schema version 3.

## v8.6.93

**Version 8.6.93 - Persistent Master Volume**

- Adds a compact, accessible master-volume slider to the Game Menu with live narration and ambient level adjustment.
- Preserves the last non-muted volume independently from the header speaker mute state and restores it across reloads, PWA relaunches, and New Game.
- Scales narration and configured ambient normal/duck levels without restarting media, changing playback position, or changing category settings; save schema remains version 3.

## v8.6.92

**Version 8.6.92 - Reliable iOS Ambient Audio**

- Replaces the ambient Web Audio state machine with one persistent, preloaded HTML audio element using the configured `Ambient/caverns.ogg` source.
- Starts or resumes eligible ambient playback directly from speaker and mission-selection gestures, with temporary retry handling for iPhone/PWA playback restrictions.
- Preserves settings-only menu toggles, narration ducking, smooth master fades, playback position across master mute, offline caching, narration isolation, and save schema version 3.

## v8.6.91

**Version 8.6.91 - Event-Driven Audio Lifecycle**

- Centralizes live audio activation on the master speaker, mission selection, and explicitly armed one-time browser recovery gestures; ordinary UI interaction and rendering remain audio-neutral.
- Isolates Safari narration priming in a dedicated unlock-only audio element so Game Menu and other controls cannot replace, pause, reload, or invalidate production narration.
- Restores selected ambient audio directly from the speaker gesture after master audio is re-enabled while preserving the caverns loop, configured gains, narration ducking, and save schema version 3.

## v8.6.90

**Version 8.6.90 - iOS Ambient Foreground Recovery**

- Re-primes the ambient audio session on the next valid gesture after foregrounding, including when iOS incorrectly reports its interrupted audio context as running.
- Replaces the stale ambient loop with exactly one fresh source while preserving master audio, Ambient, Narration, ducking, and save preferences.
- Keeps failed WebKit recovery attempts bounded and eligible for another user-gesture retry.

## v8.6.89

**Version 8.6.89 - Reliable Master Audio Re-enable**

- Freshly primes selected narration whenever the master speaker is re-enabled, while leaving failed attempts retryable.
- Starts required narration and ambient unlock attempts together from the master-speaker gesture without changing settings-only behavior.
- Recovers suspended or interrupted ambient audio contexts and adds lightweight PWA visibility recovery while preserving `Ambient/caverns.ogg`, narration ducking, and save schema version 3.

## v8.6.88

**Version 8.6.88 - Independent Audio Settings and Master Control**

- Separates the sticky Narration and Ambient Noise settings from the header speaker's independently persisted master audio state.
- Applies the latest stored category settings only when master audio is enabled, so changing either Game Menu switch never disturbs live playback.
- Preserves ambient looping, narration ducking, one-time Safari/PWA audio unlock behavior, New Game preference persistence, and save schema version 3.

## v8.6.87

**Version 8.6.87 - Narration Menu Toggle**

- Replaces the Game Menu audio button with a Narration switch matching the existing Ambient Noise control.
- Preserves the existing narration and ambient master-control behavior while displaying the current Narration On/Off state.

## v8.6.86

**Version 8.6.86 - Reliable Ambient Playback and Persistent Control**

- Makes ambient initialization failures retryable and keeps Safari/iPhone/PWA audio permission separate from successful configuration and audio decoding.
- Adds a persistent, accessible Ambient Noise switch to the Game Menu while retaining Game Audio as the narration-and-ambient master control.
- Keeps `Ambient/caverns.ogg` config-driven and offline precached, with seamless looping, narration ducking, and uninterrupted playback across ordinary UI interaction.

## v8.6.85

**Version 8.6.85 - Uninterrupted Ambient Audio**

- Makes ambient unlock, active-state updates, and playback reconciliation idempotent so ordinary UI interaction, renders, and navigation do not disturb an already-playing ambient source or its gain.
- Retains a one-time Safari/iPhone/PWA gesture fallback that removes itself after successful audio permission, while preserving narration ducking, Game Audio transitions, New Game cleanup, and save schema version 3.

## v8.6.84

**Version 8.6.84 - Remove UI Click Audio**

- Removes button and dropdown click sound playback, configuration, and offline precaching.
- Keeps buttons and dropdowns functional while preserving narration, ambient audio, ducking, Game Audio controls, and save schema version 3.

## v8.6.83

**Version 8.6.83 - Dropdown Click Audio**

- Reduces the button click sound gain to `0.0875`, half of its previous level.
- Plays the same click sound once when an enabled native dropdown selection changes, including dynamically rendered selects.
- Keeps button and dropdown SFX under the Game Audio master control without affecting narration, ambient playback, ducking, or save schema version 3.

## v8.6.82

**Version 8.6.82 - Refresh Button Click Audio Cache**

- Bumps only the application and cache versions so clients, including iPhone/PWA installs, fetch the replaced button click audio file.
- Preserves gameplay, SFX behavior, narration, ambient audio, styling, and save schema version 3.

## v8.6.81

**Version 8.6.81 - Quieter Button Clicks**

- Reduces the global button click sound gain by 50% for less intrusive UI feedback.
- Updates visible, internal, cache-busting, and service-worker cache versions to v8.6.81.

## v8.6.80

**Version 8.6.80 - Add Global Button Click Sound**

- Adds a low-latency, configuration-driven click sound to every enabled HTML button through one delegated handler, including dynamically rendered controls.
- Keeps button SFX under the existing Game Audio master control without interrupting narration, ambient playback, or ambient ducking.
- Precaches the validated SFX configuration and selected WAV for offline/PWA use while preserving save schema version 3.

## v8.6.79

**Version 8.6.79 - Refine Wounded Operative Border Color**

- Changes only the wounded operative status row border color to `#ffd35bb0`.
- Preserves wounded row backgrounds, text colors, wound indicators, dimensions, opacity, all other operative-status styling, and save schema version 3.

## v8.6.78

**Version 8.6.78 - Normalize Board Setup Checklist Highlighting**

- Removes the unintended required-confirmation emphasis from the breach-points Board Setup checklist item.
- Keeps every Board Setup checklist item on the normal check-row appearance without changing completion, Board Ready, persistence, or navigation behavior.
- Preserves emphasized required confirmations in tabletop and end-of-turn confirmation flows, along with save schema version 3.

## v8.6.77

**Version 8.6.77 - Consistent Game Audio Toggle**

- Routes both speaker controls through the same start and stop behavior for ambient audio and narration.
- Avoids restarting pending narration when existing narration successfully resumes.

## v8.6.76

**Version 8.6.76 - Unified Game Audio Menu Control**

- Replaced the undersized narration replay control with a full-width game-menu button and speaker icon.
- The control now starts or stops both ambient audio and narration, with a label that reflects the current playback setting.

## v8.6.75

**Version 8.6.75 - Seamless Ambient Audio and Narration Ducking**

- Adds a configuration-driven, seamless Web Audio ambient bed during mission setup and active battles, controlled by the existing master speaker and stopped by New Game.
- Automatically ducks and smoothly restores ambient gain around all centralized narration, including consecutive queues and narration preemption.
- Precaches the ambient configuration and its validated selected track for offline/PWA play while preserving narration caching and save schema version 3.

## v8.6.74

**Version 8.6.74 - Tomb Event Narration Timing**

- Defers accepted Tomb World Event narration until the Strategy Phase Events view containing the event is rendered and visible.
- Preserves gameplay order for consecutive accepted events while preventing rejected, redrawn, or previously requested event instances from being narrated.
- Preserves narration queuing and non-overlap, speaker pause/resume, Replay Last, New Game cancellation, Deadly Encounter narration, Safari audio unlock, mission intros, outcomes, and save schema version 3.

## v8.6.73

**Version 8.6.73 - Deadly Encounters Narration Runtime Support**

- Automatically narrates newly committed room and objective feature discoveries.
- Plays both real features resolved by an Unusual result sequentially in determination order, without replaying duplicate discoveries.
- Advances the app cache so all available Deadly Encounters narration is precached through the existing manifest-driven service worker flow.
- Preserves narration controls, event/mission/outcome behavior, Safari audio unlock priming, and save schema version 3.

## v8.6.72

**Version 8.6.72 - Restore Narration Playback After New Game**

- Fixes a regression where starting a new game could invalidate the Safari/iPhone audio unlock and prevent narration from playing.
- Continues to destructively stop real active or paused narration when a new game is confirmed.
- Preserves Board Setup Mission Intro playback, speaker pause/resume, and the outlined speaker-with-X disabled icon.

## v8.6.71

**Version 8.6.71 - Correct Narration Icon State and New Game Audio Cleanup**

- Corrects the disabled narration control so it displays the outlined speaker with an X instead of the enabled wave icon.
- Stops and clears active or paused narration when a new game is actually started.
- Preserves speaker-toggle pause/resume behavior and the user's Narration On/Off preference.

## v8.6.70

**Version 8.6.70 - Refine Board Setup Narration Toggle Behavior**

- Starts a pending Mission Intro when narration is enabled after entering Board Setup with narration disabled.
- Preserves pause and resume from the same playback position when narration is toggled during playback.
- Refines the disabled header speaker to an outlined speaker with an X replacing the sound waves.

## v8.6.69

**Version 8.6.69 - Restore Mission Narration and Refine Speaker State**

- Restores Mission Intro playback when Board Setup appears after advancing from Mission Selection.
- Guarantees narration defaults to On when no preference has ever been stored, while preserving explicit On/Off choices.
- Replaces the disabled speaker graphic with an outlined speaker and a clear X.

## v8.6.68

**Version 8.6.68 - Simplified Narration Playback Control**

- Simplifies the header speaker to a direct Narration On/Off toggle.
- Pauses active narration when turned off and resumes from the same position when turned back on.
- Removes narration volume controls and relies on physical device/system volume.
- Removes duplicate Narration controls from the Game Menu while preserving persistent On/Off state.

## v8.6.67

**Version 8.6.67 - Header Narration Volume Control**

- Adds a persistent speaker control to the application header.
- Adds quick narration enable/disable control and a dropdown volume slider.
- Preserves narration enabled state and volume across reloads, PWA restarts, and application updates.


## v8.6.66

**Version 8.6.66 - Complete Production Mission Intro Narration**

- Adds production Mission Intro narration for Mission 04: Destroy the Sarcophagus.
- Completes production narration coverage for all six mission intros.
- Preserves existing narration behavior and save compatibility.


## v8.6.65

**Version 8.6.65 - Complete Production Mission Outcome Narration**

- Adds the remaining production Mission Outcome narration for Missions 01, 02, 03, 05, and 06.
- Adds Victory and Defeat narration for each mission, for 10 new outcome clips total.
- Preserves existing narration behavior and save compatibility.


## v8.6.64

**Version 8.6.64 - Consecutive Tomb Event Narration Queue**

- Queues consecutive automatic Tomb Event narration so every event plays in order without overlap.
- Clears pending Tomb Event narration when mission narration or Replay Last preempts playback.
- Preserves the v8.6.63 production Tomb Event audio, manifest-driven offline caching, and save compatibility.

## v8.6.63

**Version 8.6.63 - Add Production Tomb Event Narration**

- Adds production narration for the remaining nine Tomb Events.
- Completes narrated coverage for all Tomb Events.
- Preserves manifest-driven offline narration caching.

## v8.6.62

**Version 8.6.62 - Add Production Mission Intro Narration**

- Adds production narration for Mission 02, Mission 03, Mission 05, and Mission 06 introductions.
- Expands mission briefing narration while preserving manifest-driven offline audio caching.

## v8.6.61

**Version 8.6.61 - Prepare Narration Pipeline for Full Production Rollout**

- Adds manifest-driven offline caching for every available narration recording.
- Adds production-scale narration validation and approved-entry selection in the local Producer.

## v8.6.60

**Version 8.6.60 - Improve Mission Narration Timing**

- Mission narration now begins while viewing the mission map during board setup.
- Narration stops when returning to mission selection, ready to restart for the next selected mission.
- Simplifies the Game Menu terminology to “Narration”.

## v8.6.59

**Version 8.6.59 - Add Dungeon Master Narration Pilot Audio**

- Adds five Dungeon Master Narration pilot recordings and activates their manifest metadata.
- Uses the selected Tomb World Narrator voice for the pilot recordings.

## v8.6.58

**Version 8.6.58 - Add Windows Narration Producer**

- Adds a secure, localhost-only Windows Narration Producer with dry-run, approval, and explicit generation safeguards.
- Restores the canonical reviewed narration scripts. This release does not add or generate any narration audio.

## v8.6.57

**Version 8.6.57 - Add Dungeon Master Narration Framework**

- Added optional, device-local narration preferences and compact Game Menu controls with replay support.
- Added semantic narration hooks for new mission introductions, accepted Tomb World Events, and successfully finalized mission outcomes without changing gameplay or save data.
- Added the 29-entry unavailable-audio manifest, approved production scripts, and offline-ready runtime structure; no narration audio or voice-service integration is included.

## v8.6.56

**Version 8.6.56 - Extend Required Confirmation Highlighting**

- Centralized the green required-confirmation treatment and limited it to unchecked confirmation rows.
- Extended the shared treatment to the end-of-turn completion and Breach Points setup confirmations.
- Preserved checkbox validation, button availability, layout, and save compatibility.

## v8.6.55

**Version 8.6.55 - Highlight Visibility Confirmation**

- Highlighted the required tabletop visibility and distance confirmation row with a green-tinted background and bright green border.
- Preserved the existing checkbox styling and behavior, operative selection row styling, combat flow, and save compatibility.

## v8.6.54

**Version 8.6.54 - Clarify Breach and Hatch Target Selectors**

- Renamed the Breach target field to "Breach point" and clarified its selection prompt.
- Renamed the Operate Hatch target field to "Hatchway" and clarified its selection prompt.
- Preserved target availability, filtering, action resolution, AP costs, mission progress, and save compatibility.

## v8.6.53

**Version 8.6.53 - Further Dim Redrawn Tomb World Event Cards**

- Further dimmed only redrawn Tomb World event cards by changing their brightness from 75% to 37.5%.
- Kept resolved, active, and pending Tomb World event cards visually unchanged.
- Preserved all card content, layout, gameplay behavior, and save compatibility.

## v8.6.52

**Version 8.6.52 - Dim Redrawn Tomb World Event Cards**

- Dimmed only redrawn Tomb World event cards by 25% while keeping their text and REDRAWN badges readable.
- Kept resolved, active, and pending Tomb World event cards visually unchanged.
- Preserved gameplay logic and save compatibility.

## v8.6.51

**Version 8.6.51 - Make Redrawn Tomb World Event Cards Visibly Unused**

- Dimmed redrawn Tomb World event cards while preserving readable card text and badges.
- Added a subtle diagonal sci-fi overlay exclusively to redrawn event cards.
- Kept active, resolved, and pending event cards visually unchanged.

## v8.6.50

**Version 8.6.50 - Highlight Wounded Operatives**

- Added a 2px #f5ff5b border to wounded living operatives in the Operative Status panel.
- Preserved the existing red eliminated treatment for operatives at zero wounds.
- Kept wound counts and existing status-panel layout behavior unchanged.

## v8.6.49

**Version 8.6.49 - Restore Split-Pane Toggle Off Appearance**

- Kept the split-pane toggle's dim border and icon colors while it is off, including after pointer clicks and repeated toggles.
- Preserved an accessible keyboard-only focus outline without making the off state look enabled.
- Updated visible, internal, cache-busting, and service-worker cache versions to v8.6.49.

## v8.6.48

**Version 8.6.48 - Clarify Operative Status Toggle State**

- Dimmed the Operative Status split-view icon when the panel is off.
- Preserved the bright green active treatment when the panel is enabled.
- Improved hover and keyboard-focus feedback while keeping the off state clearly distinct.

## v8.6.47

**Version 8.6.47 - Make Operative Status Panel Section Heights Dynamic**

- Made the NPO and Player Operatives section heights dynamic in the desktop / landscape status panel.
- Reallocated unused vertical space between the two sections based on actual content needs.
- Reduced unnecessary internal scrolling when all operatives can fit in the available space.
- Preserved existing operative card styling and wound/status visibility.

## v8.6.46

**Version 8.6.46 - Improve Operative Status Panel Readability**

- Expanded the Operative Status panel responsively on large displays.
- Reduced unnecessary operative name and type truncation.
- Added minimum readable widths before using two-column roster layouts.
- Prioritized full operative information over avoiding internal scrolling.
- Preserved prominent wound counts and existing eliminated styling.

## v8.6.45

**Version 8.6.45 - Refine Operative Status Panel**

- Made wound counts the primary visual information in the Operative Status panel.
- Added compact bordered boxes for living operatives.
- Reused the existing roster red-border/icon treatment for eliminated operatives.
- Removed wound-percentage color classifications.
- Preserved the existing responsive and fit-first panel behavior.

## v8.6.44

**Version 8.6.44 - Optional Operative Status Panel**

- Added an optional large-screen Operative Status panel.
- Added compact live NPO and Player operative status displays.
- Added wound-condition coloring and current-activation highlighting.
- Added responsive fit behavior designed to avoid unnecessary scrolling.
- Preserved the existing single-column mobile and portrait-tablet experience.

## v8.6.43

**Version 8.6.43 - Clarify My Will Be Done Automation**

- Clarified that the app asks whether an attacking NPO is in the sarcophagus room and automatically applies Accurate 1 when applicable.
- Preserved the official event effect text, existing combat automation, and other Tomb World Event explanations.

## v8.6.42

**Version 8.6.42 - Handle Combat With No NPO Targets**

- Prevented Player operatives from selecting Shoot or Fight when no valid NPO targets remain.
- Fixed Complete Activation becoming trapped by an impossible pending combat action.
- Allowed Player operatives to continue using legal movement and mission actions after all current NPOs are eliminated.
- Preserved mission-specific victory conditions and support for NPOs appearing later.

## v8.6.41

**Version 8.6.41 - Enlarge Active Movement Icons**

* Increased the standard movement and move-to-shoot icons by 50 percent on active NPO question cards.
* Preserved the existing smaller size and muted color of movement icons in question history.
* Kept all SVG artwork, colors, and gameplay behavior unchanged.

## v8.6.40

- Rebuilt the dedicated move-to-shoot SVG with a full outer target ring, center point, and four separate crosshair arms.
- Applied the same fixed bright-green reticle artwork to Reposition-to-Shoot and Dash-to-Shoot cards, history, and confirmations while preserving standard movement endpoints.

## v8.6.39

- Standardized NPO Reposition, Dash, and movement-to-shoot icons through a shared semantic mapping.
- Restored the bright-green reticle-ended icon for Reposition-to-Shoot and Dash-to-Shoot questions, history, and confirmations.
- Enlarged movement icons in active and completed guide cards while preserving mobile alignment.

## v8.6.38

- Kept the relocate-to-shoot icon on completed Dash-to-Shoot activation cards while preserving the standard Dash and Reposition icons everywhere else.

## v8.6.37

- Resized the custom relocate-to-shoot icon to match the Dash icon's width, movement marks, and visual weight while retaining its target reticle.

## v8.6.36

**Version 8.6.36 - Relocate to Shoot Icon**

* Added a bright-green relocate-to-shoot icon combining a movement start, rightward chevrons, and target reticle.
* Applied the new icon only to NPO movement questions that reposition or dash into a valid shooting position.
* Preserved the existing icons, activation behavior, layout, and save compatibility.

## v8.6.35

**Version 8.6.35 - Replace Dash and Charge Movement Icon**

* Replaced the shared Dash and Charge icon with a movement icon featuring connected start and destination circles and three directional chevrons.
* Reused the existing icon color, sizing, alignment, and accessibility behavior across questions, history entries, and movement confirmations.
* Preserved the separate Fall Back, Reposition, Shoot, Fight, target-selection, and control-range icons and all action rules.

## v8.6.34

**Version 8.6.34 - Use Target Reticle for Target Selection**

* Replaced the NPO Shoot and Fight action icon with the existing target reticle while choosing a target.
* Kept the normal action icons on questions and steps that are not selecting a target.
* Preserved target priorities, selection behavior, accessibility, and combat rules.

## v8.6.33

**Version 8.6.33 - Replace Star Icons with Radar Scope**

* Replaced the five-point star icon with the existing radar-scope icon.
* Added the radar icon to all NPO control-range questions.
* Reused one shared radar SVG across active questions, history, and action cards.
* Preserved all NPO rules, decisions, and activation behavior.

## v8.6.32

**Version 8.6.32 - Add Automatic Hot Weapon Rule Support**

* Added automatic Hot rolls after weapons with Hot are used.
* Applied self-damage using the weapon’s effective Hit stat.
* Resolved Hot once after complete Blast and Torrent actions.
* Added persistent recovery and duplicate-roll protection.
* Added Player and NPO incapacitation handling for Hot damage.

## v8.6.31

**Version 8.6.31 - Fix Player Operative Selector After Cancel**

* Fixed the Player operative selector becoming unresponsive after canceling and reopening an activation on iPhone.
* Removed temporary pointer-event suppression from the native selector.
* Prevented touch devices from programmatically focusing the selector when the Guide opens.
* Preserved native picker closing, keyboard accessibility, and activation state.

## v8.6.30

**Version 8.6.30 - Hide Mobile Scrollbars**

* Hid scrollbar tracks and thumbs throughout mobile layouts while preserving touch scrolling.
* Restored the scrollbar-free mobile appearance for pages, dialogs, maps, phase tracks, and checklists.
* Preserved existing desktop scrollbar behavior and all scrollable container dimensions and overflow behavior.

## v8.6.29

**Version 8.6.29 - Fix Player Multi-Target Combat Resume**

* Added deterministic weapon and profile identity for legacy Player team data.
* Fixed valid Torrent and Blast attacks incorrectly displaying Combat could not resume.
* Preserved the selected weapon profile across every multi-target attack.
* Added safe recovery for older pending combat state without stable weapon IDs.
* Preserved AP, damage, refresh recovery, and existing combat rules.

## v8.6.28

**Version 8.6.28 - Clarify Grade 1 Tomb World Event Text**

* Updated the Grade 1 Threat Escalation card to explain that Grade 1 will not trigger any Tomb World events, while other enabled rules may still trigger them.

## v8.6.27

**Version 8.6.27 - Enlarge Victory and Defeat Artwork on Desktop**

* Enlarged Victory and Defeat artwork on desktop screens for greater visual presence.
* Preserved the existing mobile and tablet artwork size and result-screen layout.
* Kept artwork centered, proportional, and contained within the battle-complete panel.

## v8.6.26

**Version 8.6.26 - Sync Operate Hatch Actions with Mission Progress**

* Added closed-hatchway target selection to Player activation Operate Hatch actions.
* Kept Breach targets limited to closed breach points and validated both action types at completion.
* Reused canonical mission progress, history, transaction, and save-recovery state for both actions.
* Preserved Mission & Map corrections, unique feature counting, and save version 3 compatibility.

## v8.6.25

**Version 8.6.25 - Sync Breach Actions with Mission Progress**

* Connected Player activation Breach actions to the canonical mission-feature tracker.
* Mission & Map, Mission Details, Dashboard, and Battle Complete now remain synchronized.
* Added unique feature counting and duplicate-commit protection.
* Preserved manual correction, save recovery, and the existing Demolition Protocol rules.

## v8.6.24

**Version 8.6.24 - Close Player Operative Picker After Selection**

* Fixed the Player operative selection list remaining open on iPhone.
* Prevented activation rerenders from refocusing the operative selector.
* Added touch-aware picker closing without degrading keyboard accessibility.
* Preserved operative selection, AP, actions, and activation state.

## v8.6.23

**Version 8.6.23 - Clarify Weapon Rule Summaries**

* Replaced duplicate Piercing entries with one clear gameplay description.
* Explained that Piercing reduces the defender’s defense dice.
* Added correct singular and plural wording for Piercing values.
* Consolidated similar duplicated automatically handled weapon-rule entries.
* Preserved all existing combat calculations and automation.

## v8.6.22

**Version 8.6.22 - Prevent Guide Titles from Receiving Focus**

* Removed keyboard and programmatic focus from non-interactive titles.
* Dialogs now use their headings through accessible labeling instead of focusing them.
* Initial focus now moves to the first meaningful interactive control.
* Preserved visible focus indicators for all real controls.

## v8.6.21

**Version 8.6.21 - Add Help to New Game Setup Menu**

* Added the existing Help screen to the Game Menu during New Game Setup.
* Preserved the current setup step, selections, and background while viewing Help.
* Restored focus to the Help button when returning to the Game Menu.
* Kept About, save controls, and setup behavior unchanged.

## v8.6.20

**Version 8.6.20 - Keep Operative Cards Consistent Across Roster Groups**

* Standardized operative card widths across all roster categories.
* Single-operative groups now use one normal grid column instead of stretching across the row.
* Preserved consistent selected-state styling and responsive layouts.
* Added support for future categories with any number of operatives.

## v8.6.19

**Version 8.6.19 - Add About and Legal Information**

* Added an About screen accessible from the Game Menu.
* Added author credit for J.R. Benning.
* Added unofficial-project, ownership, non-affiliation, official-rules,
  warranty, liability, privacy, and user-responsibility notices.
* Added a repository asset and intellectual-property audit.
* Preserved gameplay state and offline access.

## v8.6.18

**Version 8.6.18 - Remove Focusability from Battle Result Labels**

* Changed Victory and Defeat to non-interactive result content.
* Removed them from keyboard tab navigation.
* Eliminated the undesirable focus border without weakening real control focus indicators.
* Preserved Battle Complete styling and accessibility.

## v8.6.17

**Version 8.6.17 - Fix Mission Objective Feature Card Spacing**

* Added proper spacing between feature names and numbers.
* Moved feature status text onto a separate line.
* Standardized active and completed Mission Objective card rendering.
* Preserved mission tracking and completion behavior.

## v8.6.16

**Version 8.6.16 - Clarify Grade Gameplay Changes**

* Reworded Grade effects to clearly explain what will happen after escalation.
* Identified reinforcements explicitly as NPO reinforcements.
* Distinguished app-controlled effects from player tabletop actions.
* Standardized future tense, timing, terminology, and singular/plural grammar across all Grades.

## v8.6.15

**Version 8.6.15 - Show Desktop Background During Game Setup**

* Desktop backgrounds are now selected when New Game setup begins.
* The selected image remains visible throughout setup, gameplay, and Battle Complete.
* Setup navigation, refresh, and Update App preserve the same image.
* Mobile and portrait layouts retain the existing black-to-green background.

## v8.6.14

**Version 8.6.14 - Explain Grade Gameplay Changes**

* Added clear gameplay descriptions to Grade-change pop-up cards.
* Grade cards now explain the active reinforcement, event, and awakening behavior.
* Descriptions are derived from the same Grade configuration used by gameplay.
* Added Restless Tomb-aware wording without changing any Grade mechanics.

## v8.6.13

**Version 8.6.13 - Add Persistent Desktop Backgrounds**

* Added one randomly selected landscape background for each new game.
* Desktop games retain the same selected background for the complete battle.
* Added manifest-based discovery for additional sequentially named landscape images.
* Preserved the existing stylized black-to-green background on mobile and portrait layouts.
* Added save, import, update, and offline persistence for the selected desktop background.

After adding or removing files in `Assets/Images/Backgrounds/`, run `python3 tools/generate-background-manifest.py` and include the regenerated manifest in the next application release.

## v8.6.12

**Version 8.6.12 - Fix Combat Summary Word Wrapping**

* Prevented combat summary cards from splitting normal words.
* Added a responsive multi-row desktop summary layout.
* Preserved readable text and mobile responsiveness.

## v8.6.6

**Version 8.6.6 - Fix Blast Combat Resolution**

- Initialized a fresh attack and defense roll for every Blast target while keeping the originally selected weapon profile locked.
- Applied each target's damage before advancing and skipped targets that were no longer valid.
- Cleared Blast target and dice state when an attack is cancelled or completed.
- Preserved standard single-target attacks and the normal activation flow.

## v8.6.11

**Version 8.6.11 - Preserve Weapon Across Multi-Target Attacks**

- Locked the selected weapon and profile for the complete multi-target attack.
- Removed repeated weapon selection between targets.
- Preserved separate dice, damage, and weapon-rule resolution for every target.
- Preserved single AP cost, sequence recovery, and save compatibility.

## v8.6.10

**Version 8.6.10 - Remove Redundant Target Confirmation Screen**

- Target confirmation now proceeds directly into combat.
- Removed the unnecessary read-only target confirmation step.
- Simplified the single-target attack flow.
- Preserved AP, target selection, multi-target attacks, and save recovery.

## v8.6.9

**Version 8.6.9 - Fix NPO Target Confirmation**

- Fixed Confirm Target after direct current-position Shoot and Fight checks.
- Restored reliable target confirmation across all NPO attack entry paths.
- Added visible recovery for invalid target or missing attack state.
- Preserved AP, target priorities, Player wound labels, multi-target combat, and save compatibility.

## v8.6.8

**Version 8.6.8 - Check Attacks Before NPO Movement**

- Added current-position Shoot and Fight checks before movement intended to enable those attacks.
- NPOs now attack immediately when a valid target is already available.
- Prevented unnecessary Reposition, Dash, and Charge AP spending.
- Preserved NPO priorities, movement distances, attack follow-ups, multi-target combat, and save compatibility.

## v8.6.7

**Version 8.6.7 - Fix Multi-Target Attack Resolution**

- Fixed Blast, Torrent, and Sweeping attacks so every selected target receives a separate combat sequence.
- Added reliable shared target sequencing for Player and NPO attacks.
- Added per-target damage, persistence, history, and final multi-target summaries.
- Preserved single AP costs, weapon rules, combat effects, missions, and activation behavior.

## v8.6.6 (previous release)

**Version 8.6.6 - Show Reposition Distance in NPO Guidance**

- Added each NPO’s Move distance to Reposition questions and confirmation instructions.
- Updated shooting, fighting, support, and mission-focused Reposition guidance.
- Preserved the fixed 3-inch Dash distance and all existing movement behavior.
- Preserved AP costs, movement intent, combat follow-ups, and save compatibility.

## v8.6.5

**Version 8.6.5 - Show Player Wounds in Target Selection**

- Added current and maximum wounds to Player operative target-selection labels.
- Updated NPO Shoot, Fight, special-action, and guided secondary-target selectors.
- Preserved target priorities, eligibility, ordering, combat, and automatic selection behavior.
- Kept target IDs and save data unchanged.

## v8.6.4

**Version 8.6.4 - Automate Transdimensional Relocation**

- Corrected Transdimensional Relocation to randomly select two Player operatives and swap their positions.
- Added automatic, persisted selection of two eligible operatives.
- Added clear tabletop swap instructions and an action-specific confirmation.
- Added safe redraw handling when fewer than two eligible operatives are available.
- Preserved all operative wounds, orders, activation states, missions, and other event behavior.

## v8.6.3

**Version 8.6.3 - Clarify Event Placement Instructions**

- Replaced vague `printed placement` terminology with clear references to event-card placement instructions.
- Improved Awakened Warrior instructions and resolved messaging.
- Clarified placement wording across Tomb World events and reinforcements.
- Preserved all event, placement, reinforcement, and Strategy Phase behavior.

## v8.6.2

**Version 8.6.2 - Automate Dimensional Banishment**

* Dimensional Banishment now automatically rolls and displays 2D6.
* The Guide compares the result with the target’s remaining wounds and explains whether the target survives or is incapacitated.
* Removed manual Dimensional Banishment entry controls.
* Added safe persistence and incapacitation-effect integration.
* Preserved all weapon profiles, combat values, missions, and activation behavior.

## v8.6.1

**Version 8.6.1 - Simplify Breach Navigation**

* Replaced Close Guide with Cancel on the first Breach Sarcophagus question.
* Removed Close Guide from later Breach steps.
* Added full-width Back navigation on secondary and confirmation screens.
* Preserved all Breach eligibility, AP, dice, mission progress, and victory behavior.

## v8.6.0

**Version 8.6.0 - Correct Destroy Sarcophagus Mission Flow**

- Moved Breach Sarcophagus into individual Player operative activations.
- Added control-range, AP, action-usage, and eligibility checks.
- Removed the repeatable end-of-turn Breach button.
- Added immediate Player victory when Destruction Points reach 20.
- Preserved Nanoscarab Repair while the objective remains incomplete.

## v8.5.4

**Version 8.5.4 - Clarify Partial Reinforcement Deployment**

* Clearly separated deployable NPOs from reinforcements blocked by battlefield capacity or physical inventory.
* Updated deployment headings after confirmation.
* Added precise blocking reasons and singular or plural wording.
* Preserved all reinforcement generation and deployment rules.

## v8.5.3

**Version 8.5.3 - Recognize Weapon Range Rules**

* Recognized Range weapon rules as supported target-eligibility checks.
* Removed misleading unsupported-rule messages and warnings for Range.
* Prevented duplicate console warnings for unknown weapon rules.
* Preserved all combat calculations and weapon behavior.

## v8.5.2

**Version 8.5.2 - Clarify Fall Back Control Range Question**

- Clarified the first Fall Back question so its title and helper consistently describe the NPO being within a Player operative’s control range.
- Preserved all Fall Back eligibility, priority, AP, and activation behavior.

## v8.5.1

**Version 8.5.1 - Fix Guided Weapon Rule Combat Resume**

- Fixed Torrent, Blast, and Seek Light combat resumption after guided tabletop questions.
- Combat screens are now rebuilt before dice rolling begins.
- Preserved weapon, target, profile, and secondary-target selections.
- Added safe recovery instead of an uncaught missing-DOM error.

## v8.5.0

**Version 8.5.0 - Replace Manual Weapon Rule Resolution**

- Replaced generic manual weapon-rule instructions with automatic and guided resolution.
- Automated Piercing Crits and Stun.
- Added guided Blast, Torrent, Seek Light, and Shock flows.
- Added persistent multi-target attack sequencing.
- Preserved Severe, combat values, activation behavior, missions, and events.

## v8.4.3

**Version 8.4.3 - Automate the Severe Weapon Rule**

- Severe now automatically converts one retained normal success into a critical success when no critical success was retained.
- Updated combat dice, damage, persistence, and accessibility to reflect the converted result.
- Removed incorrect manual-resolution instructions for Severe.
- Preserved all other weapon rules, combat behavior, missions, and events.

## v8.4.2

**Version 8.4.2 - Unify NPO Movement Confirmation Layout**

- Updated NPO movement confirmation screens to use the full activation heading, profile strip, and card layout.
- Moved movement confirmation buttons into the same control area as NPO question choices.
- Added Back navigation that safely returns to the selecting question without committing movement.
- Added Close Guide navigation that preserves the pending movement and follow-up state.
- Preserved movement intent, AP costs, combat, missions, and event behavior.

## v8.4.1

**Version 8.4.1 - Preserve NPO Movement Intent**

- Added separate movement purposes so rejecting a Reposition-to-Shoot option does not reject every Reposition.
- Movement that promises Shoot or Fight now proceeds directly to that follow-up action.
- Added clear final-AP Dash guidance so players know the activation will end.
- Preserved NPO priorities, AP costs, combat, missions, and event behavior.

## v8.4.0

**Version 8.4.0 - Simplify NPO Activation Guidance**

- Rewrote NPO Activation questions and instructions in concise, plain language.
- Removed internal labels such as Applicability, Feasibility, printed objective, and effective APL.
- Added behavior-specific Reposition and Dash guidance.
- Reformatted target priorities and special-action instructions for faster tabletop use.
- Preserved all NPO priorities, AP costs, combat, missions, events, and activation behavior.

## v8.3.1

**Version 8.3.1 - Fix Fall Back Question Guidance**

- Clarified that the initial control-range question does not require movement.
- Moved Fall Back movement instructions to the destination-feasibility question.
- Preserved Fall Back’s 2 AP cost and existing activation behavior.

## v8.3.0

**Version 8.3.0 - Clarify NPO Movement Guidance**

- Replaced unclear `printed objective` terminology with direct movement guidance.
- Simplified completed-action progress summaries to concise action names.
- Preserved NPO priorities, AP costs, and activation behavior.

## v8.2.0

**Version 8.2.0 - Clarify NPO Fall Back Guidance**

- Reworded the Fall Back question to explain that the NPO must finish outside every Player operative’s control range.
- Added clear guidance for movement distance, route selection, and base placement.
- Preserved Fall Back priority, AP cost, eligibility, and activation behavior.

## v8.1.0

**Version 8.1.0 - Streamline NPO Multi-Action Flow**

- Removed redundant action-completed interstitials after confirmed NPO movement.
- NPOs now proceed directly from Reposition, Dash, Charge, and Fall Back confirmation to their next applicable action.
- Removed duplicate generic completion screens after acknowledged Shoot and Fight combat results.
- Added compact AP and completed-action context to subsequent activation questions.
- Preserved meaningful special-action, combat, event, mission, and ability resolution screens.

## v8.0.1

**Version 8.0.1 - Fix NPO Action Eligibility and Activation Restore**

- Replaced vague NPO action questions with objective tabletop eligibility questions.
- Preserved printed behavior priorities while ensuring the player confirms facts rather than making tactical choices.
- Corrected Necron Warrior Fall Back handling so it is considered only when the NPO is within Player control range.
- Fixed refresh and Update App restoration during in-progress NPO activations.
- Added a visible recovery screen for unexpected startup restoration errors.

## v8.0.0

**Version 8.0.0 - Full NPO Multi-Action Activations**

- Rebuilt NPO activations around a persistent AP-based action loop.
- NPOs now reevaluate their printed behavior after movement, attacks, and special actions while AP remains.
- Added complete action history, correct AP spending, multi-action combat continuation, and safe save-and-reload behavior.
- Prevented activations from ending after the first ordinary action when additional useful legal actions remain.
- Preserved all NPO profiles, combat rules, Tomb World events, missions, and existing Player behavior.

## v7.6.3

**Version 7.6.3 - Remove Leading Player Roster Delimiter**

- Removed the unnecessary leading dot from the Player operative list on the deployment screen.
- Standardized compact Player and NPO deployment lists to use separators only between operative names.
- Preserved Player numbering, weapon variants, roster order, and deployment behavior.

---

## v7.6.2

**Version 7.6.2 - Remove Team Loading Layout Shift**

- Removed the temporary visible Kill Team loading message that caused the setup screen to shift and flash.
- Retained the disabled `Loading Team...` button and accessible loading state.
- Preserved load failures, retry behavior, and all v7.6.1 stale-request protections.

---

## v7.6.1

**Version 7.6.1 - Prevent Stale Player Team Selection**

- Disabled Build Roster until the currently selected Kill Team has completely loaded.
- Added request-token protection so older team-load responses cannot overwrite a newer selection.
- Added defensive roster-screen validation and clear loading, failure, and retry states.
- Preserved all Player roster rules, operative numbering, and existing setup behavior.

---

## v7.6.0

**Version 7.6.0 - Renumber Selected Player Operatives**

- Renumbered duplicate Player operatives sequentially after the final legal roster is selected instead of retaining source-data instance numbers.
- Applied one persisted display-number mapping across setup, deployment, activation, combat, casualty tracking, and battle summaries while preserving operative IDs and save compatibility.

---

## v7.5.9

**Version 7.5.9 - Standardize Duplicate Operative Naming**

- Added one shared, roster-aware display-name formatter for Player and NPO operatives.
- Applied sequential duplicate numbering across rosters, deployment, activation, combat, dialogs, events, notifications, and battle summaries.
- Kept single-instance operative names unnumbered and preserved saved data and gameplay behavior.

---

## v7.5.8

**Version 7.5.8 - Standardize Player Operative Variant Naming**

- Standardized player operative weapon and loadout variant names to use parentheses instead of em dashes throughout the interface.
- Added stable display-order numbering for duplicate Player Operatives across setup, gameplay, and the battle record.
- Preserved operative IDs, existing saved games, sorting, filtering, and gameplay behavior.

---

## v7.5.7

**Version 7.5.7 - Clean Up the Battle Complete Screen**

- Changed the Battle Complete heading focus outline from the browser-default blue to the app’s green accent.
- Removed Confirm Escape, Undo Escape, and other mission-editing controls from completed mission reviews.
- Preserved final mission progress, operative statuses, accessibility focus, and all active mission controls.

---

## v7.5.6

**Version 7.5.6 - Enforce the Four Turning Point Limit**

- Prevented battles from advancing beyond Turning Point 4.
- Added final mission outcome evaluation when Turning Point 4 ends.
- Added guided victory or defeat recording when the final result requires tabletop confirmation.
- Safely redirects previously saved Turning Point 5 battles to final resolution without repeating gameplay.

---

## v7.5.5

**Version 7.5.5 - Collapse Active Tomb World Events**

- Made the Active Tomb World Events panel collapsible and collapsed by default during gameplay.
- Added a compact active-event count so the current activation remains prominent on mobile screens.
- Preserved full event descriptions when expanded and retained all automatic and guided event mechanics.

---

## v7.5.4

**Version 7.5.4 - Split Strategy Phase into Guided Steps**

- Split the Strategy Phase into Strategy Actions, Tomb World Events, and Reinforcements & Review screens.
- Added Back and Continue navigation with persistent step progress.
- Kept required event and reinforcement resolution blocking on the appropriate step.
- Preserved initiative, event draws, redraws, reinforcements, Restless Tomb, and all existing gameplay behavior.

---

## v7.5.3

**Version 7.5.3 - Fix Tomb World Event Redraws**

- Fixed The Maze Reforms `No Valid Changes · Draw Again` action so it reliably displays one replacement event card.
- Made event redraws atomic and persistent so rapid taps, rerendering, and reload cannot draw duplicate cards.
- Added safe event-deck recycling and recoverable handling when no replacement is available.
- Applied the same centralized redraw behavior to all Tomb World events that can require another card.

---

## v7.5.2

**Version 7.5.2 - Restore Guided Aggressive Defence Resolution**

- Pauses an incapacitating Player attack after prevention effects to show the mandatory animated Aggressive Defence D3 result before removing the Macrocyte.
- Applies one retaliatory wound exactly once on a 2 or 3 and preserves the within-2-inch answer throughout the pending attack.

---

## v7.5.1

**Version 7.5.1 - Allocate the Lowest Available NPO Numbers**
- Added one deterministic physical-instance allocator shared by every NPO creation path.
- Starting rosters, reinforcements, Tomb World events, mission effects, and manual additions now use the lowest available number for each NPO type.
- Preserved random NPO-type and loadout selection, physical and loadout limits, natural display sorting, and existing saved-battle identities.
- Stopped setup deletion from renumbering the NPO instances that remain allocated.

## v7.5.0

**Version 7.5.0 - Correct and Automate Tomb World Event Effects**
- Added a reusable gameplay engine for persistent Tomb World events.
- Corrected and automated Dark of the Tomb, My Will Be Done, Reanimation Protocols, Countertemporal Shifting, and Subjugation Glyphs using the bundled official mission pack.
- Integrated event effects with rerolls, weapon rules, per-die damage, incapacitation, reanimation, and effective APL.
- Persisted event dice, selections, and answers so navigation and reload cannot repeat an effect.
- Preserved Restless Tomb, Deadly Encounters, event probabilities, and unrelated gameplay.

## v7.4.2

**Version 7.4.2 - Remove Duplicate Strategy Event Effects**

- Removed duplicate active-event cards from the Strategy Phase when the full Tomb World Event card is already displayed.
- Added a clear `RESOLVED • ACTIVE` presentation for persistent event effects.
- Preserved compact active-event reminders during later gameplay screens.
- Corrected singular and plural event-card summary wording.
- Preserved all event rules, Restless Tomb behavior, event state, timing, and expiry.

## v7.4.1

**Version 7.4.1 - Stop Repeated NPO Migration Notices**

- Fixed current numbered NPO instance names being incorrectly reported as legacy aliases.
- Current canonical saves now load idempotently without showing the v7 roster-migration notice after ordinary app updates or reloads.
- Genuine legacy aliases, invalid loadouts, obsolete fields, and other real save repairs continue to migrate once and remain fully supported.

## v7.4.0

**Version 7.4.0 - Reorganize Strategy Phase Results**

- Reordered the Strategy Phase screen for clearer rules timing and results.
- Grouped Restless Tomb requirements with Tomb World event cards.
- Added dynamic required, drawn, and resolved event counts.
- Added clear Pending, Redrawn, and Resolved event statuses.
- Moved Current Battlefield State below event and reinforcement results.
- Preserved all Strategy Phase gameplay, event-count, Restless Tomb, and Deadly Encounters behavior.

## v7.3.0

**Version 7.3.0 - Add Deadly Encounters: Tomb Worlds**

- Added Deadly Encounters: Tomb Worlds as an optional official PvE solo expansion from White Dwarf 521, independent from Restless Tomb.
- Added complete Room and Objective D33 tables, battle-wide feature uniqueness, and Unusual multi-feature resolution.
- Added persistent manual room, eligible-marker, carrier-ready state, operative-location, roll, effect, pending-resolution, and correction tracking.
- Added save, reload, import, and export support while preserving the Restless Tomb event calculation and existing mission behavior.
- Added concise, copyright-conscious feature guidance; consult White Dwarf 521, February 2026 for authoritative wording.

## v7.2.0

**Version 7.2.0 - Add Optional Restless Tomb Events**

- Added the optional Restless Tomb house rule to Mission Briefing for all six missions.
- Beginning with Turning Point 2, the option guarantees a minimum of one Tomb World event during each Strategy Phase; standard event rules still control higher event counts.
- Restless Tomb defaults to off and persists with the current battle through save, reload, export, and import.

## v7.1.2

**Version 7.1.2 - Correct NPO Activation Tracker Start States**

- Reserve NPOs no longer appear as Activated: the Activation Tracker now lists only deployed and previously deployed eliminated NPOs.
- Dormant NPOs use a distinct, subdued Dormant state and style while preserving visible status text.
- Common Threat behavior remains unchanged across all missions: living deployed NPOs are Dormant at Threat 0 and Ready above Threat 0.

## v7.1.1

**Version 7.1.1 - NPO Card Action Placement**

- Kept Gameplay Profile with the normal operative information and confined the bottom-aligned action area to the wound/heal row followed by Remove NPO.

## v7.1.0

**Version 7.1.0 - Mission Selection Responsiveness and Deployment UI**

- Mission choices now show their selected state immediately, before dependent mission automation finishes loading, and stale loads cannot replace a newer selection.
- Simplified Deploy Kill Teams by removing deployment-screen NPO roster editing and regeneration while preserving the generated roster and deployment flow.
- Corrected the compact deployed-NPO list to place one delimiter only between alphabetically sorted operative names.
- Bottom-aligned the wound and heal controls across NPO roster cards using the existing responsive flex layout.

## v7.0.7

**Version 7.0.7 - Complete v7 Validation, Documentation, and Cleanup**

- Completed release validation of the seven supported Tomb World NPO types, their 21-model physical inventory, legal instance loadouts, alphabetical presentation, deployment, activation, combat, support rules, reinforcement, threat, history, and battle completion paths.
- Verified current-save reload and import/export round trips plus deterministic legacy migration, including safe cleanup of obsolete NPO portrait and Obelisk Node Matrix fields and regeneration for unsupported retired active rosters.
- Expanded player help for the Tomb World box roster, alphabetical lists, per-instance loadouts, text-only NPO presentation, unsupported Matrix rules, and the v7 save-migration flow.
- Validated responsive and accessible text-based NPO displays and the offline application shell while preserving player-operative portraits, mission maps, status icons, existing gameplay balance, and player-operative behavior.
- Removed a stale persistence-result assumption that prevented a valid saved battle from enabling and restoring **Continue Game**, with focused regression coverage.

### Supported Tomb World NPO pool

The Guide uses the physical NPO models in the Tomb World box: the **Canoptek Circle**, **Necron Warriors**, and **Canoptek Scarab Swarms**. The Canoptek Circle consists of the **Geomancer**, **Canoptek Tomb Crawler**, **Canoptek Macrocyte Warrior**, **Canoptek Macrocyte Accelerator**, and **Canoptek Macrocyte Reanimator**. Together with the Necron Warrior and Canoptek Scarab Swarm, these are the seven active NPO types.

Rosters draw from the 21 physical models available in the box. Applicable loadouts are selected per operative instance, and user-facing NPO lists use alphabetical, natural-number ordering. NPO portraits are intentionally not displayed, and the Obelisk Node Matrix is not supported by the app.

Current and older saves are handled by the v7 migration system. Known legacy aliases are normalized safely. An active battle containing an unsupported retired NPO must return to setup and regenerate its NPO roster after the player confirms the migration notice; canceling leaves the original saved data unchanged.

## v7.0.6

**Version 7.0.6 - Legacy Save and Retired NPO Migration**

- Added one deterministic, idempotent migration pipeline for browser saves and imported files, including canonical supported NPO identities, stable instance IDs, loadouts, wounds, and current profiles.
- Detects unsupported or over-allocated active NPO rosters and requires an explicit, cancelable return to setup instead of trimming or silently substituting models.
- Removes obsolete NPO portrait and Obelisk Node Matrix fields while preserving player data, settings, mission and roster selections, and completed historical records.
- Validates migrated active allocations against the authoritative v7 catalog and preserves alphabetical NPO presentation.

---

## v7.0.5

**Version 7.0.5 - Obelisk Node Matrix Cleanup**

- Removed all active Obelisk Node Matrix support and references, including Matrix-derived bonuses, targeting alternatives, UI, and state.
- Preserved the normal visible-distance options for Canoptek Control, Molecular Breach, Overcharge, Cranial Overload, Reanimate, and Nanoscarab Beam.
- Added narrowly scoped save normalization that safely ignores obsolete Matrix-only fields from existing v7 saves without changing ordinary operative or battle-history state.
- Confirmed that no Matrix-only assets or cache entries remain, while retaining mission, player-operative, status, faction, and eliminated-NPO assets.

---

## v7.0.4

**Version 7.0.4 - Text-Based NPO Displays**

- Removed the obsolete Canoptek Circle miniature portraits and kept active NPO catalog, roster, deployment, activation, combat, and selector displays compact and text based.
- Removed the remaining NPO portrait asset dependency without adding replacement thumbnails, fallbacks, loading handlers, or cache entries.
- Preserved player-operative image assets, mission maps, action and status icons, and the eliminated-NPO skull overlay and red card border.
- Preserved NPO gameplay behavior, save identity, alphabetical display ordering, and the intentional exclusion of the Obelisk Node Matrix.

---

## v7.0.3

**Version 7.0.3 - Canoptek Circle Activation and Combat Integration**

- Integrated all five Canoptek Circle types into the shared NPO activation recommendation, effective-APL, action-legality, target-selection, and combat flows.
- Added loadout-aware attacks and weapon modes, guided Canoptek support actions, Reanimate and Nanoscarab Beam resolution, and Canoptek incapacitation and post-attack effects.
- Added A Ceaseless Scuttling to the Strategy Phase with a new-instance physical-model exception, plus persistent rule history, threat-safe state, and turning-point restrictions.
- Preserved alphabetical presentation, existing Necron Host behavior, and the intentional exclusion of the Obelisk Node Matrix and NPO portraits.

---

## v7.0.2

**Version 7.0.2 - Complete Canoptek Circle NPO Profiles**

- Added complete structured profiles, errata-corrected weapons, operative actions, and passive rules for all five Canoptek Circle NPO types.
- Added loadout-dependent weapon modes and persistent temporary APL, Molecular Breach, Reanimate, and Nanoscarab Beam rule state using the shared NPO profile schema.
- Audited Necron Warrior and Canoptek Scarab Swarm against the shared schema without changing their existing gameplay statistics.
- Continued to exclude the unsupported Obelisk Node Matrix while preserving normal non-Matrix targeting options and alphabetical NPO display ordering.

---

## v7.0.1

**Version 7.0.1 - NPO Roster Generation and Box Inventory Limits**

- Updated NPO roster generation to allocate only models from the authoritative Tomb World physical inventory.
- Enforced physical box quantities globally across starting rosters, reserves, eliminated operatives, events, and reinforcements.
- Added stable operative numbering and instance loadout selection, including the one-isolator Tomb Crawler limit.
- Updated reinforcement availability to respect every model already allocated to the active game.

---

## v6.7.5

**Version 6.7.5 - Consistent Eliminated Operative Borders**

- Applied the Activation Tracker's red eliminated border treatment to eliminated Player Operative and NPO roster cards.
- Preserved the existing eliminated badges, dimming, and Player/Necron skull overlays while matching the border thickness and corner radius across all three views.
- Added focused regression coverage and synchronized visible, internal, cache-busting, and service-worker cache versions to v6.7.5.

## v6.7.4

**Version 6.7.4 - Prominent Eliminated NPO Overlay**

- Unified Player Operative and NPO eliminated-card opacity, overlay scale, centering, and stacking while preserving their distinct artwork.
- Increased the Necron emblem's brightness and contrast and added a subtle white outer glow so it remains crisp and immediately visible over card contents.
- Added focused regression coverage and synchronized visible, internal, cache-busting, and service-worker cache versions to v6.7.4.

## v6.7.3

**Version 6.7.3 - Eliminated NPO Overlay Layering**

- Ensured the shared eliminated-card skull overlay layer renders above every Player Operative and NPO card child without changing its appearance or placement.
- Added regression coverage for the shared overlay z-index and synchronized visible, internal, cache-busting, and service-worker cache versions to v6.7.3.

## v6.7.2

**Version 6.7.2 - Damaged Necron Skull Overlay**

- Replaced the eliminated NPO roster overlay with the supplied damaged Necron skull artwork while retaining the Player Operative skull-and-crossbones.
- Reused the existing elimination overlay dimensions, centering, dimming, and responsive positioning.
- Synchronized visible, internal, cache-busting, and service-worker cache versions to v6.7.2.

## v6.7.1

**Version 6.7.1 - Scout Squad Review Corrections**

- Explicitly classified Scout operative datacard entries as passive abilities or 1AP unique actions without adding team-specific gameplay branches.
- Marked Tactical Manoeuvre and Diversion as Forward Scouting options while preserving their contextual Strategy Phase guidance and usage limits.
- Strengthened Scout Squad tests and synchronized visible, internal, cache-busting, and service-worker cache versions to v6.7.1.

## v6.7.0

**Version 6.7.0 - Scout Squad Player Kill Team**

- Added Scout Squad as a selectable 9-operative Player Kill Team with one required Sergeant, unique specialist limits, repeatable Warriors, and mutually exclusive Sergeant, Heavy Gunner, and Warrior loadouts.
- Added all supplied datacard weapon profiles, operative abilities, Forward Scouting options, Strategic Gambit guidance, stable IDs, offline registration, and save-compatible team data.
- Added Scout Squad validation, roster, profile, combat-path, persistence, offline, version, and existing-team regression coverage.
- Engine Enhancements: None. The established definition-driven roster, combat, guidance, and persistence architecture supports Scout Squad without team-specific gameplay branches.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.7.0.


## v6.6.1

**Version 6.6.1 - Spectre Squad Review Corrections**

- Completed opt-in stable-ID validation for Spectre operative weapons, abilities, faction rules, and gambits.
- Added generic manual tabletop weapon-resolution guidance for Blast and Torrent profiles, including explicit affected-roster updates.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.6.1.

## v6.6.0

**Version 6.6.0 - Spectre Squad Player Kill Team**

- Added Spectre Squad as a selectable 11-operative Player Kill Team with mandatory operatives, unique specialists, repeatable Troopers, and mutually exclusive loadouts.
- Added all supplied datacard weapon profiles, operative guidance, Elite Fieldcraft and Camo Cloaks tabletop reminders, offline registration, and save-compatible stable IDs.
- Generalized mutually exclusive roster selection groups, Player team definition validation, and the multi-weapon selection placeholder without team-name branches.
- Added Spectre Squad coverage plus Deathwatch and Tempestus Aquilons regression checks.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.6.0.

## v6.5.1

**Version 6.5.1 - Player Team Review Corrections**

- Applied complete data-driven roster validation during setup and deployment, including required leader and Gravis limits.
- Limited faction Strategic Gambit reminders to their declared turning points and clarified legal-roster guidance.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.5.1.

## v6.5.0

**Version 6.5.0 - Tempestus Aquilons Player Kill Team**

- Added the Tempestus Aquilons as a selectable 11-operative Player Kill Team with official datacards, loadout choices, multiple weapon profiles, and tabletop faction-rule guidance.
- Generalized roster category requirements and limits so future Player Kill Teams can declare legal selection constraints in data.
- Added regression coverage for roster legality, profiles, state tracking, save compatibility, and the existing Deathwatch team.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.5.0.

## v6.4.11

**Version 6.4.11 - Aligned Player Roster Actions**

- Anchored Player operative Wound and Heal controls to the bottom of each card so action rows align despite different weapon-list lengths or operative statuses.
- Preserved the responsive roster grid, existing card styling, eliminated state, and all roster behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.4.11.

## v6.4.10

**Version 6.4.10 - Aligned NPO Roster Actions**

- Anchored each Remove NPO action to the bottom of its card so statuses with and without wound controls align in the responsive roster grid.
- Preserved the existing card dimensions, button styling, roster behavior, and mobile-first layout.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.4.10.

## v6.4.9

**Version 6.4.9 - Consistent NPO Roster Removal**

- Added the existing roster removal action to Reserve NPO cards after verifying that Reserve entries are not protected mission or reinforcement state.
- Renamed NPO roster removal buttons to **Remove NPO** so they pair consistently with **Add NPO**.
- Preserved the existing removal handler and all reinforcement, activation, mission, and persistence behavior.

## v6.4.8

**Version 6.4.8 - Read-Only NPO Activation Status**

- Removed the manual Ready and Expend controls from NPO roster cards.
- Kept automatic activation tracking and status indicators unchanged while preserving wound and roster management controls.
- Updated the NPO roster guidance and simplified the remaining card actions.

## v6.4.7

**Version 6.4.7 - Roster Restoration Safeguards**

- Prevented an out-of-action NPO from being restored when the maximum active NPO limit is already reached.
- Preserved Player activation history when healing an eliminated operative, preventing healing from granting another activation.
- Added focused regression coverage for Player and NPO wound restoration behavior.

## v6.4.6

**Version 6.4.6 - Roster Card Consistency and Wound Controls**

- Unified Player and NPO roster card headers, status badges, compact statistics, wound displays, and wound controls.
- Added persistent Player roster wound/heal controls and conservative one-wound restoration without granting another activation.
- Removed roster-only Player status editing, Restore Operative, and Player Attack controls while preserving guided-play flows.

## v6.4.5

**Version 6.4.5 - Activation Tracker Eliminated-State Styling**

- Updated eliminated Player operative and NPO tracker rows to use the Guide's red eliminated-state border, background, and text treatment.
- Added the existing skull symbol to eliminated tracker rows with narrow-row fallback behavior that preserves name and status readability.
- Preserved activation state behavior, restoration controls, and READY/ACTIVATED presentation.

---

## v6.4.4

**Version 6.4.4 - Resolve Combat Weapon Summary Clarity**

- Shows an em dash in the Resolve Combat Weapon summary while a required multi-weapon selection is pending.
- Keeps the weapon dropdown placeholder and existing selection, Continue, and single-weapon automatic behaviors unchanged.

## v6.4.3

**Version 6.4.3 - Multi-Weapon Combat Selection Fix**

- Synchronized NPO weapon dropdown choices with the authoritative combat draft, header profile, and Continue action.
- Preserved valid weapon selections across dialog rerenders while keeping the placeholder disabled and the single-weapon automatic flow unchanged.
- Added regression coverage for selection, rerendering, header updates, Continue enablement, and attack-roll startup.

## v6.4.2

**Version 6.4.2 - Contextual NPO Combat Guidance**

- Shows weapon guidance only for the matching attack type and weapon, while keeping profile recommendations visible across profiles of that weapon.
- Limits Weapon Sentinel guidance to shooting resolution and refreshes guidance when the selected NPO weapon profile changes.

## v6.4.1

**Version 6.4.1 - Zero-NPO Deployment Guidance**

- Treats missions with no starting NPOs as a valid deployment state, explains when enemies enter later, and removes the unnecessary zero-operative confirmation.
- Preserves the existing deployment checklist for missions that begin with one or more NPOs.

## v6.4.0

**Version 6.4.0 - Scout Sub-Crypt Mission Engine**

- Registered Mission 05 with the data-driven Mission Engine, including animated D3 room awakening, authoritative room-scout progress, correction, HUD/details history, completion, and restoration.
- Preserved the official no-starting-NPO setup, first-entry awakening, Conceal/Ready placement flow, Operate Hatch Threat exception, Scout Room Threat reduction, and immediate three-room victory.
- Added offline caching, validation, and regression coverage for the Mission 05 definition and synchronized all release versions to v6.4.0.
- Engine Enhancements: None.

## v6.3.0

**Version 6.3.0 - Recover Transponder Mission Engine**

- Implemented Mission 03, Recover Transponder, with JSON-driven D3 search rolls, escaped-carrier completion, Mission HUD, Mission Details, history, and save/load support.
- Registered and cached the Mission 03 definition for online and offline play while retaining the existing focused transponder site and carrier workflow.
- Added Mission 03 automated acceptance plus Mission 01, Mission 02, and Mission 04 regression coverage.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.3.0.

## v6.2.0

**Version 6.2.0 - Demolition Protocol Mission Engine**

- Implemented Mission 02, Demolition Protocol, with JSON-driven sabotage progress, the existing feature checklist, Mission HUD, Mission Details, history, and save/load support.
- Registered and cached the Mission 02 definition for online and offline play without adding Mission-02-specific behavior to the generic Mission Engine.
- Added Mission 02 automated acceptance plus Mission 01 and Mission 04 regression coverage.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.2.0.

## v6.1.1

**Version 6.1.1 - Mobile Mission Status HUD**

- Hid the completed Mission HUD checkmark on phone-sized portrait and landscape viewports so the full `COMPLETE` label remains visible and centered.
- Preserved the checkmark on tablet and desktop layouts, along with the existing completed state, green styling, text size, and HUD tile sizing.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.1.1.

## v6.1.0

**Version 6.1.0 - Shifting Labyrinth Mission Engine**

- Implemented Mission 01, Shifting Labyrinth, with JSON-driven escape progress, dynamic roster-based targets, animated Auspex Calibration D3 rolls, Mission HUD, Mission Details, history, and save/load support.
- Extended the generic Mission Engine with safe dynamic target expressions and D3 dice while preserving Mission 04 behavior.
- Added Mission 01 automated acceptance and Mission 04 regression coverage.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.1.0.

## v6.0.0

**Version 6.0.0 - Mission Objective Engine**

- Released the data-driven Mission Objective Engine with Mission 04, Destroy Sarcophagus, as its original automated reference mission.
- Added compact Mission HUD and Mission Details interfaces, lifecycle-driven Ready-step repair, and objective progress that remains independent from battle victory.
- Added versioned mission-runtime persistence, legacy-save recovery, definition validation, accessible mission dialogs, and offline caching for the Mission 04 definition.
- Completed the Work Package 08 automated acceptance and release-readiness review; see `docs/mission_engine/FINAL_ACCEPTANCE.md` for the traceable results and known limitations.
- Updated visible, internal, cache-busting, and service-worker cache versions to v6.0.0.

## v5.8.1

**Version 5.8.1 - Simplified Firefight Activation Card**

- Removed the repeated initiative status banner from Firefight activation cards.
- Preserved activation titles, progress counters, instructions, and alternating activation behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.8.1.

## v5.8.0

**Version 5.8.0 - Persistence, Migration, and Versioning**

- Added an explicit integer save schema version and a sequential migration pipeline for legacy saves.
- Added defensive save validation, gameplay-state defaults, and safe removal of invalid roster references.
- Preserved unknown gameplay fields, rejected newer incompatible schemas without overwriting them, and left the original browser save untouched when loading or migration fails.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.8.0.

## v5.7.10

**Version 5.7.10 - Reinforcement Placement Confirmation**

- Removed the unnecessary hatchway text fields from reinforcement placement cards.
- Reinforcement placement checkboxes now directly record confirmation and control Strategy Phase completion.
- Preserved legacy hatchway values when normalizing existing saved games.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.10.

## v5.7.9

**Version 5.7.9 - Aggressive Defense Construct Messaging**

- Clarified that Aggressive Defense Construct inflicts retaliatory damage on the attacking operative.
- Included the attacking operative's name in both successful and no-damage results when available.
- Preserved the existing elimination banner and all combat rules, timing, damage, and wound behavior.
- Updated visible, internal, cache-busting, and service-worker cache versions to v5.7.9.

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
