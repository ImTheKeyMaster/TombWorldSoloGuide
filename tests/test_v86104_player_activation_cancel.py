"""Cancellation safety coverage adapted to v9.1 sequential Player actions."""
from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()


def section(start, end):
    return APP.split(start,1)[1].split(end,1)[0]


class PlayerActivationCancelTests(unittest.TestCase):
    def test_cancel_abandons_only_unconfirmed_action_context(self):
        cancel=section('function cancelCurrentHumanPlayerAction','function selectHumanPlayerAction')
        self.assertIn('activation.pendingAction=null',cancel)
        self.assertIn('state.combatState=null',cancel)
        self.assertIn('state.missionActionContext=null',cancel)
        self.assertIn('state.weaponRuleResolution=null',cancel)

    def test_cancel_does_not_roll_back_committed_gameplay(self):
        cancel=section('function cancelCurrentHumanPlayerAction','function selectHumanPlayerAction')
        for mutation in ('remainingAp=','resolvedActions=','completedActionIds=','playerWounds=','setThreat('):
            self.assertNotIn(mutation,cancel)

    def test_current_action_has_an_explicit_cancel_control(self):
        select=section('function selectHumanPlayerAction','function commitHumanPlayerAction')
        self.assertIn('id="cancelHumanPlayerAction"',select)
        self.assertIn("$('#cancelHumanPlayerAction').onclick=cancelCurrentHumanPlayerAction",select)

    def test_action_is_not_spent_during_selection(self):
        select=section('function selectHumanPlayerAction','function commitHumanPlayerAction')
        self.assertIn('activation.pendingAction=',select)
        self.assertNotIn('remainingAp=',select)
        self.assertNotIn('resolvedActions=',select)

    def test_successful_commit_spends_ap_once(self):
        commit=section('function commitHumanPlayerAction','function confirmEndHumanPlayerActivation')
        self.assertIn('completedActionIds||[]).includes(pending.actionId)',commit)
        self.assertIn('activation.remainingAp=before-pending.cost',commit)
        self.assertIn('activation.pendingAction=null',commit)

    def test_complete_activation_requires_a_locked_operative(self):
        completion=section('async function completeHumanPlayerActivation','const PLAYER_ACTION_COSTS')
        self.assertIn("state.lastActivation?.side==='player'",completion)
        self.assertIn('if(!activation)return',completion)

    def test_release_version_and_save_schema(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';",APP)
        self.assertIn('const SAVE_VERSION = 3;',PERSISTENCE)


if __name__=='__main__': unittest.main()
