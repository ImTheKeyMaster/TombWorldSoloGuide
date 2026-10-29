"""Regression tests for Solo NPO Strike/Block decisions and the Aegis/Macrocyte fight."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_solo_npo_chooses_legal_tactically_useful_fight_actions():
    # Execute the real production functions, rather than copying the heuristic
    # into the test. Include the shared Strike/Block commit paths.
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync('app.js', 'utf8');

function functionSource(name) {
  const start = source.indexOf('  function ' + name + '(');
  assert(start >= 0, 'Missing production function ' + name);
  const next = source.indexOf('\n  function ', start + 12);
  return source.slice(start, next < 0 ? source.length : next);
}
const names = [
  'otherFightRole', 'unresolvedFightSuccesses', 'fightBlockTargets',
  'advanceFightTurn', 'commitFightStrike', 'commitFightBlock',
  'soloNpoFightDecision'
];
const ctx = {
  weaponHasRule: (profile, id) => (profile.ruleIds || []).includes(id),
  isDeathwatchPlayerTeam: () => false,
  pendingPlayerNpoFightIncapacitation: () => false,
  setFightOperativeWounds: () => {},
  resolveFightShock: () => null,
  qualifyingWhirlingStrike: () => false,
  qualifyingHorrifyingFlaying: () => false,
  state: {roster: []},
  save: () => {}
};
const engine = new Function(
  'ctx', 'with(ctx){\n' + names.map(functionSource).join('\n') +
  '\nreturn {' + names.join(',') + '};\n}'
)(ctx);
const {soloNpoFightDecision: decide, commitFightStrike: strike,
       commitFightBlock: block, fightBlockTargets: legalTargets} = engine;

function fight({playerWounds = 15, npoWounds = 7,
                playerDice = ['critical', 'critical', 'normal'],
                npoDice = ['normal'], capacity = 1, brutal = false} = {}) {
  const dice = (kinds, prefix) => kinds.map((kind, index) => ({
    id: prefix + index, kind, status: 'unresolved'
  }));
  return {
    id: 'aegis-macrocyte', turn: 'attacker', history: [],
    resolutionIndex: 0, completed: false, ruleTriggers: {},
    attacker: {id: 'aegis', label: 'Aegis', side: 'player', wounds: playerWounds,
      profile: {normal: 4, crit: 6, ruleIds: brutal ? ['brutal'] : []}},
    defender: {id: 'macrocyte', label: 'Canoptek Macrocyte Warrior 1',
      side: 'npo', wounds: npoWounds,
      profile: {normal: 3, crit: 4, ruleIds: []}},
    successes: {attacker: dice(playerDice, 'a'), defender: dice(npoDice, 'n')},
    blockCapacity: {attacker: 2, defender: capacity}
  };
}

// Exact screenshot sequence: Aegis's initial critical deals 6 (7 -> 1);
// Aegis still has one critical and one normal, while the NPO has one
// normal. It cannot parry the lethal critical, so it must Strike instead
// of wasting its only remaining success blocking Aegis's normal.
{
  const f = fight();
  assert(strike(f, 'attacker', 'a0'));
  assert.equal(f.defender.wounds, 1);
  assert.equal(f.turn, 'defender');
  const choice = decide(f, 'defender');
  assert.deepEqual(choice, {type: 'strike', successId: 'n0'});
  assert(strike(f, 'defender', choice.successId));
  assert.equal(f.attacker.wounds, 12);
  assert.equal(f.history[1].type, 'strike');
  assert(strike(f, 'attacker', 'a2'));
  assert.equal(f.defender.wounds, 0);
  assert.equal(f.completed, true);
  assert.deepEqual(f.history.map(entry => entry.type),
                   ['strike', 'strike', 'strike']);
}

// A legal critical Block prevents an immediately lethal critical Strike.
{
  const f = fight({npoWounds: 5, playerDice: ['critical'],
                   npoDice: ['critical']});
  f.turn = 'defender';
  const choice = decide(f, 'defender');
  assert.deepEqual(choice, {type: 'block', successId: 'n0',
                            targetSuccessIds: ['a0']});
  assert(block(f, 'defender', choice.successId, choice.targetSuccessIds));
  assert.equal(f.successes.attacker[0].status, 'blocked');
}

// A normal Block can stop a lethal normal success.
{
  const f = fight({npoWounds: 3, playerDice: ['normal'],
                   npoDice: ['normal']});
  f.turn = 'defender';
  assert.equal(decide(f, 'defender').type, 'block');
}

// A killing NPO Strike wins priority over a defensive Block.
{
  const f = fight({playerWounds: 3, npoWounds: 5,
                   playerDice: ['critical'], npoDice: ['normal']});
  f.turn = 'defender';
  const choice = decide(f, 'defender');
  assert.deepEqual(choice, {type: 'strike', successId: 'n0'});
  assert(strike(f, 'defender', choice.successId));
  assert.equal(f.attacker.wounds, 0);
  assert.equal(f.completed, true);
}

// Regression: even a two-success Shield cannot block a lethal critical
// using a normal success. Do not Block an irrelevant normal instead.
{
  const f = fight({npoWounds: 1, capacity: 2,
                   playerDice: ['critical', 'normal'],
                   npoDice: ['normal']});
  f.turn = 'defender';
  assert.deepEqual(decide(f, 'defender'),
                   {type: 'strike', successId: 'n0'});
}

// When both enemy normals together are lethal, a two-success Shield
// may Block both and should be preferred over a nonlethal Strike.
{
  const f = fight({npoWounds: 5, capacity: 2,
                   playerDice: ['normal', 'normal'],
                   npoDice: ['normal']});
  f.turn = 'defender';
  const choice = decide(f, 'defender');
  assert.deepEqual(choice, {type: 'block', successId: 'n0',
                            targetSuccessIds: ['a0', 'a1']});
  assert(block(f, 'defender', choice.successId, choice.targetSuccessIds));
  assert(f.successes.attacker.every(die => die.status === 'blocked'));
}

// Brutal disallows a normal Block, even against a normal success.
{
  const f = fight({npoWounds: 1, brutal: true,
                   playerDice: ['normal'], npoDice: ['normal']});
  f.turn = 'defender';
  assert.deepEqual(decide(f, 'defender'),
                   {type: 'strike', successId: 'n0'});
  assert.equal(block(f, 'defender', 'n0', ['a0']), false);
}

// Vary dice pools, wound totals, Shield capacity, and Brutal. The AI
// must never propose an illegal or duplicate Block target, and must
// not waste a normal Block when an unblocked critical is already lethal.
for (const playerDice of [['normal'], ['critical'],
                          ['critical', 'normal'], ['normal', 'normal']]) {
  for (const npoDice of [['normal'], ['critical'], ['normal', 'critical']]) {
    for (const npoWounds of [1, 3, 5, 7, 10]) {
      for (const capacity of [1, 2]) {
        for (const brutal of [false, true]) {
          const f = fight({playerWounds: 15, npoWounds, playerDice,
                           npoDice, capacity, brutal});
          f.turn = 'defender';
          const choice = decide(f, 'defender');
          const owner = f.successes.defender.find(d => d.id === choice.successId);
          assert(owner, 'AI must consume an available own success');
          if (choice.type === 'block') {
            const legal = legalTargets(f, 'defender', owner).map(d => d.id);
            assert(choice.targetSuccessIds.length >= 1);
            assert(choice.targetSuccessIds.length <= capacity);
            assert.equal(new Set(choice.targetSuccessIds).size,
                         choice.targetSuccessIds.length);
            assert(choice.targetSuccessIds.every(id => legal.includes(id)),
                   'AI proposed illegal Block against ' + playerDice);
            assert(block(f, 'defender', choice.successId, choice.targetSuccessIds));
          } else {
            assert.equal(choice.type, 'strike');
            assert(strike(f, 'defender', choice.successId));
          }
          const unavoidableLethalCritical =
            playerDice.includes('critical') && 6 >= npoWounds &&
            npoDice.every(kind => kind === 'normal');
          if (unavoidableLethalCritical) {
            assert.equal(choice.type, 'strike',
              'NPO must not Block a harmless normal while a lethal crit remains');
          }
        }
      }
    }
  }
}
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True,
        text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_solo_fight_uses_one_npo_decision_engine_in_both_modes():
    render_start = APP.index("  function renderFightResolution(")
    render_end = APP.index("\n  function ", render_start + 12)
    render = APP[render_start:render_end]
    assert "if(!human){const choice=soloNpoFightDecision(fight,role)" in render
    assert render.index("soloNpoFightDecision(fight,role)") < render.index(
        "if(document.documentElement.dataset.ui==='tomb')"
    )
    assert APP.count("function soloNpoFightDecision(") == 1
