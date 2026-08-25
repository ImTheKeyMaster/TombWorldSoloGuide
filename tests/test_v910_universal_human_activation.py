from pathlib import Path
import re
import json
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(name, next_name):
    return APP.split(f"function {name}", 1)[1].split(f"function {next_name}", 1)[0]


def test_shared_shell_is_used_by_player_and_pvp_necron():
    assert "function renderHumanActivationShell" in APP
    assert "renderHumanActivationShell({" in source("renderHumanPlayerActionPicker", "playerSequentialStage")
    assert "renderHumanActivationShell({" in source("renderHumanNpoActionPicker", "selectHumanNpoAction")


def test_solo_necron_ai_decision_flow_is_preserved():
    solo = source("continueSoloNpoActivation", "normalizeUnknownAttackMovement")
    assert "recommendedNpoActions" in solo
    assert "runNpoPrompt" in solo
    assert "continueSoloNpoActivation();" in source("continueNpoActivation", "continueHumanNecronActivation")


def test_player_movement_actions_commit_sequentially():
    catalog = source("playerHumanActionCatalog", "playerHumanActionState")
    for action in ("Reposition", "Dash", "Charge", "Fall Back"):
        assert f"name:'{action}'" in catalog
    assert "Movement Complete" in source("selectHumanPlayerAction", "commitHumanPlayerAction")


def test_player_combat_actions_commit_sequentially_and_keep_transaction_state():
    picker = source("selectHumanPlayerAction", "commitHumanPlayerAction")
    assert "showPendingPlayerAttackWizard" in picker
    assert "continuePlayerMultiTargetAttack" in picker
    assert "pendingAttackResults" in source("commitHumanPlayerAction", "confirmEndHumanPlayerActivation")
    assert "weaponRuleResolution" in APP and "pendingDice" in APP


def test_shoot_fight_mutual_exclusion_has_visible_reasons():
    legality = source("playerHumanActionState", "renderHumanActivationShell")
    assert "Unavailable after Fight" in legality
    assert "Unavailable after Shoot" in legality


def test_cancel_only_discards_current_uncommitted_action():
    cancel = source("cancelCurrentHumanPlayerAction", "selectHumanPlayerAction")
    assert "activation.pendingAction=null" in cancel
    assert "resolvedActions" not in cancel
    assert "remainingAp" not in cancel


def test_ap_commit_is_guarded_and_exactly_once():
    commit = source("commitHumanPlayerAction", "confirmEndHumanPlayerActivation")
    assert "completedActionIds||[]).includes(pending.actionId)" in commit
    assert "pending.cost>before" in commit
    assert "activation.remainingAp=before-pending.cost" in commit
    assert "activation.pendingAction=null" in commit


def test_player_combat_request_identity_uses_durable_activation_and_action_sequence():
    identity = source("playerActionTransactionIdentity", "showPendingPlayerAttackWizard")
    combat = source("showPlayerCombatResolution", "previewPendingPlayerAttack")
    assert "activation.activationId" in identity
    assert "pending.actionSequence" in identity
    assert "actionIdentity.activationId" in combat
    assert "actionIdentity.actionId" in combat


def test_failed_or_cancelled_action_spends_no_ap():
    cancel = source("cancelCurrentHumanPlayerAction", "selectHumanPlayerAction")
    assert "remainingAp" not in cancel
    assert "No action was spent" in source("showActivationFeatureTargetSelection", "showActivationBreachTargetSelection")


def test_pvp_necron_catalog_special_actions_and_targeting_are_retained():
    assert "function legalHumanNpoActions" in APP
    assert "function supportedHumanNpoActions" in APP
    assert "eligibleNpoSpecialActionTargets" in APP
    for action in ("Canoptek Control", "Molecular Breach", "Geomantic Disturbance", "Nanoscarab Beam"):
        assert action in APP


def test_operate_hatch_breach_and_sarcophagus_are_sequential_actions():
    catalog = source("playerHumanActionCatalog", "playerHumanActionState")
    assert "Operate Hatch" in catalog and "Breach Sarcophagus" in catalog
    assert "showActivationFeatureTargetSelection" in source("selectHumanPlayerAction", "commitHumanPlayerAction")
    assert "completePlayerActivation(stage)" in source("performBreachSarcophagus", "confirmMissionAction")


def test_threat_commits_per_action_with_idempotency_key():
    completion = source("completePlayerActivation", "npoName")
    assert "threatCommitKey" in completion
    assert "committedEffectKeys" in completion
    assert "stage.humanActionName" in completion


def test_reload_restores_active_player_ap_history_and_lock():
    restore = APP.split("merged.lastActivation.side==='player'", 1)[1].split("if(merged.phase==='strategy'", 1)[0]
    for field in ("activationId", "remainingAp", "startingAp", "completedActionIds", "resolvedActions", "pendingAction"):
        assert field in restore
    assert "if(activePlayerActivation()){renderHumanPlayerActionPicker();return true;}" in APP


def test_persistence_validation_does_not_discard_a_player_activation():
    script = r"""
const p=require('./persistence.js');
const catalog={warrior:{id:'warrior',type:'Warrior',name:'Warrior',physicalQuantity:1,wounds:8,move:5,apl:2,save:3,baseSize:32,defaultWeaponId:'blade'}};
const save={saveVersion:3,gameMode:'pvp',roster:[],playerRoster:['player-one'],playerOperativeStates:{'player-one':{inPlay:true}},
 lastActivation:{side:'player',operativeId:'player-one',activationId:'1:1:player:player-one',startingAp:3,remainingAp:2,
 completedActionIds:['move'],resolvedActions:[{id:'move',name:'Reposition'}],committed:false}};
const result=p.migrateSaveDetailed(save,catalog);
console.log(JSON.stringify({activation:result.state.lastActivation,cleared:result.report.pendingStateCleared}));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    restored = json.loads(result.stdout)
    assert restored["activation"]["operativeId"] == "player-one"
    assert restored["activation"]["remainingAp"] == 2
    assert restored["activation"]["completedActionIds"] == ["move"]
    assert "lastActivation" not in restored["cleared"]


def test_persistence_validation_does_not_accept_player_id_as_npo_id():
    script = r"""
const p=require('./persistence.js');
const catalog={warrior:{id:'warrior',type:'Warrior',name:'Warrior',physicalQuantity:1,wounds:8,move:5,apl:2,save:3,baseSize:32,defaultWeaponId:'blade'}};
const save={saveVersion:3,gameMode:'pvp',roster:[],playerRoster:['player-one'],
 lastActivation:{side:'npo',npoId:'player-one',activationId:'1:1:npo:player-one',committed:false}};
const result=p.migrateSaveDetailed(save,catalog);
console.log(JSON.stringify({activation:result.state.lastActivation,cleared:result.report.pendingStateCleared}));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    restored = json.loads(result.stdout)
    assert restored["activation"] is None
    assert "lastActivation" in restored["cleared"]


def test_pending_dice_recovery_remains_integrated():
    assert "resumePendingDiceWorkflow" in APP
    assert "pendingDiceContextIsCurrent" in APP
    assert "if(state.combatState?.side==='player'){resolvePendingPlayerAttacks" in APP
    assert "breach-sarcophagus" in PERSISTENCE


def test_active_operative_is_locked_after_selection_and_guide_can_close():
    picker = source("renderHumanPlayerActionPicker", "playerSequentialStage")
    assert "activation.operativeId" in picker
    assert "Close Guide" in source("renderHumanActivationShell", "renderHumanPlayerActionPicker")
    assert "activePlayerActivation();" in source("showPlayerActivation", "playerActivationSummary")


def test_end_activation_confirmations_cover_ap_and_zero_actions():
    end = source("confirmEndHumanPlayerActivation", "completeHumanPlayerActivation")
    assert "AP remain" in end
    assert "has not performed any actions" in end
    assert "Continue Activation" in end and "End Activation" in end


def test_zero_ap_and_self_incapacitation_complete_automatically():
    commit = source("commitHumanPlayerAction", "confirmEndHumanPlayerActivation")
    assert "playerCurrentWounds(activation.operativeId)<=0||activation.remainingAp<=0" in commit
    assert "completeHumanPlayerActivation" in commit


def test_completion_counters_hook_and_side_advance_are_once_guarded():
    completion = source("completeHumanPlayerActivation", "randomReinforcement")
    assert "activation.committed=true" in completion
    assert "state.activationNumber++" in completion
    assert "advanceAfterActivation('player')" in completion
    assert "onPlayerActivationCompleted" in completion


def test_completion_hook_checkpoint_resumes_without_repeating_bookkeeping():
    completion = source("completeHumanPlayerActivation", "randomReinforcement")
    resume = source("resumeCheckpointedGameplayContext", "missionDiceTotal")
    assert "if(activation.committed)" in completion
    assert "completionHookPending" in completion
    assert "state.activationNumber++" not in completion.split("if(activation.committed)", 1)[1].split("activation.committed=true", 1)[0]
    assert "completionHookPending){await completeHumanPlayerActivation()" in resume


def test_mobile_and_accessible_action_contract():
    assert "aria-label=\"${escapeHtml(accessible)}\"" in APP
    assert "aria-description" in APP
    assert "@media(max-width:430px)" in CSS and "@media(max-width:340px)" in CSS
    assert "overflow-wrap:anywhere" in CSS


def test_player_batch_instruction_and_pass_checkbox_are_removed():
    assert "Select everything this operative will do" not in APP
    assert "eaPass" not in APP
    assert "Complete Activation</button>" not in source("showPlayerActivation", "playerActivationSummary")


def test_release_version_cache_and_save_schema():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}'" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}'" in SW
    assert "tomb-world-battle-guide-${APP_VERSION}" not in SW
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`" in SW
    assert f"V{CURRENT_APP_VERSION}" in INDEX and f"?v={CURRENT_APP_VERSION}" in INDEX
    assert f"Version {CURRENT_APP_VERSION} - Universal Human Activations" in README
    assert "const SAVE_VERSION = 3" in PERSISTENCE
