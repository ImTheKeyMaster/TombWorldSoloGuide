#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationPr4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()

    def function_source(self, name, next_name):
        return self.app.split(f'function {name}(', 1)[1].split(f'function {next_name}(', 1)[0]

    def test_every_npo_uses_its_printed_behavior_order(self):
        expected = {
            'Canoptek Scarab Swarm': ['Fight', 'Charge the closest player operative via the shortest possible route', 'Reposition towards the closest player operative, to cover if possible', 'Dash towards the closest player operative, to cover if possible'],
            'Necron Warrior': ['Fall Back', 'Shoot', 'Reposition to gain a valid unobscured target or better win the mission', 'Dash to gain a valid unobscured target or better win the mission', 'Fight'],
            'Canoptek Tomb Crawler': ['Fight', 'Shoot', 'Reposition to gain a valid unobscured target or better win the mission', 'Dash to gain a valid unobscured target or better win the mission'],
            'Canoptek Macrocyte': ['Fight', 'Shoot', 'Reposition to gain a valid unobscured target or better win the mission', 'Dash to gain a valid unobscured target or better win the mission'],
        }
        for operative, actions in expected.items():
            definition = self.app.split(f"'{operative}': {{", 1)[1].split("\n    },", 1)[0]
            encoded = ','.join(repr(action) for action in actions)
            self.assertIn(f'actions:[{encoded}]', definition)

    def test_question_flow_stops_at_first_legal_action(self):
        source = self.function_source('runNpoPrompt', 'chooseNpoDecision')
        self.assertIn('if(answer)resolveNpo', source)
        self.assertIn('else runNpoPrompt(n,index+1', source)
        self.assertNotIn('objective', source)
        self.assertNotIn('wounded', source)
        self.assertNotIn('clustered', source)

    def test_active_question_icon_uses_the_printed_action(self):
        question = self.function_source('npoActionQuestion', 'npoIcon')
        self.assertIn('action,title:', question)
        renderer = self.function_source('renderActiveNpoQuestion', 'runNpoPrompt')
        self.assertIn("npoQuestionIcons[q.action.split(' ')[0]]", renderer)
        self.assertNotIn('npoQuestionIcons[q.key]', renderer)

    def test_activation_threat_principle_is_printed_in_order(self):
        source = self.function_source('showNpoSelection', 'remainingPlayerOperatives')
        criteria = ['has an ability, or is a threat, to Shoot or Fight', 'is not in cover', 'is closest to a Player operative']
        self.assertEqual(sorted(criteria, key=source.index), criteria)
        self.assertIn('determine one at random', source)
        self.assertNotIn('compatibilityBehavior', source)

    def test_target_priorities_are_action_specific(self):
        source = self.function_source('chooseNpoDecision', 'resolveNpo')
        self.assertIn("action.startsWith('Fight')", source)
        self.assertIn("action.startsWith('Shoot')", source)
        self.assertIn('most likely to incapacitate', source)
        self.assertIn('greatest mission impact', source)
        self.assertIn('not obscured, not in cover, closest, then Ready', source)
        self.assertIn('randomize any remaining tie', source)
        self.assertNotIn('largest cluster', source)

    def test_recommendation_does_not_commit_activation(self):
        staging = self.function_source('resolveNpo', 'initiativeSummary')
        for mutation in ('n.ready=false', 'state.npoActivated++', 'state.activationNumber++', 'advanceAfterActivation', 'setThreat('):
            self.assertNotIn(mutation, staging)
        commit = self.function_source('completeNpoActivation', 'applyNpoAttackDamage')
        for mutation in ('n.ready=false', 'state.npoActivated++', 'state.activationNumber++', 'advanceAfterActivation', 'setThreat('):
            self.assertIn(mutation, commit)
        self.assertIn('if(state.lastActivation?.committed)return', commit)

    def test_version_and_cache_identifiers_are_synchronized(self):
        expected = '5.7.2'
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / 'service-worker.js').read_text())
        index = (ROOT / 'index.html').read_text()
        self.assertIn(f'styles.css?v={expected}', index)
        self.assertIn(f'app.js?v={expected}', index)
        self.assertIn(f'V{expected}', index)
        self.assertTrue((ROOT / 'README.md').read_text().startswith(f'# Tomb World Solo Guide v{expected}'))


if __name__ == '__main__':
    unittest.main()
