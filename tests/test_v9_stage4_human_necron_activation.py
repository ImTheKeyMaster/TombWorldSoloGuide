#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


class Stage4HumanNecronActivationTests(unittest.TestCase):
    def section(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_selection_dispatches_without_threat_principle_in_pvp(self):
        selection = self.section("function showNpoSelection", "function remainingPlayerOperatives")
        pvp = selection.split("if(isPvpMode())", 1)[1].split("return;", 1)[0]
        self.assertIn("Choose a Ready Necron to activate", pvp)
        self.assertNotIn("Threat Principle", pvp)
        self.assertIn("n.ready&&n.deployed&&n.wounds>0", pvp)
        self.assertIn("Use the Threat Principle", selection)
        self.assertIn("if(candidates.length===1)", selection)

    def test_one_top_level_dispatch_bypasses_solo_ai(self):
        dispatcher = self.section("function continueNpoActivation", "function continueHumanNecronActivation")
        human = self.section("function continueHumanNecronActivation", "function continueSoloNpoActivation")
        solo = self.section("function continueSoloNpoActivation", "function normalizeUnknownAttackMovement")
        self.assertIn("if(isPvpMode())", dispatcher)
        self.assertIn("continueHumanNecronActivation", dispatcher)
        for ai_function in ("recommendedNpoActions", "runNpoPrompt", "chooseNpoDecision", "continueGuaranteedNpoFollowUp"):
            self.assertNotIn(ai_function, human)
        self.assertIn("recommendedNpoActions", solo)
        self.assertIn("runNpoPrompt", solo)

    def test_human_catalog_is_separate_from_ai_priority(self):
        catalog = self.section("function supportedHumanNpoActions", "function legalHumanNpoActions")
        legality = self.section("function legalHumanNpoActions", "function filterLegalNpoActions")
        ai = self.section("function recommendedNpoActions", "function attackAvailabilityForMovementIntent")
        for action in ("Reposition", "Dash", "Charge", "Fall Back", "Shoot", "Fight"):
            self.assertIn(action, catalog)
        self.assertIn("definition.actions", catalog)
        self.assertIn("filterLegalNpoActions", legality)
        self.assertIn("rankLegalNpoActions(n,legalNpoActions", ai)

    def test_shared_legality_keeps_ap_repeat_combat_and_movement_rules(self):
        rules = self.section("function filterLegalNpoActions", "function rankLegalNpoActions")
        self.assertIn("cost>remainingAp||completed.has(id)", rules)
        self.assertIn("id==='shoot'&&completed.has('fight')", rules)
        self.assertIn("id==='fight'&&completed.has('shoot')", rules)
        self.assertIn("id==='charge'", rules)
        self.assertIn("id==='fall-back'", rules)
        self.assertIn("oncePerTurningPoint", rules)
        self.assertIn("ordersExcluded", rules)

    def test_picker_is_sequential_accessible_and_shows_progress(self):
        picker = self.section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
        self.assertIn("data-human-npo-action", picker)
        self.assertIn("disabled", picker)
        self.assertIn("aria-label", picker)
        self.assertIn("AP remaining", self.section("function renderNpoActivationHeader", "function renderNpoGuideFooter"))
        self.assertIn("Completed actions", picker)
        self.assertIn("End Activation", picker)
        self.assertNotIn("checkbox", picker)

    def test_movement_commits_only_from_confirmation_and_never_forces_follow_up(self):
        resolver = self.section("function resolveNpoAction", "function initiativeSummary")
        before_handler, handler = resolver.split("$('#confirmNpoMovement').onclick", 1)
        self.assertNotIn("commitNpoAction", before_handler)
        self.assertIn("commitNpoAction", handler)
        self.assertIn("pendingAction.id==='dash'", handler)
        self.assertIn("&&!isPvpMode()", handler)
        human_select = self.section("function selectHumanNpoAction", "function confirmEndHumanNpoActivation")
        self.assertIn("pendingFollowUpAction:null", human_select)
        self.assertIn("movementIntent:null", human_select)

    def test_human_target_selection_has_no_ai_priority(self):
        result = self.section("function renderNpoDecisionResult", "async function completeNpoActivation")
        self.assertIn("Choose an eligible target", result)
        self.assertIn("!isPvpMode()&&decision.target.length", result)
        self.assertIn("isPvpMode()?'':`<small>TARGET PRIORITY", result)
        self.assertIn("confirmNpoAttackTarget", result)
        decision = self.section("function humanNpoDecision", "function renderHumanNpoActionPicker")
        self.assertIn("target:[]", decision)
        self.assertNotIn("Most likely", decision)

    def test_end_with_ap_requires_deliberate_confirmation(self):
        ending = self.section("function confirmEndHumanNpoActivation", "function renderNpoGuideFooter")
        self.assertIn("still has ${remaining} AP remaining", ending)
        self.assertIn("Continue Activation", ending)
        self.assertIn("End Activation", ending)
        self.assertIn("completeNpoActivation", ending)

    def test_resume_reuses_persisted_activation_and_shared_commit_engine(self):
        human = self.section("function continueHumanNecronActivation", "function continueSoloNpoActivation")
        commit = self.section("function commitNpoAction", "function renderNpoActionResult")
        self.assertIn("activation.pendingAction", human)
        self.assertIn("activation.awaitingActionResult", human)
        self.assertIn("activation.remainingAp", human)
        self.assertIn("activation.completedActionIds", commit)
        self.assertIn("activation.resolvedActions", commit)
        self.assertIn("save()", commit)

    def test_mobile_action_buttons_stack_and_wrap(self):
        self.assertIn(".human-npo-action-list", CSS)
        self.assertIn("grid-template-columns:1fr", CSS)
        self.assertIn("white-space:normal", CSS)
        self.assertIn("overflow-wrap:anywhere", CSS)


if __name__ == "__main__":
    unittest.main()
