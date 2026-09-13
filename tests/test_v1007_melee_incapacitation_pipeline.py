"""End-to-end regression coverage for staged lethal Player Fight damage."""
from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def body(name):
    match = re.search(rf"  (?:async )?function {name}\([^\n]*\)\{{", APP)
    assert match, name
    start, depth = match.start(), 0
    for index in range(APP.find("{", match.start()), len(APP)):
        if APP[index] == "{":
            depth += 1
        elif APP[index] == "}":
            depth -= 1
            if depth == 0:
                return APP[start:index + 1]
    raise AssertionError(name)


def test_lethal_macrocyte_fight_stages_then_runs_authoritative_pipeline():
    sources = "\n".join(body(name) for name in (
        "otherFightRole", "unresolvedFightSuccesses", "advanceFightTurn",
        "resolveFightShock", "setFightOperativeWounds", "commitFightStrike",
        "fightRoleDamage", "fightResultExplanation", "buildFightResult",
        "pendingAttackResults", "continuePlayerMultiTargetAttack",
        "acknowledgeFightResult", "applyPendingPlayerDamage",
    ))
    script = f"""
let aggressiveCalls=0, saves=0, fightCompletionInProgress=false, activeFightContinuation=null, resolvedStage=null;
const state={{turningPoint:1,activationNumber:1,playerWounds:{{p:10}},playerCasualtyIds:[],playerRoster:['p'],roster:[{{id:'m',type:'Canoptek Macrocyte Warrior',wounds:3,ready:true,deployed:true,battlefieldState:'deployed'}}],npoRuleState:{{incapacitationTriggers:[],oncePerTurningPoint:{{}},stage3Triggers:{{}}}},eventState:{{reanimationAttempts:{{}}}},weaponRuleResolution:null,fightState:null}};
const save=()=>{{saves++;}}, playerOperativesRemaining=()=>1, weaponHasRule=()=>false;
const resolveNpoIncapacitation=()=>({{candidates:[]}}), activeNpos=()=>state.roster.filter(n=>n.wounds>0&&n.deployed);
const eventTransaction=()=>({{}}), isPvpMode=()=>false, npoDefinition=()=>({{id:'macrocyte'}});
const showAggressiveDefenseResolution=(stage,pending)=>{{aggressiveCalls++;pending.pipelineObserved={{after:pending.after,within:pending.attackerWithinTwo,targetWounds:state.roster[0].wounds}};}};
const showIncapacitationOrderChoice=offerReanimateForPendingDamage=showReanimationProtocolsResolution=()=>{{throw Error('unexpected prevention UI')}};
const resolveMultiThreatEliminator=()=>{{}}, finishPlayerAttackResolution=()=>{{}}, checkGameEnd=()=>false;
const playerName=id=>id, npoName=n=>n.type, log=()=>{{}}, applyTemporaryAplModifier=()=>{{}};
const restoreFightContinuation=()=>activeFightContinuation;
const resolvePendingPlayerAttacks=stage=>{{resolvedStage=stage;return applyPendingPlayerDamage(stage);}};
{sources}
const fight={{id:'fight-1',attackerWithinTwo:true,attacker:{{side:'player',id:'p',label:'Player',initialWounds:10,wounds:10,profile:{{name:'Blade',normal:4,crit:4}}}},defender:{{side:'npo',id:'m',label:'Macrocyte',initialWounds:3,wounds:3,profile:{{name:'Claws',normal:3,crit:3}}}},successes:{{attacker:[{{id:'hit',kind:'normal',status:'unresolved'}}],defender:[]}},turn:'attacker',resolutionIndex:0,history:[],ruleTriggers:{{}},completed:false}};
if(!commitFightStrike(fight,'attacker','hit')||fight.defender.wounds!==0||!fight.completed)process.exit(1);
if(state.roster[0].wounds!==3||!state.roster[0].deployed)process.exit(2);
const result=buildFightResult(fight);
if(result.committed||result.before!==3||result.after!==0||result.damage!==3||result.attackerWithinTwo!==true)process.exit(3);
fight.result=result;state.fightState=fight;
const stage={{playerOperativeId:'p',pendingMeleeResults:[]}};
activeFightContinuation=pending=>continuePlayerMultiTargetAttack(stage,'melee',pending);
const restoredFight=JSON.parse(JSON.stringify(fight));
state.fightState=restoredFight;
acknowledgeFightResult(restoredFight);
if(!restoredFight.resultAcknowledged||state.fightState!==null||fightCompletionInProgress)process.exit(4);
const pending=resolvedStage?.pendingMeleeResults[0];
if(resolvedStage?.pendingMeleeResults.length!==1||pending.transactionId!==result.transactionId||aggressiveCalls!==1)process.exit(5);
if(pending.pipelineObserved.after!==0||!pending.pipelineObserved.within||pending.pipelineObserved.targetWounds!==3)process.exit(6);
if(state.roster[0].wounds!==3||pending.committed)process.exit(7);
pending.aggressiveDefenseResolved=true;
if(applyPendingPlayerDamage(resolvedStage)||!pending.committed)process.exit(8);
if(state.roster[0].wounds!==0||state.roster[0].deployed||state.roster[0].battlefieldState!=='out-of-action')process.exit(9);
if(applyPendingPlayerDamage(resolvedStage)||aggressiveCalls!==1)process.exit(10);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_nonlethal_and_opposite_direction_still_commit_immediately():
    sources = "\n".join(body(name) for name in (
        "otherFightRole", "unresolvedFightSuccesses", "advanceFightTurn",
        "resolveFightShock", "setFightOperativeWounds", "commitFightStrike",
    ))
    script = f"""
const state={{playerWounds:{{p:3}},playerCasualtyIds:[],playerRoster:['p'],roster:[{{id:'n',wounds:3,ready:true,deployed:true,battlefieldState:'deployed'}}]}};
const save=()=>{{}},playerOperativesRemaining=()=>1,weaponHasRule=()=>false;
const resolveRewardsOfAnnihilation=()=>{{}};
{sources}
const makeFight=(attacker,defender)=>({{id:'fight',attacker,defender,successes:{{attacker:[{{id:'a',kind:'normal',status:'unresolved'}}],defender:[{{id:'d',kind:'normal',status:'unresolved'}}]}},turn:'attacker',resolutionIndex:0,history:[],ruleTriggers:{{}},completed:false}});
let fight=makeFight({{side:'player',id:'p',wounds:3,profile:{{normal:1,crit:1}}}},{{side:'npo',id:'n',wounds:3,profile:{{normal:3,crit:3}}}});
commitFightStrike(fight,'attacker','a');
if(state.roster[0].wounds!==2||fight.defender.wounds!==2||fight.completed)process.exit(1);
state.roster[0].wounds=3;state.roster[0].deployed=true;state.roster[0].battlefieldState='deployed';
fight=makeFight({{side:'npo',id:'n',wounds:3,profile:{{normal:3,crit:3}}}},{{side:'player',id:'p',wounds:3,profile:{{normal:3,crit:3}}}});
fight.turn='defender';
commitFightStrike(fight,'defender','d');
if(state.roster[0].wounds!==0||state.roster[0].deployed||fight.attacker.wounds!==0)process.exit(2);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_pipeline_transport_ui_and_save_contract_are_preserved():
    assert "activeFightContinuation=result=>continuePlayerMultiTargetAttack(playerStage,'melee',result)" in body("restoreFightContinuation")
    assert "attackerWithinTwo:Boolean(fight.attackerWithinTwo)" in body("buildFightResult")
    assert "Attacker is within 2\"" not in body("showPlayerCombatResolution")
    fields = body("aggressiveDefenseFields")
    assert "attackType==='shoot'" in fields and 'Attacker is within 2&quot; of this Macrocyte' in fields
    assert CURRENT_APP_VERSION == "10.0.7"
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
