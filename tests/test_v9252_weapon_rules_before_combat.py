#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def function_source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def render_shared_screen(guidance_html="", rules_html=""):
    renderer = "function showSharedCombatResolutionScreen" + function_source(
        "function showSharedCombatResolutionScreen", "function showCombatResumeRecovery"
    )
    script = f"""
let markup='';
const escapeHtml=value=>String(value);
const showModal=(title,html)=>{{markup=html;}};
const modal={{classList:{{add:()=>{{}}}},scrollTop:0}};
const modalBody={{scrollTop:0}};
const window={{scrollTo:()=>{{}}}};
const $=selector=>({{selector}});
{renderer}
showSharedCombatResolutionScreen({{
  title:'Resolve Combat',attackerName:'Canoptek Tomb Crawler 1',defenderName:'Blademaster',
  attackType:'shoot',weaponName:'Transdimensional isolator',attackLabel:'5 dice · 4+',
  defenseLabel:'3 dice · 3+',cancelId:'cancel',continueId:'continue',
  guidanceHtml:{json.dumps(guidance_html)},rulesHtml:{json.dumps(rules_html)}
}});
process.stdout.write(markup);
"""
    return subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True)


def dimensional_banishment_rules_html():
    handlers = APP[APP.index("const WEAPON_RULE_HANDLERS"):APP.index("const NPO_ACTION_TRANSITIONS")]
    renderer = "function weaponRulesHtml" + function_source(
        "function weaponRulesHtml", "function normalizedGuidanceMatchText"
    )
    summaries = APP[APP.index("  function normalizedWeaponRuleId"):APP.index("  function createWeaponRuleResolution")]
    script = f"""
const console={{warn:()=>{{}}}};
const escapeHtml=value=>String(value);
{handlers}
{renderer}
{summaries}
const profile={{rules:['Dimensional Banishment','Dimensional Banishment'],ruleIds:['dimensional-banishment']}};
process.stdout.write(weaponRulesHtml(profile));
"""
    return subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True)


def test_shared_shooting_dom_order_places_guidance_and_rules_before_dice_and_results():
    rules_html = dimensional_banishment_rules_html()
    markup = render_shared_screen(
        '<section data-guidance>Weapon Guidance: Weapon Sentinel</section>',
        f'<div data-rules>{rules_html}</div>',
    )
    assert markup.index("data-guidance") < markup.index("data-rules")
    assert markup.index("data-rules") < markup.index('id="automaticCombat"')
    assert markup.index('id="automaticCombat"') < markup.index('id="combatResults"')
    assert markup.count("Dimensional Banishment") == 1
    assert "Handled automatically." in markup


def test_optional_guidance_and_rules_sections_do_not_create_placeholders():
    guidance = '<section data-guidance>Weapon Guidance</section>'
    rules = '<section data-rules>Weapon Rules</section>'
    for guidance_html, rules_html in ((guidance, rules), (guidance, ""), ("", rules), ("", "")):
        markup = render_shared_screen(guidance_html, rules_html)
        assert ("data-guidance" in markup) is bool(guidance_html)
        assert ("data-rules" in markup) is bool(rules_html)
        if guidance_html and rules_html:
            assert markup.index("data-guidance") < markup.index("data-rules")
        for marker in ("data-guidance", "data-rules"):
            if marker in markup:
                assert markup.index(marker) < markup.index('id="automaticCombat"')


def test_dimensional_banishment_explanation_and_result_keep_distinct_positions():
    player = function_source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
    npo = function_source("function showNpoAttackWizard", "function spinnerField")
    resolution = function_source("function renderCombatResolution", "function combatAttackLabel")
    assert "rulesHtml:weaponRulesHtml(profile)" in player
    assert npo.index("guidanceHtml:") < npo.index("rulesHtml:")
    assert "rulesHtml:`<div id=\"npoCombatRules\">${weaponRulesHtml(initialProfile)}</div>`" in npo
    assert resolution.index("ATTACK DICE") < resolution.index("combatAbilityReminder(combat)")
    assert "dimensionalBanishmentTriggered" in resolution
    assert "resolveDimensionalBanishment" not in function_source(
        "function weaponRulesHtml", "function normalizedGuidanceMatchText"
    )


def test_fight_flow_remains_separate_and_unchanged_by_shooting_defense_layout():
    fight = function_source("async function startSharedFight", "function fightParticipantState")
    fight_roll = function_source("function renderFightRoll", "function fightResolutionRecordHtml")
    assert "showSharedCombatResolutionScreen" not in fight
    assert "DEFENSE DICE" not in fight_roll
    assert fight_roll.index("fightWeaponRulesHtml(fight)") < fight_roll.index("fightRollParticipantHtml(fight,'attacker'")


def test_v9252_version_surfaces_and_storage_compatibility():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 52)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
