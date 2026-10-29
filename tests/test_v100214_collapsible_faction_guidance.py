"""v10.0.214: Rules and gambits use collapsed, accessible disclosures."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_collapsed_rules_gambits_and_nested_forward_scouting():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function factionGuidanceHtml(');
const end=source.indexOf('  function playerDisplayIdentity(',start);
assert(start>0&&end>start);
const ctx={
  state:{turningPoint:1},
  escapeHtml:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;'),
  playerTeamData:{factionRules:[
    {name:'Veteran Astartes',timing:'During activation',text:'Repeat shoots or fights.'},
    {name:'Special Issue Ammunition',text:'Pick an effect when shooting.'}
  ],strategicGambits:[{name:'Tactical Gambit',text:'Do a strategic action.',turningPoints:[1]}]}
};
const render=new Function('ctx','with(ctx){'+source.slice(start,end)+'return factionGuidanceHtml;}')(ctx);
const count=(html,re)=>(html.match(re)||[]).length;
let html=render();
assert(html.includes('<h3>Faction Rules Guidance</h3>'));
assert.equal(count(html,/<details class="mission-rule faction-rule-disclosure">/g),2);
assert.equal(count(html,/<summary><strong>/g),2);
assert(!html.includes('<details class="mission-rule faction-rule-disclosure" open'));
assert(!html.includes('<details class="mission-rule faction-rule-disclosure" open>'));
assert(html.includes('<summary><strong>Veteran Astartes</strong></summary>'));
assert(html.includes('<summary><strong>Special Issue Ammunition</strong></summary>'));
assert(html.includes('<small>During activation</small><p>Repeat shoots or fights.</p>'));
assert(html.includes('<p>Pick an effect when shooting.</p>'));
html=render('gambits');
assert(html.includes('<h3>Faction Strategic Gambits</h3>'));
assert.equal(count(html,/<details class="mission-rule faction-rule-disclosure">/g),1);
assert(html.includes('<summary><strong>Tactical Gambit</strong></summary>'));
assert(html.includes('Do a strategic action.'));
ctx.state.turningPoint=2;
assert.equal(render('gambits'),'','Turning-point filtering is unchanged');
ctx.playerTeamData={
  factionRules:[
    {name:'Forward Scouting',timing:'End of setup',text:'Select options.',forwardScoutingParent:true},
    {name:'Redeploy',text:'Move unit.',forwardScoutingOption:true,forwardScoutingOrder:1,selectionLimit:1},
    {name:'Reposition',text:'Set new position.',forwardScoutingOption:true,forwardScoutingOrder:2,selectionLimit:2}
  ],
  strategicGambits:[{name:'Diversion',text:'Distract enemy.',forwardScoutingOption:true,forwardScoutingOrder:3,selectionLimit:1}]
};
html=render();
assert.equal(count(html,/<details class="mission-rule forward-scouting-rule faction-rule-disclosure">/g),1);
assert.equal(count(html,/<details class="forward-scouting-disclosure">/g),1);
assert(html.includes('<summary><strong>Forward Scouting</strong></summary>'));
assert(html.includes('View 3 scouting options'));
assert(html.includes('Hide 3 scouting options'));
assert(html.indexOf('Redeploy')<html.indexOf('Reposition'));
assert(html.indexOf('Reposition')<html.indexOf('Diversion'));
assert.equal(count(html,/class="forward-scouting-option"/g),3);
assert(!html.includes('class="mission-rule forward-scouting-rule faction-rule-disclosure" open'));
assert(!html.includes('class="forward-scouting-disclosure" open'));
assert(!html.includes('<summary><strong>Redeploy</strong></summary>'),'Sub-options remain nested, not duplicated');
"""
    p=subprocess.run(["node","-e",script],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert p.returncode == 0, p.stderr or p.stdout


def test_styles_and_touch_targets_are_scoped():
    block=CSS.split("/* v10.0.214: Faction rules and strategic gambits",1)[1]
    assert '.faction-guidance .faction-rule-disclosure > summary{' in block
    assert 'min-height:48px;' in block
    assert 'cursor:pointer;' in block
    assert 'summary:focus-visible' in block
    assert '.faction-rule-disclosure[open] > summary::after' in block
    assert 'prefers-reduced-motion:reduce' in block
    assert '.mission-rule summary' not in block, 'Other mission briefings remain unaffected'
    assert '.forward-scouting-disclosure summary' in CSS


def test_pwa_version_and_game_storage_unchanged():
    assert tuple(map(int,CURRENT_APP_VERSION.split('.'))) >= (10,0,214)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT/"service-worker.js").read_text()
    html=(ROOT/"index.html").read_text()
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    check=subprocess.run(["node","--check","app.js"],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert check.returncode == 0,check.stderr
