"""v10.0.198: Deathwatch and Spectre stateful regression tests."""
import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")

def node(source):
    completed = subprocess.run(["node", "-e", source], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr or completed.stdout

def test_deathwatch_either_double_shoot_or_double_fight_and_surcharge():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function isDeathwatchPlayerTeam()'),b=s.indexOf('  function playerHumanActionCatalog(',a);
const api=new Function('ctx','with(ctx){'+s.slice(a,b)+'return {playerMayRepeatAction,deathwatchSecondShootExtraCost};}')({selectedPlayerTeamName:()=> 'Deathwatch'});
const done=(...ids)=>({resolvedActions:ids.map(id=>({id,attackSummaries:[]}))});
assert(api.playerMayRepeatAction(done('shoot'),'shoot'));
assert(!api.playerMayRepeatAction(done('shoot','melee','melee'),'shoot'));
assert(!api.playerMayRepeatAction(done('shoot','shoot','melee'),'melee'));
const prior=name=>({resolvedActions:[{id:'shoot',attackSummaries:[{weaponName:name}]}]});
assert.equal(api.deathwatchSecondShootExtraCost(prior('Stalker bolt rifle (heavy)'),'Frag cannon (shell)'),1);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Bolt pistol'),'Frag cannon (shell)'),0);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Frag cannon (shell)'),'Bolt pistol'),0);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Bolt pistol'),'Melta bomb'),1);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Melta bomb'),'Bolt pistol'),1);
assert.equal(api.deathwatchSecondShootExtraCost(prior(''),'Frag cannon (shell)'),0);
""")

def test_ammunition_profile_survives_result_recording():
    assert "profile:{...profile},before," in APP
    assert "profile:{...profile,rules:weapon.rules||[]},before," not in APP
    assert "profile.rules.includes(rule)?profile.rules:[...profile.rules,rule]" in APP
    assert "locked?.profile||playerWeaponProfile" in APP

def test_spectre_specialist_action_catalog_and_accounting():
    for token in ("id:'issueMission',name:'Issue Mission',group:'operative',cost:0",
                  "id:'medikit',name:'Medikit',group:'operative',cost:0",
                  "id:'loadWeapon',name:'Load Weapon',group:'operative',cost:1",
                  "['charge','dash','shoot'].some(id=>completed.has(id))",
                  "completed.has('loadWeapon')&&['charge','dash','shoot'].includes(action.id)",
                  "record.issuedOperativeIds.push(targetId)", "state.playerWounds[targetId]=restored"):
        assert token in APP
    assert "Recipient did not benefit from Medic! this turning point" in APP

def test_spectre_fieldcraft_once_per_npo_activation_and_ready_issued():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function spectreFieldcraftCandidates()'),b=s.indexOf('  function continueSoloNpoActivation()',a);
assert(a>0&&b>a);
const record={points:1,usedOperativeIds:[],issuedOperativeIds:[],interruptedEnemyActivationIds:[],coolHeadedUsed:false};
const ctx={isSpectrePlayerTeam:()=>true,isPvpMode:()=>false,spectreFieldcraftRecord:()=>record,inPlayLivingPlayerOperativeIds:()=>['ready','expended','trooper-1-lasrifle','vox-relay-beacon'],state:{playerActivatedIds:['expended']}};
const api=new Function('ctx','with(ctx){'+s.slice(a,b)+'return {spectreFieldcraftCandidates,spectreMayInterruptNpo};}')(ctx);
const enemy={order:'Engage',wounds:6},act={side:'npo',activationId:'a',committed:false,awaitingActionResult:{id:'shoot'}};
assert.deepEqual(api.spectreFieldcraftCandidates(),['ready','trooper-1-lasrifle']);
record.issuedOperativeIds.push('expended');
assert.deepEqual(api.spectreFieldcraftCandidates(),['ready','expended','trooper-1-lasrifle']);
assert(api.spectreMayInterruptNpo(enemy,act));
record.interruptedEnemyActivationIds.push('a');
assert(!api.spectreMayInterruptNpo(enemy,act));
record.interruptedEnemyActivationIds.length=0;record.points=0;
assert(api.spectreMayInterruptNpo(enemy,act));
record.coolHeadedUsed=true;
assert(!api.spectreMayInterruptNpo(enemy,act));
assert(!api.spectreMayInterruptNpo({...enemy,order:'Conceal'},act));
""")
    assert "if(transitionMode===NPO_ACTION_TRANSITIONS.ACKNOWLEDGE||offerFieldcraft)" in APP
    assert "record.usedOperativeIds.push(id)" in APP
    assert "activation.awaitingActionResult={...record,endsActivation}" in APP
    assert "state.lastActivation?.side==='npo'&&!state.lastActivation.committed&&state.lastActivation.awaitingActionResult" in APP

def test_zero_ap_scout_terrain_and_reposition_tracking():
    assert "const freeScoutHatch=action.id==='hatch'&&spectreGuideScoutingAvailable()" in APP
    assert "if(action.cost>remaining&&!freeScoutHatch)" in APP
    assert "const zeroCostAction=playerHumanActionCatalog(activation).some(action=>" in APP
    assert "const furtherFreeActions=playerHumanActionCatalog(activation).some(action=>" in APP
    assert "if(activation.remainingAp<1)$('#regularScoutHatch').disabled=true" in APP
    assert "const repositionAlreadyUsed=(record.repositionUsedIds||[]).includes(actor.value)" in APP
    assert "item.side==='player'&&item.label===playerName(actor.value)" in APP

def test_version():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 198)
    assert f"V{CURRENT_APP_VERSION}" in (ROOT / 'index.html').read_text(encoding='utf-8')
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / 'service-worker.js').read_text(encoding='utf-8')
