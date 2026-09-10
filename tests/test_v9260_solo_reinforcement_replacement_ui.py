import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
RELEASE_VERSION = ".".join(("9", "2", "60"))
BASELINE_VERSION = ".".join(("9", "2", "59"))


def function_source(name):
    start = APP.index(f"function {name}")
    brace = APP.index("){", start) + 1
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(APP)):
        char = APP[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return APP[start : index + 1]
    raise AssertionError(f"Unclosed function: {name}")


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_release_surfaces_and_9259_baseline_history():
    assert f"## v{BASELINE_VERSION}" in README
    assert CURRENT_APP_VERSION == RELEASE_VERSION
    assert f"const APP_VERSION = '{RELEASE_VERSION}';" in WORKER
    assert f'<div class="version">V{RELEASE_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={RELEASE_VERSION}") == 10
    assert f"analytics.js?release={RELEASE_VERSION}" in INDEX
    assert README.startswith(
        f"# Tomb World Battle Guide v{RELEASE_VERSION}\n\n## v{RELEASE_VERSION}"
    )
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_resolver_clears_guide_owned_controls_but_keeps_pvp_choice_pending():
    resolver = function_source("resolveVariantNpoRequest")
    script = f"""
const assert=require('assert');
let mode='solo';
const state={{variantState:{{replacementTransactions:{{}}}}}};
const isPvpMode=()=>mode==='pvp';
const isFlayerCurseTomb=()=>true;
const isDestroyerCultTomb=()=>false;
const npoDefinition=()=>({{}});
const currentTombWorldVariant=()=>({{name:'Flayer Curse Infected Tomb'}});
const log=()=>{{}};
{resolver}
const request={{type:'Necron Warrior',weaponId:'gauss-flayer',replacementOptions:['Necron Warrior','Flayed One']}};
const solo=resolveVariantNpoRequest(request,{{transactionId:'reinforcement:2:0:Necron Warrior'}});
assert.equal(solo.type,'Flayed One');
assert.equal(solo.weaponId,undefined);
assert.equal(solo.replacementOptions,undefined);
assert.equal(solo.replacementTransactionId,undefined);
assert.deepEqual(state.variantState.replacementTransactions['reinforcement:2:0:Necron Warrior'],{{
  id:'reinforcement:2:0:Necron Warrior',originalType:'Necron Warrior',originalWeaponId:'gauss-flayer',
  options:['Necron Warrior','Flayed One'],selectedType:'Flayed One',owner:'guide',committed:true
}});
mode='pvp';
const pvp=resolveVariantNpoRequest(request,{{transactionId:'reinforcement:3:0:Necron Warrior'}});
assert.equal(pvp.type,'Necron Warrior');
assert.deepEqual(pvp.replacementOptions,['Necron Warrior','Flayed One']);
assert.equal(pvp.replacementTransactionId,'reinforcement:3:0:Necron Warrior');
assert.equal(state.variantState.replacementTransactions[pvp.replacementTransactionId].owner,'necron-controller');
assert.equal(state.variantState.replacementTransactions[pvp.replacementTransactionId].committed,false);
"""
    run_node(script)


def test_reinforcement_selector_is_driven_by_owner_and_pending_status():
    helper = function_source("isHumanNpoReplacementPending")
    script = f"""
const assert=require('assert');
let mode='solo';
const isPvpMode=()=>mode==='pvp';
const state={{variantState:{{replacementTransactions:{{
  solo:{{owner:'guide',committed:true}},
  pending:{{owner:'necron-controller',committed:false}},
  committed:{{owner:'necron-controller',committed:true}}
}}}}}};
{helper}
const staleSolo={{replacementOptions:['Necron Warrior','Flayed One'],replacementTransactionId:'solo'}};
assert.equal(isHumanNpoReplacementPending(staleSolo),false);
mode='pvp';
assert.equal(isHumanNpoReplacementPending({{replacementOptions:['Necron Warrior','Flayed One'],replacementTransactionId:'pending'}}),true);
assert.equal(isHumanNpoReplacementPending({{replacementOptions:['Necron Warrior','Flayed One'],replacementTransactionId:'committed'}}),false);
assert.equal(isHumanNpoReplacementPending(staleSolo),false);
const reloaded=JSON.parse(JSON.stringify({{replacementOptions:['Necron Warrior','Flayed One'],replacementTransactionId:'pending'}}));
assert.equal(isHumanNpoReplacementPending(reloaded),true);
"""
    run_node(script)


def test_solo_card_uses_final_instance_and_has_no_replacement_control():
    review = APP[APP.index("function strategyReviewStepHtml") : APP.index("function reinforcementBlockedReason")]
    assert "isHumanNpoReplacementPending(npo)?" in review
    assert "npoName(npo)" in review
    assert "npoDefinition(npo.type),npo.weaponId" in review
    assert 'data-reinforcement-placement="${escapeHtml(npo.id)}"' in review
    assert "Confirm placement for ${escapeHtml(npoName(npo))}" in review
    assert "data-reinforcement-replacement" in review
    assert "Randomly determine an open hatchway" in review
    helper = function_source("isHumanNpoReplacementPending")
    script = f"""
const assert=require('assert');
let mode='solo';
const flayed={{id:'flayed-one-5',name:'Flayed One 5',type:'Flayed One',weaponId:'flayer-claws',
  reinforcement:{{placementConfirmed:false}},replacementOptions:['Necron Warrior','Flayed One'],replacementTransactionId:'tx'}};
let state={{roster:[flayed],reinforcementState:{{operativeIds:[flayed.id],blocked:0,status:'placement'}},
  variantState:{{replacementTransactions:{{tx:{{owner:'guide',committed:true,originalType:'Necron Warrior',selectedType:'Flayed One'}}}}}},threat:2}};
const isPvpMode=()=>mode==='pvp';
{helper}
{review}
const sortedNposForDisplay=x=>x, opponentSingularLabel=()=>'Necron', opponentPluralLabel=()=>'Necrons';
const reinforcementBlockedReason=()=>'', escapeHtml=x=>String(x), npoName=n=>n.name;
const npoDefinition=()=>({{}}), npoWeapon=()=>({{name:'Flayer claws'}}), readyNpos=()=>[];
const threatGrade=()=>1, canLeaveStrategyEvents=()=>true, canCompleteStrategyPhase=()=>false;
const missionStrategyPending=()=>false, strategyProgressHtml=()=>'', strategyNavigationHtml=()=>'';
const window={{matchMedia:()=>({{matches:true}})}};
let html=strategyReviewStepHtml({{}});
assert.match(html,/Flayed One 5 · Flayer claws/);
assert.match(html,/data-reinforcement-placement="flayed-one-5"/);
assert.match(html,/Confirm placement for Flayed One 5/);
assert.doesNotMatch(html,/Choose NPO/);
assert.doesNotMatch(html,/data-reinforcement-replacement/);
assert.doesNotMatch(html,/Necron Warrior/);
state=JSON.parse(JSON.stringify(state));
html=strategyReviewStepHtml({{}});
assert.match(html,/Flayed One 5 · Flayer claws/);
assert.doesNotMatch(html,/Choose NPO|data-reinforcement-replacement/);
mode='pvp';
state.variantState.replacementTransactions.tx={{owner:'necron-controller',committed:false}};
html=strategyReviewStepHtml({{}});
assert.match(html,/Choose NPO/);
assert.match(html,/data-reinforcement-replacement="flayed-one-5"/);
state=JSON.parse(JSON.stringify(state));
assert.match(strategyReviewStepHtml({{}}),/data-reinforcement-replacement="flayed-one-5"/);
"""
    run_node(script)


def test_confirmation_only_commits_a_pending_human_replacement():
    confirmation = APP[
        APP.index("function confirmReinforcementPlacement") : APP.index(
            "async function rollInitiative"
        )
    ]
    assert "if(confirmed&&isHumanNpoReplacementPending(npo))" in confirmation
    assert "commitPvpNpoReplacement(npo,selected)" in confirmation
    assert "npo.reinforcement.placementConfirmed=Boolean(confirmed)" in confirmation
    assert "npo.deployed=npo.reinforcement.placementConfirmed" in confirmation
    assert "state.reinforcementState.operativeIds.every" in confirmation


def test_all_variant_paths_share_the_generic_resolution_rule():
    assert "replaceType:'Necron Warrior',replacements:['Flayed One']" in APP
    assert "replaceType:TOMB_CRAWLER_TYPE,replacements:['Skorpekh Destroyer','Hexmark Destroyer']" in APP
    assert "npoSetupReplacement:value=>crownworld" in APP
    assert "reinforcementGeneration:value=>optionalReplacement" in APP
    assert "const rr=resolveVariantNpoRequest(request" in APP
    assert "setupCrownworldCrawlerPair" in APP


def test_generation_probabilities_counts_and_placement_rules_are_untouched():
    resolver = function_source("resolveVariantNpoRequest")
    generation = function_source("processReinforcementStage")
    assert "isFlayerCurseTomb()&&options.includes('Flayed One')?'Flayed One'" in resolver
    assert "isDestroyerCultTomb()&&options.includes('Skorpekh Destroyer')?'Skorpekh Destroyer'" in resolver
    assert "const requested=gradeConfig(d.grade).reinforcements" in generation
    assert "actual=Math.min(requested,slots)" in generation
    assert "reinforcements.push(rr)" in generation
    assert "following the Tomb World reinforcement placement restrictions" in APP


def test_release_note_documents_scope_and_pvp_preservation():
    release = README.split(f"## v{RELEASE_VERSION}", 1)[1].split(
        f"## v{BASELINE_VERSION}", 1
    )[0]
    assert "Solo Reinforcement Replacement UX" in release
    assert "final generated operative" in release
    assert "human replacement choices in PvP" in release
    assert "save/resume state" in release
