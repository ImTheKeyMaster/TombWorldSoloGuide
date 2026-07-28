import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def definitions():
    source = APP.split("const npoDefinitions = ", 1)[1].split(";\n\n  // Official 2D6 table", 1)[0]
    script = f"const data={source}; process.stdout.write(JSON.stringify(data));"
    return json.loads(subprocess.check_output(["node", "-e", script], text=True))


class CanoptekProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = definitions()

    def weapon(self, operative, weapon_id, profile_id=None, kind="rangedWeapons"):
        weapon = next(item for item in self.profiles[operative][kind] if item["id"] == weapon_id)
        if profile_id:
            return next(item for item in weapon["profiles"] if item["id"] == profile_id)
        return weapon

    def test_all_active_profiles_share_schema_and_base_stats(self):
        expected = {
            "Geomancer": (3, 6, 3, 14),
            "Canoptek Tomb Crawler": (2, 5, 3, 21),
            "Canoptek Macrocyte Warrior": (2, 7, 4, 7),
            "Canoptek Macrocyte Accelerator": (2, 7, 4, 7),
            "Canoptek Macrocyte Reanimator": (2, 7, 4, 7),
        }
        schema = {"id", "type", "name", "apl", "move", "save", "wounds", "rangedWeapons", "meleeWeapons", "actions", "passiveRules", "strategicRules", "keywords"}
        for name, stats in expected.items():
            profile = self.profiles[name]
            self.assertTrue(schema <= profile.keys(), name)
            self.assertEqual(tuple(profile[key] for key in ("apl", "move", "save", "wounds")), stats)
        for name in ("Necron Warrior", "Canoptek Scarab Swarm"):
            self.assertTrue(schema <= self.profiles[name].keys(), name)

    def test_errata_corrected_weapon_profiles(self):
        quake = self.weapon("Geomancer", "tremorglaive", "quake")
        self.assertEqual((quake["attacks"], quake["damage"]), (5, {"normal": 1, "critical": 2}))
        warrior = self.profiles["Canoptek Macrocyte Warrior"]
        self.assertEqual(self.weapon("Canoptek Macrocyte Warrior", "gauss-scalpel")["damage"], {"normal": 2, "critical": 3})
        self.assertEqual(self.weapon("Canoptek Macrocyte Warrior", "claws-and-tail", kind="meleeWeapons")["attacks"], 3)
        for mode in self.weapon("Canoptek Macrocyte Warrior", "tesla-caster")["profiles"]:
            self.assertEqual(mode["attacks"], 4)
        aggressive = next(rule for rule in warrior["passiveRules"] if rule["id"] == "aggressive-defence")
        self.assertEqual((aggressive["successThreshold"], aggressive["damage"]), (2, 1))

    def test_loadouts_modes_ranges_and_area_values_are_structured(self):
        crawler = self.profiles["Canoptek Tomb Crawler"]
        warrior = self.profiles["Canoptek Macrocyte Warrior"]
        self.assertEqual([item["id"] for item in crawler["loadoutOptions"]], ["twin-gauss-reapers", "transdimensional-isolator"])
        self.assertEqual([item["id"] for item in warrior["loadoutOptions"]], ["gauss-scalpel", "tesla-caster"])
        self.assertEqual(self.weapon("Canoptek Tomb Crawler", "twin-gauss-reapers", "sweeping")["torrent"], 1)
        self.assertEqual(self.weapon("Canoptek Macrocyte Warrior", "tesla-caster", "living-lightning")["blast"], 2)
        self.assertEqual(self.weapon("Canoptek Macrocyte Accelerator", "spark")["range"], 4)
        self.assertEqual(self.weapon("Canoptek Macrocyte Reanimator", "atomiser-beam")["range"], 6)

    def test_actions_passives_and_matrix_exclusion(self):
        geomancer = self.profiles["Geomancer"]
        self.assertEqual([item["id"] for item in geomancer["actions"]], ["geomantic-disturbance", "canoptek-control", "molecular-breach"])
        self.assertNotIn("obelisk", json.dumps(self.profiles).lower())
        accelerator = self.profiles["Canoptek Macrocyte Accelerator"]
        self.assertEqual([item["temporaryAplModifier"]["amount"] for item in accelerator["actions"]], [1, -1])
        reanimator = self.profiles["Canoptek Macrocyte Reanimator"]
        self.assertTrue(reanimator["actions"][0]["oncePerTurningPoint"])
        self.assertTrue(reanimator["passiveRules"][0]["oncePerTurningPoint"])

    def test_rule_helpers_and_persistence_hooks_exist(self):
        for helper in ("npoProfileSchemaValid", "effectiveApl", "applyTemporaryAplModifier", "expireActivationEffects", "applyMolecularBreach", "consumeMolecularBreach", "resolveGeomanticDisturbance", "markerControlApl", "ceaselessScuttlingEligible", "reanimateEligible", "applyReanimate", "useNanoscarabBeam"):
            self.assertIn(f"function {helper}", APP)
        self.assertIn("npoRuleState:{aplModifiers:[],pendingMovementEffects:[]", APP)
        self.assertIn("state.npoRuleState.reanimatedTargetIds=[]", APP)
        self.assertRegex(APP, re.compile(r"function aggressiveDefenseDamage\(rollResult\).*?return result>=2\?1:0", re.S))

    def test_legacy_placeholder_stats_fall_back_to_completed_profile(self):
        self.assertIn("move:Number(npo.move)>0?Number(npo.move):definition.move", APP)
        self.assertIn("maxWounds:Number(npo.maxWounds)>0?Number(npo.maxWounds):definition.wounds", APP)
        self.assertIn("npo.wounds!==null", APP)

    def test_unautomated_weapon_rules_require_explicit_tabletop_resolution(self):
        self.assertIn("const tabletopRules=", APP)
        self.assertIn("Piercing Crits|Blast|Torrent|Seek Light|Severe|Shock|Stun", APP)
        self.assertIn("confirm any required tabletop targets or effects", APP)

    def test_reanimate_penalty_and_healing_edge_cases_are_safe(self):
        self.assertIn("deferCurrentActivation:duringTargetActivation", APP)
        self.assertIn("if(item.deferCurrentActivation){item.deferCurrentActivation=false;return true;}", APP)
        self.assertIn("playerDefinition(target.id)?.wounds", APP)

    def test_profile_ui_and_version(self):
        self.assertIn("Gameplay profile", APP)
        self.assertIn("Operative actions", APP)
        self.assertIn("Passive rules", APP)
        self.assertIn("const APP_VERSION = '7.1.2';", APP)
        self.assertIn("V7.1.2", (ROOT / "index.html").read_text())
        self.assertNotIn("npoPortrait", APP)


if __name__ == "__main__":
    unittest.main()
