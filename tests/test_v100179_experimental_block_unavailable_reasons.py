"""Exhaustive reason-matrix checks for Experimental Fight Block guidance."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_every_no_block_case_gets_the_correct_reason_and_no_legal_block_is_hidden():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const section=(start,end)=>{
  const a=src.indexOf(start),b=src.indexOf(end,a+start.length);
  assert(a>=0&&b>a,'Missing '+start);
  return src.slice(a,b);
};
const source=[
  section('  function fightBlockTargets(','  function canFightBlock('),
  section('  function semanticFightActions(','  function fightRoleDamage('),
  section('  function experimentalFightStrikeAdvice(','  function experimentalActionFirstFightHtml('),
  section('  function experimentalActionFirstFightHtml(','  function bindExperimentalActionFirstFight(')
].join('\n');
const context={
 otherFightRole:role=>role==='attacker'?'defender':'attacker',
 unresolvedFightSuccesses:(fight,role)=>fight.successes[role].filter(item=>item.status==='unresolved'),
 weaponHasRule:(profile,id)=>(profile.ruleIds||[]).includes(id),
 escapeHtml:value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
 titleCaseRuleId:value=>value[0].toUpperCase()+value.slice(1),
 isPvpMode:()=>false,
 experimentalFightPoolHtml:()=>'<section class="fight-pool">Participant</section>',
 fightLastResolutionHtml:()=>''
};
const api=new Function('ctx','with(ctx){'+source+
  '\nreturn {fightBlockTargets,semanticFightActions,experimentalFightBlockUnavailableHtml,experimentalActionFirstFightHtml};}')(context);
const die=(id,kind)=>({id,kind,status:'unresolved'});
const sets={
 none:[],
 normals:[die('n1','normal'),die('n2','normal')],
 crits:[die('c1','critical'),die('c2','critical')],
 mixed:[die('n3','normal'),die('c3','critical')]
};
let scenarios=0,unavailable=0,legal=0;
for(const role of ['attacker','defender']){
 for(const brutal of [false,true]){
  for(const [ownType,own] of Object.entries(sets)){
   for(const [enemyType,enemy] of Object.entries(sets)){
    const you={side:'player',label:'Disruptor',wounds:7,maxWounds:7,profile:{name:'Bayonet',normal:3,crit:4,ruleIds:[]}};
    const them={side:'npo',label:'Necron Warrior',wounds:9,maxWounds:9,
      profile:{name:'Claws <Reaper>',normal:3,crit:4,ruleIds:brutal?['brutal']:[]}};
    const fight={attacker:role==='attacker'?you:them,defender:role==='attacker'?them:you,turn:role,
      successes:{attacker:role==='attacker'?own:enemy,defender:role==='attacker'?enemy:own},
      history:[],blockCapacity:{[role]:1}};
    const actions=api.semanticFightActions(fight,role);
    const reason=api.experimentalFightBlockUnavailableHtml(fight,role,actions);
    scenarios++;
    if(!own.length){assert.equal(reason,'');continue;}
    if(actions.blocks.length){
      legal++;
      assert.equal(reason,'','Do not show notice if a legal Block exists: '+[role,brutal,ownType,enemyType]);
      const markup=api.experimentalActionFirstFightHtml(fight,role,you,actions,1);
      assert.match(markup,/data-exp-fight-choice="block"/);
      assert.doesNotMatch(markup,/BLOCK UNAVAILABLE/);
      continue;
    }
    unavailable++;
    assert.match(reason,/BLOCK UNAVAILABLE/,'Missing notice: '+[role,brutal,ownType,enemyType]);
    assert.match(reason,/role="note"/);
    if(!enemy.length){
      assert.match(reason,/No unresolved enemy successes remain to cancel/);
      assert.match(reason,/tabletop rules also allow a Block with none remaining/);
      assert.doesNotMatch(reason,/Brutal \(/);
    }else if(brutal){
      assert.match(reason,/Brutal \(Claws &lt;Reaper>/);
      assert.match(reason,/Only critical successes can Block/);
    }else{
      assert.equal(enemyType,'crits','Only critical-only enemy dice can prevent normal Blocks without Brutal');
      assert.match(reason,/The enemy has only critical successes/);
      assert.match(reason,/You need a critical success to Block one/);
      assert.doesNotMatch(reason,/Brutal/);
    }
    const markup=api.experimentalActionFirstFightHtml(fight,role,you,actions,1);
    assert.equal((markup.match(/BLOCK UNAVAILABLE/g)||[]).length,1,'Exactly one notice');
    assert.doesNotMatch(markup,/data-exp-fight-choice="block"/);
    assert.match(markup,/data-exp-fight-choice="strike"/);
    assert.match(markup,/Resolve Selected Action/);
   }
  }
 }
}
assert.equal(scenarios,64);
assert(legal>0&&unavailable>0);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_experimental_scope_existing_shield_and_game_rules_preserved():
    guidance=APP.split("  function experimentalFightBlockUnavailableHtml(",1)[1].split(
        "  function experimentalActionFirstFightHtml(",1)[0]
    assert "if(actions.blocks.length)return ''" in guidance
    assert "role=\"note\"" in guidance
    assert "fightBlockUnavailableHeading" in guidance
    assert "experimentalFightBlockShieldClip" in guidance
    assert "Brutal" in guidance and "critical successes" in guidance
    assert "The enemy has only critical successes." in guidance
    assert "No unresolved enemy successes remain to cancel." in guidance
    assert "tabletop rules also allow a Block with none remaining" in guidance
    assert "commitFightBlock" not in guidance
    assert "setFightOperativeWounds" not in guidance
    assert "html[data-ui=\"tomb\"][data-experimental=\"on\"]" in CSS
    assert "if(document.documentElement.dataset.ui==='tomb'&&document.documentElement.dataset.experimental==='on')" in APP
    assert "if(weaponHasRule(opponent.profile,'brutal')&&blocker.kind!=='critical')return [];" in APP


def test_app_cache_and_docs_versions():
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
