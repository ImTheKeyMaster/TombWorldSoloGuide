import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()


def section(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


class V801ActivationRestoreTests(unittest.TestCase):
    def test_01_normalize_does_not_call_state_dependent_id(self):
        self.assertNotIn('missionActivationId(', section('function normalizeState', 'function npoDefinition'))

    def test_02_normalization_fallback_does_not_read_global_state(self):
        self.assertIn("activationIdFromState(merged,'npo',merged.lastActivation.npoId)", APP)

    def test_03_pure_helper_accepts_explicit_state(self):
        helper = section('function activationIdFromState', 'function missionActivationId')
        self.assertIn('sourceState', helper)
        self.assertNotIn('state.', helper)
        self.assertNotIn('document', helper)

    def test_04_existing_activation_ids_are_preserved(self):
        self.assertIn('merged.lastActivation.activationId||activationIdFromState', APP)

    def test_05_missing_ids_are_deterministic(self):
        helper = section('function activationIdFromState', 'function missionActivationId')
        script = f"{helper}; const s={{turningPoint:2,activationNumber:4}}; if(activationIdFromState(s,'npo','x')!=='2:5:npo:x')process.exit(1); if(activationIdFromState(s,'npo','x')!==activationIdFromState(s,'npo','x'))process.exit(2);"
        subprocess.run(['node', '-e', script], cwd=ROOT, check=True)

    def test_06_question_state_restores(self):
        self.assertIn('questionHistory:Array.isArray(merged.lastActivation.questionHistory)', APP)
        self.assertIn('currentContext:{inEnemyControlRange:null', APP)

    def test_07_pending_movement_restores_safely(self):
        self.assertIn("pendingAction:isRecord(merged.lastActivation.pendingAction)", APP)
        self.assertIn("typeof merged.lastActivation.pendingAction.id==='string'", APP)
        self.assertIn('if(activation.pendingAction){resolveNpoAction(n,activation.pendingAction);return;}', APP)

    def test_07b_action_result_restores_without_recommitting(self):
        self.assertIn('activation.awaitingActionResult={...record,endsActivation}', APP)
        self.assertIn('if(activation.awaitingActionResult){renderNpoActionResult', APP)
        self.assertIn('ROUTINE_NPO_MOVEMENT_ACTIONS.has(activation.awaitingActionResult.id)', APP)
        renderer = section('function renderNpoActionResult', 'function renderNpoActivationEnd')
        self.assertIn('activation.awaitingActionResult=null;save()', renderer)
        self.assertNotIn('commitNpoAction(', renderer)

    def test_08_remaining_ap_preserved(self):
        self.assertIn('remainingAp:remaining', APP)

    def test_09_completed_actions_preserved(self):
        self.assertIn('completedActionIds:Array.isArray(merged.lastActivation.completedActionIds)', APP)

    def test_10_pending_combat_preserved(self):
        self.assertIn('combatDraft', APP)
        self.assertIn('const saved=state.lastActivation?.combatDraft', APP)

    def test_11_damage_not_applied_twice(self):
        self.assertIn('resolutionCommitted||!pending||!canCommitNpoAction', APP)

    def test_12_activation_started_hook_not_repeated(self):
        continuation = section('function showNpoSelection', 'function remainingPlayerOperatives')
        self.assertNotIn('notifyMissionActivationStarted', continuation)

    def test_13_journal_entries_not_duplicated(self):
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        self.assertEqual(commit.count('log('), 1)

    def test_14_runtime_startup_save_does_not_hit_tdz(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const saved={phase:'firefight',activeNpoId:'saved-npo',lastActivation:{npoId:'saved-npo',remainingAp:1,committed:false}};
const nodes=new Map();
function element(){return {hidden:false,disabled:false,open:false,innerHTML:'',style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},addEventListener(){},querySelector(){return element()},querySelectorAll(){return []},setAttribute(){},removeAttribute(){},showModal(){this.open=true},close(){this.open=false}};}
const document={addEventListener(){},querySelector(selector){if(!nodes.has(selector))nodes.set(selector,element());return nodes.get(selector);},querySelectorAll(){return []},createElement(){return element();}};
const context={console,document,window:{addEventListener(){},location:{reload(){}}},navigator:{onLine:true},localStorage:{getItem(){return JSON.stringify(saved);},setItem(){},removeItem(){}},fetch(){return Promise.reject(new Error('stop after initialization'));},requestAnimationFrame(){},matchMedia(){return {matches:true};},URL:{createObjectURL(){return '';},revokeObjectURL(){}},Blob,crypto:{randomUUID(){return 'uuid';}},setTimeout,clearTimeout,
  TombWorldPersistence:{currentSaveVersion(){return 7;},migrateSaveDetailed(raw){return {state:raw,report:{requiresRegeneration:false,aliasesApplied:[],instanceNamesRepaired:[],instanceIdsCreated:[],instanceIdsRepaired:[],loadoutsNormalized:[],woundsClamped:[],unsupportedRetiredTypes:[],invalidPhysicalLimits:[],errors:[],pendingStateCleared:[]}};},createPersistedSave(state){return state;},resetActiveBattle(state){return state;}},
  TombWorldDeadlyEncounters:{emptyState(){return {rooms:{},objectives:{},operativeLocations:{},resolutionHistory:[]};},normalizeState(state){return state||this.emptyState();},features:[]},TombWorldEventEffects:{},TombWorldMissionEngine:{}};
context.globalThis=context;
vm.runInNewContext(fs.readFileSync('app.js','utf8'),context);
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Cannot access 'state' before initialization", result.stderr)

    def test_15_update_app_uses_reload_restore_path(self):
        self.assertIn("if(updateRequested)window.location.reload()", APP)
        self.assertIn('let state;', APP)

    def test_16_unexpected_failure_renders_recovery_card(self):
        recovery = section('function renderStartupRecovery', 'if(startupInitializationError)')
        self.assertIn('Retry Loading', recovery)
        self.assertIn('Export Save', recovery)
        self.assertIn('role="alert"', recovery)

    def test_17_recovery_does_not_delete_save(self):
        recovery = section('function renderStartupRecovery', 'if(startupInitializationError)')
        self.assertNotIn('removeItem', recovery)
        self.assertIn('localStorage.getItem(STORAGE_KEY)', recovery)

    def test_18_version_801_everywhere(self):
        self.assertIn("const APP_VERSION = '8.6.23';", APP)
        self.assertIn("const APP_VERSION = '8.6.23';", WORKER)
        self.assertIn('V8.6.23', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.23'))
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.23', INDEX)


if __name__ == '__main__':
    unittest.main()
