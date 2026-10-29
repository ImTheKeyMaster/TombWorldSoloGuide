# Tomb World Battle Guide v10.0.206

## v10.0.206

### Experimental Fight Resolution duel layout

- **VS divider:** add a compact centered diamond VS badge between the two existing portrait/stat cards, with no change to combatant information or portrait positioning.
- **Horizontal exchange history:** swipe through numbered exchange cards in chronological order, each retaining its one or two action records and full damage/block details. Automatically scroll to the latest exchange on re-render.
- **Strike and Block:** arrange available choices as two side-by-side, visually distinct panels with compact option cards, preserved button semantics, and the existing confirm workflow. Explain unavailable Blocks as before.
- **Strictly Experimental Solo:** Standard Tomb and PvP continue using their original markup, vertical fight history, and Strike/Block presentation. No combat logic, save format, or dice changes.
- **PWA:** advance all shell/code/service-worker versions to 10.0.206.

## v10.0.205

### Require an explicit weapon choice before resolving any attack

- **No accidental first-weapon selection:** never convert the empty "Select a weapon..." option into index 0 when a player chooses Continue on a shooting or melee attack, including after previous actions in the same activation.
- **Defense in depth:** initialize Continue as disabled; enable it only with a valid target and weapon; revalidate both in the click handler before resolving weapon rules, deducting AP, or rolling dice.
- **Single-weapon operatives:** keep the existing locked-in, read-only weapon choice with an explicit index 0. Preserve Deathwatch Special Issue Ammunition, target rails, and Standard/Experimental flows.
- **PWA:** bump to 10.0.205 to refresh cached HTML, JavaScript, and service-worker assets without changing saved-game format.

## v10.0.204

### Offline-first cold start reliability on iPhone PWA

- **Immediate offline startup:** return already-cached HTML, JS, CSS, JSON and app shell resources before asking the network. Match versioned code exactly so previous JavaScript and new HTML are never combined. Retain historical completed offline caches until the replacement is fully prepared.
- **Poor connectivity:** cap new, uncached core resource fetch attempts rather than leaving requests pending indefinitely. A missing shell renders a dark standalone retry page; a missing script/data file is reported as a load error instead of blocking forever.
- **Visible loading and recovery:** render an inline, dark startup panel independently of external CSS/JS. If the application has not rendered within 9 seconds, offer Retry Loading and Export Saved Battle; no local saved game is deleted.
- **Nonblocking styling and updates:** load noncritical stylesheet without preventing the initial dark screen, register the service worker without waiting for the window load event, and defer large optional offline media downloads until after startup.
- **Bounded startup data:** initial mission/team/background manifest requests use deadlines and normal browser HTTP caching in addition to the PWA service worker. Failing fetches do not erase local saves.
- **Preservation:** Standard and Experimental, fight resolution, portraits, mission logic, save schema and all NPO/Imperial rules remain unchanged. All release/PWA asset versions advance together.

## v10.0.203

### Explain automatic Fight strikes in Experimental

- **Clarity before confirming:** when a selected Strike will leave only matching successes and the opponent has no successes, describe their automatic follow-up damage and whether it will eliminate the target.
- **Fight Result:** show a chronological breakdown of chosen and automatically resolved Strikes, including actual damage applied when the last Strike would otherwise exceed remaining wounds.
- **Combat rules unchanged:** keep the existing automatic-strike behavior, but add an optional `automatic` marker to Fight history, preserved by normal save/resume. The result breakdown is Experimental-only. Standard and PvP UI stay unchanged.
- **PWA:** advance to version 10.0.203 so both the app and cached assets refresh.

## v10.0.202

### Full Fight exchange history in Experimental

- **All exchanges:** keep every resolved action visible as numbered exchanges in the original sequence. Exchange groups contain two actions where available, including a final single-action group.
- **Compact mobile history:** keep the newest exchange highlighted and scroll the bounded history area to the latest entry; scroll upward to review earlier exchanges without pushing Fight choices off-screen.
- **Compatibility:** preserve the Standard/PvP history view, Block shield icons, action logic, stored Fight history, and existing save schema. Release/PWA cache v10.0.202.

## v10.0.201

### Experimental Fight Resolution exchange chronology

- **Chronological exchange order:** pair consecutive resolved actions from the beginning of a Fight, whether the NPO or the player acts first. Preserve actual action order from saved fight history, even on re-render and resume.
- **Exchange numbering:** display one numbered circle in the Last Exchange heading for the exchange, never a circle beside each action. Exchange 1 contains actions 1 and 2, Exchange 2 contains actions 3 and 4, and so on.
- **Block appearance:** use the exact half-filled shield icon from the available normal Block choice in the exchange display. Leave the crossed-out Block Unavailable icon untouched.
- **Isolation:** Standard and PvP remain unchanged; no Fight decision, dice, save schema, profile, or portrait changes. Release and PWA cache updated to v10.0.201.

## v10.0.200

### Experimental Fight Resolution block shield clarification

- **Experimental only:** display an unbroken white shield outline for a successful Block recorded in Last Exchange. The slash remains exclusively on the existing Block Unavailable action guidance icon.
- **Standard mode and Fight mechanics:** unchanged; all combat outcomes, saved games and miniature portraits are preserved.
- **PWA:** increment app and offline cache release to v10.0.200.

## v10.0.199

### Experimental-only Fight Resolution exchange timeline

- **Experimental mode:** replace the blended Last Exchange text with two compact, numbered player/NPO action cards, including Strike/Block icons and a concise damage or Block outcome. Use the established green accent for the player and white for the NPO, without introducing yellow or amber.
- **Action selection:** remove the numbered circles next to "Choose your action" and "Confirm your action" in Experimental mode. The exchange timeline keeps its 1/2 turn numbers.
- **Standard mode:** keep the existing Last Exchange rendering and numbered action headings unchanged. No combat mechanics, portraits, rules, save schema, or offline asset inventory changes.
- **PWA:** advance the application, asset cache URLs, and service-worker version to 10.0.199 to refresh the experimental styling.

## v10.0.198

### Follow-up corrections and Spectre specialist action support

- **Deathwatch:** enforce the either-two-Shoots-or-two-Fights restriction; require both shooting profiles to be in the special-weapon list for the second Shoot AP surcharge (or either to be a melta bomb); do not duplicate an already-present ammunition rule; and retain the selected Special Issue Ammunition modifiers in recorded combat summaries rather than replacing them with base weapon rules.
- **Spectre:** add guided Issue Mission (0AP), Medikit (0AP), and Load Weapon (1AP) with target selection and AP accounting; ensure Load Weapon's Charge/Dash/Shoot conflicts are enforced in both directions. Medikit heals up to the recorded 2D3 roll.
- **Spectre Elite Fieldcraft:** during a Solo NPO Engage-order activation, pause after the NPO action for an optional free Spectre Shoot, Dash or Reposition. Keep the suspended NPO activation and AP state intact; track once-per-NPO-activation, once-per-operative-turn and Fieldcraft point usage. Resolve range/movement and shooting on the tabletop and enter the NPO's remaining wounds, including any reanimation.
- **Joint Ops:** verified the exact bundled `Assets/Tomb-World-Mission-Pack.pdf` against the Standard NPO profiles and corrected Scarab attack fallback, Crawler twin gauss `Punishing` instead of `Severe`, Macrocyte Gauss scalpel/Tesla/Claws attack and damage values, and Aggressive Defence Construct's actual 2/3 damage on D3 rolls of 2/3. Punishing now resolves in both new and resumed combat, including multi-target attacks.
- **Competitive mechanic excluded from Solo:** removed `Expendable Construct` from the Joint Ops Macrocyte and prevented the competitive `A Ceaseless Scuttling` gambit from adding obligatory Solo reinforcements. The existing optional PvP gambit, official Joint Ops generation table, NPO AI, and selected Tomb World variants are preserved.
- **Preserved:** threat rules, mission data, portraits, Standard/Experimental modes, saved games and offline PWA cache behavior.
- **Still guided:** Deathwatch counteractions and ploy/equipment economy; Spectre Medic! reactive saves, Camo Cloaks cover saves and some conditional weapon abilities. The Guide does not infer unseen tabletop visibility or ranges.


## v10.0.197

### Official October 28 Kill Team mechanics and Joint Ops precedence

- **Joint Ops precedence:** retain the distinct Tomb World Joint Ops Necron NPO datacards, variant rules, mission tables, wound totals and AI; the competitive Canoptek Circle roster and obelisk matrix are not substituted. The competitive Dimensional Banishment clarification is already handled through target survival checking.
- **Deathwatch:** make Gravis optional (at most one); permit a second Shoot or a second Fight per activation; charge the correct extra AP for a second Shoot using qualifying weapons, with selected weapon names preserved in activation history. Add once-per-turn Special Issue Ammunition selection on the Shoot weapon screen (excluding melta bombs/universal grenades, and Blast on Torrent). Apply Aegis storm shield double-block capacity, Demolisher's Aggressive Force damage reduction and charged heavy-hammer Brutal/Ceaseless conditions. Publish complete faction-rule guidance for unautomated counteractions.
- **Spectre Squad:** constrain the Vox-Relay Beacon to its Signal action, expose a real 1AP Signal for the Beacon and Vox-Operator with the correct respective 6-inch or visibility rules, apply +1 player APL until the recipient's next activation and persist it through save/load. Provide a tabletop-confirmed 0AP Scout Terrain Operate Hatch discount once per activation (when a Guide has been selected). Correct the Vox-Operator's Signal wording and the Ready Step guidance for games beyond four turning points.
- **Core / Tomb World:** correct the previously overgeneralized Tomb World wall cover/obscuring reference. Only wall corners and ends intervene unless the active operative has passed the wall. Clarify when an elevated rampart intervenes under the October Core Rules.
- Preserves Standard and Experimental, portraits, weapon-selection single-choice UX, existing mission logic and save key.
- **Still guided, not automated:** Spectre Elite Fieldcraft interruptions and other specialist free actions; Deathwatch counteraction combinations, equipment selections and full ploy accounting. Never silently resolve tabletop visibility, range or positioning.

## v10.0.196

### Restore uncluttered weapon-selection dialogs

- Remove the October 2026 Terrain & cover dropdown/disclosure from both player and Necron shooting weapon-selection screens in Standard and Experimental.
- Delete its unused markup helper and CSS. Keep October 28 Tomb World terrain clarifications in How It Works and the in-game Help reference.
- Preserve weapon selection, single-profile read-only labels, weapon rules, guidance, Cancel/Continue, combat state, saves and preloading.

## v10.0.195

### October 28 Kill Team terrain guidance

- Update the How It Works and in-game Help references: Tomb World wall pieces including pillars follow normal terrain rules; Vantage Point cover depends on the rampart's Light/Heavy category and targeting line; ladders cannot extend a Reposition beyond the ladder's permitted span.
- Show an optional collapsed Terrain & cover reference at Player and Necron shooting weapon selection without changing existing weapon controls or increasing the default modal height significantly.
- Link to the official Games Workshop October 28 announcement for current terrain diagrams. Tabletop geometry remains a player decision, not an automatically inferred legality or saving throw.
- All Deathwatch, Canoptek Circle and Spectre Squad unit/team errata remain on hold until verified against the October 28 PDFs.
- No changes to movement calculations, cover saves, targets, weapon rules, combat resolution, mission logic, NPO AI decisions, saved state, portraits or preloading.

## v10.0.194

### Show a fixed Necron weapon when only one profile is available

- On the Tomb UI Necron Select Weapon screen, replace the iOS/browser dropdown with a read-only weapon name when exactly one profile is available.
- Preserve the existing selection index in a hidden input so guidance, weapon rules, confirmation, back navigation and saved attack drafts continue to use the same code path.
- Keep the dropdown and dynamic guidance updates for multiple profiles. Standard and Experimental share this behavior.
- Reuse the already approved read-only weapon styling from player combat; leave gameplay, portraits, preloading, settings and saved state unchanged.

## v10.0.193

### Reduce Death Korps shooting portrait zoom by 20%

- Reduce only Death Korps artwork in Blast/Torrent multi-target shooting result cards and in Resolve Combat attack/defense dice cards from 1.3× to 1.04× image zoom, exactly 20% smaller.
- Preserve portrait placement, existing fade/contrast, text, dice, and combat mechanics. The parent card dimensions and baseline positioning are unchanged.
- Leave Deathwatch and Necron artwork at its existing zoom, as well as Fight Result, Fight Roll and Activation portraits. No changes to the shared renderer or saved state.
- Apply in both Standard and Experimental Tomb UI, and update the offline PWA assets/cache version.

## v10.0.192

### Shift Fight Result portraits left to show more of each miniature

- Move both Fight Result miniature/base centres 12% of their card width leftward, matching the approved visual mockup so more of each miniature and its right-side equipment are visible.
- Keep physical miniature scale, the taller model's 90% height cap, both bases aligned 2px above the card bottoms, fade, text readability, and unchanged card layout.
- Limit the horizontal shift to Fight Result in both Standard and Experimental. Leave Fight Resolution, Activation, game state, and image assets untouched.
- Apply the same horizontal adjustment to fallback Fight Result CSS if silhouette measurement is unavailable; update the offline PWA version to v10.0.192.

## v10.0.191

### Table-accurate miniature scaling in Fight cards

- Use a shared runtime canvas measurement of each native portrait's visible silhouette and the widest opaque horizontal span in the base band, instead of fitting incompatible PNG/WebP canvas dimensions into matching CSS boxes.
- Pair participants using real-world miniature base diameters (e.g. 25mm Death Korps and 28mm Canoptek Macrocyte Warrior from NPO metadata). Compute a single common pixels-per-mm scale based on their measured figure-to-base proportions. Set the taller visible figure to 90% of the card height; retain relative height and base-width ratios for the other model.
- Align the bottoms of the physical miniature silhouettes 2px above the bottom of the cards. Center miniature bases, not opaque bounding boxes. Preserve card text layering, masks, brightness, and bottom-aligned sizing fallback when canvas is not available.
- Apply only in Tomb Fight Resolution and Fight Result; Standard and Experimental share the same flow. Activation, Fight Roll, image preloading, roster and gameplay persistence remain unchanged.

## v10.0.190

### Match Death Korps to Necron miniature scale in Fight cards

- Remove the extra Death Korps width and right offset introduced in v10.0.189 on Fight Result, restoring the same 100%/190px maximum as the Necron.
- Remove the Death Korps-only 118px/76% size boost in Fight Resolution so it inherits the Necron's normal 98px/68% frame, including the narrow-screen responsive scaling.
- Preserve both miniatures' full-height, contained and bottom-aligned artwork, their card text overlays, all portrait mappings and preloading, and the existing Death Korps Activation framing.
- Standard and Experimental Tomb modes share the fix; combat mechanics and persisted state are unchanged.

## v10.0.189

### Restore large bottom-aligned Fight miniature portraits

- Restore the Necron's formerly larger Fight Result cutout width (up to 190px or full card width) while keeping the shared bottom baseline, contained head and readable names/wounds/damage.
- Slightly enlarge Death Korps cutouts in Fight Result and Fight Resolution without zoom-clipping. Remove the v10.0.188 per-faction top insets that made them smaller.
- Use one bottom-anchored, full-height native-image styling rule for both Fight surfaces and all factions. Preserve the already unified portrait renderer, faction mappings, green Deathwatch brightness, preloading and the complete Death Korps Activation framing from v10.0.185.
- Standard and Experimental share the same Tomb Fight screens. No gameplay state, save schema, or other layouts changed.

## v10.0.188

### Position only Death Korps miniature cutouts lower in Fight views

- Correct the Death Korps model framing in Fight Resolution and Fight Result: reduce the portrait artwork's effective height slightly and inset it from the top so the head is fully visible while the base stays aligned to the bottom of its card.
- Leave Necron and Deathwatch miniature positions, image sizing, and fading exactly as approved in v10.0.187. No shared image renderer changes.
- Preserve v10.0.185 Death Korps activation zoom, the Fight Result card layout, combat rules, dice, text, and save state.

## v10.0.187

### Fit and align both Fight Result miniatures

- Match Death Korps and Necron miniature bases along the bottom of their respective Fight Result cards, keeping the entire figure in view rather than clipping its head.
- Limit decorative portrait width and soften the edge nearest the text, so operative names, wounds, and damage remain readable without hiding either miniature.
- Preserve the approved Fight Resolution base alignment, reduced Death Korps Activation zoom, native shared image renderer, Standard/Experimental modes, and all combat state and logic.

## v10.0.186

### Align miniature bases and reveal full Trooper portrait in Fight Resolution

- Bottom-anchor both the player and Necron model portraits in the compact Tomb Fight Resolution participant cards, rather than offsetting them above the card. This prevents the Death Korps Trooper's head from being cropped by the upper edge and visually aligns model bases.
- Use contain-fit and bottom-aligned image positioning inside each portrait surface, preserving each faction's existing fade, opacity, and masking, as well as dice, wounds, status badges, and text layout.
- Keep the already-approved v10.0.185 **smaller Death Korps Activation portrait** unchanged, along with the unified native PNG/WebP image renderer, Classic mode, saved game state and all combat logic.

## v10.0.185

### Show the complete Death Korps miniature on activation

- Correct the v10.0.184 Death Korps activation zoom increase, which made the model more prominent but cropped more of the miniature. The goal is to **zoom out**, showing more of the figure and its base like the Necron activation example.
- Reduce Death Korps activation photo widths to 135% (default), 140% (phone), and 145% (narrow phone), previously 185% / 195% / 200%. Position the smaller photo slightly inside the right edge.
- Change only Death Korps activation framing. Preserve approved portrait masks, transparency, overlap behind Completed Actions or Movement, all other faction sizes, the shared native image renderer, game rules and saved state.

## v10.0.184

### Match Death Korps activation portrait zoom to Necron activation

- Increase the Death Korps activation photograph size only, using responsive widths of 185% (desktop), 195% (phone), and 200% (narrow phone), with adjusted top/right positioning. This gives the model greater visual prominence, closer to the approved Necron activation portrait.
- Preserve portrait fade, mask, layering behind Completed Actions and Movement, and the unified native image renderer. Do not alter Deathwatch or Necron zoom, combat portraits, roster cards, rules, dice, or saved game state.

## v10.0.183

### Use one resilient portrait renderer for Deathwatch, Death Korps, and Necrons

- All three factions now use one native HTML image renderer across activation, Fight Roll, combat summaries, and roster surfaces, removing embedded external SVG image dependencies that may stop painting when iOS suspends the PWA.
- Keep faction-specific asset lookup separate: Death Korps and Deathwatch use PNG photos; Necrons use supplied, pre-colored transparent WebPs (with existing versioned URLs and model-specific selection).
- Preserve original file mappings, preloading, approved fade/mask, brightness, sizing and framing, including Death Korps overlap behind Movement/Completed Actions, Deathwatch contrast, and Necron crops. The native IMG uses `object-fit: contain` with faction-specific positioning.
- Retain SVG resume recovery for any other SVG artwork. No combat mechanics, saved data, navigation, or operative state is modified.
- Add shared native-renderer regression tests for all factions, Trooper 3 activation, plasma Gunner Fight Roll and existing roster/combat paths.

## v10.0.181

### Repaint SVG portraits after extended iOS PWA suspension

- Address iOS WebKit occasionally showing an empty operative portrait after resuming a standalone PWA, even though the rest of the Fight Roll card and its dice remain visible.
- Preserve the fast, debounced 100 ms SVG image-node refresh and follow it with a 1500 ms rebuild of SVG paint surfaces, which can be necessary after WebKit restores backgrounded GPU/compositing resources.
- Cancel both repaint phases if the app returns to the background; support visibility changes, window focus, and back/forward cache restoration without affecting fight results, state persistence, current screen, or scroll position.
- Keep existing portrait coverage limited to factions with supplied miniature artwork. Death Korps and Deathwatch support Fight portraits; teams without supplied Fight portraits are not given fictitious artwork.
- Add resume/repaint regression coverage, including shared SVG roots and repeated foreground/background cycles.

## v10.0.180

### Promote Action First Fight and Block-unavailable explanations to Standard

- Promote the approved Action First Fight Resolution choices, two-step Choose/Confirm interaction, Strike advice, and BLOCK UNAVAILABLE explanations from Experimental into Standard Tomb UI.
- Explain when no legal Block option exists because the opponent retains only critical successes, an enemy Brutal weapon requires critical Blocks, or there are no unresolved enemy successes to cancel (noting the Guide's no-target Block limitation).
- Preserve legal Block and Shield choices, existing dice, turn logic, saved fights and game mechanics. Classic retains its previous Fight Resolution layout and behavior.
- Keep the Experimental toggle available for future previews, without changing the approved Standard/Experimental Fight UX.

## v10.0.179

### Experimental: explain all missing Block choices in Fight Resolution

- Keep the existing muted shield-and-slash BLOCK UNAVAILABLE notice and show it whenever no legal Block can be offered in the Experimental action-first Fight screen.
- Explain Brutal when an enemy Brutal weapon permits only critical Blocks and the active operative has none, including when the enemy retains only critical successes.
- Explain the ordinary normal-versus-critical restriction when the enemy has only critical successes and the active operative only normal successes.
- Explain when the opponent has no unresolved successes to cancel, accurately noting that tabletop rules still permit blocking without a target, whereas the Guide only offers target-canceling Blocks.
- Never show the notice when legal Blocks are available, when the active operative has no successes, or as a replacement for normal PVP/NPO resolution. Preserve Strike/Block mechanics, dice, turn handling and Standard/Classic UI.

## v10.0.178

### Experimental: keep the BLOCK UNAVAILABLE icon's diagonal inside the shield

- Clip the diagonal slash to the existing shield outline, preventing the line from extending beyond the shield while retaining the original shape and muted icon styling.
- Leave the Experimental Brutal notice conditions, action choices, fight logic, Standard and Classic screens unchanged.
- Refresh PWA asset and offline cache versions to v10.0.178.


## v10.0.177

### Experimental: explain when Brutal prevents a Block

- In Experimental Fight Resolution, show a compact noninteractive "BLOCK UNAVAILABLE" note when the opponent's Brutal melee weapon prevents your remaining normal success from blocking an enemy normal success.
- Identify the actual opponent weapon in the note, explain the critical-success requirement, and clarify that no critical successes remain.
- Do not show the note when Block is legal, the opponent has no unresolved normal successes, or the lack of a Block is unrelated to Brutal.
- Leave Standard and Classic layouts, action-selection and confirmation, the shared Fight engine, and automatic solo NPO choices unchanged.
- Refresh the PWA shell and offline cache to v10.0.177.



## v10.0.176

### Experimental: streamline Fight Resolution choices

- Remove the redundant Your Turn heading, instruction line, dynamic action-summary paragraph, and footnote from only the new Experimental Fight screen, while keeping the active model cards and the Confirm button.
- Use filled sword and shield silhouettes matching the original action-first mockup rather than the thin improvised spear/shield outlines.
- Give concise conditional tactical guidance directly in Strike cards whenever normal and critical successes both remain. Describe preserving the critical for a later Block as a possibility, not a guarantee of another turn.
- Shorten Strike copy to Deal N damage because the opponent is identified in the header cards.
- Keep Standard, Classic, automated NPO actions, Shield targeting, fight calculations, and battle result behavior untouched.
- Refresh app and offline-cache versions to v10.0.176.


## v10.0.175

### Experimental: Action First Fight Resolution

- In **Experimental** only, replace the Fight Resolution decision area with large vertical STRIKE and BLOCK choices, based on the selected first mockup.
- Group legal Critical and Normal Success actions by STRIKE and BLOCK, with explicit damage and the enemy success that a Block cancels. Never ask the human to select the NPO's decision.
- Require selecting exactly one action and confirming before spending a success. The existing automatic solo NPO decision engine and alternating turn rules are unchanged.
- Preserve Shield target selection, fight history, portraits, active participant and wound counters, and no-block scenarios.
- Standard and Classic remain unchanged. Experimental is enabled using the app's version-label toggle (seven taps).
- Refresh the service-worker app shell and assets to v10.0.175.


## v10.0.174

### Clarify ownership of personal miniature photographs in About

- Add a dedicated Miniature Photography section to the About page explaining that the miniature photos feature the creator's personally owned models and independently produced photography, not official Games Workshop product photographs.
- Affirm that the physical miniatures and original photography do not transfer any copyright, trademark, design, or character rights belonging to Games Workshop or other rights holders.
- Preserve the Games Workshop disclaimer, other About sections, navigation, privacy and gameplay. Update the historic IP asset audit with a dated author-provided provenance clarification without expanding it to maps, backgrounds, or other imagery.
- Refresh app shell, service-worker cache, and version labels to v10.0.174.

## v10.0.173

### Promote approved elimination styling to Standard

- Make the approved red outline and prominent uppercase ELIMINATED label standard on Fight Result participants, eliminated Defense Dice cards, and chained/multi-target attack summaries in Tomb UI.
- Keep the eliminated defender's border on the Defense Dice card, not the surrounding shooting/combat result; retain neutral dark card backgrounds without the old badge or redundant elimination banner.
- Retain an elimination label for manually recorded tabletop resolution where no Defense Dice card is rendered.
- Preserve existing Classic presentation, combat mechanics, dice animation, portraits, wounds, saves, and battle history. Standard and Experimental now share the approved appearance; Experimental remains available for future enhancements.

## v10.0.172

### Experimental: mark eliminated defenders within their Defense Dice card

- For shared automatic shooting/combat resolution, apply the red elimination border and prominent ELIMINATED text to the defeated defender's Defense Dice card, matching Fight Result participant cards.
- Remove the red border from the entire combat resolution section; keep the attack dice card, rules applied, stats, and outer result panel neutral.
- When an attack uses tabletop-recorded results without a Defense Dice card, retain the elimination text in the neutral resolution summary rather than losing the status.
- Keep Standard and Classic behavior unchanged, including original elimination banners; preserve Fight Result, multi-target cards, portraits, dice animations, and game state.

## v10.0.171

### Preview consistent elimination cards in Experimental mode

- Experimental Fight Result, Resolve Combat, and chained/multi-target attack summary cards now show a thin red outline with a prominent all-caps ELIMINATED label inside the affected card.
- Remove the separate elimination banner/pill on Experimental combat screens and the small eliminated badge on Experimental multi-target summaries.
- Keep the original dark card fill instead of the red-tinted eliminated background. Retain damage, wounds, dice, portraits, accessibility and game progression.
- Standard and Classic keep their pre-existing elimination presentation; the new preview requires the Experimental toggle.

## v10.0.170

### Restore SVG portraits when the iOS PWA resumes

- Repaint external SVG image elements after returning from background, restoring operative portraits without rotating the phone.
- Listen for visibility changes, back/forward cache restores, and window focus; debounce foreground events and skip work while hidden.
- Replace only decorative SVG image nodes; preserve active activation/combat state, AP, scroll position, user inputs, portrait styling, image URLs, and offline resources.
- Include a foreground/background regression harness. Standard and Experimental modes share the fix.

## v10.0.169

### Promote approved Deathwatch green portraits and remove obsolete assets

- Use the 11 already-green cutouts from `Assets/Images/TombUI/Deathwatch/` for every Deathwatch operative in Standard and Experimental, across roster, activation, shooting, fight, and multi-target screens.
- Retain the approved compact-card opacity (0.52 for Fight Roll/Result and shooting dice; 0.38 for Fight Resolution, 0.36 / 0.34 on narrow devices), with no added brightness filter and with original masks/framing.
- Remove the old `DeathwatchRoster` / `DeathwatchActivation` WebPs and Sergeant SVG, obsolete SVG grayscale/chroma-key color conversion, experimental artwork gate and old cache references. Keep the original user-supplied PNG filenames unchanged.
- Preserve operative IDs, roster composition, combat mechanics, persistence, image warmup/offline behavior and independent Experimental toggle. Refresh the app and PWA cache to V10.0.169.

## v10.0.168

### Calibrate Experimental Deathwatch combat portraits against Necron artwork

- Remove the extra brightness/contrast filter applied to supplied green Deathwatch PNGs in compact combat cards.
- Tune their alpha to better match neighboring Necron portraits: 0.52 in shooting dice and Fight Roll/Result cards, and 0.38 in compact Fight Resolution cards (slightly lower on narrow phones).
- Preserve visual framing, fade masks, overlay text, roster/selection/activation portraits, Standard Mode rendering and all non-Deathwatch artwork.
- No changes to operative data, combat decisions or saved game state. Refresh app and PWA asset cache to V10.0.168.

## v10.0.167

### Brighten supplied Deathwatch portraits in Experimental combat cards

- Give the supplied green Deathwatch PNG portraits higher contrast and opacity in Shooting Attack/Defense dice cards, Fight Roll/Result cards and compact Fight Resolution participant cards, only when Experimental Mode is enabled.
- Preserve the approved portrait framing, masks, text layering and interaction, and keep the roster selection, detail and activation portraits unchanged.
- Standard Mode, other Kill Teams, Necron portraits and Classic UI continue using the original rendering. No combat mechanics or save formats change.
- Update app and PWA cache version to V10.0.167.

## v10.0.166

### Preview supplied green Deathwatch portraits in Experimental Mode

- Experimental Mode uses the 11 newly supplied transparent green portraits from `Assets/Images/TombUI/Deathwatch/` in the operative roster rail, detail selection, activation, combat/Fight, and multi-target results, without the older SVG green-key filter.
- Match the supplied `Deathwatch_headtake.png` and `Deathwatch_horder-slayer.png` to the existing `headtaker` and `horde-slayer` operative IDs without changing their rules or names.
- Standard Mode retains the original DeathwatchRoster and DeathwatchActivation photos and green SVG treatment, including the existing Sergeant SVG. The old folders remain in place for a later promotion decision.
- Warm the appropriate portrait set when Deathwatch is selected. Precache the 11 new preview portraits for offline use. Preserve existing Death Korps, Necron, gameplay, state and navigation behavior.
- Release V10.0.166 with the independent Experimental Mode toggle.

## v10.0.165

### Promote Death Korps miniature photos to Standard Mode

- Promote the approved Experimental portrait associations for Gunner (Grenade Launcher, Meltagun, Plasma Gun), Medic, Sniper, Troopers 3/4, and alternate Vox-Operator to both Standard and Experimental modes.
- Retain the corrected Gunner (Flamer) filename and other existing portraits. Keep the fifth Trooper photograph registered for a future operative identity without changing roster rules.
- Continue using the same portrait lookup for roster, activation, combat and image preloading; preserve combat mechanics, game state and Back/resume behavior.
- Keep the independent Experimental toggle available for future changes. Refresh version and PWA cache to V10.0.165.

## v10.0.164

### Preview additional Death Korps miniature photos in Experimental Mode

- Associate new Gunner (Grenade Launcher, Meltagun, Plasma Gun), Medic, Sniper and Trooper 3/4 photographs with their operative IDs when Experimental Mode is enabled.
- Preview the alternate Vox-Operator image in Experimental Mode. Register the fifth Trooper photograph for a future `trooper-5` identity without adding an operative or changing roster rules.
- Correct the renamed Gunner (Flamer) image path in both modes, retaining all other Standard portrait assignments.
- Pre-cache every referenced Death Korps image for offline use. Preserve preloading, combat, activation, save state and navigation behavior.
- Update app shell and service-worker cache to V10.0.164.

## v10.0.163

### Promote Rules Applied shooting feedback to Standard

- Promote the approved compact **RULES APPLIED** shooting-combat summary from Experimental to the Standard Tomb UI, keeping the same look and actual-effects-only logic.
- Only show verified changes to dice, successful attacks and damage from Severe, Rending, Lethal, Accurate, Balanced/Ceaseless, Piercing/Piercing Crits and Devastating; no panel when no rule changed anything.
- Preserve accurate result handling for physical dice records, no-defense-roll Devastating incapacitations, and unchanged Classic UI and melee.
- Keep the Severe conversion note consolidated into the rules-applied panel instead of duplicating it under attack dice.
- Leave the independent Experimental Mode toggle available for future enhancements.
- Update app version and offline cache to V10.0.163.

## v10.0.162

### Experimental shooting results: Rules Applied

- Experimental Tomb UI shows a concise **RULES APPLIED** panel on automated shooting results when actual dice or damage prove a weapon rule had an effect; otherwise no panel appears.
- Display confirmed Severe and Rending critical conversions, Lethal critical thresholds, Accurate retained successes, Balanced/Ceaseless rerolls, the actual Piercing/Piercing Crits defense-dice reduction, and Devastating immediate damage.
- Do not infer effects from the weapon's rule list alone: Piercing Crits only credits greater reductions actually used, Devastating incapacitations do not falsely credit skipped defense rolls, and physically recorded combat does not fabricate rule applications.
- In Experimental Mode, move the existing Severe note into the applied-effects panel rather than repeating it beneath the dice. Keep elimination, damage, wound calculations, and triggered event messages exactly as before.
- Standard Mode, Classic UI, weapon guidance/selection, melee combat, and game-state mechanics stay unchanged. Experimental remains opt-in.
- Refresh PWA cache and assets for V10.0.162.

## v10.0.161

### Promote Necron roster re-roll to Standard

- Offer the approved subtle **Re-roll roster** action in both Standard and Experimental Tomb setup flows, on Deploy Kill Teams when one or more starting Necrons are selected for deployment.
- Keep the action completely hidden and inactive for missions with no starting Necrons and after the battle begins.
- Re-roll the legal Necron roster and starting deployment dice, reset Necron deployment confirmation, and preserve mission, player roster/deployment, optional rules and the previous force on generation failure.
- Preserve the independent Experimental Mode toggle for future features, without affecting this now-standard functionality.
- Refresh app and offline assets to V10.0.161.

## v10.0.160

### Refine Experimental Necron roster re-roll

- Only offer the Experimental Necron re-roll when the selected mission actually starts with deployed Necrons. Missions showing **Starting Necrons: None** have no re-roll action.
- Enforce the same safeguard in the re-roll handler, so a hidden control cannot accidentally regenerate a roster for missions without starting Necrons.
- Replace the prominent full-width green re-roll button and explanatory paragraph with a subtle, right-aligned, compact text action beneath the starting roster. Retain a usable touch target and an accessible explanation.
- Keep Standard Mode unchanged, retain the option for applicable missions and preserve all game setup information and the earlier re-roll failure recovery.
- Bump PWA shell and cache to V10.0.160.

## v10.0.159

### Experimental Necron roster re-roll during setup

- In Experimental Mode, the Deploy Kill Teams step offers Re-roll Necron Roster. This generates a fresh legal Necron pool plus a new mission starting-deployment dice roll, retaining the selected mission, player roster, and optional rules.
- Re-roll discards the former Necron roster and its starting-placement confirmation. Other board and player deployment checkboxes are retained, and the new deployment must be confirmed before continuing.
- Reset variant-specific generated roster replacement transactions on each re-roll, so replacement decisions are fresh; preserve the previous complete roster and setup state if generation fails.
- Only allow the action while on the setup deployment step with Experimental Mode enabled. Standard Mode has no re-roll control and is unchanged. Changing Experimental Mode on that step refreshes the control without restarting setup.
- App shell and offline cache version incremented to v10.0.159.

## v10.0.158

### Promote weapon rules on selection to Standard

- The approved weapon-selection layout is now shared by Standard and Experimental Tomb UI. Necron weapon profile choices show live Weapon Guidance and Weapon Rules, and shooting results focus on dice, damage, and rule effects instead of repeating the full rule list.
- A single-profile shooting weapon with rules still has a selection step to review those rules before rolling, for both Player and Necron flows. Rule-free single-profile attacks can continue directly to combat.
- Preserve Classic presentation, selected weapons, shooting mechanics, Blast/Torrent secondary targets, navigation, persistence, and the independent Experimental switch for future enhancements.
- Refresh PWA resources and offline cache to v10.0.158.

## v10.0.157

### Preview Weapon Rules alongside Weapon Guidance

- Experimental Mode shows profile-specific Weapon Rules beneath Weapon Guidance on the Necron Select Weapon dialog; both update as the selected profile changes.
- Experimental shooting combat dice/results no longer repeat the full Weapon Rules list, for Necron or Player attacks; actual rule effects and damage remain visible during resolution.
- Show the Select Weapon step for single-profile Necron attacks with rules even when there is no guidance, and retain the Player weapon-selection step for single-weapon shooting attacks with rules, so rules are always accessible before dice.
- Standard Mode and classic UI retain their existing weapon selection, guidance and combat rules screens; save data and rules mechanics are unchanged.
- Update app shell/offline cache to V10.0.157.

## v10.0.156

### Skip empty Blast/Torrent secondary-target checks

- Skip the secondary-target checklist automatically when no other living, in-play operative can be selected. Continue directly to the primary target's combat dice in both player and NPO shooting flows.
- Preserve normal tabletop checks and selection whenever additional candidates exist, including friendly operatives for Blast.
- Keep primary-target identity, Seek Light answers, rule-resolution persistence, and existing combat/damage sequencing intact.
- Update the PWA shell and offline cache to V10.0.156.

## v10.0.155

### Skip redundant pre-roll combat confirmation in Standard Mode

- After selecting a Necron shooting profile, continue immediately to any necessary Blast/Torrent target or Seek Light check, then roll combat dice, without an unchanged intermediate Resolve Combat confirmation.
- Display event-specific room questions on a small, dedicated Attack conditions step only when genuinely required, preserving their answers for the attack.
- Preserve the true combat dice/results screen, existing damage and multi-target order, Classic UI, Back navigation, and saved-game compatibility.
- Update the offline cache and displayed version to V10.0.155.


## v10.0.154

### Consistent compact progress for all multi-target attacks

- Standard Tomb UI shows a green `Target X of Y` label above the combat dice for Blast, Torrent, Sweeping, and any other attack with two or more selected targets.
- Remove the redundant bottom-of-screen weapon/attacker/target details during these attacks for both Player and NPO resolution, in Standard and Experimental modes.
- Suppress malformed `Target 1 of undefined` footers when Blast or Torrent has only one confirmed target or a saved sequence has no known target count.
- Preserve the classic presentation, dice scrolling, saved-game format, combat rules, and damage/activation processing. Refresh the offline cache to V10.0.154.

## v10.0.153

### Promote current Experimental combat improvements to Standard Mode

- Make compact portrait Fight Resolution, text Crits/Normal success counters, clearer action buttons and collapsible help the default Tomb UI experience in both Standard and Experimental modes.
- Make mobile shooting Dice/Results-first order and auto-scroll-to-animation standard, keeping desktop layouts unchanged.
- Make the Necron Select Weapon step with live profile-specific guidance and safe Torrent/Blast Back handling standard.
- Keep the compact green Sweeping Target X of Y counter above shooting dice for multi-target attacks in both modes.
- Preserve the Experimental switch, separate storage key and independent playground for future work; existing features no longer depend on the switch.
- No game-rule, damage, action/activation, saved-game schema or portrait asset changes. Refresh app and offline cache to V10.0.153.

## v10.0.152

### Experimental Sweeping target progress above shooting dice

- During multi-target Sweeping shooting attacks, replace the verbose bottom-of-screen attack progress (weapon heading, target name and wounds) with a concise green `Target X of Y` label directly above the dice.
- Keep the count correct as the attack advances to each secondary target, including resumed multi-target sequences. Reuse the existing sequence index and total count without changing combat mechanics.
- Apply only in Experimental Tomb UI. Standard Mode and non-Sweeping Blast/Torrent progress remain unchanged.
- Preserve miniature portraits, damage calculations, attack sequencing, saved-game compatibility and the V10.0.149 dice-animation visibility logic.

## v10.0.151

### Experimental Torrent and Blast Back navigation

- Back from a pre-roll Torrent/Blast (or Seek Light) tabletop check now returns to the Experimental Necron weapon-selection step, preserving the selected weapon profile.
- Clear only unconfirmed secondary-target/visibility answers before revisiting weapon selection, avoiding an accidental multi-target profile lock. Preserve completed attacks and confirmed multi-target outcomes.
- Allow a Back path for guided single-profile attacks even when the initial weapon-selection step was automatically skipped.
- Keep Standard Mode navigation, combat mechanics, save structure, and dice behavior unchanged.
- Update app and offline cache versions to V10.0.151.

## v10.0.150

### Experimental Necron weapon guidance at selection

- Move Necron Weapon Guidance from Resolve Combat to a new weapon-selection step in Experimental Mode. Update that guidance immediately when the weapon profile changes, including profile-specific guidance and general abilities.
- Show the selection step for multi-profile Necron shooting attacks and single-profile attacks with relevant guidance. Keep weapon choices visible before dice roll and retain access to Weapon Rules during resolution.
- Preserve existing player weapon-selection summaries, special-rule checks, saved combat drafts, and all Standard Mode screens and behavior.
- Keep dice-first mobile presentation, portrait artwork, combat mechanics, and cache compatibility unchanged.

## v10.0.149

### Experimental mobile Resolve Combat dice-first presentation

- On mobile portrait and narrow touch landscape screens in Experimental Mode, display required weapon choices first, followed by animated Attack Dice, Defense Dice, combat results, and then weapon guidance/rules.
- Bring the currently animating dice card into the visible portion of the scrolling combat dialog before rendering its first animation frame, including attack, defense, and result animations.
- Preserve desktop and Standard Mode ordering, and leave gameplay mechanics, dice timing, sound, persistence, portraits, and saved-game behavior unchanged.
- Update the app shell and service-worker cache to V10.0.149.

## v10.0.148

### Experimental Fight Resolution success-count labels

- Replace the star and dot glyphs in Experimental Fight Resolution combatant cards with plain-text `Crits` and `Normal` labels for remaining successes.
- Keep card positions, portrait assets, count calculations, accessibility labels, and all action handlers unchanged.
- Preserve the original Standard Mode Fight Resolution appearance and combat mechanics.
- Refresh the application shell and offline cache to V10.0.148.

## v10.0.147

### Experimental Fight Resolution narrow-screen layout hardening

- Keep the two Experimental combatant portraits and status cards side by side on narrow iPhones (including 320px layouts). The existing Standard Mode one-column fallback remains unchanged.
- Reduce narrow-screen padding, miniature overlays and success-count spacing without changing underlying images, action buttons or combat mechanics.
- Extend the existing Experimental Fight Resolution regression test with Strike, Block and Shield dispatch checks and CSS isolation assertions.
- Refresh the application and offline cache version consistently.

## v10.0.146

### Experimental compact Fight Resolution preview

- Experimental Mode now has compact combatant cards showing the acting operative, wounds, remaining critical/normal successes and existing Deathwatch, Death Korps, and Necron miniature portraits.
- Reduce repeated Fight Resolution instructions to a compact action prompt. Full turn-taking explanation is available under an optional details disclosure.
- Preserve the original Standard Mode Fight Resolution HTML exactly, including its instructions and actions. No changes to damage, Strike, Block, shield, automated responses, dice, or saved fight state.
- Keep all new CSS isolated to the experimental Fight Resolution wrapper and experimental UI switch. Other fight screens and normal mode remain unchanged.
- Refresh the app shell and offline cache to V10.0.146.

## v10.0.145

### Finish Death Korps miniature portrait loading during new-game setup

- Team selection already started loading its Death Korps photographs, but did not wait for network downloads or decoding before enabling Build Roster. On a newly installed device the first activation could still display an empty miniature for several seconds.
- Track a single image and readiness promise per unique Death Korps photo, retaining and reusing completed images across roster rails, combat, and activation screens.
- While setting up a new game, wait for images to load and decode before unlocking the roster step; cap the wait at 12 seconds to avoid trapping players if assets are unavailable.
- Existing saves continue to open without a new setup delay; failed assets can be retried and changing teams cancels stale selection outcomes.
- Preserve the existing UI, artwork, gameplay, offline behavior, and V10.0.144 loadout naming.

## v10.0.144

### Player operative loadout names

- Show roster numbers before parenthesized loadouts across Kill Teams, for example Gunner 3 (Meltagun), without changing operative IDs or saved roster numbering.
- Preserve unnumbered variants, existing numbered Troopers and Warriors, and non-variant operative names.

## v10.0.143

### General dialog safe-area scrolling on iPhone

- Keep general Tomb dialogs, including Game Menu, inside the iPhone status-bar and home-indicator safe areas with a single native scrolling region.
- Prevent the background document from competing for touch scrolling while the main dialog is open.
- Preserve all card, text, button, artwork, and screen layout sizing; leave the separate Deathwatch and Death Korps activation dialog framing and scrolling rules unchanged.
- Continue using the original green styling and dialog backdrop, without introducing a gradient or mask on content.
- Release V10.0.143 consistently in the app, index assets, and offline service worker.

## v10.0.142

### Reliable iPhone offline startup and service-worker updates

- Precache the HTML, JavaScript, CSS, manifests, and game definitions as the required startup bundle. Prepare larger optional portraits, maps, icons, audio, and backgrounds after installation, rather than allowing one large asset to abort the offline app update.
- Preserve older offline caches during an update and reuse their media and fallback files when the network is unavailable. Avoid copying large offline audio caches during service-worker activation.
- Keep offline-preparation progress reporting and retries; do not alter save storage, gameplay, activation screens, or miniature artwork.
- Update the app shell and cache version consistently to v10.0.142.

## v10.0.141

### NPO shooting and fighting target selection rail

- Replace the dropdown with the existing horizontally scrollable portrait target rail when a Necron selects a Death Korps or Deathwatch operative to Shoot or Fight.
- Reuse the correct miniature photographs and artwork for the selected team, with live wound totals, selected styling and accessible keyboard/arrow controls.
- Preserve the original target priority instructions, eligibility validation, confirmation behavior, saved target selections, and combat resolution. Keep dropdowns for unsupported teams and layouts.
- Apply the same behavior in Standard and Experimental Tomb modes, and update the release and offline cache to v10.0.141.

## v10.0.140

### Match Death Korps activation portrait framing to Deathwatch

- Reduce the visual scale of Death Korps miniature portraits on human activation screens in both portrait and landscape orientations to match Deathwatch miniature framing.
- Adjust horizontal positioning and vertical offset while preserving the transparent source artwork, left-side fade, and Movement-panel overlap.
- Keep Deathwatch portraits, all roster rails, combat art, gameplay mechanics, and Standard/Experimental behavior unchanged.
- Update the app shell and service-worker cache to v10.0.140.

## v10.0.139

### iPhone activation scrolling

- Keep Death Korps and Deathwatch activation dialogs within iPhone safe areas, with a single native vertical scroll region even when swiping over action buttons.
- Ensure users can scroll to the Mission / Battlefield actions and End Activation footer without scrolling the background page.
- Restrict the change to human activation dialogs, preserving artwork, game mechanics, and the Standard/Experimental modes.
- Bump the app shell and offline cache to v10.0.139.

## v10.0.138

### Finish an incapacitated operative's in-progress activation

- Allow a Fight, shooting attack, or retaliatory effect to finish committing an already-started player action even when the attacker is eliminated during resolution.
- Record its resolved actions and apply action/Threat bookkeeping once, then automatically finish the eliminated operative's activation instead of returning to a screen with unused AP.
- On a saved-game resume or other attempt to reopen the activation, finish an eliminated operative's stale activation rather than display actionable controls.
- Preserve the normal Ready-operative validation for new activations and advance turn order through the existing completion path.
- Bump the app shell and service-worker cache to v10.0.138.



## v10.0.130

### Promote combined Necron activation to Standard mode

- The inline Necron roster rail, ready-operative selection, operative portraits, details, and Begin Activation now appear directly in the standard Necron Activation card in both Standard and Experimental modes.
- Keep Skip Remaining Necrons beneath the roster and preserve Threat Principle guidance, keyboard/scrollable selection, live Ready validation, unfinished-activation resume, and mission bookkeeping.
- Keep the Experimental Features toggle available and functioning for the existing Deathwatch-only inline activation preview and future experiments. Standard Deathwatch, other teams, rules, and saved games are unchanged.
- Retain the older Necron modal picker implementation as a compatible fallback for direct selection entry, but the regular activation card no longer opens an extra picker.
- Update responsive Necron inline card styling so it applies regardless of the experimental preference; bump cache and release references.



## v10.0.129

### Experimental inline Necron activation selection

- With Experimental Features enabled, place the existing Necron roster rail, detail/portrait, and Begin Activation directly in the Necron activation card; include Skip Remaining Necrons below the selector.
- Reuse the same Necron rail markup and event bindings as Standard mode, including the Threat Principle explanation, scrollable roster, keyboard controls, live Ready validation, and stats.
- Resume an in-progress Necron activation without allowing another to start; refresh the card before launching its activation wizard to keep the underlying screen current.
- Leave Standard mode's Necron activation button and modal unchanged, as well as the previous Deathwatch preview and all gameplay/save data.
- Improve responsive spacing for the inline Necron rail and keep its styling behind the Experimental Features flag.


## v10.0.128

### Experimental inline Deathwatch activation selection

- With Experimental Features enabled, show the existing Deathwatch roster rail, portrait/details, and Begin Activation directly in the Fight Phase activation card; include the existing Skip Remaining Deathwatch Operatives control below.
- Reuse the same operative selector markup and binding code as the existing standard dialog so portraits, readiness filtering, stats, keyboard controls, and activation validation stay consistent.
- Keep Standard mode's original card and modal flow unchanged. Necron selection, other Kill Teams, combat, and game state are unaffected.
- Switching Experimental Features on or off refreshes the currently visible Fight Phase card without modifying the save.

## v10.0.127

### Promote Tomb UI to standard and preserve an experimental playground

- Make the established Tomb UI the default for all users and saved games, including the setup styling, Deathwatch and Necron roster rails, activation portraits, and target rails. Retire the legacy Classic UI switch without altering gameplay or saved-game data.
- Keep the seven-taps-on-version Experimental panel as a separately stored, opt-in "Experimental Features" switch for future previews. It does not change the standard interface until a future feature deliberately uses the flag.
- Ignore the old `tombWorldSolo.experimentalUI.v1` preference on launch, so previous classic/experimental choices cannot accidentally restore Classic mode. Preserve the existing game save and all other preferences.
- Preserve current visual styling, assets, and PWA caching behavior apart from the release version.

## v10.0.126

### Skip remaining operatives after closing an unfinished player guide

- Allow skipping an untouched, active player activation along with the remaining operatives, after explicit confirmation, while preserving the normal skip turn scheduler.
- Prevent silently ignoring Skip Remaining when the active operative already has actions recorded or work pending; explain why and offer Resume Activation.
- Preserve completed actions, mission resolution, saved games, and Necron skip behavior.

## v10.0.125

### Preload Deathwatch activation roster thumbnails

- Preload and decode the small Deathwatch roster portraits when the Deathwatch team finishes loading in Experimental UI; keep decoded images available for reuse.
- Also warm the portraits when Experimental UI is enabled or when the activation roster dialog opens, avoiding repeat downloads or decode work.
- Retain the existing SVG green tinting, selection controls, layout, and game/save behavior.

## v10.0.124

### New coffin-inspired PWA app icons

- Replace the old icon with the selected emerald coffin/portal art in Apple touch (180px), standard Android/PWA (192px and 512px), and a 1024px master PNG.
- Add Android adaptive maskable versions at 192px and 512px; register them in the PWA manifest.
- Use the new art for desktop and app-header icons, including an ICO favicon fallback.
- Refresh the service worker's cache version and precache the new artwork for offline use.
- Keep all gameplay rules, screens, and saved games unchanged.

## v10.0.123

### Readable Deathwatch roster rail names

- Give all ready Deathwatch operative tiles an equal minimum width of 120px so long names such as Demolisher stay unbroken.
- Allow horizontal swiping within the rail on small screens, while wider screens expand the tiles evenly to fill the available width.
- Keep existing miniature art, selection, keyboard navigation, Necron rosters, and Current UI behavior unchanged.

## v10.0.122

### Keep reference PDFs out of PWA caching

- Keep the Tomb World Mission Pack and the nine Kill Team reference PDFs in the repository for development and rules checks.
- Confirm no PDF is in the core offline precache or the extended offline media package.
- Bypass service-worker caching for every PDF URL, including direct PDF navigation; PDFs remain available normally over the network.
- Preserve game mechanics, saved games, and all existing offline gameplay assets.

## v10.0.121

### Responsive Fight portrait fade

- Preserve the existing protective portrait fade on narrow Fight Roll and Fight Result cards.
- Use each card's available width to soften the fade from 440px and remove it at 560px, including landscape and desktop modals without requiring an orientation check.
- Preserve original portrait sizing, opacity, clipping, card layout, and combat behavior.

## v10.0.120

### Restore saved Fights without a startup crash

- Normalize an in-progress Fight using the restored NPO roster rather than reading global game state before it is initialized.
- Preserve saved Fight dice, results, wounds, continuation state, and the entire battle. The Recovery screen no longer repeats for saves affected by this initialization bug.
- Include a behavioral regression check that restores a saved Fight while global state is undefined, including Macrocyte Warrior proximity handling.

## v10.0.119

### Safe startup recovery diagnostics

- Show the actual startup error on the Recovery screen so an initialization or network failure is not mistaken for a corrupted game save.
- Keep the original saved game untouched when recovery is displayed and distinguish loading failures from save failures.
- Make **Export Save** more prominent; append its download anchor to the document and delay revoking the temporary URL to improve reliability on iPhone.
- Preserve Retry Loading and all normal gameplay, UI, and saved-game formats.

## v10.0.118

### Fight Result portrait full-height framing

- Prevent the Deathwatch and Necron Fight Result portraits from ending abruptly above the bottoms of taller participant cards. Artwork now fits within each card's full height, with its original aspect ratio preserved.
- Keep the translucent artwork behind participant names, damage, wounds, and eliminated status while preserving card dimensions, the two-column iPhone layout, and the Current UI fallback.
- Leave Fight Roll portrait framing and all fight resolution mechanics unchanged.

## v10.0.117

### Portraits on Fight Roll and Fight Result cards

- Show existing green Deathwatch and transparent Necron portraits behind each participant's roll and result card, including eliminated models.
- Frame the miniature head/upper half at the top right within each card, with dice, wound counts, and other text layered above it. The image is decorative and has no effect on card dimensions or controls.
- Look up miniature images by stable combat participant ID and side; maintain safe fallback for unsupported Kill Teams or missing images.
- Current Mode hides artwork immediately, and Experimental Mode shows it even when the cards were already rendered. Fight resolution state, rolls, damage, and Continue behavior are unchanged.

## v10.0.116

### Scarab Swarm Blast/Torrent portrait framing

- Move only the **Canoptek Scarab Swarm** result portrait upward in Experimental Mode's Blast/Torrent Attack Complete cards, revealing more of the swarm above the Damage and Wounds pills.
- Preserve the existing size, top-right alignment, opacity, text/pill layering, and every other operative portrait. No combat or saved-state changes.

## v10.0.115

### Necron portraits on reinforcement placement cards

- Experimental Mode's **Deploy Reinforcements and Review** checklist now places the correct Necron upper-body miniature at the top-right of each reinforcement card, behind the existing name, loadout, instructions, and checkbox.
- Reuses the green transparent artwork and mapping already used for Necron activation and Blast summaries; no additional assets or portrait manipulation are needed.
- Portraits are decorative and cropped by the original checklist card, which retains its height, selection controls, confirmation state, and placement logic.
- Original Mode, reinforcement overview, generated names, and game logic remain unchanged.

## v10.0.114

### Experimental Blast/Torrent completion portrait

- Displays a large, top-right portrait of the **damaged target** behind the Attack Complete result card in Experimental Mode, using the existing Deathwatch or Necron artwork.
- Resolves the image by the result's stable target ID and defender side, including Blast friendly-fire targets. Incapacitated Necrons are still found in the full saved roster.
- Crops to the miniature's head/upper body, with the existing Damage and Wounds pills layered above the art for readability; preserves the original card dimensions and button behavior.
- Leaves Current Mode, targets without known portraits, and other attack-summary contexts unchanged. No combat calculations or save-state changes.

## v10.0.113

### Experimental Necron target rail for player attacks

- Replaces the Target NPO/Necron dropdown on the player Shoot/Melee attack preparation screen with a horizontally scrollable Necron portrait rail in Experimental Tomb UI when there are multiple targets.
- Reuses the existing transparent Necron artwork, displaying each target's numbered name and projected current/max wounds below the image, with only the selected target highlighted.
- Keeps Weapon selection, combat eligibility, weapon-rule checks, and Continue behavior unchanged, using the existing hidden `combatTarget` ID as the integration point.
- Retains the original dropdown in Current Mode and the existing automatic/read-only single-target behavior.

## v10.0.112

### Combat participant portraits

- Places a cropped upper-body Necron attacker and Deathwatch defender portrait inside their respective Resolve Combat summary pills when matching artwork exists, including the reverse player-attack case.
- Anchors both transparent green portrait treatments to each pill's upper right, and mirrors the defender artwork left toward the attacker while the attacker remains right-facing.
- Clips artwork to the original summary pill bounds without changing height or adding detail panels; keeps both pills the same grid-row height.
- Preserves all combat resolution data, non-portrait summary fields, save compatibility, and fallback for Kill Teams without portrait assets.

## v10.0.111

### Experimental Necron attack target roster rail

- Adds a compact, horizontally scrollable Deathwatch portrait rail to the unconfirmed Shoot/Fight target-selection step in Experimental Mode.
- Displays each eligible target's name and live current/max wound count below its image, with a single selected highlight and no details panel.
- Preserves target priority, target eligibility, confirmation, combat state, existing Current UI dropdowns, and other Kill Teams.
- Adds accessible target names, keyboard navigation, and focused regression coverage.

## v10.0.110

### Crisp, cache-safe Necron portraits

- Restores all 11 of the exact supplied green transparent Necron images as 384 x 384 portraits, preserving their colors, transparency, and operative associations.
- Adds a release version to Necron image URLs in both the SVG renderer and the service-worker precache so outdated HTTP and PWA image caches cannot keep serving previous portraits.
- Preserves the Experimental roster/activation UI and leaves the Current UI unchanged.
- Updates binary asset hashes and validates the portraits' dimensions and transparency.

## v10.0.109

### Exact supplied green Necron portraits

- Replaces all 11 Experimental Tomb UI Necron portrait assets with crops made directly from the user's supplied green-colorized transparent PNGs.
- No recoloring, grayscale conversion, background removal, masking, or runtime color filters are applied.
- The supplied transparency is preserved and each source is only centered, cropped, and scaled for portrait use.
- Maps the supplied models to the Geomancer, two Tomb Crawlers, Macrocyte Accelerator, Macrocyte Reanimator, three Macrocyte Warriors, Scarab Swarm, Gauss Flayer Warrior, and Gauss Reaper Warrior.
- Bumps the app and service-worker cache so stale portrait assets from v10.0.107 are replaced.

## v10.0.107

### Supplied Transparent Necron Portraits

- Replaces all 11 Necron portrait assets with the user's supplied pre-colored transparent cutouts.
- Centers and crops each supplied source into a transparent square portrait asset before it reaches the UI.
- Removes the runtime Necron grayscale, green colorization, background-key, alpha-mask, and sharpening pipeline. The supplied artwork is rendered as-is.
- Keeps the existing operative-to-portrait mapping: two Tomb Crawlers, Scarab Swarm, Gauss Flayer and Gauss Reaper Warriors, Geomancer, Accelerator, Reanimator, and three numbered Macrocyte Warriors.
- Uses the same direct transparent portrait renderer in the Necron roster rail, selected detail panel, human-controlled activation view, and solo activation view.
- Keeps Current UI unchanged.


## v10.0.106

### Larger Necron Portraits and Cleaner Cutouts

- Makes the Experimental Necron miniatures substantially larger inside the existing portrait frames so individual operatives are easier to identify at a glance.
- Uses model-family-specific framing for Warriors, Tomb Crawlers, Geomancer, Macrocytes, and Scarabs instead of one generic zoom.
- Intentionally allows some base cropping where needed so the miniature itself occupies more of the frame.
- Strengthens the dedicated background alpha key and makes its transfer ramp more decisive so the remaining photographed tabletop/background blobs are removed.
- Preserves the v10.0.105 Photoshop-style colorization equivalent to approximately Hue 135, Saturation 23, Lightness 0.
- Keeps the same framed/colorized helper for the roster rail, selected detail portrait, human-controlled Necron activation portrait, and solo activation portrait.
- Current UI remains unchanged.


## v10.0.105

### Transparent Necron Portrait Backgrounds

- Separates subject colorization from background extraction so the photographed tabletop/background is removed instead of being colorized into a green-gray blob.
- Keeps the Photoshop-equivalent colorization requested by the user: grayscale first, then RGB colorize at approximately Hue 135, Saturation 23, Lightness 0.
- Preserves that colorization with the existing lookup tables while using a dedicated, stronger alpha mask only for background removal.
- Uses a softer alpha ramp after the cutoff so dark miniature detail is retained instead of disappearing with the background.
- Re-centers the Gauss Flayer Warrior after background removal while preserving the separate Gauss Reaper framing.
- The same transparent-background treatment feeds the roster rail, selected detail portrait, human-controlled Necron activation portrait, and solo Necron activation portrait.
- Current UI remains unchanged.


## v10.0.104

### Deathwatch-Matched Necron Portrait Framing

- Removes the v10.0.103 CSS zoom, brightness, and contrast overrides that made the Necron Roster Rail look washed out and unlike Deathwatch.
- Uses explicit source-image framing so Necron Warriors and Scarab Swarms are cropped around the miniature instead of showing excess empty source area, while the taller Necron models receive a small consistent crop.
- Centers each crop in the same 384 × 384 portrait viewport used by Deathwatch, so the Roster Rail and detail portrait use the same layout behavior.
- Runs Necron artwork through the same grayscale-first green colorization and sharpening values as Deathwatch.
- Uses the exact Deathwatch grayscale, transparency key, green lookup tables, alpha transfer, and sharpening pipeline instead of the stronger Necron-only key that was stripping dark miniature detail.
- The same framing and color treatment is reused by the Necron activation portraits; Current UI remains unchanged.


## v10.0.103

### Brighter, Larger Necron Roster Portraits

- Enlarges the Experimental Necron Roster Rail portrait area without changing the Deathwatch Roster Rail.
- Zooms the Necron portrait artwork inside each rail slot so the miniature occupies substantially more of the available frame.
- Brightens and slightly increases contrast on the green Necron treatment so dark armor details remain legible against the Tomb UI background.
- Applies a lighter version of the same visibility improvement to the selected Necron detail portrait.
- Includes responsive sizing for phone and short-landscape layouts while preserving existing horizontal scrolling behavior.


## v10.0.102

### Necron Activation Portrait Alignment

- Fixes the Experimental solo Necron Activation wizard so tall Necron portraits fit completely inside the activation header instead of extending above the modal and being clipped.
- Keeps the portrait bottom-aligned with the activation header while constraining its rendered height to the available header height.
- Preserves the existing green treatment, right-side placement, Roster Rail, human-controlled Necron activation portrait, and Current UI behavior.


## v10.0.101

### Experimental Necron Roster Rail and Activation Portraits

- Adds high-resolution portrait assets created from the supplied Tomb World Necron miniatures and matches them to the app's supported physical NPO types.
- Applies the same grayscale-first green colorization, sharpening, and hardened background transparency used by the Deathwatch portrait treatment.
- Replaces the Experimental Mode Necron activation dropdown with the same Roster Rail interaction used for Deathwatch, including an operative detail panel and no initial selection.
- Allows the Necron rail to scroll horizontally when more Ready Necrons are present than can comfortably fit in the dialog.
- Adds the selected Necron portrait to the human-controlled Necron Activation shell and to the Solo Necron activation wizard header.
- Image mapping uses the supplied Scarab Swarm, Geomancer, two Tomb Crawlers, three Macrocyte Warriors, Macrocyte Accelerator, Macrocyte Reanimator, and Gauss Flayer / Gauss Reaper Necron Warriors.
- Current UI remains unchanged; expansion NPOs without supplied portrait artwork retain the standard icon fallback.


## v10.0.100

### Unselected Deathwatch Roster Rail on Open

- Keeps every Ready operative visually unselected when the experimental Deathwatch activation picker opens.
- Focuses the non-interactive roster instruction on dialog open rather than automatically focusing the first operative, avoiding the false selection highlight on iPhone.
- Preserves green selected-state styling, keyboard focus indicators when navigating the rail, and disabled Begin Activation until a real selection is made.
- Classic picker and other kill teams are unchanged.


## v10.0.99

### Mobile Roster Rail Name Spacing

- Detects Roster Rail operative names that fit on a single line on small screens.
- When a name does not wrap, reduces the otherwise reserved two-line name space and gives that room back to the operative portrait.
- Keeps the larger reserve for names that actually need two lines, preventing overlap or truncation.
- Desktop Roster Rail sizing is unchanged.
- Remains limited to Experimental Tomb UI + Deathwatch.


## v10.0.98

### Green Deathwatch Roster Rail

- Applies the same green grayscale/colorization, sharpening, and hardened background transparency used on the Deathwatch activation portraits to the Roster Rail thumbnails.
- Applies the same treatment to the selected operative preview in the Roster Rail detail panel.
- Uses the existing high-resolution Deathwatch activation portrait assets as the source so the Roster Rail keeps the improved miniature detail from recent activation-screen work.
- Leaves the Current/classic operative picker unchanged and remains limited to Experimental Tomb UI + Deathwatch.


## v10.0.97

### Responsive Activation Portrait Framing

- In landscape layouts with enough horizontal room, expands the portrait's left clipping allowance so wide side-facing poses can extend farther left instead of being unnecessarily cut off.
- In portrait layouts, restores a small visual gap between the weapon/loadout pill and the Movement frame.
- Lowers the portrait by the same portrait-only amount so the miniature still touches the Movement frame exactly, preserving the no-gap image-to-Movement treatment from v10.0.96.
- Keeps the right-edge anchoring, hardened transparency, high-resolution activation assets, and Experimental Deathwatch-only scope.


## v10.0.96

### Flush Activation Portrait Anchoring

- Shifts the Experimental Deathwatch activation portrait to the modal's right edge so the miniature visually touches the activation frame instead of stopping at the modal's inner padding.
- Pulls the Movement group up to the activation header boundary so the portrait reaches and touches the Movement frame with no visible gap.
- Adds a dedicated alpha clamp after sharpening that removes the remaining low-opacity source background while preserving the approved grayscale/colorized miniature treatment.
- Keeps the high-resolution 384×384 activation art, side-safe overflow, and Experimental Deathwatch-only scope.


## v10.0.95

### Activation Portrait Framing

- Keeps the high-resolution Deathwatch activation portraits from v10.0.94.
- Opens the portrait clipping region on the left and right so side-facing poses are not cut off at the portrait column edge.
- Keeps the lower edge clipped at the activation header boundary so artwork still cannot paint into the Movement panel.
- Lowers the portrait artwork slightly so the miniature reaches and visually touches the Movement panel border.
- Keeps the operative name and profile chips above any portrait overflow for readability.
- Remains limited to Experimental Tomb UI + Deathwatch.


## v10.0.94

### High-Resolution Deathwatch Activation Portraits

- Adds a dedicated 384×384 activation portrait set generated from the newly supplied high-resolution Deathwatch source artwork.
- The activation screen no longer enlarges the 192×192 Roster Rail images, eliminating the primary source of lost miniature detail.
- Keeps the approved Photoshop-style treatment from v10.0.93: grayscale first, Hue 135 / Saturation 23 / Lightness 0 colorization, luminance-keyed background removal, and light sharpening.
- Runs that treatment at the full 384×384 SVG resolution before the browser scales the result into the activation card.
- Leaves the Roster Rail artwork unchanged and keeps the feature limited to Experimental Tomb UI + Deathwatch.


## v10.0.93

### Photoshop-Matched Activation Portrait

- Rebuilds the Deathwatch activation portrait treatment to mirror the approved Photoshop workflow: grayscale first, then RGB colorization approximating Hue 135, Saturation 23, Lightness 0.
- Uses HSL-derived lookup tables across the grayscale range so highlights and midtones retain the mockup's pale green character instead of drifting too dark or too saturated.
- Keeps the luminance-keyed transparent background treatment and a lighter sharpening pass for crisp miniature detail.
- Clips the portrait container at its lower edge so the miniature reaches the Movement panel but never paints into it.
- Remains limited to Experimental Tomb UI + Deathwatch.


## v10.0.92

### Activation Portrait Brightness and Integration

- Lifts Deathwatch portrait shadows and midtones so armor, weapon, and face details read much closer to the approved mockup.
- Adds a light sharpening pass inside the SVG filter without reintroducing the muddy CSS post-processing removed in v10.0.91.
- Preserves more dark miniature detail by softening the luminance-key threshold while keeping the studio background transparent.
- Enlarges the portrait slightly and allows it to extend naturally down toward the Movement panel, where the later-painted Movement card clips the lower miniature and visually integrates it into the activation layout.
- Keeps the change limited to Experimental Tomb UI + Deathwatch.


## v10.0.91

### Crisp Transparent Activation Portraits

- Replaces the black-background blend treatment with an SVG luminance-keyed alpha cutout, so the Deathwatch miniature actually renders over the activation panel with transparent surrounding pixels.
- Removes CSS grayscale/sepia/contrast and blend-mode processing that was crushing miniature detail.
- Keeps a crisp high-contrast green-scale treatment inside the SVG filter while preserving bright armor and weapon detail.
- Retains the approved larger mockup-style scale and upper-right placement.
- Applies only to Experimental Tomb UI + Deathwatch. Current mode and other Kill Teams remain unchanged.

## v10.0.90

### Experimental Activation Portrait Polish

- Enlarges the Deathwatch activation portrait to match the approved mockup proportions more closely.
- Raises contrast so miniature details read clearly against the dark activation panel.
- Uses a lightening blend with contrast-crushed source backgrounds so the portrait visually behaves like a transparent cutout instead of a visible square image.
- Removes the previous lower fade and keeps the portrait clipped naturally by the activation header area.
- Preserves the existing Experimental Tomb UI + Deathwatch-only scope. Current mode and other Kill Teams remain unchanged.

## v10.0.89

### Experimental Activation Operative Portrait

- Adds a subtle green-scale image of the active Deathwatch operative to the upper-right of the human activation screen.
- Reuses the existing Deathwatch Roster Rail portrait for the active operative, including the corrected Sergeant source.
- Uses a muted green HUD treatment with screen blending and a lower fade so the portrait reads as atmosphere rather than primary content.
- Keeps the image non-interactive and reserves its own header column so it does not cover activation text or action controls.
- Applies only to Experimental Tomb UI + Deathwatch. Current mode and all other Kill Teams remain unchanged.

## v10.0.88

### Restore Full Operative Detail Portrait

- Restores the pre-10.0.87 Deathwatch detail portrait behavior so the full miniature is visible instead of being constrained to the smaller fixed image box.
- Reserves enough height in the unselected detail panel to match the selected portrait footprint, avoiding the first-selection dialog jump without shrinking the miniature.
- Preserves the stand-in image, reserved stats/copy footprint, rounded rail ends, selection behavior, Current UI, and non-Deathwatch activation flows.

## v10.0.87

### Stable Experimental Activation Dialog Height

- Locks the Deathwatch detail-image frame to a fixed height at desktop, phone, and compact-landscape breakpoints so loading the first selected operative cannot enlarge the grid row.
- Keeps the stand-in icon, reserved stats footprint, rounded rail ends, and selection styling unchanged.
- Remains isolated to Experimental Tomb UI; Current mode and non-Deathwatch activation flows are unchanged.

## v10.0.86

### Experimental Roster Rail Polish

- Rounds the outer corners of the first and last operative cells so the selector follows the curved rail instead of appearing clipped.
- Removes the small triangular selection marker; the green selected border/glow remains the only selection treatment.
- Reserves the full stats and description footprint before selection so the activation dialog no longer changes height when the first operative is chosen.
- Keeps the detail stand-in image, keyboard behavior, gameplay logic, Current UI, and non-Deathwatch activation flows unchanged.

## v10.0.85

### Experimental Roster Portrait Framing Fix

- Bottom-aligns Experimental Deathwatch Roster Rail portraits and switches the rail to non-destructive image fitting so tall operatives such as Marksman and Gunner keep their heads visible.
- Restores the Sergeant portrait with a corrected embedded source while leaving the existing roster asset set intact.
- Adds an intentional dimmed Tomb World icon as the detail-panel stand-in before an operative is selected.
- Keeps Begin Activation disabled until a real operative is selected and preserves the Current UI and all non-Deathwatch activation flows unchanged.

## v10.0.84

### Experimental Deathwatch Roster Rail

- Replaces the plain Ready-operative dropdown with a compact graphical Roster Rail only when Experimental Tomb UI is enabled for Deathwatch.
- Uses eleven uniformly aligned Deathwatch operative portraits with their bases set to a consistent bottom position.
- Keeps selection inside one integrated horizontal rail, with a single larger detail panel for the chosen operative.
- Preserves the existing Current-mode dropdown exactly, and leaves non-Deathwatch activation selection unchanged.
- Adds keyboard radio-style navigation, responsive iPhone portrait/landscape styling, and offline precaching for the new portrait assets.
- Does not change activation rules, save data, roster legality, or gameplay state.

## v10.0.83

### Opaque Setup Back Buttons

- Makes the ghost-style Back buttons inside Experimental New Game Setup cards fully opaque so honeycomb artwork cannot show through the button surface.
- Uses the existing dark app surface color while preserving the button border, typography, dimensions, and interaction behavior.
- Applies only to Experimental setup cards; Current mode and non-setup ghost buttons remain unchanged.

## v10.0.82

### Experimental Honeycomb Across New Game Setup

- Extends the approved mirrored green honeycomb treatment from Deploy Kill Teams to every screen carrying the New Game Setup flow.
- Covers game-mode selection, Kill Team selection, roster-loading/error states, and every normal setup step: Mission, Killzone, Team, Roster, Options, Deploy, and Ready.
- Reuses one decorative markup helper and one shared CSS treatment so placement, fading, green palette, and phone behavior stay consistent.
- Preserves each screen's existing layout, fixed mobile action footer, controls, loading state, Current mode, and gameplay behavior.

## v10.0.81

### Experimental Hex Cluster Mirror

- Mirrors the approved true-honeycomb Deploy composition.
- Moves the upper cluster from the top-left edge to the top-right edge.
- Moves the lower cluster from the bottom-right edge to the bottom-left edge.
- Mirrors the fade masks and phone offsets with the clusters while preserving green color, opacity, geometry, footer behavior, and responsive sizing.
- Keeps Current mode and gameplay unchanged.

## v10.0.80

### Experimental Hex Theme Refinement

- Changes the true-honeycomb Deploy decoration from cyan/blue to the app's existing green theme.
- Reduces base, cluster, highlight, and phone opacities so the hex field stays decorative without competing with checklist text.
- Softens the glow while preserving the approved hex geometry, top anchor, broken/faded pattern, mobile footer behavior, and responsive sizing.
- Keeps Current mode and gameplay unchanged.

## v10.0.79

### Experimental Hex Placement + Mobile Footer Fix

- Anchors the left true-honeycomb cluster directly to the top edge of the Deploy Kill Teams card with no gap.
- Restores the existing mobile Back / Deployment Complete fixed footer by excluding wizard actions from the hex content stacking rule.
- Keeps the true six-sided honeycomb geometry, broken/faded pattern, phone scaling, Current mode, and gameplay unchanged.
- Adds regression coverage for both the top-edge anchor and preservation of the fixed mobile wizard action footer.

## v10.0.78

### Experimental True Honeycomb Hex Field

- Removes the rejected fog-only treatment from Deploy Kill Teams.
- Rebuilds the hex concept with individually clipped six-sided CSS cells arranged in a real staggered honeycomb grid rather than intersecting diagonal lines.
- Places broken/faded hex clusters along the left edge and lower-right edge to match the approved mockup direction while leaving the content center clear.
- Uses only HTML decoration plus CSS clip-path, gradients, opacity, and responsive sizing; no image assets or SVGs.
- Shrinks and thins the clusters on narrow phones without consuming layout space or changing Current mode.

## v10.0.77

### Experimental Billowing Atmospheric Fog

- Removes the rejected broken-hex treatment from Deploy Kill Teams.
- Replaces it with fog alone: two overlapping CSS-generated cloud layers made from many soft radial lobes rather than one broad gradient.
- Gives the two fog banks different blur radii, opacity, scale, and slow drift paths so they appear to waft and billow independently.
- Reduces density and movement on phone-sized screens and disables motion when reduced-motion is requested.
- Keeps the existing Deploy layout, controls, gameplay behavior, and Current mode unchanged.

## v10.0.76

### Experimental Broken Hex + Atmospheric Fog

- Adds a new Experimental-only Deploy Kill Teams treatment combining a faint broken hex field with low atmospheric fog.
- Keeps the hex geometry concentrated around the perimeter so content remains clear on phone-sized screens.
- Uses only CSS gradients, masks, opacity, and pseudo-elements; no raster/SVG artwork or new runtime dependencies.
- Scales the pattern density and fog intensity down on narrow screens while preserving the existing card layout and Current mode.

## v10.0.75

### Clean Experimental Baseline

- Removes the discarded inspection-stamp and field-marking experiment from Deploy Kill Teams.
- Experimental Tomb UI again mirrors the Current interface while preserving the hidden selector for future prototypes.
- Removes all deploy-specific decorative markup and styling from the five rejected visual experiments.
- Leaves gameplay, layout, controls, and Current mode unchanged.

## v10.0.74

### Experimental Deploy Inspection Markings

- Removes the discarded deployment telemetry rail experiment from Deploy Kill Teams.
- Adds visual direction #5: worn inspection stamps and field markings inside the Deploy Kill Teams card while Experimental Tomb UI is enabled.
- Uses an original "DEPLOYMENT AUTHORIZED" stencil, sector/grid identifiers, barcode-like inventory marks, and restrained hazard chevrons.
- Keeps the existing card geometry, buttons, spacing, checklist, gameplay behavior, Current mode, and all other setup screens unchanged.
- Uses CSS-only decorative layers with no new image assets, scripts, or runtime dependencies.

## v10.0.73

### Experimental Deploy Telemetry Rail

- Removes the discarded etched-metal surface experiment from Deploy Kill Teams.
- Adds visual direction #3: a narrow decorative telemetry rail inside the Deploy Kill Teams card while Experimental Tomb UI is enabled.
- Uses tiny numbered ticks, fragmented machine marks, a muted vertical instrumentation line, and restrained cyan status indicators.
- Keeps the existing card geometry, buttons, spacing, checklist, gameplay behavior, Current mode, and all other setup screens unchanged.
- Uses CSS-only decorative layers with no new image assets or runtime dependencies.

## v10.0.72

### Experimental Etched-Metal Deploy Surface

- Removes the discarded armored corner-plate experiment from Deploy Kill Teams.
- Adds a subtle etched-metal surface treatment to the Deploy Kill Teams card while Experimental Tomb UI is enabled.
- Uses faint machining lines, irregular abrasion scratches, hairline fracture scoring, and one restrained cyan power trace.
- Keeps the existing card geometry, buttons, spacing, checklist, gameplay behavior, and Current mode unchanged.
- Uses CSS-only decorative layers with no new runtime dependencies or image assets.

## v10.0.71

### Experimental Armored Deploy Corners

- Removes the discarded Deploy Kill Teams watermark prototype.
- Adds four compact original armored corner plates to the Deploy Kill Teams card while Experimental Tomb UI is enabled.
- Uses worn gunmetal plates, recessed rivets, a restrained cyan power groove, and one faint fracture detail for a grim-dark military-industrial feel.
- Keeps the existing card geometry, buttons, spacing, checklist, and gameplay behavior unchanged.
- Leaves Current mode and every other setup screen unchanged.

## v10.0.70

### Experimental Deploy Watermark

- Adds one original grim-dark watermark to the Deploy Kill Teams card while Experimental Tomb UI is enabled.
- Uses a weathered skull, segmented mechanical halo, cracked targeting ring, and invented machine glyphs without recognizable faction insignia.
- Keeps the watermark faint and non-interactive behind existing content, with no layout, control, checklist, or gameplay changes.
- Leaves Current mode and every other setup screen unchanged.
- Precaches the SVG for offline use and bumps the app/cache version.

## v10.0.69

### Experimental Styling Reverted

- Restores the clean Experimental-mode baseline from v10.0.67.
- Removes the Cyberpunk Glitch Deploy Kill Teams styling experiment and its dedicated stylesheet/tests.
- Keeps the hidden seven-tap Current/Experimental selector and device-local mode setting.
- Experimental mode again intentionally mirrors Current mode until the next visual direction is chosen.
- Bumps the release/cache version so devices discard the briefly deployed experimental styling.

## v10.0.67

### Experimental Interface Reset

- Removes the discarded experimental Tomb interface implementation, styling, artwork, frame assets, and regression tests added after the hidden-mode switch was introduced.
- Keeps the device-local seven-tap Current/Experimental selector and its early startup bootstrap.
- Experimental mode intentionally mirrors the current interface for now, leaving a clean feature-flagged foundation for the next design direction.
- Removes the old experimental assets from the offline cache so previously installed devices refresh to the clean baseline.

## v10.0.16

### Hidden Experimental UI Toggle

- Adds a device-local, seven-tap developer panel for opting into the experimental Tomb visual design.
- Applies the saved visual mode before the main stylesheet loads, with classic mode as the failure-safe default.
- Introduces modest, fully scoped Tomb theme accents without changing gameplay or the classic presentation.

## v10.0.15

### Official Restless Tomb Classification

- Correctly identifies Restless Tomb as an official White Dwarf 521 expansion rule throughout the app.
- Preserves Restless Tomb as an independent optional checkbox compatible with every Tomb World variant.
- Reuses the existing green official-expansion badge styling and refreshes the application cache version.

## v10.0.14

### Clearer Hot Weapon Checks

- Renamed the Hot resolution dialog to HOT WEAPON CHECK.
- Added a concise explanation of why the Hot check occurs and how it can damage the attacker.
- Solo now explicitly states that the Guide rolls the Hot D6 automatically.
- PvP instructs the Player to roll the D6 through the existing manual dice flow.
- Replaced the unclear "Hot roll" label with "D6 Roll."
- Preserved all existing Hot timing, damage, persistence, and dice behavior.

## v10.0.13

### iPhone Dice Audio Recovery

- Narration Play and Resume gestures now silently prepare enabled Dice Roll audio on iPhone.
- Fixed Dice Roll sound remaining silent when Ambient Noise was disabled.
- Ambient Noise, Narration, and Dice Roll preferences remain fully independent.
- No Dice sound is played merely by pressing Narration Play or Resume.

## v10.0.12

### Optional Rules Spacing Polish

- Added subtle separation between the Tomb World Variant heading and its option cards on the setup screen.

## v10.0.11

### Cleaner Optional Content Setup

- "Other Optional Rules" is now collapsed by default to reduce setup-screen clutter.
- Restless Tomb and Deadly Encounters remain available through an accessible expandable section.
- Expanding or collapsing the section does not change selected optional-rule state.

## v10.0.10

### Player-Started Narration

- Narration Cogitator now opens before narration audio begins.
- New narrations initially show a Play control instead of starting automatically.
- After playback begins, the control changes between Pause and Resume normally.
- Transcript, queue, Skip, Stop All, and Hide/Show behavior remain available before playback starts.
- Ambient ducking now begins only when narration actually plays.

## v10.0.9

### Aggressive Defence Result Clarity

- Aggressive Defence now explains the outcome of its D3 roll before the Player continues.
- Rolls of 2 or 3 clearly show that the attacking operative suffers 1 retaliatory damage.
- A roll of 1 clearly shows that no retaliatory damage is inflicted.
- Preserved the existing Aggressive Defence rule, dice persistence, and damage resolution.

## v10.0.8

### Independent Ambient and Dice Audio Controls

- Fully separated Ambient Noise and Dice Roll runtime behavior.
- Turning Ambient Noise off no longer affects Dice Roll sound.
- Dice Roll now prepares its own audio context independently when enabled.
- Preserved the master audio override while keeping all category preferences independent.

## v10.0.7

### Melee Incapacitation Pipeline Fix

- Player melee Fight results that would incapacitate an NPO now pass through the same incapacitation-effect pipeline as other Player attacks.
- Fixed Aggressive Defence not triggering when a melee Fight incapacitated a Canoptek Macrocyte Warrior.
- Preserved Reanimation Protocols, Macrocyte Reanimate, and simultaneous incapacitation-effect ordering for melee results.
- Prevented premature NPO removal and duplicate melee damage.

## v10.0.6

### Macrocyte Melee Proximity

- Melee Fight actions against Canoptek Macrocyte Warriors now automatically satisfy the Aggressive Defence within-2-inch condition.
- Removed the redundant proximity checkbox from the melee attack setup.
- Ranged attacks still ask for the tabletop proximity confirmation when required.

## v10.0.5

### Immediate Ambient Noise Control

- The Game Menu Ambient Noise switch now immediately starts or fades out ambient playback while preserving the master, narration, and dice-roll settings.

## v10.0.4

### Visible Reanimation Protocols Rolls

- Reanimation Protocols now visibly displays its automatic Solo D6 roll whenever an eligible NPO would be incapacitated.
- The Guide clearly shows whether the roll reanimated the NPO or failed.
- Preserved the existing once-per-NPO, per-Turning-Point event behavior and incapacitation-effect ordering.

## v10.0.3 - Rounded Narration Cogitator

**Version 10.0.3**

- Replaced the Narration Cogitator's chamfered shell with a rounded blue monitor housing.
- Rounded the close button frame to match while preserving narration behavior, layout, and CRT effects.

## v10.0.2 - Setup Heading Focus Polish

**Version 10.0.2**

- Removed the visible focus decoration from programmatically focused setup-step headings.
- Preserved setup-step focus management, interactive control focus indicators, gameplay behavior, and save schema version 3.

## v10.0.1 - Narration Cogitator Polish

**Version 10.0.1**

- Refined the Narration Cogitator's CRT-blue presentation and transcript readability.
- Corrected narration transcript dialog positioning across mobile and desktop layouts.
- Preserved gameplay behavior, save schema version 3, and the existing storage key.

## v10.0.0 - Narration Cogitator

**Version 10.0.0**

- Added synchronized on-screen narration transcripts with word-by-word highlighting, elapsed time, and playback progress for the existing narration audio.
- Added Pause / Resume, Skip This Narration, Stop All Narration, Hide / Show Transcript, and queue-safe narration controls.
- Added mobile auto-follow with manual-scroll suspension and a sci-fi cogitator-style narration display.
- Added permanent word-timing metadata for all current narration and included transcript alignment data in explicit offline preparation.
- Preserved audio-only fallback when transcript metadata is unavailable; no ElevenLabs runtime dependency is required.
- No gameplay save migration is required.

## v9.2.63

**Version 9.2.63**

### Dark of the Tomb Reroll Enforcement

- Dark of the Tomb now fully suppresses Player Shoot attack-dice rerolls when the target is confirmed more than 8 inches away.
- Balanced, Ceaseless, and other Guide-managed attack rerolls now obey the event's shared reroll permission without changing their normal behavior at shorter range, in melee, or for NPO attacks.
- Preserved combat save/resume behavior and the existing tabletop distance confirmation.

## v9.2.62

**Version 9.2.62**

### A Ceaseless Scuttling Solo Actions

- Replaced the Solo setup checkbox with two explicit outcomes: "Set Up Macrocyte Warrior" and "No Legal Setup Location."
- The affirmative setup button now directly confirms the physical tabletop placement without an additional modal.
- Preserved Guide-owned Solo resolution, PvP choices, eligibility rules, exactly-once creation, and save/resume behavior.

## v9.2.61

**Version 9.2.61**

### A Ceaseless Scuttling Solo Setup Confirmation

- Replaced the redundant Solo "Resolve A Ceaseless Scuttling" action button with a direct "Macrocyte Warrior set up" tabletop confirmation checkbox.
- The Guide still determines when the Gambit applies, while the Player confirms only the physical placement of the new Macrocyte Warrior.
- Preserved the no-legal-setup-location path, PvP choices, existing Scuttling rules, and save/resume behavior.

## v9.2.60

**Version 9.2.60**

### Solo Reinforcement Replacement UX

- Removed the contradictory NPO replacement selector after the Guide has already resolved a Tombs Beyond Counting reinforcement replacement in Solo play.
- Reinforcement placement now consistently displays the final generated operative, such as a Flayed One replacing a Necron Warrior, while preserving human replacement choices in PvP.
- Preserved existing replacement rules, placement behavior, save/resume state, and all optional Tomb World content.

## v9.2.59

**Version 9.2.59**

### Tombs Beyond Counting Resume Validation

- Recognize all five current Tombs Beyond Counting NPO datacards when normalizing local and imported saves, without adding them to Standard Tomb World generation.
- Keep variant legality separate from catalog recognition so legal expansion battles resume while wrong-variant rosters still use the safe recovery flow.
- Preserve the save schema and storage key so affected v9.2.58 battles become resumable without conversion or regeneration.

## v9.2.58

**Version 9.2.58**

### Basic Production Visitor Analytics

- Add an isolated Cloudflare Web Analytics module for aggregate production-site traffic such as visits, device type, and referral source.
- Restrict Analytics to the official `imthekeymaster.github.io/TombWorldSoloGuide/` path, without gameplay events or gameplay-state transmission.
- Keep offline play independent of Analytics; offline events are not queued, and Cloudflare's external Analytics resources are not cached by the service worker.

**Usage Analytics:** This Guide uses Cloudflare Web Analytics to understand aggregate site traffic such as visits, device type, and referral source. Gameplay state, rosters, dice results, combat results, and saved battles are not intentionally sent to analytics. Offline use is not reported.

## v9.2.57

**Version 9.2.57**

### Responsive Mission HUD Values

- Allow textual Mission HUD values such as `OBJECTIVE MET` to wrap naturally at word boundaries when the Mission column is narrow.
- Keep the shared value row content-sized so all six HUD cells expand together for wrapped values and contract again when the value fits on one line.
- Preserve compact numeric values, the dynamic label row, and the existing Mission and Threat HUD interactions without JavaScript measurement or fixed two-line spacing.

## v9.2.56

**Version 9.2.56**

### Escape Objective and Battle Completion UX

- Distinguish Shifting Labyrinth's minimum escape requirement from the total starting operatives and the operatives still eligible to extract.
- Show `OBJECTIVE MET` while extraction play continues, reserving `MISSION COMPLETE` for the mission's existing terminal state.
- Present the escape-target milestone once, log objective achievement once, and continue tracking subsequent escapes without interrupting normal Turning Point progression.

## v9.2.55

**Version 9.2.55**

### Dynamically Aligned HUD Labels and Values

- Place all six battle HUD labels in one shared, content-sized Grid row and all six values in one shared value row, so values remain aligned when labels wrap to different line counts.
- Use CSS subgrid to preserve each label/value pair and the existing Threat and Mission button boxes while allowing the tallest current label to size the row automatically.
- Remove the portrait label minimum height so the HUD expands for a three-line team name and shrinks again when wider viewports reduce wrapping, without JavaScript measurement or fixed three-line spacing.

## v9.2.54

**Version 9.2.54**

### Mission-Driven Tomb World Battle Endings

- Remove the obsolete automatic four-Turning-Point battle limit: incomplete Tomb World Joint Ops missions now continue through Turning Point 5 and later until their mission-specific victory or defeat condition is met.
- Correct Shifting Labyrinth so it resolves only after every starting player operative has been removed from the killzone and uses `Math.ceil(starting operatives / 2)` for its half-or-more escape threshold.
- Preserve normal Ready, mission Ready-hook, initiative, Tomb World Event, reinforcement, and Firefight processing beyond Turning Point 4, and preserve Turning Point values above 4 when saving and loading.
- Replace the invalid v7.5.6 limit expectations with regression coverage for mission-driven outcomes and late Turning Points.

## v9.2.53

**Version 9.2.53**

### Activation Flow Regression Fixes

- Restore Skip Remaining Activations on clean activation cards by clearing completed combat, dice, mission-action, weapon-rule, Fight, and Hot transaction state when an activation finishes.
- Automatically begin the activation when exactly one player operative remains Ready, while retaining the existing picker when multiple operatives are available.
- Preserve the existing activation scheduler, side-specific Skip behavior, transaction-safety guards, save key, and Scout Sub-Crypt activation behavior.

## v9.2.52

**Version 9.2.52**

### Weapon Rules Before Combat Resolution

- Resolve Combat now presents contextual Weapon Guidance first, followed by all applicable Weapon Rules, before showing attack and defense dice.
- Automatic rule result cards, including Dimensional Banishment, remain after the combat dice at their existing resolution point.
- The shared presentation applies consistently to Player and NPO shooting, while Fight rolls now show both combatants’ applicable weapon rules before their dice, without changing dice, damage, trigger timing, persistence, or weapon-rule execution.

## v9.2.51

**Version 9.2.51**

- Show only each canonical room name on the filtered Scout Sub-Crypt awakened-room selection buttons, without the redundant Unopened status.
- Remove generic Other Damage bookkeeping from the operative activation guide and pending action-completion dialogs.
- Keep roster wound controls, action transactions, Scout Sub-Crypt awakening, NPO generation, and persistent readiness behavior unchanged.

## v9.2.50

**Version 9.2.50**

- Preserve each deployed NPO's Ready or Dormant state when Threat decreases, including after Scout Room reduces Threat to 0.
- Continue to awaken Dormant NPOs when Threat rises from 0 and to create newly generated NPOs as Dormant while Threat is 0.
- Keep the Activation Tracker, status-bar Ready count, activation selector, and Battle Journal aligned with persistent per-NPO readiness.

## v9.2.49

**Version 9.2.49**

- Clarify that the Guide automatically resolves mission dice for Auspex Calibration, Locate Item, Breach Sarcophagus, Nanoscarab Repair, and Awaken Rooms while the player performs the remaining tabletop movement and placement.
- Identify the Guide as the generator of starting NPO rosters and Strategy Phase reinforcements, preserving the displayed formulas and tabletop setup responsibilities.
- Clarify automated Turning Point 2+ initiative ownership while preserving all existing dice, mission, Scout Sub-Crypt, and save behavior.

## v9.2.48

**Version 9.2.48**

- Use each mission's validated Turning Point 1 initiative side without requesting dice, while retaining the Player fallback for older mission definitions.
- Roll one Player D6 and one Necron/NPO D6 through the shared Dice Provider on every later Turning Point, including at Threat 0.
- Reroll tied initiative rounds with resumable per-side dice checkpoints, then preserve the resolved side through the first activation and Battle Record.

## v9.2.47

**Version 9.2.47**

- Awaken Scout Sub-Crypt rooms immediately after a first Operate Hatch, Breach, or manually reported First Room Entry during an operative's activation.
- Generate D3 plus the current Threat Grade NPOs (maximum 5) through the existing dice and roster systems, with immediate Ready or Dormant state based on Threat.
- Persist separate Awakened and Scouted room state, awakening provenance, pending room selection, and generated NPO IDs while making cleanup primarily display room status.

## v9.2.46

**Version 9.2.46**

- Added strict validation and idempotent confirmation for external-damage bookkeeping, preserving active AP and action state after nonlethal damage.
- Completed lethal bookkeeping damage through the canonical player activation lifecycle and made bookkeeping optionally available before a pending action is committed.
- Removed inert legacy damage-action AP, summary, and Threat semantics while keeping older saves loadable, and restored PvP Necron named actions under Operative Actions.

## v9.2.45

**Version 9.2.45**

- Removed the generic Special Actions section and its misleading 1AP Other Damage action from the operative activation guide.
- Kept external damage available as wound bookkeeping without spending AP or changing action history, and retained conditional support for genuine named operative actions.
- Preserved standard and mission actions, incapacitation handling, the save schema, and the existing storage key.

## v9.2.44

**Version 9.2.44**

- Replaced Scout Room's generic eligibility failure with specific Threat, room-clearance, completion, AP, and used-action statuses.
- Added a one-tap room-selection dialog that uses tracked Mission 05 room-to-NPO state while leaving physical operative placement and control-range legality to the player.
- Preserved the 1AP action transaction, scouting progress, mission completion, activation continuity, and save compatibility.

## v9.2.43

**Version 9.2.43**

- Replaced the generic Mission Action in the operative guide with mission-specific action metadata.
- Preserved Pick Up Marker for Recover Transponder, renamed the existing Breach action for Destroy Sarcophagus, and added Scout Room for Scout Sub-Crypt.
- Preserved the v9.2.42 dynamic Breach AP calculation and save-data compatibility.

## v9.2.42

**Version 9.2.42**

- Corrected Breach to cost 2 AP for normal operatives and 1 AP for operatives whose datacards or eligible weapon profiles provide the reduction.
- Excluded Blast and Torrent weapon profiles from granting the Piercing-based Breach reduction.
- Preserved all existing Breach resolution effects, activation flows, and save data.

## v9.2.41

**Version 9.2.41**

- Keeps a side that chooses Skip Remaining unavailable for the rest of the current Turning Point, including across saves and reloads.
- Schedules consecutive activations for the only eligible side, then clears both finished-side flags during the next Turning Point Ready/reset flow.

## v9.2.40

**Version 9.2.40**

- Makes Skip Remaining side-specific, leaving the opposing side's eligible activations unchanged and continuing that side without empty alternations.
- Uses contextual kill-team and Necron activation labels, with per-side first-activation visibility in PvP and immediate Necron skipping in Solo.

## v9.2.39

**Version 9.2.39**

- Added an objective-completion shortcut that resolves all remaining Player and NPO activation trackers after one confirmation.
- Continues directly to Score and clean up without simulating actions, running NPO AI, or completing end-of-turn procedures.

## v9.2.38

**Version 9.2.38**

- Prevented the browser default white first paint with a critical Tomb World shell background.
- Kept the map card and image loading surface dark while mission map assets load, decode, or fail.

## v9.2.37

**Version 9.2.37**

- Removes Recover Transponder's manual carrier update and redundant escape-confirmation flows while preserving automatic carrier tracking.
- Makes the Mission Details Confirm Escape button directly and idempotently resolve extraction victory.
- Resets every Victory and Defeat outcome screen to the top of the document's scrolling element after rendering.

## v9.2.36

**Version 9.2.36**

- Streamlines Recover Transponder's final-marker pickup: the sole unresolved marker is discovered by the normal 1AP Pick Up Marker action without redundant marker selection or a D3 roll.

## v9.2.35

**Version 9.2.35**

- Added the complete Recover Transponder search, carrier, drop, bookkeeping, extraction, and outcome flow.
- Integrated Locate Item with player activations, AP accounting, central dice persistence, mission history, and save migration.
- Preserved the existing save schema and storage key while migrating older Mission 03 progress in place.

## v9.2.33

**Version 9.2.33**

- Kept Transdimensional Relocation's team-aware random-selection summary visible after the event is resolved.

## Project Status and Contributions

Tomb World Battle Guide is a personal, independently maintained project.

Suggestions, bug reports, and gameplay feedback are welcome through GitHub Issues. External code contributions and pull requests are not generally accepted. Development decisions and all changes incorporated into the official version are made by the project owner.

The repository is public for transparency, hosting, and community visibility. Public availability of the source does not make the project community-maintained.

## Source and License

The source code for Tomb World Battle Guide is publicly viewable on GitHub. No open-source license is currently granted for the project's original code.

Games Workshop, Warhammer, Kill Team, and related names, rules, imagery, and other intellectual property remain the property of their respective rights holders. This unofficial fan-made play aid is not affiliated with or endorsed by Games Workshop.

## v9.2.32

**Version 9.2.32**

- Clarified Transdimensional Relocation so the event identifies that the Guide already randomly selected two operatives, using the active Kill Team name.

## v9.2.31

**Version 9.2.31**

- Restricted A Ceaseless Scuttling to battles that actually have access to the Macrocyte Warrior rule.
- In Solo, the Guide now decides to use the gambit when eligible and asks the Player only to resolve the physical setup.
- Preserved the optional tactical decision for the Necron player in PvP.

## v9.2.30

**Version 9.2.30**

- Condensed Scout Squad Forward Scouting guidance into one expandable faction-rule card.
- Nested all Forward Scouting options beneath their parent rule while preserving their full tabletop guidance.

## v9.2.29

**Version 9.2.29**

- Fixed Deploy Kill Teams so battles with no starting NPOs can complete deployment normally.

## v9.2.28

**Version 9.2.28**

- Reduced unnecessary instructional text in roster and optional-content setup.
- Simplified the Games Workshop mission-map source label.
- Removed Solo-only Deadly Encounters references from PvP screens.

## v9.2.27

**Version 9.2.27**

- Fixed starting NPO deployment confirmation so it remains checked after legal roster transformations such as Crownworld Tomb Crawler replacement.
- Corrected the starting NPO deployment count to reflect the actual physical models being deployed.
- Fixed Check All to use the same authoritative deployment state.

## v9.2.26

**Version 9.2.26**

- Moved roster required/maximum counts into the expandable roster category headers.
- Combined roster status with the Selected roster summary.
- Removed the redundant Roster Requirements panel and visible Loadout choices status row.

## v9.2.25

**Version 9.2.25**

- Clarified the message shown when an older incompatible battle cannot be resumed while preserving compatible setup choices.
- Removed the internal mission-pack PDF file-path caption from official mission map displays.
- Reduced fresh PWA installation downloads by leaving the full mission-pack PDF out of the automatic offline cache while retaining all six mission maps.
- Added accessible, non-blocking progress feedback when an installed standalone PWA first prepares narration, ambient audio, and backgrounds for complete offline use; ordinary browser visits retain lightweight core caching only.

## v9.2.24

**Version 9.2.24**

- Deadly Encounters now appears in the Game Menu only when the optional expansion is enabled for the current Solo battle.
- Disabled Solo battles and PvP battles no longer show an unnecessary Deadly Encounters menu item.
- Deadly Encounters setup, mission summaries, Help documentation, and enabled-battle functionality remain unchanged.

## v9.2.23

**Version 9.2.23**

- Torrent secondary targets are no longer automatically preselected; players now explicitly select the operatives that are valid on the tabletop.
- Returning to an in-progress Torrent resolution restores previously selected secondary targets.
- Breach and Operate Hatch Threat Check dice animation and Dice Roll sound now play only in Solo; PvP immediately displays the manually entered physical die result.

## v9.2.22

**Version 9.2.22**

- Simplified Necron activation screens by removing the decorative action/question icons and reclaiming the space for gameplay information.
- Added dice animation and Dice Roll sound feedback when Breach and Operate Hatch Threat Check results are revealed.
- Threat Check animation uses the already committed roll and preserves v9.2.21 reload-safe result behavior.

## v9.2.21

**Version 9.2.21**

- Added clear Threat Check result feedback after human Breach and Operate Hatch rolls.
- Result screens now show the committed roll, Threat contribution, and Threat before/after before returning to the activation.
- Threat Check results are reload-safe and cannot reapply Threat after refresh.

## v9.2.20

**Version 9.2.20**

- Standardized Optional Rules & Expansions on the Mission Briefing with the same card presentation used for Special Rules.
- Removed the duplicate Standard Tomb World text in the briefing.
- Tomb World Variant, Restless Tomb, and Deadly Encounters now have clearer individual read-only summaries.

## v9.2.19

**Version 9.2.19**

- Improved Roster Requirements readability by bolding only each requirement label while displaying its current count/status at normal weight.
- Removed the redundant “Give every starting NPO a Conceal order” deployment checkbox.
- Starting NPOs still begin with Conceal orders automatically, and all other deployment requirements remain unchanged.

## v9.2.18

**Version 9.2.18**

- Removed the redundant Mission Details item from the Game Menu.
- Mission & Map remains the full mission reference screen.
- Mission Details remains available as a quick status popup by tapping the Mission HUD during Guided Play.

## v9.2.17

**Version 9.2.17**

- Simplified Solo NPO Activation headers by removing the redundant standalone APL pill.
- Removed the Order pill from Solo NPO Activation headers.
- Preserved Wounds, AP remaining, weapon/loadout, effects, and all underlying Solo AI/APL/Order behavior.

## v9.2.16

**Version 9.2.16**

- Added narration audio for Flesh Hunger, Rewards of Annihilation, and Enforcer of the Phaerons.
- Completed narration availability for all 14 Tomb World events, including offline caching through the narration manifest.
- Corrected an encoding error in the Reanimation Protocols narration script without changing its generated audio metadata.

## v9.2.15

**Version 9.2.15**

- Moved full-roster eliminated skull decorations to the top visual layer so they are no longer hidden behind stat boxes.
- Enlarged the Necron eliminated skull to match the Player skull-and-crossbones visual size.
- Preserved upper-card placement, compact-view exclusions, and eliminated-card interactions.

## v9.2.14

**Version 9.2.14**

- Repositioned eliminated NPO skull artwork so it no longer overlaps Gameplay profile.
- Muted Gameplay profile styling on eliminated NPO roster cards while keeping the profile accessible.
- Restored a skull-and-crossbones overlay for eliminated Player operatives on the full Player Roster page.
- Compact tracker and dashboard views remain skull-free.

## v9.2.13

**Version 9.2.13**

- Restored the Necron skull overlay for eliminated operatives on the full NPO Roster page.
- Compact dashboard and tracker views remain text-only to preserve space.
- ELIMINATED remains the standardized visible defeated-operative status.

## v9.2.12

**Version 9.2.12**

- Standardized Shooting weapon details with the Melee attack screen.
- Removed the redundant repeated weapon name beneath the Shooting weapon selector.
- Combined ranged weapon statistics and Weapon Rules into one details card.
- Weapons without special rules now show only their profile statistics.

## v9.2.11

**Version 9.2.11**

- Added a small amount of spacing above the melee Weapon field so it no longer crowds the Target NPO dropdown focus outline.
- Preserved native browser dropdown behavior and accessibility.

## v9.2.10

**Version 9.2.10**

- Standardized defeated-operative UI terminology to “Eliminated.”
- Fight Result and dashboard views no longer use mixed “Incapacitated” / “Eliminated” wording.
- Removed the skull icon from defeated operative cards to improve readability and save space.

## v9.2.9

**Version 9.2.9**

- Simplified the Human Activation header by removing the redundant standalone APL pill.
- Removed the Order pill from the Human Activation header.
- Preserved AP remaining, wounds, loadout, effects, and all underlying APL/Order rules.

## v9.2.8

**Version 9.2.8**

- Combined melee weapon statistics and Weapon Rules into one details card.
- Removed the redundant weapon-name repetition beneath the weapon selector.
- Weapons without special rules now show only their profile statistics.
- Preserved the hidden empty-state behavior introduced in v9.2.6.

## v9.2.7

**Version 9.2.7**

- Fight Resolution now identifies the acting operative with “[Operative Name]’s Turn” instead of generic player-facing wording.
- Improved clarity in shared-device PvP play without changing Fight rules or turn ownership.

## v9.2.6

**Version 9.2.6**

- Hid the empty melee weapon summary card until a weapon is selected.
- Preserved the dialog layout so selecting a weapon does not resize or shift the Resolve Melee Attack screen.

## v9.2.5

**Version 9.2.5**

- Fixed Fight Result summaries that could omit committed Strike damage.
- Fight summaries now reconcile with the authoritative Damage Dealt totals for both participants.
- Block information remains visible without implying that Blocks deal damage.
- Replaced incomplete first/last Strike narration with concise aggregate Fight damage summaries.

## v9.2.4

**Version 9.2.4**

- Added a final Fight Result screen showing damage dealt and suffered by both participants.
- Fight outcomes are now shown before returning to the activation picker or ending an activation.
- Completed Actions now reports both damage dealt and Fight retaliation damage.
- Improved clarity when one participant runs out of unresolved successes and the opponent resolves the remainder.

## v9.2.3

**Version 9.2.3**

- Simplified Fight Roll results by removing redundant Failure counts.
- Clarified that all Strike/Block choices belong to the ACTING NOW operative.
- Strike and Block choices now use equal visual emphasis.
- Removed duplicate equivalent Fight choices.
- Solo Fight now clearly reports the NPO's automatic response before returning control to the Player.

## v9.2.2

**Version 9.2.2**

- Restored visible Fight dice results so melee resolution is easier to follow.
- Fight now clearly separates dice rolling from Strike/Block resolution.
- Improved active-turn and unresolved-success presentation.
- Trivial no-choice remaining Strikes can resolve automatically while preserving all Strike-triggered rules.
- Fight rules remain unchanged.

## v9.2.1

**Version 9.2.1**

- Corrected an action-legality bug that incorrectly made Fight unavailable after Shoot and Shoot unavailable after Fight.
- Human-controlled operatives can now perform both actions in the same activation when they have sufficient AP and the player determines the tabletop actions are legal.
- Shoot → Charge → Fight is supported for eligible operatives.
- Normal once-per-activation and movement-action restrictions remain unchanged.

## v9.2.0

**Version 9.2.0 - Tombs Beyond Counting**

- Adds optional Tombs Beyond Counting support from White Dwarf 517, selected before NPO deployment as one of three Tomb World variants: Flayer Curse Infected Tomb, Destroyer Cult Tomb, or Crownworld of the Dynasty Tomb.
- Adds five Necron NPO datacards with Solo behavior and PvP human-control support, including rules-driven Flayed One, Destroyer, Royal Warden, and Lychguard replacements.
- Adds Flesh Hunger, Rewards of Annihilation, and Enforcer of the Phaerons to their corresponding variant event decks, together with shared weapon rules and bespoke NPO abilities.
- Retains the corrected v9.1.1 alternating Strike/Block Fight engine, Standard Tomb World behavior, existing-save compatibility, and save schema version 3.

## v9.1.1

**Version 9.1.1 - Correct Kill Team Fight and Retaliation Resolution**

- Replaced Fight's former attack-versus-save calculation with one shared, persisted alternating Strike/Block sequence for Player and NPO Fight actions.
- Both combatants now roll their selected melee weapon's attack dice; normal and critical Strikes commit damage immediately, while legal Blocks consume both the blocking success and selected opposing success.
- Added deterministic Solo NPO Fight decisions, human Player and PvP Necron decisions, Brutal Block restrictions, and Strike-timed Shock resolution.
- Preserved Stun and pre-sequence melee rerolls through the central Dice Provider. Incomplete legacy aggregate Fight drafts are reset to the current action picker on load; the rest of the saved battle is preserved and the save schema remains version 3.
- Corrected the canonical Canoptek Tomb Crawler claws profile to include Brutal.
- Shoot resolution, hidden Tombs Beyond Counting definitions and variants, event composition, and setup behavior are unchanged.

## v9.1.0

**Version 9.1.0 - Universal Human Activations**

- Adds one sequential activation system for human-controlled Kill Team operatives and PvP Necrons.
- Resolves Kill Team actions one at a time, with AP and Completed Actions remaining visible throughout the activation.
- Reevaluates action legality after each committed action and replaces Player batch planning and Pass with explicit End Activation.
- Preserves the existing Guide-controlled Solo Necron AI decision flow and save schema version 3.

## v9.0.1

**Version 9.0.1 - Reliable Grade Narration**

- Fixes intermittent Grade escalation narration by marking narration complete only after playback successfully starts.
- Allows failed or blocked Grade narration attempts to retry while preserving duplicate suppression after successful playback.
- Preserves Solo and Player vs. Player gameplay behavior, audio preferences, ambient audio, Dice SFX, and save schema version 3.

## v9.0.0

**Version 9.0.0 - Tomb World Battle Guide**

- Adds Solo / Player vs. Player mode selection. Solo retains Guide-controlled Necrons and automatic dice; PvP gives a second player control of Necron actions, targets, and weapon/profile choices through the shared rules engine and mode-aware terminology.
- Adds physical PvP dice entry for attack, defense, initiative, mission, Tomb World Event, Threat, and Necron special-action rolls, including persistent partial entry and resumable committed results.
- Renames the product to Tomb World Battle Guide and uses the `tombWorldBattleGuide.v1` runtime namespace. Pre-v9 saved battles and preferences are intentionally not migrated; the save schema remains version 3.
- Keeps Deadly Encounters Solo-only and rolls the PWA cache to `tomb-world-battle-guide-`, cleaning obsolete Tomb World application caches without affecting unrelated origin caches.

## v8.6.108

**Version 8.6.108 - Clarify Chittering Drone Guide Actions**

- Explains whether A Chittering Drone requires an automatic Guide restoration or tabletop Scarab placement without changing the official event effect text.
- Labels the multiple-wounded action as Restore Selected Scarab Swarm and makes resolved healing messages explicitly identify the Guide's automatic wound change.
- Preserves event resolution, redraw, inventory, battlefield-capacity, Battle Record, navigation, persistence, and save schema version 3.

## v8.6.107

**Version 8.6.107 - iPhone Strategy Event Tap Fix**

- Keeps accidental double-tap zoom prevention on noninteractive page areas without suppressing taps on buttons, links, form controls, or ARIA interactive controls.
- Makes Tomb World event action buttons explicit non-submit buttons so The Maze Reforms resolves or redraws immediately and exactly once from a normal iPhone tap.
- Preserves event transactions, Strategy Phase navigation, saved-game compatibility, and save schema version 3.

## v8.6.106

**Version 8.6.106 - Streamlined Empty Strategy Phase**

- Lets Strategy Phase Actions complete the phase directly when no Tomb World Events or Reinforcements require review.
- Removes the unnecessary three-step progress indicator in this single-screen Strategy flow.
- Preserves the full Events and Reinforcement workflow whenever either contains meaningful work.
- Preserves mission Strategy requirements, blocked-reinforcement reporting, Firefight initialization, and save schema version 3.

## v8.6.105

**Version 8.6.105 - Desktop Sidebar Scrollbar Fix**

- Removes the phantom desktop page scrollbar caused by Operative Status sidebar viewport-height geometry.
- Synchronizes the sidebar with the actual rendered application-header height instead of relying on a fragile fixed offset.
- Preserves normal page scrolling when content genuinely exceeds the viewport and existing internal operative-list scrolling.
- Preserves save schema version 3.

## v8.6.104

**Version 8.6.104 - Player Activation Cancel Fix**

- Keeps Cancel available immediately when opening Player Activation, even before an operative is selected.
- Preserves inactive operative controls and keeps Complete Activation disabled until an operative is selected.
- Preserves transactional activation behavior and save schema version 3.

## v8.6.103

**Version 8.6.103 - Low-Latency iPhone Dice Audio**

- Moves Dice Roll SFX to an isolated predecoded Web Audio buffer to reduce iPhone/WebKit start latency.
- Keeps narration and ambient audio on their existing reliable HTMLAudioElement architecture.
- Preserves synchronized 750 ms dice animation, the attenuated Dice Roll asset, master audio behavior, and the Dice Roll preference.
- Keeps save schema version 3 unchanged.

## v8.6.102

**Version 8.6.102 - Improve iPhone Dice Audio Timing**

- Uses alternating persistent Dice SFX players to reduce iPhone/WebKit restart latency during consecutive rolls such as Attack and Defense.
- Preserves synchronized 750 ms visual dice timing and the attenuated production Dice Roll sound.
- Publishes the attenuated Dice SFX under a new application/service-worker cache version so installed clients receive a consistent build.
- Preserves narration, ambient playback, user audio preferences, and save schema version 3.

## v8.6.101

**Version 8.6.101 - Synchronized Dice Roll Audio**

- Adds an intentionally attenuated dice-roll sound synchronized with visible animated dice, beginning with the tumble and completing as the dice settle.
- Adds a persistent Dice Roll toggle to the Game Menu and integrates dice audio with the existing master speaker and supported desktop volume control.
- Keeps dice audio independent from narration and ambient playback so narration continues uninterrupted while dice clatter plays.
- Preserves the existing iOS-safe HTML audio architecture, ambient lifecycle, and save schema version 3.

## v8.6.100

**Version 8.6.100 - iOS Now Playing Artwork**

- Adds dedicated PNG application artwork for Apple touch icons, the PWA manifest, and iOS/Safari Media Session surfaces.
- Provides explicit Tomb World artwork to Control Center, Dynamic Island, and other Now Playing interfaces while audio is active.
- Preserves the existing narration and ambient HTML audio architecture and save schema version 3.

## v8.6.99

**Version 8.6.99 - Clarify Dimensional Banishment Automation**

- Corrects the weapon-rule summary so Dimensional Banishment is identified as automatically handled by the Guide rather than unsupported.
- Preserves the existing automatic 2D6 resolution, remaining-wounds comparison, incapacitation, persistence, animation, journal, and multi-target behavior.
- Keeps save schema version 3 and adds regression coverage preventing the presentation layer from diverging from the existing combat implementation.

## v8.6.98

**Version 8.6.98 - Threat Escalation Narration**

- Adds production narration for Threat Escalation Grades 1–3, played once when each newly-created milestone card first appears.
- Persists each card occurrence's consumed narration state so re-renders and restores do not replay it.
- Preserves the existing shared HTML audio, narration queue, ambient ducking, speaker pause/resume, and Replay Last architecture.
- Keeps save schema version 3 with backward-compatible normalization for older milestone cards.

## v8.6.97

**Version 8.6.97 - Further Attenuated Caverns Ambience**

- Uses the supplied `Ambient/caverns_25.ogg` track, attenuated to 25% of the original amplitude, without additional audio processing.
- Precaches the newly configured ambience for offline/PWA use while retaining both `Ambient/caverns.ogg` and `Ambient/caverns_50.ogg`.
- Preserves the v8.6.96 narration controls, platform-specific Volume UI, HTML audio ambient behavior, settings-only audio toggles, and save schema version 3.

## v8.6.96

**Version 8.6.96 - Attenuated Caverns Ambience**

- Uses the supplied, professionally attenuated `Ambient/caverns_50.ogg` track without additional audio processing.
- Precaches the configured attenuated ambience for offline/PWA use while retaining the original `Ambient/caverns.ogg` asset.
- Preserves the v8.6.95 narration controls, platform-specific Volume UI, HTML audio ambient behavior, settings-only audio toggles, and save schema version 3.

## v8.6.95

**Version 8.6.95 - Resumable Master Audio and Cleaner iOS Settings**

- Makes the header speaker pause active narration non-destructively and resume the same production audio element, source, playback position, handlers, dedupe state, and queued narration from a direct user gesture.
- Keeps failed narration resumes retryable and cancels a master-paused clip instead of resuming it when Narration was disabled while muted.
- Completely omits the unsupported Volume row on iPhone and iPad while preserving the persistent native range control and live volume behavior on supported desktop platforms.
- Preserves mission-selection narration priming, HTML audio ambient playback from `Ambient/caverns.ogg`, narration ducking, and save schema version 3.

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

- Added the optional Restless Tomb rule to Mission Briefing for all six missions.
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

Rosters draw from the 21 physical models available in the box. Applicable loadouts are selected per operative instance, and user-facing NPO lists use alphabetical, natural-number ordering. NPO portraits are intentionally not displayed in Current UI. Experimental Tomb UI adds portraits for supported Tomb World Necron activation flows; expansion NPOs without supplied art use the standard icon fallback. The Obelisk Node Matrix is not supported by the app.

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

Run the focused rules-engine, mission, combat, event, reinforcement, and save-persistence regression suite from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The Guide stores current battles under the `tombWorldBattleGuide.v1` browser-storage key. The pre-v9 Tomb World Solo Guide namespace is intentionally ignored; new Solo and PvP battles use the current namespace and save schema.

The service-worker cache prefix is `tomb-world-battle-guide-`. During activation, v9 removes obsolete caches from both Tomb World cache namespaces while retaining the current cache and unrelated origin caches.

### Installing the app

- **iPhone or iPad:** Open the production site in Safari, tap **Share**, then **Add to Home Screen**.
- **Android or supported desktop browser:** Open the browser's install prompt or menu and choose **Install app** or **Add to Home screen**.

## Important

Use the official Kill Team and Tomb World publications for authoritative rules, mission wording, terrain placement, and datacards.


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
- `Assets/icon-192.png`, `Assets/icon-512.png`, and `Assets/icon-180.png` must remain inside `Assets`.
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
