import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "tools" / "narration-producer"
sys.path.insert(0, str(PRODUCER))
SPEC = importlib.util.spec_from_file_location("narration_alignment", PRODUCER / "alignment.py")
alignment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alignment)


class Response:
    ok = True
    status_code = 200

    def json(self):
        return {"loss": 0.1, "characters": [], "words": [
            {"text": "Exact", "start": 0.1234, "end": 0.5678, "loss": 0.02},
            {"text": "text.", "start": 0.5678, "end": 1.001, "loss": 0.03},
        ]}


class NarrationAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.scripts = self.root / "scripts"
        self.audio = self.root / "audio"
        self.output = self.audio / "alignment"
        self.scripts.mkdir()
        self.audio.mkdir()
        self.audio_file = self.audio / "sample.mp3"
        self.audio_file.write_bytes(b"unchanged existing mp3 bytes")
        self.script_hash = hashlib.sha256(b"Exact text.").hexdigest()
        self.audio_hash = hashlib.sha256(self.audio_file.read_bytes()).hexdigest()
        (self.scripts / "events.json").write_text(json.dumps({"scripts": [{
            "id": "event.sample", "category": "event", "script": "Exact text.",
            "scriptHash": self.script_hash,
        }]}), encoding="utf8")
        self.manifest = self.audio / "narration-manifest.json"
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self, **changes):
        entry = {"file": "sample.mp3", "available": True, "scriptHash": self.script_hash,
                 "audioHash": self.audio_hash, "durationMs": 1001}
        entry.update(changes)
        self.manifest.write_text(json.dumps({"entries": {"event.sample": entry}}), encoding="utf8")

    def generate(self, post=Mock(return_value=Response())):
        return alignment.generate_alignment("event.sample", self.manifest, self.scripts,
                                            self.audio, self.output, "test-only-key", post)

    def test_every_available_repository_manifest_entry_maps_exactly(self):
        manifest = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text())
        resolver = alignment.TranscriptResolver(ROOT / "Narration/scripts")
        for entry_id, entry in manifest["entries"].items():
            if not entry.get("available"):
                continue
            record, status = resolver.resolve(entry_id)
            self.assertEqual("OK", status, entry_id)
            self.assertEqual(entry["scriptHash"], record["computedScriptHash"], entry_id)

    def test_safe_deterministic_path_and_millisecond_rounding(self):
        self.assertEqual(self.output / "mission.03.intro.json",
                         alignment.alignment_path(self.output, "mission.03.intro"))
        self.assertEqual(self.output / "unsafe_id.json",
                         alignment.alignment_path(self.output, "unsafe/id"))
        self.assertEqual(1234, alignment.seconds_to_ms(1.2344))
        self.assertEqual(1235, alignment.seconds_to_ms(1.2346))

    def test_generated_schema_copies_hashes_and_never_contains_api_key(self):
        result = self.generate()
        saved = json.loads(alignment.alignment_path(self.output, "event.sample").read_text())
        self.assertEqual(result, saved)
        self.assertEqual({"schemaVersion", "id", "text", "durationMs", "scriptHash",
                          "audioHash", "alignmentLoss", "qualityStatus", "words"}, set(saved))
        self.assertEqual(self.script_hash, saved["scriptHash"])
        self.assertEqual(self.audio_hash, saved["audioHash"])
        self.assertEqual("Exact text.", saved["text"])
        self.assertEqual(123, saved["words"][0]["startMs"])
        self.assertNotIn("test-only-key", json.dumps(saved))

    def test_missing_valid_stale_and_malformed_detection(self):
        path = alignment.alignment_path(self.output, "event.sample")
        entry = dict(json.loads(self.manifest.read_text())["entries"]["event.sample"], id="event.sample")
        self.assertEqual("MISSING", alignment.validate_alignment(path, entry)[0])
        self.generate()
        self.assertEqual("VALID", alignment.validate_alignment(path, entry)[0])
        changed = dict(entry, scriptHash="new")
        self.assertEqual("STALE SCRIPT", alignment.validate_alignment(path, changed)[0])
        changed = dict(entry, audioHash="new")
        self.assertEqual("STALE AUDIO", alignment.validate_alignment(path, changed)[0])
        path.write_text("not JSON")
        self.assertEqual("INVALID", alignment.validate_alignment(path, entry)[0])

    def test_validation_requires_the_exact_transcript_and_manifest_duration(self):
        self.generate()
        path = alignment.alignment_path(self.output, "event.sample")
        entry = dict(json.loads(self.manifest.read_text())["entries"]["event.sample"], id="event.sample")
        self.assertEqual("VALID", alignment.validate_alignment(path, entry, "Exact text.")[0])
        self.assertEqual("INVALID", alignment.validate_alignment(path, entry, "Different text.")[0])
        self.assertEqual("INVALID", alignment.validate_alignment(path, dict(entry, durationMs=999), "Exact text.")[0])

    def test_inventory_supports_skip_and_resume(self):
        first = alignment.inventory(self.manifest, self.scripts, self.audio, self.output)
        self.assertEqual(1, first["totals"]["missing"])
        self.generate()
        resumed = alignment.inventory(self.manifest, self.scripts, self.audio, self.output)
        self.assertEqual(1, resumed["totals"]["valid"])
        self.assertEqual([], [item for item in resumed["items"]
                              if item["alignmentStatus"] in ("MISSING", "STALE SCRIPT", "STALE AUDIO")])

    def test_stale_alignment_is_eligible_for_regeneration(self):
        self.generate()
        old = json.loads(alignment.alignment_path(self.output, "event.sample").read_text())
        old["audioHash"] = "old"
        alignment.atomic_write(alignment.alignment_path(self.output, "event.sample"), old)
        self.assertEqual("STALE AUDIO", alignment.inventory(
            self.manifest, self.scripts, self.audio, self.output)["items"][0]["alignmentStatus"])
        self.generate()
        self.assertEqual("VALID", alignment.inventory(
            self.manifest, self.scripts, self.audio, self.output)["items"][0]["alignmentStatus"])

    def test_mocked_api_failure_does_not_write_alignment_or_damage_audio(self):
        response = Response()
        response.ok = False
        response.status_code = 429
        before = hashlib.sha256(self.audio_file.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.generate(Mock(return_value=response))
        self.assertFalse(alignment.alignment_path(self.output, "event.sample").exists())
        self.assertEqual(before, hashlib.sha256(self.audio_file.read_bytes()).hexdigest())

    def test_generation_posts_existing_audio_and_exact_text(self):
        post = Mock(return_value=Response())
        self.generate(post)
        self.assertEqual(alignment.ALIGNMENT_API_URL, post.call_args.args[0])
        self.assertEqual("Exact text.", post.call_args.kwargs["data"]["text"])
        self.assertEqual("test-only-key", post.call_args.kwargs["headers"]["xi-api-key"])

    def test_manifest_cannot_read_audio_outside_the_library(self):
        self.write_manifest(file="../outside.mp3")
        with self.assertRaisesRegex(ValueError, "outside the audio library"):
            self.generate()

    def test_connection_and_non_json_failures_do_not_write_output(self):
        with self.assertRaisesRegex(ValueError, "could not be reached"):
            self.generate(Mock(side_effect=RuntimeError("secret transport detail")))
        response = Response()
        response.json = Mock(side_effect=ValueError("not JSON"))
        with self.assertRaisesRegex(ValueError, "invalid forced-alignment response"):
            self.generate(Mock(return_value=response))
        self.assertFalse(alignment.alignment_path(self.output, "event.sample").exists())


if __name__ == "__main__":
    unittest.main()
