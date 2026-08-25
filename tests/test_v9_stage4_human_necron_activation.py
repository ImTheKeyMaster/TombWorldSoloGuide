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
        self.assertIn("const n=readyNpos().find", pvp)
        self.assertNotIn("const n=candidates.find", pvp)
        self.assertIn("That Necron is no longer Ready", pvp)
        self.assertIn("closeModal();render();showToast", pvp)
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
        self.assertIn("n.battlefieldState!=='deployed'||n.dormant||!n.ready", human)
        self.assertNotIn("!n.deployed", human)
        self.assertIn("state.activeNpoId=null;state.lastActivation=null;save();closeModal();render();return", human)
        self.assertIn("if(n.wounds<=0){completeNpoActivation();return;}", human)
        self.assertIn("recommendedNpoActions", solo)
        self.assertIn("runNpoPrompt", solo)

    def test_self_incapacitated_pvp_necron_completes_before_stale_cleanup(self):
        human = self.section("function continueHumanNecronActivation", "function continueSoloNpoActivation")
        completion = self.section("async function completeNpoActivation", "function applyNpoAttackDamage")
        incapacitated = "if(n.wounds<=0){completeNpoActivation();return;}"
        stale = "if(n.battlefieldState!=='deployed'||n.dormant||!n.ready)"
        self.assertIn(incapacitated, human)
        self.assertIn(stale, human)
        self.assertLess(human.index(incapacitated), human.index(stale))
        for lifecycle_step in ("if(activation?.committed)", "completionHookPending", "state.npoActivated++", "state.activationHistory.unshift", "advanceAfterActivation('npo')", "onNpoActivationCompleted"):
            self.assertIn(lifecycle_step, completion)

    def test_human_catalog_is_separate_from_ai_priority(self):
        catalog = self.section("function supportedHumanNpoActions", "function legalHumanNpoActions")
        legality = self.section("function legalHumanNpoActions", "function filterLegalNpoActions")
        ai = self.section("function recommendedNpoActions", "function attackAvailabilityForMovementIntent")
        for action in ("Reposition", "Dash", "Charge", "Fall Back", "Shoot", "Fight"):
            self.assertIn(action, catalog)
        self.assertIn("definition.actions", catalog)
        self.assertIn("filterLegalNpoActions", legality)
        self.assertIn("rankLegalNpoActions(n,legalNpoActions", ai)

    def test_pvp_special_actions_can_target_activated_living_operatives(self):
        targets = self.section("function eligibleNpoSpecialActionTargets", "function legalHumanNpoActions")
        resolver = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        self.assertIn("isPvpMode()?inPlayLivingPlayerOperativeIds():remainingPlayerOperatives()", targets)
        self.assertIn("eligibleNpoSpecialActionTargets(n,action)", resolver)
        self.assertNotIn("const enemyOptions=remainingPlayerOperatives()", resolver)

    def test_pvp_persistent_special_action_targets_exclude_duplicate_effects(self):
        targets = self.section("function eligibleNpoSpecialActionTargets", "function legalHumanNpoActions")
        self.assertIn("action.id!=='cranial-overload'", targets)
        self.assertIn("item.sourceId===n.id&&item.targetId===target.id&&item.ruleId==='cranial-overload'", targets)
        self.assertIn("action.id!=='overcharge'||!state.npoRuleState.aplModifiers.some", targets)
        self.assertIn("item.sourceId===n.id&&item.targetId===target.id&&item.ruleId==='overcharge'", targets)
        self.assertIn("action.id!=='molecular-breach'||!state.npoRuleState.pendingMovementEffects.some", targets)
        self.assertIn("effect.targetId===target.id&&effect.ruleId==='molecular-breach'", targets)
        self.assertEqual(targets.count("!isPvpMode()||action.id!="), 3)

    def test_special_action_self_targeting_uses_definition_metadata(self):
        targets = self.section("function eligibleNpoSpecialActionTargets", "function legalHumanNpoActions")
        definitions = self.section("const npoDefinitions", "const npoGenerationTable")
        self.assertIn("action.target?.excludeSelf!==true||target.id!==n.id", targets)
        self.assertNotIn("action.id==='nanoscarab-beam'||target.id!==n.id", targets)
        molecular = definitions.split("{id:'molecular-breach'", 1)[1].split("}", 1)[0]
        overcharge = definitions.split("{id:'overcharge'", 1)[1].split("}", 1)[0]
        self.assertNotIn("excludeSelf", molecular)
        self.assertIn("excludeSelf:true", overcharge)
        self.assertIn("keywordsAll:['Canoptek Circle']", molecular)
        self.assertIn("keywordsAll:['Canoptek Circle','Canoptek']", overcharge)

    def test_self_target_change_preserves_other_friendly_and_duplicate_filters(self):
        targets = self.section("function eligibleNpoSpecialActionTargets", "function legalHumanNpoActions")
        self.assertIn("action.target.keywordsAll.every", targets)
        self.assertIn("target.wounds<target.maxWounds", targets)
        self.assertIn("reanimatedTargetIds.includes(target.id)", targets)
        self.assertIn("item.ruleId==='overcharge'", targets)
        self.assertIn("effect.ruleId==='molecular-breach'", targets)

    def test_failed_pvp_persistent_effect_returns_without_committing_ap(self):
        resolver = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        guard_index = resolver.index("if(result?.applied===false)")
        for application in (
            "result.applied=applyMolecularBreach",
            "result.applied=applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'overcharge'",
            "result.applied=applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'cranial-overload'",
        ):
            self.assertLess(resolver.index(application), guard_index)
        failure = resolver.split("result?.applied===false", 1)[1].split("const targetName", 1)[0]
        self.assertIn("if(isPvpMode()){state.lastActivation.pendingAction=null;save();renderHumanNpoActionPicker(n);}", failure)
        self.assertIn("No AP was spent", failure)
        self.assertIn("return", failure)
        self.assertNotIn("finishNpoSpecialAction", failure)
        self.assertNotIn("commitNpoAction", failure)
        self.assertNotIn("log(", failure)
        self.assertNotIn("completedActionIds", failure)
        self.assertNotIn("resolvedActions", failure)

    def test_valid_persistent_effects_still_apply_and_commit_once(self):
        resolver = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        finish = self.section("function finishNpoSpecialAction", "function resolveNpo")
        self.assertEqual(resolver.count("applyMolecularBreach(n.id,target.id)"), 1)
        self.assertEqual(resolver.count("applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'overcharge',amount:1})"), 1)
        self.assertEqual(resolver.count("applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'cranial-overload',amount:-1})"), 1)
        self.assertEqual(resolver.count("finishNpoSpecialAction(n,action,result,decision,answers,questionHistory)"), 1)
        self.assertEqual(finish.count("commitNpoAction("), 1)

    def test_duplicate_effect_guards_do_not_change_solo_resolution(self):
        targets = self.section("function eligibleNpoSpecialActionTargets", "function legalHumanNpoActions")
        resolver = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        self.assertEqual(targets.count("!isPvpMode()||action.id!="), 3)
        self.assertIn("if(result?.applied===false)", resolver)
        failure = resolver.split("if(result?.applied===false)", 1)[1].split("const targetName", 1)[0]
        self.assertIn("button.disabled=false", failure)
        self.assertIn("if(isPvpMode())", failure)

    def test_shared_legality_keeps_ap_repeat_combat_and_movement_rules(self):
        rules = self.section("function filterLegalNpoActions", "function rankLegalNpoActions")
        self.assertIn("cost>remainingAp||completed.has(id)", rules)
        self.assertIn("id==='shoot'&&completed.has('fight')", rules)
        self.assertIn("id==='fight'&&completed.has('shoot')", rules)
        self.assertIn("id==='charge'&&['reposition','dash','fall-back']", rules)
        self.assertIn("id==='fall-back'", rules)
        self.assertIn("oncePerTurningPoint", rules)
        self.assertIn("ordersExcluded", rules)

    def test_picker_is_sequential_accessible_and_shows_progress(self):
        picker = self.section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
        shell = self.section("function renderHumanActivationShell", "function renderHumanPlayerActionPicker")
        self.assertIn("renderHumanActivationShell", picker)
        self.assertIn("disabled:!available", picker)
        self.assertIn("aria-label", shell)
        self.assertIn("AP remaining", shell)
        self.assertIn("Completed Actions", shell)
        self.assertIn("End Activation", shell)
        self.assertNotIn("checkbox", picker)

    def test_activation_header_shows_fixed_or_selected_weapon(self):
        header = self.section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
        self.assertIn("definition.loadoutOptions?.find", header)
        self.assertIn("||npoWeapon(definition,n.weaponId)?.name", header)
        self.assertIn("${loadout?", header)

    def test_activation_tracker_marks_selected_necron_active(self):
        tracker_status = self.section("function npoTrackerStatus", "function npoStatus")
        active_check = "npo.id===state.activeNpoId&&state.lastActivation?.npoId===npo.id&&!state.lastActivation?.committed"
        self.assertIn(active_check, tracker_status)
        self.assertLess(tracker_status.index(active_check), tracker_status.index("npo.ready"))
        self.assertIn("{status:'ACTIVE',className:'active'}", tracker_status)
        self.assertIn(".tracker-operative.active", CSS)

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

    def test_pvp_shoot_and_fight_require_tabletop_target_confirmation(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("id=\"npoTabletopTargetConfirmed\"", wizard)
        self.assertIn("valid target for this shooting attack, including visibility, range, and other applicable targeting requirements", wizard)
        self.assertIn("within control range and is a valid target for this Fight action", wizard)
        guard = "if(isPvpMode()&&!restoredRoll&&!state.lastActivation?.combatDraft?.tabletopTargetConfirmed)return;"
        self.assertIn(guard, wizard)
        self.assertLess(wizard.index(guard), wizard.index("runAutomaticCombatRolls({"))

    def test_pvp_target_confirmation_gates_dice_ap_damage_and_completion(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("tabletopTargetConfirmed:event.currentTarget.checked", wizard)
        self.assertIn("screen.continueButton.disabled=!event.currentTarget.checked||!profile", wizard)
        start = wizard.split("const startAutomaticCombat", 1)[1]
        guard = "if(isPvpMode()&&!restoredRoll&&!state.lastActivation?.combatDraft?.tabletopTargetConfirmed)return;"
        self.assertLess(start.index(guard), start.index("combatTimer=runAutomaticCombatRolls({"))

    def test_confirmed_pvp_attacks_use_existing_stage3_dice_flow(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        combat = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("attackType==='shoot'", wizard)
        self.assertIn("attackType==='melee'", wizard)
        self.assertIn("runAutomaticCombatRolls({", wizard)
        self.assertIn("await requestAttackDiceForProfile", combat)
        self.assertIn("await requestDefenseDice", combat)

    def test_cancel_before_tabletop_confirmation_spends_no_ap(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        cancel = wizard.split("const cancel=()=>", 1)[1].split("let combatTimer", 1)[0]
        self.assertIn("combatDraft:null", cancel)
        self.assertIn("if(onCancel)onCancel()", cancel)
        self.assertNotIn("commitNpoAction", cancel)
        self.assertNotIn("applyNpoAttackDamage", cancel)

    def test_solo_attack_target_and_dice_flow_remain_automatic(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("else if(availableProfiles.length===1&&!resumeGuided)startAutomaticCombat()", wizard)
        self.assertIn("else if(locked&&!resumeGuided)startAutomaticCombat()", wizard)
        result = self.section("function renderNpoDecisionResult", "async function completeNpoActivation")
        self.assertIn("!isPvpMode()&&!targetConfirmed&&eligibleTargetIds.length===1", result)
        self.assertIn("!isPvpMode()&&decision.target.length", result)

    def test_pvp_attack_surfaces_use_presentation_terminology(self):
        result = self.section("function showNpoTargetRecovery", "async function completeNpoActivation")
        combat = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("opponentSingularLabel()", result)
        self.assertIn("playerSideLabel()", result)
        self.assertIn("playerSideLabel()", combat)
        self.assertNotIn("Return to NPO Activation", result)
        self.assertNotIn("That Player operative is no longer", result)

    def test_end_with_ap_requires_deliberate_confirmation(self):
        ending = self.section("function confirmEndHumanNpoActivation", "function renderNpoGuideFooter")
        self.assertIn("${remaining} AP remain", ending)
        self.assertIn("This operative has not performed any actions.", ending)
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
