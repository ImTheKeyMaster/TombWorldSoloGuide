import re
from pathlib import Path
from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


CATALOG = section("const tombsBeyondCountingNpoDefinitions", "// Official NPO datacards")


def definition(name):
    start = f"'{name}': {{"
    following = CATALOG.split(start, 1)[1]
    candidates = [following.find(f"\n    '{other}': {{") for other in (
        "Flayed One", "Skorpekh Destroyer", "Hexmark Destroyer", "Royal Warden", "Lychguard"
    ) if f"\n    '{other}': {{" in following]
    return following[: min(candidates)] if candidates else following


def test_exact_flayed_one_and_skorpekh_datacards():
    flayed = definition("Flayed One")
    assert "move:5,apl:2,save:4,wounds:9,baseSize:32" in flayed
    assert "name:'Flayer claws',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:5}" in flayed
    assert "rules:['Ceaseless','Rending']" in flayed
    assert "name:'Horrifying Flaying',deferred:true" in flayed

    skorpekh = definition("Skorpekh Destroyer")
    assert "move:6,apl:2,save:3,wounds:18,baseSize:50" in skorpekh
    assert "name:'Skorpekh hyperphase weapons',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:6}" in skorpekh
    assert "rules:['Balanced','Lethal 5+','Whirling Onslaught*']" in skorpekh
    assert "deferredRules:['Whirling Onslaught']" in skorpekh
    assert "name:'Hulking',deferred:true" in skorpekh


def test_exact_hexmark_datacard_and_profile_types():
    card = definition("Hexmark Destroyer")
    assert "move:6,apl:2,save:3,wounds:15,baseSize:50" in card
    assert "name:'Focused',attacks:5,hit:3,damage:{normal:3,critical:2}" in card
    assert "rules:['Range 9\"','Ceaseless','Devastating 2','Piercing 1','Saturate']" in card
    assert "name:'Sweeping',attacks:4,hit:3,damage:{normal:3,critical:2}" in card
    assert "rules:['Range 9\"','Devastating 2','Piercing 1','Saturate','Torrent 2\"']" in card
    assert "range:9,devastating:2,piercing:1,torrent:2" in card
    assert "name:'Enmitic disintegrator pistols (point-blank)',type:'melee',attacks:5,hit:3,damage:{normal:3,critical:4},rules:[]" in card
    assert "name:'Multi-Threat Eliminator',deferred:true" in card


def test_exact_royal_warden_datacard():
    card = definition("Royal Warden")
    assert "move:5,apl:3,save:3,wounds:14,baseSize:32" in card
    assert "name:'Relic gauss blaster',type:'ranged',attacks:4,hit:3,damage:{normal:4,critical:6}" in card
    assert "rules:['Lethal 5+','Piercing 1']" in card
    assert "name:'Bayonet',type:'melee',attacks:4,hit:3,damage:{normal:3,critical:4},rules:[]" in card
    assert "name:'Engrammatic Logic',deferred:true" in card


def test_exact_lychguard_datacard_and_exclusive_loadout():
    card = definition("Lychguard")
    assert "move:5,apl:2,save:3,wounds:13,baseSize:32,exclusiveMeleeLoadout:true" in card
    assert "loadoutOptions:[{id:'hyperphase-sword',name:'Hyperphase sword'},{id:'warscythe',name:'Warscythe'}]" in card
    assert "name:'Hyperphase sword',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:6}" in card
    assert "rules:['Lethal 5+','Shield*']" in card and "deferredRules:['Shield']" in card
    assert "name:'Warscythe',type:'melee',attacks:4,hit:3,damage:{normal:5,critical:7}" in card
    profiles = section("function npoAttackProfiles", "function canonicalAttackProfile")
    assert "weapon.id===npo.weaponId" in profiles
    assert "definition.exclusiveMeleeLoadout" in profiles


def test_expansion_catalog_is_hidden_from_standard_inventory_generation_and_add_npo():
    standard = section("const npoDefinitions = {", "const tombsBeyondCountingNpoDefinitions")
    generation = section("const npoGenerationTable", "const eventDefinitions")
    add_npo = section("function showAddNpo", "function changeNpoLoadout")
    for name in ("Flayed One", "Skorpekh Destroyer", "Hexmark Destroyer", "Royal Warden", "Lychguard"):
        assert name not in standard
        assert name not in generation
        assert name not in add_npo
    assert "Object.values(npoDefinitions).reduce" in APP
    assert "types=sortedNposForDisplay(Object.keys(npoDefinitions))" in add_npo
    assert "Object.keys(npoDefinitions).map" in section("function npoInventory", "function lowestAvailableNpoInstances")


def test_variants_events_versions_and_save_schema_remain_unchanged():
    variants = section("const TOMB_WORLD_VARIANTS", "const initialState")
    assert variants.count("available:false") == 3
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    event_deck = section("const eventDeck = [", "];\n\n  function eventDefinition")
    assert all(name not in event_deck for name in ("Flesh Hunger", "Rewards of Annihilation", "Enforcer of the Phaerons"))


def test_shared_rule_parser_and_handlers_cover_all_stage_two_rules():
    handlers = section("const WEAPON_RULE_HANDLERS", "const NPO_ACTION_TRANSITIONS")
    for rule in ("balanced", "ceaseless", "rending", "devastating", "saturate"):
        assert re.search(rf"\b{rule}:\{{", handlers)
    parser = section("function normalizedWeaponRuleId", "function normalizedWeaponRuleWarningKey")
    assert "(?:\\s+\\d+(?:\\+)?)?" in parser
    values = section("function weaponRuleValue", "function effectiveDefenseDiceCount")
    assert "const value=String(rule).match(/(\\d+)/)" in values
    assert "devastatingDamageForAttack" in APP


def test_balanced_and_ceaseless_use_optional_shared_dice_provider_flow():
    chooser = section("function chooseHumanWeaponReroll", "async function applyWeaponRuleRerolls")
    assert "data-reroll-skip" in chooser
    assert "dice.map((die,index)" in chooser
    assert "new Set(dice.filter" in chooser
    assert "All ${value}s" in chooser
    rerolls = section("async function applyWeaponRuleRerolls", "function weaponHasRule")
    assert "for(const ruleId of ['balanced','ceaseless'])" in rerolls
    assert "requestDiceResults({requestKey" in rerolls
    assert "count:indexes.length" in rerolls
    assert ":reroll:${ruleId}:1" in rerolls
    assert "resumeKind:'combat'" in rerolls
    assert "rerolledBy:ruleId" in rerolls
    assert "die.value===Number(choice)" in rerolls
    assert "value===1" not in rerolls


def test_pvp_initial_attack_request_is_acknowledged_before_a_reroll_request():
    attack = section("async function requestAttackDiceForProfile", "async function requestDefenseDice")
    checkpoint = attack.index("if(onInitialRoll)onInitialRoll(dice)")
    acknowledge = attack.index("if(isPvpMode())acknowledgeDiceRequest(requestKey)")
    reroll = attack.index("await applyWeaponRuleRerolls")
    assert checkpoint < acknowledge < reroll
    assert "resumeKind:'combat'" in attack


def test_rending_devastating_and_saturate_are_shared_and_ordered():
    rending = section("function applyRendingToAttackDice", "function applyAttackSuccessConversions")
    assert "some(die=>die.retained&&die.kind==='crit')" in rending
    assert "findIndex(die=>die.retained&&die.kind==='hit')" in rending
    assert "rendingConverted:true" in rending
    conversions = section("function applyAttackSuccessConversions", "function beneficialRerollChoice")
    assert conversions.index("applySevereToAttackDice") < conversions.index("applyRendingToAttackDice")
    devastating = section("function devastatingDamageForAttack", "function resolveRetainedCombat")
    assert "retainedDiceTotals(attackDice).critical*value" in devastating
    shared_roll = section("function runAutomaticCombatRolls", "function retainedDiceTotals")
    assert "Saturate: cover saves cannot be retained." in shared_roll
    assert "Confirm tabletop target legality" not in shared_roll


def test_existing_lethal_piercing_range_and_torrent_paths_are_reused():
    canonical = section("function canonicalAttackProfile", "function normalizeNpo")
    assert "/Lethal\\s*(\\d)\\+/i" in canonical
    assert "/(?:Piercing|AP)\\s*(\\d+)/i" in canonical
    handlers = section("const WEAPON_RULE_HANDLERS", "const NPO_ACTION_TRANSITIONS")
    for rule in ("lethal", "piercing", "range", "torrent"):
        assert re.search(rf"\b{rule}:\{{", handlers)
    assert "runAutomaticCombatRolls" in APP
    assert "attackType" in section("function runAutomaticCombatRolls", "function retainedDiceTotals")
