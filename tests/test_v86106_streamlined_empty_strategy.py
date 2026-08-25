from versioning import CURRENT_APP_VERSION
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def function_body(name):
    match = re.search(rf"  function {name}\([^\n]*", APP)
    if not match:
        return ""
    end = APP.find("\n  function ", match.end())
    return APP[match.start():end if end >= 0 else len(APP)]


class StreamlinedEmptyStrategyTests(unittest.TestCase):
    def run_shortcut_cases(self, cases):
        script = f"""
let state;
function strategyEventPresentation(data){{return {{required:data.requiredEventCount||0,events:data.events||[]}};}}
function strategyRequiredRedrawPending(){{return Boolean(state.redrawPending);}}
function canLeaveStrategyEvents(){{return !state.strategyData.eventPending&&!state.redrawPending;}}
{function_body("strategyHasNoDownstreamWork").strip()}
const cases={cases};
console.log(JSON.stringify(cases.map(item=>{{state=item;return strategyHasNoDownstreamWork();}})));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def test_01_shortcut_uses_canonical_event_and_reinforcement_state(self):
        body = function_body("strategyHasNoDownstreamWork")
        for expected in (
            "strategyEventPresentation(d)", "presentation.required===0", "!d.eventPending",
            "event.status==='drawn'", "!strategyRequiredRedrawPending()",
            "canLeaveStrategyEvents()", "completed?.includes('reinforcement')",
            "reinforcements.turningPoint===state.turningPoint", "reinforcements.status==='complete'",
            "reinforcements.operativeIds", "reinforcements.blocked",
            "reinforcements.blockedByCapacity", "reinforcements.blockedByInventory", "d.blocked",
        ):
            self.assertIn(expected, body)
        self.assertNotIn("shifting-labyrinth", body.lower())

    def test_02_actions_switches_destination_and_hides_progress_only_for_shortcut(self):
        body = function_body("strategyActionsStepHtml")
        self.assertIn("completeFromActions=strategyHasNoDownstreamWork()", body)
        self.assertIn("completeFromActions?'':strategyProgressHtml('actions')", body)
        self.assertIn("completeFromActions?'completeStrategyFromActions':'continueStrategyEvents'", body)
        self.assertIn("completeFromActions?'Strategy Phase Complete':'Continue to Tomb World Events'", body)
        self.assertIn("Resolve Strategy Phase Actions", body)
        self.assertIn("Strategy Phase Checklist", body)

    def test_03_required_events_and_reinforcements_preserve_full_flow(self):
        shortcut = function_body("strategyHasNoDownstreamWork")
        actions = function_body("strategyActionsStepHtml")
        self.assertIn("presentation.required===0", shortcut)
        self.assertIn("!(reinforcements.operativeIds||[]).length", shortcut)
        self.assertIn("strategyProgressHtml('actions')", actions)
        self.assertIn("continueStrategyEvents", actions)
        self.assertIn("showStrategyViewStep('events','actions')", function_body("bindPlay"))

    def test_03b_constructed_states_only_allow_the_genuinely_empty_case(self):
        base = "{turningPoint:2,strategyData:{requiredEventCount:0,eventPending:false,events:[],blocked:0},strategyPipeline:{completed:['reinforcement']},reinforcementState:{turningPoint:2,status:'complete',operativeIds:[],blocked:0,blockedByCapacity:0,blockedByInventory:0}}"
        cases = f"[{base},{{...{base},strategyData:{{...{base}.strategyData,requiredEventCount:1}}}},{{...{base},reinforcementState:{{...{base}.reinforcementState,status:'placement',operativeIds:['npo-1']}}}},{{...{base},reinforcementState:{{...{base}.reinforcementState,status:'blocked',blocked:1}}}},{{...{base},strategyData:{{...{base}.strategyData,eventPending:true,events:[{{status:'drawn'}}]}}}},{{...{base},redrawPending:true}},{{...{base},strategyPipeline:{{completed:[]}}}}]"
        self.assertEqual("[true,false,false,false,false,false,false]", self.run_shortcut_cases(cases))

    def test_04_blocked_reinforcement_reporting_is_not_skipped(self):
        shortcut = function_body("strategyHasNoDownstreamWork")
        review = function_body("strategyReviewStepHtml")
        self.assertIn("!(Number(reinforcements.blocked)||0)", shortcut)
        self.assertIn("!(Number(reinforcements.blockedByCapacity)||0)", shortcut)
        self.assertIn("!(Number(reinforcements.blockedByInventory)||0)", shortcut)
        self.assertIn("No reinforcements could be deployed", review)

    def test_05_mandatory_action_keeps_complete_destination_disabled(self):
        body = function_body("strategyActionsStepHtml")
        self.assertIn("disabled:missionPending", body)
        self.assertIn("Resolve the mandatory mission Strategy Phase rule before continuing.", body)
        self.assertIn("canLeaveStrategyActions()", function_body("canCompleteStrategyPhase"))

    def test_06_direct_completion_revalidates_and_reuses_initiative_logic(self):
        binding = function_body("bindPlay")
        direct = next(line for line in binding.splitlines() if "$('#completeStrategyFromActions')" in line)
        normal = next(line for line in binding.splitlines() if "$('#continueStrategy')" in line)
        self.assertIn("!strategyHasNoDownstreamWork()||!canCompleteStrategyPhase()", direct)
        initiative = "state.strategyData?.suggestedInitiative==='npo'?'npo':'player'"
        self.assertIn(initiative, direct)
        self.assertIn(initiative, normal)
        self.assertEqual(direct.count("beginFirefight("), 1)

    def test_07_completion_uses_existing_firefight_initializer(self):
        direct = next(line for line in function_body("bindPlay").splitlines() if "$('#completeStrategyFromActions')" in line)
        for stale_state_mutation in ("viewStep=", "eventPending=", "reinforcementState="):
            self.assertNotIn(stale_state_mutation, direct)

    def test_08_release_is_consistent_and_save_schema_stays_three(self):
        self.assertEqual((8, 6, 106), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f"<div class=\"version\">V{CURRENT_APP_VERSION}</div>", INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
                      "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
                      "dice-sfx.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
