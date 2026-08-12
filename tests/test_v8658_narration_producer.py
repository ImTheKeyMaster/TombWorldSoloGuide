import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
TOOL = ROOT / "tools" / "narration-producer"

try:
    import flask  # noqa: F401
    import requests  # noqa: F401
    import dotenv  # noqa: F401
    import mutagen  # noqa: F401
except ImportError:
    server = None
else:
    spec = importlib.util.spec_from_file_location("producer_server", TOOL / "server.py")
    server = importlib.util.module_from_spec(spec)
    sys.modules["producer_server"] = server
    spec.loader.exec_module(server)


def records():
    result = []
    for name in ("missions.json", "events.json", "outcomes.json"):
        result.extend(json.loads((ROOT / "Narration" / "scripts" / name).read_text(encoding="utf-8"))["scripts"])
    return result


class ProducerStaticTests(unittest.TestCase):
    def test_windows_structure_and_local_binding(self):
        self.assertTrue((ROOT / "SETUP_NARRATION_PRODUCER.bat").exists())
        self.assertTrue((ROOT / "RUN_NARRATION_PRODUCER.bat").exists())
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("narration-producer/.env", ignored)
        self.assertIn("narration-producer/.venv/", ignored)
        source = (TOOL / "server.py").read_text(encoding="utf-8")
        self.assertIn("host='127.0.0.1'", source)
        self.assertNotIn("host='0.0.0.0'", source)
        self.assertEqual("ELEVENLABS_API_KEY=\n", (TOOL / ".env.example").read_text(encoding="utf-8"))

    def test_canonical_library_and_hashes(self):
        scripts = records()
        self.assertEqual(29, len(scripts))
        self.assertEqual(["mission.04.intro"], [item["id"] for item in scripts if item["status"] == "draft"])
        for item in scripts:
            normalized = item["script"].replace("\r\n", "\n").replace("\r", "\n").strip()
            self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), item["scriptHash"])
        reanimation = next(item for item in scripts if item["id"] == "event.reanimation-protocols")
        self.assertIn("For a time, death may not be enough", reanimation["script"])
        self.assertNotIn("The mission is won. You have overcome", " ".join(item["script"] for item in scripts))

    def test_generated_sources_manifest_metadata_and_audio_stay_synchronized(self):
        scripts = {item["id"]: item for item in records()}
        entries = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text())["entries"]
        self.assertEqual(29, len(entries))
        self.assertEqual(set(scripts), set(entries))
        for script_id, item in scripts.items():
            entry = entries[script_id]
            generated = item["status"] == "generated"
            self.assertEqual(generated, entry.get("available"), script_id)
            if not generated:
                self.assertIsNone(entry.get("file"), script_id)
                continue
            self.assertTrue(item.get("outputFile"), script_id)
            self.assertEqual(item["outputFile"], entry.get("file"), script_id)
            audio = ROOT / "Assets" / "Audio" / "Narration" / item["outputFile"]
            self.assertTrue(audio.is_file() and audio.stat().st_size > 0, script_id)
            for key in ("scriptHash", "settingsHash", "generationHash", "audioHash"):
                self.assertTrue(item.get(key), f"{script_id}: source {key}")
                self.assertEqual(item[key], entry.get(key), f"{script_id}: manifest {key}")
            self.assertTrue(item.get("voiceId"), script_id)
            self.assertTrue(item.get("modelId"), script_id)
            self.assertGreater(entry.get("durationMs", 0), 0, script_id)
            self.assertEqual(hashlib.sha256(audio.read_bytes()).hexdigest(), item["audioHash"], script_id)

    def test_producer_selection_is_approval_driven_not_pilot_id_driven(self):
        browser = (TOOL / "static" / "producer.js").read_text(encoding="utf-8")
        markup = (TOOL / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("x.status==='approved'&&!x.reviewRequired", browser)
        self.assertIn('id="approved">Select Approved', markup)
        self.assertNotIn("Select Pilot Batch", markup)

    def test_browser_has_no_secret_or_direct_tts_call(self):
        browser = (TOOL / "static" / "producer.js").read_text(encoding="utf-8")
        self.assertNotIn("ELEVENLABS_API_KEY", browser)
        self.assertNotIn("api.elevenlabs.io", browser)
        self.assertNotIn("xi-api-key", browser)


@unittest.skipIf(server is None, "Producer dependencies are not installed")
class ProducerApiTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_status_never_exposes_key(self):
        with mock.patch.object(server, "key", return_value="SECRET_TEST_KEY"):
            body = self.client.get("/api/status").get_data(as_text=True)
        self.assertNotIn("SECRET_TEST_KEY", body)
        self.assertIn('"apiKeyConfigured":true', body)

    def test_dry_run_never_calls_tts_and_blocks_draft_without_key(self):
        chosen = json.loads((ROOT / "Narration/producer-settings.json").read_text())
        chosen["voiceId"] = "test-voice"
        with mock.patch.object(server.requests, "post") as tts:
            data = self.client.post("/api/dry-run", json={"ids": ["mission.01.intro", "mission.04.intro"], "settings": chosen}).get_json()
        tts.assert_not_called()
        self.assertEqual(2, data["totals"]["selected"])
        self.assertEqual(1, data["totals"]["blocked"])
        self.assertEqual(2, data["totals"]["approved"] + data["totals"]["blocked"])
        self.assertGreater(data["totals"]["totalCharacters"], 0)

    def test_generation_and_force_generation_require_confirmation(self):
        self.assertEqual(400, self.client.post("/api/generate", json={"ids": []}).status_code)
        response = self.client.post("/api/generate", json={"ids": [], "confirmation": True, "force": True})
        self.assertEqual(400, response.status_code)

    def test_secret_settings_and_outside_writes_are_rejected(self):
        response = self.client.post("/api/settings", json={"voiceSettings": {"apiKey": "secret"}})
        self.assertEqual(400, response.status_code)
        with self.assertRaises(ValueError):
            server.allowed_write(ROOT / "README.md")

    def test_changed_approved_script_is_review_required(self):
        item = next(item for item in server.library() if item["id"] == "mission.01.intro")
        changed = dict(item, script=item["script"] + " Changed.")
        self.assertNotEqual(server.digest(server.normalize(changed["script"])), changed["scriptHash"])


if __name__ == "__main__":
    unittest.main()
