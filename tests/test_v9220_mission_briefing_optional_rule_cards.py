from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def ready_briefing_source():
    start = APP.index("const rules=(m.rules||[]).map", APP.index("function setupContent"))
    end = APP.index("\n  }", start)
    return APP[start:end]


def test_optional_settings_use_three_shared_mission_rule_cards():
    briefing = ready_briefing_source()
    optional = briefing[briefing.index("optional-rules-summary") :]

    assert "Optional Rules &amp; Expansions" in optional
    assert optional.count('<section class="mission-rule"') == 3
    assert 'id="briefing-variant-title"' in optional
    assert '>Restless Tomb</strong>' in optional
    assert '>Deadly Encounters</strong>' in optional
    assert '<p><strong>Tomb World Variant:</strong>' not in optional
    assert '<p><strong>Restless Tomb:</strong>' not in optional
    assert '<p><strong>Deadly Encounters:</strong>' not in optional
    assert ".mission-rule{padding:13px 14px;border:1px solid var(--line);border-radius:12px" in CSS


def test_variant_card_uses_selected_name_without_duplicate_standard_briefing():
    briefing = ready_briefing_source()

    assert "selectedVariant=currentTombWorldVariant()" in briefing
    assert "selectedVariant.briefing===selectedVariant.name?'':" in briefing
    assert "${escapeHtml(selectedVariant.name)}</strong>${variantSource}${variantBriefing}" in briefing
    assert "selectedVariant.id==='standard'?'<small>Tomb World Variant</small>'" in briefing
    assert "Official Expansion<br>White Dwarf 517" in briefing
    assert "<p>${escapeHtml(selectedVariant.briefing)}</p>" in briefing


def test_optional_card_statuses_derive_from_existing_authoritative_state():
    briefing = ready_briefing_source()

    assert "${state.restlessTombEnabled?'On':'Off'}" in briefing
    assert ">House Rule</small>" in briefing
    assert "state.deadlyEncountersEnabled?'Enabled':'Disabled'" in briefing
    assert "isPvpMode()?'Disabled<br>" in briefing
    assert "Solo battles only" in briefing
    assert "Official Expansion<br>White Dwarf 521" in briefing


def test_instruction_remains_after_all_three_cards():
    briefing = ready_briefing_source()
    instruction = "Go Back to Optional Rules &amp; Expansions to change these settings before beginning the battle."

    assert briefing.index(instruction) > briefing.index('id="briefing-deadly-encounters-title"')
    assert 'class="optional-rules-instruction"' in briefing
    assert ".optional-rules-instruction{display:block;margin-top:12px;color:var(--muted)" in CSS


def test_special_rules_and_ready_actions_are_unchanged():
    briefing = ready_briefing_source()

    assert "presentSideTerminology(rule.name||'Special Rule')" in briefing
    assert "presentSideTerminology(rule.timing)" in briefing
    assert "presentSideTerminology(rule.summary||'')" in briefing
    assert "${escapeHtml(presentSideTerminology(m.objective))}" in briefing
    assert "${escapeHtml(m.number)} · ${escapeHtml(m.name)}" in briefing
    assert '<button class="btn ghost" id="setupBack">Back</button>' in briefing
    assert '<button class="btn primary" id="beginGame">Begin Turning Point 1</button>' in briefing


def test_interactive_optional_rules_setup_and_state_handlers_remain_present():
    assert '<input type="radio" name="tombWorldVariant"' in APP
    assert '<input id="restlessTombEnabled" type="checkbox"' in APP
    assert '<input id="deadlyEncountersEnabled" type="checkbox"' in APP
    assert "state.restlessTombEnabled=e.target.checked;save();render()" in APP
    assert "if(isPvpMode())return;state.deadlyEncountersEnabled=e.target.checked;save();render()" in APP
    assert "setTombWorldVariant(e.target.value)" in APP


def test_v9220_version_and_persistence_surfaces_are_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 20)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in (
        "styles.css",
        "mission-engine.js",
        "persistence.js",
        "deadly-encounters.js",
        "event-effects.js",
        "audio-capabilities.js",
        "narration.js",
        "ambient.js",
        "dice-sfx.js",
        "app.js",
    ):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
