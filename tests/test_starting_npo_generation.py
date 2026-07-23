#!/usr/bin/env python3
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StartingNpoGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def deployment_source(self):
        setup_content = self.app.split("function setupContent(stepId)", 1)[1]
        return setup_content.split("if(stepId==='deploy'){", 1)[1].split("\n    const m=mission();", 1)[0]

    def test_two_d3_roll_is_stored_once_with_official_calculation(self):
        roll = self.source("function startingNpoRoll()", "function generateRoster")
        self.assertIn("[rollD3(),rollD3()]", roll)
        self.assertIn("dice[0]+dice[1]+3", roll)
        self.assertIn("calculation", roll)
        ensure = self.source("function ensureStartingNpoGeneration()", "function render()")
        self.assertIn("if(state.startingNpoGeneration)return false", ensure)
        self.assertIn("save()", ensure)

    def test_shared_dice_animation_settles_on_deployment_screen(self):
        presentation = self.deployment_source()
        self.assertIn("rollingDieHtml()", presentation)
        self.assertIn("animated-roll", presentation)
        self.assertIn("startingNpoResult", presentation)
        flow = self.source("function runStartingNpoGeneration()", "function renderGame()")
        self.assertIn("settleAnimatedDice", flow)
        self.assertIn("dice:generation.dice.map(value=>({value,kind:'hit'}))", flow)
        self.assertNotIn("state.setupStep", flow)
        self.assertIn("if(generation.animationShown)return", flow)

    def test_redundant_generation_step_is_removed_from_setup_progress(self):
        steps = self.source("function activeSetupSteps()", "function currentSetupStepId()")
        self.assertNotIn("'npoRoster'", steps)
        self.assertIn("'playerRoster','deploy','ready'", steps)
        render = self.source("function renderSetup()", "function missionSetupChecks")
        self.assertIn("if(stepId==='deploy')ensureStartingNpoGeneration()", render)

    def test_deployment_is_capped_without_changing_mission_roll(self):
        roll = self.source("function startingNpoRoll()", "function generateRoster")
        self.assertIn("deploymentCount:Math.min(missionRoll,MAX_NPOS)", roll)
        roster = self.source("function generateRoster(generation)", "function ensureStartingNpoGeneration")
        self.assertIn("count=MAX_NPOS", roster)
        self.assertIn("selectStartingNpos(generation)", roster)
        presentation = self.deployment_source()
        self.assertIn("Deploy the ${generation.deploymentCount} selected starting NPOs.", presentation)
        self.assertNotIn("available NPOs", presentation)
        self.assertIn("${generation.missionRoll} Starting NPOs", presentation)
        self.assertIn('class="deployment-roster"', presentation)
        self.assertIn("Deploy ${escapeHtml(playerTeamData?.teamName", presentation)
        self.assertNotIn("Necron Kill Team deployed", presentation)
        self.assertIn("placementChecks.filter(check=>check.id!=='starting-npos')", presentation)
        self.assertNotIn("error", presentation.lower())

    def test_deployment_checklist_is_preserved_for_non_empty_starting_rosters(self):
        presentation = self.deployment_source()
        self.assertIn("hasStartingNpos=generation.deployedNpoIds.length>0", presentation)
        self.assertIn("hasStartingNpos&&deploymentCheck", presentation)
        self.assertIn("hasStartingNpos?placementChecks:otherPlacementChecks", presentation)
        self.assertIn("hasStartingNpos?`<div class=\"setup-bulk-row\"", presentation)
        for mission_file in (
            "01-shifting-labyrinth.json", "02-demolition-protocol.json",
            "03-recover-transponder.json", "04-destroy-sarcophagus.json",
        ):
            mission = json.loads((ROOT / "Missions" / mission_file).read_text())
            self.assertNotEqual(mission["startingNpos"]["formula"], "0")
            self.assertIn("starting-npos", [check["id"] for check in mission["setupChecks"] if check["stage"] == "deploy"])

    def test_zero_starting_roster_has_explanation_without_npo_confirmation(self):
        presentation = self.deployment_source()
        self.assertIn('<strong>None</strong>', presentation)
        self.assertIn('This mission begins with no NPOs deployed.', presentation)
        self.assertIn('Enemy operatives will enter play later according to the mission rules.', presentation)
        self.assertIn("const deploymentRow=hasStartingNpos&&deploymentCheck", presentation)
        self.assertIn("requiredPlacementChecks.every(check=>state.setupChecks[check.id])", presentation)
        mission = json.loads((ROOT / "Missions" / "05-scout-sub-crypt.json").read_text())
        self.assertEqual(mission["startingNpos"]["formula"], "0")

    def test_empty_starting_roster_automatically_satisfies_deployment_requirement(self):
        render_setup = self.source("function renderSetup()", "function missionSetupChecks")
        self.assertIn("satisfyEmptyStartingNpoDeployment()", render_setup)
        satisfaction = self.source("function satisfyEmptyStartingNpoDeployment()", "function setupChecklistHtml")
        self.assertIn("generation.deployedNpoIds.length", satisfaction)
        self.assertIn("check.id==='starting-npos'", satisfaction)
        self.assertIn("state.setupChecks[deploymentCheck.id]=true", satisfaction)
        self.assertIn("save()", satisfaction)

    def test_persistence_prevents_reroll_on_rerender(self):
        initial = self.source("const initialState", "let state")
        self.assertIn("startingNpoGeneration:null", initial)
        normalized = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("raw?.startingNpoGeneration", normalized)
        flow = self.source("function runStartingNpoGeneration()", "function renderGame()")
        self.assertIn("generation.animationShown=true", flow)
        self.assertIn("if(generation.animationShown)return", flow)
        self.assertNotIn("startingNpoRoll()", flow)

    def test_legacy_setup_step_migration_is_persisted_once(self):
        initialization = self.source("const loadedState = load()", "let lastRenderedStepKey")
        self.assertIn("state.version===APP_VERSION)save()", initialization)
        normalized = self.source("function normalizeState(raw)", "function npoDefinition")
        migration = normalized.split("if(raw.version==='5.6.0'", 1)[1].split("merged.playerTeamId", 1)[0]
        self.assertIn("merged.setupStep=Math.max(0,Number(merged.setupStep||0)-1)", migration)
        self.assertIn("merged.version=APP_VERSION", migration)

    def test_legacy_setup_save_uses_existing_roster_without_rerolling(self):
        restored = self.source("function restoredStartingNpoGeneration()", "function generateRoster")
        self.assertIn("missionRoll=state.roster.length", restored)
        self.assertIn("animationShown:true", restored)
        ensure = self.source("function ensureStartingNpoGeneration()", "function render()")
        self.assertIn("if(state.roster.length)", ensure)
        self.assertIn("restoredStartingNpoGeneration()", ensure)
        self.assertLess(ensure.index("if(state.roster.length)"), ensure.index("startingNpoRoll()"))

    def test_generation_tables_and_reinforcements_are_unchanged(self):
        self.assertRegex(self.app, r"function rollNpo\(\)\{")
        self.assertRegex(self.app, r"function randomReinforcement\(\)\{return rollNpo\(\);\}")
        self.assertEqual(self.app.count("function rollNpo()"), 1)

    def test_selection_partitions_every_available_npo_once(self):
        selection = self.source("function selectStartingNpos(generation)", "function generateRoster")
        self.assertIn("assignedIds.size===available.length", selection)
        self.assertIn("return false", selection)
        self.assertIn("Math.min(generation.missionRoll,available.length)", selection)
        self.assertIn("slice(0,generation.deploymentCount)", selection)
        self.assertIn("slice(generation.deploymentCount)", selection)
        self.assertIn("battlefieldState=deployedIds.has(npo.id)?'deployed':'reserve'", selection)

    def test_battlefield_eligibility_excludes_reserve_and_out_of_action(self):
        active = self.source("function activeNpos()", "function reserveNpos()")
        self.assertIn("n.battlefieldState==='deployed'", active)
        self.assertIn("n.wounds > 0", active)
        self.assertGreaterEqual(self.app.count("activeNpos().filter"), 5)

    def test_reinforcements_reuse_reserve_without_duplication(self):
        reinforcement = self.source("function processReinforcementStage()", "function reinforcementTriggered")
        self.assertIn("reserveNpos().find", reinforcement)
        self.assertIn("if(n)", reinforcement)
        self.assertIn("else{", reinforcement)
        placement = self.source("function confirmReinforcementPlacement", "function rollInitiative")
        self.assertIn("npo.battlefieldState='deployed'", placement)
        self.assertNotIn("reserveIds.add(npo.id)", placement)

    def test_saved_identifiers_and_legacy_states_are_normalized(self):
        normalized = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("deployedNpoIds=normalizeIdList", normalized)
        self.assertIn("reserveNpoIds=normalizeIdList", normalized)
        npo = self.source("function normalizeNpo(npo)", "function mission()")
        self.assertIn("['reserve','deployed','out-of-action']", npo)
        self.assertRegex(npo, r"Number\(npo\.wounds\)<=0\s*\? 'out-of-action'")

    def test_legacy_in_progress_games_preserve_prior_active_roster_behavior(self):
        normalized = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("if(Number(raw.turningPoint)>0)", normalized)
        self.assertIn("!explicitStates.has(npo.id)", normalized)
        self.assertIn("npo.battlefieldState='deployed'", normalized)

    def test_combat_resolution_revalidates_deployed_target(self):
        combat = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        self.assertIn("activeNpos().find(n=>n.id===targetId)", combat)
        self.assertNotIn("state.roster.find(n=>n.id===targetId)", combat)


if __name__ == "__main__":
    unittest.main()
