import hashlib
import json
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


class AttenuatedAmbientReleaseTests(unittest.TestCase):
    def test_release_version_and_cache_busting(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertEqual((8, 6, 96), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"V{CURRENT_APP_VERSION}", index)
        self.assertNotIn("?v=8.6.95", index)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertIn("const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;", worker)

    def test_supplied_track_is_used_unchanged(self):
        original = ROOT / "Assets/Audio/Narration/Ambient/caverns.ogg"
        attenuated = ROOT / "Assets/Audio/Narration/Ambient/caverns_50.ogg"
        self.assertTrue(original.is_file())
        self.assertEqual(
            "9ec2456fa97713aebcef7ff0d5c1b15727c070abaa6ac70a2434e83d14fbb0b9",
            hashlib.sha256(attenuated.read_bytes()).hexdigest(),
        )

    def test_only_ambient_file_configuration_changed(self):
        config = json.loads(
            (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {
                "schemaVersion": 1,
                "file": "Ambient/caverns_50.ogg",
                "normalGain": 0.22,
                "duckGain": 0.055,
                "fadeInMs": 1500,
                "fadeOutMs": 800,
                "duckAttackMs": 250,
                "duckReleaseMs": 700,
                "loopStartSeconds": 0,
                "loopEndSeconds": None,
            },
            config,
        )

    def test_audio_architecture_and_offline_precache_are_preserved(self):
        ambient = (ROOT / "ambient.js").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        persistence = (ROOT / "persistence.js").read_text(encoding="utf-8")
        self.assertIn("const audio = new global.Audio();", ambient)
        self.assertNotIn("AudioContext", ambient)
        self.assertIn("await precacheAmbient(cache);", worker)
        self.assertIn("await cache.add(`./Assets/Audio/Narration/${file}`);", worker)
        self.assertIn("const SAVE_VERSION = 3;", persistence)


if __name__ == "__main__":
    unittest.main()
