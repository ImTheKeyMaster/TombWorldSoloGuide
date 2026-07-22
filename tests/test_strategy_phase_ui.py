import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
STRATEGY_CARD = re.search(
    r"function strategyCard\(\)\{(?P<body>.*?)\n  \}\n\n  function strategyEventHtml",
    APP,
    re.S,
).group("body")
REINFORCEMENTS = APP.split("function processReinforcementStage()", 1)[1].split("function reinforcementTriggered", 1)[0]


class StrategyPhaseUiTests(unittest.TestCase):
    def test_reinforcement_results_render_in_normal_card_flow(self):
        self.assertIn('class="card reinforcement-card"', STRATEGY_CARD)
        self.assertIn(".reinforcement-card{margin:18px 0", STYLES)
        self.assertNotIn("position:absolute", STYLES.split(".reinforcement-card", 1)[1].split("\n", 1)[0])
        self.assertNotIn("Additional NPOs generated", APP)
        self.assertNotIn('data-tooltip="Additional NPOs', APP)

    def test_card_lists_exact_deployed_npo_names_and_action(self):
        self.assertIn("deployingNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`)", STRATEGY_CARD)
        self.assertIn("Deploy ${deployingNpos.length} NPO", STRATEGY_CARD)
        self.assertIn("onto the battlefield using the Tomb World reinforcement rules.", STRATEGY_CARD)

    def test_empty_reinforcement_card_is_not_rendered(self):
        self.assertIn("deployingNpos.length||d.blocked", STRATEGY_CARD)
        self.assertIn("</section>`:''", STRATEGY_CARD)
        self.assertNotIn("No reinforcements arrive.", APP)

    def test_reserve_npos_are_selected_and_deployed_without_duplication(self):
        self.assertIn("reserveNpos().find", REINFORCEMENTS)
        self.assertIn("n.battlefieldState='deployed';n.deployed=true;n.dormant=state.threat===0;n.ready=!n.dormant", REINFORCEMENTS)
        self.assertIn("function activeNpos(){ return state.roster.filter(n => n.battlefieldState==='deployed'", APP)
        self.assertIn("filter(id=>id!==n.id)", REINFORCEMENTS)
        deploy_branch = REINFORCEMENTS.split("continue;", 1)[1]
        self.assertLess(deploy_branch.index("if(n){"), deploy_branch.index("createNpo(type"))

    def test_blocked_npos_are_named_and_remain_in_reserve(self):
        self.assertIn("blockedOperativeIds.push(n.id)", REINFORCEMENTS)
        blocked_branch = REINFORCEMENTS.split("if(i>=actual){", 1)[1].split("continue;", 1)[0]
        self.assertNotIn("battlefieldState=", blocked_branch)
        self.assertIn("deployed:false", blocked_branch)
        self.assertIn("if(!n){", blocked_branch)
        self.assertIn("blockedNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`)", STRATEGY_CARD)
        self.assertIn("Battlefield NPO limit reached.", STRATEGY_CARD)

    def test_loaded_blocked_ids_cannot_overlap_deployed_reinforcements(self):
        normalization = APP.split("function normalizeState(raw)", 1)[1].split("function npoDefinition", 1)[0]
        self.assertIn("!reinforcementIds.includes(id)", normalization)
        self.assertIn("npo.battlefieldState==='reserve'", normalization)

    def test_tomb_world_event_placeholder_is_removed(self):
        self.assertNotIn("No Tomb World event is required.", APP)
        self.assertIn("d.event?.status==='drawn'?strategyEventHtml(d.event):''", STRATEGY_CARD)


if __name__ == "__main__":
    unittest.main()
