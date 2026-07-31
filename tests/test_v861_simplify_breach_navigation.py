import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
BREACH_FLOW = APP.split("function clearPendingBreach(stage)", 1)[1].split("async function performBreachSarcophagus", 1)[0]


class SimplifyBreachNavigationV861Tests(unittest.TestCase):
    def test_first_question_has_cancel_and_no_close_guide(self):
        first = BREACH_FLOW.split("if(context.step==='control-range')", 1)[1].split("if(context.step==='enemy-control-range')", 1)[0]
        self.assertIn('id="cancelBreach"', first)
        self.assertIn('aria-label="Cancel and abandon Breach Sarcophagus"', first)
        self.assertNotIn("Close Guide", first)
        self.assertIn("$('#cancelBreach').onclick=()=>clearPendingBreach(stage)", first)

    def test_cancel_clears_context_and_returns_to_unchanged_activation(self):
        clear = BREACH_FLOW.split("function focusBreachQuestion", 1)[0]
        self.assertIn("state.missionActionContext=null", clear)
        self.assertIn("state.combatState={side:'player',stage:{...stage}}", clear)
        self.assertIn("showPlayerActivation(stage)", clear)
        for committed_side_effect in ("roll()", "missionBreachCommitted=true", "executeMissionAction", "log("):
            self.assertNotIn(committed_side_effect, clear)

    def test_second_question_has_only_full_width_back_navigation(self):
        second = BREACH_FLOW.split("if(context.step==='enemy-control-range')", 1)[1].split("const total=", 1)[0]
        self.assertNotIn("Close Guide", second)
        self.assertNotIn("cancelBreach", second)
        self.assertIn('class="wizard-actions breach-navigation"', second)
        self.assertIn('aria-label="Back to the sarcophagus control-range question"', second)
        self.assertIn("context.enemyControlRangeConfirmed=null;context.step='control-range'", second)
        self.assertIn("focusBreachQuestion('#breachControlQuestion')", second)

    def test_confirmation_has_only_perform_and_full_width_back(self):
        confirmation = BREACH_FLOW.split("const total=", 1)[1]
        self.assertIn('id="performBreach"', confirmation)
        self.assertNotIn("Close Guide", confirmation)
        self.assertNotIn("cancelBreach", confirmation)
        self.assertEqual(confirmation.count('class="wizard-actions breach-navigation"'), 2)
        self.assertIn('aria-label="Back to the enemy control-range question"', confirmation)
        self.assertIn("context.enemyControlRangeConfirmed=null;context.step='enemy-control-range'", confirmation)
        self.assertIn("focusBreachQuestion('#breachEnemyQuestion')", confirmation)
        self.assertNotIn("context.controlRangeConfirmed=null", confirmation)

    def test_navigation_before_perform_has_no_commit_side_effects(self):
        for committed_side_effect in ("roll()", "missionBreachCommitted=true", "executeMissionAction", "log("):
            self.assertNotIn(committed_side_effect, BREACH_FLOW)
        self.assertIn("$('#performBreach').onclick=()=>performBreachSarcophagus(stage)", BREACH_FLOW)

    def test_persisted_steps_render_the_expected_buttons(self):
        self.assertIn("if(context.step==='control-range')", BREACH_FLOW)
        self.assertIn("if(context.step==='enemy-control-range')", BREACH_FLOW)
        self.assertIn("save();renderBreachSarcophagusStep(stage)", BREACH_FLOW)
        self.assertIn(".wizard-actions.breach-navigation .btn{width:100%}", STYLES)

    def test_release_version_and_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.5';", APP)
        self.assertIn("const APP_VERSION = '8.6.5';", WORKER)
        self.assertIn("V8.6.5", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.5", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.5"))
        self.assertIn("Version 8.6.1 - Simplify Breach Navigation", README)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
