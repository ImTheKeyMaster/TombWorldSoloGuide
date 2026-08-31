import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin + 1)]


def threat_result(result_type, roll, before, after):
    function = source("function buildThreatCheckResult", "function renderThreatCheckResult")
    script = f"{function}\nprocess.stdout.write(JSON.stringify(buildThreatCheckResult({json.dumps(result_type)},{roll},{before},{after})));"
    return json.loads(subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout)


def test_all_new_torrent_steps_start_unchecked_in_every_mode():
    renderer = source("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
    assert "input.checked=sameStep?(saved.secondaryTargetIds||[]).includes(input.value):false" in renderer
    assert "automaticallySelected" not in renderer
    assert "!isPvpMode()&&ruleId==='torrent'&&attackerSide==='npo'" not in APP
    assert APP.count("showSecondaryTargetCheck({ruleId,distance:") == 2
    assert "attackerSide:'player'" in APP and "attackerSide:'npo'" in APP


def test_same_step_restores_only_saved_secondary_targets():
    renderer = source("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
    assert "saved?.ruleId===ruleId" in renderer
    assert "saved?.primaryTargetId===primaryTargetId" in renderer
    assert "saved?.profileKey===profileKey" in renderer
    assert "(saved.secondaryTargetIds||[]).includes(input.value):false" in renderer
    assert "secondaryTargetIds=$$('[data-weapon-rule-target]:checked')" in renderer


def test_zero_secondary_targets_remain_valid_after_tabletop_confirmation():
    renderer = source("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
    assert "selectedTargets=[{id:primaryTargetId" in renderer
    assert "$('#confirmSecondaryTargets').disabled=!confirmation.checked" in renderer
    assert "secondaryTargetIds.length" not in renderer
    assert "secondaryTargetIds:[" not in renderer
    assert "onContinue(state.weaponRuleResolution)" in renderer


def test_torrent_candidates_distances_and_resolution_are_preserved():
    renderer = source("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
    assert "target.id!==primaryTargetId" in renderer
    assert "target.inPlay!==false&&Number(target.wounds)>0" in renderer
    assert "Torrent attacks each selected valid enemy target within ${distance} inches" in renderer
    assert "distance:weaponRuleValue(profile,ruleId)" in APP
    assert "distance:weaponRuleValue(baseProfile,ruleId)" in APP
    assert "orderedTargetIds=[...new Set([primaryTargetId,...secondaryTargetIds]" in APP
    assert "advanceMultiTargetAttackSequence" in APP
    assert "Torrent 1\"" in APP and "Torrent 2\"" in APP


def test_blast_shared_renderer_and_friendly_candidates_are_unchanged():
    renderer = source("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
    assert "const isBlast=ruleId==='blast'" in renderer
    assert "including friendly operatives" in renderer
    assert APP.count("ruleId==='blast'?[...playerTargets,...npoTargets]") == 2
    assert "weaponHasRule(profile,'blast')?'blast'" in APP
    assert "weaponHasRule(baseProfile,'blast')?'blast'" in APP


def test_solo_first_threat_presentation_animates_committed_result_with_sound():
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    assert "const animate=!isPvpMode()&&!result.presentationSeen&&!reducedMotion" in render
    assert "animate?rollingDieHtml():dieHtml({value:result.roll" in render
    assert "animate?'animated-roll':'settled'" in render
    assert "void TombWorldDiceSfx.play()" in render
    assert "${animate?'disabled':''}>Continue" in render
    assert "${animate?'hidden':''}" in render
    assert "DICE_ROLL_ANIMATION_MS" in render
    assert "die.innerHTML=dieHtml({value:result.roll" in render
    assert "button.disabled=false" in render


def test_pvp_and_reduced_motion_use_immediate_settled_presentation():
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    animate_declaration = "const animate=!isPvpMode()&&!result.presentationSeen&&!reducedMotion;"
    assert animate_declaration in render
    assert "matchMedia('(prefers-reduced-motion: reduce)').matches" in render
    assert render.index(animate_declaration) < render.index("if(animate){")
    sound_branch = render[render.index("if(animate){"):render.index("button.onclick")]
    assert "rollingDieHtml()" not in sound_branch
    assert "TombWorldDiceSfx.play()" in sound_branch
    assert "requestDiceResults" not in render and "Math.random" not in render


def test_presentation_reload_and_transaction_guards_remain_intact():
    render = source("function renderThreatCheckResult", "function confirmEndHumanPlayerActivation")
    completion = source("async function completePlayerActivation", "function npoName")
    commit = source("function commitHumanPlayerAction", "function buildThreatCheckResult")
    assert render.index("result.presentationSeen=true") < render.index("save();") < render.index("if(animate){")
    assert "result.acknowledged=true" in render
    assert "save();commitHumanPlayerAction(stage)" in render
    assert completion.index("setThreat(inc") < completion.index("stage.threatCheckResult=buildThreatCheckResult")
    assert "threatAlreadyCommitted" in completion and "committedEffectKeys" in completion
    assert commit.count("activation.remainingAp=before-pending.cost") == 1
    assert commit.count("acknowledgeCurrentDiceRequest()") == 1
    assert "pendingDice" in APP


def test_breach_hatch_cap_scout_and_grade_rules_are_unchanged():
    assert threat_result("operateHatch", 1, 3, 3)["rollThreat"] == 0
    assert threat_result("operateHatch", 6, 3, 4)["rollThreat"] == 1
    assert threat_result("breach", 1, 3, 4)["baseThreat"] == 1
    assert threat_result("breach", 6, 3, 5)["rollThreat"] == 1
    completion = source("async function completePlayerActivation", "function npoName")
    assert "stage.hatch&&state.missionId!=='scout-sub-crypt'" in completion
    assert "boundedInteger(state.threat+amount,0,15,state.threat)" in APP
    assert "narrationSeen:false" in source("function setThreat", "function escapeHtml")


def test_v9223_release_surfaces_and_save_contract():
    expected = ".".join(map(str, (9, 2, 23)))
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert all(f"{asset}?v={expected}" in INDEX for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ))
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f"tomb-world-battle-guide-{expected}" == "tomb-world-battle-guide-" + expected
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
