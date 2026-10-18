"""Executable checks for promoting Tomb UI without losing the preview switch."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_startup_and_feature_flag_are_independent_of_classic_preference():
    js = r"""
const fs=require('node:fs');
const index=fs.readFileSync('index.html','utf8');
const app=fs.readFileSync('app.js','utf8');
const boot=index.match(/<script>\s*([\s\S]*?)<\/script>/);
if(!boot)throw Error('Missing early mode bootstrap');
const assert=(x,reason)=>{if(!x)throw Error(reason);};
function start(value,throws=false){
  const document={documentElement:{dataset:{ui:'tomb',experimental:'off'}}};
  const localStorage={getItem:(key)=>{
    if(throws)throw Error('private browsing / denied storage');
    return key==='tombWorldSolo.experimentalFeatures.v1'?value:null;
  }};
  new Function('document','localStorage',boot[1])(document,localStorage);
  return document.documentElement.dataset;
}
assert(start(null).ui==='tomb'&&start(null).experimental==='off','Production default changed');
assert(start('on').ui==='tomb'&&start('on').experimental==='on','Preview flag not restored');
assert(start('tomb').ui==='tomb'&&start('tomb').experimental==='off','Old preference affected startup');
assert(start(null,true).ui==='tomb','Storage failure reverts production UI');

const begin=app.indexOf('function experimentalFeaturesEnabled()');
const end=app.indexOf('function showExperimentalUiPanel()',begin);
assert(begin>=0&&end>begin,'Could not locate experimental flag setter');
const fragment=app.slice(begin,end);
const create=new Function('document','localStorage','EXPERIMENTAL_FEATURES_KEY',fragment+
  ';return {setExperimentalFeatures,experimentalFeaturesEnabled};');
const root={documentElement:{dataset:{ui:'tomb',experimental:'off'}}},settings={};
const localStorage={
  setItem:(key,value)=>{settings[key]=value;},
  removeItem:key=>{delete settings[key];}
};
const controls=create(root,localStorage,'tombWorldSolo.experimentalFeatures.v1');
controls.setExperimentalFeatures(true);
assert(root.documentElement.dataset.ui==='tomb'&&controls.experimentalFeaturesEnabled()
  &&settings['tombWorldSolo.experimentalFeatures.v1']==='on','Preview enable switched production or was not saved');
controls.setExperimentalFeatures(false);
assert(root.documentElement.dataset.ui==='tomb'&&!controls.experimentalFeaturesEnabled()
  &&!Object.keys(settings).length,'Preview disable changed production or failed to clear preference');
const unavailable=create(root,{setItem:()=>{throw Error('denied')},
  removeItem:()=>{throw Error('denied')}},'tombWorldSolo.experimentalFeatures.v1');
unavailable.setExperimentalFeatures(true);
assert(unavailable.experimentalFeaturesEnabled()&&root.documentElement.dataset.ui==='tomb',
  'Denied storage disabled working preview mode or production UI');
console.log('standard/experimental modes independent and storage-safe');
"""
    result = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_release_assets_and_saved_game_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 127)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")


def test_current_tomb_features_remain_production():
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert "document.documentElement.dataset.ui==='tomb'" in APP
    for feature in (
        "showExperimentalDeathwatchRosterRail(candidates)",
        "showExperimentalNecronRosterRail(candidates)",
        "experimentalDeathwatchGreenPortraitSvg(id,",
        "experimentalNpoTargetRosterRail(eligibleTargetIds)",
    ):
        assert feature in APP
    assert "document.documentElement.dataset.ui='classic'" not in APP
    assert "tombWorldSolo.experimentalUI.v1" not in INDEX
    assert "tombWorldSolo.experimentalUI.v1" not in APP
