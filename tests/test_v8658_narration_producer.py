import hashlib
import importlib.util
import json
import re
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
    for path in (ROOT / "Narration" / "scripts").glob("*.json"):
        result.extend(json.loads(path.read_text(encoding="utf-8"))["scripts"])
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
        self.assertEqual([], [item["id"] for item in scripts if item["status"] == "draft"])
        mojibake_markers = ("â€™", "Ã", "Â", "â€œ", "â€")
        for item in scripts:
            normalized = item["script"].replace("\r\n", "\n").replace("\r", "\n").strip()
            self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), item["scriptHash"])
            self.assertFalse(any(marker in item["script"] for marker in mojibake_markers), item["id"])
        reanimation = next(item for item in scripts if item["id"] == "event.reanimation-protocols")
        self.assertEqual(
            "The fallen begin to move.\n\n"
            "Emerald light returns to darkened eyes. Bodies that should lie silent rise again, driven by ancient systems that refuse to accept their destruction.\n\n"
            "For a time, death may not be enough to stop the tomb’s defenders.",
            reanimation["script"],
        )
        self.assertNotIn("The mission is won. You have overcome", " ".join(item["script"] for item in scripts))

    def test_generated_sources_manifest_metadata_and_audio_stay_synchronized(self):
        scripts = {item["id"]: item for item in records()}
        entries = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text(encoding="utf-8"))["entries"]
        self.assertEqual(set(scripts), set(entries))
        for script_id, item in scripts.items():
            entry = entries[script_id]
            generated = item["status"] == "generated"
            self.assertEqual(generated, entry.get("available"), script_id)
            if not generated:
                self.assertEqual(item["outputFile"], entry.get("file"), script_id)
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

        mission_intros = {
            script_id: item
            for script_id, item in scripts.items()
            if script_id.startswith("mission.")
        }
        self.assertEqual(6, len(mission_intros))
        self.assertTrue(all(item["status"] == "generated" for item in mission_intros.values()))
        self.assertTrue(all(entries[script_id]["available"] is True for script_id in mission_intros))

        events = {script_id: item for script_id, item in scripts.items() if script_id.startswith("event.")}
        self.assertEqual(14, len(events))
        generated_events = {script_id for script_id, item in events.items() if item["status"] == "generated"}
        self.assertEqual(11, len(generated_events))
        self.assertTrue(all(entries[script_id]["available"] is True for script_id in generated_events))

    def test_producer_selection_is_approval_driven_not_pilot_id_driven(self):
        browser = (TOOL / "static" / "producer.js").read_text(encoding="utf-8")
        markup = (TOOL / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("x.status==='approved'&&!x.reviewRequired", browser)
        self.assertIn('id="approved">Select Approved', markup)
        self.assertNotIn("Select Pilot Batch", markup)

        approved = [item["id"] for item in records() if item["status"] == "approved"]
        deadly = [item["id"] for item in records() if item["category"] == "deadly-encounter"]
        self.assertEqual(
            [
                "event.flesh-hunger",
                "event.rewards-of-annihilation",
                "event.enforcer-of-the-phaerons",
            ],
            approved,
        )
        self.assertEqual(16, len(deadly))
        self.assertTrue(all(item["status"] == "generated" for item in records() if item["category"] == "deadly-encounter"))

    def test_deadly_encounter_filter_and_generated_library(self):
        markup = (TOOL / "static" / "index.html").read_text(encoding="utf-8")
        browser = (TOOL / "static" / "producer.js").read_text(encoding="utf-8")
        self.assertIn('<option value="deadly-encounter">Deadly Encounters</option>', markup)
        self.assertIn("filter==='all'||x.category===filter", browser)

        deadly = [item for item in records() if item["category"] == "deadly-encounter"]
        self.assertEqual(16, len(deadly))
        self.assertEqual(8, sum(item["id"].startswith("deadly.room-") for item in deadly))
        self.assertEqual(8, sum(item["id"].startswith("deadly.objective-") for item in deadly))
        self.assertEqual(16, len({item["outputFile"] for item in deadly}))
        self.assertTrue(all(item["status"] == "generated" for item in deadly))
        self.assertNotIn("deadly.unusual", {item["id"] for item in deadly})

        definitions = (ROOT / "deadly-encounters.js").read_text(encoding="utf-8")
        feature_ids = set(re.findall(r"feature\('((?:room|objective)-[^']+)'", definitions))
        narration_features = {item["id"].removeprefix("deadly.") for item in deadly}
        self.assertEqual(feature_ids - {"unusual"}, narration_features)

        entries = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text(encoding="utf-8"))["entries"]
        expected_settings_hash = "196a72c39105991a6ac156aa94c746726cbc583947f7e491ba50da98b3a1117f"
        for item in deadly:
            normalized = item["script"].replace("\r\n", "\n").replace("\r", "\n").strip()
            self.assertEqual(hashlib.sha256(normalized.encode("utf-8")).hexdigest(), item["scriptHash"])
            entry = entries[item["id"]]
            self.assertTrue(entry["available"])
            self.assertEqual(item["outputFile"], entry["file"])
            self.assertEqual(item["scriptHash"], entry["scriptHash"])
            self.assertEqual(item["id"].removeprefix("deadly."), entry["deadlyEncounterFeatureId"])
            audio = ROOT / "Assets" / "Audio" / "Narration" / entry["file"]
            self.assertTrue(audio.is_file(), item["id"])
            self.assertEqual(hashlib.sha256(audio.read_bytes()).hexdigest(), entry["audioHash"])
            self.assertGreater(entry["durationMs"], 0)
            for key in ("settingsHash", "generationHash", "audioHash"):
                self.assertEqual(item[key], entry[key], f"{item['id']}: {key}")
            self.assertEqual(expected_settings_hash, item["settingsHash"])
            self.assertEqual(
                hashlib.sha256(f"{item['scriptHash']}:{item['settingsHash']}".encode("utf-8")).hexdigest(),
                item["generationHash"],
            )
            self.assertEqual("keNGlRe631vnQRvGXasN", item["voiceId"])
            self.assertEqual("eleven_multilingual_v2", item["modelId"])
            if server is not None:
                self.assertEqual(server.validate_audio(audio), entry["durationMs"])

        expected_scripts = {
            "deadly.room-darkness": "The light dies as you enter.\n\nBeyond a few meters, the chamber disappears into absolute black. Shapes become shadows, distances become uncertain, and even the metallic walls of the tomb seem to vanish into the void.\n\nWhatever waits beyond the darkness is hidden from sight.",
            "deadly.room-gravitic-anomaly": "Gravity twists.\n\nArmor suddenly feels lighter. Bodies move farther with every step, yet weapons strike with strangely diminished force as a distorted field pulls at everything within the chamber.\n\nThe laws of weight and momentum have changed here.",
            "deadly.objective-control-node": "The dormant console awakens.\n\nStreams of emerald symbols race across its surface as ancient command channels come back online. Somewhere deeper in the complex, systems begin responding to whoever controls this position.\n\nThis node offers access to the ancient command network.",
        }
        self.assertEqual(expected_scripts, {item["id"]: item["script"] for item in deadly if item["id"] in expected_scripts})

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
        chosen = json.loads((ROOT / "Narration/producer-settings.json").read_text(encoding="utf-8"))
        chosen["voiceId"] = "test-voice"

        current = server.library()
        generated = next(item for item in current if item["id"] == "mission.01.intro")
        draft = dict(
            next(item for item in current if item["id"] == "mission.04.intro"),
            status="draft",
            reviewRequired=False,
        )

        with mock.patch.object(server, "library", return_value=[generated, draft]):
            with mock.patch.object(server.requests, "post") as tts:
                data = self.client.post(
                    "/api/dry-run",
                    json={
                        "ids": ["mission.01.intro", "mission.04.intro"],
                        "settings": chosen,
                    },
                ).get_json()

        tts.assert_not_called()
        self.assertEqual(2, data["totals"]["selected"])
        self.assertEqual(1, data["totals"]["blocked"])
        self.assertEqual(2, data["totals"]["approved"] + data["totals"]["blocked"])
        self.assertGreater(data["totals"]["totalCharacters"], 0)

    def test_deadly_encounters_are_generated_and_up_to_date(self):
        chosen = json.loads((ROOT / "Narration/producer-settings.json").read_text(encoding="utf-8"))
        deadly_ids = [item["id"] for item in server.library() if item["category"] == "deadly-encounter"]

        with mock.patch.object(server.requests, "post") as tts:
            data = self.client.post(
                "/api/dry-run",
                json={"ids": deadly_ids, "settings": chosen},
            ).get_json()

        tts.assert_not_called()
        self.assertEqual(16, data["totals"]["selected"])
        self.assertEqual(16, data["totals"]["approved"])
        self.assertEqual(0, data["totals"]["wouldGenerate"])
        self.assertEqual(0, data["totals"]["blocked"])
        self.assertEqual(16, data["totals"]["wouldSkip"])

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
