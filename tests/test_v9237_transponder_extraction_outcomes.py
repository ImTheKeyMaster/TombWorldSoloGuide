from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
MISSION = (ROOT / "Missions" / "definition-03-recover-transponder.json").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def test_release_surfaces_preserve_v9237_behavior_without_save_key_change():
    expected = CURRENT_APP_VERSION
    assert tuple(map(int, expected.split("."))) >= (9, 2, 37)
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert INDEX.count(f"?v={expected}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")


def test_direct_escape_preserves_carrier_and_commits_once():
    locate = source("async function performLocateItem", "let transponderEscapePending")
    escape = source("let transponderEscapePending", "function handleTransponderCarrierIncapacitation")
    renderer = source("transponder:(engine,progress,{readOnly=false}={})=>", "destruction:(engine,progress")

    assert "progress.carrierId=carrierId" in locate
    assert "Carrier:</strong>" in renderer
    assert "Update Carrier" not in APP
    assert "updatedTransponderCarrier" not in APP
    assert '"confirmEscape"' not in MISSION
    assert renderer.count("Confirm Escape") == 1
    assert "showMissionConfirmation" not in escape
    assert "transponderEscapePending" in escape
    assert "progress.transactions?.[transactionId]" in escape
    assert "button.disabled=true" in escape
    assert "executeMissionAction('recordTransponderEscape'" in escape
    assert "progress.escaped=true" in escape
    assert "progress.extractionConfirmed=true" in escape
    assert "progress.completed=true" in escape
    assert "progress.outcome='victory'" in escape
    assert "completeMission('victory')" in escape


def test_all_outcomes_reset_document_scroll_after_render_before_focus():
    reset = source("function resetOutcomeScroll", "async function finalizeMissionCompletion")
    outcome = source("if(state.gameEnd){", "if(state.finalResolution?.pending")

    assert "const scrollContainer=document.scrollingElement||document.documentElement" in reset
    assert "scrollContainer.scrollTop=0" in reset
    assert "scrollContainer.scrollLeft=0" in reset
    assert "window.scrollTo" not in reset
    assert "requestAnimationFrame(()=>{resetOutcomeScroll();" in outcome
    assert "focus({preventScroll:true})" in outcome
    assert "state.gameEnd==='victory'" in outcome
