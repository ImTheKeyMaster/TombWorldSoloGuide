from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")


class GameAudioMenuTests(unittest.TestCase):
    def test_menu_uses_ambient_style_narration_toggle_without_speaker_icon(self):
        self.assertIn('id="narrationToggle"', APP)
        self.assertIn('<span id="narrationLabel">Narration</span>', APP)
        self.assertIn('class="ambient-toggle" id="narrationToggle"', APP)
        self.assertIn('role="switch" aria-labelledby="narrationLabel" aria-checked=', APP)
        self.assertEqual(APP.count('class="ambient-toggle-row"'), 2)
        self.assertNotIn('game-audio-btn', APP + STYLES)
        self.assertNotIn('game-audio-label', APP)

    def test_audio_toggle_labels_and_controls_both_audio_sources(self):
        self.assertIn("narrationToggle.setAttribute('aria-checked',String(narrationEnabled))", APP)
        self.assertIn("narrationToggle.querySelector('.ambient-toggle-state').textContent=narrationEnabled?'On':'Off'", APP)
        self.assertIn('async function setGameAudioEnabled(enabled)', APP)
        self.assertIn('TombWorldNarration.setMasterEnabled(enabled);', APP)
        self.assertIn('TombWorldAmbient.stop();', APP)
        self.assertIn('reconcileAmbientActiveState();', APP)
        self.assertIn('await Promise.allSettled', APP)
        self.assertEqual(APP.count('await setGameAudioEnabled(enabled);'), 1)

    def test_release_version_is_current(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', index)


if __name__ == "__main__":
    unittest.main()
