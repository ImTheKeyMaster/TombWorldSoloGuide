import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
REVIEW = APP.split("function strategyReviewStepHtml(d)", 1)[1].split(
    "function strategyCard()", 1
)[0]
GENERATION = APP.split("function processReinforcementStage()", 1)[1].split(
    "function reinforcementTriggered", 1
)[0]
CONFIRMATION = APP.split("function confirmReinforcementPlacement", 1)[1].split(
    "function rollInitiative", 1
)[0]


class PartialReinforcementDeploymentTests(unittest.TestCase):
    def test_partial_result_separates_deployable_and_blocked_counts(self):
        self.assertIn("Deploy ${pendingNpos.length} NPO", REVIEW)
        self.assertIn("additional reinforcement${blockedCount===1?'':'s'} could not be deployed", REVIEW)
        self.assertNotIn("Unable to Deploy", REVIEW)
        self.assertIn("data-reinforcement-placement", REVIEW)
        self.assertNotIn("blockedOperativeIds.map", REVIEW)

    def test_confirmation_changes_heading_and_keeps_blocked_result(self):
        self.assertIn("${deployedNpos.length} NPO${deployedNpos.length===1?'':'s'} deployed", REVIEW)
        self.assertIn("blockedCount?`<div class=", REVIEW)
        self.assertIn("placementConfirmed", REVIEW)
        self.assertIn("save();render();", CONFIRMATION)
        self.assertIn("npo.deployed=npo.reinforcement.placementConfirmed", CONFIRMATION)

    def test_fully_blocked_and_precise_reasons_are_present(self):
        self.assertIn("No reinforcements could be deployed", REVIEW)
        self.assertIn("The battlefield limit of ${MAX_NPOS} NPOs was reached.", REVIEW)
        self.assertIn("No eligible physical NPO models remain in the Tomb World inventory.", REVIEW)
        self.assertIn("The battlefield limit was reached and no eligible physical NPO models remain.", REVIEW)
        self.assertNotIn("Battlefield capacity was reached or no legal physical model remains.", APP)

    def test_generation_tracks_capacity_and_inventory_without_phantom_npos(self):
        self.assertIn("blockedByCapacity=blocked", GENERATION)
        self.assertIn("blockedByInventory++", GENERATION)
        self.assertNotIn("blockedOperativeIds.push", GENERATION)

    def test_saved_results_restore_precise_blocking_reasons(self):
        normalization = APP.split("function normalizeState(raw)", 1)[1].split(
            "function npoDefinition", 1
        )[0]
        self.assertIn("const hasBlockedReasons=", normalization)
        self.assertIn("const legacyCapacityBlocked=", normalization)
        self.assertIn("blockedByInventory=hasInventoryReason?", normalization)
        self.assertIn("deployingNpos.length||blockedCount", REVIEW)
        self.assertNotIn("deployingNpos.length||d.blocked", REVIEW)

    def test_blocked_results_do_not_control_strategy_completion(self):
        self.assertIn("state.reinforcementState.status!=='placement'", APP)
        self.assertIn("status=reinforcements.length?'placement':blocked?'blocked':'complete'", GENERATION)

    def test_warning_is_secondary_and_accessible(self):
        self.assertIn('aria-live="polite"', REVIEW)
        self.assertIn('role="status"', REVIEW)
        self.assertIn(".reinforcement-blocked{margin-top:18px", STYLES)
        self.assertIn("background:rgba(242,191,114,.06)", STYLES)

    def test_version_8_5_4_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.7.1';", APP)
        self.assertIn("const APP_VERSION = '8.7.1';", WORKER)
        self.assertIn("V8.7.1", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.7.1"))
        self.assertIn("## v8.6.25", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.7.1", INDEX)


if __name__ == "__main__":
    unittest.main()
