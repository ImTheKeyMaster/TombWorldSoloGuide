"""All supported Tomb portrait factions share one native image renderer."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_shared_native_image_renderer_for_all_three_factions():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  function portraitImageMarkup(');
const b=source.indexOf('  function experimentalNecronPortraitMarkup(',a);
assert(a>0&&b>a);
const script=source.slice(a,b);
let appVersion='10.0.183';
const ctx={
  APP_VERSION:appVersion,
  escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
  document:{documentElement:{dataset:{ui:'tomb',experimental:'off'}}},
  Image:class Image{set src(x){this._src=x;}decode(){return Promise.resolve();}}
};
const api=new Function('ctx','with(ctx){'+script+
  '\nreturn {portraitImageMarkup,deathwatchPortraitSvg,deathKorpsPortraitPhoto,experimentalNecronPortraitSvg,deathKorpsPortraitImage,deathwatchPortraitImage,experimentalNecronPortraitImage};}')(ctx);
const testImage=(s,src,cls)=>{
  assert.match(s,/^<img class="/);
  assert.match(s,/alt="" draggable="false"|draggable="false" alt=""/);
  assert(s.includes('src="'+src+'"'),src);
  assert(s.includes(cls),cls);
  assert.match(s,/width="384" height="384"/);
  assert.match(s,/decoding="async"/);
  assert.doesNotMatch(s,/<svg|<image href|<filter/);
};
for(const enabled of ['off','on']){
  ctx.document.documentElement.dataset.experimental=enabled;
  const deathwatch=api.deathwatchPortraitSvg('disruptor','fight-portrait-artwork');
  testImage(deathwatch,'Assets/Images/TombUI/Deathwatch/Deathwatch_disruptor.png',
    'deathwatch-portrait-photo');
  const deathkorps=api.deathKorpsPortraitPhoto('trooper-3','experimental-activation-portrait-svg');
  testImage(deathkorps,'Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_3.png',
    'death-korps-portrait-photo');
  const necron=api.experimentalNecronPortraitSvg({type:'Necron Warrior',weaponId:'gauss-reaper'},
    'necronActivation','fight-portrait-artwork');
  testImage(necron,'Assets/Images/TombUI/NecronActivation/necron-warrior-gauss-reaper.webp?v=10.0.183',
    'experimental-necron-framed-svg');
}
assert.equal(api.deathwatchPortraitSvg('unknown'),'');
assert.equal(api.deathKorpsPortraitPhoto('unknown'),'');
assert.equal(api.experimentalNecronPortraitSvg({type:'unknown'},'unknown'),'');
const safe=api.portraitImageMarkup('x.png" onerror="alert(1)','photo','team');
assert.doesNotMatch(safe,/onerror="/);
assert.match(safe,/&quot;/);
assert.equal((script.match(/return portraitImageMarkup\(/g)||[]).length,3,
  'exactly one factory shared by all faction wrappers');
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_photo_surfaces_reuse_pipeline_and_keep_visual_appearance():
    assert "portraitImageMarkup(deathwatchPortraitImage(id)" in APP
    assert "portraitImageMarkup(deathKorpsPortraitImage(id)" in APP
    assert "portraitImageMarkup(src?" in APP
    assert "deathwatchPortraitSvg(activation.operativeId,'experimental-activation-portrait-svg')" in APP
    assert "deathKorpsPortraitPhoto(activation.operativeId,'experimental-activation-portrait-svg')" in APP
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronHumanActivationTint','experimental-activation-portrait-svg')" in APP
    assert "return deathKorpsPortraitPhoto(id,svgClass)" in APP
    assert "function deathKorpsPortraitPhoto(id,cssClass='')" in APP
    assert "return deathwatchPortraitSvg(id,svgClass)" in APP
    assert "object-position:center top" in CSS
    assert "object-position:center center" in CSS
    assert "opacity:.52;" in CSS  # Approved Deathwatch contrast unchanged
    assert "width:157%" in CSS  # Approved Death Korps activation crop unchanged
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function refreshSvgPortraitsAfterResume(" in APP  # Fallback retained for other SVGs


def test_versioning():
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"V{CURRENT_APP_VERSION}" in html
    assert f"app.js?v={CURRENT_APP_VERSION}" in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
