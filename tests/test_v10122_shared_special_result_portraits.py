"""Special weapon outcomes show their affected miniature in both Solo modes."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def hot_card(*, side="player", damage=0, before=15, after=15, eliminated=False):
    helper = source("function hotWeaponPortraitOutcome(record)", "async function showHotResult")
    script = f"""
      const escapeHtml=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
      const playerName=id=>'Disruptor';
      const npoName=n=>n.name;
      const state={{roster:[{{id:'necron-1',name:'Necron Warrior 1'}}]}};
      const fightParticipantPortrait=participant=>'<span class="fight-portrait"><img class="fight-portrait-artwork" src="'+participant.side+'-'+participant.id+'.png" /></span>';
      {helper}
      console.log(JSON.stringify(hotWeaponPortraitOutcome({{
        attackerSide:{json.dumps(side)},attackerId:{json.dumps('necron-1' if side == 'npo' else 'disruptor')},
        damage:{damage},woundsBefore:{before},woundsAfter:{after},
        incapacitated:{json.dumps(eliminated)}
      }})));
    """
    result = subprocess.run(["node", "-e", script], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout)


def test_hot_zero_damage_still_shows_operative_and_unchanged_wounds():
    html=hot_card()
    assert "Disruptor" in html
    assert "player-disruptor.png" in html
    assert 'class="aggressive-defense-operative"' in html
    assert "No damage" in html
    assert "15 → 15" in html
    assert "ELIMINATED" not in html


def test_hot_damage_and_lethal_results_and_necron_attackers():
    hit=hot_card(damage=4,before=15,after=11)
    assert "Took 4 Hot damage" in hit
    assert "15 → 11" in hit
    lethal=hot_card(damage=4,before=3,after=0,eliminated=True)
    assert "3 → 0" in lethal
    assert 'class="aggressive-defense-operative eliminated"' in lethal
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in lethal
    necron=hot_card(side="npo",damage=2,before=9,after=7)
    assert "Necron Warrior 1" in necron
    assert "npo-necron-1.png" in necron
    assert "9 → 7" in necron


def test_both_standard_and_experimental_use_the_same_portrait_result():
    aggressive=source("async function showAggressiveDefenseResolution",
                       "function showIncapacitationOrderChoice")
    hot=source("async function showHotResult", "function completeShootingWeaponUse")
    for code in (aggressive,hot):
        assert "document.documentElement.dataset.ui==='tomb'" in code
        assert "!isPvpMode()" in code
        assert "experimentalFeaturesEnabled()" not in code
    assert "const usePortraitResult=!isPvpMode()&&document.documentElement.dataset.ui==='tomb';" in aggressive
    assert "experimentalAggressiveDefenseOutcome(" in aggressive
    assert "const showPortraitResult=!isPvpMode()&&document.documentElement.dataset.ui==='tomb';" in hot
    assert "showPortraitResult?hotWeaponPortraitOutcome(record)" in hot
    assert '${resultOutcome}' in hot
    assert "class=\"\u0024{showPortraitResult?'aggressive-defense-result hot-weapon-result':''}\"" in hot


def test_shared_portrait_renderer_supports_all_available_team_pictures():
    renderer=source("function fightParticipantPortrait", "function scaleFightPortraits")
    hot=source("function hotWeaponPortraitOutcome", "async function showHotResult")
    retaliation=source("function experimentalAggressiveDefenseOutcome", "function aggressiveDefenseRollHtml")
    assert "deathwatchPortraitSvg(participant.id,'fight-portrait-artwork')" in renderer
    assert "deathKorpsCombatPortraitSvg(participant.id,'fight-portrait-artwork')" in renderer
    assert "experimentalNecronPortraitSvg(npo," in renderer
    assert "fightParticipantPortrait(participant,'hot-weapon')" in hot
    assert "fightParticipantPortrait({side:'player',id:operativeId},'aggressive-defence')" in retaliation
    assert ".aggressive-defense-operative-portrait" in CSS
    assert "object-fit:contain;object-position:center bottom" in CSS
    assert "min-height:184px" in CSS
    assert "max-width:none;max-height:none;margin:0;transform:none" in CSS


def test_existing_hot_resolution_is_read_only_when_rendering():
    record=source("function applyHotDamage", "async function resolveHotTransaction")
    result=source("function hotWeaponPortraitOutcome", "async function showHotResult")
    dialog=source("async function showHotResult", "function completeShootingWeaponUse")
    assert "if(record.applied)return record" in record
    assert "record.woundsBefore" in result and "record.woundsAfter" in result
    assert "state.playerWounds[" not in result
    assert "attacker.wounds=" not in result
    assert "record=await resolveHotTransaction(record)" in dialog
    assert "D6 Roll: ${record.roll}" in dialog
    assert "Hit Stat: ${record.effectiveHit}+" in dialog
    assert "const reducedMotion=isPvpMode()||matchMedia" in dialog
    assert "if(record.acknowledged)return record" in source("async function resolveHotTransaction", "function hotWeaponPortraitOutcome")
