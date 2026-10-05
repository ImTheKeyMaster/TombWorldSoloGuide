# Tomb UI v3 art pack

This folder contains the high-fidelity art assets for the hidden experimental Tomb UI.

## Core approach
The mockup is treated as a game HUD, not as a conventional responsive web page. HTML/CSS own layout and live text. These assets provide the visual skin.

- `portraits.webp` contains the generated cinematic Deathwatch/Necron portrait sprite already staged on this branch.
- `screen-frame-portrait.svg` and `screen-frame-landscape.svg` are separate artboard overlays so portrait and landscape do not distort the same frame.
- `header.svg` supplies the Tomb World header environment without baked live text.
- Card state SVGs use the same geometry for ready, selected, injured and disabled states.
- Confirm and Cancel are split into left cap, stretchable center and right cap. Endcaps never stretch.
- Selection indicators are independent assets.
- `action-preview.svg` is a scalable shell with fixed icon/right zones and an expandable center.

## Implementation rules
1. Do not stretch a complete ornate button or frame independently in X and Y.
2. Preserve card aspect ratio.
3. Keep portraits clipped inside a dedicated viewport.
4. Keep names, roles, status, HUD numbers and action text as live HTML.
5. Use the portrait and landscape frame overlays only with uniform scaling against their reference artboards.
6. Apply glow with CSS plus the selected assets rather than changing component geometry.

## Portrait sprite
Treat `portraits.webp` as a 4 x 2 sprite sheet unless later replaced with fully bespoke per-operative portraits. The top row is Deathwatch archetypes and the bottom row is Necron archetypes.

This pack is assets only. It does not change gameplay or production UI until wired by a later PR.
