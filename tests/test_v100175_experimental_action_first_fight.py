"""Experimental Action First Fight Resolution regression coverage (v10.0.175)."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_action_first_choice_flow_and_standard_isolation():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function experimentalFightPoolHtml(');
const end=source.indexOf('  async function rollFightParticipant(',start);
assert(start>=0&&end>start);
const code=source.slice(start,end);
const mk=(id,kind)=>({id,kind,status:'unresolved'});
const normal=mk('player-normal','normal'),critical=mk('player-critical','critical');
const npoNormal=mk('npo-normal','normal'),npoCritical=mk('npo-critical','critical');
const makeFight=()=>({
  attacker:{side:'player',id:'sapper',label:'Sapper',wounds:7,maxWounds:7,profile:{name:'Bayonet',normal:2,crit:4}},
  defender:{side:'npo',id:'crawler',label:'Canoptek Tomb Crawler 1',wounds:15,maxWounds:21,profile:{name:'Claws',normal:3,crit:5}},
  turn:'attacker',successes:{attacker:[normal,critical],defender:[npoNormal,npoCritical]},
  history:[],blockCapacity:{attacker:1},completed:false
});
const actions={
  strikes:[{success:normal,damage:2},{success:critical,damage:4}],
  blocks:[{blocker:normal,target:npoNormal},{blocker:critical,target:npoNormal},{blocker:critical,target:npoCritical}]
};
const classList=()=>({values:new Set(),toggle(name,yes){if(yes)this.values.add(name);else this.values.delete(name);}});
function controlFromTag(tag){
  const attributes={};for(const m of tag.matchAll(/data-([a-z-]+)="([^"]+)"/g)){
    const key=m[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase());attributes[key]=m[2];
  }
  return {dataset:attributes,classList:classList(),setAttribute(key,value){this[key]=value;}};
}
function runCase({mode='tomb',enabled=true,shield=false,choice='strike',noBlocks=false,npoTurn=false}={}){
  const fight=makeFight();
  if(shield)fight.blockCapacity.attacker=2;
  if(npoTurn)fight.turn='defender';
  const states={choices:[],markup:'',modals:0,strikes:[],blocks:[],shields:[],finished:0};
  const confirm={disabled:true},summary={textContent:''};
  const modal={querySelectorAll:()=>states.choices};
  const ctx={
    state:{fightState:fight},
    document:{documentElement:{dataset:{ui:mode,experimental:enabled?'on':'off'}}},
    experimentalFeaturesEnabled:()=>enabled,
    isPvpMode:()=>false,
    otherFightRole:role=>role==='attacker'?'defender':'attacker',
    unresolvedFightSuccesses:(f,role)=>f.successes[role].filter(s=>s.status==='unresolved'),
    equivalentRemainingFightStrikes:()=>null,
    semanticFightActions:()=>({...actions,blocks:noBlocks?[]:actions.blocks}),
    titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
    escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
    fightParticipantPortrait:()=>'<span class="fight-portrait"></span>',
    fightLastResolutionHtml:()=>'<section class="fight-last-resolution">LAST EXCHANGE</section>',
    fightPoolHtml:()=>'<div>Standard pool</div>',
    showModal:(name,markup)=>{
      assert.equal(name,'Fight Resolution');
      states.modals++;states.markup=markup;
      states.choices=[...markup.matchAll(/<button type="button" class="experimental-fight-option"[^>]*>/g)]
        .map(match=>controlFromTag(match[0]));
    },
    modal,
    $:selector=>selector==='#confirmExperimentalFightChoice'?confirm:summary,
    $$:()=>[],
    commitFightStrike:(f,role,id)=>{states.strikes.push([role,id]);f.completed=true;return true;},
    commitFightBlock:(f,role,id,targets)=>{states.blocks.push([role,id,targets]);f.completed=true;return true;},
    showFightBlockSelection:(f,role,id,target)=>{states.shields.push([role,id,target]);},
    soloNpoFightDecision:()=>({type:'strike',successId:npoNormal.id}),
    finishFight:()=>{states.finished++;},
    save:()=>{}
  };
  const render=new Function('ctx','with(ctx){'+code+'\nreturn renderFightResolution;}')(ctx);
  render();
  if(npoTurn){
    assert.equal(states.modals,0,'Solo NPO acts without a human choice screen');
    assert.deepEqual(states.strikes,[['defender','npo-normal']]);
    return;
  }
  if(!enabled||mode!=='tomb'){
    assert.equal(states.choices.length,0,'Standard and Classic retain existing presentation');
    assert.doesNotMatch(states.markup,/experimental-fight-choice-screen/);
    assert.match(states.markup,/fight-action/);
    return;
  }
  assert.match(states.markup,/experimental-fight-choice-screen/);
  assert.match(states.markup,/Choose your action/);
  assert.match(states.markup,/Confirm your action/);
  assert.match(states.markup,/Guide handles the NPO/);
  assert.doesNotMatch(states.markup,/Choose their block/i);
  assert.match(states.markup,/Crits 1/);
  assert.match(states.markup,/Normal 1/);
  assert.equal(states.choices.length,noBlocks?2:5);
  assert.equal(confirm.disabled,true);
  assert.equal(states.strikes.length,0);
  assert.equal(states.blocks.length,0);
  if(noBlocks){
    assert.doesNotMatch(states.markup,/id="fightBlockHeading"/);
  }else{
    assert.match(states.markup,/id="fightBlockHeading"/);
    assert.match(states.markup,/Cancel 1 enemy Critical Success/);
    assert.match(states.markup,/Cancel 1 enemy Normal Success/);
  }
  const option=states.choices.find(button=>choice==='strike'
    ?button.dataset.fightStrike==='player-critical'
    :button.dataset.fightBlocker==='player-critical'&&button.dataset.fightBlockTarget==='npo-critical');
  assert(option,'Requested option must be available');
  option.onclick();
  assert.equal(option['aria-pressed'],'true');
  assert.equal(confirm.disabled,false);
  assert.match(summary.textContent,choice==='strike'?/Deal 4 damage/:/Block an enemy|Choose up to 2/);
  assert.equal(states.strikes.length,0,'Selecting does not resolve automatically');
  assert.equal(states.blocks.length,0);
  confirm.onclick();
  if(choice==='strike')assert.deepEqual(states.strikes,[['attacker','player-critical']]);
  else if(shield){
    assert.deepEqual(states.shields,[['attacker','player-critical','npo-critical']]);
    assert.equal(states.blocks.length,0,'Shield keeps its own target picker');
  }else assert.deepEqual(states.blocks,[['attacker','player-critical',['npo-critical']]]);
}
runCase();
runCase({choice:'block'});
runCase({choice:'block',shield:true});
runCase({noBlocks:true});
runCase({enabled:false});
runCase({mode:'classic'});
runCase({npoTurn:true});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_css_and_version_boundary():
    from versioning import CURRENT_APP_VERSION

    assert CURRENT_APP_VERSION == "10.0.175"
    assert "document.documentElement.dataset.experimental==='on'" in APP
    assert "experimentalActionFirstFightHtml(fight,role,participant,actions,capacity)" in APP
    assert "bindExperimentalActionFirstFight(fight,role,capacity)" in APP
    section = CSS.split("v10.0.175: opt-in Action First Fight choices", 1)[1]
    assert 'html[data-ui="tomb"][data-experimental="on"] .experimental-fight-choice-screen' in section
    assert ".experimental-fight-option.is-selected" in section
    assert "focus-visible" in section
    assert "@media(max-width:374px)" in section
