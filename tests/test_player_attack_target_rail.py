from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
RAIL=APP.split('function experimentalPlayerAttackTargetRail(',1)[1].split('function showPendingPlayerAttackWizard(',1)[0]
WIZARD=APP.split('function showPendingPlayerAttackWizard(',1)[1].split('function showPlayerCombatResolution(',1)[0]

def test_version_consistency():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in HTML

def test_experimental_only_target_rail_and_classic_fallback():
    assert "document.documentElement.dataset.ui==='tomb'&&!singleTarget" in WIZARD
    assert 'experimentalPlayerAttackTargetRail(targets,stage,preferredTargetId,targetSideLabel)' in WIZARD
    assert '<select id="combatTarget">' in WIZARD
    assert 'singleTarget' in WIZARD and 'readonly-select' in WIZARD

def test_images_names_and_projected_wounds():
    for snippet in ('projectedNpoWounds(npo.id,stage)','experimentalNecronPortraitMarkup(npo,','escapeHtml(npoName(npo))','player-combat-target-wounds','data-player-combat-target=','role="radiogroup"','role="radio"','aria-checked='):
        assert snippet in RAIL
    assert 'experimental-roster-detail' not in RAIL

def test_click_arrow_and_selection_update_hidden_input():
    for snippet in ("const buttons=$$('[data-player-combat-target]',modal)","targetSelect.value=id;","button.classList.toggle('selected',selected)","button.setAttribute('aria-checked',String(selected))","['ArrowLeft','ArrowRight','Home','End']","nextButton.scrollIntoView({block:'nearest',inline:'nearest'})","renderChoices();"):
        assert snippet in WIZARD
    assert 'data-dialog-focus' in WIZARD

def test_legacy_weapon_and_continue_flow_still_in_place():
    for snippet in ('id="playerWeaponSelect"',"const weaponSelect=$('#playerWeaponSelect');","weaponSelect.addEventListener('change',renderChoices)","$('#openCombatResolution').disabled=!target||!weapon;","$('#openCombatResolution').onclick=()=>{",'guardianProtocolCheck','showSecondaryTargetCheck','resumeCombatAfterWeaponRuleCheck'):
        assert snippet in WIZARD

def test_mobile_horizontal_scroll_stays_within_rail():
    styles=CSS.split('/* Experimental player-attack Necron target picker.',1)[1]
    assert 'overflow-x:auto' in styles
    assert 'scroll-snap-type:x proximity' in styles
    assert 'html[data-ui="tomb"] .player-combat-target-rail' in styles
    assert '@media(max-width:600px)' in styles
