import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_PATH = ROOT / "Player_Operatives" / "SpectreSquad.json"


class SpectreSquadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.team = json.loads(TEAM_PATH.read_text())
        cls.operatives = {operative["id"]: operative for operative in cls.team["operatives"]}
        cls.app = (ROOT / "app.js").read_text()

    def weapon(self, operative_id, weapon_id):
        return next(weapon for weapon in self.operatives[operative_id]["weapons"] if weapon["id"] == weapon_id)

    def validate(self, ids):
        selected = [self.operatives[id_] for id_ in ids if id_ in self.operatives]
        categories = {item["id"]: item for item in self.team["rosterCategories"]}
        if len(selected) != self.team["rosterSize"]:
            return False
        for category_id, category in categories.items():
            count = sum(item["category"] == category_id for item in selected)
            if count < category.get("requiredCount", 0) or count > category.get("maxCount", 10**9):
                return False
        groups = [item.get("selectionGroup") for item in selected if item.get("selectionGroup")]
        return all(groups.count(group) <= self.team["selectionRules"]["selectionGroupMax"] for group in groups)

    def default_roster(self):
        return ["veteran-sergeant", "vox-relay-beacon", "field-medicae-lascarbine", "grenadier-lascarbine",
                "guide-lascarbine", "gunner-meltagun", "heavy-gunner", "loader-lascarbine",
                "sharpshooter", "stub-gunner", "vox-operator-lascarbine"]

    def test_registry_schema_offline_and_sources(self):
        manifest = json.loads((ROOT / "Player_Operatives" / "manifest.json").read_text())
        self.assertEqual(next(team for team in manifest["teams"] if team["id"] == "spectre-squad")["file"], TEAM_PATH.name)
        self.assertIn("./Player_Operatives/SpectreSquad.json", (ROOT / "service-worker.js").read_text())
        self.assertEqual(self.team["schemaVersion"], 2)
        self.assertEqual(len(self.team["source"]["documents"]), 3)

    def test_ids_references_and_weapon_schema_are_valid(self):
        self.assertEqual(len(self.operatives), len(self.team["operatives"]))
        categories = {category["id"] for category in self.team["rosterCategories"]}
        ability_ids = set()
        for operative in self.operatives.values():
            self.assertIn(operative["category"], categories)
            weapon_ids = [weapon["id"] for weapon in operative["weapons"]]
            self.assertEqual(len(weapon_ids), len(set(weapon_ids)), operative["id"])
            for weapon in operative["weapons"]:
                self.assertIn(weapon["type"], {"ranged", "melee"})
                self.assertGreater(weapon["attacks"], 0)
                self.assertRegex(weapon["damage"], r"^\d+/\d+$")
            for ability in operative["abilities"]:
                self.assertTrue(ability["id"])
                ability_ids.add(ability["id"])
        self.assertTrue({"issue-mission", "medic", "concealed-position", "signal", "cool-headed"}.issubset(ability_ids))
        self.assertTrue(self.team["validation"]["requireStableIds"])
        self.assertIn("function validatePlayerTeamData", self.app)
        self.assertIn("invalid or duplicate faction rule ID", self.app)
        self.assertIn("invalid or duplicate ability ID", self.app)
        self.assertIn("weapon without a stable ID", self.app)

    def test_roster_size_mandatory_operatives_and_legal_default(self):
        self.assertEqual(self.team["rosterSize"], 11)
        categories = {category["id"]: category for category in self.team["rosterCategories"]}
        self.assertEqual((categories["leader"]["requiredCount"], categories["leader"]["maxCount"]), (1, 1))
        self.assertEqual((categories["support"]["requiredCount"], categories["support"]["maxCount"]), (1, 1))
        self.assertTrue(self.validate(self.default_roster()))
        self.assertFalse(self.validate(self.default_roster()[:-1]))
        self.assertFalse(self.validate(self.default_roster() + ["trooper-1-lascarbine"]))
        self.assertFalse(self.validate([id_ for id_ in self.default_roster() if id_ != "veteran-sergeant"] + ["trooper-1-lascarbine"]))
        self.assertFalse(self.validate([id_ for id_ in self.default_roster() if id_ != "vox-relay-beacon"] + ["trooper-1-lascarbine"]))

    def test_unique_specialists_allowed_troopers_and_mutually_exclusive_loadouts(self):
        groups = {}
        for operative in self.operatives.values():
            if operative.get("selectionGroup"):
                groups.setdefault(operative["selectionGroup"], []).append(operative)
        self.assertEqual({item["id"] for item in groups["gunner"]}, {"gunner-meltagun", "gunner-plasma"})
        self.assertEqual(len([group for group in groups if group.startswith("trooper-")]), 9)
        roster = self.default_roster()
        roster[-1] = "trooper-1-lascarbine"
        self.assertTrue(self.validate(roster))
        conflicting = roster[:-1] + ["trooper-1-lascarbine", "trooper-1-lasrifle"]
        self.assertFalse(self.validate(conflicting))
        self.assertIn("selectionGroupMaximum", self.app)
        self.assertIn("Choose only one loadout for each operative.", self.app)

    def test_all_operative_statistics(self):
        for operative in self.operatives.values():
            expected = (1, 0, 5, 3) if operative["id"] == "vox-relay-beacon" else ((2, 6, 5, 9) if operative["id"] == "veteran-sergeant" else (2, 6, 5, 8))
            self.assertEqual((operative["apl"], operative["move"], operative["save"], operative["wounds"]), expected, operative["id"])

    def test_distinct_weapon_profiles_and_exact_core_profiles(self):
        expected = {
            ("veteran-sergeant", "scoped-lascarbine"): (4, 3, "2/3", ["Lethal 5+", "Rending"]),
            ("veteran-sergeant", "bionic-arm"): (3, 3, "3/4", []),
            ("gunner-meltagun", "meltagun"): (4, 3, "6/3", ['Range 6"', "Devastating 4", "Piercing 2"]),
            ("gunner-plasma", "plasma-standard"): (4, 3, "4/6", ["Piercing 1"]),
            ("gunner-plasma", "plasma-supercharge"): (4, 3, "5/6", ["Hot", "Lethal 5+", "Piercing 1"]),
            ("heavy-gunner", "missile-frag"): (4, 3, "3/5", ['Blast 2"', "Heavy"]),
            ("heavy-gunner", "missile-krak"): (4, 3, "5/7", ["Heavy", "Piercing 1"]),
            ("sharpshooter", "long-las-concealed"): (4, 2, "3/3", ["Devastating 3", "Heavy", "Silent", "Concealed Position"]),
            ("sharpshooter", "long-las-mobile"): (4, 3, "3/4", []),
            ("sharpshooter", "long-las-stationary"): (4, 2, "3/3", ["Devastating 3", "Heavy"]),
            ("stub-gunner", "autostubber-focused"): (5, 3, "3/4", ["Heavy (Dash only)"]),
            ("stub-gunner", "autostubber-suppressive"): (5, 5, "0/0", ["Heavy", "Lethal 5+", "Seek Light", "Stun", 'Torrent 1"']),
            ("stub-gunner", "autostubber-sweeping"): (4, 3, "3/4", ["Heavy (Dash only)", 'Torrent 1"']),
        }
        for key, stats in expected.items():
            weapon = self.weapon(*key)
            self.assertEqual((weapon["attacks"], weapon["hit"], weapon["damage"], weapon["rules"]), stats)
        self.assertEqual(self.weapon("field-medicae-lascarbine", "lascarbine")["type"], "ranged")
        self.assertEqual(self.weapon("field-medicae-lascarbine", "gun-butt")["type"], "melee")
        for operative_id, weapon_id in [("heavy-gunner", "missile-frag"), ("stub-gunner", "autostubber-suppressive"), ("stub-gunner", "autostubber-sweeping")]:
            self.assertIn("Record wounds or elimination", self.weapon(operative_id, weapon_id)["manualResolution"])

    def test_combat_filter_and_single_multi_weapon_behaviour(self):
        self.assertIn("filter(w=>w.type===wantedType)", self.app)
        self.assertIn('<option value="">Select a weapon...</option>', self.app)
        self.assertIn("weaponSelect.value===''?null", self.app)
        self.assertIn("<strong>Weapon:</strong> —", self.app)
        self.assertIn("weapon.attacks", self.app)
        self.assertIn("if(singleTarget&&weapons.length===1", self.app)
        self.assertIn("runAutomaticCombatRolls", self.app)
        self.assertIn("if(draft)", self.app)
        self.assertNotIn("<strong>Manual tabletop resolution</strong>", self.app)
        self.assertIn("weaponRuleStatuses(profile)", self.app)

    def test_faction_and_manual_ability_classification(self):
        rules = {rule["id"]: rule for rule in self.team["factionRules"]}
        self.assertEqual(rules["elite-fieldcraft"]["automation"], "lifecycle-reminder")
        self.assertEqual(rules["camo-cloaks"]["automation"], "manual-tabletop-guidance")
        self.assertIn("Ready Step", rules["elite-fieldcraft"]["timing"])
        self.assertEqual(self.team["strategicGambits"][0]["turningPoints"], [1, 2, 3, 4])
        self.assertTrue(all(ability["automation"] == "manual-guidance" for operative in self.operatives.values() for ability in operative["abilities"]))

    def test_state_tracking_save_load_refresh_and_in_progress_combat_paths(self):
        script = """
const p=require('./persistence.js');
const save={saveVersion:1,playerTeamId:'spectre-squad',playerTeamFile:'SpectreSquad.json',playerRoster:['sharpshooter'],playerWounds:{sharpshooter:4},playerActivatedIds:['sharpshooter'],playerCasualtyIds:[],playerOperativeStates:{sharpshooter:{inPlay:true}},combatState:{side:'player',stage:{playerOperativeId:'sharpshooter',shootCombatDraft:{weaponIndex:1,rolledAttackDice:[{value:6}]}}},roster:[]};
const restored=p.migrateSave(p.createPersistedSave(save));
if(restored.playerTeamId!=='spectre-squad'||restored.playerWounds.sharpshooter!==4||restored.combatState.stage.shootCombatDraft.weaponIndex!==1)process.exit(1);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)
        for token in ["playerCurrentWounds", "playerCasualtyIds", "playerActivatedIds", "playerOperativeStates", "combatState"]:
            self.assertIn(token, self.app)

    def test_deathwatch_and_tempestus_regressions(self):
        deathwatch = json.loads((ROOT / "Player_Operatives" / "DeathWatch.json").read_text())
        aquilons = json.loads((ROOT / "Player_Operatives" / "TempestusAquilons.json").read_text())
        self.assertEqual((deathwatch["teamId"], deathwatch["rosterSize"], deathwatch["selectionRules"]["maxGravis"]), ("deathwatch", 5, 1))
        self.assertEqual((aquilons["teamId"], aquilons["rosterSize"], aquilons["selectionRules"]["mandatoryTroopers"]), ("tempestus-aquilons", 11, 3))
        self.assertIn("Drop Insertion", {rule["name"] for rule in aquilons["factionRules"]})
        self.assertNotIn("state.playerTeamId==='spectre-squad'", self.app)

    def test_version_consistency(self):
        expected = "8.6.20"
        self.assertIn(f"const APP_VERSION = '{expected}'", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}'", (ROOT / "service-worker.js").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"V{expected}", index)
        self.assertEqual(set(re.findall(r"\?v=(\d+\.\d+\.\d+)", index)), {expected})
        self.assertTrue((ROOT / "README.md").read_text().startswith(f"# Tomb World Solo Guide v{expected}"))


if __name__ == "__main__":
    unittest.main()
