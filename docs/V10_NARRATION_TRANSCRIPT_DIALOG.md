# V10 Narration Transcript Dialog (Stage 3)

## Purpose and architecture

Stage 3 adds a static, readable transcript player without moving media ownership into gameplay code. `narration.js` remains responsible for audio, playback state, and both narration queues. `narration-transcript.js` observes the public `TombWorldNarration` API and owns only presentation state: whether the current playback's dialog was hidden, focus restoration, and the animation-frame lifecycle.

Word-by-word karaoke highlighting, word timing presentation, and transcript auto-follow are explicitly **not implemented** in Stage 3.

## Dialog lifecycle

An inactive-to-active playback transition opens the dedicated transcript dialog and resets its scroll position. State changes caused by alignment arrival, progress, pausing, resuming, or master audio do not reopen a dialog hidden by the Player. An inactive transition closes the dialog, removes the reopen control, and resets the per-playback hidden state. A later queue entry or Replay Last is a new playback and opens normally.

The category eyebrow maps runtime categories as follows:

| Runtime category | Player label |
| --- | --- |
| `mission-intro` | MISSION BRIEFING |
| `event` | TOMB WORLD EVENT |
| `grade` | THREAT ESCALATION |
| `outcome` | MISSION OUTCOME |
| `deadly-encounter` | DEADLY ENCOUNTER |
| unknown/future | NARRATION |

The heading remains “Narration”; raw narration IDs are never rendered.

## Transcript and progress

The body initially displays “Loading transcript…” while lazy alignment loading is pending. Valid alignment replaces it with the complete static transcript through `textContent`. A failed or invalid alignment displays “Transcript unavailable.” without affecting audio or controls.

Progress comes only from `TombWorldNarration.getPlaybackState()`: `currentTimeMs / durationMs`, clamped from zero to one. A `requestAnimationFrame` loop reads that state while the dialog is open and playback is active. It is cancelled when the dialog hides, playback ends/stops, or the page is discarded. There is no synthetic playback clock or interval. Elapsed and total milliseconds are floored and formatted as `M:SS`; invalid, infinite, and negative values display as zero.

## Playback actions

- **Pause / Resume** uses `pauseNarration()` and `resumeNarration()`, preserving the clip, queues, and actual playback position.
- **Master mute** remains authoritative. The dialog stays visible, its pause control becomes disabled, and explanatory text directs the Player to turn master audio on. A user pause remains distinct and survives a master mute toggle.
- **Hide Transcript** (including Escape) hides only the dialog. Narration and queues continue. The compact **Show Transcript** button reopens at the current position without loading, restarting, or rewinding audio.
- **Skip** calls the engine's deterministic `skipCurrent()`. It records `lastEndReason: "skip"`, completes only the current clip through existing completion semantics, and preserves both the Tomb World Event and Deadly Encounter queues.
- **Stop Narration** calls the existing `stop()`, stopping the active clip and clearing both queues.

## Queue and end behavior

The same dialog follows Event and Deadly Encounter queue entries. A natural end or Skip closes the ended entry; the next queued active transition reuses and updates the dialog, resets progress and transcript scroll, and shows the next transcript. Stop prevents pending narration from starting. With no next entry, natural end, Skip, and Stop leave both the dialog and reopen control hidden.

## Accessibility and mobile behavior

The native dialog has an accessible heading. All actions are real, labeled buttons; the visual close glyph has the accessible name “Hide transcript.” Escape is intercepted as Hide rather than Stop. Focus moves to the Hide button when opened, to Show Transcript when hidden during playback, and back to the previously focused application control after playback ends where practical. Neither transcript text, elapsed time, nor progress is an `aria-live` region.

At phone widths, including approximately 390px, the dialog retains edge and safe-area margins, uses a viewport-bounded height, and gives the transcript its own overscroll-contained scrolling region. Progress and controls remain in the fixed footer grid with touch-sized buttons. The Stop control receives a full row on narrow phones. A compact two-column layout keeps the controls reachable in landscape, while desktop width is capped at 700px.

## Manual acceptance

1. From `v10-dev`, run `py -3 -m http.server 8000` (or `python3 -m http.server 8000` where `py` is unavailable) and open `http://localhost:8000/`.
2. If a prior PWA shell is stale, clear site data in DevTools under **Application → Storage**, then reload.
3. Start Mission 01 narration. Confirm the dialog, MISSION BRIEFING label, transcript, real progress, elapsed/total time, and uninterrupted audio.
4. Pause and Resume. Confirm the same clip resumes from the same position.
5. Hide, wait, and Show Transcript. Confirm audio never stopped or restarted and progress reflects the current position.
6. Skip a standalone clip, then queued Event and Deadly Encounter clips. Confirm `lastEndReason` is `skip` and each queue advances.
7. Stop while clips are queued. Confirm the current clip and all queued narration stop and both transcript controls disappear.
8. User-pause, toggle master audio off and on, and confirm narration remains user-paused until Resume is explicitly selected.
9. Simulate a missing alignment response. Confirm “Transcript unavailable.” while all media controls remain usable.
10. Repeat at a 390px viewport and phone landscape. Confirm there is no horizontal overflow or clipped control and only the transcript body scrolls.

Stage 3 does not change the versioned service-worker app shell or add alignment JSON files to it. Offline packaging and cache-version integration remain deferred to the dedicated offline stage. Until that release updates the cache version, local PWA testing may require clearing site data as described above.
