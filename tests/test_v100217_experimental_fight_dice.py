"""Regression coverage for approved Fight dice (Experimental in 10.0.217, promoted in 10.1.0)."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_static_dice_reuse_rolled_faces_with_standard_experimental_parity():
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const app = fs.readFileSync('app.js', 'utf8');
const start = app.indexOf('  function experimentalFightPoolHtml(');
const end = app.indexOf('  function experimentalFightResolutionHtml(', start);
assert(start > 0 && end > start);
let experimental = false;
const context = {
  experimentalFeaturesEnabled: () => experimental,
  unresolvedFightSuccesses: (fight, role) => fight.successes[role].filter(item => item.status === 'unresolved'),
  fightParticipantPortrait: () => '',
  dieHtml: die => `<div class="die ${die.kind}" data-face="${die.value}" aria-label="${die.ariaLabel}"></div>`,
  escapeHtml: String
};
const render = new Function('ctx', 'with(ctx) {' + app.slice(start, end) + 'return experimentalFightPoolHtml;}')(context);
const makeParticipant = () => ({
  side: 'player', label: 'Gunner', profile: {name:'Fists'}, wounds:12, maxWounds:15,
  attackDice: [{value:2}, {value:5}, {value:6}, {value:4}, {value:3}, {value:1}]
});
const fight = {
  turn:'attacker',
  attacker:makeParticipant(),
  defender:{...makeParticipant(),side:'npo',label:'Macrocyte'},
  successes:{
    attacker: [
      {dieIndex:0,value:2,kind:'normal',status:'unresolved'},
      {dieIndex:1,value:5,kind:'normal',status:'unresolved'},
      {dieIndex:2,value:6,kind:'critical',status:'unresolved'},
      {dieIndex:3,value:4,kind:'normal',status:'unresolved'},
      {dieIndex:4,value:3,kind:'critical',status:'unresolved'},
      {dieIndex:5,value:1,kind:'normal',status:'spent'}
    ],
    defender: [
      {dieIndex:2,value:6,kind:'critical',status:'unresolved'},
      {dieIndex:0,value:2,kind:'normal',status:'unresolved'}
    ]
  }
};
const standard = render(fight, 'attacker');
assert(!standard.includes('Crits 2'));
assert(!standard.includes('Normal 3'));
assert(standard.includes('experimental-fight-card-dice'));
assert.deepEqual([...standard.matchAll(/data-face="(\d)"/g)].map(m=>Number(m[1])),[2,5,6,4,3]);
experimental = true;
const preview = render(fight, 'attacker');
assert.equal(preview, standard, 'Standard and Experimental must show identical dice');
assert.deepEqual([...preview.matchAll(/data-face="(\d)"/g)].map(m=>Number(m[1])),[2,5,6,4,3]);
assert.equal((preview.match(/class="die hit"/g)||[]).length,3);
assert.equal((preview.match(/class="die crit"/g)||[]).length,2);
assert(!preview.includes('rolling'));
assert(!preview.includes('animated-roll'));
assert(preview.includes('Unresolved successes: 2 critical, 3 normal'));
const defender = render(fight,'defender');
assert.equal((defender.match(/class="die /g)||[]).length,2);
assert(defender.includes('data-face="6"') && defender.includes('data-face="2"'));
fight.successes.attacker[2].status='blocked';
assert.equal((render(fight,'attacker').match(/class="die /g)||[]).length,4,
  'Used or blocked dice must disappear');
fight.attacker.attackDice[0].value=4;
assert(render(fight,'attacker').includes('data-face="4"'),
  'The actual original die value has priority over a stale success snapshot');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr or result.stdout


def test_five_equal_responsive_die_slots_and_original_palette():
    section = CSS.split("/* v10.1.0: Approved Fight summary dice", 1)[1]
    assert "grid-template-columns:repeat(5,minmax(0,1fr));" in section
    assert "aspect-ratio:1;" in section
    assert "width:100%;" in section
    assert "height:auto;" in section
    assert "box-sizing:border-box;" in section
    assert "animation:none;" in section
    assert ".experimental-fight-card-dice .pip" in section
    assert ".die.crit{background:#8b6c1f;border-color:#f0d570}" in CSS
    assert ".die{width:44px;height:44px;" in CSS
    assert "experimental-fight-card-dice" not in CSS.split("/* v10.1.0: Approved Fight summary dice",1)[0]
