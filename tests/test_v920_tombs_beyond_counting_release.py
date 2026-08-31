"""v9.2 release contracts spanning the completed Stage 1-4 architecture."""

from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_identity_cache_assets_and_save_compatibility():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 0)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "./event-effects.js?v=${APP_VERSION}" in WORKER
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "Version 9.2.0 - Tombs Beyond Counting" in README
    for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "dice-sfx.js", "app.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX


def test_accessible_single_choice_variant_selector_is_released_and_defaults_standard():
    registry = section("const TOMB_WORLD_VARIANTS", "function currentTombWorldVariant")
    assert registry.count("available:true") == 4
    for variant in ("standard", "flayer-curse", "destroyer-cult", "crownworld"):
        assert f"id:'{variant}'" in registry
    options = section("if(stepId==='options')", "if(stepId==='deploy')")
    assert '<fieldset class="variant-selector">' in options
    assert '<legend>Tomb World Variant</legend>' in options
    assert 'type="radio" name="tombWorldVariant"' in options
    assert 'aria-describedby="variant-' in options
    assert "state.tombWorldVariant===variant.id?'checked'" in options
    assert "tombWorldVariant:'standard'" in APP
    assert ".variant-card:focus-within" in STYLES


def test_variant_selector_preserves_setup_focus_and_rapid_tap_behavior():
    render = section("function render()", "function guideInstructionsHtml")
    assert "if(movedToNewStep)" in render
    assert "setupHeading.focus({preventScroll:true})" in render
    touch_handler = section("document.addEventListener('touchend'", "const MAX_NPOS")
    assert "button, input, select, textarea, a, label" in touch_handler
    assert '[role="radio"]' in touch_handler
    assert "if(now-lastTouchEnd<=300)e.preventDefault()" in touch_handler


def test_setup_copy_has_no_inventory_questions_and_preserves_independent_options():
    options = section("if(stepId==='options')", "if(stepId==='deploy')")
    assert "Official Expansion - White Dwarf 517" in options
    assert "Other Optional Rules" in options
    assert "Restless Tomb" in options
    assert "Deadly Encounters: Tomb Worlds" in options
    assert "available in Solo battles only" in options
    forbidden = ("which models", "models you own", "how many flayed", "own a hexmark", "own a royal warden")
    assert not any(text in APP.lower() for text in forbidden)


def test_variant_change_uses_authoritative_invalidation_and_rebuilds_deck():
    setter = section("function setTombWorldVariant", "function satisfyEmptyStartingNpoDeployment")
    assert "invalidateStartingNpoSetup()" in setter
    assert "state.eventState.available=" in setter
    assert "state.eventState.used=[]" in setter and "state.eventState.active=[]" in setter
    assert "state.variantState={crownworldFirstCrawlerConsumed:false,replacementTransactions:{}}" in setter
    assert "state.eventState.transactions={}" in setter and "state.eventState.rewardsTriggers=[]" in setter
    assert "state.playerRoster" not in setter
    bindings = section("function bindSetup", "function runStartingNpoGeneration")
    assert "setTombWorldVariant(e.target.value)" in bindings
    assert "state.tombWorldVariant=e.target.value" not in bindings


def test_briefing_is_read_only_and_summarizes_variant_and_optional_rules():
    briefing = section("const selectedVariant=currentTombWorldVariant()", "function advanceSetupStep")
    assert "Tombs Beyond Counting · Official Expansion<br>White Dwarf 517" in briefing
    assert "selectedVariant.briefing" in briefing
    assert "${escapeHtml(selectedVariant.name)}</strong>${variantSource}${variantBriefing}" in briefing
    assert "${escapeHtml(selectedVariant.name)}<br>${variantSource}<br>" not in briefing
    assert ">Restless Tomb</strong>" in briefing and ">Deadly Encounters</strong>" in briefing
    assert 'name="tombWorldVariant"' not in briefing
    assert 'id="restlessTombEnabled"' not in briefing


def test_each_variant_adds_exactly_its_one_named_event_while_standard_is_inert():
    registry = section("const inertVariantHooks", "function currentTombWorldVariant")
    for event_id in ("flesh-hunger", "rewards-of-annihilation", "enforcer-of-the-phaerons"):
        assert registry.count(f"eventId:'{event_id}'") == 1
    assert "eventDeckAdditions:()=>eventId?[{instanceId:`${eventId}-1`" in registry
    assert "eventDeckAdditions:()=>[]" in registry


def test_expansion_npos_remain_rules_driven_and_do_not_contaminate_standard_add_npo():
    standard = section("const npoDefinitions = {", "const tombsBeyondCountingNpoDefinitions")
    add_npo = section("function showAddNpo", "function changeNpoLoadout")
    for name in ("Flayed One", "Skorpekh Destroyer", "Hexmark Destroyer", "Royal Warden", "Lychguard"):
        assert name not in standard
        assert name not in add_npo
        assert name in APP
    assert "types=sortedNposForDisplay(Object.keys(npoDefinitions))" in add_npo
    assert "manual Add NPO tool remains limited to the Standard inventory" in APP


def test_solo_and_pvp_replacement_ownership_and_human_activation_are_preserved():
    resolver = section("function resolveVariantNpoRequest", "function createMissionState")
    assert "owner:isPvpMode()?'necron-controller':'guide'" in resolver
    assert "pvpDecisionPending" in resolver
    assert "commitPvpNpoReplacement" in APP
    dispatcher = section("function continueNpoActivation()", "function continueHumanNecronActivation()")
    assert "if(isPvpMode())" in dispatcher
    assert "continueHumanNecronActivation()" in dispatcher
    assert "continueSoloNpoActivation()" in dispatcher
    human_activation = section("function continueHumanNecronActivation()", "function continueSoloNpoActivation()")
    assert "renderHumanNpoActionPicker(n)" in human_activation
    solo_activation = section("function continueSoloNpoActivation()", "function normalizeUnknownAttackMovement")
    assert "renderHumanNpoActionPicker" not in solo_activation


def test_cross_variant_rules_persistence_and_fight_contracts_remain_integrated():
    for contract in ("resolveHorrifyingFlaying", "resolveWhirlingOnslaught", "resolveMultiThreatEliminator", "resolveRewardsOfAnnihilation", "setupCrownworldCrawlerPair", "crownworldFirstCrawlerConsumed", "pendingDice", "startSharedFight"):
        assert contract in APP
    assert "Confirm tabletop target legality." not in APP
    assert "Aggregate pre-v9.1.1 melee drafts cannot be converted" in APP


def test_help_and_release_notes_describe_support_without_full_datacards():
    help_text = section("<details><summary>Tombs Beyond Counting", "<details><summary>Deadly Encounters")
    for name in ("Flayer Curse Infected Tomb", "Destroyer Cult Tomb", "Crownworld of the Dynasty Tomb"):
        assert name in help_text
    assert "White Dwarf 517" in help_text
    assert "five Necron NPO datacards" in README
    assert "three mutually exclusive" in help_text
