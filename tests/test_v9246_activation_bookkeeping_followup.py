from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_pending_final_ap_action_has_only_cancel_and_completion_controls():
    result = section("function showPendingHumanPlayerActionCompletion", "function commitHumanPlayerAction")
    assert 'id="pendingActionOtherDamage"' not in result
    assert "Apply Other Damage" not in result
    assert result.count('<button class="btn') == 2
    assert "$('#cancelHumanPlayerAction').onclick=cancelCurrentHumanPlayerAction" in result
    assert "$('#commitHumanPlayerAction').onclick=()=>completePlayerActivation(stage)" in result
    assert result.count("completePlayerActivation(stage)") == 1


def test_pending_action_commit_guards_remain_authoritative():
    commit = section("function commitHumanPlayerAction", "function continueAfterCommittedHumanAction")
    assert "pending.activationId!==activation.activationId" in commit
    assert "pending.actionId!==stage.humanActionId" in commit
    assert "(activation.completedActionIds||[]).includes(pending.actionId)" in commit
    assert "pending.cost>before" in commit


def test_removed_bookkeeping_copy_and_ids_are_not_player_facing():
    assert "Apply Other Damage" not in APP
    assert "pendingActionOtherDamage" not in APP
    assert "applyOtherDamage" not in APP
    assert "function showApplyOtherDamage" not in APP


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


def test_release_surfaces_remain_current_after_v9246():
    expected = CURRENT_APP_VERSION
    assert f"const APP_VERSION = '{expected}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{expected}</div>' in index
    assert index.count(f"?v={expected}") == 10
    assert (ROOT / "README.md").read_text().startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
