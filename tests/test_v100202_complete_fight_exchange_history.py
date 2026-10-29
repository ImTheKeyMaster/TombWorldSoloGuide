"""v10.0.202: Experimental displays all Fight exchanges with bounded mobile history."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_complete_exchange_history_and_saved_fight_rendering():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function fightResolutionRecordHtml(');
const end=source.indexOf('  function equivalentRemainingFightStrikes(',start);
let experimental=true, pvp=false;
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),escapeHtml:String
};
const render=new Function('ctx','with(ctx){'+source.slice(start,end)+'return fightLastResolutionHtml;}')(ctx);
const history=[
 {role:'defender',type:'strike',successKind:'normal',damage:2,before:12,after:10},
 {role:'attacker',type:'strike',successKind:'critical',damage:6,before:9,after:3},
 {role:'defender',type:'block',successKind:'normal',blockedKinds:['normal']},
 {role:'attacker',type:'strike',successKind:'normal',damage:4,before:10,after:6},
 {role:'defender',type:'strike',successKind:'normal',damage:2,before:10,after:8},
];
const fight={attacker:{side:'player',label:'Sergeant'},defender:{side:'npo',label:'Macrocyte'},history:[]};
assert.equal(render(fight),'');
fight.history=JSON.parse(JSON.stringify(history)); // simulate a resumed saved fight
let html=render(fight);
assert(html.includes('>EXCHANGES<')&&!html.includes('>LAST EXCHANGE<'));
assert.deepEqual([...html.matchAll(/aria-label="Exchange (\d+)"/g)].map(x=>x[1]),['1','2','3']);
assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,5);
assert(html.indexOf('6 DAMAGE')<html.indexOf('4 DAMAGE'));
assert.equal((html.match(/class="fight-exchange-group is-latest"/g)||[]).length,1);
assert(html.indexOf('fight-exchange-npo')<html.indexOf('fight-exchange-player'));
assert(html.includes('fight-exchange-history'));
assert.deepEqual(fight.history,history,'Rendering cannot mutate saved history');
experimental=false;
html=render(fight);
assert(html.includes('LAST EXCHANGE')&&!html.includes('fight-exchange-history'));
experimental=true;pvp=true;
html=render(fight);
assert(html.includes('LAST EXCHANGE')&&!html.includes('fight-exchange-history'));
""";
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_history_is_scrollable_and_latest_is_revealed_on_modal_render():
    assert "max-height:min(42vh,320px)" in CSS
    assert "overscroll-behavior:contain" in CSS
    assert ".fight-exchange-group.is-latest" in CSS
    assert "if(exchangeHistory)exchangeHistory.scrollTop=exchangeHistory.scrollHeight;" in APP
    assert "if(document.documentElement.dataset.ui==='tomb'&&experimentalFeaturesEnabled()&&!isPvpMode())" in APP


def test_version_consistency():
    assert CURRENT_APP_VERSION == "10.0.202"
    assert "V10.0.202" in (ROOT / "index.html").read_text(encoding="utf-8")
    assert "const APP_VERSION = '10.0.202';" in (ROOT / "service-worker.js").read_text(encoding="utf-8")
