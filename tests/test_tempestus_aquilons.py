import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_PATH = ROOT / "Player_Operatives" / "TempestusAquilons.json"


class TempestusAquilonsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.team = json.loads(TEAM_PATH.read_text())
        cls.operatives = {operative["id"]: operative for operative in cls.team["operatives"]}

    def weapon(self, operative_id, name):
        return next(weapon for weapon in self.operatives[operative_id]["weapons"] if weapon["name"] == name)

    def test_team_is_selectable_and_cached_offline(self):
        manifest = json.loads((ROOT / "Player_Operatives" / "manifest.json").read_text())
        entry = next(team for team in manifest["teams"] if team["id"] == "tempestus-aquilons")
        self.assertEqual(entry["file"], TEAM_PATH.name)
        self.assertIn("./Player_Operatives/TempestusAquilons.json", (ROOT / "service-worker.js").read_text())

    def test_legal_roster_shape_and_unique_specialists(self):
        self.assertEqual(self.team["rosterSize"], 11)
        categories = {category["id"]: category for category in self.team["rosterCategories"]}
        self.assertEqual(categories["tempestor"]["requiredCount"], 1)
        self.assertEqual(categories["tempestor"]["maxCount"], 1)
        self.assertEqual(categories["servo-sentry"]["requiredCount"], 1)
        self.assertEqual(categories["servo-sentry"]["maxCount"], 1)
        specialists = [o for o in self.team["operatives"] if o["category"] == "specialists"]
        self.assertEqual(len({o["id"] for o in specialists}), len(specialists))
        self.assertEqual(len([o for o in self.team["operatives"] if o["role"] == "Trooper"]), 9)
        self.assertEqual(self.team["selectionRules"]["mandatoryTroopers"], 3)

    def test_operative_statistics(self):
        expected = {
            "tempestor-power": (3, 6, 4, 9), "servo-flamer": (2, 4, 3, 10),
            "grenadier": (2, 6, 4, 8), "gunfighter": (2, 6, 4, 8),
            "gunner-melta": (2, 6, 4, 8), "gunner-plasma": (2, 6, 4, 8),
            "marksman": (2, 6, 4, 8), "precursor": (2, 6, 4, 8), "trooper-1": (2, 6, 4, 8),
        }
        for operative_id, stats in expected.items():
            operative = self.operatives[operative_id]
            self.assertEqual((operative["apl"], operative["move"], operative["save"], operative["wounds"]), stats)

    def test_special_and_multiple_weapon_profiles_are_preserved(self):
        standard = self.weapon("gunner-plasma", "Plasma carbine (standard)")
        supercharge = self.weapon("gunner-plasma", "Plasma carbine (supercharge)")
        self.assertEqual((standard["attacks"], standard["hit"], standard["damage"]), (4, 3, "4/6"))
        self.assertIn("Hot", supercharge["rules"])
        for operative_id, names in {
            "marksman": {"Hot-shot long-las (concealed)", "Hot-shot long-las (mobile)", "Hot-shot long-las (stationary)"},
            "gunfighter": {"Hot-shot laspistols (focused)", "Hot-shot laspistols (salvo)", "Hot-shot laspistols (point-blank)"},
            "servo-volley": {"Hot-shot volley gun (focused)", "Hot-shot volley gun (sweeping)"},
        }.items():
            self.assertTrue(names.issubset({w["name"] for w in self.operatives[operative_id]["weapons"]}))
        self.assertEqual(self.weapon("gunner-melta", "Melta carbine")["damage"], "6/3")

    def test_all_operatives_have_weapons_stats_and_ability_guidance(self):
        for operative in self.team["operatives"]:
            self.assertTrue(operative["weapons"], operative["id"])
            self.assertIsInstance(operative["abilities"], list)
            for weapon in operative["weapons"]:
                self.assertIn(weapon["type"], {"ranged", "melee"})
                self.assertGreater(weapon["attacks"], 0)
                self.assertRegex(weapon["damage"], r"^\d+/\d+$")

    def test_faction_setup_deployment_and_gambit_guidance(self):
        rules = {rule["name"]: rule for rule in self.team["factionRules"]}
        self.assertEqual(rules["Drop Insertion"]["automation"], "tabletop-guidance")
        self.assertIn("vertical distance", rules["Grav-chute"]["text"])
        self.assertEqual(self.team["strategicGambits"][0]["turningPoints"], [1, 2])

    def test_generic_tracking_combat_and_save_paths_remain_team_agnostic(self):
        app = (ROOT / "app.js").read_text()
        self.assertIn("function playerRosterValidation", app)
        self.assertIn("function playerCurrentWounds", app)
        self.assertIn("state.playerCasualtyIds", app)
        self.assertIn("state.playerActivatedIds", app)
        self.assertIn("playerAttackWeapons(stage.playerOperativeId,attackType)", app)
        self.assertNotIn("state.playerTeamId==='tempestus-aquilons'", app)
        self.assertIn("valid=valid&&gravisCount<=maxGravis", app)
        self.assertIn("valid=valid&&leaderCount===requiredLeaderCount", app)
        self.assertIn("entry.turningPoints.includes(state.turningPoint)", app)
        script = """
const p=require('./persistence.js');
const save={saveVersion:1,playerTeamId:'tempestus-aquilons',playerRoster:['trooper-1'],playerWounds:{'trooper-1':3},playerActivatedIds:['trooper-1'],playerCasualtyIds:[],playerOperativeStates:{'trooper-1':{inPlay:true}},roster:[]};
const restored=p.migrateSave(p.createPersistedSave(save));
if(restored.playerTeamId!=='tempestus-aquilons'||restored.playerWounds['trooper-1']!==3||restored.playerActivatedIds[0]!=='trooper-1')process.exit(1);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_deathwatch_regression_definition_is_unchanged_and_supported(self):
        deathwatch = json.loads((ROOT / "Player_Operatives" / "DeathWatch.json").read_text())
        self.assertEqual(deathwatch["teamId"], "deathwatch")
        self.assertEqual(deathwatch["rosterSize"], 5)
        self.assertEqual(deathwatch["selectionRules"]["maxGravis"], 1)
        self.assertEqual(len(deathwatch["operatives"]), 11)
        self.assertTrue(any(len(op["weapons"]) > 1 for op in deathwatch["operatives"]))


if __name__ == "__main__":
    unittest.main()
