from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
HELPER=APP.split('function combatParticipantPortrait(',1)[1].split('function showSharedCombatResolutionScreen(',1)[0]
SHARED=APP.split('function showSharedCombatResolutionScreen(',1)[1].split('function showCombatResumeRecovery(',1)[0]


def test_current_release_surfaces():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in HTML


def test_both_pills_receive_portraits_and_keep_other_fields():
    assert '<div class="combat-participant-pill"><small>Attacker</small>' in SHARED
    assert '<div class="combat-participant-pill"><small>Defender</small>' in SHARED
    assert '${attackerPortrait}' in SHARED and '${defenderPortrait}' in SHARED
    for field in ["Attack type","Weapon","Attack","Defense"]:
        assert field in SHARED


def test_reuses_necron_and_deathwatch_assets_without_new_dependencies():
    assert "experimentalNecronPortraitSvg(operative," in HELPER
    assert "experimentalDeathwatchGreenPortraitSvg(operative," in HELPER
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in HELPER
    assert "playerDefinition(operative)" in HELPER
    assert "if(!portrait)return '';" in HELPER
    assert 'aria-hidden="true"' in HELPER


def test_both_player_and_necron_combat_call_sites_pass_correct_models():
    assert "attackerPortrait:combatParticipantPortrait('npo',n,'attacker')" in APP
    assert "defenderPortrait:combatParticipantPortrait(targetSide,targetSide==='player'?target.id:target,'defender')" in APP
    assert "attackerPortrait:combatParticipantPortrait('player',stage.playerOperativeId,'attacker')" in APP
    assert "defenderPortrait:combatParticipantPortrait(targetSide,targetSide==='player'?targetId:target,'defender')" in APP


def test_artwork_clips_inside_pills_without_affecting_grid_heights():
    styles=CSS.split('/* Combat participant portraits:',1)[1]
    assert 'position:relative' in styles
    assert 'overflow:hidden' in styles
    assert 'position:absolute' in styles
    assert 'top:-3px' in styles and 'right:-5px' in styles
    assert 'max-width:78%' in styles
    assert 'facing-left .combat-participant-artwork' in styles
    assert 'transform:scaleX(-1)' in styles
    assert 'height:' not in styles.split('combat-summary-grid .combat-participant-pill{',1)[1].split('}',1)[0]


def test_no_changes_to_combat_mechanics():
    assert "showModal(title," in SHARED
    assert "id=\"automaticCombat\"" in SHARED
    assert "id=\"combatResults\"" in SHARED
    assert "id=\"${continueId}\" disabled" in SHARED
