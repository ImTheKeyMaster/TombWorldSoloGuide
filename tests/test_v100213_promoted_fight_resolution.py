"""v10.0.213 approved Fight Resolution is identical in Standard and Experimental Solo."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_solo_duel_and_action_history_have_exact_parity_and_pvp_is_unchanged():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function experimentalActionFirstFightHtml(');
const end=source.indexOf('  function bindExperimentalActionFirstFight(',start);
const historyStart=source.indexOf('  function fightResolutionRecordHtml(');
const historyEnd=source.indexOf('  function equivalentRemainingFightStrikes(',historyStart);
let experimental=false,pvp=false;
const ctx={
 document:{documentElement:{dataset:{ui:'tomb',experimental:'off'}}},
 experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 experimentalFightPoolHtml:(f,r)=>'<div class="participant">'+r+'</div>',
 experimentalFightStrikeAdvice:()=>'',titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
 escapeHtml:String,experimentalFightBlockUnavailableHtml:()=>'<section class="experimental-fight-block-unavailable"></section>'
};
const history=new Function('ctx','with(ctx){'+source.slice(historyStart,historyEnd)+'return fightLastResolutionHtml;}')(ctx);
const make=new Function('ctx','with(ctx){'+source.slice(start,end)+'return experimentalActionFirstFightHtml;}')(Object.assign(ctx,{fightLastResolutionHtml:history}));
const fight={
 attacker:{side:'player',label:'Gunner'},defender:{side:'npo',label:'Canoptek Scarab Swarm'},
 history:[
  {role:'defender',type:'strike',successKind:'normal',damage:1,before:15,after:14},
  {role:'attacker',type:'block',successKind:'critical',blockedKinds:['normal']},
  {role:'attacker',type:'strike',successKind:'normal',damage:3,before:7,after:4}
 ]
};
const actions={strikes:[{success:{id:'normal',kind:'normal'},damage:3}],
 blocks:[{blocker:{id:'critical',kind:'critical'},target:{id:'enemy',kind:'normal'}}]};
const render=()=>make(fight,'attacker',fight.attacker,actions,1);
const standard=render(),standardHistory=history(fight);
assert(standard.includes('is-duel-layout'));
assert(standard.includes('experimental-fight-versus'));
assert(standard.includes('experimental-fight-choice-columns'));
assert(standard.includes('class="experimental-fight-heading-symbol"'));
assert(!standard.includes('class="experimental-fight-option-icon"'));
assert(!standard.includes('experimental-fight-step-number'));
assert.equal((standardHistory.match(/class="fight-exchange-number"/g)||[]).length,3);
assert.deepEqual([...standardHistory.matchAll(/aria-label="Action (\d+):/g)].map(x=>x[1]),['1','2','3']);
assert(!standardHistory.includes('fight-exchange-group'));
assert(standardHistory.includes('7 → 4 wounds'));
experimental=true;ctx.document.documentElement.dataset.experimental='on';
assert.equal(render(),standard,'Both Solo modes must render precisely the same Fight chooser');
assert.equal(history(fight),standardHistory,'Both Solo modes must render the same timeline');
pvp=true;
assert(!render().includes('is-duel-layout'));
assert(!render().includes('experimental-fight-choice-columns'));
assert(!history(fight).includes('fight-exchange-history'));
assert(history(fight).includes('fight-resolution-record'),'PvP keeps its own history presentation');
assert.equal(fight.history.length,3,'No action history mutation');
"""
    run=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert run.returncode==0, run.stderr or run.stdout


def test_approved_css_has_no_experimental_toggle_dependency():
    shared_start = CSS.index("/* v10.0.199/213: Shared Solo Fight action history")
    shared_end = CSS.index("/* v10.0.203: Explain automatic residual Fight strikes", shared_start)
    shared_base = CSS[shared_start:shared_end]
    modern_start = CSS.index("/* v10.0.206/213: Approved Solo Fight Resolution design promoted to Standard.")
    modern = CSS[modern_start:]
    assert '[data-experimental="on"]' not in shared_base
    assert '[data-experimental="on"]' not in modern
    assert 'html[data-ui="tomb"] .is-duel-layout' in shared_base
    assert 'html[data-ui="tomb"] .is-duel-layout' in modern
    assert '.fight-exchange-history>.fight-exchange-card' in modern
    assert 'flex:0 0 clamp(94px,26vw,115px);' in modern
    assert '.experimental-fight-choice-columns' in modern
    assert 'experimental-fight-versus' in modern
    assert 'background:transparent;' in modern
    assert "const duelPreview=!isPvpMode();" in APP
    assert "if(document.documentElement.dataset.ui==='tomb'&&!isPvpMode())" in APP
    assert "if(!isPvpMode())exchangeHistory.scrollLeft=exchangeHistory.scrollWidth-exchangeHistory.clientWidth;" in APP
    assert "function experimentalFeaturesEnabled(){" in APP, "Experimental must remain available for future features"


def test_version_and_offline_assets_are_consistent():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,0,213)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    sw=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in sw
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
