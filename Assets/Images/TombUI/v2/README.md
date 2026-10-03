# Tomb UI v2 assets

This folder supports the hidden experimental `data-ui="tomb"` interface.

## Portrait sprite

`portrait-sprite.webp` is a 4 × 2 sprite sheet.

Top row, Deathwatch archetypes:
1. leader
2. rifleman / gunner
3. melee
4. heavy weapon

Bottom row, Necron archetypes:
1. warrior
2. armored
3. specialist
4. scarab swarm

The v2 operative picker currently uses the Deathwatch row. The Necron row is staged for the target-selector pass.

## Card frames

- `card-ready.svg`: neutral selectable card
- `card-selected.svg`: blue selected player card
- `card-valid.svg`: green valid target card
- `card-disabled.svg`: inactive / already activated card
- `card-danger.svg`: injured / invalid / out-of-range card

These are real scalable graphical assets. Live names, roles, statuses, accessibility state and selection behavior remain HTML.
