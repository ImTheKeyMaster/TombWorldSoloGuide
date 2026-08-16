import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


class IOSAmbientForegroundRecoveryTests(unittest.TestCase):
    def test_release_version_and_save_schema(self):
        self.assertEqual((8, 6, 91), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))

    def test_foreground_recovery_is_explicitly_signaled_to_the_coordinator(self):
        ambient = (ROOT / "ambient.js").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("recoveryRequired = true", ambient)
        self.assertIn("tombworldaudiorecoveryrequired", ambient)
        self.assertNotIn("addEventListener('click'", ambient)
        self.assertIn("window.addEventListener('tombworldaudiorecoveryrequired',armAudioGestureRecovery)", app)
        self.assertIn("needsAudioGestureRecovery", app)
        self.assertEqual(1, app.count("document.addEventListener('click',audioRecoveryHandler,true)"))
        self.assertIn("removeAudioGestureRecovery()", app)

    def test_narration_is_not_started_or_modified_by_ambient_recovery(self):
        ambient = (ROOT / "ambient.js").read_text(encoding="utf-8")
        self.assertNotIn("playMissionIntro", ambient)
        self.assertNotIn("setPreferenceEnabled", ambient)
        self.assertIn("tombworldnarrationactivity", ambient)


if __name__ == "__main__":
    unittest.main()
