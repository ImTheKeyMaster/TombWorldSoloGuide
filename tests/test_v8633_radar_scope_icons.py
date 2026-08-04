import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class RadarScopeIconTests(unittest.TestCase):
    def test_command_alias_reuses_radar_and_star_markup_is_removed(self):
        self.assertIn("if(type==='command')return npoIcon('radar');", APP)
        self.assertNotIn('M12 2l3 6 6 1-4.5 4.5 1 6.5-5.5-3-5.5 3 1-6.5L3 9l6-1 3-6z', APP)

    def test_control_range_questions_use_semantic_radar_selection(self):
        self.assertIn("if(question.concernsControlRange)return 'radar';", APP)
        self.assertIn("'fall-back':{\n      concernsControlRange:true,", APP)
        self.assertIn("fight:{\n      concernsControlRange:true,", APP)
        self.assertIn('npoIcon(iconForNpoQuestion(item))', APP)
        self.assertIn('npoIcon(iconForNpoQuestion(q))', APP)

    def test_radar_remains_decorative_and_action_icons_remain_distinct(self):
        self.assertIn('class="npo-question-icon npo-question-icon--radar"', APP)
        self.assertIn('aria-hidden="true"\n  focusable="false"', APP)
        self.assertIn("Fight:'radar',Charge:'movement',Shoot:'crosshair'", APP)
        self.assertIn("Reposition:'objective',Dash:'movement'", APP)


if __name__ == '__main__':
    unittest.main()
