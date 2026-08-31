import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def source(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin + 1)]


def threat_result(result_type, roll, before, after):
    function = source("function buildThreatCheckResult", "function renderThreatCheckResult")
    script = f"{function}\nprocess.stdout.write(JSON.stringify(buildThreatCheckResult({json.dumps(result_type)},{roll},{before},{after})));"
    return json.loads(subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout)


def test_shared_npo_renderers_keep_text_and_remove_all_decorative_icons():
    history = source("function renderCompletedNpoQuestions", "function renderActiveNpoQuestion")
    active = source("function renderActiveNpoQuestion", "function renderNpoActionProgress")
    movement = source("function renderNpoMovementConfirmation", "function resolveNpoAction")
    result = source("function renderNpoDecisionResult", "async function completeNpoActivation")
    for renderer in (history, active, movement, result):
        assert "npo-question-icon" not in renderer
        assert "npoIcon" not in renderer
        assert "<svg" not in renderer
    assert "item.question||item.action" in history
    assert "item.answer?'Yes':'No'" in history
    assert 'data-answer="no"' in active and 'data-answer="yes"' in active
    assert "displayAction" in movement and "decision.reason" in movement
    for text in ("NEXT ACTION", "SELECTED ACTION", "Select Target", "Confirm Target", "Resolve Combat"):
        assert text in result


def test_icon_helpers_styles_and_reserved_column_are_deleted():
    for dead in ("npoIcon", "iconForNpoQuestion", "iconForNpoDecision", "npoQuestionIcons", "npoMovementIcons"):
        assert dead not in APP
    assert ".npo-question-icon" not in CSS
    assert "grid-template-columns:minmax(0,1fr) auto" in CSS
    assert "grid-template-columns:32px minmax(0,1fr) auto" not in CSS
    assert ".npo-result-card{padding:" in CSS
    assert ".npo-question-active h3{margin:0 0 6px}" in CSS


def test_npo_action_guidance_and_decisions_are_preserved():
    for text in ("Reposition", "Dash", "Charge", "Shoot", "Fight", "TARGET PRIORITY"):
        assert text in APP
    assert "Can this NPO use ${action} now?" in APP
    assert "Check the action’s target, distance, and placement." in APP


def test_first_threat_result_uses_existing_animation_sound_and_committed_roll():
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    assert "animate?rollingDieHtml():dieHtml({value:result.roll" in render
    assert "animate?'animated-roll':'settled'" in render
    assert "void TombWorldDiceSfx.play()" in render
    assert "setTimeout" in render and "DICE_ROLL_ANIMATION_MS" in render
    assert "die.innerHTML=dieHtml({value:result.roll" in render
    assert "die.classList.replace('animated-roll','settled')" in render
    assert "threatCheckResultDetails" in render and "hidden" in render
    assert "button.disabled=false" in render
    assert "requestDiceResults" not in render and "setThreat(" not in render


def test_presentation_marker_is_saved_before_play_and_reload_is_settled():
    result = threat_result("breach", 4, 3, 5)
    assert result == {"version": 1, "type": "breach", "roll": 4, "threatBefore": 3,
                      "threatAfter": 5, "baseThreat": 1, "rollThreat": 1,
                      "acknowledged": False, "presentationSeen": False}
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    assert render.index("result.presentationSeen=true") < render.index("save();") < render.index("TombWorldDiceSfx.play()")
    assert "const animate=!isPvpMode()&&!result.presentationSeen&&!reducedMotion" in render
    assert "matchMedia('(prefers-reduced-motion: reduce)').matches" in render
    assert "result.acknowledged=true" in render
    assert "save();commitHumanPlayerAction(stage)" in render


def test_threat_rules_cap_and_scout_exception_remain_unchanged():
    assert threat_result("operateHatch", 1, 3, 3)["rollThreat"] == 0
    assert threat_result("operateHatch", 4, 3, 4)["rollThreat"] == 1
    assert threat_result("breach", 1, 3, 4)["baseThreat"] == 1
    assert threat_result("breach", 4, 3, 5)["rollThreat"] == 1
    completion = source("async function completePlayerActivation", "function npoName")
    assert "stage.hatch&&state.missionId!=='scout-sub-crypt'" in completion
    assert "boundedInteger(state.threat+amount,0,15,state.threat)" in source("function setThreat", "function escapeHtml")
    assert "committedEffectKeys" in completion and "pendingDice" in APP


def test_release_surfaces_and_save_schema():
    expected = ".".join(map(str, (9, 2, 23)))
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f"{asset}?v={expected}" in INDEX
    persistence = (ROOT / "persistence.js").read_text()
    assert "const SAVE_VERSION = 3;" in persistence
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
