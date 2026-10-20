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
    '.experimental-activation-portrait:has(image[href*="Death_Korps_"])'
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
    assert "experimentalDeathwatchActivationImage(activation.operativeId)" in APP
    assert 'experimental-activation-portrait' in APP
    assert "Death_Korps_" in KORPS_SELECTOR
    assert "Deathwatch" not in KORPS_SELECTOR
    assert "experimental-roster" not in KORPS_SELECTOR
    # These targeted rules must win over the older, general non-Marksman zoom.
    assert CSS.index(KORPS_SELECTOR) > CSS.index('/* v10.0.135: Reveal the miniature')


def test_landscape_desktop_matches_deathwatch_figure_footprint():
    rule = portrait_rules()[0]
    assert "width:150%;" in rule
    assert "right:-8%;" in rule
    assert "top:10px;" in rule
    assert "transform:none;" in rule
    assert "clip-path" not in rule  # Retain the existing overlap and silhouette treatment.


def test_iphone_portrait_uses_smaller_scale_and_narrow_fallback():
    rules = portrait_rules()
    assert re.search(
        r"@media\(max-width:520px\)\s*\{\s*" + re.escape(KORPS_SELECTOR),
        CSS,
    )
    assert "width:157%;" in rules[1]
    assert "right:-8%;" in rules[1]
    assert "top:12px;" in rules[1]
    assert re.search(
        r"@media\(max-width:380px\)\s*\{\s*" + re.escape(KORPS_SELECTOR),
        CSS,
    )
    assert "width:160%;" in rules[2]
    assert "right:-9%;" in rules[2]
    assert "top:10px;" in rules[2]


def test_existing_activation_scroll_and_portrait_layering_are_preserved():
    assert "#modal.human-activation-modal" in CSS
    assert "overflow-y:auto;" in CSS
    assert "grid-row:1 / span 2;" in CSS
    assert "pointer-events:none;" in CSS
    assert "experimental-activation-portrait:not(:has(image[href*=" in CSS


def test_release_version_and_cache_are_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    for asset in ("styles.css", "app.js", "mission-engine.js"):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in HTML
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
