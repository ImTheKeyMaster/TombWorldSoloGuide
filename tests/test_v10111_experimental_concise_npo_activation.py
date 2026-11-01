"""Regression checks for Experimental-only concise NPO Activation."""
import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_question_mode_isolation_and_rules_disclosure():
    script = r"""
const assert=require('node:assert/strict');
const source=require('node:fs').readFileSync('app.js','utf8');
const i=source.indexOf('  function useConciseExperimentalNpoGuide(');
const j=source.indexOf('  function renderNpoActionProgress(',i);
let enabled=false,pvp=false,ui='tomb';
const ctx={experimentalFeaturesEnabled:()=>enabled,isPvpMode:()=>pvp,
 document:{documentElement:{dataset:{get ui(){return ui;}}}},
 npoActionId:s=>(s||'').toLowerCase().replaceAll(' ','-'),
 conciseNpoActionName:action=>action.name,escapeHtml:String};
const render=new Function('ctx','with(ctx){'+source.slice(i,j)+
 'return {renderActiveNpoQuestion,renderCompletedNpoQuestions,conciseNpoQuestionTitle};}')(ctx);
const q={action:'Shoot',actionId:'shoot',type:'feasibility',
 title:'Does this NPO currently have a Player operative it can Shoot without moving?',
 help:'Select Yes only if it can Shoot now. Do not move yet.'};
const prior=[{action:'Fight',question:'Fight?',type:'feasibility',answer:false},
 {action:'Shoot',question:'Shoot?',type:'feasibility',answer:true}];
const old=render.renderActiveNpoQuestion(q);
assert(old.includes(q.title)&&old.includes(q.help));
assert(!old.includes('npo-concise-question'));
assert(render.renderCompletedNpoQuestions(prior).includes('npo-question-complete'));
enabled=true;
const short=render.renderActiveNpoQuestion(q);
assert(short.includes('Valid shooting target?')&&short.includes('Can Shoot'));
assert(short.includes('No target')&&short.includes('<details'));
assert(short.includes(q.title)&&short.includes(q.help));
assert(short.includes('data-answer="no"')&&short.includes('data-answer="yes"'));
const history=render.renderCompletedNpoQuestions(prior);
assert(history.includes('npo-compact-history-chip')&&history.includes('Fight: No'));
assert(history.includes('Shoot: Yes'));
assert.equal(render.conciseNpoQuestionTitle({actionId:'fall-back',type:'applicability'}),
 'In enemy control range?');
assert.equal(render.conciseNpoQuestionTitle({actionId:'reposition',
 title:'Reposition up to 7 inches and then Shoot?',
 movementIntent:{purpose:'enable-shoot'}}),'Can Reposition 7″ to Shoot?');
pvp=true;
assert.equal(render.renderActiveNpoQuestion(q),old);
pvp=false;ui='classic';
assert.equal(render.renderActiveNpoQuestion(q),old);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True,
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_movement_and_target_rules_remain_accessible():
    movement = APP.split("function renderNpoMovementConfirmation(", 1)[1].split(
        "function resolveNpoAction(", 1)[0]
    assert "if(useConciseExperimentalNpoGuide())" in movement
    assert "npo-concise-movement" in movement
    assert "npo-compact-ap-cost" in movement
    assert "Movement rules" in movement
    assert "Movement Complete" in movement
    assert "Confirm " in movement
    assert "id=" in movement
    assert "renderNpoGuideFooter()" in movement
    assert "escapeHtml(decision.reason)" in movement
    target = APP.split("function renderNpoDecisionResult(", 1)[1].split(
        "async function completeNpoActivation(", 1)[0]
    assert "const condensedTargetGuide=useConciseExperimentalNpoGuide()" in target
    assert "npo-target-priority-details" in target
    assert "Select the highest-priority eligible target." in target
    assert "priorityMarkup" in target
    assert "decision.reason" in target


def test_experimental_styles_and_pwa_versions():
    assert "npo-concise-header" in APP
    assert "npo-compact-history" in APP
    assert "npo-concise-question" in APP
    assert 'html[data-ui="tomb"] .npo-concise-question' in CSS
    assert 'html[data-ui="tomb"] .npo-target-priority-details' in CSS
    assert CURRENT_APP_VERSION == "10.1.11"
    assert CURRENT_APP_VERSION in APP
    assert CURRENT_APP_VERSION in SW
    assert "V" + CURRENT_APP_VERSION in HTML
