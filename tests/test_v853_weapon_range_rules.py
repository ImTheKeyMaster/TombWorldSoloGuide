import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


def evaluate_weapon_rules():
    handlers = APP[APP.index("const WEAPON_RULE_HANDLERS"):APP.index("const NPO_ACTION_TRANSITIONS")]
    normalize = APP[APP.index("  function normalizedWeaponRuleId"):APP.index("  function effectiveDefenseDiceCount")]
    statuses = APP[APP.index("  function weaponRuleStatuses"):APP.index("  function createWeaponRuleResolution")]
    script = f"""
const warnings=[];
const console={{warn:message=>warnings.push(message)}};
{handlers}
{normalize}
{statuses}
const rangeRules=['Range 6"','Range 8"','Range 12"'];
const rangeProfile={{rules:[rangeRules[1],'Piercing 1']}};
const unknownProfile={{rules:['Mystery Rule 2','  mystery   rule 2  ','Mystery Rule 3']}};
const rangeStatuses=weaponRuleStatuses(rangeProfile);
weaponRuleStatuses(rangeProfile);
const unknownStatuses=weaponRuleStatuses(unknownProfile);
weaponRuleStatuses(unknownProfile);
process.stdout.write(JSON.stringify({{
  normalizedRanges:rangeRules.map(rule=>({{id:normalizedWeaponRuleId(rule),value:weaponRuleValue({{rules:[rule]}},'range')}})),
  rangeHandler:WEAPON_RULE_HANDLERS[normalizedWeaponRuleId('Range 8"')],
  rangeStatuses,
  unknownStatuses,
  warnings
}}));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


class WeaponRangeRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_weapon_rules()

    def test_range_normalizes_and_preserves_distance(self):
        self.assertEqual(self.result["normalizedRanges"], [
            {"id": "range", "value": 6},
            {"id": "range", "value": 8},
            {"id": "range", "value": 12},
        ])

    def test_range_is_supported_target_selection_tabletop_check(self):
        self.assertEqual(self.result["rangeHandler"], {"mode": "tabletop-check", "phase": "target-selection"})

    def test_range_status_is_not_unsupported_and_does_not_warn(self):
        self.assertIn('Range 8": target distance checked before combat', self.result["rangeStatuses"])
        self.assertNotIn('Range 8" is not yet supported by the Guide.', self.result["rangeStatuses"])
        self.assertFalse(any('Range 8"' in warning for warning in self.result["warnings"]))

    def test_piercing_remains_automatic(self):
        self.assertIn("Piercing 1: handled automatically", self.result["rangeStatuses"])

    def test_unknown_rules_remain_visible_and_warn_only_once(self):
        self.assertEqual(len(self.result["unknownStatuses"]), 3)
        self.assertTrue(all("is not yet supported by the Guide." in status for status in self.result["unknownStatuses"]))
        unknown_warnings = [warning for warning in self.result["warnings"] if "mystery" in warning.lower()]
        self.assertEqual(len(unknown_warnings), 2)

    def test_version_853_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.9';", APP)
        self.assertIn("const APP_VERSION = '8.6.9';", WORKER)
        self.assertIn("V8.6.9", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.9"))
        self.assertIn("## v8.6.9", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.9", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
