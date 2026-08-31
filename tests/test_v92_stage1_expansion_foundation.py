import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_options_step_precedes_deploy_and_progress_uses_active_steps():
    steps = source("function activeSetupSteps()", "function currentSetupStepId()")
    assert "steps.push('playerRoster','options','deploy','ready')" in steps
    assert "if(hasMultiplePlayerTeams())steps.push('team')" in steps
    render = source("function renderSetup()", "function renderGameModeSelection()")
    assert "${state.setupStep+1} / ${steps.length}" in render
    assert "((state.setupStep+1)/steps.length)*100" in render


def test_optional_controls_are_editable_only_on_options_step():
    options = source("if(stepId==='options')", "if(stepId==='deploy')")
    assert 'id="restlessTombEnabled"' in options
    assert 'id="deadlyEncountersEnabled"' in options
    assert "isPvpMode()" in options and "available in Solo battles only" in options
    briefing = source("return `<h3>Mission Briefing</h3>", "function advanceSetupStep")
    assert 'id="restlessTombEnabled"' not in briefing
    assert 'id="deadlyEncountersEnabled"' not in briefing
    assert '<strong id="briefing-restless-tomb-title">Restless Tomb</strong>' in briefing
    assert '<strong id="briefing-deadly-encounters-title">Deadly Encounters</strong>' in briefing
    assert 'id="briefing-variant-title"' in briefing


def test_variant_registry_is_complete_and_released():
    registry = source("const TOMB_WORLD_VARIANTS", "const initialState")
    assert "standard:Object.freeze({id:'standard',name:'Standard Tomb World',available:true" in registry
    for variant in ("flayer-curse", "destroyer-cult", "crownworld"):
        assert f"id:'{variant}'" in registry
    assert registry.count("available:true") == 4
    options = source("if(stepId==='options')", "if(stepId==='deploy')")
    assert 'name="tombWorldVariant"' in options
    assert "Object.values(TOMB_WORLD_VARIANTS).filter" in options


def test_variant_helpers_and_all_stage_one_hooks_are_centralized_and_inert():
    registry = source("const inertVariantHooks", "const initialState")
    for hook in (
        "startingRosterGeneration",
        "reinforcementGeneration",
        "eventGeneratedNpoReplacement",
        "eventDeckAdditions",
        "missionRequestedNpoReplacement",
    ):
        assert hook in registry
    for helper in (
        "currentTombWorldVariant",
        "isFlayerCurseTomb",
        "isDestroyerCultTomb",
        "isCrownworldTomb",
    ):
        assert f"function {helper}" in registry
    assert "tombWorldVariantHook('startingRosterGeneration'" in APP
    assert "tombWorldVariantHook('reinforcementGeneration'" in APP
    assert "function replaceEventGeneratedNpo(request)" in registry
    assert "function replaceMissionRequestedNpo(request)" in registry


def test_variant_change_invalidates_only_generated_npo_setup():
    invalidation = source("function invalidateStartingNpoSetup()", "function satisfyEmptyStartingNpoDeployment()")
    assert "state.roster=[]" in invalidation
    assert "state.startingNpoGeneration=null" in invalidation
    assert "delete state.setupChecks['starting-npos']" in invalidation
    assert "state.playerRoster" not in invalidation
    assert "restlessTombEnabled" not in invalidation
    assert "deadlyEncountersEnabled" not in invalidation
    bindings = source("function bindSetup(stepId)", "function runStartingNpoGeneration()")
    assert "invalidateStartingNpoSetup" not in bindings


def test_variant_defaults_and_persists_without_save_schema_bump():
    assert "tombWorldVariant:'standard'" in APP
    assert "merged.tombWorldVariant=TOMB_WORLD_VARIANTS[raw.tombWorldVariant]?raw.tombWorldVariant:'standard'" in APP
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    script = r"""
const p=require('./persistence.js');
const catalog={'Test NPO':{id:'test',type:'Test NPO',name:'Test NPO',wounds:1,move:1,apl:1,save:1,baseSize:1,physicalQuantity:10,defaultWeaponId:'test'}};
const base={saveVersion:p.currentSaveVersion(),roster:[],playerRoster:[]};
for(const variant of ['standard','flayer-curse','destroyer-cult','crownworld']){
  const saved=p.createPersistedSave({...base,tombWorldVariant:variant});
  if(p.migrateSaveDetailed(JSON.parse(JSON.stringify(saved)),catalog).state.tombWorldVariant!==variant)process.exit(1);
}
if(p.migrateSaveDetailed(base,catalog).state.tombWorldVariant!=='standard')process.exit(2);
const generated={dice:[1],missionRoll:1,deploymentCount:1,availableNpos:0,deployedNpoIds:[],reserveNpoIds:[]};
const oldDeployWithTeam=p.migrateSaveDetailed({...base,screen:'setup',setupStep:4,startingNpoGeneration:generated},catalog).state;
if(oldDeployWithTeam.setupStep!==5||oldDeployWithTeam.tombWorldVariant!=='standard')process.exit(3);
const oldDeployWithoutTeam=p.migrateSaveDetailed({...base,screen:'setup',setupStep:3,startingNpoGeneration:generated},catalog).state;
if(oldDeployWithoutTeam.setupStep!==4||oldDeployWithoutTeam.tombWorldVariant!=='standard')process.exit(4);
const currentDeploy=p.migrateSaveDetailed({...base,screen:'setup',setupStep:5,tombWorldVariant:'standard'},catalog).state;
if(currentDeploy.setupStep!==5)process.exit(5);
const oldPlayerRoster=p.migrateSaveDetailed({...base,screen:'setup',setupStep:3},catalog).state;
if(oldPlayerRoster.setupStep!==3)process.exit(6);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_stage_one_adds_no_new_playable_npos_or_events_and_keeps_version():
    forbidden = (
        "Flesh Hunger",
        "Rewards of Annihilation",
        "Enforcer of the Phaerons",
    )
    event_deck = source("const eventDeck = [", "const missionStateFactories")
    assert all(name not in event_deck for name in forbidden)
    generation_table = source("const npoGenerationTable", "const eventDeck")
    for name in ("Flayed One", "Skorpekh Destroyer", "Hexmark Destroyer", "Royal Warden", "Lychguard"):
        assert name not in generation_table
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP


def test_mobile_option_styles_wrap_and_touch_targets_remain_intact():
    styles = (ROOT / "styles.css").read_text(encoding="utf-8")
    assert ".check-row input{width:22px;height:22px" in styles
    assert ".rule-classification{display:block;width:max-content;max-width:100%" in styles
    assert "@media(max-width:390px){.optional-rules .check-row{align-items:flex-start}.rule-classification{width:auto}" in styles
    assert ".wizard-shell>.wizard-card>.wizard-actions{position:fixed" in styles
