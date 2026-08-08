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


def evaluate_summaries():
    handlers = APP[APP.index("const WEAPON_RULE_HANDLERS"):APP.index("const NPO_ACTION_TRANSITIONS")]
    helpers = APP[APP.index("  function normalizedWeaponRuleId"):APP.index("  function createWeaponRuleResolution")]
    script = f"""
const warnings=[];
const console={{warn:message=>warnings.push(message)}};
{handlers}
{helpers}
const piercing1={{weaponId:'one',profileId:'one',rules:['Piercing 1'],ap:1}};
const piercing2={{weaponId:'two',profileId:'two',rules:['Piercing 2'],ap:2}};
const duplicate={{rules:['Piercing 1','Piercing 1'],ap:1}};
const invalid={{rules:['Piercing'],ap:0}};
const distinct={{rules:['Piercing 1','Piercing Crits 1'],ap:1,piercingCrits:1}};
const automaticDuplicate={{rules:['Severe','Severe'],ap:0}};
process.stdout.write(JSON.stringify({{
  one:weaponRuleSummaries(piercing1),
  two:weaponRuleSummaries(piercing2),
  duplicate:weaponRuleSummaries(duplicate),
  invalid:weaponRuleSummaries(invalid),
  distinct:weaponRuleSummaries(distinct),
  automaticDuplicate:weaponRuleSummaries(automaticDuplicate),
  defenseOne:effectiveDefenseDiceCount(piercing1,[],3),
  defenseTwo:effectiveDefenseDiceCount(piercing2,[],3),
  warnings
}}));
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)


class WeaponRuleSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_summaries()

    def test_01_version_8623_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.42';", APP)
        self.assertIn("const APP_VERSION = '8.6.42';", WORKER)
        self.assertIn("V8.6.42", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.42"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.42", INDEX)

    def test_02_to_09_piercing_is_one_clear_grammatical_item(self):
        self.assertEqual(self.result["one"], [{
            "id": "piercing-1",
            "label": "Piercing 1: Defender rolls 1 fewer defense die. Handled automatically.",
        }])
        self.assertEqual(self.result["two"], [{
            "id": "piercing-2",
            "label": "Piercing 2: Defender rolls 2 fewer defense dice. Handled automatically.",
        }])
        self.assertEqual(len(self.result["duplicate"]), 1)
        self.assertNotEqual(self.result["one"][0]["label"], "Piercing 1")
        self.assertNotEqual(self.result["one"][0]["label"], "Piercing 1: handled automatically")

    def test_10_11_selected_profile_value_matches_combat_value(self):
        self.assertIn("const value=Number(profile?.ap);", APP)
        self.assertIn("let reduction=Math.max(0,Number(profile?.ap||0));", APP)
        self.assertEqual(self.result["defenseOne"], 2)
        self.assertEqual(self.result["defenseTwo"], 1)

    def test_12_to_16_shared_renderer_covers_all_combat_paths_and_restore(self):
        self.assertIn("weaponRulesHtml(weapon?playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex}):null)", APP)
        self.assertGreaterEqual(APP.count("weaponRulesHtml(profile)"), 2)
        self.assertIn("weaponRulesHtml(initialProfile)", APP)
        self.assertIn("weaponRuleSequenceProgress(sequence", APP)
        self.assertIn("merged.weaponRuleResolution", APP)
        self.assertIn("merged.combatState", APP)
        self.assertIn("resumeCombatAfterWeaponRuleCheck", APP)

    def test_17_invalid_values_fall_back_without_malformed_text(self):
        self.assertEqual(self.result["invalid"], [{"id": "piercing", "label": "Piercing: Handled automatically."}])
        self.assertNotIn("undefined", self.result["invalid"][0]["label"])
        self.assertNotIn("0 fewer", self.result["invalid"][0]["label"])
        self.assertTrue(any("Piercing has no valid positive value" in warning for warning in self.result["warnings"]))

    def test_18_piercing_crits_remains_distinct(self):
        self.assertEqual([item["id"] for item in self.result["distinct"]], ["piercing-1", "piercing-crits"])
        self.assertEqual(self.result["distinct"][1]["label"], "Piercing Crits 1: Handled automatically.")
        self.assertIn("weaponRuleValue(profile,'piercing-crits')", APP)

    def test_19_other_automatic_rules_are_not_duplicated(self):
        self.assertEqual(self.result["automaticDuplicate"], [{"id": "severe", "label": "Severe: Handled automatically."}])

    def test_20_summary_is_one_non_focusable_list_item(self):
        renderer = APP[APP.index("  function weaponRulesHtml"):APP.index("  function normalizedGuidanceMatchText")]
        self.assertIn("<li>${escapeHtml(summary.label)}</li>", renderer)
        self.assertNotRegex(renderer, r"tabindex|<button|<a\\b")
        self.assertNotIn("weapon-rule-status", renderer)

    def test_21_22_mechanics_and_save_schema_are_unchanged(self):
        self.assertIn("return Math.max(0,Number(baseDice||0)-reduction);", APP)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_23_release_notes_are_present(self):
        self.assertIn("## v8.6.25", README)
        self.assertIn("Version 8.6.23 - Clarify Weapon Rule Summaries", README)


if __name__ == "__main__":
    unittest.main()
