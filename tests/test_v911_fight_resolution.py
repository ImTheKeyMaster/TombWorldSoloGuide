"""Focused acceptance coverage for the current release shared Fight resolution."""
from pathlib import Path
import re
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
HTML=(ROOT/'index.html').read_text()
CSS=(ROOT/'styles.css').read_text()
README=(ROOT/'README.md').read_text()
WORKER=(ROOT/'service-worker.js').read_text()


def body(name):
    match=re.search(rf"  (?:async )?function {re.escape(name)}\([^\n]*\)\{{",APP)
    assert match, name
    start=match.start(); depth=0
    signature_end=APP.find('){',start)+1
    for index in range(signature_end,len(APP)):
        if APP[index]=='{': depth+=1
        elif APP[index]=='}':
            depth-=1
            if depth==0:return APP[start:index+1]
    raise AssertionError(name)


def test_release_surfaces_and_save_contract():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP and f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'V{CURRENT_APP_VERSION}' in HTML and all(f'?v={CURRENT_APP_VERSION}' in line for line in HTML.splitlines() if 'styles.css?v=' in line or '<script src=' in line)
    assert README.startswith(f'# Tomb World Battle Guide v{CURRENT_APP_VERSION}')
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert 'const SAVE_VERSION = 3;' in (ROOT/'persistence.js').read_text()


def test_one_persisted_shared_fight_engine_and_stable_success_ids():
    assert 'fightState:null' in APP and 'normalizeFightState(raw.fightState)' in APP
    assert 'commitFightStrike' in APP and 'commitFightBlock' in APP
    assert '${id}:${role}:${index}:${die.kind}' in body('fightSuccessesFromDice')
    assert 'PlayerFightEngine' not in APP and 'NpoFightEngine' not in APP


def test_both_fighters_roll_attack_dice_and_no_fight_defense_roll():
    roll=body('rollFightParticipant')
    assert 'requestAttackDiceForProfile' in roll
    assert 'requestDefenseDice' not in roll and 'saveDice' not in roll
    start=body('startSharedFight')
    assert "rollFightParticipant(fight,'attacker')" in start
    assert "rollFightParticipant(fight,'defender')" in start


def test_attacker_first_and_turns_alternate_or_exhaust_remaining_pool():
    assert "turn:'attacker'" in body('startSharedFight')
    advance=body('advanceFightTurn')
    assert 'otherFightRole(fight.turn)' in advance
    assert 'unresolvedFightSuccesses(fight,other)' in advance


def test_strikes_consume_success_and_commit_normal_or_critical_damage_immediately():
    strike=body('commitFightStrike')
    assert "success.status='struck'" in strike
    assert "success.kind==='critical'?actor.profile.crit:actor.profile.normal" in strike
    assert 'setFightOperativeWounds(target,after)' in strike
    assert "if(after<=0){fight.completed=true" in strike


def test_blocks_consume_both_successes_and_preserve_legality():
    block=body('commitFightBlock'); legal=body('fightBlockTargets')
    assert "blocker.status='blocked'" in block and "target.status='blocked'" in block
    assert "blocker.kind==='critical'||target.kind==='normal'" in legal
    assert 'targetSuccessIds' in block and 'blockCapacity' in block


def test_brutal_is_shared_and_tomb_crawler_profile_is_corrected():
    assert "weaponHasRule(opponent.profile,'brutal')" in body('fightBlockTargets')
    assert "name:'Claws',type:'melee',attacks:4,hit:4,damage:{normal:4,critical:4},rules:['Brutal'],ruleIds:['brutal']" in APP


def test_shock_is_strike_timed_normal_first_and_idempotent():
    shock=body('resolveFightShock'); strike=body('commitFightStrike'); block=body('commitFightBlock')
    assert "find(item=>item.kind==='normal')||pool.find(item=>item.kind==='critical')" in shock
    assert 'fight.ruleTriggers[key]=true' in shock
    assert "success.kind==='critical'?resolveFightShock" in strike
    assert 'resolveFightShock' not in block
    assert 'showGuidedShockStep(combat' not in body('showNpoAttackWizard')


def test_stun_uses_retained_criticals_before_resolution():
    roll=body('rollFightParticipant')
    assert 'applyStunForAttack' in roll
    assert 'commitFightStrike' not in body('applyStunForAttack')


def test_solo_npo_is_deterministic_and_prefers_kill_then_lethal_block():
    ai=body('soloNpoFightDecision')
    assert '>=opponent.wounds' in ai and '>=actor.wounds' in ai
    assert "type:'block'" in ai and "type:'strike'" in ai
    render=body('renderFightResolution')
    assert "participant.side==='player'||isPvpMode()" in render


def test_human_controls_are_legal_accessible_and_mobile_first():
    render=body('renderFightResolution')
    assert 'aria-label="Strike with ${success.kind} success' in render
    assert 'aria-label="Block opponent ${target.kind} success' in render
    assert 'fightBlockTargets(fight,role,blocker)' in render
    assert '.fight-actions' in CSS and 'min-height:48px' in CSS
    assert '@media (max-width:374px)' in CSS


def test_player_and_npo_flows_both_enter_shared_engine():
    player=body('showPlayerCombatResolution'); npo=body('showNpoAttackWizard')
    assert "if(attackType==='melee')" in player and 'startSharedFight' in player
    assert "if(attackType==='melee')" in npo and 'startSharedFight' in npo
    assert 'choosePlayerRetaliationWeapon' in npo


def test_shoot_remains_on_aggregate_attack_vs_defense_path():
    player=body('showPlayerCombatResolution'); npo=body('showNpoAttackWizard')
    assert 'runAutomaticCombatRolls' in player and 'runAutomaticCombatRolls' in npo
    assert 'resolveRetainedCombat' in APP
    assert "if(attackType==='melee')" in player


def test_pending_dice_and_fight_identity_are_durable():
    start=body('startSharedFight'); roll=body('rollFightParticipant')
    assert 'state.fightState?.id===id' in start
    assert '`fight:${fight.id}:${role}`' in roll
    assert 'requestAttackDiceForProfile' in roll
    assert 'save()' in body('commitFightStrike') and 'save()' in body('commitFightBlock')


def test_legacy_in_progress_melee_reset_is_narrow():
    assert 'Aggregate pre-v' + CURRENT_APP_VERSION + ' melee drafts cannot be converted' in APP
    assert 'meleeCombatDraft:null,pendingMelee:null,pendingMeleeResults:[]' in APP
    assert 'localStorage.clear' not in APP


def test_hidden_expansion_and_stage3_scope_are_preserved():
    for variant in ('flayer-curse','destroyer-cult','crownworld'):
        assert re.search(rf"{re.escape(variant)}[^\n]+available:false",APP)
    assert "name:'Shield',deferred:true" not in APP  # Shield remains datacard-only metadata
    assert "deferredRules:['Shield']" in APP
    assert 'Whirling Onslaught*' in APP and "name:'Horrifying Flaying',deferred:true" in APP


def test_partial_attack_pool_is_not_treated_as_final_after_reload():
    roll=body('rollFightParticipant')
    assert 'participant.attackDiceComplete' in roll
    assert 'weaponRuleRerollsComplete(participant.attackDice,participant.profile)' in roll
    assert 'applyWeaponRuleRerolls(participant.attackDice,participant.profile' in roll
    assert 'participant.attackDiceComplete=true' in roll


def test_restored_fight_validation_and_wounds_are_authoritative():
    normalize=body('normalizeFightState')
    assert "typeof fight.id!=='string'" in normalize
    assert "!['player','npo'].includes(participant.side)" in normalize
    assert 'isRecord(participant.profile)' in normalize
    start=body('startSharedFight')
    assert 'playerCurrentWounds(participant.id)' in start
    assert "state.roster.find(item=>item.id===participant.id)?.wounds" in start


def test_legacy_npo_melee_draft_is_reset_without_losing_activation():
    assert "merged.lastActivation?.pendingAction?.id==='fight'" in APP
    assert 'combatDraft:null,targetConfirmed:false,attackResolved:false' in APP


def test_shared_commit_api_runtime_semantics():
    import subprocess
    sources='\n'.join(body(name) for name in (
        'otherFightRole','unresolvedFightSuccesses','fightBlockTargets','advanceFightTurn',
        'resolveFightShock','setFightOperativeWounds','commitFightStrike','commitFightBlock'
    ))
    script=f"""
const state={{playerWounds:{{p:9}},playerCasualtyIds:[],playerReady:1,playerRoster:['p'],playerActivatedIds:[],roster:[{{id:'n',wounds:10,ready:true,deployed:true,battlefieldState:'deployed'}}]}};
const playerOperativesRemaining=()=>1;
const save=()=>{{}};
const weaponHasRule=(profile,id)=>(profile.ruleIds||[]).includes(id);
{sources}
const base={{successes:{{attacker:[{{id:'a-c',kind:'critical',status:'unresolved'}},{{id:'a-n',kind:'normal',status:'unresolved'}}],defender:[{{id:'d-c',kind:'critical',status:'unresolved'}},{{id:'d-n',kind:'normal',status:'unresolved'}}]}},attacker:{{side:'player',id:'p',wounds:9,profile:{{normal:3,crit:5,ruleIds:['shock']}}}},defender:{{side:'npo',id:'n',wounds:10,profile:{{normal:4,crit:6,ruleIds:[]}}}},turn:'attacker',resolutionIndex:0,history:[],ruleTriggers:{{}},blockCapacity:{{attacker:1,defender:1}},completed:false}};
if(!commitFightStrike(base,'attacker','a-c'))process.exit(1);
if(base.defender.wounds!==5||base.successes.attacker[0].status!=='struck'||base.successes.defender[1].status!=='discarded-by-shock'||base.turn!=='defender')process.exit(2);
if(commitFightBlock(base,'defender','d-n',['a-c']))process.exit(3);
if(!commitFightBlock(base,'defender','d-c',['a-n']))process.exit(4);
if(base.successes.defender[0].status!=='blocked'||base.successes.attacker[1].status!=='blocked'||!base.completed)process.exit(5);
const brutal={{...base,completed:false,turn:'attacker',history:[],successes:{{attacker:[{{id:'x',kind:'normal',status:'unresolved'}}],defender:[{{id:'y',kind:'normal',status:'unresolved'}}]}},attacker:{{...base.attacker,profile:{{normal:3,crit:5,ruleIds:[]}}}},defender:{{...base.defender,profile:{{normal:4,crit:6,ruleIds:['brutal']}}}}}};
if(commitFightBlock(brutal,'attacker','x',['y']))process.exit(6);
"""
    subprocess.run(['node','-e',script],cwd=ROOT,check=True)
