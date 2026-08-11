import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
SERVICE_WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class TargetReticleTests(unittest.TestCase):
    def test_target_selection_uses_existing_crosshair_icon(self):
        self.assertIn(
            "return attackRequired&&!targetConfirmed?'crosshair':'command';",
            APP,
        )
        self.assertIn(
            "npoIcon(iconForNpoDecision(attackRequired,targetConfirmed))",
            APP,
        )
        self.assertEqual(APP.count("crosshair:'<circle"), 1)

    def test_non_target_questions_keep_semantic_action_icons(self):
        self.assertIn("Fight:'radar',Charge:'charge-movement',Shoot:'crosshair'", APP)
        self.assertIn("if(question.concernsControlRange)return 'radar';", APP)
        self.assertIn("if(type==='command')return npoIcon('radar');", APP)

    def test_release_version_is_current_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.54';", APP)
        self.assertIn("const APP_VERSION = '8.6.54';", SERVICE_WORKER)
        self.assertIn('<div class="version">V8.6.54</div>', INDEX)
        self.assertIn("# Tomb World Solo Guide v8.6.54", README)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
