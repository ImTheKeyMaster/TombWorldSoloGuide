"""v10.0.190: Death Korps is no larger than the Necron in Fight cards."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def css_rule(selector):
    matches = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert matches, selector
    return matches[-1]


def test_fight_result_necron_and_death_korps_share_identical_figure_frame():
    shared = css_rule('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait')
    assert "width:min(100%,190px)" in shared
    assert "inset:0 0 0 auto" in shared
    assert "height:100%" in shared
    assert "opacity:.4" in shared
    assert "mask-image:linear-gradient" in shared
    # No faction-specific zoom, width or right offset in Fight Result.
    assert '.fight-result-card.has-fight-portrait .fight-portrait.death-korps-portrait{' not in CSS


def test_fight_resolution_both_factions_share_size_at_all_phone_widths():
    shared = css_rule('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait')
    assert "width:98px" in CSS
    assert "max-width:68%" in CSS
    assert "bottom:0" in shared and "top:auto" in shared
    assert "height:100%" in shared
    assert '.experimental-fight-pool .fight-portrait.death-korps-portrait{' not in CSS
    # Responsive 390px and 374px rules apply to BOTH factions.
    for width, height in (("78px", "100px"), ("65px", "90px")):
        assert f"width:{width}" in CSS
        assert f"height:{height}" in CSS


def test_fight_artwork_remains_full_height_contained_and_bottom_aligned():
    result_photo = css_rule('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait .fight-portrait-artwork')
    combined = ('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait .fight-portrait-artwork,\n'
                'html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait .fight-portrait-artwork')
    shared_photo = css_rule(combined)
    for rule in (result_photo, shared_photo):
        for declaration in ("width:100%", "height:100%", "object-fit:contain", "object-position:center bottom", "transform:none"):
            assert declaration in rule
    assert "margin:0" in shared_photo
    assert "max-height:100%" in shared_photo
    for obsolete in ("width:min(76%,118px)", "width:min(115%,205px)",
                     "height:calc(100% - 14px)", "height:calc(100% - 18px)"):
        assert obsolete not in CSS


def test_no_change_to_activation_artwork_pipeline_or_game_state():
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
    assert "function warmDeathKorpsPortraitImages(" in APP
    assert "function warmDeathwatchPortraitImages(" in APP
    assert "function experimentalNecronPortraitSvg(" in APP
    assert "function fightParticipantPortrait(participant,role)" in APP
    assert "death-korps-portrait" in APP
    for width in (135, 140, 145):
        assert f"width:{width}%" in CSS
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const EXPERIMENTAL_FEATURES_KEY = 'tombWorldSolo.experimentalFeatures.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
