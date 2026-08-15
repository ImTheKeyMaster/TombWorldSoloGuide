import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
NARRATION = (ROOT / "narration.js").read_text()
AMBIENT = (ROOT / "ambient.js").read_text()


class RemoveUiSfxTests(unittest.TestCase):
    def test_sfx_runtime_and_configuration_are_removed(self):
        self.assertFalse((ROOT / "sfx.js").exists())
        self.assertFalse((ROOT / "Assets/Audio/Narration/sfx-config.json").exists())
        self.assertNotIn("sfx.js", INDEX)
        self.assertNotIn("sfx.js", WORKER)
        self.assertNotIn("TombWorldSfx", APP)

    def test_no_delegated_button_or_select_sfx_handlers_remain(self):
        runtime = "\n".join((APP, NARRATION, AMBIENT))
        self.assertNotIn("closest('button')", runtime)
        self.assertNotIn('closest("button")', runtime)
        self.assertNotIn("closest('select')", runtime)
        self.assertNotIn('closest("select")', runtime)
        self.assertNotRegex(runtime, r"addEventListener\?\.\(['\"]change['\"]")

    def test_service_worker_does_not_precache_sfx(self):
        for removed in ("SFX_CONFIG", "precacheSfx", "sfx-config.json", "Btn_Click.wav"):
            self.assertNotIn(removed, WORKER)
        self.assertNotIn("wav", WORKER.lower())

    def test_button_and_select_application_handlers_remain(self):
        self.assertIn("narrationSpeakerBtn.addEventListener('click'", APP)
        self.assertIn("targetSelect.addEventListener('change',renderChoices)", APP)
        self.assertIn("weaponSelect.addEventListener('change',renderChoices)", APP)

    def test_narration_ambient_ducking_and_game_audio_remain_integrated(self):
        self.assertIn("doc.addEventListener('click', gestureUnlockHandler, true)", NARRATION)
        self.assertNotIn("global.document?.addEventListener?.('click', () => { void unlock(); }, true)", AMBIENT)
        self.assertIn("global.document.addEventListener('click', onFirstAudioGesture, true)", AMBIENT)
        self.assertIn("global.document?.removeEventListener?.('click', onFirstAudioGesture, true)", AMBIENT)
        self.assertIn("global.addEventListener?.('tombworldnarrationactivity', onNarrationActivity)", AMBIENT)
        self.assertIn("TombWorldAmbient.unlock()", APP)
        self.assertIn("TombWorldAmbient.setActive", APP)
        self.assertIn("TombWorldAmbient.stop()", APP)
        self.assertIn("TombWorldNarration.setMasterEnabled(enabled)", APP)

    def test_release_and_save_versions(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
