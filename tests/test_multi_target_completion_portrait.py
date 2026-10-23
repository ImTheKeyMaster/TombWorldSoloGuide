from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
INDEX=(ROOT/'index.html').read_text(encoding='utf-8')
WORKER=(ROOT/'service-worker.js').read_text(encoding='utf-8')
HELPER=APP.split('function multiTargetSummaryPortrait(',1)[1].split('function renderAttackSummary(',1)[0]
SUMMARY=APP.split('function renderAttackSummary(',1)[1].split('function renderCombatResolution(',1)[0]
COMPLETE=APP.split('function showMultiTargetAttackSummary(',1)[1].split('function applySevereToAttackDice(',1)[0]

def test_versions_match():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in INDEX

def test_portrait_is_experimental_only_and_uses_damaged_target_identity():
    assert "document.documentElement.dataset.ui!=='tomb'" in HELPER
    assert 'result.targetId' in HELPER
    assert 'result.side||result.defenderSide' in HELPER
    assert 'sequence?.orderedTargets?' in HELPER
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in HELPER
    assert 'playerDefinition(id)' in HELPER
    assert 'deathwatchPortraitSvg(id,' in HELPER
    assert "state.roster.find(item=>item.id===id)" in HELPER
    assert 'experimentalNecronPortraitSvg(npo,' in HELPER
    assert 'aria-hidden="true"' in HELPER

def test_only_multi_target_complete_screen_adds_artwork():
    assert "renderAttackSummary(result,{portraitHtml:multiTargetSummaryPortrait(result,sequence)})" in COMPLETE
    assert 'portraitHtml?' in SUMMARY
    assert 'has-target-portrait' in SUMMARY
    assert '${portraitHtml}' in SUMMARY
    assert 'class="attack-confirmation-stats"' in SUMMARY
    assert 'attack.damage' in SUMMARY and 'attack.before' in SUMMARY and 'attack.after' in SUMMARY
    assert 'id="continueMultiTargetSummary"' in COMPLETE

def test_image_behind_damage_wounds_with_no_impact_on_pill_layout():
    block=CSS.split('/* Experimental Blast/Torrent completion:',1)[1]
    assert 'position:absolute' in block
    assert 'top:-21px' in block and 'right:-12px' in block
    assert 'transform:scale(1.3)' in block
    assert 'z-index:0' in block and 'z-index:1' in block
    assert 'background:rgba(6,24,15,.87)' in block
    assert '@media(max-width:600px)' in block


def test_only_scarab_swarm_receives_higher_portrait_position():
    assert "if(portrait&&npo.type==='Canoptek Scarab Swarm')" in HELPER
    assert "scarabClass=' scarab-swarm-portrait'" in HELPER
    assert 'blast-result-portrait${scarabClass}' in HELPER
    assert "scarabClass" not in SUMMARY
    assert 'html[data-ui="tomb"] .blast-result-portrait.scarab-swarm-portrait{top:-66px}' in CSS
    assert "html[data-ui=\"tomb\"] .blast-result-portrait{width:186px;height:226px;right:-10px;top:-17px}" in CSS
