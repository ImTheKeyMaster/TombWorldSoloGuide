from versioning import CURRENT_APP_VERSION
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


class RequiredConfirmationHighlightTests(unittest.TestCase):
    def test_confirmations_share_required_state_class(self):
        self.assertRegex(APP, r'class="check-row required-confirmation-row"><input id="tabletopCheckConfirmed"')
        self.assertRegex(APP, r'class="check-row required-confirmation-row"><input id="endChecked"')
        self.assertNotIn("check.id==='breach-points'?'required-confirmation-row':''", APP)

    def test_highlight_only_applies_while_checkbox_is_unchecked(self):
        rule = re.search(r"\.required-confirmation-row:has\(input:not\(:checked\)\)\{([^}]*)\}", STYLES)
        self.assertIsNotNone(rule)
        self.assertIn("background:rgba(41,127,78,.28)", rule.group(1))
        self.assertIn("border-color:#5de799", rule.group(1))
        self.assertNotIn("tabletop-confirmation-row", STYLES)

    def test_base_checkbox_style_and_validation_remain_unchanged(self):
        self.assertIn(".check-row input{width:22px;height:22px;accent-color:var(--green);flex:0 0 auto}", STYLES)
        self.assertIn("confirmation.onchange=()=>{persistStep();$('#confirmSecondaryTargets').disabled=!confirmation.checked;};", APP)
        self.assertIn("$('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});", APP)

    def test_release_versions_are_current_and_save_version_is_unchanged(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
