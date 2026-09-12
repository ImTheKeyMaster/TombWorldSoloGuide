# v10 Narration Runtime Foundation

Stage 2 adds an ephemeral, read-only narration playback-state API. It does not add a transcript dialog, playback controls, progress display, or karaoke highlighting, and it does not change the public v9.2.63 application version.

## Alignment loading and validation

`playEntry()` starts audio without waiting for transcript data, then lazily requests `Assets/Audio/Narration/alignment/<safe-id>.json`. The safe filename replaces every character outside `A-Z`, `a-z`, `0-9`, `.`, `_`, and `-` with `_`. Successfully validated alignments are cached by narration ID for the browser session, including Replay Last.

An alignment is accepted only when schema version and narration ID are correct; transcript text is non-empty; duration is a non-negative number matching the manifest; script and audio hashes match the manifest; and every word has text and ordered, non-negative numeric millisecond timestamps. `GOOD` and `REVIEW` quality records are both accepted because quality and loss are informational.

Missing, malformed, offline, or inconsistent alignment data is treated as unavailable. Alignment work never blocks audio startup, changes a queue, or throws into gameplay. The runtime PWA reads only local project alignment JSON and has no ElevenLabs runtime dependency or API key.

## Playback state API

`TombWorldNarration.getPlaybackState()` returns a new defensive snapshot containing active, playing, and pause flags; active ID and category; current and total milliseconds; transcript availability and text; cloned alignment words and metadata; cloned manifest metadata; and the last end reason (`natural` or `stop`). Active-entry tracking is separate from Replay Last state. No `Audio` object or queue is exposed.

Current position comes directly from `Audio.currentTime`. Duration prefers a finite `Audio.duration` and otherwise uses manifest `durationMs`. There is no independent progress timer.

`pauseNarration()` pauses only active, playing audio while preserving its source, position, active entry, and queues. `resumeNarration()` resumes that same user-paused audio only when narration and master audio are enabled. A user pause is tracked separately from `pausedByMaster`, so restoring master audio cannot resume a clip the user explicitly paused.

Meaningful lifecycle transitions dispatch `tombworldnarrationstatechange` with a defensive playback snapshot: playback start, alignment success or failure, user or master pause/resume, natural end, stop, and active-entry changes. No per-frame event is dispatched. Asynchronous loads are checked against both their playback request and active ID, so a late response can be cached but cannot attach to a newer clip.

This runtime state is media-only and is not written to battle saves. `SAVE_VERSION` remains `3`, and `STORAGE_KEY` remains `tombWorldBattleGuide.v1`.

## Manual browser-console acceptance

1. Serve the repository locally, open the Guide, and begin any existing narration.
2. Run `TombWorldNarration.getPlaybackState()`. Confirm `active` and `playing` are `true`, `paused` is `false`, `id` matches the clip, `currentTimeMs` increases, `durationMs` is populated, and—after the lazy request completes—`transcriptAvailable` is `true` with full `transcript` text and populated `alignment.words`.
3. Run `TombWorldNarration.pauseNarration()`. It should return `true`, and the audio should pause.
4. Run `TombWorldNarration.getPlaybackState()` again. Confirm the entry remains active, `playing` is `false`, `paused` and `pausedByUser` are `true`, and `currentTimeMs` remains near the paused position.
5. Run `await TombWorldNarration.resumeNarration()`. It should return `true`, and playback should continue from the same position.
6. Run `TombWorldNarration.stop()`, followed by `TombWorldNarration.getPlaybackState()`. Confirm `active`, `playing`, and `transcriptAvailable` are `false`, active transcript/alignment fields are empty, and `lastEndReason` is `stop`.
