import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class NpoHistoryIconColorTests(unittest.TestCase):
    def test_release_version_references_are_current(self):
        self.assertIn("const APP_VERSION = '8.6.56';", APP)
        self.assertIn("const APP_VERSION = '8.6.56';", WORKER)
        self.assertIn('<div class="version">V8.6.56</div>', INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.56"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.56", INDEX)

    def test_history_icons_use_the_history_text_color(self):
        self.assertIn(
            ".npo-question-complete .npo-question-icon{width:25px;height:25px;color:var(--muted)}",
            STYLES,
        )
        self.assertIn(
            ".npo-question-complete .npo-question-icon--movement{width:30px;height:30px;flex:0 0 30px;color:var(--muted)}",
            STYLES,
        )
        self.assertIn("<g fill=\"currentColor\" stroke=\"currentColor\">", APP)

    def test_active_icons_keep_the_green_accent(self):
        self.assertIn(
            ".npo-question-icon--movement{display:block;width:42px;height:42px;flex:0 0 42px;align-self:center;object-fit:contain;color:#76f5a8}",
            STYLES,
        )
        self.assertIn("${npoIcon(iconForNpoQuestion(q))}", APP)

    def test_only_active_question_movement_icons_are_enlarged(self):
        self.assertIn(
            ".npo-active-question>.npo-question-icon.is-movement,.npo-active-question>.npo-question-icon.is-move-to-shoot{width:63px;height:63px;flex:0 0 63px}",
            STYLES,
        )
        self.assertIn("npo-question-card--active npo-active-question", APP)
        self.assertNotIn("npo-movement-confirmation npo-active-question", APP)

    def test_movement_icons_have_distinct_semantic_classes(self):
        self.assertIn("npo-question-icon--movement is-move-to-shoot", APP)
        self.assertIn("'npo-question-icon--movement':'npo-question-icon--charge'} is-movement", APP)


if __name__ == "__main__":
    unittest.main()
