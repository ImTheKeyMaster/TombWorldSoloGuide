import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_production_catalog_boundary_and_release_contracts():
    standard = APP.split("const npoDefinitions = {", 1)[1].split(
        "const npoGenerationTable", 1
    )[0]
    expansion_types = (
        "Flayed One",
        "Skorpekh Destroyer",
        "Hexmark Destroyer",
        "Royal Warden",
        "Lychguard",
    )
    assert "const persistenceNpoDefinitions=Object.freeze({...npoDefinitions,...tombsBeyondCountingNpoDefinitions});" in APP
    assert "migrateSaveDetailed(input,persistenceNpoDefinitions)" in APP
    assert "migrateSupportedSave(parsed)" in APP
    assert "migrateSupportedSave(data)" in APP
    assert "types=sortedNposForDisplay(Object.keys(npoDefinitions))" in APP
    for npo_type in expansion_types:
        assert npo_type not in standard
    assert CURRENT_APP_VERSION == "9.2.59"
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()


def test_all_expansion_npos_round_trip_and_exact_activation_resume():
    script = r"""
const assert=require('assert');
const fs=require('fs');
const p=require('./persistence.js');
const app=fs.readFileSync('./app.js','utf8');
function objectLiteral(marker){
  const start=app.indexOf(marker)+marker.length-1;
  let depth=0,quote=null,escaped=false;
  for(let i=start;i<app.length;i++){
    const c=app[i];
    if(quote){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c===quote)quote=null;continue;}
    if(c==="'"||c==='"'||c==='`'){quote=c;continue;}
    if(c==='{')depth++;
    if(c==='}'&&--depth===0)return app.slice(start,i+1);
  }
  throw new Error(`Unclosed catalog ${marker}`);
}
const expansion=Function(`return (${objectLiteral('const tombsBeyondCountingNpoDefinitions = Object.freeze({')})`)();
const standard=Function(`return (${objectLiteral('const npoDefinitions = {')})`)();
const catalog={...standard,...expansion};
const legalVariants={
  'Flayed One':'flayer-curse','Skorpekh Destroyer':'destroyer-cult',
  'Hexmark Destroyer':'destroyer-cult','Royal Warden':'crownworld','Lychguard':'crownworld'
};
for(const [type,variant] of Object.entries(legalVariants)){
  const definition=catalog[type];
  const state={saveVersion:3,tombWorldVariant:variant,roster:[{
    id:`${definition.id}-resume`,displayNumber:1,type,name:type,
    weaponId:type==='Lychguard'?'warscythe':definition.defaultWeaponId,
    wounds:definition.wounds-1,maxWounds:definition.wounds,battlefieldState:'deployed',deployed:true,dormant:false
  }],playerRoster:[]};
  const exported=JSON.parse(JSON.stringify(p.createPersistedSave(state)));
  const first=p.migrateSaveDetailed(exported,catalog);
  assert.equal(first.report.requiresRegeneration,false,type);
  assert.deepEqual(first.report.unsupportedRetiredTypes,[],type);
  assert.equal(first.state.tombWorldVariant,variant,type);
  assert.equal(first.state.roster[0].type,type);
  assert.equal(first.state.roster[0].wounds,definition.wounds-1);
  assert.equal(first.state.roster[0].weaponId,state.roster[0].weaponId);
  const second=p.migrateSaveDetailed(p.createPersistedSave(first.state),catalog);
  assert.equal(second.report.outcome,'current',type);
  assert.deepStrictEqual(second.state,first.state,type);
}
const production={saveVersion:3,version:'9.2.58',gameMode:'solo',screen:'game',playerTeamId:'deathwatch',
  missionId:'01',tombWorldVariant:'flayer-curse',restlessTombEnabled:true,deadlyEncountersEnabled:true,
  deadlyEncountersState:{deck:['encounter'],active:null},turningPoint:1,phase:'firefight',initiative:'player',nextSide:'npo',
  playerRoster:['watch-sergeant','deathwatch-warrior'],playerActivatedIds:['watch-sergeant'],playerActivated:1,npoActivated:0,
  activationHistory:[{side:'player',operativeId:'watch-sergeant',turningPoint:1}],activationNumber:1,totalActivationsThisTP:1,
  activationFinishedForTurningPoint:{player:false,npo:false},lastActivation:{side:'player',operativeId:'watch-sergeant',completed:true,committed:true},
  playerOperativeStates:{'watch-sergeant':{inPlay:true,ready:false},'deathwatch-warrior':{inPlay:true,ready:true}},
  roster:[{id:'flayed-one-production',displayNumber:1,type:'Flayed One',name:'Flayed One',weaponId:'flayer-claws',wounds:7,maxWounds:9,battlefieldState:'deployed',deployed:true,dormant:false}]};
const resumed=p.migrateSaveDetailed(JSON.parse(JSON.stringify(p.createPersistedSave(production))),catalog);
assert.equal(resumed.report.requiresRegeneration,false);
assert.equal(resumed.report.outcome,'current');
assert.ok(!resumed.report.unsupportedRetiredTypes.includes('Flayed One'));
for(const field of ['missionId','tombWorldVariant','restlessTombEnabled','deadlyEncountersEnabled','turningPoint','phase','nextSide','activationNumber','totalActivationsThisTP','playerActivated','npoActivated'])assert.deepStrictEqual(resumed.state[field],production[field],field);
assert.deepStrictEqual(resumed.state.deadlyEncountersState,production.deadlyEncountersState);
assert.deepStrictEqual(resumed.state.playerActivatedIds,production.playerActivatedIds);
assert.deepStrictEqual(resumed.state.activationHistory,production.activationHistory);
assert.deepStrictEqual(resumed.state.lastActivation,production.lastActivation);
assert.equal(resumed.state.roster[0].id,'flayed-one-production');
assert.equal(resumed.state.roster[0].wounds,7);
assert.equal(resumed.state.roster[0].weaponId,'flayer-claws');
const retired=p.migrateSaveDetailed({saveVersion:3,roster:[{id:'old',type:'Crypt Sentinel'}],playerRoster:[]},catalog);
assert.equal(retired.report.requiresRegeneration,true);
assert.deepEqual(retired.report.unsupportedRetiredTypes,['Crypt Sentinel']);
"""
    run_node(script)


def test_current_expansion_types_are_reported_separately_when_variant_illegal():
    migration = APP.split("function migrateSupportedSave", 1)[1].split(
        "function recoverInvalidMission", 1
    )[0]
    assert "invalidVariantNpos" in migration
    assert "variantAllowsExpansionNpo" in migration
    assert "unsupportedRetiredTypes" not in migration
    validator = APP.split("function variantAllowsExpansionNpo", 1)[1].split(
        "function commitNpoRoster", 1
    )[0]
    assert "variantId==='flayer-curse'" in validator
    assert "variantId==='destroyer-cult'" in validator
    assert "variantId==='crownworld'" in validator
    assert "return false" in validator
