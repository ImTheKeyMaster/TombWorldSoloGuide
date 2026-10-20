"""Protect iPhone top safe-area visibility and single-scroll Tomb dialogs."""

import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def scoped_declaration(selector):
    pattern = re.escape(selector) + r"\s*\{([^}]*)\}"
    match = re.search(pattern, CSS)
    assert match, f"Missing CSS declaration: {selector}"
    return match.group(1)


def test_game_menu_and_other_modal_screens_avoid_ios_top_bar():
    rule = scoped_declaration('html[data-ui="tomb"] #modal:not(.human-activation-modal)')
    for snippet in (
        "position:fixed;",
        "top:max(16px,env(safe-area-inset-top));",
        "bottom:max(16px,env(safe-area-inset-bottom));",
        "max-height:calc(100dvh -",
        "overflow-y:auto;",
        "overflow-x:hidden;",
        "overscroll-behavior-y:contain;",
        "-webkit-overflow-scrolling:touch;",
        "touch-action:pan-y;",
    ):
        assert snippet in rule, snippet
    assert "mask" not in rule and "gradient" not in rule
    assert "width:" not in rule and "padding:" not in rule
    assert "background:" not in rule and "font" not in rule
    # The existing UI uses one dialog for menus, combat and roster reference.
    assert '<dialog id="modal" class="modal"' in HTML
    assert "showModal('Game Menu'," in APP
    assert "if(!modal.open)modal.showModal();" in APP


def test_background_stays_stationary_while_native_dialog_scrolls():
    rule = scoped_declaration(
        'html:has(#modal[open]),body:has(#modal[open])'
    )
    assert "overflow:hidden!important;" in rule
    assert "overscroll-behavior:none!important;" in rule
    legacy = re.search(r"body\.modal-open\s*\{[^}]*overflow:auto!important", CSS)
    assert legacy, "Expected the historical background-scroll override"
    assert CSS.index('html:has(#modal[open]),body:has(#modal[open])') > legacy.start()
    assert "modal.scrollTop=0;" in APP
    assert "modalBody.scrollTop=0;" in APP
    assert ".modal .modal-inner" in CSS
    assert "overflow:visible!important;" in CSS


def test_existing_activation_and_portrait_layouts_unchanged():
    # Human activation keeps its own dedicated scroll/safe-area rules.
    assert "html[data-ui=\"tomb\"] #modal.human-activation-modal{" in CSS
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in CSS
    assert "experimental-activation-portrait" in APP
    assert "Death_Korps_" in CSS
    assert "playerActivationOperativeEliminated" in APP
    assert 'html[data-ui="tomb"] #modal:not(.human-activation-modal)' in CSS
    assert "width:min(680px,calc(100% - 24px))" in CSS


def test_current_version_works_with_existing_offline_cache_contract():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    for asset in ("app.js", "styles.css", "mission-engine.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in HTML
