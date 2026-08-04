import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()


class NpoHistoryIconColorTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
