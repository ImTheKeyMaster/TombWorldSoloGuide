import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
STYLES = (ROOT / "styles.css").read_text()


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start) + 1)]


def threat_result(result_type, roll, before, after):
    function = source("function buildThreatCheckResult", "function renderThreatCheckResult")
    script = f"""
{function}
process.stdout.write(JSON.stringify(buildThreatCheckResult({json.dumps(result_type)},{roll},{before},{after})));
"""
    return json.loads(subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout)


def test_breach_contributions_and_roll_request_are_unchanged():
    completion = source("async function completePlayerActivation", "function npoName")
    assert "count:1,sides:6" in completion
    for roll, roll_threat in ((1, 0), (3, 0), (4, 1), (6, 1)):
        result = threat_result("breach", roll, 3, min(15, 4 + roll_threat))
        assert result["baseThreat"] == 1
        assert result["rollThreat"] == roll_threat


def test_hatch_contributions_and_mission_exception_are_unchanged():
    completion = source("async function completePlayerActivation", "function npoName")
    assert "stage.hatch&&state.missionId!=='scout-sub-crypt'" in completion
    for roll, roll_threat in ((1, 0), (3, 0), (4, 1), (6, 1)):
        result = threat_result("operateHatch", roll, 3, 3 + roll_threat)
        assert result["baseThreat"] == 0
        assert result["rollThreat"] == roll_threat


def test_result_copy_breakdown_and_accessibility():
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    for text in ("Breach · Threat Check Result", "Operate Hatch · Threat Check Result",
                 "NO ADDITIONAL THREAT", "+1 ADDITIONAL THREAT",
                 "NO THREAT INCREASE", "+1 THREAT", "Opening the Breach",
                 "Threat Check", "Threat remains", "Continue"):
        assert text in render
    assert 'aria-hidden="true">→' in render
    assert 'class="sr-only"> to ' in render
    assert "dieHtml({value:result.roll" in render
    assert "button.disabled=true" in render
    assert "Cancel" not in render and "Reroll" not in render and "Undo" not in render


def test_threat_cap_uses_actual_bounded_values():
    at_cap = threat_result("operateHatch", 6, 15, 15)
    near_cap = threat_result("breach", 6, 14, 15)
    assert at_cap["threatAfter"] == 15
    assert near_cap["threatAfter"] == 15
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    assert "Threat is already at maximum." in render
    assert "result.threatBefore===result.threatAfter" in render


def test_two_phase_commit_reload_and_duplicate_guards():
    completion = source("async function completePlayerActivation", "function npoName")
    commit = source("function commitHumanPlayerAction", "function buildThreatCheckResult")
    assert completion.index("setThreat(inc") < completion.index("stage.threatCheckResult=buildThreatCheckResult")
    assert completion.index("stage.threatCheckResult=buildThreatCheckResult") < completion.index("renderThreatCheckResult(stage)", completion.index("stage.threatCheckResult=buildThreatCheckResult"))
    assert "committedEffectKeys" in completion and "threatAlreadyCommitted" in completion
    assert "if(stage.sequential&&stage.threatCheckResult&&!stage.threatCheckResult.acknowledged)" in completion
    assert "result.acknowledged=true" in APP
    assert "save();commitHumanPlayerAction(stage)" in APP
    assert "save();acknowledgeCurrentDiceRequest()" in commit
    assert commit.index("activation.remainingAp=before-pending.cost") < commit.index("acknowledgeCurrentDiceRequest()")


def test_action_commit_and_pending_dice_remain_single_owner():
    commit = source("function commitHumanPlayerAction", "function buildThreatCheckResult")
    assert commit.count("activation.remainingAp=before-pending.cost") == 1
    assert commit.count("completedActionIds=[") == 1
    assert commit.count("acknowledgeCurrentDiceRequest()") == 1
    assert "commitHumanPlayerAction(stage)" in source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")


def test_grade_journal_and_fight_result_paths_are_untouched():
    threat = source("function setThreat", "function escapeHtml")
    assert "Threat ${before} → ${state.threat}: ${reason}" in threat
    assert "narrationSeen:false" in threat
    fight = source("function acknowledgeFightResult", "function renderFightResolution")
    assert "fight.resultAcknowledged=true;save()" in fight
    assert "renderFightResult(fight)" in fight


def test_mobile_styles_and_version_surfaces():
    assert ".threat-check-result" in STYLES
    assert ".threat-check-result .wizard-actions .btn{width:100%}" in STYLES
    expected_version = ".".join(map(str, (9, 2, 20 + 1)))
    assert CURRENT_APP_VERSION == expected_version
    assert f"const APP_VERSION = '{expected_version}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{expected_version}</div>' in INDEX
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f"{asset}?v={expected_version}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{expected_version}\n\n## v{expected_version}")
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
