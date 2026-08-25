"""Cancellation safety assertions updated for v9.1 sequential Player actions."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()

class PlayerActivationCancelTests(unittest.TestCase):
    def test_cancel_only_clears_uncommitted_context(self):
        cancel=APP.split('function cancelCurrentHumanPlayerAction',1)[1].split('function selectHumanPlayerAction',1)[0]
        self.assertIn('activation.pendingAction=null',cancel)
        self.assertIn('state.combatState=null',cancel)
        self.assertNotIn('remainingAp=',cancel)
        self.assertNotIn('resolvedActions=',cancel)

    def test_action_is_not_spent_until_successful_commit(self):
        select=APP.split('function selectHumanPlayerAction',1)[1].split('function commitHumanPlayerAction',1)[0]
        commit=APP.split('function commitHumanPlayerAction',1)[1].split('function confirmEndHumanPlayerActivation',1)[0]
        self.assertNotIn('remainingAp=',select)
        self.assertIn('activation.remainingAp=before-pending.cost',commit)
        self.assertIn('completedActionIds||[]).includes(pending.actionId)',commit)

    def test_release_save_schema_is_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;',PERSISTENCE)

if __name__=='__main__': unittest.main()
