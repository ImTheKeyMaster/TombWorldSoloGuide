import re
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class HeaderNarrationControlTests(unittest.TestCase):
    def test_release_metadata_uses_central_version(self):
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "app.js"):
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', INDEX)

    def test_header_has_accessible_enabled_and_muted_speaker_states(self):
        self.assertIn('id="narrationSpeakerBtn"', INDEX)
        self.assertIn('class="narration-icon-enabled"', INDEX)
        self.assertIn('class="narration-icon-muted"', INDEX)
        self.assertIn("narrationSpeakerBtn.querySelector('.narration-icon-enabled').hidden=!enabled", APP)
        self.assertIn("narrationSpeakerBtn.querySelector('.narration-icon-muted').hidden=enabled", APP)
        self.assertIn("narrationSpeakerBtn.setAttribute('aria-label',`Narration ${enabled?'on':'off'}`)", APP)
        self.assertIn("narrationSpeakerBtn.title=`Narration ${enabled?'on':'off'}`", APP)

    def test_header_button_directly_toggles_existing_enabled_state(self):
        self.assertIn("narrationSpeakerBtn.addEventListener('click',()=>TombWorldNarration.setEnabled(!TombWorldNarration.isEnabled()))", APP)
        self.assertIn("window.addEventListener('tombworldnarrationchange'", APP)
        self.assertIn("syncNarrationControls();", APP)

    def test_popover_and_volume_controls_are_removed(self):
        for source in (INDEX, APP, CSS):
            for removed in ('narrationPopover', 'headerNarrationVolume', 'headerNarrationVolumeValue', 'headerNarrationEnabled'):
                self.assertNotIn(removed, source)
        for attribute in ('aria-haspopup', 'aria-expanded', 'aria-controls'):
            self.assertNotIn(attribute, INDEX)

    def test_game_menu_keeps_replay_without_duplicate_preferences(self):
        menu = APP[APP.index('function showGameMenu()'):APP.index('function showAbout()')]
        self.assertIn('id="replayNarration"', menu)
        self.assertNotIn('id="narrationEnabled"', menu)
        self.assertNotIn('id="narrationVolume"', menu)
        self.assertNotIn('narrationVolumeValue', menu)

    def test_existing_unversioned_enabled_preference_is_the_only_source_of_truth(self):
        self.assertEqual(NARRATION.count("tombWorldSoloGuide.narrationEnabled"), 1)
        self.assertNotIn("tombWorldSoloGuide.narrationVolume", NARRATION)
        for source in (INDEX, APP, CSS, PERSISTENCE):
            self.assertNotIn("tombWorldSoloGuide.narrationEnabled", source)
            self.assertNotIn("tombWorldSoloGuide.narrationVolume", source)
        self.assertNotRegex(NARRATION, r"narrationEnabled.*APP_VERSION")
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_mobile_header_keeps_compact_touch_target_without_taller_header(self):
        self.assertIn("width:40px;height:40px", CSS)
        header_rule = re.search(r"\.app-header\{[^}]+\}", CSS).group(0)
        self.assertNotIn("height:", header_rule)
        self.assertIn(".brand h1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}", CSS)


if __name__ == "__main__":
    unittest.main()
