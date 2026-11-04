"""Experimental Aggressive Defence outcome remains a pure, readable preview."""

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def outcome(roll, wounds, already_applied=False):
    helper = source("function experimentalAggressiveDefenseOutcome", "function aggressiveDefenseRollHtml")
    script = f"""
      const escapeHtml = value => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;');
      const aggressiveDefenseDamage = roll => roll >= 2 ? roll : 0;
      const fightParticipantPortrait = (participant, role) =>
        '<span class="fight-portrait deathwatch-portrait"><img src="Deathwatch_bombard.png" /></span>';
      {helper}
      console.log(JSON.stringify(experimentalAggressiveDefenseOutcome(
        {roll}, 'bombard', 'Bombard', {wounds}, {json.dumps(already_applied)}
      )));
    """
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return json.loads(completed.stdout)


def test_roll_one_keeps_wounds_unchanged_and_shows_the_model():
    result = outcome(1, 8)
    assert "D3 ROLL: 1" in result["html"]
    assert "Bombard" in result["html"]
    assert "Deathwatch_bombard.png" in result["html"]
    assert "No retaliatory damage" in result["html"]
    assert "8 → 8" in result["html"]
    assert "ELIMINATED" not in result["html"]


def test_damage_previews_wounds_and_elimination():
    survived = outcome(2, 8)
    assert "Took 2 retaliatory damage" in survived["html"]
    assert "8 → 6" in survived["html"]
    assert "ELIMINATED" not in survived["html"]
    eliminated = outcome(3, 2)
    assert "Took 3 retaliatory damage" in eliminated["html"]
    assert "2 → 0" in eliminated["html"]
    assert 'class="aggressive-defense-operative eliminated"' in eliminated["html"]
    assert '<strong class="fight-eliminated">ELIMINATED</strong>' in eliminated["html"]
    assert "Eliminated." in eliminated["announcement"]


def test_rolled_damage_never_produces_negative_wounds():
    assert "1 → 0" in outcome(3, 1)["html"]
    assert "8 → 8" in outcome(3, 8, already_applied=True)["html"]
    assert "already applied" in outcome(3, 8, already_applied=True)["html"]


def test_both_solo_tomb_modes_use_portrait_preview_and_pvp_keeps_legacy():
    resolver = source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    assert "const usePortraitResult=!isPvpMode()&&document.documentElement.dataset.ui==='tomb';" in resolver
    assert "experimentalAggressiveDefenseOutcome(" in resolver
    assert ": aggressiveDefenseOutcome(retaliation.roll,playerName(stage.playerOperativeId))" in resolver
    assert "playerCurrentWounds(stage.playerOperativeId)" in resolver
    assert "Boolean(pending.aggressiveDefenseDamageApplied)" in resolver
    before_click = resolver.split("button.onclick=", 1)[0]
    assert "state.playerWounds[" not in before_click
    assert "pending.aggressiveDefenseResolved=true" in resolver
    assert "if(aggressiveDamage>0&&!pending.aggressiveDefenseDamageApplied)" in resolver


def test_portrait_layout_is_mobile_safe_and_elimination_is_prominent():
    assert ".aggressive-defense-operative-portrait" in CSS
    assert "object-position:center bottom" in CSS
    assert ".aggressive-defense-operative.eliminated" in CSS
    assert "border:2px solid var(--danger)" in CSS
    assert "@media(max-width:380px)" in CSS
