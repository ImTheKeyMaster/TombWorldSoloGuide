import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class CanoptekIntegrationTests(unittest.TestCase):
    def test_legality_precedes_role_ranking(self):
        self.assertIn("function legalNpoActions", APP)
        self.assertIn("function rankLegalNpoActions", APP)
        body = APP.split("function recommendedNpoActions", 1)[1].split("\n  }", 1)[0]
        self.assertIn("rankLegalNpoActions(n,legalNpoActions(n,context),context)", body)
        self.assertIn("cost>remainingAp", APP)
        self.assertIn("completed.has('fight')", APP)

    def test_all_circle_roles_have_priorities_and_support_actions(self):
        for profile_id in (
            "geomancer", "canoptek-tomb-crawler", "canoptek-macrocyte-warrior",
            "canoptek-macrocyte-accelerator", "canoptek-macrocyte-reanimator",
        ):
            self.assertIn(f"'{profile_id}':", APP)
        for action in ("Canoptek Control", "Molecular Breach", "Geomantic Disturbance", "Overcharge", "Cranial Overload", "Nanoscarab Beam"):
            self.assertIn(action, APP)

    def test_effective_apl_is_activation_source_and_expires(self):
        self.assertIn("apl=effectiveApl(n.id,definition.apl)", APP)
        self.assertIn("remainingAp:apl", APP)
        self.assertIn("expireActivationEffects(n.id)", APP)
        self.assertIn("applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'overcharge',amount:1})", APP)
        self.assertIn("ruleId:'cranial-overload',amount:-1", APP)

    def test_loadouts_and_modes_use_shared_attack_profiles(self):
        self.assertIn("function npoAttackProfiles", APP)
        self.assertIn("(definition.rangedWeapons||[]).filter(weapon=>weapon.id===npo.weaponId)", APP)
        self.assertIn("availableProfiles.map", APP)
        self.assertIn("dimensionalBanishmentRequired(combat)", APP)

    def test_reanimate_is_offered_before_damage_commit(self):
        application = APP.index("function applyPendingPlayerDamage")
        offer = APP.index("offerReanimateForPendingDamage", application)
        wound_commit = APP.index("n.wounds=Math.max(0,pending.after)", application)
        self.assertLess(offer, wound_commit)
        self.assertIn("state.npoRuleState.oncePerTurningPoint.reanimate", APP)
        self.assertIn("pending.after=1", APP)

    def test_scuttling_is_strategy_phase_new_instance_exception(self):
        self.assertIn('id="ceaselessScuttling"', APP)
        self.assertIn("function createCeaselessScuttlingWarrior", APP)
        self.assertIn("returned||createNpo", APP)
        self.assertIn("warrior.createdBy='a-ceaseless-scuttling'", APP)
        self.assertIn("warrior.order='Conceal'", APP)
        self.assertIn("turningPoint>1&&living<3&&deployed<MAX_NPOS", APP)

    def test_reviewed_reanimate_and_modifier_regressions(self):
        self.assertIn("protectedForAction=n.preventIncapacitationActionId===state.activationNumber", APP)
        self.assertIn("!pending.aggressiveDefenseDamageApplied", APP)
        self.assertIn("apl=effectiveApl(current.playerOperativeId,baseApl)", APP)
        self.assertIn("Continue Activation", APP)
        self.assertIn("consumeMolecularBreach(target.id,freeAction)", APP)

    def test_manual_spatial_confirmation_is_preserved(self):
        self.assertIn("I confirmed that this target is visible and within range.", APP)
        self.assertIn("Choose a visible terrain point within 8 inches", APP)
        self.assertIn("Roll Damage", APP)

    def test_version_matrix_and_portrait_constraints(self):
        self.assertIn("const APP_VERSION = '8.5.4';", APP)
        self.assertIn("V8.5.4", (ROOT / "index.html").read_text())
        self.assertNotIn("obelisk node matrix support", APP.lower())
        self.assertNotIn("npoPortrait", APP)


if __name__ == "__main__":
    unittest.main()
