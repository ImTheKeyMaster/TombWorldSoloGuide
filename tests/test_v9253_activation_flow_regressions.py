from pathlib import Path
import json
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
EXPECTED_VERSION = ".".join(("9", "2", str(52 + 1)))


def source(start, end):
    offset = APP.index(start)
    return APP[offset:APP.index(end, offset)]


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_release_surfaces_are_v9253_without_save_key_change():
    assert CURRENT_APP_VERSION == EXPECTED_VERSION
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{EXPECTED_VERSION}</div>' in index
    assert index.count(f"?v={EXPECTED_VERSION}") == 10


def test_completed_activation_clears_transaction_state_before_scheduling():
    advance = source("function advanceAfterActivation", "const GRADE_CONFIG")
    for transient in (
        "pendingDice",
        "combatState",
        "fightState",
        "missionActionContext",
        "weaponRuleResolution",
        "hotResolution",
    ):
        assert f"state.{transient}=null" in advance
    assert advance.index("state.hotResolution=null") < advance.index("setNextActivation")


def test_skip_guard_still_blocks_every_unresolved_transaction_type():
    guard = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "const safe=" in guard and "if(!safe)return false" in guard
    for transient in (
        "state.pendingDice",
        "state.combatState",
        "state.fightState",
        "state.missionActionContext",
        "state.weaponRuleResolution",
        "state.hotResolution",
    ):
        assert transient in guard


def test_clean_solo_necron_card_can_offer_skip_after_activation_completion():
    functions = source("function canSkipRemainingActivations", "function destroyedNpoCount")
    result = run_node(f"""
let state={{phase:'firefight',completed:false,gameEnd:null,nextSide:'npo',lastActivation:{{side:'player',committed:true,completed:true}},
 pendingDice:null,combatState:null,fightState:null,missionActionContext:null,weaponRuleResolution:null,hotResolution:null,npoActivated:1}};
const readyNpos=()=>[{{id:'n1'}},{{id:'n2'}}],playerOperativesRemaining=()=>4,isPvpMode=()=>false;
const selectedPlayerTeamName=()=> 'Death Korps',escapeHtml=value=>value;
const activationModelLabel=(side,options)=>side==='npo'&&options.plural?'Necrons':'Operatives';
{functions}
console.log(JSON.stringify({{allowed:canSkipRemainingActivations(),control:skipRemainingActivationsControl()}}));
""")
    assert result["allowed"] is True
    assert "Skip Remaining Necrons" in result["control"]


def test_exactly_one_ready_player_operative_bypasses_selection_dialog():
    selection = source("function showPlayerActivation", "function playerActivationSummary")
    result = run_node(f"""
let state={{playerReady:1}},begun=[],modals=0;
const activePlayerActivation=()=>null,resumeCheckpointedGameplayContext=()=>{{}},remainingPlayerOperatives=()=>['only-ready'];
const beginPlayerActivation=id=>{{begun.push(id);return true;}},setNextActivation=()=>{{}},save=()=>{{}},render=()=>{{}};
const escapeHtml=value=>value,playerName=id=>id,selectedPlayerTeamName=()=> 'Kasrkin';
const showModal=()=>{{modals++;}},$=()=>({{}});
{selection}
showPlayerActivation();
console.log(JSON.stringify({{begun,modals}}));
""")
    assert result == {"begun": ["only-ready"], "modals": 0}


def test_multiple_ready_player_operatives_still_use_existing_picker():
    selection = source("function showPlayerActivation", "function playerActivationSummary")
    assert "if(candidates.length===1){beginPlayerActivation(candidates[0]);return;}" in selection
    assert selection.index("candidates.length===1") < selection.index("showModal(")
    assert '<select id="humanPlayerSelection"' in selection
