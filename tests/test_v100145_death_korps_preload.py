"""Death Korps portraits are loaded and decoded before team setup advances."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_portrait_warmup_deduplicates_waits_for_network_and_decode_and_retries():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const begin=app.indexOf('  const DEATH_KORPS_PORTRAIT_ROOT=');
const end=app.indexOf('  function playerRosterPortraitMarkup(',begin);
assert(begin>0&&end>begin);
const images=[];
class MockImage {
  constructor(){this.onload=null;this.onerror=null;this.decoding='';images.push(this);}
  set src(value){this._src=value;}
  get src(){return this._src;}
  decode(){return new Promise((resolve,reject)=>{this.finishDecode=resolve;this.failDecode=reject;});}
}
const api=new Function('Image',app.slice(begin,end)+
  '\nreturn {warmDeathKorpsPortraitImages,warmedDeathKorpsPortraits,readyDeathKorpsPortraits,deathKorpsPortraitImage};'
)(MockImage);
const ids=['trooper-1','trooper-3','trooper-3','gunner-flamer','unknown'];
let done=false;
const first=api.warmDeathKorpsPortraitImages(ids).then(()=>{done=true;});
assert.equal(images.length,3,'each distinct operative photo should preload once');
assert.notEqual(images[0].src,api.deathKorpsPortraitImage('trooper-3'));
assert.equal(images[1].src,api.deathKorpsPortraitImage('trooper-3'));
assert.equal(images[0].decoding,'async');
assert.equal(images[0].src,api.deathKorpsPortraitImage('trooper-1'));
api.warmDeathKorpsPortraitImages(ids);
assert.equal(images.length,3,'repeated warmup should reuse existing images');
images.forEach(image=>image.onload());
Promise.resolve().then(async()=>{
  assert.equal(done,false,'load events alone must not release team setup before decode');
  images.forEach(image=>image.finishDecode());
  await first;
  assert.equal(done,true);
  const repeat=api.warmDeathKorpsPortraitImages(ids);
  await repeat;
  assert.equal(images.length,3,'decoded photos stay reusable');
  const failure=api.warmDeathKorpsPortraitImages(['confidant']);
  assert.equal(images.length,4);
  images[2].onerror();
  images[2].failDecode(Error('network'));
  await failure;
  assert(!api.warmedDeathKorpsPortraits.has(api.deathKorpsPortraitImage('confidant')));
  api.warmDeathKorpsPortraitImages(['confidant']);
  assert.equal(images.length,5,'failed portrait must be retryable');
}).catch(error=>{console.error(error);process.exitCode=1;});
""")


def test_setup_waits_for_portraits_without_delaying_existing_game_and_team_switch():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const begin=app.indexOf('  let playerManifest=null;');
const end=app.indexOf('  function validatePlayerTeamData',begin);
assert(begin>0&&end>begin);
const code=app.slice(begin,end);
const state={playerTeamId:'korps',playerRoster:[],screen:'setup'};
let completePortraits, calls=0;
const warmDeathKorpsPortraitImages=ids=>{
  calls++;
  return new Promise(resolve=>{completePortraits=resolve;});
};
const dependencies={
  state,
  fetch:async()=>({ok:true,json:async()=>({teamName:'Death Korps',operatives:[{id:'confidant'}]})}),
  validatePlayerTeamData:()=>{},
  render:()=>{},save:()=>true,assignPlayerDisplayNumbers:()=>{},
  clearPlayerTeamDependentState:()=>{},
  warmDeathKorpsPortraitImages,
  warmDeathwatchRosterImages:()=>{throw Error('incorrect faction warmup');}
};
const api=new Function('ctx','with(ctx){'+code+
  '\nreturn {loadPlayerTeamData,canBuildPlayerRoster,setManifest:data=>playerManifest=data};}'
)(dependencies);
api.setManifest({teams:[{id:'korps',file:'DeathKorps.json'}]});
(async()=>{
  let complete=false;
  const pending=api.loadPlayerTeamData('korps').then(()=>{complete=true;});
  for(let i=0;i<5;i++)await Promise.resolve();
  assert.equal(calls,1);
  assert.equal(api.canBuildPlayerRoster(),false,'setup navigation opened before portraits decoded');
  assert.equal(complete,false);
  completePortraits();
  await pending;
  assert.equal(complete,true);
  assert.equal(api.canBuildPlayerRoster(),true);
  state.screen='game';
  const resumed=api.loadPlayerTeamData('korps');
  await resumed;
  assert.equal(api.canBuildPlayerRoster(),true,'saved-game startup unexpectedly waited for portraits');
})().catch(error=>{console.error(error);process.exitCode=1;});
""")


def test_no_ui_or_gameplay_changes_and_consistent_release():
    assert "const readyDeathKorpsPortraits=new Map();" in APP
    assert "await Promise.race([portraitsReady,new Promise(resolve=>setTimeout(resolve,12000))])" in APP
    assert "if(requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId)return null;" in APP
    assert "if(state.screen==='setup')" in APP
    assert "playerActivationOperativeEliminated" in APP
    assert "experimental-activation-portrait-svg" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
