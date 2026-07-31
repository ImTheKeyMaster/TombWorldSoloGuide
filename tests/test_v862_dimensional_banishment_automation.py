#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


class DimensionalBanishmentAutomationTests(unittest.TestCase):
    def section(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def run_resolver(self, combat, dice):
        resolver = "function resolveDimensionalBanishment" + self.section(
            "function resolveDimensionalBanishment", "function resolveAutomaticDimensionalBanishment"
        )
        script = f"""
const combatAbilityHandlers={{'dimensional-banishment':({{criticalSuccesses,damage,targetIncapacitated}})=>!targetIncapacitated&&(damage>0||criticalSuccesses>0)}};
{resolver}
const original={json.dumps(combat)};
const snapshot=JSON.stringify(original);
const result=resolveDimensionalBanishment(original,{json.dumps(dice)});
console.log(JSON.stringify({{result,unchanged:snapshot===JSON.stringify(original)}}));
"""
        return json.loads(subprocess.check_output(["node", "-e", script], text=True))

    def base_combat(self, **updates):
        combat = {"profile": {"weaponId": "transdimensional-isolator"}, "critRemaining": 0,
                  "damage": 6, "before": 15, "after": 9}
        combat.update(updates)
        return combat

    def test_version_and_release_notes(self):
        self.assertIn("const APP_VERSION = '8.6.2';", APP)
        self.assertIn("const APP_VERSION = '8.6.2';", WORKER)
        self.assertIn("V8.6.2", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.2"))
        self.assertIn("Version 8.6.2 - Automate Dimensional Banishment", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.2", INDEX)

    def test_damage_or_critical_triggers_only_for_surviving_target(self):
        self.assertTrue(self.run_resolver(self.base_combat(), [5, 6])["result"]["dimensionalBanishmentTriggered"])
        critical = self.run_resolver(self.base_combat(damage=0, critRemaining=1), [3, 4])["result"]
        self.assertTrue(critical["dimensionalBanishmentTriggered"])
        self.assertFalse(self.run_resolver(self.base_combat(after=0), [6, 6])["result"]["dimensionalBanishmentTriggered"])
        self.assertFalse(self.run_resolver(self.base_combat(damage=0, critRemaining=0), [6, 6])["result"]["dimensionalBanishmentTriggered"])

    def test_pure_resolver_stores_two_dice_total_and_comparison(self):
        success = self.run_resolver(self.base_combat(), [5, 6])
        self.assertTrue(success["unchanged"])
        self.assertEqual(success["result"]["dimensionalBanishmentDice"], [5, 6])
        self.assertEqual(success["result"]["dimensionalBanishmentRoll"], 11)
        self.assertEqual(success["result"]["dimensionalBanishmentRemainingWounds"], 9)
        self.assertTrue(success["result"]["dimensionalBanishmentIncapacitated"])
        self.assertEqual(success["result"]["after"], 0)
        for dice in ([4, 5], [3, 4]):
            result = self.run_resolver(self.base_combat(), dice)["result"]
            self.assertFalse(result["dimensionalBanishmentIncapacitated"])
            self.assertEqual(result["after"], 9)

    def test_automatic_resolution_rolls_exactly_two_d6_and_is_idempotent(self):
        automatic = self.section("function resolveAutomaticDimensionalBanishment", "function rolledCombatDice")
        self.assertIn("rollDice(2,6)", automatic)
        resolver = self.section("function resolveDimensionalBanishment", "function resolveAutomaticDimensionalBanishment")
        self.assertIn("if(combat.dimensionalBanishmentResolved)return {...combat}", resolver)
        self.assertIn("dimensionalBanishmentDice:values", resolver)
        self.assertIn("dimensionalBanishmentRemainingWounds:normalAfter", resolver)

    def test_manual_controls_and_instructions_are_removed(self):
        self.assertNotIn("Dimensional Banishment 2D6 result (0 if not triggered)", APP)
        self.assertNotIn("Roll 2D6 physically", APP)
        self.assertNotIn("id=\"dimensionalBanishmentRoll\"", APP)
        self.assertNotIn("dimensionalBanishmentField", APP)

    def test_accessible_animated_result_explains_both_outcomes(self):
        reminder = self.section("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("Rolling 2D6...", reminder)
        self.assertIn("animated-roll", reminder)
        self.assertIn("Dimensional Banishment die ${index+1}: ${value}", reminder)
        self.assertIn("Dimensional Banishment total: ${total}", reminder)
        self.assertIn("is greater than the target’s", reminder)
        self.assertIn("is not greater than the target’s", reminder)
        self.assertIn("is incapacitated", reminder)
        self.assertIn("survives with", reminder)

    def test_continue_guard_is_released_after_banishment_animation(self):
        shared = self.section("function displaySharedCombatResult", "function settleDimensionalBanishment")
        player = self.section("function displayPendingPlayerCombat", "function npoBehavior")
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("const completeWaiting=()=>", shared)
        self.assertIn("visualComplete=true", shared)
        self.assertIn("return {completeWaiting}", shared)
        self.assertIn("display?.completeWaiting()", player)
        self.assertIn("display?.completeWaiting()", npo)

    def test_persistence_legacy_totals_multitarget_and_journal_guards(self):
        legacy = self.run_resolver({**self.base_combat(), "dimensionalBanishmentRoll": 10}, [])["result"]
        self.assertEqual(legacy["dimensionalBanishmentRoll"], 10)
        self.assertEqual(legacy["dimensionalBanishmentDice"], [])
        committed_legacy = self.run_resolver({**self.base_combat(after=0), "dimensionalBanishmentRoll": 10,
                                              "dimensionalBanishmentTriggered": True}, [])["result"]
        self.assertEqual(committed_legacy["dimensionalBanishmentRemainingWounds"], 9)
        self.assertTrue(committed_legacy["dimensionalBanishmentIncapacitated"])
        self.assertIn("Recorded Dimensional Banishment total", APP)
        self.assertIn("state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};\n      save();", APP)
        self.assertIn("advanceWeaponRuleResolution(queue,target.id)", APP)
        self.assertIn("dimensionalBanishmentJournaled", APP)

    def test_incapacitation_uses_existing_commit_pipeline_and_effects_remain(self):
        pipeline = self.section("function applyPendingPlayerDamage", "function showAggressiveDefenseResolution")
        self.assertIn("offerReanimateForPendingDamage", pipeline)
        self.assertIn("showIncapacitationOrderChoice", pipeline)
        self.assertIn("showAggressiveDefenseResolution", pipeline)
        self.assertIn("if(!pending||pending.committed)continue", pipeline)
        self.assertIn("pending.committed=true", pipeline)
        self.assertIn("dimensionalBanishmentRemainingWounds", APP)


if __name__ == "__main__":
    unittest.main()
