"""v10.1.6: Solo Fight Strike/Block option pills have 6px inner clearance."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_padding_preserves_both_fight_choices_and_mode_parity():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function experimentalActionFirstFightHtml(');
const b=s.indexOf('  function bindExperimentalActionFirstFight(',a);
assert(a>=0&&b>a);
let pvp=false;
const ctx={
 isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 experimentalFightPoolHtml:()=>'<section></section>',
 fightLastResolutionHtml:()=>'',experimentalFightStrikeAdvice:()=>'',escapeHtml:String,
 titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
 experimentalFightBlockUnavailableHtml:()=>'<div></div>'
};
const make=new Function('ctx','with(ctx){'+s.slice(a,b)+'return experimentalActionFirstFightHtml;}')(ctx);
const fight={attacker:{side:'player',label:'Demolisher'},defender:{side:'npo',label:'Necron Warrior'}};
const actions={strikes:[{success:{id:'n',kind:'normal'},damage:6}],
 blocks:[{blocker:{id:'n',kind:'normal'},target:{id:'enemy',kind:'normal'}}]};
const solo=make(fight,'attacker',fight.attacker,actions,1);
assert(solo.includes('experimental-fight-choice-screen is-duel-layout'));
assert.equal((solo.match(/class="experimental-fight-choice-group"/g)||[]).length,2);
assert.equal((solo.match(/class="experimental-fight-option-list"/g)||[]).length,2);
assert.equal((solo.match(/class="experimental-fight-option"/g)||[]).length,2);
assert(solo.includes('data-exp-fight-choice="strike"'));
assert(solo.includes('data-exp-fight-choice="block"'));
assert(solo.includes('id="confirmExperimentalFightChoice" disabled'));
pvp=true;
const pvpHtml=make(fight,'attacker',fight.attacker,actions,1);
assert(!pvpHtml.includes('is-duel-layout'),'PvP must not receive this layout change');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_six_pixel_inset_fits_glow_and_focus_on_small_and_large_screens():
    section=CSS.split("/* v10.1.6: Give Solo Fight Strike/Block",1)[1]
    card='html[data-ui="tomb"] .is-duel-layout .experimental-fight-choice-columns>.experimental-fight-choice-group'
    option_list=card+">.experimental-fight-option-list"
    header=card+">h5"
    assert card+"{\n  padding:9px 0 0;\n}" in section
    assert header+"{\n  padding-inline:9px;\n}" in section
    assert option_list+"{\n  box-sizing:border-box;\n  padding:6px;\n}" in section
    assert "@media(max-width:360px){" in section
    assert card+"{\n    padding:7px 0 0;\n  }" in section
    assert "padding-inline:7px;" in section
    assert "[data-experimental" not in section
    assert ":not(.is-duel-layout)" not in section
    # A 1px selected glow and a 2px focus outline with 3px offset
    # both fit inside the 6px option-list inset.
    assert "box-shadow:0 0 0 1px rgba(118,245,168,.2)" in CSS
    assert "outline:2px solid var(--green);outline-offset:3px;" in CSS
    assert 1 < 6 and 2 + 3 < 6


def test_release_offline_assets_are_consistent():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,1,6)
    index=(ROOT / "index.html").read_text(encoding="utf-8")
    worker=(ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"styles.css?v={CURRENT_APP_VERSION}" in index
    assert f"app.js?v={CURRENT_APP_VERSION}" in index
    assert f"V{CURRENT_APP_VERSION}" in index
