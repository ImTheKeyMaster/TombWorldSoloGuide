import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES = (ROOT / "styles.css").read_text()
APP = (ROOT / "app.js").read_text()


class TestV8627DesktopResultArtwork(unittest.TestCase):
    def test_01_mobile_result_artwork_size_is_preserved(self):
        self.assertIn(
            ".mission-outcome .game-end-image{max-width:min(100%,360px)}",
            STYLES,
        )

    def test_02_desktop_result_artwork_is_enlarged(self):
        self.assertRegex(
            STYLES,
            re.compile(
                r"@media\(min-width:821px\)\{\.mission-outcome "
                r"\.game-end-image\{max-width:min\(100%,600px\)\}\}"
            ),
        )

    def test_03_artwork_remains_centered_and_proportional(self):
        self.assertIn(
            ".game-end-image{display:block;width:100%;max-width:768px;height:auto;"
            "margin:0 auto 22px;",
            STYLES,
        )

    def test_04_rule_only_targets_mission_outcome_artwork(self):
        self.assertEqual(STYLES.count("max-width:min(100%,600px)"), 1)
        self.assertIn(
            '<img class="game-end-image" src="Assets/Images/${resultClass}.png"',
            APP,
        )


if __name__ == "__main__":
    unittest.main()
