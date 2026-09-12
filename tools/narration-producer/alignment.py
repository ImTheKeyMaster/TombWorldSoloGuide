"""Forced-alignment harvesting for the local Narration Producer."""
from __future__ import annotations

import json
import hashlib
import math
import os
import re
import tempfile
from pathlib import Path

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


def validate_alignment(path, entry):
    path = Path(path)
    if not path.exists():
        return "MISSING", None
    try:
        data = json.loads(path.read_text(encoding="utf8"))
        required = (data.get("schemaVersion") == ALIGNMENT_SCHEMA_VERSION
                    and data.get("id") == entry["id"]
                    and isinstance(data.get("text"), str)
                    and isinstance(data.get("durationMs"), int)
                    and isinstance(data.get("words"), list)
                    and all(isinstance(word, dict)
                            and isinstance(word.get("text"), str)
                            and isinstance(word.get("startMs"), int)
                            and isinstance(word.get("endMs"), int)
                            and word["startMs"] <= word["endMs"]
                            for word in data["words"]))
        if not required:
            return "INVALID", None
        if data.get("scriptHash") != entry.get("scriptHash"):
            return "STALE SCRIPT", data
        if data.get("audioHash") != entry.get("audioHash"):
            return "STALE AUDIO", data
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
        audio_path = Path(audio_dir) / entry.get("file", "")
        audio_missing = bool(entry.get("available")) and (not entry.get("file") or not audio_path.is_file())
        audio_hash_mismatch = (bool(entry.get("available")) and not audio_missing
                               and hashlib.sha256(audio_path.read_bytes()).hexdigest() != entry.get("audioHash"))
        if script and script.get("computedScriptHash") != entry.get("scriptHash"):
            mapping = "SCRIPT HASH MISMATCH"
        status, alignment = validate_alignment(alignment_path(alignment_dir, entry_id), entry)
        items.append({
            "id": entry_id, "available": bool(entry.get("available")), "file": entry.get("file"),
            "alignmentStatus": status, "qualityStatus": alignment.get("qualityStatus") if alignment else None,
            "alignmentLoss": alignment.get("alignmentLoss") if alignment else None,
            "mappingStatus": mapping, "audioMissing": audio_missing,
            "audioHashMismatch": audio_hash_mismatch,
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
        "scriptMissing": sum(item["mappingStatus"] == "SCRIPT MISSING" for item in items),
        "ambiguous": sum(item["mappingStatus"] == "AMBIGUOUS" for item in items),
        "scriptHashMismatch": sum(item["mappingStatus"] == "SCRIPT HASH MISMATCH" for item in items),
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
        if start > end:
            raise ValueError("ElevenLabs returned an invalid word timing range.")
        loss = _number_or_none(word.get("loss"))
        if loss is not None:
            losses.append(loss)
        words.append({"text": word["text"], "startMs": start, "endMs": end, "loss": loss})
    overall = _number_or_none(response.get("loss"))
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
    audio_path = Path(audio_dir) / entry.get("file", "")
    if not audio_path.is_file():
        raise ValueError("The existing narration audio file is missing.")
    if hashlib.sha256(audio_path.read_bytes()).hexdigest() != entry.get("audioHash"):
        raise ValueError("The existing narration audio hash does not match the narration manifest.")
    if not api_key:
        raise ValueError("Configure the API key before generating alignment metadata.")
    with audio_path.open("rb") as audio:
        response = post(ALIGNMENT_API_URL, headers={"xi-api-key": api_key},
                        files={"file": (audio_path.name, audio, "audio/mpeg")},
                        data={"text": transcript["script"]}, timeout=180)
    if not response.ok:
        error = ValueError("ElevenLabs could not complete forced alignment.")
        error.stop_batch = response.status_code in (401, 402, 403, 429)
        raise error
    result = convert_response(entry, transcript["script"], response.json())
    atomic_write(alignment_path(alignment_dir, entry_id), result)
    return result
