"""Fight Resolution portrait baseline regression for Death Korps and Necron."""

from pathlib import Path
import re

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def css_rules(selector):
    return re.findall(re.escape(selector)+r"\s*\{([^}]*)\}",CSS)


def test_both_fight_cards_share_a_bottom_aligned_uncropped_miniature():
    frame='html[data-ui="tomb"] .experimental-fight-pool .fight-portrait'
    artwork='html[data-ui="tomb"] .experimental-fight-pool .fight-portrait-artwork'
    rules=css_rules(frame)
    assert len(rules)>=2
    assert "top:auto" in rules[-1]
    assert "bottom:0" in rules[-1]
    assert "height:100%" in rules[-1]
    art_rules=css_rules(artwork)
    assert "object-fit:contain" in art_rules[-1]
    assert "object-position:center bottom" in art_rules[-1]
    assert "experimental-fight-pools" in CSS
    assert "overflow:hidden" in CSS
    assert "fight-portrait.deathwatch-portrait" in CSS
    assert "opacity:.38" in CSS


def test_other_portrait_screens_and_existing_death_korps_zoom_unchanged():
    start=CSS.index("/* v10.0.186: Fight Resolution miniature bases")
    tail=CSS[start:].split("/* v10.0.187: Align both Fight Result",1)[0]
    assert ".experimental-fight-pool .fight-portrait" in tail
    assert ".fight-roll-pool" not in tail
    assert ".fight-result-card" not in tail
    assert ".experimental-activation-portrait" not in tail
    assert ".experimental-necron-activation-portrait" not in tail

    korps=(
      'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>'
      '.experimental-activation-portrait:has(img.death-korps-portrait-photo)'
      ' .experimental-activation-portrait-svg'
    )
    widths=[int(re.search(r"width:(\d+)%",r).group(1)) for r in css_rules(korps)]
    assert widths==[135,140,145],widths
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
    assert "function deathKorpsPortraitPhoto(" in APP
    assert "function experimentalNecronPortraitSvg(" in APP


def test_release_and_stored_game_data_unchanged():
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
