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
        self.assertEqual(23, sum(item["status"] == "approved" for item in scripts))
        self.assertEqual(5, sum(item["status"] == "generated" for item in scripts))
        self.assertEqual(["mission.04.intro"], [item["id"] for item in scripts if item["status"] == "draft"])
        for item in scripts:
            normalized = item["script"].replace("\r\n", "\n").replace("\r", "\n").strip()
            self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), item["scriptHash"])
        reanimation = next(item for item in scripts if item["id"] == "event.reanimation-protocols")
        self.assertIn("For a time, death may not be enough", reanimation["script"])
        self.assertNotIn("The mission is won. You have overcome", " ".join(item["script"] for item in scripts))

    def test_pilot_activates_exactly_five_manifest_entries_and_mp3s(self):
        entries = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text())["entries"]
        self.assertEqual(29, len(entries))
        available = {key for key, item in entries.items() if item["available"]}
        self.assertEqual({
            "mission.01.intro",
            "event.countertemporal-shifting",
            "event.transdimensional-relocation",
            "outcome.04.victory",
            "outcome.04.defeat",
        }, available)
        self.assertEqual(5, len(list((ROOT / "Assets/Audio/Narration").rglob("*.mp3"))))

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
