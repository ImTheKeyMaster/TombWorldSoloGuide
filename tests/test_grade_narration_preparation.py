import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).parents[1]
TOOL = ROOT / "tools" / "narration-producer"
GRADE_SOURCE = ROOT / "Narration" / "scripts" / "grades.json"

APPROVED_SCRIPTS = {
    "grade.1.stirring": (
        "Deep within the crypt, dormant systems answer the intrusion.\n\n"
        "Emerald lights flicker into life. Ancient machines begin to move, slow and deliberate, as the tomb turns its attention toward the living.\n\n"
        "The awakening has begun."
    ),
    "grade.2.awakened": (
        "The signal spreads through the tomb.\n\n"
        "More systems come online. More guardians rise. The silence of the crypt gives way to the measured rhythm of a war machine returning to life.\n\n"
        "The Tomb World is awake."
    ),
    "grade.3.overrun": (
        "The tomb answers in force.\n\n"
        "Ancient defenses converge through every passage as the crypt pulses with hostile purpose. What began as an intrusion has become open war.\n\n"
        "The Tomb World is fully awake.\n\n"
        "There will be no silence now. Only war."
    ),
}


try:
    import dotenv  # noqa: F401
    import flask  # noqa: F401
    import mutagen  # noqa: F401
    import requests  # noqa: F401
except ModuleNotFoundError:
    server = None
else:
    spec = importlib.util.spec_from_file_location("grade_producer_server", TOOL / "server.py")
    server = importlib.util.module_from_spec(spec)
    sys.modules["grade_producer_server"] = server
    spec.loader.exec_module(server)


class GradeNarrationPreparationTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(GRADE_SOURCE.read_text(encoding="utf-8"))
        self.grades = self.source["scripts"]
        self.manifest = json.loads(
            (ROOT / "Assets" / "Audio" / "Narration" / "narration-manifest.json").read_text(encoding="utf-8")
        )["entries"]

    def test_source_contains_exactly_the_three_approved_grade_scripts(self):
        self.assertEqual(1, self.source["schemaVersion"])
        self.assertEqual(list(APPROVED_SCRIPTS), [item["id"] for item in self.grades])
        self.assertEqual({"grade"}, {item["category"] for item in self.grades})
        self.assertEqual({"generated"}, {item["status"] for item in self.grades})
        self.assertEqual(APPROVED_SCRIPTS, {item["id"]: item["script"] for item in self.grades})
        self.assertEqual(3, len({item["outputFile"] for item in self.grades}))

        all_grades = []
        for path in (ROOT / "Narration" / "scripts").glob("*.json"):
            records = json.loads(path.read_text(encoding="utf-8"))["scripts"]
            all_grades.extend(item for item in records if item["category"] == "grade")
        self.assertEqual(list(APPROVED_SCRIPTS), [item["id"] for item in all_grades])

    def test_generated_metadata_and_manifest_match_exact_audio(self):
        settings = json.loads((ROOT / "Narration" / "producer-settings.json").read_text(encoding="utf-8"))
        expected_settings_hash = server.settings_hash(settings) if server else "196a72c39105991a6ac156aa94c746726cbc583947f7e491ba50da98b3a1117f"
        for grade, item in enumerate(self.grades, 1):
            normalized = item["script"].replace("\r\n", "\n").replace("\r", "\n").strip()
            expected_script_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            expected_generation_hash = hashlib.sha256(
                f"{expected_script_hash}:{expected_settings_hash}".encode("utf-8")
            ).hexdigest()
            audio = ROOT / "Assets" / "Audio" / "Narration" / item["outputFile"]
            expected_audio_hash = hashlib.sha256(audio.read_bytes()).hexdigest()

            self.assertEqual("generated", item["status"])
            self.assertEqual(expected_script_hash, item["scriptHash"])
            self.assertEqual(expected_settings_hash, item["settingsHash"])
            self.assertEqual(expected_generation_hash, item["generationHash"])
            self.assertEqual(expected_audio_hash, item["audioHash"])
            self.assertEqual(settings["voiceId"], item["voiceId"])
            self.assertEqual(settings["modelId"], item["modelId"])
            self.assertTrue(audio.is_file())
            self.assertGreater(audio.stat().st_size, 0)

            entry = self.manifest[item["id"]]
            self.assertEqual("grade", entry["category"])
            self.assertEqual(grade, entry["grade"])
            self.assertEqual(item["outputFile"], entry["file"])
            self.assertTrue(entry["available"])
            for key in ("scriptHash", "settingsHash", "generationHash", "audioHash"):
                self.assertEqual(item[key], entry[key])
            self.assertGreater(entry["durationMs"], 0)
            if server:
                self.assertEqual(server.validate_audio(audio), entry["durationMs"])

    def test_producer_filter_and_generic_library_discovery(self):
        markup = (TOOL / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<option value="grade">Threat Escalation</option>', markup)
        if server is None:
            self.skipTest("Producer dependencies are not installed")
        discovered = [item for item in server.library() if item["category"] == "grade"]
        self.assertEqual(list(APPROVED_SCRIPTS), [item["id"] for item in discovered])
        self.assertTrue(all(item["fileSource"] == "grades.json" for item in discovered))

    def test_dry_run_marks_all_grades_ready_with_valid_settings(self):
        if server is None:
            self.skipTest("Producer dependencies are not installed")
        settings = json.loads((ROOT / "Narration" / "producer-settings.json").read_text(encoding="utf-8"))
        rows = server.plan(set(APPROVED_SCRIPTS), settings)
        self.assertEqual(list(APPROVED_SCRIPTS), [item["id"] for item in rows])
        self.assertTrue(all(item["approved"] for item in rows))
        self.assertTrue(all(not item["blocked"] for item in rows))
        self.assertTrue(all(item["wouldSkip"] for item in rows))
        self.assertTrue(all(item["reason"] == "Up to date." for item in rows))

    def test_runtime_and_versions_remain_unchanged(self):
        runtime = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ROOT.glob("*.js")
        )
        self.assertIn("playGradeEscalation", runtime)
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        persistence = (ROOT / "persistence.js").read_text(encoding="utf-8")
        self.assertEqual((8, 6, 101), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", app)
        self.assertEqual("3", re.search(r"SAVE_VERSION = (\d+)", persistence).group(1))


if __name__ == "__main__":
    unittest.main()
