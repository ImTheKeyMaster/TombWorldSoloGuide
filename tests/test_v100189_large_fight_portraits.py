"""v10.0.189: Large, fully contained and bottom-aligned native Fight portraits."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def last_rule(selector):
    blocks = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert blocks, selector
    return blocks[-1]


def test_fight_result_necron_regains_large_frame_and_retains_bottom_baseline():
    frame = last_rule('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait')
    assert "width:min(100%,190px)" in frame
    assert "width:min(48%,148px)" not in CSS
    assert "inset:0 0 0 auto" in frame
    assert "height:100%" in frame
    assert "opacity:.4" in frame
    assert "-webkit-mask-image:linear-gradient" in frame
    assert "mask-image:linear-gradient" in frame
    # v10.0.190 removes the v10.0.189 Death Korps-only enlarged frame.
    # Both factions now inherit this same result card frame.
    tail = CSS.split("/* v10.0.190:", 1)[1]
    assert "width:min(115%,205px)" not in CSS
    assert ".fight-portrait.death-korps-portrait{" not in tail


def test_fight_resolution_korps_larger_and_same_full_height_alignment():
    shared_frame = last_rule('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait')
    assert "top:auto" in shared_frame
    assert "bottom:0" in shared_frame
    assert "height:100%" in shared_frame
    # Death Korps and Necrons inherit the same 98px/68% responsive frame.
    frame = CSS.split('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait{', 1)[1].split('}', 1)[0]
    assert "width:98px" in frame
    assert "max-width:68%" in frame
    assert "width:min(76%,118px)" not in CSS
    # The Necron stays on the already-approved 98px Fight Resolution scale.
    assert "width:98px" in CSS
    assert "height:calc(100% - 14px)" not in CSS
    assert "height:calc(100% - 18px)" not in CSS


def test_both_fight_surfaces_use_one_uncropped_bottom_aligned_photo_rule():
    # Limit the original portrait regression to rules preceding subsequent
    # unrelated Experimental UI experiments (such as the VS badge shadow).
    tail = CSS.split("/* v10.0.190: Fight Resolution", 1)[1].split(
        "/* v10.0.206/213: Approved Solo Fight Resolution design promoted to Standard.", 1
    )[0]
    selector = ('html[data-ui="tomb"] .experimental-fight-pool .fight-portrait .fight-portrait-artwork,\n'
                'html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait .fight-portrait-artwork')
    rule = last_rule(selector)
    for declaration in ("display:block", "width:100%", "height:100%", "max-height:100%",
                        "margin:0", "object-fit:contain", "object-position:center bottom",
                        "transform:none"):
        assert declaration in rule, declaration
    assert "clip-path:" not in tail
    assert "filter:" not in tail
    assert "opacity:" not in tail
    assert "body" not in tail


def test_text_fades_shared_pipeline_activation_and_state_preserved():
    assert '.fight-result-card.has-fight-portrait>*:not(.fight-portrait)' in CSS
    assert '.fight-result-card.has-fight-portrait>h3' in CSS
    assert '.fight-result-card.has-fight-portrait dl' in CSS
    assert 'text-shadow:0 1px 5px' in CSS
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
    assert "return portraitImageMarkup(deathwatchPortraitImage(id)" in APP
    assert "return portraitImageMarkup(deathKorpsPortraitImage(id)" in APP
    assert "return portraitImageMarkup(src?" in APP
    assert "function warmDeathwatchPortraitImages(" in APP
    assert "function warmDeathKorpsPortraitImages(" in APP
    assert "function experimentalNecronPortraitImage(npo)" in APP  # Necron source selection remains shared
    for width in (135, 140, 145):
        assert f"width:{width}%" in CSS
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const EXPERIMENTAL_FEATURES_KEY = 'tombWorldSolo.experimentalFeatures.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
