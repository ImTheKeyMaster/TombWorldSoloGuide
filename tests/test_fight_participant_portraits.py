from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
INDEX=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
HELPER=APP.split('function fightParticipantPortrait(participant,role)',1)[1].split('function fightRollParticipantHtml(fight,role,animate)',1)[0]
ROLL=APP.split('function fightRollParticipantHtml(fight,role,animate)',1)[1].split('function fightWeaponRulesHtml(fight)',1)[0]
RESULT=APP.split('function fightResultParticipantHtml(participant,role)',1)[1].split('function acknowledgeFightResult(fight)',1)[0]
COMPLETE=APP.split('function renderFightResult(fight)',1)[1].split('function finishFight(fight)',1)[0]

def test_versions_match():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in INDEX

def test_correct_existing_images_using_participant_side_and_id():
    assert "participant.side==='npo'" in HELPER
    assert "state.roster.find(item=>item.id===participant.id)" in HELPER
    assert 'experimentalNecronPortraitSvg(npo,' in HELPER
    assert "participant.side==='player'" in HELPER
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in HELPER
    assert 'playerDefinition(participant.id)' in HELPER
    assert 'experimentalDeathwatchGreenPortraitSvg(participant.id,' in HELPER
    assert "return artwork?" in HELPER
    assert 'aria-hidden="true"' in HELPER

def test_both_fight_roll_and_fight_result_render_portraits():
    assert "fightParticipantPortrait(participant,role)" in ROLL
    assert "fightParticipantPortrait(participant,role)" in RESULT
    assert "has-fight-portrait" in ROLL
    assert "has-fight-portrait" in RESULT
    assert "${portrait}<small>" in ROLL
    assert "${portrait}<h3>" in RESULT
    assert "data-fight-roll-dice" in ROLL
    assert 'class="fight-roll-result"' in ROLL
    assert "participant.damageDealt" in RESULT
    assert "participant.before" in RESULT and "participant.after" in RESULT
    assert "fightResultParticipantHtml(result.participants.attacker,'attacker')" in COMPLETE
    assert "fightResultParticipantHtml(result.participants.defender,'defender')" in COMPLETE

def test_art_behind_content_clipped_and_gated_by_mode_without_height_changes():
    style=CSS.split('/* Decorative upper-body portraits inside Fight Roll and Fight Result participant cards.',1)[1]
    assert 'html:not([data-ui="tomb"]) .fight-portrait{display:none}' in style
    assert '.fight-roll-pool.has-fight-portrait' in style
    assert '.fight-result-card.has-fight-portrait' in style
    assert 'position:relative' in style and 'overflow:hidden' in style
    assert 'position:absolute' in style
    assert 'z-index:0' in style and 'z-index:1' in style
    assert 'pointer-events:none' in style
    assert 'transform:scale(1.3)' in style
    assert 'text-shadow' in style
    assert '@media(max-width:600px)' in style
    assert 'min-height:' not in style
