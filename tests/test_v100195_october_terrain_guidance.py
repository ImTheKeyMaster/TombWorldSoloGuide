"""October 28 Kill Team terrain clarifications are reference-only, not mechanics."""

from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")
HTML=(ROOT/"index.html").read_text(encoding="utf-8")
SW=(ROOT/"service-worker.js").read_text(encoding="utf-8")
README=(ROOT/"README.md").read_text(encoding="utf-8")


def run_node(source):
    result=subprocess.run(["node","-e",source],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode==0, result.stderr or result.stdout


def test_help_screen_shows_all_three_terrain_updates_in_both_modes():
    source=r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf('  function terrainShootingHintHtml(){');
const end=app.indexOf('  function renderHome(){',start);
assert(start>0&&end>start);
const source=app.slice(start,end);
for(const pvp of [false,true]){
  const ctx={isPvpMode:()=>pvp,playerSideLabel:()=>pvp?'Imperium':'Player',
    opponentSingularLabel:()=>pvp?'Necron':'NPO',
    escapeHtml:x=>x,presentSideTerminology:x=>x};
  const api=new Function('ctx','with(ctx){'+source+'return {guideInstructionsHtml,terrainShootingHintHtml};}')(ctx);
  for(const full of [false,true]){
    const reference=api.guideInstructionsHtml(full);
    assert.match(reference,/Terrain update · 28 October 2026/);
    assert.match(reference,/Tomb World walls/);
    assert.match(reference,/normal Kill Team terrain rules/);
    assert.match(reference,/Vantage Points/);
    assert.match(reference,/rampart's Light or Heavy cover/);
    assert.match(reference,/targeting line/);
    assert.match(reference,/Ladders/);
    assert.match(reference,/permitted span/);
    assert.match(reference,/warhammer-community.com\/en-gb\/articles\/k04goqrk\/kill-team-october-update/);
    assert.match(reference,/The Guide cannot measure terrain/);
  }
  const hint=api.terrainShootingHintHtml();
  assert.match(hint,/<details class="terrain-shooting-hint">/);
  assert.doesNotMatch(hint,/<details[^>]*open\b/);
  assert.match(hint,/pillars/);
  assert.match(hint,/rampart/);
  assert.match(hint,/targeting line/);
}
"""
    run_node(source)


def test_shooting_hints_are_read_only_and_do_not_affect_melee_or_combat():
    player=APP.split("  function showPendingPlayerAttackWizard(",1)[1].split("  function showPlayerCombatResolution(",1)[0]
    npo=APP.split("  function showExperimentalNpoWeaponSelection(",1)[1].split("  function showNpoAttackConditionCheck(",1)[0]
    assert "${attackType==='shoot'?terrainShootingHintHtml():''}" in player
    assert "${terrainShootingHintHtml()}" in npo
    assert player.count("terrainShootingHintHtml()")==1
    assert npo.count("terrainShootingHintHtml()")==1
    assert "weaponSelect.addEventListener('change',renderChoices)" in player
    assert "const weaponControl=weapons.length===1" in player
    assert "if(!singleProfile)select.addEventListener('change',updateGuidance)" in npo
    assert "if(rules)rules.innerHTML=profile?weaponRulesHtml(profile):''" in npo
    assert ".terrain-shooting-hint summary" in CSS
    assert ".terrain-shooting-hint p" in CSS
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_release_and_review_scope():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'V{CURRENT_APP_VERSION}' in HTML
    assert f'app.js?v={CURRENT_APP_VERSION}' in HTML
    assert f'styles.css?v={CURRENT_APP_VERSION}' in HTML
    assert "team errata remain on hold" in README.lower()
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
