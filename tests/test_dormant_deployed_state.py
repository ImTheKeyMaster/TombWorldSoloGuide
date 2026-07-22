#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DormantDeployedStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_activation_requires_deployed_ready_awakened_npo(self):
        active = self.source("function activeNpos()", "function reserveNpos()")
        ready = self.source("function readyNpos()", "function livingPlayerOperativeCount")
        self.assertIn("battlefieldState==='deployed'", active)
        self.assertIn("n.wounds > 0", active)
        self.assertIn("n.ready&&!n.dormant", ready)
        self.assertIn("readyNpos().find", self.source("function nextNpo()", "function showNpoSelection"))

    def test_all_deployed_dormant_message_has_no_activation_button(self):
        status = self.source("function initiativeStatusHtml()", "function missionStrategyPending")
        self.assertIn("deployed.every(npo=>npo.dormant)", status)
        self.assertIn("All deployed NPOs are currently dormant. No NPO activation occurs.", status)
        activation = self.source("function nextStepCard()", "function initiativeStatusHtml")
        self.assertIn("readyNpos().length>0", activation)
        self.assertEqual(activation.count("Activate NPO"), 1)

    def test_awakened_battlefield_uses_normal_activation_without_banner(self):
        activation = self.source("function nextStepCard()", "function initiativeStatusHtml")
        npo_activation = activation.split("if(state.nextSide==='npo'", 1)[1]
        self.assertNotIn("initiativeStatusHtml()", npo_activation)
        self.assertNotIn("summary-box", npo_activation)

    def test_reserve_is_never_dormant_or_eligible(self):
        create = self.source("function createNpo(", "function rollNpo")
        self.assertIn("battlefieldState==='deployed'", create)
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("npo.battlefieldState==='reserve'", normalize)
        self.assertIn("npo.dormant=false", normalize)
        self.assertIn("npo.battlefieldState==='out-of-action'", normalize)
        self.assertNotIn("RESERVE':n.dormant", self.app)
        selection = self.source("function selectStartingNpos", "function generateRoster")
        self.assertIn("npo.dormant=npo.deployed&&state.threat===0", selection)

    def test_target_lists_use_only_active_npos(self):
        player_attack = self.source("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        self.assertIn("activeNpos().filter", player_attack)
        resolution = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        self.assertIn("activeNpos().find", resolution)

    def test_reinforcement_moves_reserve_to_deployed_and_applies_threat_dormancy(self):
        reinforcement = self.source("function processReinforcementStage()", "function reinforcementTriggered")
        self.assertIn("reserveNpos().find", reinforcement)
        self.assertIn("n.battlefieldState='deployed'", reinforcement)
        self.assertIn("n.dormant=state.threat===0", reinforcement)
        self.assertIn("n.ready=!n.dormant", reinforcement)

    def test_save_load_preserves_independent_states(self):
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("importedDormancy.has(npo.id)?importedDormancy.get(npo.id)", normalize)
        npo = self.source("function normalizeNpo(npo)", "function mission()")
        self.assertIn("['reserve','deployed','out-of-action']", npo)
        self.assertIn("dormant:Boolean(npo.dormant)", npo)

    def test_zero_wound_npo_is_always_normalized_out_of_action(self):
        npo = self.source("function normalizeNpo(npo)", "function mission()")
        self.assertLess(npo.index("Number(npo.wounds)<=0"), npo.index("['reserve','deployed','out-of-action']"))
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        out_of_action = normalize.split("npo.battlefieldState==='out-of-action'", 1)[1].split("return;", 1)[0]
        self.assertIn("npo.dormant=false", out_of_action)
        self.assertIn("npo.ready=false", out_of_action)


if __name__ == "__main__":
    unittest.main()
