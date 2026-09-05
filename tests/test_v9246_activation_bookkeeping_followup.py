from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_strict_damage_validation_and_single_commit_guard():
    damage = section("function showApplyOtherDamage", "function renderHumanPlayerActionPicker")
    assert "input.valueAsNumber" in damage
    assert "!Number.isInteger(amount)||amount<1||amount>wounds" in damage
    assert "Enter a whole number from 1 to ${wounds}." in damage
    assert "Math.floor" not in damage
    assert "Math.min" not in damage
    assert "if(button.disabled)return" in damage
    assert "button.disabled=true" in damage
    assert "pendingStage&&!canCommitHumanPlayerAction(pendingStage)" in damage


def test_nonlethal_bookkeeping_preserves_the_authoritative_activation():
    damage = section("function showApplyOtherDamage", "function renderHumanPlayerActionPicker")
    adjustment = section("function adjustPlayerWounds", "function adjustWounds")
    assert "if(remaining>0){save();onNonlethal();return;}" in damage
    assert "activationBookkeeping&&activePlayerActivation()?.operativeId===id" in adjustment
    preserving = adjustment.split("if(preservingCurrentActivation)", 1)[1].split("if(checkGameEnd())", 1)[0]
    assert "setNextActivation" not in preserving
    for field in ("remainingAp", "completedActionIds", "resolvedActions", "pendingAction", "actionSequence"):
        assert field not in damage.split("if(remaining>0)", 1)[0]


def test_lethal_bookkeeping_uses_canonical_completion_once_and_clears_pending_state():
    damage = section("function showApplyOtherDamage", "function renderHumanPlayerActionPicker")
    completion = section("async function completeHumanPlayerActivation", "const PLAYER_ACTION_COSTS")
    assert "if(pendingStage)commitHumanPlayerAction(pendingStage,{deferContinuation:true})" in damage
    assert damage.count("completeHumanPlayerActivation()") == 1
    assert "expireActivationEffects(operativeId);advanceAfterActivation('player')" in completion
    assert "executeMissionLifecycleHook('onPlayerActivationCompleted'" in completion
    assert completion.count("state.lastActivation=null") == 2


def test_pending_final_ap_action_offers_optional_bookkeeping_without_committing_it():
    result = section("function showPendingHumanPlayerActionCompletion", "function commitHumanPlayerAction")
    assert 'id="pendingActionOtherDamage"' in result
    assert result.index("Apply Other Damage") < result.index("id=\"commitHumanPlayerAction\"")
    assert "pendingStage:stage" in result
    assert "onNonlethal:()=>showPendingHumanPlayerActionCompletion(stage,action,descriptions,completionLabel)" in result
    assert result.count("completePlayerActivation(stage)") == 1


def test_pending_action_is_validated_before_bookkeeping_damage_is_applied():
    damage = section("function showApplyOtherDamage", "function showPendingHumanPlayerActionCompletion")
    validator = section("function canCommitHumanPlayerAction", "function showApplyOtherDamage")
    commit = section("function commitHumanPlayerAction", "function continueAfterCommittedHumanAction")
    assert damage.index("canCommitHumanPlayerAction(pendingStage)") < damage.index("adjustPlayerWounds(")
    assert "pending.activationId===activation.activationId" in validator
    assert "pending.actionId===stage?.humanActionId" in validator
    assert "!(activation.completedActionIds||[]).includes(pending.actionId)" in validator
    assert "pending.cost<=activation.remainingAp" in validator
    assert "pending.activationId!==activation.activationId" in commit
    assert "(activation.completedActionIds||[]).includes(pending.actionId)" in commit
    assert "pending.cost>before" in commit


def test_legacy_damage_action_state_is_inert_but_save_key_is_compatible():
    costs = section("const PLAYER_ACTION_COSTS", "function playerActionCost")
    summary = section("function playerActivationSummary", "function newlyEliminated")
    activation = section("async function completePlayerActivation", "function npoName")
    assert "damage:" not in costs
    assert "stage.damage" not in summary
    assert "stage.damage" not in activation
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_pvp_named_actions_are_grouped_as_operative_and_hatches_as_mission():
    picker = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    groups = section("const HUMAN_ACTION_GROUPS", "function activePlayerActivation")
    assert "id==='operate-hatch'?'mission':'operative'" in picker
    assert "'special'" not in picker
    assert "label:'Operative Actions'" in groups
    assert "Special Actions" not in groups


def test_release_surfaces_are_v9246():
    expected = ".".join(("9", "2", str(40 + 6)))
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{expected}</div>' in index
    assert index.count(f"?v={expected}") == 10
    assert (ROOT / "README.md").read_text().startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
