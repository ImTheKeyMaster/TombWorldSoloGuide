"""Fight portrait adjustment is Death Korps-only and preserves other factions."""

from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_fight_portrait_class_is_only_added_for_death_korps():
    js = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const a=src.indexOf('  function fightParticipantPortrait(participant,role){');
const b=src.indexOf('  function fightRollParticipantHtml(',a);
assert(a>0&&b>a);
let team='death korps';
const ctx={
 state:{roster:[{id:'necron-1',type:'Necron Warrior'}]},
 selectedPlayerTeamName:()=>team,
 playerDefinition:id=>({id}),
 deathKorpsPortraitImage:id=>id==='trooper-2'?'Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_2.png':'',
 deathwatchPortraitImage:id=>id==='disruptor'?'Assets/Images/TombUI/Deathwatch/Deathwatch_disruptor.png':'',
 deathKorpsCombatPortraitSvg:()=>'<img src="korps.png">',
 deathwatchPortraitSvg:()=>'<img src="watch.png">',
 experimentalNecronPortraitSvg:()=>'<img src="necron.webp">'
};
const portrait=new Function('ctx','with(ctx){'+src.slice(a,b)+'\nreturn fightParticipantPortrait;}')(ctx);
const korps=portrait({side:'player',id:'trooper-2'},'attacker');
assert.match(korps,/fight-portrait-attacker death-korps-portrait/);
assert.match(korps,/korps.png/);
assert.doesNotMatch(korps,/deathwatch-portrait/);
team='deathwatch';
const watch=portrait({side:'player',id:'disruptor'},'attacker');
assert.match(watch,/fight-portrait-attacker deathwatch-portrait/);
assert.doesNotMatch(watch,/death-korps-portrait/);
const necron=portrait({side:'npo',id:'necron-1'},'defender');
assert.match(necron,/fight-portrait-defender/);
assert.doesNotMatch(necron,/death-korps-portrait|deathwatch-portrait/);
assert.match(necron,/necron.webp/);
"""
    result = subprocess.run(["node", "-e", js], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_css_changes_only_death_korps_and_lowers_figure():
    tail = CSS.split("/* v10.0.187: Move ONLY Death Korps miniature portraits lower.", 1)[1]
    selector = 'html[data-ui="tomb"] .experimental-fight-pool .fight-portrait.death-korps-portrait'
    r = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", tail)
    assert len(r) == 1
    assert "bottom:-12px;" in r[0]
    for target in (
        selector + ' .fight-portrait-artwork',
        'html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait.death-korps-portrait .fight-portrait-artwork',
    ):
        matches = re.findall(re.escape(target) + r"\s*\{([^}]*)\}", tail)
        assert len(matches) == 1
        assert "object-fit:contain" in matches[0]
        assert "object-position:center bottom" in matches[0]
        assert "transform:none" in matches[0]
    assert ".experimental-fight-pool .fight-portrait{" not in tail
    assert ".fight-result-card .fight-portrait{" not in tail
    assert ".experimental-necron-framed-svg{" not in tail
    assert ".deathwatch-portrait{" not in tail
    assert "width:135%;" in CSS  # Approved smaller Death Korps activation portrait
    assert "width:140%;" in CSS
    assert "width:145%;" in CSS


def test_version_and_no_gameplay_mutations():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
