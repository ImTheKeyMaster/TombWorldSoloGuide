"""Death Korps activation miniature framing stays proportionate across orientations."""

import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")

KORPS_SELECTOR = (
    'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>'
    '.experimental-activation-portrait:has(img.death-korps-portrait-photo)'
    ' .experimental-activation-portrait-svg'
)


def portrait_rules():
    rules = re.findall(re.escape(KORPS_SELECTOR) + r"\s*\{([^}]*)\}", CSS)
    assert len(rules) == 3, "Expected landscape/default, phone, and narrow-phone rules"
    return rules


def test_death_korps_only_not_deathwatch_or_roster():
    assert "const DEATH_KORPS_PORTRAIT_ROOT=" in APP
    assert "Death_Korps_${filename}.png" in APP
    assert "portraitMarkup:document.documentElement.dataset.ui==='tomb'" in APP
    assert "selectedPlayerTeamName().toLowerCase()==='death korps'" in APP
    assert "deathwatchPortraitImage(activation.operativeId)" in APP
    assert 'experimental-activation-portrait' in APP
    assert "death-korps-portrait-photo" in KORPS_SELECTOR
    assert "Deathwatch" not in KORPS_SELECTOR
    assert "experimental-roster" not in KORPS_SELECTOR
    # These targeted rules must win over the older general Deathwatch zoom.
    assert CSS.index(KORPS_SELECTOR) > CSS.index('/* v10.0.135/169: Reveal the portrait')


def test_landscape_desktop_shows_more_of_full_miniature():
    rule = portrait_rules()[0]
    assert "width:135%;" in rule
    assert "right:-5%;" in rule
    assert "top:4px;" in rule
    assert "transform:none;" in rule
    assert "clip-path" not in rule  # Retain the existing overlap and silhouette treatment.


def test_iphone_portrait_scales_down_to_show_full_model_and_base():
    rules = portrait_rules()
    assert re.search(
        r"@media\(max-width:520px\)\s*\{\s*" + re.escape(KORPS_SELECTOR),
        CSS,
    )
    assert "width:140%;" in rules[1]
    assert "right:-5%;" in rules[1]
    assert "top:8px;" in rules[1]
    assert re.search(
        r"@media\(max-width:380px\)\s*\{\s*" + re.escape(KORPS_SELECTOR),
        CSS,
    )
    assert "width:145%;" in rules[2]
    assert "right:-6%;" in rules[2]
    assert "top:6px;" in rules[2]


def test_miniature_zoom_is_reduced_from_v100184_and_other_factions_unchanged():
    rules = portrait_rules()
    widths = [int(re.search(r"width:(\\d+)%", rule).group(1)) for rule in rules]
    assert widths == [135, 140, 145]
    assert all(new < old for new, old in zip(widths, [185, 195, 200]))
    assert all(new < old for new, old in zip(widths, [150, 157, 160]))
    assert ":has(img.death-korps-portrait-photo)" in KORPS_SELECTOR
    assert "img.deathwatch-portrait-photo" in CSS
    assert "img.experimental-necron-framed-svg" in CSS


def test_existing_activation_scroll_and_portrait_layering_are_preserved():
    assert "#modal.human-activation-modal" in CSS
    assert "overflow-y:auto;" in CSS
    assert "grid-row:1 / span 2;" in CSS
    assert "pointer-events:none;" in CSS
    assert "experimental-activation-portrait .experimental-activation-portrait-svg" in CSS


def test_release_version_and_cache_are_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    for asset in ("styles.css", "app.js", "mission-engine.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in HTML
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
