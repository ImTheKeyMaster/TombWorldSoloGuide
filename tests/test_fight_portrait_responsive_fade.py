"""Responsive fade coverage for Fight Roll and Fight Result portraits."""

from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PORTRAITS = CSS.split(
    "/* Decorative upper-body portraits inside Fight Roll and Fight Result participant cards. */", 1
)[1].split("/* Recovery: show an actionable startup error", 1)[0]


def test_release_version_matches_asset_urls_and_service_worker():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX


def test_each_fight_card_is_its_own_width_container():
    card_rule = PORTRAITS.split(
        'html[data-ui="tomb"] .fight-roll-pool.has-fight-portrait,', 1
    )[1].split("}", 1)[0]
    assert '.fight-result-card.has-fight-portrait' in card_rule
    assert "container-type:inline-size" in card_rule
    assert "overflow:hidden" in card_rule
    assert "isolation:isolate" in card_rule
    assert 'html:not([data-ui="tomb"]) .fight-portrait{display:none}' in PORTRAITS


def test_narrow_cards_keep_the_existing_protective_fade():
    default_rule = PORTRAITS.split(
        'html[data-ui="tomb"] .fight-portrait{', 1
    )[1].split("}", 1)[0]
    assert "opacity:.44" in default_rule
    assert "pointer-events:none" in default_rule
    assert "rgba(0,0,0,.75) 32%,#000 65%" in default_rule
    assert "-webkit-mask-image:" in default_rule
    assert "mask-image:" in default_rule


def test_medium_cards_have_a_softer_fade_and_wide_cards_none():
    medium = PORTRAITS.split("@container (min-width:440px){", 1)[1].split(
        "@container (min-width:560px){", 1
    )[0]
    wide = PORTRAITS.split("@container (min-width:560px){", 1)[1]
    assert 'html[data-ui="tomb"] .fight-portrait{' in medium
    assert "rgba(0,0,0,.88) 23%,#000 50%" in medium
    assert "mask-image:linear-gradient(" in medium
    assert "html[data-ui=\"tomb\"] .fight-portrait{" in wide
    assert "-webkit-mask-image:none" in wide
    assert "mask-image:none" in wide
    assert "@media" not in medium + wide


def test_fight_result_full_height_and_card_content_layers_are_preserved():
    assert 'html[data-ui="tomb"] .fight-result-card .fight-portrait{' in PORTRAITS
    assert "height:100%" in PORTRAITS
    assert "transform:none" in PORTRAITS
    assert "z-index:0" in PORTRAITS and "z-index:1" in PORTRAITS
