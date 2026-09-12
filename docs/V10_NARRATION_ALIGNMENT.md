# v10 narration forced-alignment harvesting

## Purpose and boundaries

Forced alignment creates permanent, build-time transcript timing metadata for the existing narration MP3 library. It does not synthesize, transcode, normalize, or replace audio. The production PWA does not contact ElevenLabs; only the local Python Narration Producer does.

The producer sends each existing MP3 and its exact authoritative text to `POST https://api.elevenlabs.io/v1/forced-alignment` as multipart fields named `file` and `text`. Authentication uses `ELEVENLABS_API_KEY` from the ignored `tools/narration-producer/.env` file. The key is sent only by Flask and is never returned to browser code or written to output.

## Source mapping and validation

`tools/narration-producer/alignment.py` contains the single ID-to-transcript resolver. It indexes the `scripts` arrays in `Narration/scripts/*.json`, covering mission introductions, events (including Tombs Beyond Counting sources), grades, outcomes, and deadly encounters. An entry is not submitted if its ID is missing or duplicated, its category/output path differs between the source and manifest, its audio is unavailable or missing, its audio path escapes the narration library, or its source-script/audio hash does not exactly match the manifest.

The inventory reports available and unavailable entries; valid, missing, stale, and invalid alignments; missing audio; missing or ambiguous scripts; and script-hash mismatches.

## Output

Files are written atomically beneath `Assets/Audio/Narration/alignment/` using a deterministic, filesystem-safe form of the manifest ID, for example `mission.03.intro.json`.

Each JSON document has schema version 1 and contains:

* `id` and the complete authoritative `text`, including punctuation and paragraph breaks;
* manifest `durationMs`, `scriptHash`, and `audioHash`;
* ElevenLabs `alignmentLoss` and a local `qualityStatus`;
* `words`, each with `text`, integer `startMs`, integer `endMs`, and API `loss` when supplied.

An alignment is `VALID` only when it is structurally usable and both hashes equal the current manifest. A mismatch is reported as `STALE SCRIPT` or `STALE AUDIO`; malformed metadata is `INVALID`. Stale data is never silently accepted.

`qualityStatus` is `GOOD` for a structurally complete response by default. `REVIEW` is a deliberately conservative local heuristic, not an ElevenLabs guarantee: overall loss must exceed `0.5` and be more than three times the median returned per-word loss. All loss values remain available for human review, and elevated loss alone does not discard otherwise complete timing data.

## Harvest the library locally

1. Check out `v10-dev` and ensure the working tree is current.
2. Run `SETUP_NARRATION_PRODUCER.bat` once if the producer virtual environment is not installed.
3. Run `RUN_NARRATION_PRODUCER.bat`.
4. Use **Open API Key File**, put the active key after `ELEVENLABS_API_KEY=` in the local `.env`, save it, and choose **Recheck API Key**. Never commit `.env`.
5. In **ALIGNMENT**, choose **Refresh Status** and resolve any missing-audio, missing-script, ambiguous, or script-hash-mismatch issue before submitting that entry.
6. Choose **Generate Missing/Stale Alignments** and confirm. Processing is sequential. The producer skips unavailable entries and valid hash-matched files, reports each current ID, and stops on authentication, quota/payment, or rate-limit responses while safely retaining completed files.
7. Choose **Refresh Status** after completion. The target is every available entry reported valid, with zero missing, stale, invalid, or failed entries. Review entries marked `REVIEW` and their preserved loss values.

The operation is restartable. If it is interrupted, repeat step 6: valid files are skipped and only missing/stale candidates are submitted, avoiding duplicate credit use. Individual cards also provide **Generate Alignment** or **Regenerate Alignment** for targeted retries.

Run `python -m unittest tests.test_v10_narration_alignment` from the repository root to validate mapping, schema, hashes, status detection, restart behavior, and mocked API handling without an API key or any network call.
