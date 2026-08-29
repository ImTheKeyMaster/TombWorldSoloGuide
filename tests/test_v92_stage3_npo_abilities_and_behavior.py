import re
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text(encoding='utf-8')
PERSISTENCE = (ROOT / 'persistence.js').read_text(encoding='utf-8')


def body(name):
    match = re.search(rf'(?:async )?function {name}\([^)]*\)\{{', APP)
    assert match, name
    start = match.start()
    next_match = re.search(r'\n  (?:async )?function \w+\(', APP[match.end():])
    return APP[start: match.end() + next_match.start()] if next_match else APP[start:]


def test_horrifying_flaying_uses_fight_occurrence_dice_provider_and_temporary_apl():
    strike = body('commitFightStrike')
    ability = body('resolveHorrifyingFlaying')
    assert 'qualifyingHorrifyingFlaying' in strike and "target.side==='player'" in strike
    assert 'historyEntry.index' in ability and 'candidateIds' in ability
    assert 'inPlayLivingPlayerOperativeIds' in ability and 'incapacitatedId' in ability
    assert 'choosePriorityPlayerTarget' in ability and 'isPvpMode()' in ability
    assert 'requestDiceResults' in ability and 'sides:6' in ability
    assert 'occurrence.roll>=3' in ability and 'applyTemporaryAplModifier' in ability
    assert "ruleId:'horrifying-flaying'" in ability and "status==='complete'" in ability
    candidate_checkpoint=ability.index('candidateIds=await chooseTabletopOperatives')
    assert 'save();' in ability[candidate_checkpoint:ability.index('requestDiceResults')]
    assert "if(!occurrence.targetId)" in ability


def test_horrifying_flaying_apl_expires_after_next_activation():
    apply = body('applyTemporaryAplModifier')
    expire = body('expireActivationEffects')
    assert "expires:'end-of-target-next-activation'" in apply
    assert 'item.deferCurrentActivation=false' in expire
    assert 'item.targetId!==operativeId' in expire


def test_solo_horrifying_target_priority_prefers_ready_after_lowest_wounds():
    priority = body('choosePriorityPlayerTarget')
    assert 'playerCurrentWounds(a)-playerCurrentWounds(b)' in priority
    assert 'Number(state.playerActivatedIds.includes(a))-Number(state.playerActivatedIds.includes(b))' in priority


def test_whirling_triggers_only_from_committed_critical_strike_and_is_idempotent():
    qualify = body('qualifyingWhirlingStrike')
    strike = body('commitFightStrike')
    splash = body('resolveWhirlingOnslaught')
    assert "success?.kind==='critical'" in qualify and "skorpekh-hyperphase-weapons" in qualify
    assert strike.index("success.status='struck'") < strike.index('qualifyingWhirlingStrike')
    assert 'commitFightBlock' not in qualify
    assert 'primaryId' in splash and 'id!==primaryId' in splash
    assert 'sides:3' in splash and 'damageByTarget[targetId]!==undefined' in splash
    assert "status==='complete'" in splash and 'historyEntry.index' in splash


def test_whirling_secondary_casualties_do_not_end_primary_fight():
    splash = body('resolveWhirlingOnslaught')
    assert 'commitStage3PlayerDamage(targetId,damage)' in splash
    assert 'fight.completed=true' not in splash


def test_hulking_is_target_selection_reminder_only():
    wizard = body('showPendingPlayerAttackWizard')
    assert 'Hulking:' in wizard and 'cannot use Light terrain' in wizard
    assert 'target.order' in wizard
    assert 'effectiveDefenseDiceCount' not in wizard
    assert 'Confirm tabletop target legality' not in APP
    assert 'requiresStage3TargetCheck' in wizard


def test_multi_threat_trigger_and_final_failed_dice_count():
    damage = body('applyPendingPlayerDamage')
    count = body('finalDiscardedFailedAttackDice')
    reaction = body('resolveMultiThreatEliminator')
    assert "pending.attackType==='shoot'" in damage and "hexmark-destroyer" in damage
    assert "!die.retained&&die.kind==='miss'" in count
    assert 'pending.attackDice||[]' in reaction and 'focusedHexmarkReactionProfile' in reaction
    assert 'finalDiscardedFailedAttackDice' in body('focusedHexmarkReactionProfile')
    assert 'STAGE3_RULE_TEXT.multiThreatRange' in reaction


def test_multi_threat_profile_attack_cap_target_and_free_cost_semantics():
    profile = body('focusedHexmarkReactionProfile')
    reaction = body('resolveMultiThreatEliminator')
    assert "profile.profileId==='focused'" in profile
    assert 'Math.min(finalDiscardedFailedAttackDice(failedDice)+1,4)' in profile
    assert 'stage.playerOperativeId' in reaction
    assert "hexmark.order='Engage'" in reaction
    assert 'commitNpoAction' not in reaction
    assert 'remainingAp' not in reaction


def test_multi_threat_pvp_offer_pre_removal_and_reload_state():
    damage = body('applyPendingPlayerDamage')
    reaction = body('resolveMultiThreatEliminator')
    assert damage.index('resolveMultiThreatEliminator') < damage.index("n.battlefieldState='out-of-action'")
    assert 'askPerformOrSkip' in reaction and "decision==='skip'" in reaction
    for field in ('withinEight','offered','decision','attackCount','profile','orderBefore','orderChanged','attackDice','defenseDice','damageCommitted'):
        assert field in reaction
    assert "status==='complete'" in reaction and 'pending.multiThreatResolved=true' in reaction
    assert "reaction.withinEight=await askYesNoRuleQuestion" in reaction
    assert "reaction.decision=isPvpMode()?await askPerformOrSkip" in reaction
    assert "reaction.profile?{...reaction.profile}" in reaction
    assert "acknowledgeDiceRequest(`${base}:defense`)" in reaction


def test_multi_threat_checkpoints_every_manual_pause_boundary():
    reaction = body('resolveMultiThreatEliminator')
    range_answer = reaction.index('reaction.withinEight=await askYesNoRuleQuestion')
    offer = reaction.index('reaction.offered=true')
    decision = reaction.index('reaction.decision=isPvpMode()?await askPerformOrSkip')
    snapshot = reaction.index('reaction.profile={...profile}')
    attack = reaction.index('reaction.attackDice=await requestAttackDiceForProfile')
    defense = reaction.index('reaction.defenseDice=await requestDefenseDice')
    for checkpoint, following in ((range_answer, offer), (offer, decision), (decision, snapshot), (snapshot, attack), (attack, defense)):
        assert 'save();' in reaction[checkpoint:following]
    assert 'save();acknowledgeDiceRequest(`${base}:defense`)' in reaction[defense:]


def test_multi_threat_resolves_after_attack_consequences_but_defers_removal():
    damage = body('applyPendingPlayerDamage')
    hook = damage.index("npoDefinition(n.type)?.id==='hexmark-destroyer'")
    aggressive = damage.index('showAggressiveDefenseResolution')
    removal = damage.index("n.battlefieldState='out-of-action'")
    assert aggressive < hook < removal
    pre_reaction = damage[aggressive:hook]
    assert 'resolveNpoIncapacitation' not in pre_reaction
    assert "n.wounds=Math.max(0,pending.after)" not in pre_reaction


def test_engrammatic_logic_is_contextual_reminder_not_injury_engine():
    guidance = body('npoCombatGuidanceHtml')
    assert 'STAGE3_RULE_TEXT.engrammatic' in guidance
    assert 'npo.wounds<npo.maxWounds' in guidance
    assert "id==='royal-warden'" in guidance
    assert 'ignore stat changes caused by being Injured' in APP
    assert 'effectiveInjured' not in APP
    assert 'STAGE3_RULE_TEXT.engrammatic' in body('renderNpoActivationHeader')
    assert 'STAGE3_RULE_TEXT.engrammatic' in body('renderHumanNpoActionPicker')


def test_shield_uses_shared_block_capacity_and_records_two_ids():
    start = body('startSharedFight')
    block = body('commitFightBlock')
    shield = body('shieldBlockCapacity')
    assert "profile?.weaponId==='hyperphase-sword'?2:1" in shield
    assert 'shieldBlockCapacity(attacker)' in start and 'shieldBlockCapacity(defender)' in start
    assert 'targets.length>capacity' in block
    assert 'blockedSuccessIds:targets.map' in block
    assert 'fightBlockTargets' in block


def test_shield_human_ui_and_solo_ai_share_fight_engine():
    render = body('renderFightResolution')
    ai = body('soloNpoFightDecision')
    assert 'Shield:' in render and 'up to two unresolved successes' in render
    assert 'showFightBlockSelection' in render and 'commitFightBlock' in render
    assert 'capacity' in ai and 'legal.slice(0,capacity)' in ai
    assert APP.count('function commitFightBlock') == 1


def test_shield_solo_ai_values_two_success_combined_damage():
    ai = body('soloNpoFightDecision')
    assert 'capacity>1' in ai
    assert 'enemy.reduce' in ai
    assert 'shieldPlans' in ai
    assert '.slice(0,capacity)' in ai


def test_guardian_protocol_is_specific_player_shoot_gate():
    wizard = body('showPendingPlayerAttackWizard')
    assert "attackType!=='shoot'" in wizard
    assert "id!=='royal-warden'" in wizard and "id==='lychguard'" in wizard
    assert "item.order==='Engage'" in wizard
    assert 'STAGE3_RULE_TEXT.guardianRange' in wizard
    assert 'STAGE3_RULE_TEXT.guardianPrevented' in wizard
    assert 'guardian-protocol:${identity.activationId}:${identity.actionId}:${target.id}' in wizard
    assert 'withinControlRange:null' in wizard
    assert 'requiresStage3TargetCheck' in wizard
    assert wizard.index('guardianProtocolCheck') < wizard.index('selectSecondaryTargets();})')


def test_stage3_solo_priorities_and_order_rules():
    rank = body('rankLegalNpoActions')
    choose = body('chooseNpoDecision')
    expected = {
        'flayed-one': "['Fight','Charge','Reposition','Dash']",
        'skorpekh-destroyer': "['Fight','Charge','Reposition','Dash']",
        'hexmark-destroyer': "['Fall Back','Shoot','Reposition','Dash','Fight']",
        'royal-warden': "['Fall Back','Shoot','Reposition','Dash','Fight']",
        'lychguard': "['Fight','Charge','Reposition','Dash']",
    }
    for operative, priority in expected.items():
        assert f"'{operative}':{priority}" in rank
    assert 'engage-if-fight-or-charge' in choose
    assert 'engage-if-shoot-or-fight' in choose
    assert "n.order=stance" in choose and "'Conceal'" in choose


def test_lychguard_warden_movement_intent_persists_in_shared_activation():
    inquiry = body('npoMovementInquiry')
    instruction = body('npoMovementInstruction')
    prompt = body('runNpoPrompt')
    assert "id:'reposition-toward-royal-warden'" in inquiry
    assert "purpose:'toward-royal-warden'" in inquiry
    assert 'STAGE3_RULE_TEXT.lychguardMovement' in inquiry
    assert "focus==='warden'" in instruction and 'closest Player operative' in instruction
    assert 'state.lastActivation.movementIntent={...q.movementIntent' in prompt
    assert "id:'dash-toward-royal-warden'" in inquiry
    assert "movementIntent?.purpose==='toward-royal-warden'" in body('chooseNpoDecision')


def test_stage3_secondary_damage_uses_shared_casualty_bookkeeping():
    damage = body('commitStage3PlayerDamage')
    assert 'playerCasualtyIds.push(operativeId)' in damage
    assert 'playerActivatedIds.push(operativeId)' in damage
    assert 'state.playerReady=playerOperativesRemaining()' in damage


def test_all_five_use_shared_human_activation_and_hatches():
    catalog = APP.split('const tombsBeyondCountingNpoDefinitions',1)[1].split('// Official NPO datacards',1)[0]
    for operative in ('Flayed One','Skorpekh Destroyer','Hexmark Destroyer','Royal Warden','Lychguard'):
        card = catalog.split(f"'{operative}': {{",1)[1].split('\n    },',1)[0]
        assert 'operatesHatches:true' in card
    assert APP.count('function renderHumanNpoActionPicker') == 1
    picker = body('renderHumanNpoActionPicker')
    assert 'supportedHumanNpoActions' in picker and 'renderHumanActivationShell' in picker
    assert 'onEnd:()=>confirmEndHumanNpoActivation' in picker


def test_stage3_persistence_dice_and_versions_remain_compatible():
    assert 'stage3Triggers' in body('normalizeState')
    assert 'requestDiceResults' in body('resolveWhirlingOnslaught')
    assert 'requestDiceResults' in body('resolveHorrifyingFlaying')
    assert 'requestAttackDiceForProfile' in body('resolveMultiThreatEliminator')
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert 'const SAVE_VERSION = 3;' in PERSISTENCE
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP


def test_variants_hidden_and_event_deck_unchanged():
    variants = APP.split('const TOMB_WORLD_VARIANTS',1)[1].split('const initialState',1)[0]
    assert variants.count('available:false') == 3
    event_deck = APP.split('const eventDeck = [',1)[1].split('];\n\n  function eventDefinition',1)[0]
    for event in ('Flesh Hunger','Rewards of Annihilation','Enforcer of the Phaerons'):
        assert event not in event_deck
