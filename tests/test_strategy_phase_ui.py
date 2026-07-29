import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
STRATEGY_CARD = APP.split("function strategyActionsStepHtml", 1)[1].split("function strategyEventHtml", 1)[0]
REINFORCEMENTS = APP.split("function processReinforcementStage()", 1)[1].split("function reinforcementTriggered", 1)[0]


class StrategyPhaseUiTests(unittest.TestCase):
    def test_strategy_stat_tooltips_are_hidden_on_mobile(self):
        self.assertIn("showStatTooltips=!window.matchMedia('(max-width:600px)').matches", STRATEGY_CARD)
        self.assertIn("tooltipAttrs=text=>showStatTooltips?", STRATEGY_CARD)
        self.assertIn("infoDot=showStatTooltips?", STRATEGY_CARD)
        self.assertIn(
            "@media(max-width:600px){.strategy-stat-grid .tooltip-stat{cursor:default}"
            ".strategy-stat-grid .tooltip-stat::after,.strategy-stat-grid .info-dot{display:none}}",
            STYLES,
        )

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
        self.assertIn('No reinforcements were generated this Turning Point.', STRATEGY_CARD)
        self.assertNotIn("No reinforcements arrive.", APP)

    def test_reserve_npos_are_selected_and_deployed_without_duplication(self):
        self.assertIn("reserveNpos().find", REINFORCEMENTS)
        self.assertIn("n.battlefieldState='reserve';n.deployed=false;n.dormant=false;n.ready=false", REINFORCEMENTS)
        placement = APP.split("function confirmReinforcementPlacement", 1)[1].split("function rollInitiative", 1)[0]
        self.assertIn("npo.battlefieldState=npo.deployed?'deployed':'reserve'", placement)
        self.assertIn("function activeNpos(){ return state.roster.filter(n => n.battlefieldState==='deployed'", APP)
        self.assertIn("filter(id=>id!==n.id)", REINFORCEMENTS)
        deploy_branch = REINFORCEMENTS.split("continue;", 1)[1]
        self.assertLess(deploy_branch.index("if(n){"), deploy_branch.index("createNpo(type"))

    def test_blocked_reinforcements_do_not_allocate_phantom_models(self):
        self.assertIn("blocked=requested-actual", REINFORCEMENTS)
        self.assertIn("if(!rr){blocked++;continue;}", REINFORCEMENTS)
        self.assertNotIn("if(i>=actual)", REINFORCEMENTS)
        self.assertNotIn("blockedOperativeIds.push(n.id)", REINFORCEMENTS)
        self.assertIn("no legal physical model remains.", STRATEGY_CARD)

    def test_loaded_blocked_ids_cannot_overlap_deployed_reinforcements(self):
        normalization = APP.split("function normalizeState(raw)", 1)[1].split("function npoDefinition", 1)[0]
        self.assertIn("!reinforcementIds.includes(id)", normalization)
        self.assertIn("npo.battlefieldState==='reserve'", normalization)

    def test_tomb_world_event_placeholder_is_removed(self):
        self.assertIn("No Tomb World event is required during this Strategy Phase.", APP)
        self.assertIn("displayedEvents.map(event=>strategyEventHtml(event,activeEffects)).join('')", STRATEGY_CARD)


if __name__ == "__main__":
    unittest.main()
