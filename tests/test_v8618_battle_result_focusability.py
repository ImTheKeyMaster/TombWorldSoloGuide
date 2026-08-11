import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def function_body(name):
    match = re.search(rf"  (?:async )?function {name}\([^\n]*", APP)
    if not match:
        return ""
    ends = [position for position in (
        APP.find("\n  function ", match.end()),
        APP.find("\n  async function ", match.end()),
    ) if position >= 0]
    return APP[match.start():min(ends) if ends else len(APP)]


class BattleResultFocusabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render = function_body("renderGame")
        cls.completed = cls.render[:cls.render.index("if(state.finalResolution?.pending")]

    def test_01_application_displays_version_8618(self):
        self.assertIn("const APP_VERSION = '8.6.52';", APP)
        self.assertIn("const APP_VERSION = '8.6.52';", WORKER)
        self.assertIn("V8.6.52", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.52"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.52", INDEX)

    def test_02_victory_is_semantic_non_interactive_content(self):
        self.assertIn("const resultLabel=victory?'Victory':'Defeat'", self.completed)
        self.assertIn('<h2 class="battle-result battle-result--${resultClass}">${resultLabel}</h2>', self.completed)

    def test_03_defeat_uses_the_same_semantic_non_interactive_content(self):
        self.assertIn("const resultClass=victory?'victory':'defeat'", self.completed)
        self.assertIn('battle-result--${resultClass}', self.completed)

    def test_04_victory_is_not_rendered_as_a_button(self):
        self.assertNotRegex(self.completed, r'<button[^>]*>\$\{resultLabel\}</button>')
        self.assertNotIn('<button>Victory</button>', self.completed)

    def test_05_defeat_is_not_rendered_as_a_button(self):
        self.assertNotIn('<button>Defeat</button>', self.completed)
        self.assertNotIn("<button>${victory?'Victory':'Defeat'}</button>", self.completed)

    def test_06_result_has_no_tabindex_zero(self):
        result_elements = re.findall(r'<h[23][^>]*battle-result[^>]*>', self.completed)
        self.assertTrue(result_elements)
        self.assertTrue(all('tabindex="0"' not in element for element in result_elements))

    def test_07_neither_result_variant_adds_tabindex(self):
        self.assertNotRegex(self.completed, r'battle-result[^>]*tabindex')
        self.assertNotRegex(self.completed, r'tabindex[^>]*battle-result')

    def test_08_tab_order_contains_only_real_battle_complete_controls(self):
        result_position = self.completed.index('class="battle-result')
        review_position = self.completed.index('id="reviewCompletedMission"')
        new_game_position = self.completed.index('id="gameEndNewGame"')
        self.assertLess(result_position, review_position)
        self.assertLess(review_position, new_game_position)
        self.assertNotIn('tabindex="0"', self.completed)

    def test_09_result_never_receives_programmatic_focus(self):
        self.assertNotRegex(self.render, r"battle-result[^\n]*\.focus\(")
        self.assertNotIn("$('#battle-complete-heading')?.focus()", self.render)
        self.assertIn("$('#reviewCompletedMission')?.focus()", self.render)
        self.assertIn("$('#recordFinalDefeat')?.focus()", self.render)

    def test_10_result_has_no_click_handler(self):
        self.assertNotRegex(self.render, r"battle-result[^\n]*(?:onclick|addEventListener)")
        self.assertNotIn("$('.battle-result').onclick", self.render)

    def test_11_result_does_not_have_a_pointer_cursor(self):
        result_rules = re.findall(r'[^{}]*\.battle-result[^{}]*\{([^{}]*)\}', STYLES)
        self.assertTrue(all('cursor:pointer' not in rule.replace(' ', '') for rule in result_rules))
        self.assertNotIn('.battle-result:hover', STYLES)
        self.assertNotIn('.battle-result:active', STYLES)

    def test_12_real_controls_retain_visible_focus_styling(self):
        self.assertRegex(STYLES, r'\.btn:focus-visible[^\{]*\{[^}]*outline:2px solid var\(--green\)')
        self.assertNotIn('.battle-result:focus', STYLES)

    def test_13_result_remains_available_to_assistive_technology(self):
        self.assertIn('<img class="game-end-image" src="Assets/Images/${resultClass}.png" alt="">', self.completed)
        self.assertIn('<h2 class="battle-result', self.completed)
        self.assertIn('<h3 class="battle-result', self.completed)
        self.assertNotRegex(self.completed, r'battle-result[^>]*(?:aria-hidden|role="(?:button|link)")')

    def test_14_victory_and_defeat_calculation_paths_remain_unchanged(self):
        self.assertIn("const victory=state.gameEnd==='victory'", self.render)
        self.assertIn("$('#recordFinalDefeat').onclick=()=>completeMission('defeat')", self.render)
        self.assertIn("$('#recordFinalVictory').onclick=()=>completeMission('victory')", self.render)
        self.assertIn("victory?missionEngine()?.success:missionEngine()?.failure", self.render)

    def test_15_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_16_release_notes_describe_the_scoped_accessibility_fix(self):
        self.assertIn("## v8.6.25", README)
        self.assertIn("**Version 8.6.18 - Remove Focusability from Battle Result Labels**", README)
        self.assertIn("without weakening real control focus indicators", README)


if __name__ == "__main__":
    unittest.main()
