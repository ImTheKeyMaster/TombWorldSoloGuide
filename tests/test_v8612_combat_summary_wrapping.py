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


def css_rule(selector):
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", STYLES)
    if not match:
        raise AssertionError(f"Missing CSS rule for {selector}")
    return re.sub(r"\s+", "", match.group(1))


class V8612CombatSummaryWrappingTests(unittest.TestCase):
    def test_01_version_references_are_current(self):
        self.assertIn("const APP_VERSION = '8.6.50';", APP)
        self.assertIn("const APP_VERSION = '8.6.50';", WORKER)
        self.assertIn("V8.6.50", INDEX)
        self.assertIn("styles.css?v=8.6.50", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.50"))

    def test_02_summary_values_wrap_words_normally(self):
        rule = css_rule(".combat-summary-value")
        self.assertIn("min-width:0", rule)
        self.assertIn("word-break:normal", rule)
        self.assertIn("overflow-wrap:break-word", rule)
        self.assertIn("hyphens:none", rule)
        self.assertNotIn("word-break:break-all", rule)
        self.assertNotIn("overflow-wrap:anywhere", rule)
        scoped = css_rule(".combat-participants .combat-summary-value")
        self.assertIn("overflow-wrap:break-word", scoped)

    def test_03_all_six_summary_values_use_scoped_class(self):
        screen = APP[APP.index("function showSharedCombatResolutionScreen"):APP.index("function severeAppliedHtml")]
        for label in ("Attacker", "Defender", "Attack type", "Weapon", "Attack", "Defense"):
            self.assertRegex(screen, rf"<small>{label}</small><strong class=\"combat-summary-value\">")
        self.assertIn("combat-summary-grid", screen)

    def test_04_grid_adapts_to_multiple_rows(self):
        rules = css_rule(".combat-summary-grid.has-attack-profile")
        self.assertIn("grid-template-columns:repeat(auto-fit,minmax(135px,1fr))", rules)
        self.assertIn("gap:.5rem", rules)
        self.assertNotIn("repeat(6", rules)

    def test_05_mobile_grid_has_no_forced_overflow(self):
        rules = css_rule(".combat-summary-grid.has-attack-profile")
        minimum = int(re.search(r"minmax\((\d+)px", rules).group(1))
        gap = float(re.search(r"gap:([\d.]+)rem", rules).group(1)) * 16
        mobile_content_width = 390 - 16 - 28
        self.assertLessEqual((minimum * 2) + gap, mobile_content_width)
        self.assertIn("overflow-x:hidden", STYLES)

        narrow_phone_rule = (
            "@media(max-width:360px){\n"
            "  .combat-summary-grid,.combat-summary-grid.has-attack-profile{grid-template-columns:1fr}\n"
            "}"
        )
        self.assertIn(narrow_phone_rule, STYLES)
        self.assertGreater(STYLES.index(narrow_phone_rule), STYLES.index("/* v8.6.12 combat summary wrapping */"))

    def test_06_long_names_are_escaped_and_text_is_not_shrunk(self):
        screen = APP[APP.index("function showSharedCombatResolutionScreen"):APP.index("function severeAppliedHtml")]
        self.assertIn("${escapeHtml(attackerName)}", screen)
        self.assertIn("${escapeHtml(weaponName)}", screen)
        self.assertNotRegex(css_rule(".combat-summary-value"), r"font-size:")

    def test_07_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_08_release_notes(self):
        self.assertIn("Version 8.6.12 - Fix Combat Summary Word Wrapping", README)


if __name__ == "__main__":
    unittest.main()
