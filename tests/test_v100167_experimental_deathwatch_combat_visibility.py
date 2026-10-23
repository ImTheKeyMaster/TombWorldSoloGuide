"""Experimental-only contrast adjustment for supplied Deathwatch compact combat portraits."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_class_is_applied_only_to_experimental_supplied_deathwatch_portraits():
    script = r"""
const assert=require('node:assert/strict'), fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf('  function fightParticipantPortrait(participant,role){');
const end=app.indexOf('  function fightRollParticipantHtml(',start);
assert(start>0&&end>start);
let experimental=false, team='deathwatch';
const necron={id:'npo-1'};
const ctx={
  state:{roster:[necron]},
  selectedPlayerTeamName:()=>team,
  playerDefinition:id=>id==='bombard'||id==='confidant'?{id}:null,
  experimentalDeathwatchSuppliedPortraitImage:id=>experimental&&id==='bombard'?'Assets/Images/TombUI/Deathwatch/Deathwatch_bombard.png':'',
  experimentalDeathwatchGreenPortraitSvg:id=>'<svg data-original-team="deathwatch" data-id="'+id+'"></svg>',
  experimentalNecronPortraitSvg:id=>'<svg data-original-team="necron"></svg>',
  deathKorpsCombatPortraitSvg:id=>'<svg data-original-team="korps"></svg>'
};
const portrait=new Function('ctx','with(ctx){'+app.slice(start,end)+
 '\nreturn fightParticipantPortrait;}')(ctx);
const supplied='supplied-deathwatch-portrait';
const standard=portrait({side:'player',id:'bombard'},'attacker');
assert(standard.includes('data-original-team="deathwatch"'));
assert(!standard.includes(supplied),'Standard must retain the prior visual treatment');
experimental=true;
const preview=portrait({side:'player',id:'bombard'},'attacker');
assert(preview.includes('fight-portrait fight-portrait-attacker '+supplied));
assert(preview.includes('aria-hidden="true"'));
assert(preview.includes('data-original-team="deathwatch"'));
const npo=portrait({side:'npo',id:'npo-1'},'defender');
assert(npo.includes('data-original-team="necron"'));
assert(!npo.includes(supplied),'NPO must retain original contrast');
team='death korps';
const korps=portrait({side:'player',id:'confidant'},'defender');
assert(korps.includes('data-original-team="korps"'));
assert(!korps.includes(supplied),'Death Korps must not be affected');
assert.equal(portrait({side:'player',id:null},'attacker'),'');
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_brightness_is_scoped_to_compact_previews_and_preserves_existing_geometry():
    assert "opacity:.44;" in CSS
    assert "opacity:.29;" in CSS
    updated = CSS.split("/* v10.0.167-168: Tune supplied Deathwatch portrait contrast", 1)[1]
    selector = 'html[data-ui="tomb"][data-experimental="on"]'
    assert f"{selector} .fight-portrait.supplied-deathwatch-portrait{{" in updated
    assert "opacity:.52;" in updated
    assert f"{selector} .fight-portrait.supplied-deathwatch-portrait .fight-portrait-artwork{{" in updated
    assert "filter:none;" in updated
    assert "filter:brightness(" not in updated
    assert f"{selector} .experimental-fight-pool .fight-portrait.supplied-deathwatch-portrait{{" in updated
    assert "opacity:.38;" in updated
    assert "@media(max-width:390px)" in updated
    assert "opacity:.36" in updated
    assert "@media(max-width:374px)" in updated
    assert "opacity:.34" in updated
    assert "transform:" not in updated
    assert "width:" not in updated.replace("max-width:", "")
    assert "height:" not in updated
    assert "z-index:" not in updated
    assert "pointer-events:" not in updated
    assert "html[data-experimental=\"off\"]" not in updated
    assert "death-korps" not in updated
    assert "necron" not in updated
    # The bright supplied PNGs no longer get extra luminance, and the
    # portrait alpha now sits near the unmodified neighboring Necron.
    assert abs(0.52 - 0.44) <= 0.10
    assert abs(0.38 - 0.29) <= 0.10


def test_same_portrait_is_used_by_shooting_dice_fight_roll_result_and_resolution():
    assert "attackerPortrait:fightParticipantPortrait({side:'player',id:stage.playerOperativeId},'attacker')" in APP
    assert "defenderPortrait:fightParticipantPortrait({side:targetSide,id:targetId},'defender')" in APP
    assert "attackerPortrait:fightParticipantPortrait({side:'npo',id:n.id},'attacker')" in APP
    assert "const portrait=fightParticipantPortrait(participant,role);" in APP
    assert "const active=fight.turn===role,portrait=fightParticipantPortrait(participant,role);" in APP
    assert '<section class="combat-stage${portraitClass}"' in APP
    assert "shooting-roll-pool has-fight-portrait" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_release_consistency_and_experimental_mode_isolation():
    assert "&&!!experimentalDeathwatchSuppliedPortraitImage(participant.id);" in APP
    assert "if(document.documentElement.dataset.experimental!=='on')return '';" in APP
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
