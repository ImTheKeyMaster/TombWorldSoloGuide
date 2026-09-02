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


def test_zero_starting_npos_use_a_satisfied_not_complete_predicate():
    deployment = source("if(stepId==='deploy'){", "const m=mission();")
    assert "const hasStartingNpos=generation.deployedNpoIds.length>0" in deployment
    assert "const allNposPlaced=startingNpoDeploymentComplete(generation)" in deployment
    assert "const npoDeploymentSatisfied=!hasStartingNpos||allNposPlaced" in deployment
    assert "playerValid&&state.playerDeployed&&npoDeploymentSatisfied&&allPlacementChecked" in deployment
    assert "playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked" not in deployment


def test_zero_starting_npo_presentation_and_requirements_remain_implicit():
    deployment = source("if(stepId==='deploy'){", "const m=mission();")
    assert "This mission begins with no ${escapeHtml(opponentPluralLabel())} deployed." in deployment
    assert "const deploymentRow=hasStartingNpos&&deploymentCheck" in deployment
    assert "const requiredPlacementChecks=hasStartingNpos?placementChecks:otherPlacementChecks" in deployment
    assert "${hasStartingNpos?`<div class=\"setup-bulk-row\"" in deployment
    assert "setupChecks['starting-npos']" not in deployment


def test_completion_semantics_cover_zero_nonzero_variants_and_reload():
    completion = "function startingNpoDeploymentComplete" + source(
        "function startingNpoDeploymentComplete", "function setStartingNposDeployed"
    )
    script = f"""
const assert=require('assert');
let state;
{completion}
function deploymentState(generation,playerValid,playerDeployed,allPlacementChecked){{
  const hasStartingNpos=generation.deployedNpoIds.length>0;
  const allNposPlaced=startingNpoDeploymentComplete(generation);
  const npoDeploymentSatisfied=!hasStartingNpos||allNposPlaced;
  return {{hasStartingNpos,npoDeploymentSatisfied,enabled:playerValid&&playerDeployed&&npoDeploymentSatisfied&&allPlacementChecked}};
}}
for(const variant of ['standard','flayer-curse','destroyer-cult','crownworld']){{
  for(const restlessTombEnabled of [false,true]){{
    state={{tombWorldVariant:variant,restlessTombEnabled,roster:[]}};
    const generation={{deployedNpoIds:[],reserveNpoIds:[]}};
    assert.deepEqual(deploymentState(generation,true,true,true),{{hasStartingNpos:false,npoDeploymentSatisfied:true,enabled:true}});
    assert.equal(deploymentState(JSON.parse(JSON.stringify(generation)),true,true,true).enabled,true);
    assert.equal(deploymentState(generation,false,true,true).enabled,false);
    assert.equal(deploymentState(generation,true,false,true).enabled,false);
    assert.equal(deploymentState(generation,true,true,false).enabled,false);
  }}
}}
const generation={{deployedNpoIds:['a','b'],reserveNpoIds:['reserve']}};
state={{roster:[{{id:'a',deployed:false,battlefieldState:'reserve'}},{{id:'b',deployed:false,battlefieldState:'reserve'}},{{id:'reserve',deployed:false,battlefieldState:'reserve'}}]}};
assert.equal(deploymentState(generation,true,true,true).enabled,false);
state.roster.find(npo=>npo.id==='a').deployed=true;
state.roster.find(npo=>npo.id==='a').battlefieldState='deployed';
state.roster.find(npo=>npo.id==='b').deployed=true;
state.roster.find(npo=>npo.id==='b').battlefieldState='deployed';
assert.equal(deploymentState(generation,true,true,true).enabled,true);
"""
    subprocess.run(["node", "-e", script], check=True)


def test_check_all_remains_hidden_for_zero_and_authoritative_for_nonzero():
    deployment = source("if(stepId==='deploy'){", "const m=mission();")
    handler = source("$('#checkAllDeployment')?.addEventListener", "$$('[data-roster-category-toggle]')")
    assert "${hasStartingNpos?`<div class=\"setup-bulk-row\"" in deployment
    assert "npoDeploymentSatisfied&&allPlacementChecked" in deployment
    assert "setStartingNposDeployed(true)" in handler
    assert "if(playerRosterValidation().valid)state.playerDeployed=true" in handler


def test_generation_variants_scout_and_crownworld_rules_are_unchanged():
    variants = source("const TOMB_WORLD_VARIANTS", "function currentTombWorldVariant")
    for variant in ("standard", "flayer-curse", "destroyer-cult", "crownworld"):
        assert variant in variants
    assert '"formula": "0"' in (ROOT / "Missions/05-scout-sub-crypt.json").read_text()
    crownworld = source("function setupCrownworldCrawlerPair", "function rollNpo")
    assert "commitNpoRoster([...remaining,warden,lychguard]" in crownworld
    assert "state.variantState.crownworldFirstCrawlerConsumed=true" in crownworld
    scout = (ROOT / "Player_Operatives/ScoutSquad.json").read_text(encoding="utf-8")
    assert "Scout Heavy Gunner" in scout
    assert "Scout Warrior" in scout


def test_v9229_release_and_save_compatibility_surfaces():
    version = CURRENT_APP_VERSION
    assert tuple(map(int, version.split("."))) >= (9, 2, 29)
    assert f"const APP_VERSION = '{version}';" in APP
    assert f"const APP_VERSION = '{version}';" in WORKER
    assert f'<div class="version">V{version}</div>' in INDEX
    assert INDEX.count(f"?v={version}") == 10
    assert "tomb-world-battle-guide-${APP_VERSION}" not in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{version}\n\n## v{version}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
