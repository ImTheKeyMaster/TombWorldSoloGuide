from versioning import CURRENT_APP_VERSION
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def function_source(name):
    markers = (f"  function {name}", f"function {name}", f"  async function {name}")
    start = min(position for marker in markers if (position := APP.find(marker)) >= 0)
    ends = [position for marker in ("\n  function ", "\nfunction ", "\n  async function ")
            if (position := APP.find(marker, start + 1)) >= 0]
    end = min(ends) if ends else len(APP)
    return APP[start:end]


class V8642NoNpoCombatTargetsTests(unittest.TestCase):
    def test_authoritative_target_helper_uses_deployed_living_npos(self):
        active = function_source("activeNpos")
        helper = function_source("hasValidPlayerCombatTargets")
        self.assertIn("battlefieldState==='deployed'", active)
        self.assertIn("n.wounds > 0", active)
        self.assertIn("activeNpos().some", helper)
        self.assertIn("projectedNpoWounds", helper)

    def test_activation_marks_both_combat_actions_unavailable_without_targets(self):
        catalog = function_source("playerHumanActionCatalog")
        legality = function_source("playerHumanActionState")
        self.assertIn("name:'Shoot'", catalog)
        self.assertIn("name:'Fight'", catalog)
        self.assertIn("!hasValidPlayerCombatTargets({})", legality)
        self.assertIn("reason:'No valid target'", legality)

    def test_unresolved_stale_combat_is_cleared_without_refunding_resolved_actions(self):
        source = function_source("normalizeImpossiblePlayerCombat")
        self.assertIn("pendingAttackResults(normalized,attackType).length", source)
        self.assertIn("normalized[attackType]=false", source)
        self.assertIn("CombatDraft`]=null", source)
        self.assertIn("state.weaponRuleResolution=null", source)
        self.assertNotIn("apl", source.lower())
        self.assertNotIn("playerOperativeId=", source)

    def test_completion_and_target_entry_normalize_impossible_combat(self):
        self.assertIn("stage=normalizeImpossiblePlayerCombat(stage)", function_source("completePlayerActivation"))
        resolver = function_source("resolvePendingPlayerAttacks")
        self.assertIn("stage=normalizeImpossiblePlayerCombat(stage)", resolver)
        wizard = function_source("showPendingPlayerAttackWizard")
        self.assertIn("if(!targets.length)", wizard)
        self.assertIn("showPlayerActivation(normalizeImpossiblePlayerCombat(stage))", wizard)

    def test_no_zero_enemy_victory_rule_was_added(self):
        helper = function_source("hasValidPlayerCombatTargets")
        self.assertNotIn("victory", helper.lower())
        self.assertNotIn("gameEnd", helper)

    def test_target_availability_is_recalculated_not_persisted(self):
        helper = function_source("hasValidPlayerCombatTargets")
        self.assertIn("activeNpos()", helper)
        self.assertNotIn("state.", helper)

    def test_version_and_save_version(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
