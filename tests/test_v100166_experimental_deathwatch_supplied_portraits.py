"""Regression tests for approved shared Deathwatch portraits and offline cleanup."""

import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PORTRAITS = ROOT / "Assets/Images/TombUI/Deathwatch"
FILES = {
    "sergeant": "Deathwatch_sergeant.png",
    "aegis": "Deathwatch_aegis.png",
    "breacher": "Deathwatch_breacher.png",
    "blademaster": "Deathwatch_blademaster.png",
    "marksman": "Deathwatch_marksman.png",
    "demolisher": "Deathwatch_demolisher.png",
    "horde-slayer": "Deathwatch_horder-slayer.png",
    "headtaker": "Deathwatch_headtake.png",
    "gunner": "Deathwatch_gunner.png",
    "bombard": "Deathwatch_bombard.png",
    "disruptor": "Deathwatch_disruptor.png",
}


def test_every_deathwatch_id_has_one_supplied_portrait_in_both_modes():
    team = json.loads((ROOT / "Player_Operatives/DeathWatch.json").read_text(encoding="utf-8"))
    assert set(FILES) == {x["id"] for x in team["operatives"]}
    for operative_id, filename in FILES.items():
        assert (PORTRAITS / filename).is_file(), operative_id
        assert (PORTRAITS / filename).stat().st_size > 100_000, operative_id
        assert f"'./Assets/Images/TombUI/Deathwatch/{filename}'" in SW
        js_id = f"'{operative_id}'" if "-" in operative_id else operative_id
        assert f"{js_id}:'{filename}'" in APP
    for old in ("DeathwatchRoster", "DeathwatchActivation"):
        assert not (ROOT / "Assets/Images/TombUI" / old).exists()
        assert old + "/" not in APP
        assert old + "/" not in SW


def test_photo_lookup_and_native_img_render_are_identical_in_both_modes_and_preloaded():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function portraitImageMarkup(');
const end=source.indexOf('  // User-photographed Death Korps cutouts',start);
assert(start>0&&end>start);
const pictures=[];
class Image {
 constructor(){pictures.push(this);this.decoding='';this.onerror=null;this.decodeCount=0;}
 set src(value){this._src=value;}
 get src(){return this._src;}
 decode(){this.decodeCount++;return Promise.resolve();}
}
const document={documentElement:{dataset:{ui:'tomb',experimental:'off'}}};
const api=new Function('document','Image','escapeHtml',source.slice(start,end)+
 '\nreturn {url:deathwatchPortraitImage,svg:deathwatchPortraitSvg,warm:warmDeathwatchPortraitImages,cache:warmedDeathwatchPortraitImages};'
)(document,Image,x=>x);
const files={
 sergeant:'Deathwatch_sergeant.png',aegis:'Deathwatch_aegis.png',
 breacher:'Deathwatch_breacher.png',blademaster:'Deathwatch_blademaster.png',
 marksman:'Deathwatch_marksman.png',demolisher:'Deathwatch_demolisher.png',
 'horde-slayer':'Deathwatch_horder-slayer.png',headtaker:'Deathwatch_headtake.png',
 gunner:'Deathwatch_gunner.png',bombard:'Deathwatch_bombard.png',
 disruptor:'Deathwatch_disruptor.png'
};
for(const mode of ['off','on']){
 document.documentElement.dataset.experimental=mode;
 for(const [id,file] of Object.entries(files)){
  const url='Assets/Images/TombUI/Deathwatch/'+file;
  assert.equal(api.url(id),url,mode+': '+id);
  const svg=api.svg(id,'art');
  assert(svg.includes('src="'+url+'"'),mode+': '+id);
  assert(svg.includes('class="art deathwatch-portrait-photo"'),mode+': '+id);
  assert(!svg.includes('<filter')&&!svg.includes('filter="'),mode+': '+id);
 }
}
assert.equal(api.url('unknown'),'');
assert.equal(api.svg('unknown','art'),'');
api.warm(['sergeant','aegis','aegis','missing']);
assert.equal(pictures.length,2,'Only unique real photographs should warm');
assert(pictures.every(p=>p.decoding==='async'&&p.decodeCount===1));
assert(pictures[0].src.endsWith('Deathwatch_sergeant.png'));
api.warm(['aegis','sergeant']);
assert.equal(pictures.length,2,'Subsequent renders reuse decoded images');
pictures[1].onerror();
assert(!api.cache.has(api.url('aegis')),'Failed image can retry');
api.warm(['aegis']);
assert.equal(pictures.length,3);
document.documentElement.dataset.experimental='off';
api.warm(['aegis']);
assert.equal(pictures.length,3,'Standard reuses same cached image');
document.documentElement.dataset.ui='classic';
api.warm(['bombard']);
assert.equal(pictures.length,3,'Classic view does not preload Tomb assets');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_all_portrait_surfaces_use_shared_code_without_old_filter_or_preview_gate():
    assert "function deathwatchPortraitSvg(id,svgClass='')" in APP
    assert "function warmDeathwatchPortraitImages(ids)" in APP
    assert "const resolvedPortraitMarkup=portraitMarkup;" in APP
    assert "deathwatchPortraitSvg(activation.operativeId,'experimental-activation-portrait-svg')" in APP
    assert "return deathwatchPortraitSvg(id,svgClass)" in APP
    assert "deathwatchPortraitSvg(id,'blast-result-portrait-artwork')" in APP
    assert "deathwatchPortraitSvg(participant.id,'fight-portrait-artwork')" in APP
    assert "if(data.teamName?.toLowerCase()==='deathwatch')warmDeathwatchPortraitImages(data.operatives.map(operative=>operative.id));" in APP
    for legacy in (
        "experimentalDeathwatchGreenPortraitSvg", "experimentalDeathwatchActivationImage",
        "experimentalDeathwatchRosterImage", "experimentalActivationPortraitCutout",
        "EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT", "DEATHWATCH_SUPPLIED_IMAGE_ROOT",
        "grayKeyed", "colorized",
    ):
        assert legacy not in APP, legacy
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "deathKorpsPortraitImage(id)" in APP
    assert "function resumeCombatAfterWeaponRuleCheck(" in APP


def test_versions_experimental_toggle_and_offline_manifest_are_safe():
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert "document.documentElement.dataset.experimental=enabled?'on':'off';" in APP
    assert "The approved green Deathwatch portraits are now standard" in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    for filename in ("app.js", "styles.css", "persistence.js"):
        assert f"{filename}?v={CURRENT_APP_VERSION}" in INDEX
    assert "const OPTIONAL_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in SW
    assert "const CORE_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in SW
