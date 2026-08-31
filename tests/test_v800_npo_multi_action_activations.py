from versioning import CURRENT_APP_VERSION
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
README = (ROOT / 'README.md').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()


class ActivationModel:
    COSTS = {'reposition': 1, 'dash': 1, 'charge': 1, 'shoot': 1, 'fight': 1, 'fall-back': 2}

    def __init__(self, apl):
        self.starting = apl
        self.remaining = apl
        self.completed = []
        self.resolved = []
        self.declined = set()
        self.pass_number = 1
        self.committed = False

    def decline(self, action):
        self.declined.add(action)

    def commit(self, action, cost=None):
        cost = self.COSTS[action] if cost is None else cost
        if self.committed or action in self.completed or cost > self.remaining:
            return False
        before = self.remaining
        self.remaining -= cost
        self.completed.append(action)
        self.resolved.append((action, before, self.remaining))
        self.pass_number += 1
        self.declined.clear()
        return True


class V800NpoMultiActionActivationTests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(f'function {start}(', 1)[1].split(f'function {end}(', 1)[0]

    def test_01_effective_apl_is_starting_budget(self):
        source = self.source('beginNpoActivation', 'showNpoSelection')
        self.assertIn('startingAp:apl,remainingAp:apl', source)

    def test_02_reposition_cost(self): self.assertEqual(ActivationModel.COSTS['reposition'], 1)
    def test_03_dash_cost(self): self.assertEqual(ActivationModel.COSTS['dash'], 1)
    def test_04_charge_cost(self): self.assertEqual(ActivationModel.COSTS['charge'], 1)
    def test_05_shoot_cost(self): self.assertEqual(ActivationModel.COSTS['shoot'], 1)
    def test_06_fight_cost(self): self.assertEqual(ActivationModel.COSTS['fight'], 1)
    def test_07_fall_back_cost(self):
        self.assertEqual(ActivationModel.COSTS['fall-back'], 2)
        self.assertIn("'fall-back':2", APP)

    def test_08_special_action_defined_costs(self):
        for action in ('geomantic-disturbance', 'canoptek-control', 'molecular-breach', 'overcharge', 'cranial-overload', 'nanoscarab-beam'):
            self.assertRegex(APP, rf"id:'{action}'.*?ap:1")

    def test_09_ap_never_negative(self):
        model = ActivationModel(1)
        self.assertFalse(model.commit('fall-back'))
        self.assertEqual(model.remaining, 1)
        self.assertIn('Math.max(0,before-apCost)', APP)

    def test_10_completed_action_cannot_repeat(self):
        model = ActivationModel(3); self.assertTrue(model.commit('shoot')); self.assertFalse(model.commit('shoot'))

    def test_11_decline_reconsidered_after_context_change(self):
        model = ActivationModel(2); model.decline('shoot'); model.commit('reposition'); self.assertNotIn('shoot', model.declined)

    def test_12_decline_not_reasked_in_same_pass(self):
        source = self.source('npoActionQuestion', 'renderCompletedNpoQuestions')
        self.assertIn('declinedActionIds', source)

    def test_13_reposition_then_shoot(self):
        model = ActivationModel(2); self.assertTrue(model.commit('reposition')); self.assertTrue(model.commit('shoot')); self.assertEqual(model.remaining, 0)

    def test_14_dash_then_shoot(self):
        model = ActivationModel(2); self.assertTrue(model.commit('dash')); self.assertTrue(model.commit('shoot'))

    def test_15_charge_then_fight(self):
        model = ActivationModel(2); self.assertTrue(model.commit('charge')); self.assertTrue(model.commit('fight'))

    def test_16_attack_then_nonconflicting_action(self):
        model = ActivationModel(2); self.assertTrue(model.commit('shoot')); self.assertTrue(model.commit('dash'))

    def test_17_shoot_and_fight_are_not_mutually_exclusive(self):
        self.assertNotIn("id==='shoot'&&completed.has('fight')", APP)
        self.assertNotIn("id==='fight'&&completed.has('shoot')", APP)
        self.assertIn("cost>remainingAp||completed.has(id)", APP)

    def test_18_movement_yes_is_affirmative(self):
        self.assertIn('to get a clear shot. If that is not possible, move it to help the mission.', APP)

    def test_19_contradictory_wording_absent(self):
        self.assertNotIn('cannot move to a valid shooting position', APP.lower())

    def test_20_standard_actions_continue(self):
        self.assertIn("canContinue?'Continue Activation':'Complete Activation'", APP)

    def test_21_special_actions_use_common_commit(self):
        source = self.source('finishNpoSpecialAction', 'resolveNpo')
        self.assertIn('commitNpoAction({', source)

    def test_22_attack_callback_commits_action(self):
        renderer = self.source('renderNpoDecisionResult', 'completeNpoActivation')
        self.assertIn('commitNpoAction({actionId:pending.id', renderer)
        self.assertNotIn('completeNpoActivation(summary)', renderer)

    def test_23_unused_ap_can_complete(self):
        self.assertIn('No useful actions remain.', APP)
        self.assertIn('AP remain${remaining===1', APP)

    def test_24_three_ap_supports_three_actions(self):
        model = ActivationModel(3)
        for action in ('reposition', 'dash', 'shoot'): self.assertTrue(model.commit(action))
        self.assertEqual((model.remaining, len(model.resolved)), (0, 3))

    def test_25_activation_counters_only_in_final_commit(self):
        commit = self.source('completeNpoActivation', 'applyNpoAttackDamage')
        self.assertEqual(commit.count('state.npoActivated++'), 1)
        self.assertEqual(commit.count('state.activationNumber++'), 1)

    def test_26_mission_hooks_once(self):
        self.assertEqual(self.source('beginNpoActivation', 'showNpoSelection').count("notifyMissionActivationStarted('npo'"), 1)
        completion = self.source('completeNpoActivation', 'applyNpoAttackDamage')
        self.assertEqual(completion.count("executeMissionLifecycleHook('onNpoActivationCompleted'"), 2)
        self.assertIn('completionHookPending', completion)

    def test_27_threat_uses_complete_sequence_flag(self):
        commit = self.source('completeNpoActivation', 'applyNpoAttackDamage')
        self.assertIn('state.lastActivation.attackPerformed', commit)
        self.assertEqual(commit.count('setThreat('), 1)

    def test_28_history_is_chronological(self):
        source = self.source('commitNpoAction', 'renderNpoActionResult')
        self.assertIn('activation.resolvedActions=[...(activation.resolvedActions||[]),record]', source)

    def test_29_reload_preserves_remaining_ap(self):
        self.assertIn('remainingAp:remaining', APP)
    def test_30_reload_preserves_movement(self):
        self.assertIn('completedActionIds:Array.isArray(merged.lastActivation.completedActionIds)', APP)
    def test_31_reload_preserves_attack_results(self):
        self.assertIn('resolvedActions:Array.isArray(merged.lastActivation.resolvedActions)', APP)
        self.assertIn('combatDraft', APP)
    def test_32_reload_does_not_duplicate_damage(self):
        self.assertIn('resolutionCommitted||!pending||!canCommitNpoAction', APP)
    def test_33_journal_is_committed_once(self):
        source = self.source('commitNpoAction', 'renderNpoActionResult')
        self.assertEqual(source.count('log('), 1)
    def test_34_rapid_taps_are_idempotent(self):
        source = self.source('canCommitNpoAction', 'commitNpoAction')
        self.assertIn('pending?.id===actionId', source)
        self.assertIn('pending.decisionPass===activation.decisionPass', source)
    def test_35_dead_targets_excluded(self):
        self.assertIn('inPlayLivingPlayerOperativeIds()', APP)
        self.assertIn('state.npoAttackTargetId=null', self.source('commitNpoAction', 'renderNpoActionResult'))
    def test_36_aggressive_defence_preserved(self): self.assertIn("id:'aggressive-defence'", APP)
    def test_37_event_effects_preserved(self): self.assertIn("tombWorldEventActive('my-will-be-done')", APP)
    def test_38_deadly_encounters_preserved(self): self.assertIn('DeadlyEncounters', APP)
    def test_39_player_activations_preserved(self): self.assertIn('function completePlayerActivation(', APP)
    def test_40_version_800_everywhere(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP); self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'V{CURRENT_APP_VERSION}', INDEX); self.assertTrue(README.startswith(f'# Tomb World Battle Guide v{CURRENT_APP_VERSION}'))
    def test_41_supported_npo_profiles_unchanged_and_present(self):
        for name in ('Necron Warrior', 'Canoptek Tomb Crawler', 'Geomancer', 'Canoptek Macrocyte Warrior', 'Canoptek Macrocyte Accelerator', 'Canoptek Macrocyte Reanimator', 'Canoptek Scarab Swarm'):
            self.assertIn(f"'{name}': {{", APP)

    def test_stale_controls_cannot_apply_side_effects_before_commit_validation(self):
        movement = self.source('resolveNpoAction', 'initiativeSummary')
        self.assertLess(movement.index('canCommitNpoAction(pendingAction.id'), movement.index('consumeMolecularBreach(n.id'))
        combat = self.source('showNpoAttackWizard', 'spinnerField')
        self.assertLess(combat.index('canCommitNpoAction(pending.id'), combat.index('applyNpoAttackDamage(n,target,summary)'))

    def test_incapacitation_can_finish_an_active_activation(self):
        continuation = self.source('continueNpoActivation', 'canCommitNpoAction')
        self.assertIn('n.wounds<=0', continuation)
        completion = self.source('completeNpoActivation', 'applyNpoAttackDamage')
        self.assertNotIn('if(!n||!n.ready)return', completion)

    def test_final_activation_commit_guard_is_set_before_side_effects(self):
        completion = self.source('completeNpoActivation', 'applyNpoAttackDamage')
        guard = 'state.lastActivation.committed=true;state.lastActivation.completed=true'
        self.assertLess(completion.index(guard), completion.index('setThreat('))
        self.assertLess(completion.index(guard), completion.index('state.npoActivated++'))


if __name__ == '__main__':
    unittest.main()
