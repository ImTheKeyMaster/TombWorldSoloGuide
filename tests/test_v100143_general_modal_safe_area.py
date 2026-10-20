"""Regression checks for iPhone modal safe-area scrolling without layout changes."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")

GENERAL_RULE = 'html[data-ui="tomb"] #modal:not(.human-activation-modal)'
ACTIVATION_RULE = 'html[data-ui="tomb"] #modal.human-activation-modal'
LOCK_RULE = (
    'html[data-ui="tomb"]:has(#modal[open]),'
    'html[data-ui="tomb"] body:has(#modal[open])'
)


def block(selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert match, f"CSS rule is missing: {selector}"
    return match.group(1)


def test_general_dialog_only_is_in_viewport_and_scrolls_itself():
    style = block(GENERAL_RULE)
    for rule in (
        "position:fixed;",
        "top:max(16px,env(safe-area-inset-top));",
        "bottom:max(16px,env(safe-area-inset-bottom));",
        "max-height:calc(100dvh -",
        "overflow-x:hidden;",
        "overflow-y:auto;",
        "overscroll-behavior-y:contain;",
        "-webkit-overflow-scrolling:touch;",
        "touch-action:pan-y;",
    ):
        assert rule in style, f"Expected mobile dialog rule: {rule}"
    for forbidden in (
        "width:", "padding:", "font-size:", "border-radius:", "background:",
        "mask-image:", "transform:", "grid-template", "display:",
    ):
        assert forbidden not in style, f"Unexpected layout or visual change: {forbidden}"


def test_page_scrolling_is_locked_only_with_shared_tomb_modal_open():
    lock = block(LOCK_RULE)
    assert "overflow:hidden!important;" in lock
    assert "overscroll-behavior:none!important;" in lock
    assert 'html:has(#modal[open]),body:has(#modal[open])' not in CSS
    assert 'id="modal" class="modal"' in HTML
    assert 'id="experimentalUiDialog"' in HTML
    assert 'id="diceEntryDialog"' in HTML
    assert "if(!modal.open)modal.showModal();" in APP


def test_existing_activation_dialog_framing_is_untouched():
    activation = block(ACTIVATION_RULE)
    general = block(GENERAL_RULE)
    assert GENERAL_RULE != ACTIVATION_RULE
    assert "overflow-y:auto;" in activation
    assert "max-height:calc(100dvh -" in activation
    assert "human-activation-modal" in GENERAL_RULE
    assert "experimental-activation-portrait" in CSS
    assert "experimental-roster-rail-modal" in CSS
    assert "npo-target-roster-rail" in CSS
    assert "max-height:none!important;" in CSS
    assert "modal.scrollTop=0;" in APP
    assert "modalBody.scrollTop=0;" in APP
    assert "modal.classList.toggle('human-activation-modal'" in APP
    assert "touch-action:pan-y;" in general


def test_version_and_offline_cache_remain_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    for asset in ("styles.css", "app.js", "mission-engine.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in HTML
    assert "cache.addAll(CORE_PRECACHE_ASSETS)" in SW
