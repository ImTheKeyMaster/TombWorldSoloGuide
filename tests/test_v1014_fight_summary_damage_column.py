"""v10.1.4 Fight Result: clearly label numbers as DAMAGE DEALT."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_result_summary_column_labels_match_outgoing_damage_not_wounds_received():
    script = r"""
const assert = require('node:assert/strict'), fs = require('node:fs');
const s = fs.readFileSync('app.js', 'utf8');
const start = s.indexOf('  function compactFightResultSummaryHtml(');
const end = s.indexOf('  function renderFightResult(', start);
assert(start > 0 && end > start);
const helper = new Function('ctx','with(ctx){'+s.slice(start,end)+'return compactFightResultSummaryHtml;}')({
  escapeHtml:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
});
const result={
  participants:{
    attacker:{name:'Gunner',damageDealt:6},
    defender:{name:'Canoptek Macrocyte Warrior 2',damageDealt:0}
  },
  explanation:[
    'Canoptek Macrocyte Warrior 2 retained no successes.',
    'Gunner dealt 6 total Strike damage.'
  ]
};
const out=helper(result);
assert.match(out, /<div class="fight-result-summary-header"><h3>SUMMARY<\/h3><span>DAMAGE DEALT<\/span><\/div>/);
assert(out.includes('Gunner</span><strong>6</strong>'));
assert(out.includes('Canoptek Macrocyte Warrior 2</span><strong>0</strong>'));
assert(!out.includes('6 damage') && !out.includes('0 damage'), 'Damage units belong to the column heading');
assert(out.includes('Canoptek Macrocyte Warrior 2 retained no successes.'));
assert(!out.includes('Gunner dealt 6 total Strike damage.'), 'Do not duplicate damage totals');
assert.equal((out.match(/class="fight-result-summary-row"/g)||[]).length,2);
const escaped=helper({
  participants:{attacker:{name:'R&D <Aegis>',damageDealt:1},defender:{name:'Necron',damageDealt:2}},
  explanation:[]
});
assert(escaped.includes('R&amp;D &lt;Aegis&gt;'));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_tomb_scoping_and_original_classic_fight_summary():
    section=CSS.split("/* v10.1.4: Explicit scorecard column", 1)[1]
    assert 'html[data-ui="tomb"] .fight-result-summary-header{' in section
    assert "display:flex;" in section
    assert "justify-content:space-between;" in section
    assert "text-align:right;" in section
    assert "white-space:nowrap;" in section
    assert "font-variant-numeric:tabular-nums;" in section
    assert "overflow-wrap:anywhere;" in CSS
    render=APP.split("  function renderFightResult(fight){",1)[1].split("  function finishFight(fight){",1)[0]
    assert "document.documentElement.dataset.ui==='tomb'?'':'<h3>SUMMARY</h3>'" in render
    assert "document.documentElement.dataset.ui==='tomb'?compactFightResultSummaryHtml(result)" in render
    assert "experimentalFightAutomaticStrikeResultHtml(result)" in render
    assert "fightResultParticipantHtml(result.participants.attacker,'attacker')" in render
    assert "fightResultParticipantHtml(result.participants.defender,'defender')" in render


def test_release_version_is_consistent():
    assert CURRENT_APP_VERSION=="10.1.4"
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    assert "const APP_VERSION = '10.1.4';" in APP
    assert "const APP_VERSION = '10.1.4';" in worker
    assert "app.js?v=10.1.4" in index
    assert "styles.css?v=10.1.4" in index
    assert "V10.1.4" in index
