"""Verify Solo NPO profiles against exact Joint Ops: Tomb World Mission Pack pp. 5-7.

Competitive Canoptek Circle datacards and strategic gambits are not Solo sources.
"""
import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")

def node(program):
    result=subprocess.run(["node","-e",program],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0, result.stderr or result.stdout

def test_official_joint_ops_profiles_and_no_competitive_additions():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  const npoDefinitions = {'),b=s.indexOf('  // Official 2D6 table',a);
assert(a>=0&&b>a);
const n=new Function(s.slice(a,b)+'return npoDefinitions;')();
const scarab=n['Canoptek Scarab Swarm'],warrior=n['Necron Warrior'],crawler=n['Canoptek Tomb Crawler'],macro=n['Canoptek Macrocyte Warrior'];
const pair=p=>p.damage.normal+'/'+p.damage.critical;
assert.deepEqual([scarab.apl,scarab.move,scarab.save,scarab.wounds],[2,6,5,10]);
assert.deepEqual([scarab.meleeWeapons[0].attacks,scarab.meleeWeapons[0].hit,pair(scarab.meleeWeapons[0])],[5,4,'1/2']);
assert.deepEqual([warrior.apl,warrior.move,warrior.save,warrior.wounds],[2,5,4,9]);
assert.deepEqual(warrior.rangedWeapons.map(p=>[p.attacks,p.hit,pair(p)]),[[4,4,'3/4'],[4,3,'3/4']]);
assert.deepEqual([crawler.apl,crawler.move,crawler.save,crawler.wounds],[2,5,3,21]);
const gauss=crawler.rangedWeapons.find(w=>w.id==='twin-gauss-reapers');
assert.deepEqual(gauss.profiles.map(p=>[p.attacks,p.hit,pair(p)]),[[5,4,'4/5'],[4,4,'4/5']]);
assert(gauss.profiles.every(p=>p.rules.includes('Punishing')&&!p.rules.includes('Severe')));
assert.deepEqual([macro.apl,macro.move,macro.save,macro.wounds],[2,7,4,7]);
const scalpel=macro.rangedWeapons.find(w=>w.id==='gauss-scalpel');
const tesla=macro.rangedWeapons.find(w=>w.id==='tesla-caster');
assert.deepEqual([scalpel.attacks,scalpel.hit,pair(scalpel)],[4,4,'3/4']);
assert.deepEqual(tesla.profiles.map(p=>[p.attacks,p.hit,pair(p)]),[[5,4,'2/3'],[5,4,'2/3']]);
assert.deepEqual([macro.meleeWeapons[0].attacks,macro.meleeWeapons[0].hit,pair(macro.meleeWeapons[0])],[4,4,'3/4']);
assert.deepEqual(macro.passiveRules.map(p=>p.id),['aggressive-defence']);
assert.deepEqual(macro.strategicRules,[]);
assert.equal(macro.passiveRules[0].damage,'roll-result');
""")

def test_punishing_rule_one_failed_die_only_after_critical_and_resume_idempotent():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function retainSuccessfulDice('),b=s.indexOf('  function beneficialRerollChoice',a);
const api=new Function('ctx','with(ctx){'+s.slice(a,b)+'return {retainSuccessfulDice,applyPunishingToAttackDice,applyAttackSuccessConversions};}')({
 weaponHasRule:(p,r)=>p.rules.includes(r[0].toUpperCase()+r.slice(1)),
 applySevereToAttackDice:(dice)=>({dice})
});
const profile={rules:['Punishing']};
const dice=[{value:6,kind:'crit'},{value:1,kind:'miss'},{value:2,kind:'miss'}];
const first=api.applyAttackSuccessConversions(dice,profile);
assert.equal(first.filter(x=>x.punishingConverted).length,1);
assert.equal(first[1].kind,'hit');
assert.equal(first[1].retained,true);
assert.equal(first[2].retained,false);
assert.deepEqual(api.applyAttackSuccessConversions(first,profile),first);
assert.equal(api.applyAttackSuccessConversions([{value:4,kind:'hit'},{value:1,kind:'miss'}],profile).filter(x=>x.punishingConverted).length,0);
assert.equal(api.applyAttackSuccessConversions(dice,{rules:[]}).filter(x=>x.punishingConverted).length,0);
""")
    assert "return applyAttackSuccessConversions(rerolled,profile);" in APP
    assert "attackDice=applyAttackSuccessConversions(resumedDice,profile);" in APP

def test_macrocyte_aggressive_defence_d3_result_not_flat_one_damage():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function aggressiveDefenseDamage('),b=s.indexOf('  function aggressiveDefenseDamageValue',a);
const f=new Function(s.slice(a,b)+'return aggressiveDefenseDamage;')();
assert.deepEqual([1,2,3].map(f),[0,2,3]);
""")
    assert "function aggressiveDefenceDamage(rollResult){return Number(rollResult)>=2?Number(rollResult):0;}" in APP

def test_competitive_scuttling_ineligible_in_joint_ops_solo():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function ceaselessScuttlingEligible('),b=s.indexOf('  function ceaselessScuttlingUnavailableReason(',a);
const ctx={isPvpMode:()=>false,ceaselessScuttlingAvailable:()=>true,MAX_NPOS:10,state:{turningPoint:2,roster:[],strategyData:{}}};
const f=new Function('ctx','with(ctx){'+s.slice(a,b)+'return ceaselessScuttlingEligible;}')(ctx);
assert.equal(f(2,[{type:'Canoptek Macrocyte Warrior',wounds:7,battlefieldState:'deployed'}],{}),false);
ctx.isPvpMode=()=>true;
assert.equal(f(2,[{type:'Canoptek Macrocyte Warrior',wounds:7,battlefieldState:'deployed'}],{}),true);
""")
    assert "function soloCeaselessScuttlingPending(){return !isPvpMode()&&ceaselessScuttlingEligible();}" in APP
    assert "const npoGenerationTable = [" in APP
    assert "tombWorldVariant" in APP

def test_release_version():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 198)
