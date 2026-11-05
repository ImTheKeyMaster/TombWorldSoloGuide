"""A Grade 3 Strategy Phase must recover with only two physical reserve Necrons."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_resuming_tp5_with_zero_deployed_and_two_reserves():
    # Execute the production strategy-resume, reinforcement and placement functions.
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const extract=(start,end)=>{
  const i=app.indexOf(start);
  assert(i>=0,`Missing ${start}`);
  const j=app.indexOf(end,i+start.length);
  assert(j>=0,`Missing ${end}`);
  return app.slice(i,j);
};
const funcs=[
  extract('async function finishTurningPointStart()','function completeStrategyStage'),
  extract('function completeStrategyStage','function processReadyStep'),
  extract('function processReinforcementStage','function reinforcementTriggered'),
  extract('function reinforcementTriggered','function confirmReinforcementPlacement'),
  extract('function confirmReinforcementPlacement','async function rollInitiative'),
  extract('function randomReinforcement','function nextNpo')
].join('\n');
const build=new Function('ctx',`
const {state,MAX_NPOS,TOMB_CRAWLER_TYPE,activeNpos,reserveNpos,npoInventory,
  isHumanNpoReplacementPending,experimentalNpoMiniatureReuseEnabled,
  tombWorldVariantHook,resolveVariantNpoRequest,rollNpo,roll,generatedWeaponId,
  npoGenerationTable,createNpo,commitNpoRoster,gradeConfig,threatGrade,
  setupCrownworldCrawlerPair,showToast,log,save,render,$,npoName}=ctx;
${funcs}
return {finishTurningPointStart,randomReinforcement,confirmReinforcementPlacement};
`);
function setup(reuse=false,throwOnNew=false){
  const stats={created:0,writes:0,renders:0,logs:[]};
  const reserve=id=>({id,type:'Necron Warrior',name:id,wounds:7,maxWounds:7,
    battlefieldState:'reserve',deployed:false,ready:false,dormant:false});
  const state={
    phase:'strategy',strategyStage:'event',turningPoint:5,threat:15,
    nextSide:'player',newIds:[],roster:[
      reserve('reserve-1'),reserve('reserve-2'),
      {id:'fallen-1',type:'Necron Warrior',wounds:0,battlefieldState:'out-of-action'}
    ],
    strategyPipeline:{current:'reinforcement',completed:['ready','mission-ready-hooks','initiative','event']},
    strategyData:{grade:3,eventPending:false,events:[],eventIndex:0,reinforcements:[]},
    startingNpoGeneration:{reserveNpoIds:['reserve-1','reserve-2']},
    reinforcementState:{turningPoint:5,status:'idle',operativeIds:[],blocked:0}
  };
  const ctx={
    state,MAX_NPOS:10,TOMB_CRAWLER_TYPE:'Canoptek Tomb Crawler',
    activeNpos:()=>state.roster.filter(n=>n.battlefieldState==='deployed'&&n.wounds>0),
    reserveNpos:()=>state.roster.filter(n=>n.battlefieldState==='reserve'&&n.wounds>0),
    npoInventory:()=>({'Necron Warrior':{remaining:reuse?1:0}}),
    isHumanNpoReplacementPending:()=>false,
    experimentalNpoMiniatureReuseEnabled:()=>reuse,
    tombWorldVariantHook:(_,value)=>value,resolveVariantNpoRequest:value=>value,
    rollNpo:()=>({type:'Necron Warrior',weaponId:'gauss-flayer'}),
    roll:()=>1,generatedWeaponId:()=> 'gauss-flayer',
    npoGenerationTable:[{type:'Necron Warrior',weaponId:'gauss-flayer'}],
    createNpo:(type,name,options)=>{
      stats.created++;
      if(throwOnNew)throw Error('No Necron Warrior model remains available.');
      return {id:'recycled-model',type,name,wounds:7,maxWounds:7,weaponId:options.weaponId,
        battlefieldState:'reserve',deployed:false,ready:false,dormant:false,
        reinforcement:options.reinforcement};
    },
    commitNpoRoster:roster=>{state.roster=roster;return true;},
    gradeConfig:()=>({reinforcements:3}),threatGrade:()=>3,
    setupCrownworldCrawlerPair:()=>{throw Error('Unexpected Crownworld setup');},
    showToast:message=>{throw Error('Unexpected toast: '+message);},
    log:message=>stats.logs.push(message),
    save:()=>{stats.writes++;return true;},render:()=>{stats.renders++;},
    $:()=>null,npoName:n=>n.name
  };
  return {app:build(ctx),state,stats};
}
(async()=>{
  const standard=setup();
  assert.equal(standard.app.randomReinforcement(['reserve-1','reserve-2']),null,
    'Already assigned reserve models must not remain allocatable');
  assert.equal(await standard.app.finishTurningPointStart(),true,
    'Resume must return to Strategy Phase summary');
  assert.equal(standard.state.strategyStage,'summary');
  assert.equal(standard.state.strategyPipeline.current,'complete');
  assert.equal(standard.state.reinforcementState.status,'placement');
  assert.deepEqual(standard.state.reinforcementState.operativeIds,['reserve-1','reserve-2']);
  assert.equal(standard.state.reinforcementState.blocked,1);
  assert.equal(standard.state.reinforcementState.blockedByInventory,1);
  assert.equal(standard.stats.created,0,
    'Do not allocate a nonexistent third Necron model');
  assert.equal(standard.state.roster.filter(n=>n.wounds>0).length,2,
    'No existing model should be eliminated or duplicated by the fix');
  standard.app.confirmReinforcementPlacement('reserve-1',true);
  standard.app.confirmReinforcementPlacement('reserve-2',true);
  assert.equal(standard.state.reinforcementState.status,'complete');
  assert.equal(standard.state.roster.filter(n=>n.ready&&n.deployed).length,2,
    'Both original reserves must become Ready after confirmation');

  const experimental=setup(true);
  assert.equal(await experimental.app.finishTurningPointStart(),true);
  assert.equal(experimental.state.reinforcementState.blocked,0);
  assert.equal(experimental.state.reinforcementState.operativeIds.length,3,
    'Experimental physical-model reuse must remain available');
  assert.equal(experimental.stats.created,1);

  const unexpectedInventoryShortfall=setup(true,true);
  assert.equal(await unexpectedInventoryShortfall.app.finishTurningPointStart(),true,
    'Even a createNpo physical-inventory shortfall must not trap Strategy recovery');
  assert.equal(unexpectedInventoryShortfall.state.reinforcementState.blocked,1);
  assert.equal(unexpectedInventoryShortfall.state.reinforcementState.blockedByInventory,1);
  assert.equal(unexpectedInventoryShortfall.state.strategyStage,'summary');
  console.log('TP5 reserve-only Strategy recovery regressions passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_version_and_physical_inventory_guards():
    assert "randomReinforcement(state.reinforcementState.operativeIds)" in APP
    assert "const excluded=new Set(excludedReserveIds)" in APP
    assert "state.reinforcementState.blockedByInventory++" in APP
    assert "const APP_VERSION = '10.1.28';" in APP
    assert "const APP_VERSION = '10.1.28';" in (ROOT / "service-worker.js").read_text()
    assert (ROOT / "README.md").read_text().startswith("# Tomb World Battle Guide v10.1.28")
