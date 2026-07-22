import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "app.js").read_text()


class ReinforcementCheckboxInteractionTests(unittest.TestCase):
    def function_source(self, start, end):
        return APP.split(f"function {start}", 1)[1].split(f"function {end}", 1)[0]

    def test_placement_rows_are_tappable_and_have_no_hatchway_inputs(self):
        placement_markup = re.search(
            r"const placements=.*?\.join\(''\);", APP, re.DOTALL
        ).group(0)
        self.assertIn('<label class="check-row">', placement_markup)
        self.assertIn("data-reinforcement-placement", placement_markup)
        self.assertNotIn("data-reinforcement-hatchway", APP)
        self.assertNotIn("recordReinforcementHatchway", APP)

    def test_real_confirmation_logic_survives_rerender_and_controls_strategy(self):
        confirmation = "function confirmReinforcementPlacement(id,confirmed)" + self.function_source(
            "confirmReinforcementPlacement(id,confirmed)", "rollInitiative()"
        )
        script = f"""
const assert=require('assert');
const state={{
  roster:[
    {{id:'a',reinforcement:{{placementConfirmed:false}},deployed:false}},
    {{id:'b',reinforcement:{{hatchway:'legacy',placementConfirmed:false}},deployed:false}}
  ],
  reinforcementState:{{status:'placement',operativeIds:['a','b']}}
}};
let rendered;
function save(){{}}
function render(){{
  rendered={{
    checkboxes:state.roster.map(npo=>({{id:npo.id,checked:npo.reinforcement.placementConfirmed}})),
    continueStrategyDisabled:state.reinforcementState.status==='placement'
  }};
}}
{confirmation}
confirmReinforcementPlacement('a',true);
assert.equal(state.roster[0].reinforcement.placementConfirmed,true);
assert.equal(rendered.checkboxes[0].checked,true);
assert.equal(state.reinforcementState.status,'placement');
assert.equal(rendered.continueStrategyDisabled,true);
confirmReinforcementPlacement('b',true);
assert.equal(state.reinforcementState.status,'complete');
assert.equal(rendered.continueStrategyDisabled,false);
confirmReinforcementPlacement('a',false);
assert.equal(state.roster[0].reinforcement.placementConfirmed,false);
assert.equal(state.reinforcementState.status,'placement');
assert.equal(rendered.continueStrategyDisabled,true);
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_strategy_button_uses_placement_status_and_legacy_hatchways_are_preserved(self):
        strategy_card = self.function_source("strategyCard()", "strategyEventHtml(event)")
        self.assertIn("placementPending=state.reinforcementState.status==='placement'", strategy_card)
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled':''", strategy_card)
        normalization = self.function_source("normalizeNpo(npo)", "mission()")
        self.assertIn("hatchway:String(npo.reinforcement.hatchway||'')", normalization)


if __name__ == "__main__":
    unittest.main()
