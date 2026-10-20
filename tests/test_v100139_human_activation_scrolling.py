"""Regression contract for long, touch-scrollable player activation dialogs on iPhone."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def activation_scroll_rule():
    match = re.search(
        r'html\[data-ui="tomb"\] #modal\.human-activation-modal\s*\{([^}]*)\}',
        CSS,
    )
    assert match, "Missing scoped human activation scrolling rules"
    return match.group(1)


def test_human_activations_are_the_only_dialogs_that_get_scroll_class():
    modal = APP.split("function showModal(title,content,onClose,focusKey=null)", 1)[1]
    modal = modal.split("function closeModal()", 1)[0]
    assert "modal.classList.toggle('human-activation-modal'" in modal
    assert "Boolean(modalBody.querySelector('.human-activation-shell'))" in modal
    assert modal.index("modalBody.innerHTML=") < modal.index("modal.classList.toggle(")
    assert modal.index("modal.classList.toggle(") < modal.index("modal.showModal()")
    assert 'class="human-activation-shell' in APP
    assert "renderHumanPlayerActionPicker" in APP


def test_activation_dialog_scrolls_vertically_inside_safe_areas():
    rule = activation_scroll_rule()
    for expected in (
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
        assert expected in rule, f"Missing iPhone scroll behavior: {expected}"
    assert "overflow:visible!important" not in rule
    # The actual markup is #modal > #modalBody > .modal-inner, not a direct child.
    assert '<dialog id="modal" class="modal"' in HTML
    assert '<div id="modalBody"></div>' in HTML
    assert 'modalBody.innerHTML=`<div class="modal-inner"' in APP
    assert re.search(
        r'#modal\.human-activation-modal #modalBody>\.modal-inner\s*\{[^}]*'
        r'overflow:visible!important;[^}]*padding-bottom:calc\(28px \+ env\(safe-area-inset-bottom\)\);',
        CSS,
    ), "Modal inner must not form a competing scroll region or hide the footer"


def test_activation_artwork_and_combat_logic_are_unchanged():
    assert "experimental-activation-portrait" in APP
    assert "deathKorpsPortraitImage(activation.operativeId)" in APP
    assert "finishingCurrentHumanPlayerAction" in APP
    assert "playerActivationOperativeEliminated" in APP


def test_version_is_coordinated_for_offline_refresh():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
