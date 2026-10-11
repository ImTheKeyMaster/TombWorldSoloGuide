from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'styles.css').read_text(encoding='utf-8')
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
WORKER = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
HELPER = APP.split('function experimentalNpoTargetRosterRail(eligibleTargetIds)',1)[1].split('function updateNpoTargetConfirmationAvailability',1)[0]
RENDER = APP.split('function renderNpoDecisionResult(',1)[1].split('async function completeNpoActivation',1)[0]

def test_release_versions_match():
    assert tuple(map(int,CURRENT_APP_VERSION.split('.'))) >= (10,0,111)
    assert f'V{CURRENT_APP_VERSION}' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER

def test_rail_is_limited_to_experimental_deathwatch_attacks():
    assert "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'&&attackRequired&&!targetConfirmed&&eligibleTargetIds.length>0" in RENDER
    assert 'experimentalNpoTargetRosterRail(eligibleTargetIds)' in RENDER
    assert '<select id="npoPriorityTarget"' in RENDER
    assert '<input id="npoPriorityTarget"' in RENDER

def test_rail_uses_live_wounds_names_portraits_and_stable_ids():
    for expression in ['eligibleTargetIds.map((id,index)=>{','playerCurrentWounds(id)','playerDefinition(id)?.wounds','experimentalDeathwatchGreenPortraitSvg(id,','escapeHtml(playerName(id))','escapeHtml(woundLabel)','data-npo-target-id=','playerTargetAriaLabel(id)']:
        assert expression in HELPER
    assert 'experimental-roster-detail' not in HELPER

def test_selection_and_keyboard_support():
    assert 'role="radiogroup"' in HELPER
    assert 'role="radio"' in HELPER
    for snippet in ["classList.toggle('selected',selected)","button.setAttribute('aria-checked',String(selected))","['ArrowLeft','ArrowRight','Home','End']","nextButton.scrollIntoView({block:'nearest',inline:'nearest'})","state.npoAttackTargetId=id;","updateNpoTargetConfirmationAvailability();","if(!eligibleNpoAttackTargets().includes(id))"]:
        assert snippet in RENDER
    assert 'data-dialog-focus' in RENDER
    assert "const targetButtons=$$('[data-npo-target-id]',modal);" in RENDER

def test_confirm_target_retains_original_action_checks():
    confirm=APP.split('function confirmNpoAttackTarget(n,decision)',1)[1].split('function openNpoCombat(',1)[0]
    for snippet in ['eligibleNpoAttackTargets()','state.npoAttackTargetId=selectedTargetId;','pendingAction.id','openNpoCombat(n,decision,[],state.lastActivation.answers||{})']:
        assert snippet in confirm

def test_horizontal_mobile_layout_is_scoped_to_tomb_mode():
    block=CSS.split('Experimental Deathwatch target rail.',1)[1]
    assert 'html[data-ui="tomb"] .npo-target-roster-rail' in block
    assert 'overflow-x:auto' in block
    assert 'html[data-ui="tomb"] .npo-target-roster-wounds' in block
    assert 'html[data-ui="tomb"] .npo-target-roster-item.selected' in block
    assert '@media(max-width:600px)' in block
