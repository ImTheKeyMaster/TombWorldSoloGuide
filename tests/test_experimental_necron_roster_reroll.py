"""Regression checks for experimental-only setup roster re-roll."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text(encoding='utf-8')
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'service-worker.js').read_text(encoding='utf-8')


def node_check(script):
    completed = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_reroll_is_gated_atomic_and_preserves_other_setup():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const begin=source.indexOf('  function rerollStartingNpoRoster(');
const end=source.indexOf('  function ensureStartingNpoGeneration(',begin);
assert.ok(begin>0&&end>begin);
const method=source.slice(begin,end);

function execute({experimental=true,screen='setup',step='deploy',generated=true,fail=false,throws=false}={}){
 const calls=[];
 const original={
  screen,phase:'setup',missionId:'mission-03',tombWorldVariant:'flayer-curse',
  roster:[{id:'old-npo',type:'Necron Warrior',wounds:8}],
  startingNpoGeneration:generated?{missionRoll:7,dice:[1,3],deployedNpoIds:['old-npo'],reserveNpoIds:[],animationShown:true}:null,
  setupChecks:{'starting-npos':true,'player-zone':true},
  variantState:{crownworldFirstCrawlerConsumed:true,replacementTransactions:{'starting:0:necron':{selectedType:'Necron Warrior'}}},
  newIds:['old-npo'],journal:[{message:'old'}],
  playerTeamId:'deathwatch',playerRoster:['player-01'],playerDeployed:true
 };
 const state=JSON.parse(JSON.stringify(original));
 const context={
  state,experimentalFeaturesEnabled:()=>experimental,
  currentSetupStepId:()=>step,
  startingNpoRoll:()=>{calls.push('roll');return {missionRoll:9,dice:[3,3],deployedNpoIds:[],reserveNpoIds:[],animationShown:false};},
  generateRoster:generation=>{
   calls.push('generate');
   assert.deepEqual(state.variantState.replacementTransactions,{});
   assert.equal(state.variantState.crownworldFirstCrawlerConsumed,false);
   state.roster=[{id:'new-npo',type:'Scarab Swarm',wounds:5}];
   state.newIds=['new-npo'];
   state.journal.push({message:'new'});
   if(throws)throw Error('Unexpected generation failure');
   if(fail)return null;
   generation.deployedNpoIds=['new-npo'];
   return {count:1};
  },
  save:()=>calls.push('save'),
  render:()=>calls.push('render'),
  console:{error:()=>calls.push('error')}
 };
 const reroll=new Function('ctx','with(ctx){'+method+'return rerollStartingNpoRoster;}')(context);
 return {ok:reroll(),state,original,calls};
}
const success=execute();
assert.equal(success.ok,true);
assert.deepEqual(success.calls,['roll','generate','save','render']);
assert.deepEqual(success.state.roster.map(n=>n.id),['new-npo']);
assert.deepEqual(success.state.startingNpoGeneration.deployedNpoIds,['new-npo']);
assert.equal(success.state.startingNpoGeneration.missionRoll,9);
assert.equal(success.state.startingNpoGeneration.animationShown,false);
assert.equal(success.state.setupChecks['starting-npos'],false);
assert.equal(success.state.setupChecks['player-zone'],true);
assert.deepEqual(success.state.playerRoster,['player-01']);
assert.equal(success.state.playerDeployed,true);
assert.equal(success.state.missionId,'mission-03');
assert.equal(success.state.tombWorldVariant,'flayer-curse');
assert.deepEqual(success.state.variantState.replacementTransactions,{});

for(const option of [{experimental:false},{screen:'game'},{step:'ready'},{step:'options'},{generated:false}]){
 const output=execute(option);
 assert.equal(output.ok,false);
 assert.deepEqual(output.state,output.original);
 assert.deepEqual(output.calls,[]);
}
for(const option of [{fail:true},{throws:true}]){
 const output=execute(option);
 assert.equal(output.ok,false);
 assert.deepEqual(output.state,output.original,'Failure must restore the exact prior roster, checks, journal and variant transactions');
 assert.ok(output.calls.includes('save'));
 assert.ok(output.calls.includes('render'));
}
console.log('Experimental setup roster re-roll: success, guards and failure recovery passed');
"""
    node_check(script)


def test_reroll_button_and_mode_switch_are_deploy_only():
    # The button is created only in the deployment branch and only with Experimental enabled.
    deploy = APP.split("    if(stepId==='deploy'){", 1)[1].split('    const m=mission();', 1)[0]
    assert "const rerollControl=experimentalFeaturesEnabled()" in deploy
    assert 'id="rerollStartingNpoRoster"' in deploy
    assert 'Re-roll Necron Roster' in deploy
    assert '${missionRoll}${rerollControl}' in deploy
    assert 'Reconfirm the Necron models you place.' in deploy

    binding = APP.split('  function bindSetup(stepId){', 1)[1].split('  function runStartingNpoGeneration(){', 1)[0]
    assert "if(stepId==='deploy')runStartingNpoGeneration();" in binding
    assert "$('#rerollStartingNpoRoster')?.addEventListener('click',rerollStartingNpoRoster);" in binding
    toggle = APP.split('  function setExperimentalFeatures(enabled){', 1)[1].split('  function showExperimentalUiPanel(){', 1)[0]
    assert "if(state.screen==='setup'&&currentSetupStepId()==='deploy')render();" in toggle


def test_release_and_persistence_are_compatible():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function experimentalFeaturesEnabled(){" in APP
