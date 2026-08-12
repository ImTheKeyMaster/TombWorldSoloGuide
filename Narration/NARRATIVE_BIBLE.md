# Dungeon Master Narration — Narrative Bible

## Purpose

Dungeon Master Narration is optional, sparse cinematic audio that adds atmosphere without carrying rules information. Gameplay and every instruction remain complete when narration is disabled or unavailable.

## Approved scope

Narration is limited to mission introductions, accepted Tomb World Events, and mission-specific victory or defeat. It does not describe UI controls, phases, activations, movement, attacks, dice, action points, or routine game operations.

## Voice and delivery

Use a restrained, ominous storyteller voice. Favor short sentences, deliberate pauses, and the ancient mechanical horror of a Necron tomb. Never address interface actions or improvise rules. Preserve the approved script text exactly during production.

## Production records

The canonical approved text lives in `scripts/`. `scriptHash` identifies that exact text. `generationHash` and `audioHash` remain `null` until a future offline production process records generation settings and generated audio. Runtime availability is controlled separately by the public narration manifest.

No voice-service credential or generation integration belongs in the browser application.
