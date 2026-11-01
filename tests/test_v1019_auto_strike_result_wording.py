"""Regression: a fully automatic Fight Result must not imply a player choice."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auto_strike_summary_uses_choice_aware_wording():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const first=source.indexOf('  function experimentalFightAutomaticStrikeResultHtml(');
const last=source.indexOf('  function renderFightResult(',first);
assert(first>=0 && last>first);
const ctx={
  isPvpMode:()=>false,
  document:{documentElement:{dataset:{ui:'tomb'}}},
  escapeHtml:String,
  titleCaseRuleId:s=>s.charAt(0).toUpperCase()+s.slice(1)
};
const render=new Function('ctx','with(ctx){'+source.slice(first,last)+'return experimentalFightAutomaticStrikeResultHtml;}')(ctx);
const base={
  attackerName:'Bombard',
  defenderName:'Canoptek Macrocyte Warrior 3',
  fightHistory:[
    {type:'strike',role:'attacker',successKind:'normal',damage:3,before:7,after:4,automatic:true},
    {type:'strike',role:'attacker',successKind:'normal',damage:3,before:4,after:1,automatic:true}
  ]
};
const allAuto=render(base);
assert(allAuto.includes('automatically resolved 2 Strikes.'));
assert(!allAuto.includes('after your choice'));
assert(!allAuto.includes('additional 2'));
assert.equal((allAuto.match(/AUTO · Bombard · Normal Strike/g)||[]).length,2);
const mixed=render({...base,fightHistory:[
  {type:'strike',role:'attacker',successKind:'critical',damage:4,before:11,after:7},
  ...base.fightHistory
]});
assert(mixed.includes('automatically resolved 2 additional Strikes after your choice.'));
assert(mixed.includes('CHOSEN · Bombard · Critical Strike'));
assert.equal((mixed.match(/AUTO · Bombard · Normal Strike/g)||[]).length,2);
const single=render({...base,fightHistory:base.fightHistory.slice(0,1)});
assert(single.includes('automatically resolved 1 Strike.'));
assert(!single.includes('after your choice'));
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
