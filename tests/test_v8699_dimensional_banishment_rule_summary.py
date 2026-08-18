#!/usr/bin/env python3
from versioning import CURRENT_APP_VERSION
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def evaluate_summary():
    handlers = APP[APP.index("const WEAPON_RULE_HANDLERS"):APP.index("const NPO_ACTION_TRANSITIONS")]
    renderer = "function weaponRulesHtml" + APP.split("function weaponRulesHtml", 1)[1].split("function normalizedGuidanceMatchText", 1)[0]
    helpers = APP[APP.index("  function normalizedWeaponRuleId"):APP.index("  function createWeaponRuleResolution")]
    script = f"""
const console={{warn:()=>{{}}}};
const escapeHtml=value=>String(value);
{handlers}
{renderer}
{helpers}
const profile={{rules:['Dimensional Banishment','Dimensional Banishment'],ruleIds:['dimensional-banishment']}};
process.stdout.write(JSON.stringify({{
  handler:WEAPON_RULE_HANDLERS['dimensional-banishment'],
  summaries:weaponRuleSummaries(profile),
  html:weaponRulesHtml(profile)
}}));
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)


class DimensionalBanishmentRuleSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_summary()

    def test_version_metadata_and_save_schema(self):
        self.assertEqual((8, 6, 102), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_shared_summary_registers_automatic_mechanics(self):
        self.assertEqual("automatic", self.result["handler"]["mode"])
        self.assertEqual(1, len(self.result["summaries"]))
        summary = self.result["summaries"][0]
        self.assertEqual("dimensional-banishment", summary["id"])
        self.assertIn("Handled automatically.", summary["label"])
        self.assertIn("rolls 2D6", summary["label"])
        self.assertIn("exceeds the target’s remaining wounds", summary["label"])
        self.assertNotIn("not yet supported by the Guide", summary["label"])

    def test_shared_renderer_outputs_one_non_focusable_summary(self):
        html = self.result["html"]
        self.assertEqual(1, html.count("Dimensional Banishment"))
        self.assertEqual(1, html.count("<li>"))
        self.assertNotRegex(html, r"tabindex|<button|<a\\b")

    def test_existing_automatic_resolver_remains_automatic(self):
        automatic = APP.split("function resolveAutomaticDimensionalBanishment", 1)[1].split("function rolledCombatDice", 1)[0]
        resolver = APP.split("function resolveDimensionalBanishment", 1)[1].split("function resolveAutomaticDimensionalBanishment", 1)[0]
        self.assertIn("rollDice(2,6)", automatic)
        self.assertEqual(1, automatic.count("rollDice(2,6)"))
        self.assertIn("if(combat.dimensionalBanishmentResolved)return {...combat}", resolver)
        self.assertIn("total>normalAfter", resolver)
        for manual_text in ("Dimensional Banishment 2D6 result (0 if not triggered)", "Roll 2D6 physically", 'id="dimensionalBanishmentRoll"', "dimensionalBanishmentField"):
            self.assertNotIn(manual_text, APP)


if __name__ == "__main__":
    unittest.main()
