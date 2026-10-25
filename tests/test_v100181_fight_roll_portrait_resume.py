"""Retained Fight Roll portraits and iOS restoration do not touch gameplay state."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def test_death_korps_plasma_gunner_fight_uses_native_image_not_external_svg():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
function section(start,end){
 const i=source.indexOf(start),j=source.indexOf(end,i+start.length);
 assert(i>0&&j>i,'Missing code '+start);
 return source.slice(i,j);
}
const portraitCode=section('  function fightParticipantPortrait(','  function fightWeaponRulesHtml(');
const context={
 state:{roster:[]},
 selectedPlayerTeamName:()=> 'Death Korps',
 playerDefinition:id=>id==='gunner-plasma-gun'?{id}:null,
 deathKorpsCombatPortraitSvg:(id,cls)=>
  '<img class="'+cls+' death-korps-portrait-photo" src="Assets/Images/TombUI/DeathKorps/Death_Korps_gunner_plasma.png">',
 deathwatchPortraitImage:()=>'',deathwatchPortraitSvg:()=>'',experimentalNecronPortraitSvg:()=> '',
 escapeHtml:text=>String(text),
 fightDiePresentation:d=>({value:d.value,retained:true,kind:'hit'}),
 fightRollSummary:()=>'<strong>1 Normal Success</strong>',
 attackRuleAppliedHtml:()=>'',severeAppliedHtml:()=>'',dieHtml:()=>'<i>die</i>'
};
const api=new Function('ctx','with(ctx){'+portraitCode+
 '\nreturn {fightParticipantPortrait,fightRollParticipantHtml};}')(context);
const gunner={side:'player',id:'gunner-plasma-gun',label:'Gunner 2 (Plasma Gun)',
 profile:{name:'Bayonet',dice:3,hit:4,normal:2,crit:3},attackDice:[{value:5}]};
const html=api.fightRollParticipantHtml({attacker:gunner},'attacker',false);
assert.match(html,/Gunner 2 \(Plasma Gun\)/);
assert.match(html,/class="combat-stage fight-roll-pool has-fight-portrait"/);
assert.match(html,/img class="fight-portrait-artwork death-korps-portrait-photo"/);
assert.match(html,/src="Assets\/Images\/TombUI\/DeathKorps\/Death_Korps_gunner_plasma.png"/);
assert.doesNotMatch(html,/<svg|<image href/);
assert.match(html,/class="dice-row settled"/);
assert.match(html,/1 Normal Success/);
context.selectedPlayerTeamName=()=> 'Kasrkin';
const absent=api.fightParticipantPortrait(gunner,'attacker');
assert.equal(absent,'','Kasrkin has no dedicated Fight miniature portraits in this release');
"""
    run=subprocess.run(["node","-e",script],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert run.returncode==0,run.stderr or run.stdout


def test_two_phase_restore_keeps_state_and_saved_combat_untouched():
    start=APP.index("  // iOS standalone PWAs can restore the DOM")
    end=APP.index("  function normalizeSarcophagusControllers(",start)
    code=APP[start:end]
    assert "document.querySelectorAll('svg image[href]')" in code
    assert "root.replaceWith(root.cloneNode(true))" in code
    assert "image.replaceWith(image.cloneNode(true))" in code
    assert "const replacedRoots=new Set()" in code
    assert "1500" in code
    assert "window.addEventListener('pagehide',cancelSvgPortraitRefresh)" in code
    for forbidden in ["save()","showModal(","state.fightState","state.combatState","renderFightRoll(","document.body.innerHTML","location.reload","scrollTo(","replaceState("]:
        assert forbidden not in code,forbidden


def test_versioned_release_shell():
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
