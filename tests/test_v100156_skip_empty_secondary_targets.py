"""Regression coverage for automatic bypass of empty Blast/Torrent checklists in V10.0.156."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_empty_secondary_check_bypasses_modal_for_player_and_npo():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const rules=source.slice(source.indexOf('  function createWeaponRuleResolution('),source.indexOf('  function normalizeMultiTargetAttackSequence('));
const screen=source.slice(source.indexOf('  function showSecondaryTargetCheck('),source.indexOf('  function multiTargetSequenceCount('));

function run({rule='torrent',side='npo',targets=[],saved=null,selectedIds=[]}={}){
  const calls=[],state={turningPoint:3,activationNumber:4,weaponRuleResolution:saved};
  const controls={};
  const ctx={
    state,
    isRecord:value=>!!value&&typeof value==='object',
    save:()=>calls.push('save'),
    showModal:(title,markup)=>calls.push(['modal',title,markup]),
    escapeHtml:value=>String(value),
    weaponRuleTargetOption:target=>'<input value="'+target.id+'">',
    weaponRuleResumePending:false,
    $:id=>controls[id]??(controls[id]={checked:false,disabled:false}),
    $$:selector=>selector==='[data-weapon-rule-target]:checked'
      ?selectedIds.map(value=>({value}))
      :selector==='[data-weapon-rule-target]'
        ?targets.map(target=>({value:target.id,checked:selectedIds.includes(target.id)}))
        :[]
  };
  const fn=new Function('ctx','with(ctx){'+rules+screen+'return showSecondaryTargetCheck;}')(ctx);
  fn({ruleId:rule,distance:1,attackerSide:side,attackerId:'attacker',primaryTargetId:'primary',
      targets,weaponId:'weapon',weaponName:'Gun',profileKey:'focused',profileName:'Focused',weaponRules:['Torrent 1'],
      onContinue:resolution=>calls.push(['continue',resolution]),onBack:()=>calls.push('back')});
  return {calls,state,controls};
}
const primary={id:'primary',wounds:5,inPlay:true};
const live={id:'other',wounds:5,inPlay:true,targetSide:'player'};
const attacker={id:'attacker',wounds:5,inPlay:true};
const out={id:'gone',wounds:5,inPlay:false};
const dead={id:'dead',wounds:0,inPlay:true};

// A lone target should not produce the pointless confirmation screen.
const alone=run({targets:[primary,attacker,out,dead]});
assert.deepEqual(alone.calls.map(entry=>Array.isArray(entry)?entry[0]:entry),['save','continue']);
assert.deepEqual(alone.state.weaponRuleResolution.orderedTargetIds,['primary']);
assert.deepEqual(alone.state.weaponRuleResolution.orderedTargets,[{targetId:'primary',targetSide:'player'}]);
assert.deepEqual(alone.state.weaponRuleResolution.secondaryTargetIds,[]);
assert.equal(alone.state.weaponRuleResolution.tabletopCheckConfirmed,true);
assert.equal(alone.state.weaponRuleResolution.continueConfirmed,true);
assert.deepEqual(alone.state.weaponRuleResolution.sequenceResults,[]);

// Apply the same behavior to Player shooting, Blast, and saved Seek Light answers.
const player=run({rule:'blast',side:'player',targets:[primary],saved:{primaryTargetId:'primary',seekLightAnswer:'yes'}});
assert.deepEqual(player.calls.map(entry=>Array.isArray(entry)?entry[0]:entry),['save','continue']);
assert.deepEqual(player.state.weaponRuleResolution.orderedTargets,[{targetId:'primary',targetSide:'npo'}]);
assert.equal(player.state.weaponRuleResolution.seekLightAnswer,'yes');
assert.equal(player.state.weaponRuleResolution.ruleId,'blast');

// Positive candidates still need user selection and tabletop confirmation.
const selectable=run({targets:[primary,live]});
assert.equal(selectable.calls[0][0],'modal');
assert.equal(selectable.calls[0][1],'Torrent');
assert.ok(selectable.calls[0][2].includes('tabletopCheckConfirmed'));
assert.equal(selectable.calls.some(item=>Array.isArray(item)&&item[0]==='continue'),false);
assert.equal(selectable.controls['#confirmSecondaryTargets'].disabled,true);
selectable.controls['#tabletopCheckConfirmed'].checked=true;
selectable.controls['#tabletopCheckConfirmed'].onchange();
assert.equal(selectable.controls['#confirmSecondaryTargets'].disabled,false);
selectable.controls['#confirmSecondaryTargets'].onclick({currentTarget:{disabled:false}});
assert.deepEqual(selectable.state.weaponRuleResolution.orderedTargetIds,['primary']);
assert.equal(selectable.state.weaponRuleResolution.continueConfirmed,true);

// A player Blast can hit nearby friendlies, so don't skip when one is present.
const friendly=run({rule:'blast',side:'player',targets:[primary,{id:'friendly',targetSide:'player',wounds:8,inPlay:true}]});
assert.equal(friendly.calls[0][0],'modal');

// Even a single eligible target must keep the normal confirmation step.
const torrent=run({rule:'torrent',side:'player',targets:[primary,{id:'npo2',targetSide:'npo',wounds:3,inPlay:true}]});
assert.equal(torrent.calls[0][0],'modal');

// No rule state should be silently confirmed if creating a player sequence fails.
const unavailable=run({rule:'blast',side:'player',targets:[],saved:null});
assert.equal(unavailable.state.weaponRuleResolution.continueConfirmed,true);

console.log('Empty and non-empty secondary-target routes passed');
"""
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_version_and_rule_callers():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert "if(!eligible.length){" in APP
    assert "showSecondaryTargetCheck({ruleId,distance:" in APP
    assert "onContinue:proceed,onBack:back" in APP
    assert "onContinue:resume,onBack:back" in APP
