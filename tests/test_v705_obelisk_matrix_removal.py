import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
PRODUCTION = "\n".join(
    (ROOT / name).read_text()
    for name in ("app.js", "index.html", "styles.css", "service-worker.js", "manifest.webmanifest")
)


def definitions():
    source = APP.split("const npoDefinitions = ", 1)[1].split(";\n\n  // Official 2D6 table", 1)[0]
    script = f"const data={source}; process.stdout.write(JSON.stringify(data));"
    return json.loads(subprocess.check_output(["node", "-e", script], text=True))


def persistence_result(expression):
    script = f"const p=require('./persistence.js'); process.stdout.write(JSON.stringify({expression}));"
    return json.loads(subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True))


class ObeliskMatrixRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = definitions()

    def test_no_matrix_gameplay_ui_rules_or_accessibility_text(self):
        self.assertNotIn("obelisk node matrix support", PRODUCTION.lower())
        self.assertNotRegex(PRODUCTION.lower(), r"within (?:your |the )?matrix|matrix (?:bonus|range|status)")
        self.assertNotRegex(INDEX, r"(?i)aria-(?:label|describedby)=[^>]*(?:obelisk|matrix)")

    def test_profiles_keep_only_supported_actions_and_ranges(self):
        geomancer = self.profiles["Geomancer"]
        self.assertEqual([action["id"] for action in geomancer["actions"]], [
            "geomantic-disturbance", "canoptek-control", "molecular-breach"
        ])
        for action_id in ("canoptek-control", "molecular-breach"):
            action = next(action for action in geomancer["actions"] if action["id"] == action_id)
            self.assertEqual((action["target"]["visible"], action["target"]["range"]), (True, 6))
        accelerator = self.profiles["Canoptek Macrocyte Accelerator"]
        self.assertEqual([(action["id"], action["target"]["range"]) for action in accelerator["actions"]], [
            ("overcharge", 3), ("cranial-overload", 3)
        ])
        reanimator = self.profiles["Canoptek Macrocyte Reanimator"]
        self.assertEqual(reanimator["actions"][0]["target"]["range"], 6)
        self.assertEqual(reanimator["passiveRules"][0]["target"]["range"], 6)
        self.assertTrue(reanimator["passiveRules"][0]["replacement"]["dashEndsWithinSourceControlRange"])

    def test_base_apl_weapons_and_non_matrix_modifiers_remain_authoritative(self):
        expected_apl = {
            "Geomancer": 3, "Canoptek Tomb Crawler": 2,
            "Canoptek Macrocyte Warrior": 2, "Canoptek Macrocyte Accelerator": 2,
            "Canoptek Macrocyte Reanimator": 2,
        }
        self.assertEqual({name: self.profiles[name]["apl"] for name in expected_apl}, expected_apl)
        accelerator = self.profiles["Canoptek Macrocyte Accelerator"]
        self.assertEqual([action["temporaryAplModifier"]["amount"] for action in accelerator["actions"]], [1, -1])
        self.assertEqual([item["amount"] for item in self.profiles["Canoptek Macrocyte Reanimator"]["passiveRules"][0]["temporaryAplModifiers"]], [-1, -1])
        self.assertIn("markerControlApl", self.profiles["Canoptek Tomb Crawler"]["passiveRules"][1])
        self.assertNotRegex(json.dumps(self.profiles), r"(?i)obelisk|matrix")

    def test_legacy_matrix_state_is_removed_without_touching_ordinary_state(self):
        legacy = {
            "saveVersion": 1, "version": "7.0.4", "turningPoint": 2,
            "obeliskNodes": [{"x": 1}], "matrixActive": True,
            "roster": [{"id": "crawler-1", "type": "Canoptek Tomb Crawler", "wounds": 17,
                        "withinMatrix": True, "matrixPowered": True}],
            "activationHistory": [{"text": "An old historical entry remains readable."}],
            "npoRuleState": {
                "aplModifiers": [
                    {"id": "matrix:1", "ruleId": "matrix-bonus", "targetId": "crawler-1", "amount": 1},
                    {"id": "overcharge:a:b", "ruleId": "overcharge", "targetId": "crawler-1", "amount": 1},
                ],
                "pendingMovementEffects": [{"id": "obelisk:1", "ruleId": "obelisk-node-control"}],
                "oncePerTurningPoint": {"matrixControl": True, "reanimate": True},
            },
        }
        result = persistence_result(f"p.migrateSave({json.dumps(legacy)})")
        self.assertEqual(result["saveVersion"], 3)
        self.assertEqual((result["turningPoint"], result["roster"][0]["wounds"]), (2, 17))
        self.assertEqual(result["activationHistory"], legacy["activationHistory"])
        self.assertNotIn("obeliskNodes", result)
        self.assertNotIn("withinMatrix", result["roster"][0])
        self.assertNotIn("matrixPowered", result["roster"][0])
        self.assertEqual([item["ruleId"] for item in result["npoRuleState"]["aplModifiers"]], ["overcharge"])
        self.assertEqual(result["npoRuleState"]["pendingMovementEffects"], [])
        self.assertEqual(result["npoRuleState"]["oncePerTurningPoint"], {"reanimate": True})

    def test_new_saves_do_not_write_injected_matrix_fields(self):
        state = {
            "version": "7.5.0", "matrixActive": True,
            "roster": [{"id": "warrior-1", "type": "Canoptek Macrocyte Warrior", "wounds": 7, "insideMatrix": True}],
            "npoRuleState": {"aplModifiers": [{"ruleId": "matrix-accurate", "amount": 1}]},
        }
        result = persistence_result(f"p.createPersistedSave({json.dumps(state)})")
        self.assertEqual(result["saveVersion"], 3)
        self.assertNotIn("matrixActive", result)
        self.assertNotIn("insideMatrix", result["roster"][0])
        self.assertEqual(result["npoRuleState"]["aplModifiers"], [])

    def test_release_and_offline_assets_are_synchronized(self):
        self.assertIn("const APP_VERSION = '8.6.19';", APP)
        self.assertIn("const APP_VERSION = '8.6.19';", WORKER)
        self.assertIn("V8.6.19", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        for asset in ("app.js", "mission-engine.js", "persistence.js", "styles.css"):
            self.assertIn(f"{asset}?v=8.6.19", INDEX)
        self.assertNotRegex(WORKER, r"(?i)(?:obelisk|matrix)[^\n]*(?:png|svg|jpe?g|webp)")

    def test_ordering_portrait_and_unrelated_behavior_regressions(self):
        self.assertIn("sortedNposForDisplay(state.roster)", APP)
        self.assertIn("numeric:true,sensitivity:'base'", APP)
        self.assertNotIn("npoPortrait", APP)
        self.assertTrue(any((ROOT / "Assets/Images/Death Korps").glob("*.jpg")))
        self.assertIn("eliminated-necron-skull.png", (ROOT / "styles.css").read_text())
        for operative in ("Necron Warrior", "Canoptek Scarab Swarm"):
            self.assertIn(operative, self.profiles)


if __name__ == "__main__":
    unittest.main()
