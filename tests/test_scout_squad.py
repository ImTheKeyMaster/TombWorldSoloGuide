import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_PATH = ROOT / "Player_Operatives" / "ScoutSquad.json"

class ScoutSquadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.team = json.loads(TEAM_PATH.read_text())
        cls.ops = {operative["id"]: operative for operative in cls.team["operatives"]}
        cls.app = (ROOT / "app.js").read_text()

    def weapon(self, operative, weapon):
        return next(item for item in self.ops[operative]["weapons"] if item["id"] == weapon)

    def validate(self, selected):
        definitions = [self.ops[item] for item in selected if item in self.ops]
        if len(definitions) != self.team["rosterSize"]:
            return False
        for category in self.team["rosterCategories"]:
            count = sum(item["category"] == category["id"] for item in definitions)
            if count < category.get("requiredCount", 0) or count > category.get("maxCount", float("inf")):
                return False
        groups = {}
        for item in definitions:
            if item.get("selectionGroup"):
                groups[item["selectionGroup"]] = groups.get(item["selectionGroup"], 0) + 1
        return all(count <= self.team["selectionRules"]["selectionGroupMax"] for count in groups.values())

    def default_roster(self):
        return ["sergeant-shotgun", "heavy-gunner-heavy-bolter", "hunter", "sniper", "tracker",
                "warrior-1-shotgun", "warrior-2-boltgun", "warrior-3-pistol-blade", "warrior-4-shotgun"]

    def test_registry_schema_offline_and_sources(self):
        manifest = json.loads((ROOT / "Player_Operatives" / "manifest.json").read_text())
        self.assertEqual(next(team for team in manifest["teams"] if team["id"] == "scout-squad")["file"], TEAM_PATH.name)
        self.assertEqual(self.team["schemaVersion"], 2)
        self.assertTrue(self.team["validation"]["requireStableIds"])
        self.assertEqual(self.team["source"]["documents"], ["Scout Squad - Datacards", "Scout Squad - Faction Rules", "Scout Squad - Operative Selection"])
        self.assertIn("./Player_Operatives/ScoutSquad.json", (ROOT / "service-worker.js").read_text())

    def test_stable_unique_ids_and_references(self):
        self.assertEqual(len(self.ops), len(self.team["operatives"]))
        categories = {item["id"] for item in self.team["rosterCategories"]}
        rule_ids = [item["id"] for item in self.team["factionRules"] + self.team["strategicGambits"]]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        for operative in self.ops.values():
            self.assertIn(operative["category"], categories)
            weapons = [item["id"] for item in operative["weapons"]]
            abilities = [item["id"] for item in operative["abilities"]]
            self.assertTrue(all(weapons)); self.assertEqual(len(weapons), len(set(weapons)))
            self.assertTrue(all(abilities)); self.assertEqual(len(abilities), len(set(abilities)))

    def test_legal_roster_size_mandatory_sergeant_and_invalid_limits(self):
        roster = self.default_roster()
        self.assertEqual(self.team["rosterSize"], 9)
        self.assertTrue(self.validate(roster))
        self.assertFalse(self.validate(roster[:-1]))
        self.assertFalse(self.validate(roster + ["warrior-5-shotgun"]))
        self.assertFalse(self.validate(roster[1:] + ["warrior-5-shotgun"]))
        self.assertEqual(next(c for c in self.team["rosterCategories"] if c["id"] == "leader")["requiredCount"], 1)

    def test_unique_specialists_allowed_warriors_and_mutually_exclusive_loadouts(self):
        self.assertEqual(sum(op["officialName"] == "Scout Warrior" for op in self.ops.values()), 24)
        self.assertEqual({self.ops[f"warrior-1-{suffix}"]["selectionGroup"] for suffix in ["shotgun", "boltgun", "pistol-blade"]}, {"warrior-1"})
        conflict = self.default_roster()[:-1] + ["warrior-1-boltgun", "warrior-4-shotgun"]
        self.assertFalse(self.validate(conflict))
        heavy_conflict = ["sergeant-shotgun", "heavy-gunner-heavy-bolter", "heavy-gunner-missile-launcher", "hunter", "sniper", "warrior-1-shotgun", "warrior-2-shotgun", "warrior-3-shotgun", "warrior-4-shotgun"]
        self.assertFalse(self.validate(heavy_conflict))
        self.assertIn("Choose only one loadout for each operative.", self.app)

    def test_all_operative_stats(self):
        for operative in self.ops.values():
            self.assertEqual((operative["move"], operative["save"], operative["baseSize"]), (6, 4, 28))
            expected = (3, 11) if operative["role"] == "Leader" else (2, 10)
            self.assertEqual((operative["apl"], operative["wounds"]), expected)
        self.assertEqual({op["officialName"] for op in self.ops.values()}, {"Scout Sergeant", "Scout Heavy Gunner", "Scout Hunter", "Scout Sniper", "Scout Tracker", "Scout Warrior"})

    def test_exact_weapon_profiles_and_loadouts(self):
        expected = {
            ("sergeant-shotgun", "astartes-shotgun"): ("ranged", 4, 2, "4/4", ['Range 6"']),
            ("sergeant-pistol-chainsword", "chainsword"): ("melee", 5, 3, "4/5", []),
            ("heavy-gunner-heavy-bolter", "heavy-bolter-focused"): ("ranged", 5, 3, "4/5", ["Heavy (Dash only)", "Piercing Crits 1"]),
            ("heavy-gunner-heavy-bolter", "heavy-bolter-sweeping"): ("ranged", 4, 3, "4/5", ["Heavy (Dash only)", "Piercing Crits 1", 'Torrent 1"']),
            ("heavy-gunner-missile-launcher", "missile-launcher-frag"): ("ranged", 4, 3, "3/5", ['Blast 2"', "Heavy (Dash only)"]),
            ("heavy-gunner-missile-launcher", "missile-launcher-krak"): ("ranged", 4, 3, "5/7", ["Heavy (Dash only)", "Piercing 1"]),
            ("sniper", "sniper-rifle-mobile"): ("ranged", 4, 3, "3/4", []),
            ("sniper", "sniper-rifle-stationary"): ("ranged", 4, 2, "3/3", ["Devastating 3", "Heavy (Dash only)", "Silent"]),
            ("hunter", "combat-blade"): ("melee", 4, 3, "4/5", []),
        }
        for key, value in expected.items():
            item = self.weapon(*key)
            self.assertEqual((item["type"], item["attacks"], item["hit"], item["damage"], item["rules"]), value)
        for key in [("heavy-gunner-heavy-bolter", "heavy-bolter-sweeping"), ("heavy-gunner-missile-launcher", "missile-launcher-frag")]:
            self.assertIn("Record wounds or elimination", self.weapon(*key)["manualResolution"])

    def test_shooting_melee_single_multi_and_one_roll_paths(self):
        sniper = self.ops["sniper"]["weapons"]
        self.assertEqual(len([w for w in sniper if w["type"] == "ranged"]), 3)
        self.assertEqual(len([w for w in sniper if w["type"] == "melee"]), 1)
        warrior = self.ops["warrior-1-shotgun"]["weapons"]
        self.assertEqual(len([w for w in warrior if w["type"] == "ranged"]), 1)
        self.assertIn("filter(w=>w.type===wantedType)", self.app)
        self.assertIn('<option value="">Select a weapon...</option>', self.app)
        self.assertIn("<strong>Weapon:</strong> —", self.app)
        self.assertIn("if(singleTarget&&weapons.length===1", self.app)
        self.assertIn("if(draft)", self.app)
        self.assertIn("runAutomaticCombatRolls", self.app)

    def test_faction_rules_abilities_and_usage_limits(self):
        rules = {item["id"]: item for item in self.team["factionRules"]}
        gambits = {item["id"]: item for item in self.team["strategicGambits"]}
        self.assertEqual(rules["forward-scouting"]["selectionCount"], 6)
        self.assertEqual({key: rules[key]["selectionLimit"] for key in ["redeploy", "reposition", "trip-alarm", "booby-trap", "devise-plan", "designate-target", "spy"]}, {"redeploy": 1, "reposition": 2, "trip-alarm": 2, "booby-trap": 1, "devise-plan": 1, "designate-target": 1, "spy": 1})
        self.assertEqual(gambits["tactical-manoeuvre"]["usageLimit"], {"count": 2, "period": "battle"})
        self.assertEqual(gambits["diversion"]["usageLimit"], {"count": 1, "period": "battle"})
        self.assertTrue(all(item["forwardScoutingOption"] for item in list(rules.values())[1:] + list(gambits.values())))
        self.assertTrue(all(item["selectionLimit"] == 1 for item in gambits.values()))
        self.assertEqual(rules["trip-alarm"]["automation"], "lifecycle-reminder")
        self.assertTrue(all(item["automation"] in {"manual-tabletop-guidance", "lifecycle-reminder"} for item in rules.values()))
        self.assertTrue(all(a["automation"] == "manual-guidance" for op in self.ops.values() for a in op["abilities"]))
        actions = {a["id"]: a for op in self.ops.values() for a in op["abilities"] if a["id"] in {"optics", "track-enemy", "auspex-scan"}}
        self.assertEqual(set(actions), {"optics", "track-enemy", "auspex-scan"})
        self.assertTrue(all(action["kind"] == "unique-action" and action["apCost"] == 1 for action in actions.values()))
        self.assertTrue(all(a["kind"] == "passive-ability" for op in self.ops.values() for a in op["abilities"] if a["id"] not in actions))

    def test_save_refresh_combat_wounds_elimination_activation_and_off_board(self):
        script = r'''const p=require('./persistence.js');
const save={saveVersion:1,playerTeamId:'scout-squad',playerTeamFile:'ScoutSquad.json',playerRoster:['sniper'],playerWounds:{sniper:4},playerActivatedIds:['sniper'],playerCasualtyIds:['sniper'],playerOperativeStates:{sniper:{inPlay:false,offBoardReason:'mission'}},combatState:{side:'player',stage:{playerOperativeId:'sniper',shootCombatDraft:{weaponIndex:2,rolledAttackDice:[{value:6}]}}},factionRuleState:{forwardScouting:['trip-alarm']},roster:[]};
const restored=p.migrateSave(p.createPersistedSave(save));
if(restored.playerTeamId!=='scout-squad'||restored.playerWounds.sniper!==4||restored.playerActivatedIds[0]!=='sniper'||restored.playerCasualtyIds[0]!=='sniper'||restored.playerOperativeStates.sniper.inPlay!==false||restored.combatState.stage.shootCombatDraft.rolledAttackDice.length!==1||restored.factionRuleState.forwardScouting[0]!=='trip-alarm')process.exit(1);'''
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)
        for token in ["playerCurrentWounds", "playerCasualtyIds", "playerActivatedIds", "playerOperativeStates", "combatState"]:
            self.assertIn(token, self.app)

    def test_existing_team_regressions_and_no_team_branch(self):
        deathwatch = json.loads((ROOT / "Player_Operatives" / "DeathWatch.json").read_text())
        aquilons = json.loads((ROOT / "Player_Operatives" / "TempestusAquilons.json").read_text())
        spectre = json.loads((ROOT / "Player_Operatives" / "SpectreSquad.json").read_text())
        self.assertEqual((deathwatch["teamId"], deathwatch["rosterSize"]), ("deathwatch", 5))
        self.assertEqual((aquilons["teamId"], aquilons["rosterSize"]), ("tempestus-aquilons", 11))
        self.assertEqual((spectre["teamId"], spectre["rosterSize"]), ("spectre-squad", 11))
        self.assertNotRegex(self.app, r"playerTeamId\s*={2,3}\s*['\"]scout-squad")

    def test_version_consistency(self):
        expected = "7.1.2"
        self.assertIn(f"const APP_VERSION = '{expected}'", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}'", (ROOT / "service-worker.js").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"V{expected}", index)
        self.assertEqual(set(re.findall(r"\?v=(\d+\.\d+\.\d+)", index)), {expected})
        self.assertTrue((ROOT / "README.md").read_text().startswith(f"# Tomb World Solo Guide v{expected}"))

if __name__ == "__main__":
    unittest.main()
