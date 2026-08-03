import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class V842NpoMovementConfirmationLayoutTests(unittest.TestCase):
    def test_question_and_confirmation_share_activation_header(self):
        header = section('function renderNpoActivationHeader', 'function renderNpoGuideFooter')
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('NPO Activation: ${escapeHtml(npoName(n))}', header)
        for text in ('Wounds:', 'APL ${definition.apl}', 'Order:', 'loadout', 'modifiers.map',
                     'Next movement uses Molecular Breach', 'renderNpoActionProgress()'):
            self.assertIn(text, header)
        self.assertIn('aria-label="Activation profile"', header)
        self.assertIn('${renderNpoActivationHeader(n)}', prompt)
        self.assertIn('${renderNpoActivationHeader(n)}', confirmation)

    def test_all_movement_actions_use_the_question_icon_source(self):
        icons = section('const npoQuestionIcons', 'function npoIcon')
        for action in ('Reposition', 'Dash', 'Charge', 'Fall Back'):
            self.assertIn(action, icons)
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('npoIcon(npoQuestionIcons[displayAction])', confirmation)
        self.assertNotIn("npoIcon('command')", confirmation)

    def test_confirmation_is_an_accessible_active_question_card(self):
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('npo-question-active npo-question-card--active npo-movement-confirmation', confirmation)
        self.assertIn('aria-labelledby="${headingId}"', confirmation)
        self.assertIn('aria-describedby="${instructionId}"', confirmation)
        self.assertIn("headingId='activeNpoMovementHeading'", confirmation)
        self.assertNotRegex(confirmation, r'<h[1-6][^>]*tabindex')
        self.assertIn('focusInitialDialogControl(modal)', confirmation)
        self.assertNotIn('displayAction.toUpperCase()', confirmation)

    def test_confirm_button_uses_full_width_choice_area(self):
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('class="ai-choice-grid"', confirmation)
        self.assertIn('class="ai-choice yes npo-movement-confirm"', confirmation)
        self.assertIn('Confirm ${escapeHtml(displayAction)} Complete', confirmation)
        self.assertIn('.npo-movement-confirm{grid-column:1 / -1;width:100%}', CSS)

    def test_confirmation_and_question_share_footer(self):
        footer = section('function renderNpoGuideFooter', 'function runNpoPrompt')
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('>Back</button>', footer)
        self.assertIn('>Close Guide</button>', footer)
        self.assertIn('${renderNpoGuideFooter(', prompt)
        self.assertIn('${renderNpoGuideFooter()}', confirmation)
        self.assertIn("$('[data-close]',modal).onclick=closeModal", confirmation)

    def test_back_unwinds_only_pending_selection_without_committing(self):
        back = section('function backFromNpoMovementConfirmation', 'function renderNpoMovementConfirmation')
        self.assertIn("selected?.type!=='selected'", back)
        self.assertIn('previous.answer!==true', back)
        self.assertIn('history.slice(0,-2)', back)
        self.assertIn('activation.pendingAction=null', back)
        self.assertIn('activation.movementIntent=null', back)
        self.assertIn('activation.pendingFollowUpAction=null', back)
        self.assertIn('activation.currentContext={...previous.contextBefore}', back)
        self.assertIn('activation.answers={...previous.answers}', back)
        self.assertIn('runNpoPrompt(n,previous.index,previous.answers,earlierHistory)', back)
        self.assertIn('focusInitialDialogControl(modal)', back)
        for forbidden in ('commitNpoAction', 'consumeMolecularBreach', 'declinedActionIds', 'log(', 'showModal('):
            self.assertNotIn(forbidden, back)

    def test_close_and_restore_leave_pending_state_intact(self):
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        restore = section('function continueNpoActivation', 'function continueGuaranteedNpoFollowUp')
        self.assertIn("$('[data-close]',modal).onclick=closeModal", confirmation)
        self.assertNotIn('pendingAction=null', confirmation)
        self.assertIn('if(activation.pendingAction){resolveNpoAction(n,activation.pendingAction);return;}', restore)

    def test_confirm_keeps_existing_idempotent_commit_and_follow_up(self):
        resolver = section('function resolveNpoAction', 'function initiativeSummary')
        commit = section('function canCommitNpoAction', 'function renderNpoActionResult')
        follow_up = section('function continueGuaranteedNpoFollowUp', 'function canCommitNpoAction')
        self.assertIn('if(!canCommitNpoAction(pendingAction.id,pendingAction.apCost))return', resolver)
        self.assertIn('button.disabled=true', resolver)
        self.assertIn('consumeMolecularBreach', resolver)
        self.assertEqual(resolver.count('commitNpoAction({actionId:pendingAction.id'), 1)
        self.assertIn('completedActionIds', commit)
        self.assertIn('movementCommitted:true', commit)
        self.assertIn('resolveNpoAction(n,activation.pendingAction)', follow_up)

    def test_pending_movement_persists_without_save_version_change(self):
        normalization = section('if(isRecord(merged.lastActivation)', 'state.npoAttackTargetId=null')
        for field in ('questionHistory', 'pendingAction', 'movementIntent', 'pendingFollowUpAction'):
            self.assertIn(field, normalization)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_v842_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.34';", APP)
        self.assertIn("const APP_VERSION = '8.6.34';", WORKER)
        self.assertIn('V8.6.34', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.34'))
        self.assertIn('## v8.6.25', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.34', INDEX)


if __name__ == '__main__':
    unittest.main()
