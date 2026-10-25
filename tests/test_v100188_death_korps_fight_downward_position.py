"""Only Death Korps Fight images move downward, with bases still aligned."""

from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_death_korps_class_only_on_the_death_korps_participant():
    js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const a=app.indexOf('  function fightParticipantPortrait(participant,role){');
const b=app.indexOf('  function fightRollParticipantHtml(',a);
assert(a>0&&b>a);
let team='death korps';
const ctx={
 state:{roster:[{id:'necron-1',type:'Necron Warrior'}]},
 selectedPlayerTeamName:()=>team,
 playerDefinition:id=>({id}),
 deathKorpsPortraitImage:id=>id==='trooper-2'?'korps.png':'',
 deathwatchPortraitImage:id=>id==='disruptor'?'deathwatch.png':'',
 deathKorpsCombatPortraitSvg:()=>'<img src="korps.png">',
 deathwatchPortraitSvg:()=>'<img src="watch.png">',
 experimentalNecronPortraitSvg:()=>'<img src="necron.webp">'
};
const portrait=new Function('ctx','with(ctx){'+app.slice(a,b)+'\nreturn fightParticipantPortrait;}')(ctx);
const korps=portrait({side:'player',id:'trooper-2'},'attacker');
assert.match(korps,/fight-portrait-attacker death-korps-portrait/);
team='deathwatch';
const dw=portrait({side:'player',id:'disruptor'},'attacker');
assert.match(dw,/fight-portrait-attacker deathwatch-portrait/);
assert.doesNotMatch(dw,/death-korps-portrait/);
const necron=portrait({side:'npo',id:'necron-1'},'defender');
assert.match(necron,/necron.webp/);
assert.doesNotMatch(necron,/death-korps-portrait|deathwatch-portrait/);
"""
    result=subprocess.run(["node","-e",js],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_new_framing_supersedes_tiny_death_korps_cutouts_without_moving_base():
    tail=CSS.split("/* v10.0.189: Keep Fight Resolution",1)[1]
    for selector,size in (
        ('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait.death-korps-portrait','width:min(76%,118px)'),
        ('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait.death-korps-portrait','width:min(115%,205px)'),
    ):
        blocks=re.findall(re.escape(selector)+r"\\s*\\{([^}]*)\\}",tail)
        assert len(blocks)==1
        assert size in blocks[0]
    assert "height:calc(100% - 14px)" not in CSS
    assert "height:calc(100% - 18px)" not in CSS
    assert "margin-top:14px" not in tail
    assert "margin-top:18px" not in tail
    assert "/* v10.0.186: Fight Resolution miniature bases" in CSS
    assert "/* v10.0.187: Align both Fight Result miniature bases" in CSS
    assert "width:135%;" in CSS
    assert "width:140%;" in CSS
    assert "width:145%;" in CSS

def test_release_consistency_and_state_unchanged():
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"V{CURRENT_APP_VERSION}" in html
    assert f"app.js?v={CURRENT_APP_VERSION}" in html
    assert f"styles.css?v={CURRENT_APP_VERSION}" in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
