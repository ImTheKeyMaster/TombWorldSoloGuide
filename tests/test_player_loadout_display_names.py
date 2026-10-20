"""Regression tests for player operative display numbering and loadout suffixes."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_loadout_follows_roster_number_without_changing_operative_ids():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const helpers=source.slice(source.indexOf('  function playerDisplayIdentity(id)'),
                           source.indexOf('  function allocateDisplayNumber('));
assert(helpers.includes('const variant='),'Shared formatter must recognize unnumbered source variants');

let definitions=[];
const state={playerRoster:[],playerDisplayNumbers:{},roster:[]};
const make=new Function('playerDefinition','npoDefinition','state',
  helpers+';return {playerName,playerDisplayIdentity};');
const {playerName}=make(id=>definitions.find(entry=>entry.id===id)||null,()=>null,state);
const check=(team,ids,numbers,expected)=>{
  definitions=JSON.parse(fs.readFileSync('Player_Operatives/'+team,'utf8')).operatives;
  state.playerRoster=[...ids];
  state.playerDisplayNumbers={...numbers};
  assert.deepEqual(ids.map(playerName),expected,team);
  assert.deepEqual(state.playerRoster,ids,'Display formatting must not change saved IDs');
};

check('DeathKorps.json',
  ['gunner-flamer','gunner-grenade-launcher','gunner-meltagun','gunner-plasma-gun'],
  {'gunner-flamer':1,'gunner-grenade-launcher':2,'gunner-meltagun':3,'gunner-plasma-gun':4},
  ['Gunner 1 (Flamer)','Gunner 2 (Grenade Launcher)',
   'Gunner 3 (Meltagun)','Gunner 4 (Plasma Gun)']);
check('Kasrkin.json',
  ['gunner-flamer','gunner-meltagun','gunner-plasma-gun'],
  {'gunner-flamer':1,'gunner-meltagun':2,'gunner-plasma-gun':3},
  ['Gunner 1 (Flamer)','Gunner 2 (Meltagun)','Gunner 3 (Plasma Gun)']);
check('ScoutSquad.json',
  ['warrior-2-boltgun','warrior-3-shotgun'],
  {'warrior-2-boltgun':2,'warrior-3-shotgun':3},
  ['Scout Warrior 2 (Boltgun)','Scout Warrior 3 (Astartes Shotgun)']);
check('SpectreSquad.json',
  ['trooper-2-lascarbine','trooper-3-lasrifle'],
  {'trooper-2-lascarbine':2,'trooper-3-lasrifle':3},
  ['Trooper 2 (Lascarbine)','Trooper 3 (Lasrifle)']);
check('DeathKorps.json',['gunner-meltagun'],{},['Gunner (Meltagun)']);
check('DeathKorps.json',['confidant'],{},['Confidant']);
check('TempestusAquilons.json',['gunner-melta','gunner-plasma'],{},
  ['Gunner (Melta)','Gunner (Plasma)']);
check('SpectreSquad.json',['field-medicae-lascarbine'],{},
  ['Field Medicae (Lascarbine)']);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
