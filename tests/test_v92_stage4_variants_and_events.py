from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
EFFECTS = (ROOT / "event-effects.js").read_text()
INDEX = (ROOT / "index.html").read_text()
SW = (ROOT / "service-worker.js").read_text()


def test_variant_registry_remains_hidden_and_adds_one_card_each():
    assert "'flayer-curse':Object.freeze" in APP and "available:false" in APP
    assert "eventId:'flesh-hunger'" in APP
    assert "eventId:'rewards-of-annihilation'" in APP
    assert "eventId:'enforcer-of-the-phaerons'" in APP
    assert "eventDeckAdditions:()=>eventId?[{instanceId:`${eventId}-1`" in APP
    options = APP[APP.index("if(stepId==='options')"):APP.index("if(stepId==='deploy')")]
    assert "flayer-curse" not in options and "destroyer-cult" not in options and "crownworld" not in options


def test_optional_replacements_use_hooks_and_preserve_original_options():
    assert "replacementOptions:[request.type,...replacements]" in APP
    assert "replaceType:'Necron Warrior',replacements:['Flayed One']" in APP
    assert "replaceType:TOMB_CRAWLER_TYPE,replacements:['Skorpekh Destroyer','Hexmark Destroyer']" in APP
    assert "startingRosterGeneration" in APP and "reinforcementGeneration" in APP
    assert "replaceMissionRequestedNpo" in APP and "replaceEventGeneratedNpo" in APP
    assert "if(selected!==request.type)delete resolved.weaponId" in APP
    assert "owner:isPvpMode()?'necron-controller':'guide'" in APP


def test_crownworld_is_actual_setup_atomic_and_capacity_safe():
    assert "npoSetupReplacement" in APP
    assert "setupCrownworldCrawlerPair" in APP
    assert "otherDeployed+2>MAX_NPOS" in APP
    assert "commitNpoRoster([...remaining,warden,lychguard]" in APP
    assert "crownworldFirstCrawlerConsumed=true" in APP
    assert "Set up the Lychguard within the Royal Warden's Control Range." in APP
    assert "crownworld:starting:" in APP and "crownworld:reinforcement:" in APP and "crownworld:mission:" in APP
    assert "createdIds:[warden.id,lychguard.id]" in APP


def test_awakened_warrior_and_flesh_hunger_paths():
    assert "replacementOptions:['Necron Warrior','Lychguard']" in APP
    assert "type==='Lychguard'" in APP and "'hyperphase-sword':'warscythe'" in APP
    assert "type==='flesh-hunger'" in APP
    assert "placementHatchway=`Hatchway ${roll(6)}`" in APP
    assert "0 AP; no activation or attack" in APP
    assert "No Fight or Shoot was granted" in APP
    assert "activeNpos().length>=MAX_NPOS" in APP


def test_rewards_is_attributed_durable_and_uses_central_dice_provider():
    assert "resolveRewardsOfAnnihilation(n,target,summary)" in APP
    assert "['Skorpekh Destroyer','Hexmark Destroyer'].includes(n.type)" in APP
    assert "casualtyWounds>=12?2:1" in APP
    assert "requestDiceResults({count:diceCount,sides:3" in APP
    assert "Math.min(n.maxWounds,n.wounds+total)" in APP
    assert "if(transaction.committed)return false" in APP
    assert "casualtyId:target.id" in APP and "restored:n.wounds-before" in APP


def test_enforcer_redraw_overlay_and_specific_room_question():
    assert "No living, deployed Royal Warden was in the killzone" in APP
    assert "sameRoomAsRoyalWarden" in APP
    assert "in the same room as a Royal Warden?" in APP
    assert "n.type==='Royal Warden'||Boolean" in APP
    assert "'enforcer-of-the-phaerons'" in EFFECTS
    assert "if(!profile.rules.some(rule=>/^Ceaseless$/" in EFFECTS
    assert "profile={...context.profile,rules:[...(context.profile?.rules||[])]}" in EFFECTS
    assert "Confirm tabletop target legality." not in APP


def test_persistence_is_optional_without_schema_or_product_version_bump():
    assert "variantState:{crownworldFirstCrawlerConsumed:false" in APP
    assert "rewardsTriggers:Array.isArray" in APP
    assert "const SAVE_VERSION = 3" in (ROOT / "persistence.js").read_text()
    from versioning import CURRENT_APP_VERSION
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}'" in APP
    assert f"v={CURRENT_APP_VERSION}" in INDEX
    assert "9.2.0" not in APP and "9.2.0" not in INDEX and "9.2.0" not in SW
    assert "Do you own this miniature?" not in APP


def test_expansion_roster_types_are_legal_only_for_their_variant():
    assert "variantAllowsExpansionNpo(npo.type,variantId)" in APP
    assert "variantId==='flayer-curse'" in APP and "type==='Flayed One'" in APP
    assert "variantId==='destroyer-cult'" in APP
    assert "variantId==='crownworld'" in APP
    assert "return false;" in APP[APP.index("function variantAllowsExpansionNpo"):APP.index("function commitNpoRoster")]


def test_crownworld_reinforcement_pair_updates_placement_completion():
    reinforcement = APP[APP.index("function confirmReinforcementPlacement"):APP.index("async function rollInitiative")]
    assert "pair.npos.forEach" in reinforcement
    assert "reinforcementState.operativeIds.every" in reinforcement
    assert "reinforcementState.status=complete?'complete':'placement'" in reinforcement


def test_rewards_manual_dice_has_a_dedicated_reload_resume_path():
    assert "pending.resumeKind==='rewards'" in APP
    assert "resumeKind:'rewards'" in APP
    assert "sourceTransactionId:identity" in APP
    assert "!state.eventState.rewardsTriggers.includes(transaction.id)" in APP
    assert "delete transaction.requesting" in APP


def test_variant_event_instance_is_restored_when_loading_an_existing_deck():
    assert "variantDeck.forEach(card=>{if(!available.includes(card.instanceId)&&!used.includes(card.instanceId))available.push(card.instanceId);})" in APP


def test_rewards_uses_authoritative_stage_three_and_fight_sources():
    assert "sourceNpo:hexmark" in APP
    assert "transactionId:`multi-threat-eliminator:${transactionId}`" in APP
    assert "transactionId:`whirling:${fight.id}:${historyEntry.index}:${targetId}`" in APP
    assert "transactionId:`fight:${fight.id}:${historyEntry.index}`" in APP


def test_enforcer_applies_to_shared_npo_fight_profiles():
    assert "function effectiveEnforcerNpoWeaponProfile" in APP
    assert "weaponHasRule(profile,'ceaseless')" in APP
    assert "npo.type==='Royal Warden'||await askYesNoRuleQuestion" in APP
    melee = APP[APP.index("if(attackType==='melee'){"):APP.index("const initialProfile", APP.index("if(attackType==='melee'){"))]
    assert "await effectiveEnforcerNpoWeaponProfile(n,baseAttackerProfile,'melee')" in melee
