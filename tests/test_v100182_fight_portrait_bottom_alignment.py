"""Ensure Death Korps heads fit and miniature bases align in Fight Resolution."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def test_only_death_korps_moves_down_in_fight_resolution():
    specific='html[data-ui="tomb"] .experimental-fight-pool .fight-portrait.death-korps-portrait'
    rule=re.findall(re.escape(specific)+r"\\s*\\{([^}]*)\\}",CSS)
    assert len(rule)==1
    assert "top:12px;" in rule[0]
    assert "bottom:auto;" in rule[0]
    art=specific+' .fight-portrait-artwork'
    art_rule=re.findall(re.escape(art)+r"\\s*\\{([^}]*)\\}",CSS)
    assert len(art_rule)==1
    assert "object-position:center bottom" in art_rule[0]
    assert "object-fit:contain" in art_rule[0]
    assert "transform:none" in art_rule[0]
    assert "html[data-ui=\\"tomb\\"] .fight-portrait.deathwatch-portrait" in CSS
    assert "opacity:.38" in CSS
    # Do not add new overrides to the generic Necron or Deathwatch portrait.
    tail=CSS.split("/* v10.0.182: Move ONLY Death Korps Fight Resolution",1)[1]
    assert '.experimental-fight-pool .fight-portrait{' not in tail
    assert '.fight-result-card.has-fight-portrait .fight-portrait{' not in tail


def test_only_death_korps_fight_result_is_bottom_aligned():
    selector='html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait.death-korps-portrait'
    rule=re.findall(re.escape(selector)+r"\\s*\\{([^}]*)\\}",CSS)
    assert len(rule)==1
    assert "inset:0 0 0 auto" in rule[0]
    assert "height:100%" in rule[0]
    art=selector+' .fight-portrait-artwork'
    art_rule=re.findall(re.escape(art)+r"\\s*\\{([^}]*)\\}",CSS)
    assert len(art_rule)==1
    assert "object-fit:contain" in art_rule[0]
    assert "object-position:center bottom" in art_rule[0]
    assert "transform:none" in art_rule[0]
    assert "death-korps-portrait" in APP
    assert "deathKorpsPortraitImage(participant.id)" in APP
    assert "html[data-ui=\\"tomb\\"] .fight-result-card .fight-portrait{" in CSS

def test_death_korps_activation_zoom_reduced_for_full_figure():
    selector=(
      'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>'
      '.experimental-activation-portrait:has(img.death-korps-portrait-photo)'
      ' .experimental-activation-portrait-svg'
    )
    rules=re.findall(re.escape(selector)+r"\s*\{([^}]*)\}",CSS)
    assert len(rules)==3
    for rule,max_zoom in zip(rules,(138,145,148)):
        zoom=int(re.search(r"width:(\d+)%",rule).group(1))
        assert zoom<=max_zoom
        assert zoom<150
    assert "object-fit:contain" in CSS
    assert "clip-path:inset(-96px -96px -64px -220px)" in CSS
    assert "pointer-events:none" in CSS


def test_shared_native_renderer_keeps_faction_sources_and_combat_rules_untouched():
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
    for term in ("deathwatchPortraitSvg","deathKorpsPortraitPhoto","experimentalNecronPortraitSvg"):
        assert f"function {term}(" in APP
    assert "return portraitImageMarkup(" in APP
    assert "function experimentalActionFirstFightHtml(" in APP
    assert "function semanticFightActions(" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
