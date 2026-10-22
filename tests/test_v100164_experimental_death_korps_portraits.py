"""Approved Death Korps portraits render consistently in Standard and Experimental modes."""
import re
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
IMAGES = ROOT / "Assets/Images/TombUI/DeathKorps"

NEW_IMAGES = (
    "Death_Korps_gunner-meltagun.png",
    "Death_Korps_gunner_grenade.png",
    "Death_Korps_gunner_plasma.png",
    "Death_Korps_medic.png",
    "Death_Korps_sniper.png",
    "Death_Korps_trooper_3.png",
    "Death_Korps_trooper_4.png",
    "Death_Korps_trooper_5.png",
    "Death_Korps_vox-operator_2.png",
)


def test_approved_portraits_resolve_in_both_modes():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const begin=src.indexOf('  const DEATH_KORPS_PORTRAIT_ROOT=');
const end=src.indexOf('  function playerRosterPortraitMarkup(',begin);
assert(begin>0&&end>begin);
const document={documentElement:{dataset:{experimental:'off'}}};
const pictures=[];
class Image {
  constructor(){pictures.push(this);this.decoding='';this.onload=null;this.onerror=null;}
  set src(value){this._src=value;}
  get src(){return this._src;}
  decode(){return Promise.resolve();}
}
const api=new Function('document','Image',src.slice(begin,end)+
  '\nreturn {deathKorpsPortraitImage,warmDeathKorpsPortraitImages,warmedDeathKorpsPortraits};'
)(document,Image);
const url=(id)=>api.deathKorpsPortraitImage(id);
const expected={
  'gunner-flamer':'gunner_flamer',
  'gunner-grenade-launcher':'gunner_grenade',
  'gunner-meltagun':'gunner-meltagun',
  'gunner-plasma-gun':'gunner_plasma',
  medic:'medic',sniper:'sniper',
  'trooper-3':'trooper_3','trooper-4':'trooper_4',
  'trooper-5':'trooper_5','vox-operator':'vox-operator_2'
};
for(const mode of ['off','on']){
 document.documentElement.dataset.experimental=mode;
 for(const [id,file] of Object.entries(expected)){
  const path=url(id);
  assert.equal(path,'Assets/Images/TombUI/DeathKorps/Death_Korps_'+file+'.png',mode+': '+id);
  assert(fs.existsSync(path),'missing portrait: '+path);
 }
 assert.equal(url('nonexistent'),'');
 assert.equal(url('watchmaster'),'Assets/Images/TombUI/DeathKorps/Death_Korps_watchmaster.png');
 assert.equal(url('trooper-1'),'Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_1.png');
 assert.equal(url('trooper-2'),'Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_2.png');
 assert.equal(url('confidant'),'Assets/Images/TombUI/DeathKorps/Death_Korps_confidant.png');
}
document.documentElement.dataset.experimental='on';
const imagesToWarm=['trooper-1','trooper-3','gunner-flamer','medic'];
(async()=>{
 const waiting=api.warmDeathKorpsPortraitImages(imagesToWarm);
 assert.equal(pictures.length,4,'Experimental mode must preload distinct photos');
 assert(pictures.every(p=>p.decoding==='async'));
 pictures.forEach(p=>p.onload());
 await waiting;
 assert.equal(api.warmedDeathKorpsPortraits.size,4);
 document.documentElement.dataset.experimental='off';
 assert.match(url('trooper-3'),/trooper_3\.png$/,'Standard must retain the promoted Trooper 3 image');
 const next=api.warmDeathKorpsPortraitImages(['trooper-3','vox-operator']);
 assert.equal(pictures.length,5,'Previously cached matching photos must be reused');
 pictures[4].onload();
 await next;
 assert.equal(api.warmedDeathKorpsPortraits.size,5);
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_all_new_portraits_are_precached_and_old_path_is_not():
    for name in (*NEW_IMAGES, "Death_Korps_gunner_flamer.png"):
        assert (IMAGES / name).is_file(), f"Missing file: {name}"
        assert f"./Assets/Images/TombUI/DeathKorps/{name}" in SW
    assert "Death_Korps_gunner.png" not in SW
    assert "DEATH_KORPS_EXPERIMENTAL_PORTRAITS" not in APP
    assert "const filename=DEATH_KORPS_PORTRAITS[id];" in APP


def test_version_and_existing_portrait_surfaces_stay_intact():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    for name in ("app.js", "styles.css", "persistence.js"):
        assert f"{name}?v={CURRENT_APP_VERSION}" in INDEX
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "warmDeathKorpsPortraitImages" in APP
    assert "deathKorpsPortraitImage(activation.operativeId)" in APP
    assert "function deathKorpsCombatPortraitSvg(" in APP
    assert "function playerRosterPortraitMarkup(" in APP
    assert "function resumeCombatAfterWeaponRuleCheck(" in APP
    assert "function advanceMultiTargetAttackSequence(" in APP
