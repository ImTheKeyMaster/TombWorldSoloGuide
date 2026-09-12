"""Forced-alignment harvesting for the local Narration Producer."""
from __future__ import annotations

import json
import hashlib
import math
import os
import re
import tempfile
from pathlib import Path
import requests

ALIGNMENT_SCHEMA_VERSION = 1
ALIGNMENT_API_URL = "https://api.elevenlabs.io/v1/forced-alignment"


def normalize(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def alignment_path(alignment_dir, entry_id):
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", entry_id)
    return Path(alignment_dir) / f"{safe_name}.json"


def seconds_to_ms(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Alignment timing must be a finite number.")
    return round(value * 1000)


class TranscriptResolver:
    """The single authoritative manifest-ID to source-script resolver."""

    def __init__(self, scripts_dir):
        self.records = {}
        for source in sorted(Path(scripts_dir).glob("*.json")):
            data = json.loads(source.read_text(encoding="utf8"))
            for record in data.get("scripts", []):
                item = dict(record, fileSource=source.name)
                self.records.setdefault(record.get("id"), []).append(item)

    def resolve(self, entry_id):
        matches = self.records.get(entry_id, [])
        if not matches:
            return None, "SCRIPT MISSING"
        if len(matches) != 1:
            return None, "AMBIGUOUS"
        script = matches[0].get("script")
        if not isinstance(script, str) or not normalize(script):
            return None, "SCRIPT MISSING"
        text = normalize(script)
        return dict(matches[0], script=text, computedScriptHash=hashlib.sha256(text.encode("utf8")).hexdigest()), "OK"


def validate_alignment(path, entry, transcript=None):
    path = Path(path)
    if not path.exists():
        return "MISSING", None
    try:
        data = json.loads(path.read_text(encoding="utf8"))
        if not isinstance(data, dict) or data.get("id") != entry["id"]:
            return "INVALID", None
        if data.get("scriptHash") != entry.get("scriptHash"):
            return "STALE SCRIPT", data
        if data.get("audioHash") != entry.get("audioHash"):
            return "STALE AUDIO", data
        required = (data.get("schemaVersion") == ALIGNMENT_SCHEMA_VERSION
                    and isinstance(data.get("text"), str)
                    and (transcript is None or data.get("text") == transcript)
                    and isinstance(data.get("durationMs"), int) and data["durationMs"] >= 0
                    and data.get("durationMs") == entry.get("durationMs")
                    and isinstance(data.get("scriptHash"), str) and bool(data["scriptHash"])
                    and isinstance(data.get("audioHash"), str) and bool(data["audioHash"])
                    and data.get("qualityStatus") in ("GOOD", "REVIEW")
                    and _number_or_none(data.get("alignmentLoss")) is not None
                    and isinstance(data.get("words"), list)
                    and bool(data["words"])
                    and all(isinstance(word, dict)
                            and isinstance(word.get("text"), str) and bool(word["text"])
                            and isinstance(word.get("startMs"), int)
                            and isinstance(word.get("endMs"), int)
                            and (word.get("loss") is None or _number_or_none(word.get("loss")) is not None)
                            and 0 <= word["startMs"] <= word["endMs"]
                            for word in data["words"]))
        if not required:
            return "INVALID", None
        return "VALID", data
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return "INVALID", None


def inventory(manifest_path, scripts_dir, audio_dir, alignment_dir):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf8"))
    resolver = TranscriptResolver(scripts_dir)
    items = []
    for entry_id, raw_entry in manifest.get("entries", {}).items():
        entry = dict(raw_entry, id=entry_id)
        script, mapping = resolver.resolve(entry_id)
        try:
            audio_path = existing_audio_path(audio_dir, entry.get("file", ""))
            audio_path_invalid = False
        except (TypeError, ValueError):
            audio_path = None
            audio_path_invalid = True
        audio_missing = bool(entry.get("available")) and (
            audio_path_invalid or not entry.get("file") or not audio_path.is_file())
        audio_hash_mismatch = (bool(entry.get("available")) and not audio_missing
                               and hashlib.sha256(audio_path.read_bytes()).hexdigest() != entry.get("audioHash"))
        if script and script.get("computedScriptHash") != entry.get("scriptHash"):
            mapping = "SCRIPT HASH MISMATCH"
        elif script and (script.get("category") != entry.get("category")
                         or script.get("outputFile") != entry.get("file")):
            mapping = "METADATA MISMATCH"
        status, alignment = validate_alignment(
            alignment_path(alignment_dir, entry_id), entry, script["script"] if script else None)
        items.append({
            "id": entry_id, "available": bool(entry.get("available")), "file": entry.get("file"),
            "alignmentStatus": status, "qualityStatus": alignment.get("qualityStatus") if alignment else None,
            "alignmentLoss": alignment.get("alignmentLoss") if alignment else None,
            "mappingStatus": mapping, "audioMissing": audio_missing,
            "audioHashMismatch": audio_hash_mismatch,
            "audioPathInvalid": audio_path_invalid,
        })
    available = [item for item in items if item["available"]]
    return {"items": items, "totals": {
        "entries": len(items), "available": len(available),
        "valid": sum(item["alignmentStatus"] == "VALID" for item in available),
        "missing": sum(item["alignmentStatus"] == "MISSING" for item in available),
        "stale": sum(item["alignmentStatus"].startswith("STALE") for item in available),
        "invalid": sum(item["alignmentStatus"] == "INVALID" for item in available),
        "unavailable": sum(not item["available"] for item in items),
        "audioMissing": sum(item["audioMissing"] for item in items),
        "audioHashMismatch": sum(item["audioHashMismatch"] for item in items),
        "audioPathInvalid": sum(item["audioPathInvalid"] for item in items),
        "scriptMissing": sum(item["mappingStatus"] == "SCRIPT MISSING" for item in items),
        "ambiguous": sum(item["mappingStatus"] == "AMBIGUOUS" for item in items),
        "scriptHashMismatch": sum(item["mappingStatus"] == "SCRIPT HASH MISMATCH" for item in items),
        "metadataMismatch": sum(item["mappingStatus"] == "METADATA MISMATCH" for item in items),
    }}


def _number_or_none(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def convert_response(entry, transcript, response):
    if not isinstance(response, dict) or not isinstance(response.get("words"), list) or not response["words"]:
        raise ValueError("ElevenLabs returned an incomplete forced-alignment response.")
    words = []
    losses = []
    for word in response["words"]:
        if not isinstance(word, dict) or not isinstance(word.get("text"), str):
            raise ValueError("ElevenLabs returned an invalid aligned word.")
        start, end = seconds_to_ms(word.get("start")), seconds_to_ms(word.get("end"))
        if start < 0 or start > end:
            raise ValueError("ElevenLabs returned an invalid word timing range.")
        loss = _number_or_none(word.get("loss"))
        if loss is not None:
            losses.append(loss)
        words.append({"text": word["text"], "startMs": start, "endMs": end, "loss": loss})
    overall = _number_or_none(response.get("loss"))
    if overall is None:
        raise ValueError("ElevenLabs returned forced alignment without a valid overall loss.")
    # This is a review heuristic, not an ElevenLabs quality guarantee: only flag an
    # overall loss that is both conspicuously absolute and 3x the median word loss.
    median = sorted(losses)[len(losses) // 2] if losses else None
    review = overall is not None and overall > 0.5 and median is not None and overall > median * 3
    return {
        "schemaVersion": ALIGNMENT_SCHEMA_VERSION, "id": entry["id"], "text": transcript,
        "durationMs": entry.get("durationMs"), "scriptHash": entry.get("scriptHash"),
        "audioHash": entry.get("audioHash"), "alignmentLoss": overall,
        "qualityStatus": "REVIEW" if review else "GOOD", "words": words,
    }


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".alignment-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf8") as output:
            json.dump(data, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def existing_audio_path(audio_dir, relative_path):
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("The narration manifest audio path is missing.")
    root = Path(audio_dir).resolve()
    path = (root / relative_path).resolve()
    if root not in path.parents:
        raise ValueError("The narration manifest audio path is outside the audio library.")
    return path


def generate_alignment(entry_id, manifest_path, scripts_dir, audio_dir, alignment_dir, api_key, post):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf8"))
    raw_entry = manifest.get("entries", {}).get(entry_id)
    if raw_entry is None:
        raise ValueError("Narration manifest entry not found.")
    entry = dict(raw_entry, id=entry_id)
    if not entry.get("available"):
        raise ValueError("Narration audio is marked unavailable.")
    transcript, mapping = TranscriptResolver(scripts_dir).resolve(entry_id)
    if mapping != "OK":
        raise ValueError(f"Authoritative script mapping is {mapping.lower()}.")
    if transcript.get("computedScriptHash") != entry.get("scriptHash"):
        raise ValueError("The authoritative script hash does not match the narration manifest.")
    if (transcript.get("category") != entry.get("category")
            or transcript.get("outputFile") != entry.get("file")):
        raise ValueError("The authoritative script metadata does not match the narration manifest.")
    audio_path = existing_audio_path(audio_dir, entry.get("file", ""))
    if not audio_path.is_file():
        raise ValueError("The existing narration audio file is missing.")
    if hashlib.sha256(audio_path.read_bytes()).hexdigest() != entry.get("audioHash"):
        raise ValueError("The existing narration audio hash does not match the narration manifest.")
    if not api_key:
        raise ValueError("Configure the API key before generating alignment metadata.")
    try:
        with audio_path.open("rb") as audio:
            response = post(ALIGNMENT_API_URL, headers={"xi-api-key": api_key},
                            files={"file": (audio_path.name, audio, "audio/mpeg")},
                            data={"text": transcript["script"]}, timeout=180)
    except requests.RequestException as error:
        raise ValueError("ElevenLabs forced alignment could not be reached.") from error
    if not response.ok:
        if response.status_code in (401, 403):
            message = "ElevenLabs rejected the API key. Verify the local key and try again."
        elif response.status_code == 402:
            message = "ElevenLabs reported insufficient quota or a payment requirement."
        elif response.status_code == 429:
            message = "ElevenLabs rate-limited forced alignment. Wait before resuming the batch."
        else:
            message = "ElevenLabs could not complete forced alignment."
        error = ValueError(message)
        error.stop_batch = response.status_code in (401, 402, 403, 429)
        raise error
    try:
        response_data = response.json()
    except (TypeError, ValueError) as error:
        raise ValueError("ElevenLabs returned an invalid forced-alignment response.") from error
    result = convert_response(entry, transcript["script"], response_data)
    atomic_write(alignment_path(alignment_dir, entry_id), result)
    return result
