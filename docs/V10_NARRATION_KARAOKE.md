# V10 Synchronized Narration Transcript (Stage 4)

## Synchronization architecture

Stage 4 extends the single visible-dialog `requestAnimationFrame` loop introduced in Stage 3. On each frame, the presentation reads `TombWorldNarration.getPlaybackState().currentTimeMs`; the HTML Audio position remains the only narration clock. There is no interval, estimated duration, word counter, or synthetic playback time. Browser stalls, background throttling, Pause/Resume, and playback restarts therefore recover on the next visible frame without replaying missed transitions.

## Safe transcript mapping

The authoritative `state.transcript` remains the displayed source. Alignment tokens are processed in order with a forward-only cursor. Exact matching is attempted first, followed by a case-insensitive match that does not alter displayed capitalization. Text between matched tokens is retained as DOM text nodes, and matched non-whitespace tokens become non-interactive `span` elements carrying only their alignment index. The implementation uses `createTextNode`, `createElement`, `textContent`, and `replaceChildren`; it never constructs transcript HTML.

This preserves source punctuation, apostrophes, hyphens, spacing, and newlines. Whitespace-only alignment tokens are not wrapped because the authoritative whitespace is already retained. A skipped region containing letters or numbers, a missing token, invalid timing, or an empty result rejects the entire mapping. Rejection displays the existing static transcript instead of a partial highlighted transcript. Audio, progress, and controls remain available.

## Word states and pauses

- **Upcoming:** the word has not started and is readable at reduced emphasis.
- **Current:** `startMs <= currentTimeMs < endMs`, shown in luminous Tomb World green with a restrained glow.
- **Spoken:** `endMs <= currentTimeMs`, shown at normal foreground emphasis.

Before the first word, every word is upcoming. During a genuine gap, completed words are spoken and no word is current; this makes dramatic silence visible and prevents future words from highlighting early. After the last word, all words are spoken and none remains current.

The current position is found with binary searches over start and end timestamps. Normal forward playback changes only the old current word, the new current word, and any newly completed range. A backward time jump performs a clean recalculation. The transcript DOM is built once per active transcript and is not rebuilt per frame.

## Auto-follow and manual reading

Auto-follow affects only the scrollable transcript body. The current word may remain anywhere in a safe zone spanning 25% through 75% of the viewport height. It is moved toward the vertical center only after leaving that zone, so the view does not scroll for every word.

Wheel, touch, pointer, selection, and non-programmatic scroll interaction suspend following for 4 seconds. Each new interaction renews the timeout, allowing the Player to scroll ahead and select text without being pulled back. Programmatic follow scrolling is marked briefly so its own scroll events do not trigger suspension. When inactivity expires, the next visible animation frame returns the current word to view if necessary.

When `prefers-reduced-motion: reduce` is active, following uses instant `auto` scrolling. Highlighting and visibility tracking remain enabled.

## Playback lifecycle

- **Pause/Resume:** highlighting freezes naturally because audio-backed `currentTimeMs` stops, then continues from the actual resumed position.
- **Hide/Show Transcript:** hiding cancels the visible-dialog frame loop while audio continues. Showing performs one immediate full state catch-up at current audio time, follows the current word, and restarts the same loop without restarting audio.
- **Replay Last and queued entries:** an inactive transition or a different narration ID discards span references, cursors, scroll suspension, and prior classes. The next transcript is mapped fresh while narration alignment data remains managed by the runtime cache.
- **Skip/Stop/natural end:** existing Stage 3 semantics remain unchanged and end the current highlighting lifecycle.

## Accessibility

Highlighting is visual only. Word spans have no role, `tabindex`, event handler, individual accessible name, or live-region behavior. Focus never follows words, and assistive technology receives no per-word announcements. The progress bar remains informational and non-seekable. No word seeking, playback speed, or caption preference controls are introduced.

## Manual acceptance

1. Check out `v10-dev`, run `py -3 -m http.server 8000` (or `python3 -m http.server 8000`), open `http://localhost:8000/`, and clear stale site data if necessary.
2. At approximately 390px width, start Mission 01. Confirm upcoming, current, and spoken treatments track the voice without reflow, horizontal overflow, or unreachable controls.
3. Use a clip with dramatic pauses. Confirm no next word highlights during silence and progress continues from real audio time.
4. Pause on a highlighted word, wait, and Resume. Confirm both progress and highlighting freeze and resume together.
5. Hide the transcript, wait several seconds, and Show it. Confirm an immediate catch-up and comfortable current-word position without an audio restart.
6. Scroll and select text manually. Confirm the view remains under Player control for about four seconds, then calmly returns only if the current word is outside the safe zone.
7. Skip into a queued narration, Stop a queue, and Replay Last. Confirm no word classes or scroll state leak between entries.
8. Enable reduced motion. Confirm highlighting remains synchronized and any required following is instantaneous rather than smooth.
9. Simulate invalid or unavailable alignment. Confirm the complete static transcript or “Transcript unavailable.” appears while all playback controls continue working.

The runtime PWA reads only bundled narration audio and alignment JSON. It makes no ElevenLabs API calls.
