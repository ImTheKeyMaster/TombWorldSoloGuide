"""Regression tests for the approved Deathwatch combat portrait contrast."""

from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_deathwatch_style_applies_in_both_modes_without_affecting_necrons_or_korps():
    js = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf('  function fightParticipantPortrait(participant,role){');
const end=app.indexOf('  function fightRollParticipantHtml(',start);
assert(start>0&&end>start);
let team='deathwatch';
const ctx={
 state:{roster:[{id:'npo-1'}]},
 selectedPlayerTeamName:()=>team,
 playerDefinition:id=>({id}),
 deathwatchPortraitImage:id=>id==='bombard'?'Assets/Images/TombUI/Deathwatch/Deathwatch_bombard.png':'',
 deathwatchPortraitSvg:id=>'<svg data-team="deathwatch" data-id="'+id+'"></svg>',
 experimentalNecronPortraitSvg:()=>'<svg data-team="necron"></svg>',
 deathKorpsCombatPortraitSvg:()=>'<svg data-team="korps"></svg>'
};
const draw=new Function('ctx','with(ctx){'+app.slice(start,end)+'\nreturn fightParticipantPortrait;}')(ctx);
const deathwatch=draw({side:'player',id:'bombard'},'attacker');
assert(deathwatch.includes('fight-portrait-attacker deathwatch-portrait'));
assert(deathwatch.includes('data-team="deathwatch"'));
assert(deathwatch.includes('aria-hidden="true"'));
const npo=draw({side:'npo',id:'npo-1'},'defender');
assert(npo.includes('data-team="necron"'));
assert(!npo.includes('deathwatch-portrait'));
team='death korps';
const korps=draw({side:'player',id:'confidant'},'defender');
assert(korps.includes('data-team="korps"'));
assert(!korps.includes('deathwatch-portrait'));
assert.equal(draw({side:'player',id:null},'attacker'),'');
"""
    result = subprocess.run(["node", "-e", js], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_final_brightness_is_unconditional_and_changes_no_geometry():
    css = CSS.split("/* v10.0.169: Approved Deathwatch combat portrait transparency", 1)[1].split('/* v10.0.171: Preview a consistent', 1)[0]
    selector = 'html[data-ui="tomb"]'
    assert f"{selector} .fight-portrait.deathwatch-portrait{{" in css
    assert "opacity:.52;" in css
    assert f"{selector} .experimental-fight-pool .fight-portrait.deathwatch-portrait{{" in css
    assert "opacity:.38;" in css
    assert "@media(max-width:390px)" in css and "opacity:.36" in css
    assert "@media(max-width:374px)" in css and "opacity:.34" in css
    assert "[data-experimental=" not in css
    assert "filter:brightness(" not in css
    assert "filter:none" not in css
    assert "transform:" not in css
    assert "width:" not in css.replace("max-width:", "")
    assert "height:" not in css
    assert "z-index:" not in css
    assert "opacity:.44;" in CSS  # Necron and other faction baseline is unchanged
    assert "opacity:.29;" in CSS


def test_same_portrait_flows_to_shooting_fight_result_and_resolution():
    assert "attackerPortrait:fightParticipantPortrait({side:'player',id:stage.playerOperativeId},'attacker')" in APP
    assert "defenderPortrait:fightParticipantPortrait({side:targetSide,id:targetId},'defender')" in APP
    assert "const portrait=fightParticipantPortrait(participant,role);" in APP
    assert "const active=fight.turn===role,portrait=fightParticipantPortrait(participant,role);" in APP
    assert "shooting-roll-pool has-fight-portrait" in APP
    assert "&&!!deathwatchPortraitImage(participant.id);" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_version_and_independent_experimental_toggle():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
