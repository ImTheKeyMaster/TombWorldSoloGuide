"""Use native HTML images for Death Korps portraits across activation and combat."""

import re
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_native_portrait_markup_for_trooper_activation_gunner_fight_and_roster():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
function section(start,end){
 const i=app.indexOf(start),j=app.indexOf(end,i+start.length);
 assert(i>0&&j>i,'Missing source: '+start);
 return app.slice(i,j);
}
const helpers=section('  const DEATH_KORPS_PORTRAIT_ROOT=','  function usesPlayerPortraitRail(');
const combat=section('  function deathKorpsCombatPortraitSvg(','  // Shared shooting dice cards');
const activation=section('  function renderHumanPlayerActionPicker(','  function playerSequentialStage(');
const portraits=section('  function fightParticipantPortrait(','  function fightWeaponRulesHtml(');
const escapeHtml=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
let team='Death Korps',activationCaptured=null;
const ctx={
 escapeHtml,
 selectedPlayerTeamName:()=>team,
 deathwatchPortraitSvg:()=>'<svg data-team="deathwatch"></svg>',
 deathwatchPortraitImage:()=> '',
 document:{documentElement:{dataset:{ui:'tomb',experimental:'off'}}},
 activePlayerActivation:()=>({operativeId:'trooper-3',remainingAp:1,baseApl:2,effectiveApl:2,startingAp:2,resolvedActions:[]}),
 playerDefinition:id=>({id,wounds:7,weapons:[{name:'Lasgun'},{name:'Bayonet'}]}),
 playerActivationOperativeEliminated:()=>false,
 state:{npoRuleState:{aplModifiers:[]},eventState:{playerAplModifiers:[]},playerOperativeStates:{},roster:[]},
 playerName:()=> 'Trooper 3',
 playerCurrentWounds:()=>7,
 playerHumanActionCatalog:()=>[],
 playerHumanActionState:()=>({}),
 selectHumanPlayerAction:()=>{},
 confirmEndHumanPlayerActivation:()=>{},
 renderHumanActivationShell:params=>{activationCaptured=params;},
 renderOperativeStatusPanel:()=>{},
 unawakenedScoutRooms:()=>[],
 fightDiePresentation:die=>({...die,retained:true,kind:'hit'}),
 fightRollSummary:()=>'<strong>1 Normal Success</strong>',
 fightParticipantPortrait:null,
 experimentalNecronPortraitSvg:()=>'<svg data-team="necron"></svg>',
 attackRuleAppliedHtml:()=>'',severeAppliedHtml:()=>'',dieHtml:()=>'<i>die</i>',
 titleCaseRuleId:s=>s,showPlayerActivation:()=>{},
 completeHumanPlayerActivation:()=>{},
 selectedPlayerTeamName:null
};
ctx.selectedPlayerTeamName=()=>team;
const api=new Function('ctx','with(ctx){'+helpers+combat+activation+portraits+
 '\nreturn {deathKorpsPortraitImage,deathKorpsPortraitPhoto,playerRosterPortraitMarkup,'+
 'deathKorpsCombatPortraitSvg,renderHumanPlayerActionPicker,fightParticipantPortrait,fightRollParticipantHtml};}')(ctx);
for(const enabled of ['off','on']){
 ctx.document.documentElement.dataset.experimental=enabled;
 api.renderHumanPlayerActionPicker();
 const photo=activationCaptured.portraitMarkup;
 assert.match(photo,/^<img class="experimental-activation-portrait-svg death-korps-portrait-photo"/);
 assert.match(photo,/src="Assets\/Images\/TombUI\/DeathKorps\/Death_Korps_trooper_3.png"/);
 assert.match(photo,/width="384" height="384"/);
 assert.match(photo,/decoding="async"/);
 assert.match(photo,/alt=""/);
 assert.doesNotMatch(photo,/<svg|<image href/);
 assert.match(api.playerRosterPortraitMarkup('trooper-3','player-roster-svg'),
   /<img class="player-roster-svg death-korps-portrait-photo"/);
 assert.match(api.deathKorpsCombatPortraitSvg('gunner-plasma-gun','fight-portrait-artwork'),
   /<img class="fight-portrait-artwork death-korps-portrait-photo".*Death_Korps_gunner_plasma.png/);
 const gunner={side:'player',id:'gunner-plasma-gun',label:'Gunner 2 (Plasma Gun)',
   profile:{name:'Bayonet',dice:3,hit:4,normal:2,crit:3},attackDice:[{value:5}]};
 const fight=api.fightRollParticipantHtml({attacker:gunner},'attacker',false);
 assert.match(fight,/class="combat-stage fight-roll-pool has-fight-portrait"/);
 assert.match(fight,/img class="fight-portrait-artwork death-korps-portrait-photo"/);
 assert.match(fight,/Death_Korps_gunner_plasma.png/);
 assert.match(fight,/class="dice-row settled"/);
 assert.doesNotMatch(fight,/<image href/);
}
assert.equal(api.deathKorpsPortraitPhoto('unknown'),'');

// Deathwatch still keeps the supplied SVG artwork; no fabricated portrait.
team='Deathwatch';
assert.match(api.playerRosterPortraitMarkup('trooper-3'),/data-team="deathwatch"/);
team='Kasrkin';
assert.equal(api.fightParticipantPortrait({side:'player',id:'gunner-plasma-gun'},'attacker'),'');
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,
                          capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_activation_mask_and_framing_remain_and_native_image_scoped_to_korps():
    assert "img.death-korps-portrait-photo" in CSS
    assert ':has(image[href*="Death_Korps_"])' not in CSS
    prefix='html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>'
    selector=prefix+'.experimental-activation-portrait:has(img.death-korps-portrait-photo) .experimental-activation-portrait-svg'
    rules=re.findall(re.escape(selector)+r"\s*\{([^}]*)\}",CSS)
    assert len(rules)==3
    assert "width:150%" in rules[0]
    assert "width:157%" in rules[1]
    assert "width:160%" in rules[2]
    assert "mask-image:linear-gradient" in CSS
    assert "clip-path:inset(-96px -96px -64px -220px)" in CSS
    assert "img.death-korps-portrait-photo{object-fit:contain;object-position:center top;}" in CSS
    assert "experimental-activation-portrait-svg" in APP
    assert "deathwatchPortraitSvg" in APP
    assert "experimentalNecronPortraitSvg" in APP


def test_version_and_state_stability():
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function refreshSvgPortraitsAfterResume(" in APP
