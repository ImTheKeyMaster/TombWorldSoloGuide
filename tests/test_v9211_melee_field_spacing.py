import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def wizard_source():
    start = APP.index("function showPendingPlayerAttackWizard")
    return APP[start:APP.index("function showPlayerCombatResolution", start)]


WIZARD = wizard_source()


def test_target_and_weapon_selects_remain_in_order():
    target = '<select id="combatTarget">'
    weapon = '<select id="playerWeaponSelect">'
    assert target in WIZARD
    assert weapon in WIZARD
    assert WIZARD.index(target) < WIZARD.index(weapon)


def test_shoot_and_melee_weapon_fields_receive_six_pixel_top_spacing():
    assert "const weaponFieldClass='field weapon-field';" in WIZARD
    assert '<div class="${weaponFieldClass}"><label>Weapon</label>' in WIZARD
    assert ".weapon-field{margin-top:6px}" in CSS
    assert ".field{margin" not in CSS


def test_focus_visibility_and_native_select_appearance_are_preserved():
    assert not re.search(r"(?:select|\*):focus(?:-visible)?\s*\{\s*outline\s*:\s*none", CSS)
    field_select = CSS[CSS.index(".field select,.field input{"):CSS.index(".toggle-list")]
    assert not re.search(r"(?:-webkit-|-moz-)?appearance\s*:\s*none", field_select)
    assert "background-image" not in field_select
    assert "playerWeaponSelect::" not in CSS
    assert "combatTarget::" not in CSS


def test_select_dimensions_and_padding_are_unchanged():
    field_select = CSS[CSS.index(".field select,.field input{"):].split("}", 1)[0]
    assert "padding:13px" in field_select
    assert "min-height:47px" in field_select
    assert "border:1px solid var(--line)" in field_select
    assert "border-radius:12px" in field_select


def test_v928_details_and_continue_validation_remain_intact():
    assert "weapon-details${attackType==='melee'?' melee-weapon-summary melee-weapon-summary-pending':''}" in WIZARD
    assert "weaponRulesHtml(profile,{semanticHeading:true})" in WIZARD
    assert "weaponSummary.setAttribute('aria-hidden',String(!weapon))" in WIZARD
    assert "$('#openCombatResolution').disabled=!target||!weapon;" in WIZARD


def test_release_surfaces_and_save_schema():
    expected = CURRENT_APP_VERSION
    assert f"const APP_VERSION = '{expected}';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert f"styles.css?v={expected}" in INDEX
    assert f"app.js?v={expected}" in INDEX
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{expected}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
