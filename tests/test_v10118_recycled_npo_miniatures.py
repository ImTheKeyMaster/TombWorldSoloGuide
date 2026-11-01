"""Experimental Solo NPO recycling keeps physical limits and combat history separate."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def node(source):
    result = subprocess.run(
        ["node", "-e", source], cwd=ROOT, capture_output=True,
        text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_recycling_creates_unique_ids_and_reuses_only_unoccupied_physical_slots():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function experimentalNpoMiniatureReuseEnabled()');
const b=s.indexOf('  function variantAllowsExpansionNpo(',a);
const definitions={
  'Necron Warrior':{id:'necron-warrior',name:'Necron Warrior',physicalQuantity:2,loadoutOptions:[{id:'gauss'}]},
  'Canoptek Tomb Crawler':{id:'crawler',name:'Canoptek Tomb Crawler',physicalQuantity:1,loadoutOptions:[{id:'iso'}]}
};
const dead=(number)=>({id:'necron-warrior-'+number,type:'Necron Warrior',displayNumber:number,name:'Warrior '+number,wounds:0,battlefieldState:'out-of-action',weaponId:'gauss'});
const state={roster:[dead(1),dead(2)]};
let experimental=true,mode='solo';
const ctx={state,npoDefinitions:definitions,npoDefinition:type=>definitions[type],
  MAX_PHYSICAL_NPOS:3,TOMB_CRAWLER_TYPE:'Canoptek Tomb Crawler',ISOLATOR_LOADOUT:'iso',
  isRecord:v=>v!==null&&typeof v==='object'&&!Array.isArray(v),
  isPvpMode:()=>mode==='pvp',experimentalFeaturesEnabled:()=>experimental,
  document:{documentElement:{dataset:{ui:'tomb'}}}};
const api=new Function('ctx','with(ctx){'+s.slice(a,b)+'return {experimentalNpoMiniatureReuseEnabled,npoInventory,lowestAvailableNpoInstances,validateNpoRoster};}')(ctx);
assert(api.experimentalNpoMiniatureReuseEnabled());
assert.equal(api.npoInventory(state.roster)['Necron Warrior'].remaining,0);
assert.equal(api.npoInventory(state.roster,{reuseEliminated:true})['Necron Warrior'].remaining,2);
assert.equal(api.lowestAvailableNpoInstances('Necron Warrior',1).length,0);
const added=(slot)=>({...dead(slot.displayNumber),id:slot.id,wounds:9,battlefieldState:'reserve',physicalReuse:slot.physicalReuse});
const a1=api.lowestAvailableNpoInstances('Necron Warrior',1,{reuseEliminated:true})[0];
assert.deepEqual([a1.id,a1.displayNumber,a1.physicalReuse],['necron-warrior-1-reused-1',1,true]);
state.roster.push(added(a1));
assert(api.validateNpoRoster(state.roster).valid);
const a2=api.lowestAvailableNpoInstances('Necron Warrior',1,{reuseEliminated:true})[0];
assert.equal(a2.id,'necron-warrior-2-reused-1');
state.roster.push(added(a2));
assert.equal(api.npoInventory(state.roster,{reuseEliminated:true})['Necron Warrior'].remaining,0);
assert.equal(api.lowestAvailableNpoInstances('Necron Warrior',1,{reuseEliminated:true}).length,0);
assert(api.validateNpoRoster(state.roster).valid);
assert.equal(state.roster.filter(x=>x.wounds===0).length,2);
const duplicate={...added(a1),id:'illegal-duplicate'};
assert(!api.validateNpoRoster([...state.roster,duplicate]).valid);
state.roster[2].wounds=0;
const a3=api.lowestAvailableNpoInstances('Necron Warrior',1,{reuseEliminated:true})[0];
assert.equal(a3.id,'necron-warrior-1-reused-2');
state.roster.push(added(a3));
assert(api.validateNpoRoster(state.roster).valid);
experimental=false;
assert(!api.experimentalNpoMiniatureReuseEnabled());
mode='pvp';experimental=true;
assert(!api.experimentalNpoMiniatureReuseEnabled());
""")


def test_saved_games_keep_reuse_marker_and_original_numbering():
    normalize=section("function normalizeState(raw)", "function npoDefinition")
    npo=section("function normalizeNpo(npo)", "function mission()")
    assert "validateNpoRoster(raw.roster)" in normalize
    assert "validateNpoRoster(merged.roster)" in normalize
    assert "if(!merged.roster.some(npo=>npo.physicalReuse===true))" in normalize
    assert "...npo," in npo
    assert "physicalReuse:true" in APP
    assert "newIds.push(n.id)" in APP


def test_retry_only_for_complete_inventory_blocked_strategy_checkpoints():
    retry=section("function canRetryBlockedReinforcements", "function reinforcementTriggered")
    review=section("function strategyReviewStepHtml", "function reinforcementBlockedReason")
    bind=section("function bindPlay", "async function startTurningPoint")
    assert "reinforcement.status==='blocked'" in retry
    assert "Number(reinforcement.blockedByInventory)===Number(reinforcement.blocked)" in retry
    assert "!(reinforcement.operativeIds||[]).length" in retry
    assert "processReinforcementStage({retryBlockedInventory:true})" in bind
    assert 'id="retryBlockedReinforcements"' in review
    assert "if(state.strategyPipeline.completed.includes('reinforcement')&&!retryBlockedInventory)return;" in retry
    assert "if(!state.strategyPipeline.completed.includes('reinforcement'))completeStrategyStage" in retry
    assert "slots=Math.max(0,MAX_NPOS-activeNpos().length)" in retry


def test_standard_and_pvp_keep_existing_allocation_behavior():
    inventory=section("function experimentalNpoMiniatureReuseEnabled", "function validateNpoRoster")
    generation=section("function processReinforcementStage", "function reinforcementTriggered")
    picker=section("function randomReinforcement", "function nextNpo")
    assert "!isPvpMode()" in inventory
    assert "experimentalFeaturesEnabled()" in inventory
    assert "reuseEliminated=experimentalNpoMiniatureReuseEnabled()" in generation
    assert "npoInventory(state.roster,{reuseEliminated:experimentalNpoMiniatureReuseEnabled()})" in picker
    assert "reserveNpos().find" in generation
