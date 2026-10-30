"""Compact Fight Result Summary coverage for v10.1.3."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_compact_summary_renders_both_damage_totals_without_duplicate_prose():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const start=src.indexOf('  function compactFightResultSummaryHtml(');
const end=src.indexOf('  function finishFight(fight){',start);
assert(start>0&&end>start);
let mode='tomb',markup='',acknowledged=0;
const modal={};
const ctx={
 escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'),
 document:{documentElement:{dataset:{get ui(){return mode;}}}},
 showModal:(title,html)=>{assert.equal(title,'Fight Result');markup=html;},
 fightResultParticipantHtml:(p,role)=>'<section data-role="'+role+'">'+p.name+'</section>',
 experimentalFightAutomaticStrikeResultHtml:()=>'<section class="fight-auto-strike-result">STRIKES RESOLVED</section>',
 scaleFightPortraits:()=>{},
 $:()=>({set onclick(fn){this.callback=fn;}}),
 acknowledgeFightResult:()=>{acknowledged++;},
 };
const api=new Function('ctx','with(ctx){'+src.slice(start,end)+
  'return {compactFightResultSummaryHtml,renderFightResult};}')(ctx);
const result={
 participants:{
  attacker:{name:'Marksman',damageDealt:9},
  defender:{name:'Necron Warrior 5',damageDealt:3}
 },
 explanation:['Marksman dealt 9 total Strike damage.','Necron Warrior 5 dealt 3 total Strike damage.'],
};
const compact=api.compactFightResultSummaryHtml(result);
assert(compact.includes('Marksman</span><strong>9</strong>'));
assert(compact.includes('<div class="fight-result-summary-header"><h3>SUMMARY</h3><span>DAMAGE DEALT</span></div>'));
assert(!compact.includes('9 damage'))
assert(compact.includes('Necron Warrior 5</span><strong>3</strong>'));
assert(!compact.includes('total Strike damage'));
assert.equal((compact.match(/class="fight-result-summary-row"/g)||[]).length,2);
api.renderFightResult({result});
assert(markup.includes('class="fight-result-explanation"'));
assert(markup.includes('fight-result-summary-rows'));
assert(markup.includes('STRIKES RESOLVED'));
assert(!markup.includes('9 total Strike damage'));
mode='classic';
api.renderFightResult({result});
assert(markup.includes('Marksman dealt 9 total Strike damage.'));
assert(!markup.includes('fight-result-summary-rows'));
// Blocked successes and unusual results remain visible without duplicate totals.
mode='tomb';
const extra={
 ...result,participants:{
 attacker:{name:'Aegis & <Shield>',damageDealt:0},
 defender:{name:'Macrocyte',damageDealt:0}
 },
 explanation:[
  'Neither operative retained a success.',
  'Aegis blocked 2 Macrocyte Normal Successes.',
  'No damage was dealt.'
 ]
};
const special=api.compactFightResultSummaryHtml(extra);
assert(special.includes('Aegis &amp; &lt;Shield&gt;'));
assert(special.includes('Aegis blocked 2 Macrocyte Normal Successes.'));
assert(special.includes('Neither operative retained a success.'));
assert(!special.includes('No damage was dealt.'));
assert(special.includes('<strong>0</strong>'));
const oneSided=api.compactFightResultSummaryHtml({
 participants:{attacker:{name:'Scout',damageDealt:4},defender:{name:'Warrior',damageDealt:0}},
 explanation:['Warrior retained no successes.','Scout dealt 4 total Strike damage.']
});
assert(oneSided.includes('Warrior retained no successes.'));
assert(!oneSided.includes('total Strike damage'));
"""
    completed=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert completed.returncode==0,completed.stderr or completed.stdout


def test_summary_spacing_is_scoped_and_fight_mechanics_preserved():
    section=CSS.split("/* v10.1.3: Compact Fight Result Summary",1)[1]
    assert 'html[data-ui="tomb"] .fight-result-explanation{' in section
    assert "gap:5px;" in section and "padding:10px 12px;" in section
    assert "margin:0 0 3px;" in section
    assert "line-height:1.35;" in section
    assert "overflow-wrap:anywhere;" in section
    assert "fight-result-summary-row>strong" in section
    assert "function fightResultExplanation(fight,result)" in APP
    assert "function commitFightStrike(fight,role,successId" in APP
    assert "function commitFightBlock(fight,role,blockerId" in APP
    assert "result.explanation=fightResultExplanation(fight,result)" in APP
    assert "document.documentElement.dataset.ui==='tomb'?compactFightResultSummaryHtml(result)" in APP


def test_version_and_pwa_cache_consistency():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,1,3)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"app.js?v={CURRENT_APP_VERSION}" in html
    assert f"styles.css?v={CURRENT_APP_VERSION}" in html
    assert f"V{CURRENT_APP_VERSION}" in html
