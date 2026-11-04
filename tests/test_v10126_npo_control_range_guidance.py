"""Regression for the shared solo NPO control-range (1 inch) prompt and rules."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_fall_back_control_range_guidance_explains_bases_visibility_and_mutuality():
    inquiry = APP.split("'fall-back':{", 1)[1].split("\n    },", 1)[0]
    help_text = re.search(r"applicabilityHelp:'([^']+)'", inquiry)
    assert help_text, "Fall Back applicability guidance missing"
    guidance = help_text.group(1)
    assert "1″" in guidance
    assert "nearest points of the models’ bases" in guidance
    assert "at least one operative can see the other" in guidance
    assert "in each other’s control range" in guidance
    assert "Select In range" in guidance
    assert "Do not move the NPO yet" in guidance


def test_compact_question_renders_one_inch_without_changing_other_actions():
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync('app.js','utf8');
const i = source.indexOf('  function useConciseNpoGuide(){');
const j = source.indexOf('  function renderNpoActionProgress(', i);
assert(i !== -1 && j > i);
const ctx = {
  isPvpMode:()=>false,
  document:{documentElement:{dataset:{ui:'tomb'}}},
  npoActionId: action => String(action).toLowerCase(),
  escapeHtml: text => String(text).replaceAll('&','&amp;').replaceAll('<','&lt;')
};
const ui = new Function('ctx','with(ctx){'+source.slice(i,j)+
  'return {renderActiveNpoQuestion,conciseNpoQuestionTitle};}')(ctx);
const q = {action:'Fall Back',actionId:'fall-back',type:'applicability',
 title:'Is this NPO within the control range of any Player operative?',
 help:'Measure between the nearest points of the models’ bases. They are in each other’s control range when within 1″ and at least one operative can see the other. Select In range only when both conditions are met. Do not move the NPO yet.'};
const rendered=ui.renderActiveNpoQuestion(q);
assert.equal(ui.conciseNpoQuestionTitle(q),'In enemy control range (1″)?');
assert(rendered.includes('In enemy control range (1″)?'));
assert(rendered.includes('Rules &amp; guidance'));
assert(rendered.includes('at least one operative can see the other'));
assert(rendered.includes('Out of range')&&rendered.includes('In range'));
assert.equal(ui.conciseNpoQuestionTitle({...q,type:'feasibility'}),'Can Fall Back safely?');
assert.equal(ui.conciseNpoQuestionTitle({...q,actionId:'fight'}),'Enemy in control range?');
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, timeout=20
    )
    assert result.returncode == 0, result.stderr or result.stdout
