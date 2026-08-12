import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class VisibilityConfirmationHighlightTests(unittest.TestCase):
    def test_confirmation_row_has_dedicated_semantic_class(self):
        row = re.search(
            r'<label class="([^"]+)"><input id="tabletopCheckConfirmed"[^>]*>'
            r'<span>I have confirmed visibility and distance on the tabletop\.</span></label>',
            APP,
        )
        self.assertIsNotNone(row)
        self.assertIn("check-row", row.group(1).split())
        self.assertIn("tabletop-confirmation-row", row.group(1).split())

    def test_highlight_is_independent_of_checkbox_state(self):
        rule = re.search(r"\.tabletop-confirmation-row\{([^}]*)\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("background:", rule.group(1))
        self.assertIn("border-color:#5de799", rule.group(1))
        self.assertNotIn(":checked", rule.group(0))

    def test_base_checkbox_style_and_other_rows_remain_generic(self):
        self.assertIn(
            ".check-row input{width:22px;height:22px;accent-color:var(--green);flex:0 0 auto}",
            STYLES,
        )
        self.assertEqual(APP.count("tabletop-confirmation-row"), 1)

    def test_release_versions_are_current_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.55';", APP)
        self.assertIn("const APP_VERSION = '8.6.55';", WORKER)
        self.assertIn('<div class="version">V8.6.55</div>', INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.55"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.55", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
