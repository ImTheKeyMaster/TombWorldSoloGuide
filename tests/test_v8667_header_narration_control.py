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
        self.assertIn("`Narration ${enabled?'on':'off'}. Open volume controls`", APP)

    def test_popover_opens_and_closes_by_button_outside_click_and_escape(self):
        self.assertRegex(INDEX, r'id="narrationPopover"[^>]* hidden')
        self.assertIn("narrationPopover.hidden=!opening", APP)
        self.assertIn("!event.target.closest('.narration-header-control')", APP)
        self.assertIn("event.key==='Escape'", APP)
        self.assertIn("closeNarrationPopover()", APP)

    def test_slider_initializes_from_and_writes_to_narration_api(self):
        self.assertIn('id="headerNarrationVolume" type="range" min="0" max="100"', INDEX)
        self.assertIn('aria-label="Narration volume"', INDEX)
        self.assertIn("Math.round(TombWorldNarration.getVolume()*100)", APP)
        self.assertIn("TombWorldNarration.setVolume(Number(event.target.value)/100)", APP)

    def test_toggle_uses_existing_api_and_change_event_keeps_ui_synced(self):
        self.assertIn("TombWorldNarration.setEnabled(event.target.checked)", APP)
        self.assertIn("window.addEventListener('tombworldnarrationchange'", APP)
        self.assertIn("syncNarrationControls();", APP)
        self.assertIn("headerNarrationEnabled.setAttribute('aria-label',`Narration ${enabled?'on':'off'}`)", APP)

    def test_existing_unversioned_preferences_remain_the_only_source_of_truth(self):
        self.assertEqual(NARRATION.count("tombWorldSoloGuide.narrationEnabled"), 1)
        self.assertEqual(NARRATION.count("tombWorldSoloGuide.narrationVolume"), 1)
        for source in (INDEX, APP, CSS, PERSISTENCE):
            self.assertNotIn("tombWorldSoloGuide.narrationEnabled", source)
            self.assertNotIn("tombWorldSoloGuide.narrationVolume", source)
        self.assertNotRegex(NARRATION, r"narration(?:Enabled|Volume).*APP_VERSION")
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_mobile_popover_stays_within_viewport_without_taller_header(self):
        self.assertIn("width:min(280px,calc(100vw - 24px))", CSS)
        self.assertIn("width:40px;height:40px", CSS)
        header_rule = re.search(r"\.app-header\{[^}]+\}", CSS).group(0)
        self.assertNotIn("height:", header_rule)
        self.assertIn(".brand h1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}", CSS)


if __name__ == "__main__":
    unittest.main()
