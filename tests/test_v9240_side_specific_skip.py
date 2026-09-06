from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    offset = APP.index(start)
    return APP[offset:APP.index(end, offset)]


def test_release_surfaces_keep_save_key_and_schema_unchanged():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 41)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")


def test_visibility_is_current_side_specific_and_transaction_safe():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "const side=state.nextSide" in visibility
    assert "side==='player'&&playerOperativesRemaining()<=0" in visibility
    assert "side==='npo'&&readyNpos().length<=0" in visibility
    assert "state.phase!=='firefight'||state.completed||state.gameEnd" in visibility
    assert "activation&&!activation.committed&&!activation.completed" in visibility
    for pending in ("state.pendingDice", "state.combatState", "state.fightState", "state.missionActionContext", "state.weaponRuleResolution", "state.hotResolution"):
        assert pending in visibility
    assert "objectiveEngine" not in visibility
    assert "missionProgress" not in visibility


def test_solo_and_pvp_use_the_required_per_side_first_activation_rules():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "if(!isPvpMode()&&side==='npo')return true" in visibility
    assert "side==='player'?state.playerActivated>0:state.npoActivated>0" in visibility
    assert "activationsCompleted" not in visibility


def test_activation_cards_use_contextual_names_and_stack_skip_after_primary():
    cards = source("function nextStepCard(){", "function missionStrategyPending")
    assert "activationSideName('player')" in cards
    assert "Activate Next ${teamName} Operative" in cards
    assert "Activate ${activationModelLabel('player')}" in cards
    assert "<h2>${escapeHtml(teamName)} Activation</h2>" in cards
    assert "<h2 class=\"npo-activation-title\">Necron Activation</h2>" in cards
    assert "state.npoActivated>0?'Activate Next Necron'" in cards
    assert cards.count("${skipRemainingActivationsControl()}") == 2
    assert cards.count("${skipRemainingActivationsControl()}</section>") == 2
    assert ".skip-remaining-activations{width:100%;margin-top:10px}" in STYLES
    assert "NPO Activation" not in cards


def test_model_labels_cover_solo_necrons_pvp_operatives_and_articles():
    labels = source("function activationSideName", "function canSkipRemainingActivations")
    assert "side==='npo'?'Necron':selectedPlayerTeamName()" in labels
    assert "isPvpMode()?'Necron Operatives':'Necrons'" in labels
    assert "/^[aeiou]/i.test(teamName)?'an':'a'" in labels
    assert "${teamName} Operatives" in labels


def test_shared_gameplay_terminology_is_contextual_in_solo_and_pvp():
    terminology = source("function playerSideLabel", "function deadlyEncountersActive")
    assert "return selectedPlayerTeamName()" in terminology
    assert "return 'Necron'" in terminology
    assert "return 'Necrons'" in terminology
    presenter = source("function presentSideTerminology", "function canBuildPlayerRoster")
    assert "if(!isPvpMode())return text" not in presenter
    assert ".replace(/NPOs\\b/g,()=>opponentPluralLabel())" in presenter
    assert ".replace(/Player\\b/g,()=>playerSideLabel())" in presenter


def test_downstream_activation_guidance_uses_shared_contextual_terminology():
    selection = source("function showNpoSelection", "function remainingPlayerOperatives")
    assert "opponentSingularLabel()" in selection
    assert "playerSideLabel()" in selection
    header = source("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "opponentSingularLabel()" in header
    instructions = source("function npoSpecialActionDescription", "function resolveNpoSpecialAction")
    assert "presentSideTerminology(text)" in instructions
    assert "isPvpMode()?text.replaceAll" not in instructions


def test_confirmation_is_contextual_and_back_only_closes_the_dialog():
    confirmation = source("function confirmSkipRemainingActivations", "function skipRemainingActivations")
    assert "activationSideName(side)" in confirmation
    assert "activationModelLabel(side,{plural:true})" in confirmation
    assert "SKIP REMAINING ${models.toUpperCase()}?" in confirmation
    assert "may continue to activate" in confirmation
    assert "data-close data-dialog-focus>BACK" in confirmation
    assert "SKIP ${escapeHtml(sideName.toUpperCase())}" in confirmation
    assert "save()" not in confirmation


def test_skip_transaction_mutates_only_the_current_side_and_reuses_alternation():
    transaction = source("function skipRemainingActivations(){", "function showCeaselessScuttling")
    assert "skipRemainingActivationsPending||!canSkipRemainingActivations()" in transaction
    assert "const side=state.nextSide" in transaction
    player_branch = transaction.split("if(side==='player')", 1)[1].split("}else{", 1)[0]
    npo_branch = transaction.split("}else{", 1)[1].split("advanceAfterActivation", 1)[0]
    assert "remainingPlayerOperatives()" in player_branch
    assert "state.playerActivatedIds" in player_branch
    assert "readyNpos()" not in player_branch
    assert "readyNpos().forEach" in npo_branch
    assert "state.playerActivatedIds" not in npo_branch
    assert "advanceAfterActivation(side)" in transaction
    assert "state.activationNumber+=" not in transaction
    assert "state.playerActivated=" not in transaction
    assert "state.npoActivated+=" not in transaction
    assert "state.phase='end'" not in transaction
    for forbidden in ("executeMissionLifecycleHook", "completePlayerActivation", "completeNpoActivation", "continueNpoActivation", "requestDiceResults", "setThreat("):
        assert forbidden not in transaction


def test_existing_scheduler_continues_the_other_side_or_enters_score_cleanup():
    scheduler = source("function setNextActivation", "const GRADE_CONFIG")
    assert "!state.activationFinishedForTurningPoint.player&&playerOperativesRemaining()>0" in scheduler
    assert "!state.activationFinishedForTurningPoint.npo&&readyNpos().length>0" in scheduler
    assert "if(!playerCanAct&&!npoCanAct)" in scheduler
    assert "state.phase='end'" in scheduler
    assert "if(!playerCanAct)" in scheduler and "state.nextSide='npo'" in scheduler
    assert "if(!npoCanAct)" in scheduler and "state.nextSide='player'" in scheduler
    end_card = source("if(state.phase==='end'){", "setNextActivation(state.nextSide")
    assert "Score and clean up" in end_card
    assert 'id="endChecked" type="checkbox"' in end_card
    assert 'id="finishTp" disabled' in end_card


def test_skip_state_persists_in_existing_model_flags_and_resets_next_turn():
    transaction = source("function skipRemainingActivations(){", "function showCeaselessScuttling")
    assert transaction.index("save()") < transaction.index("render()")
    normalizer = source("function normalizeState", "function npoDefinition")
    assert "merged.playerActivatedIds=" in normalizer
    assert "merged.roster=" in normalizer
    start_turn = source("async function startTurningPoint", "async function continueTurningPointStart")
    assert "state.playerActivated=0;state.npoActivated=0" in start_turn
    assert "state.playerActivatedIds=[]" in start_turn
    assert "processReadyStep()" in start_turn


def test_immediate_victory_and_recent_regressions_remain_intact():
    escape = source("let transponderEscapePending", "function handleTransponderCarrierIncapacitation")
    outcome = source("if(state.gameEnd){", "if(state.finalResolution?.pending")
    assert "completeMission('victory')" in escape
    assert "confirmSkipRemainingActivations" not in escape
    assert "requestAnimationFrame(()=>{resetOutcomeScroll();" in outcome
    assert "Assets/Maps/mission-${missionNumber}.png?v=${APP_VERSION}" in APP
