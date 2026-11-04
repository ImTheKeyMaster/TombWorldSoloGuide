"""All six Deathwatch ammo choices explain the benefit without changing mechanics."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def slice_between(first, last):
    return APP[APP.index(first):APP.index(last, APP.index(first))]


def node(source):
    run = subprocess.run(
        ["node", "-e", source], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert run.returncode == 0, run.stderr or run.stdout


def test_six_options_have_specific_accurate_benefits_and_no_unsupported_choices():
    definitions = slice_between("const DEATHWATCH_SPECIAL_AMMO=", "function deathwatchAmmoTransaction")
    legality = slice_between("function deathwatchAmmoLegal(", "function deathwatchAugmentProfile")
    node("""
const assert=require('node:assert/strict');
const escapeHtml = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;');
""" + definitions + legality + """
const labels=['Blast 1"','Devastating 1','Lethal 5+','Piercing Crits 1','Saturate','Severe'];
assert.deepEqual([...DEATHWATCH_SPECIAL_AMMO],labels);
assert.deepEqual(Object.keys(DEATHWATCH_AMMO_BENEFITS),labels);
const legalWeapon={name:'Bolt pistol',rules:[]};
for(const rule of labels){
  const markup=deathwatchAmmoBenefitHtml(rule,legalWeapon);
  assert(markup.includes(rule.replaceAll('"','&quot;')) || markup.includes(rule));
  assert(markup.includes('AMMUNITION BENEFIT'));
  assert(markup.includes('The Guide applies this effect automatically.'));
  assert(!markup.includes('undefined'));
}
assert(deathwatchAmmoBenefitHtml('Devastating 1', {name:'Bolt pistol',rules:['Devastating 1']}).includes('already has this rule'));
assert.equal(deathwatchAmmoBenefitHtml('Blast 1"',{name:'Flame weapon',rules:['Torrent 2"']}),'');
assert.equal(deathwatchAmmoBenefitHtml('Severe',{name:'Melta bomb',rules:[]}), '');
assert.equal(deathwatchAmmoBenefitHtml('',legalWeapon),'');
assert.equal(deathwatchAmmoBenefitHtml('Fake',legalWeapon),'');
assert(DEATHWATCH_AMMO_BENEFITS['Devastating 1'].includes('immediate damage'));
assert(DEATHWATCH_AMMO_BENEFITS['Lethal 5+'].includes('5 or 6'));
assert(DEATHWATCH_AMMO_BENEFITS['Piercing Crits 1'].includes('fewer defence die'));
assert(DEATHWATCH_AMMO_BENEFITS['Saturate'].includes('cover saves'));
assert(DEATHWATCH_AMMO_BENEFITS['Severe'].includes('one normal success'));
assert(DEATHWATCH_AMMO_BENEFITS['Blast 1"'].includes('other operatives'));
""")


def test_dynamic_guidance_is_in_both_solo_modes_and_next_to_selector():
    wizard = slice_between("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
    assert "const showAmmoGuidance=ammunitionAvailable&&document.documentElement.dataset.ui==='tomb'&&(!isPvpMode()||experimentalFeaturesEnabled());" in wizard
    assert "${showAmmoGuidance?" in wizard
    assert "${experimentalAmmoGuidance?" not in wizard
    assert 'id="deathwatchAmmoBenefit"' in wizard
    assert wizard.index("${ammunitionControl}") < wizard.index("deathwatchAmmoBenefit") < wizard.index("${secondShootHint}")
    assert "stage.deathwatchAmmoRule=ammunition.value" in wizard
    assert "const html=ammunition.value?deathwatchAmmoBenefitHtml(ammunition.value,weapon):'';" in wizard
    assert "benefit.hidden=!html;" in wizard
    assert "$('#deathwatchAmmo')?.addEventListener('change',renderChoices)" in wizard
    assert "weaponSelect.addEventListener('change',renderChoices)" in wizard
    assert ".deathwatch-ammo-benefit:not([hidden])" in CSS


def test_ammo_and_attack_mechanics_still_use_existing_transaction_and_rules():
    ammo = slice_between("function deathwatchAmmoTransaction", "function playerWeaponProfile")
    wizard = slice_between("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
    assert "deathwatchAmmoTransaction().used" in ammo
    assert "critThreshold:rule==='Lethal 5+'?Math.min(5,profile.critThreshold)" in ammo
    assert "const rules=profile.rules.includes(rule)?profile.rules:[...profile.rules,rule]" in ammo
    assert "option.disabled=!deathwatchAmmoLegal(weapon,option.value)" in wizard
    assert "playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex,stage})" in wizard


def test_ammo_guidance_mode_gate_behaviour():
    wizard = slice_between("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
    predicate = next(line.strip() for line in wizard.splitlines() if line.strip().startswith("const showAmmoGuidance="))
    node(f"""
const assert=require('node:assert/strict');
for(const mode of ['standard','experimental']){{
  for(const gameMode of ['solo','pvp']){{
    for(const available of [false,true]){{
      const ammunitionAvailable=available;
      const document={{documentElement:{{dataset:{{ui:'tomb'}}}}}};
      const isPvpMode=()=>gameMode==='pvp';
      const experimentalFeaturesEnabled=()=>mode==='experimental';
      {predicate}
      assert.equal(showAmmoGuidance,available&&(gameMode==='solo'||mode==='experimental'));
    }}
  }}
}}
""")
