"""v10.0.209/213: one Strike/Block icon per heading in both Solo modes."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_experimental_headings_have_one_symbol_and_option_buttons_have_none():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function experimentalActionFirstFightHtml(');
const end=source.indexOf('  function bindExperimentalActionFirstFight(',start);
assert(start>=0&&end>start);
const make=new Function('ctx','with(ctx){'+source.slice(start,end)+'return experimentalActionFirstFightHtml;}');
const fight={attacker:{side:'player',label:'Gunner'},defender:{side:'npo',label:'Necron Warrior'}};
const actions={
  strikes:[
    {success:{id:'n1',kind:'normal'},damage:3},
    {success:{id:'c1',kind:'critical'},damage:4}
  ],
  blocks:[
    {blocker:{id:'c1',kind:'critical'},target:{id:'enemy-c',kind:'critical'}},
    {blocker:{id:'n1',kind:'normal'},target:{id:'enemy-n',kind:'normal'}}
  ]
};
let experimental=true,pvp=false;
const ctx={
  experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
  otherFightRole:r=>r==='attacker'?'defender':'attacker',
  experimentalFightPoolHtml:()=>'<div class="participant"></div>',
  fightLastResolutionHtml:()=>'<div class="fight-exchange-history"></div>',
  experimentalFightStrikeAdvice:()=>'',titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
  escapeHtml:String,experimentalFightBlockUnavailableHtml:()=>'<section class="experimental-fight-block-unavailable"></section>'
};
const render=(capacity=1)=>make(ctx)(fight,'attacker',fight.attacker,actions,capacity);
const count=(s,p)=>(s.match(p)||[]).length;
let preview=render();
assert.equal(count(preview,/class="experimental-fight-heading-symbol"/g),2);
assert.equal(count(preview,/class="experimental-fight-option-icon"/g),0);
assert.equal(count(preview,/class="experimental-fight-option-radio"/g),4);
assert.equal(count(preview,/data-exp-fight-choice="strike"/g),2);
assert.equal(count(preview,/data-exp-fight-choice="block"/g),2);
assert(preview.includes('<strong>STRIKE</strong></span>'));
assert(preview.includes('<strong>BLOCK</strong></span>'));
assert(preview.includes('data-fight-block-target="enemy-c"'));
assert(preview.includes('id="confirmExperimentalFightChoice" disabled'));
assert(preview.includes('experimental-fight-versus'));
assert(preview.includes('fight-exchange-history'));
const firstHeading=preview.split('<h5 id="fightStrikeHeading">')[1].split('</h5>')[0];
const secondHeading=preview.split('<h5 id="fightBlockHeading">')[1].split('</h5>')[0];
assert(firstHeading.includes('M21.2 2.8'),'Sword glyph at Strike heading');
assert(!firstHeading.includes('<small>') && !firstHeading.includes('Deal damage'),'No redundant Strike subtitle');
assert(secondHeading.includes('M12 5.5 6.3 7.7'),'Original half-filled shield at Block heading');
assert(!secondHeading.includes('<small>') && !secondHeading.includes('Cancel an enemy attack success'),'No redundant Block subtitle');
assert(preview.includes('Cancel 1 enemy Normal Success'),'Block choices still explain consequences');
preview=render(2);
assert(preview.includes('<strong>BLOCK · SHIELD</strong>'),'Shield capacity kept');
assert(!preview.includes('<small>Cancel an enemy attack success</small>'));
assert(preview.includes('Deal 3 damage'));
assert(preview.includes('Shield: choose up to 2 enemy successes'));
actions.blocks=[];
preview=render();
assert.equal(count(preview,/class="experimental-fight-heading-symbol"/g),1);
assert(preview.includes('class="experimental-fight-block-unavailable"'));
actions.blocks=[{blocker:{id:'n1',kind:'normal'},target:{id:'enemy-n',kind:'normal'}}];
experimental=false;pvp=false;
const standard=render();
assert.equal(count(standard,/class="experimental-fight-heading-symbol"/g),2,'Standard uses the promoted header icons');
assert.equal(count(standard,/class="experimental-fight-option-icon"/g),0,'No repeated icons in Standard');
experimental=true;pvp=false;
assert.equal(render(),standard,'Standard and Experimental Solo headers match');
pvp=true;
const versus=render();
assert.equal(count(versus,/class="experimental-fight-heading-symbol"/g),0,'PvP remains unchanged');
assert.equal(count(versus,/class="experimental-fight-option-icon"/g),3,'PvP retains original icons');
assert(versus.includes('<h5 id="fightStrikeHeading">STRIKE <span>Deal damage</span></h5>'));
assert(versus.includes('<h5 id="fightBlockHeading">BLOCK <span>Cancel an enemy attack success</span></h5>'));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_icon_header_styles_only_in_experimental_duel():
    block = CSS.split("/* v10.0.209: In Experimental Solo Fight", 1)[1].split("/* v10.0.211: Flatten Experimental Fight history", 1)[0]
    assert 'html[data-ui="tomb"] .is-duel-layout' in block
    assert '.experimental-fight-heading-symbol' in block
    assert '.experimental-fight-heading-label' in block
    assert 'width:20px;' in block
    assert '.experimental-fight-option-radio' not in block
    assert '.fight-exchange-card' not in block
    assert '.experimental-fight-pool' not in block


def test_version_and_js_syntax():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 209)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    sw = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in sw
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    check = subprocess.run(["node", "--check", "app.js"], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert check.returncode == 0, check.stderr
