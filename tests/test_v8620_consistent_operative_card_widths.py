import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
SETUP_CONTENT = APP[APP.index("function setupContent(stepId)") :]
ROSTER_RENDERER = SETUP_CONTENT[SETUP_CONTENT.index("if(stepId==='playerRoster')") : SETUP_CONTENT.index("if(stepId==='deploy')")]
CATEGORY_CSS = CSS[CSS.index("/* v3.3.0 categorized Player roster selection */") : CSS.index(".update-notice")]


class ConsistentOperativeCardWidthsV8620Tests(unittest.TestCase):
    def test_01_application_displays_version_8620(self):
        self.assertIn("const APP_VERSION = '8.6.21';", APP)
        self.assertIn("const APP_VERSION = '8.6.21';", WORKER)
        self.assertIn("V8.6.21", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.21"))

    def test_02_every_category_uses_the_shared_grid_component(self):
        section = re.search(r"return `<section class=\"roster-category\"[\s\S]+?`;", ROSTER_RENDERER).group(0)
        self.assertIn('class="player-roster-grid roster-category-content"', section)
        self.assertNotRegex(section, r"single-card|only-operative|full-width-card|leader-card-wide")

    def test_03_single_operative_occupies_one_desktop_column(self):
        self.assertIn(".roster-category-content{grid-template-columns:repeat(3,minmax(0,1fr));", CATEGORY_CSS)
        self.assertNotRegex(CATEGORY_CSS, r":only-child[^{}]*\{[^}]*grid-column")
        self.assertNotRegex(CATEGORY_CSS, r"player-roster-card[^{}]*\{[^}]*grid-column\s*:\s*1\s*/\s*-1")

    def test_04_one_two_and_three_card_groups_share_card_widths(self):
        self.assertIn("category.operatives.map(o=>", ROSTER_RENDERER)
        self.assertIn(".roster-category-content>.player-roster-card{min-width:0;width:100%}", CATEGORY_CSS)
        self.assertNotRegex(ROSTER_RENDERER, r"operatives\.length\s*[<=>]|only-operative|single-card")

    def test_05_selected_cards_do_not_change_width(self):
        selected_rule = re.search(r"\.player-roster-card\.selected\{([^}]*)\}", CSS).group(1)
        self.assertNotRegex(selected_rule, r"width|grid-column|margin")
        self.assertIn("*{box-sizing:border-box}", CSS)

    def test_06_leader_has_no_special_layout(self):
        self.assertNotRegex(CATEGORY_CSS, r"leader[^{}]*\{[^}]*(?:width|grid|flex)")
        self.assertNotRegex(ROSTER_RENDERER, r"leader[^\n`]*(?:single-card|full-width|grid-column)")

    def test_07_no_single_card_expansion_rule_exists(self):
        self.assertNotRegex(CSS, r"\.player-roster-card:only-child")
        self.assertNotRegex(CSS, r"(?:single-card|only-operative|full-width-card|leader-card-wide)[^{}]*\{[^}]*grid-column\s*:\s*1\s*/\s*-1")

    def test_08_responsive_shared_column_counts(self):
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", CATEGORY_CSS)
        self.assertIn("@media(max-width:800px){.roster-category-content{grid-template-columns:repeat(2,minmax(0,1fr))}}", CATEGORY_CSS)
        self.assertIn("grid-template-columns:minmax(0,1fr)", CATEGORY_CSS)

    def test_09_names_wrap_only_at_normal_break_points(self):
        card_rules = "\n".join(re.findall(r"[^{}]*(?:player-roster-card|player-roster-card-head)[^{}]*\{[^}]*\}", CSS))
        self.assertNotIn("word-break:break-all", card_rules)
        self.assertNotIn("overflow-wrap:anywhere", card_rules)
        self.assertIn(".roster-category-content .player-roster-card-head>div{min-width:0}", CATEGORY_CSS)

    def test_10_stats_remain_contained(self):
        self.assertIn(".roster-category-content .operative-stat-line{grid-template-columns:repeat(4,minmax(0,1fr));min-width:0}", CATEGORY_CSS)
        self.assertIn(".roster-category-content .operative-stat-line span{min-width:0}", CATEGORY_CSS)

    def test_11_selection_control_remains_positioned_and_accessible(self):
        self.assertIn(".roster-category-content .player-roster-card-head>span{flex:0 0 27px}", CATEGORY_CSS)
        self.assertIn("player-roster-card-head{display:flex;justify-content:space-between", CSS)
        self.assertIn('type="button" class="player-roster-card', ROSTER_RENDERER)
        self.assertIn("${chosen?'✓':'+'}", ROSTER_RENDERER)

    def test_12_grid_cannot_introduce_horizontal_scrolling(self):
        self.assertIn("repeat(3,minmax(0,1fr))", CATEGORY_CSS)
        self.assertIn("min-width:0;width:100%", CATEGORY_CSS)
        self.assertNotRegex(CATEGORY_CSS, r"min-width\s*:\s*230px")

    def test_13_roster_selection_and_counts_are_preserved(self):
        self.assertIn('data-select-player="${o.id}"', ROSTER_RENDERER)
        self.assertIn("const categorySelected=category.operatives.filter", ROSTER_RENDERER)
        self.assertIn("${categorySelected} selected", ROSTER_RENDERER)
        self.assertIn('aria-expanded="${expanded}"', ROSTER_RENDERER)

    def test_14_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_15_release_assets_and_notes_are_current(self):
        for asset in ("styles.css", "app.js", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js"):
            self.assertIn(f"{asset}?v=8.6.21", INDEX)
        self.assertIn("## v8.6.21", README)
        self.assertIn("Keep Operative Cards Consistent Across Roster Groups", README)


if __name__ == "__main__":
    unittest.main()
