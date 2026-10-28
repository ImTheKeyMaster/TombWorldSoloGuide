"""October 28 Deathwatch/Spectre: Joint Ops precedence and legal action economy."""

import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
DW = json.loads((ROOT / "Player_Operatives/DeathWatch.json").read_text(encoding="utf-8"))
SP = json.loads((ROOT / "Player_Operatives/SpectreSquad.json").read_text(encoding="utf-8"))


def node(source):
    result = subprocess.run(["node", "-e", source], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_deathwatch_roster_and_source():
    assert DW["selectionRules"]["maxGravis"] == 1
    assert next(c for c in DW["rosterCategories"] if c["id"] == "gravis").get("requiredCount", 0) == 0
    assert DW["source"]["revision"] == "28 October 2026"
    assert set(r["id"] for r in DW["factionRules"]) == {"veteran-astartes", "special-issue-ammunition"}
    assert len(DW["operatives"]) == 11


def test_deathwatch_repeat_shoot_and_weapon_extra_ap_rules():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  function isDeathwatchPlayerTeam()');
const b=source.indexOf('  function playerHumanActionCatalog(',a);
assert(a>0&&b>a);
let team='Deathwatch';
const api=new Function('ctx','with(ctx){'+source.slice(a,b)+'return {playerActionUses,playerMayRepeatAction,deathwatchSecondShootExtraCost};}')({selectedPlayerTeamName:()=>team});
const empty={resolvedActions:[]};
const prior=weaponName=>({resolvedActions:[{id:'shoot',attackSummaries:[{weaponName}]}]});
assert.equal(api.deathwatchSecondShootExtraCost(empty,'Plasma pistol (standard)'),0);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Plasma pistol (standard)'),'Plasma pistol (supercharge)'),1);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Bolt pistol'),'Heavy plasma incinerator'),0);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Bolt pistol'),'Melta bomb'),1);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Melta bomb'),'Bolt pistol'),1);
assert.equal(api.playerMayRepeatAction(prior('Bolt pistol'),'shoot'),true);
assert.equal(api.playerMayRepeatAction({resolvedActions:[{id:'shoot'},{id:'shoot'}]},'shoot'),false);
assert.equal(api.playerMayRepeatAction({resolvedActions:[{id:'melee'}]},'melee'),true);
assert.equal(api.playerMayRepeatAction({resolvedActions:[{id:'melee'},{id:'melee'}]},'melee'),false);
assert.equal(api.playerMayRepeatAction(prior('Bolt pistol'),'move'),false);
team='Spectre Squad';
assert.equal(api.playerMayRepeatAction(prior('Bolt pistol'),'shoot'),false);
assert.equal(api.deathwatchSecondShootExtraCost(prior('Melta bomb'),'Bolt pistol'),0);
"""
    node(script)
    assert "if(completed.has(action.id)&&!playerMayRepeatAction(activation,action.id))" in APP
    assert "if((activation.completedActionIds||[]).includes(pending.actionId)&&!playerMayRepeatAction" in APP
    assert "pending.cost=required;stage.humanActionCost=required;save();" in APP
    assert "weaponName:item.weaponName||''" in APP


def test_deathwatch_special_ammunition_applies_to_profile_not_just_guidance():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  const DEATHWATCH_SPECIAL_AMMO=');
const b=source.indexOf('  const combatAbilityHandlers',a);
assert(a>0&&b>a);
const state={eventState:{transactions:{}},turningPoint:2};
const ctx={
 state,selectedPlayerTeamName:()=> 'Deathwatch',
 isDeathwatchPlayerTeam:()=>true,
 parseWeaponDamage:()=>({normal:2,crit:3}),
 canonicalPlayerWeaponIdentity:()=>({weaponId:'x',profileId:'x:default'}),
 weaponPiercingValue:()=>0
};
const api=new Function('ctx','with(ctx){'+source.slice(a,b)+'return {deathwatchAmmoTransaction,deathwatchAmmoLegal,playerWeaponProfile};}')(ctx);
let gun={name:'Gauss lookalike',type:'ranged',attacks:4,hit:3,damage:'2/3',rules:[]};
let option={operativeId:'sergeant',attackType:'shoot',weaponIndex:0,stage:{deathwatchAmmoRule:'Lethal 5+'}};
assert.equal(api.playerWeaponProfile(gun,option).critThreshold,5);
assert(api.playerWeaponProfile(gun,option).rules.includes('Lethal 5+'));
option.stage.deathwatchAmmoRule='Blast 1"';
assert(api.playerWeaponProfile(gun,option).rules.includes('Blast 1"'));
assert.equal(api.deathwatchAmmoLegal({...gun,rules:['Torrent 2"']},'Blast 1"'),false);
assert.equal(api.deathwatchAmmoLegal({...gun,name:'Melta bomb'},'Severe'),false);
api.deathwatchAmmoTransaction().used=true;
assert(!api.playerWeaponProfile(gun,option).rules.includes('Blast 1"'));
state.turningPoint=3;
assert(api.playerWeaponProfile(gun,option).rules.includes('Blast 1"'));
"""
    node(script)
    assert "deathwatchAmmoTransaction().used=true" in APP
    assert "if(attackType==='shoot'&&targetSide==='player'&&isDeathwatchPlayerTeam()&&target.id==='aegis')" in APP
    assert "profile={...profile,ap:reduced,rules}" in APP
    assert "stage.deathwatchAmmoRule=ammunition.value" in APP
    assert "deathwatchAmmoLegal(weapon,option.value)" in APP


def test_spectre_signal_restrictions_and_apl_persistence():
    assert SP["source"]["revision"] == "28 October 2026"
    beacon=next(o for o in SP["operatives"] if o["id"]=="vox-relay-beacon")
    assert beacon["apl"]==1 and beacon["move"]==0
    assert "within 6" in next(a["text"] for a in beacon["abilities"] if a["id"]=="signal")
    for operative in (o for o in SP["operatives"] if o["id"].startswith("vox-operator-")):
        text=next(a["text"] for a in operative["abilities"] if a["id"]=="signal")
        assert "visible" in text and "within 6" not in text
    assert all("turningPoints" not in entry for entry in SP["strategicGambits"])
    assert "operative.id==='vox-relay-beacon')return [{id:'signal'" in APP
    assert "operative.id.startsWith('vox-operator-'))actions.push({id:'signal'" in APP
    assert "state.eventState.playerAplModifiers.push({id:effectId" in APP
    assert "expires:'end-of-target-next-activation'" in APP
    assert "activation.pendingAction=null" in APP
    assert "No eligible teammate" in APP


def test_scout_terrain_hatch_discount_with_manual_tabletop_check():
    assert "function spectreGuideScoutingAvailable()" in APP
    assert "isSpectrePlayerTeam()&&(state.playerRoster||[]).some(id=>id.startsWith('guide-'))" in APP
    assert "scoutTerrainDiscount:Boolean(stage.scoutTerrainDiscount)" in APP
    assert "activation.pendingAction.cost=cost" in APP
    assert "Yes · 0AP" in APP
    assert "No · 1AP" in APP
    assert "Territory terrain remains scouted if the Guide is incapacitated" in APP


def test_joint_ops_and_other_team_behaviour_are_not_replaced():
    assert "npoGenerationTable" in APP
    assert "Canoptek Macrocyte Warrior" in APP
    assert "A Ceaseless Scuttling" in APP or "ceaselessScuttlingEligible" in APP
    assert "function combatAbilityHandlers" not in APP  # Shared handlers remain a dictionary.
    assert "targetIncapacitated" in APP
    assert "if(after<=0){fight.completed=true" in APP
    assert "only corners and ends of Wall terrain" in APP


def test_release_version():
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    sw=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in sw
    assert f"V{CURRENT_APP_VERSION}" in html
