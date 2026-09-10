from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def full_function(start, end):
    return start + source(start, end)


def test_completion_uses_current_physical_starting_selection():
    completion = source(
        "function startingNpoDeploymentComplete",
        "function setStartingNposDeployed",
    )
    assert "deployedIds=generation?.deployedNpoIds||[]" in completion
    assert "deployedIdSet.size===deployedIds.length" in completion
    assert "reserveIdSet.size===reserveIds.length" in completion
    assert "!reserveIdSet.has(id)" in completion
    assert "npo.id===id&&npo.deployed&&npo.battlefieldState==='deployed'" in completion
    assert "npo.id===id&&!npo.deployed&&npo.battlefieldState==='reserve'" in completion
    assert "deploymentCount" not in completion
    assert "availableNpos" not in completion


def test_completion_executes_for_standard_crownworld_reload_and_reserves():
    completion = full_function(
        "function startingNpoDeploymentComplete",
        "function setStartingNposDeployed",
    )
    script = f"""
let state;
{completion}
const assert=require('assert');
const physicalIds=['macrocyte-1','macrocyte-2','lychguard','warrior-1','warrior-2','warrior-3','warrior-4','warden'];
const generation={{deploymentCount:7,availableNpos:10,deployedNpoIds:physicalIds,reserveNpoIds:['reserve-1','reserve-2','reserve-3']}};
state={{startingNpoGeneration:generation,roster:[...physicalIds.map(id=>({{id,deployed:true,battlefieldState:'deployed'}})),...generation.reserveNpoIds.map(id=>({{id,deployed:false,battlefieldState:'reserve'}}))]}};
assert.equal(startingNpoDeploymentComplete(),true);
state=JSON.parse(JSON.stringify(state));
assert.equal(startingNpoDeploymentComplete(),true);
state.roster.find(npo=>npo.id==='warden').deployed=false;
assert.equal(startingNpoDeploymentComplete(),false);
state.roster.find(npo=>npo.id==='warden').deployed=true;
state.roster.find(npo=>npo.id==='reserve-1').deployed=true;
state.roster.find(npo=>npo.id==='reserve-1').battlefieldState='deployed';
assert.equal(startingNpoDeploymentComplete(),false);
state.roster.find(npo=>npo.id==='reserve-1').deployed=false;
state.roster.find(npo=>npo.id==='reserve-1').battlefieldState='reserve';
state.startingNpoGeneration.reserveNpoIds.push('warden');
assert.equal(startingNpoDeploymentComplete(),false);
for(const variant of ['standard','flayer-curse','destroyer-cult']){{
  state={{tombWorldVariant:variant,startingNpoGeneration:{{deploymentCount:2,availableNpos:3,deployedNpoIds:['a','b'],reserveNpoIds:['r']}},roster:[{{id:'a',deployed:true,battlefieldState:'deployed'}},{{id:'b',deployed:true,battlefieldState:'deployed'}},{{id:'r',deployed:false,battlefieldState:'reserve'}}]}};
  assert.equal(startingNpoDeploymentComplete(),true);
}}
"""
    subprocess.run(["node", "-e", script], check=True)


def test_manual_deployment_uses_shared_authoritative_helper_and_one_render():
    binding = source("$('#npoDeployed')?.addEventListener", "$('#checkAllDeployment')")
    assert "setStartingNposDeployed(e.target.checked)" in binding
    assert binding.count("save();render()") == 1
    generic = source("$$('[data-check]')", "$('#checkAllSetup')")
    assert "c.id!=='npoDeployed'" in generic


def test_shared_helper_marks_current_models_and_setup_confirmation():
    helper = source("function setStartingNposDeployed", "function generateRoster")
    assert "const selected=new Set(generation.deployedNpoIds||[])" in helper
    assert "npo.deployed=deployed" in helper
    assert "npo.battlefieldState=deployed?'deployed':'reserve'" in helper
    assert "npo.deployed=false" in helper
    assert "npo.battlefieldState='reserve'" in helper
    assert "state.setupChecks['starting-npos']=Boolean(deployed)" in helper
    assert "save()" not in helper
    assert "render()" not in helper


def test_crownworld_replacement_updates_ids_once_without_uncheck_reversal():
    helper = source("function setStartingNposDeployed", "function generateRoster")
    assert "deployed&&!state.variantState.crownworldFirstCrawlerConsumed" in helper
    assert "setupCrownworldCrawlerPair(crawler" in helper
    assert "selected.delete(crawler.id)" in helper
    assert "pair.npos.forEach(npo=>selected.add(npo.id))" in helper
    assert "generation.deployedNpoIds=[...selected]" in helper
    assert "setupCrownworldCrawlerPair" not in helper.split("if(deployed", 1)[0]
    pair = source("function setupCrownworldCrawlerPair", "function rollNpo")
    assert "state.variantState.crownworldFirstCrawlerConsumed=true" in pair
    assert "commitNpoRoster([...remaining,warden,lychguard]" in pair


def test_shared_helper_executes_replacement_once_across_uncheck_and_recheck():
    helper = full_function("function setStartingNposDeployed", "function generateRoster")
    script = f"""
const assert=require('assert');
const TOMB_CRAWLER_TYPE='Canoptek Tomb Crawler';
let replacementCalls=0;
const crawler={{id:'crawler',type:TOMB_CRAWLER_TYPE,deployed:false,battlefieldState:'reserve'}};
const reserve={{id:'reserve',type:'Necron Warrior',deployed:false,battlefieldState:'reserve'}};
const state={{startingNpoGeneration:{{deploymentCount:1,availableNpos:2,deployedNpoIds:['crawler'],reserveNpoIds:['reserve']}},roster:[crawler,reserve],setupChecks:{{}},variantState:{{crownworldFirstCrawlerConsumed:false}}}};
function setupCrownworldCrawlerPair(){{
  replacementCalls++;
  const pair=[{{id:'warden',deployed:true,battlefieldState:'deployed'}},{{id:'lychguard',deployed:true,battlefieldState:'deployed'}}];
  state.roster=[reserve,...pair];
  state.variantState.crownworldFirstCrawlerConsumed=true;
  return {{replaced:true,npos:pair}};
}}
function showToast(){{}}
{helper}
assert.equal(setStartingNposDeployed(true),true);
assert.deepEqual(new Set(state.startingNpoGeneration.deployedNpoIds),new Set(['warden','lychguard']));
assert.equal(replacementCalls,1);
assert.equal(state.setupChecks['starting-npos'],true);
assert.equal(reserve.deployed,false);
assert.equal(reserve.battlefieldState,'reserve');
setStartingNposDeployed(false);
assert.equal(state.setupChecks['starting-npos'],false);
assert(state.roster.filter(npo=>['warden','lychguard'].includes(npo.id)).every(npo=>!npo.deployed&&npo.battlefieldState==='reserve'));
setStartingNposDeployed(true);
assert.equal(replacementCalls,1);
assert.equal(state.roster.filter(npo=>['warden','lychguard'].includes(npo.id)).length,2);
assert(state.roster.filter(npo=>['warden','lychguard'].includes(npo.id)).every(npo=>npo.deployed&&npo.battlefieldState==='deployed'));
"""
    subprocess.run(["node", "-e", script], check=True)


def test_display_count_and_renderer_follow_transformed_ids():
    deployment = source("if(stepId==='deploy'){", "const m=mission();")
    assert "Deploy the ${generation.deployedNpoIds.length} selected starting" in deployment
    assert "startingNpoDeploymentComplete(generation)" in deployment
    assert "generation.deployedNpoIds.length===generation.deploymentCount" not in deployment
    assert "generation.deployedNpoIds.length+generation.reserveNpoIds.length" not in deployment


def test_check_all_uses_state_not_dom_events_and_preserves_player_validation():
    handler = source("$('#checkAllDeployment')?.addEventListener", "$$('[data-roster-category-toggle]')")
    assert "missionSetupChecks('deploy').filter(check=>check.id!=='starting-npos')" in handler
    assert "setStartingNposDeployed(true)" in handler
    assert "if(playerRosterValidation().valid)state.playerDeployed=true" in handler
    assert handler.count("save();render()") == 1
    assert "dispatchEvent" not in handler
    assert "checkbox.checked" not in handler


def test_all_variant_hooks_remain_available_without_generation_rule_changes():
    variants = source("const TOMB_WORLD_VARIANTS", "function currentTombWorldVariant")
    for variant in ("standard", "flayer-curse", "destroyer-cult", "crownworld"):
        assert variant in variants
    roll = source("function startingNpoRoll", "function restoredStartingNpoGeneration")
    selection = source("function selectStartingNpos", "function startingNpoDeploymentComplete")
    assert "deploymentCount:Math.min(missionRoll,MAX_NPOS)" in roll
    assert "generation.deploymentCount=Math.min(generation.missionRoll,available.length)" in selection


def test_release_and_save_compatibility_surfaces():
    version = CURRENT_APP_VERSION
    assert f"const APP_VERSION = '{version}';" in APP
    assert f"const APP_VERSION = '{version}';" in WORKER
    assert f'<div class="version">V{version}</div>' in INDEX
    assert INDEX.count(f"?v={version}") == 10
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "tomb-world-battle-guide-" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{version}\n\n## v{version}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
