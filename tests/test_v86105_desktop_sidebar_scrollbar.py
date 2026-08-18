import re
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class DesktopSidebarScrollbarRegressionTests(unittest.TestCase):
    def test_release_version_and_save_schema(self):
        self.assertEqual((8, 6, 105), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", (ROOT / "service-worker.js").read_text())
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)

    def test_sidebar_uses_one_measured_header_height(self):
        self.assertNotIn("top:71px", CSS)
        self.assertNotIn("100dvh - 71px", CSS)
        self.assertIn("top:var(--app-header-height)", CSS)
        self.assertEqual(2, CSS.count("calc(100dvh - var(--app-header-height))"))
        self.assertIn("appHeader.getBoundingClientRect().height", APP)
        self.assertIn("'--app-header-height'", APP)

    def test_header_measurement_tracks_header_and_viewport_changes(self):
        self.assertIn("new ResizeObserver", APP)
        self.assertIn("appHeaderResizeObserver?.observe(appHeader)", APP)
        self.assertRegex(APP, r"addEventListener\('resize',\(\)=>\{syncAppHeaderHeight\(\)")
        self.assertRegex(APP, r"addEventListener\('orientationchange',\(\)=>\{syncAppHeaderHeight\(\)")

    def test_scrolling_and_responsive_behavior_are_preserved(self):
        for selector in ("html", "body", ".game-workspace", ".app-shell"):
            self.assertNotRegex(CSS, rf"{re.escape(selector)}\s*\{{[^}}]*overflow-y\s*:\s*hidden")
        self.assertIn(".operative-status-section.allow-scroll .operative-status-list{overflow-y:auto", CSS)
        self.assertIn("@media (max-width:899px)", CSS)
        self.assertIn(".operative-status-panel{display:none!important}", CSS)
        self.assertNotIn(".game-workspace{position:relative;min-width:0;min-height", CSS)


if __name__ == "__main__":
    unittest.main()
