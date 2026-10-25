"""Fight portraits use actual image silhouettes and physical base ratios."""

from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
ENGINE = (ROOT / "fight-portrait-scale.js").read_text(encoding="utf-8")


def test_silhouette_measurement_base_calibration_and_90_percent_height():
    source = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('fight-portrait-scale.js','utf8');
const win={};
(new Function('window','document',source))(win,{});
const {analyzePixels,calculatePair}=win.TombWorldFightPortraitScale;
assert.equal(typeof analyzePixels,'function');
assert.equal(typeof calculatePair,'function');
function makeFigure(width,height,bodyX1,bodyX2,bodyTop,baseX1,baseX2,baseTop,baseBottom){
  const bytes=new Uint8ClampedArray(width*height*4);
  const fill=(x1,x2,y1,y2)=>{
    for(let y=y1;y<=y2;y++)for(let x=x1;x<=x2;x++){
      bytes[(y*width+x)*4+3]=255;
    }
  };
  fill(bodyX1,bodyX2,bodyTop,baseTop);
  fill(baseX1,baseX2,baseTop,baseBottom);
  return analyzePixels(bytes,width,height);
}
const trooper=makeFigure(110,150,39,69,22,22,87,126,146);
const macrocyte=makeFigure(100,200,37,63,4,20,75,176,197);
assert(trooper && macrocyte);
assert.equal(trooper.baseWidth,66);
assert.equal(macrocyte.baseWidth,56);
assert.equal(trooper.bottom,146);
assert.equal(macrocyte.bottom,197);
const layouts=calculatePair([{baseMm:25,geometry:trooper},{baseMm:28,geometry:macrocyte}],200);
assert.equal(layouts.length,2);
assert(Math.abs(Math.max(...layouts.map(item=>item.figureHeight))-180)<.0001);
assert(layouts[0].figureHeight<layouts[1].figureHeight);
assert(Math.abs(layouts[0].baseDiameter/layouts[1].baseDiameter-25/28)<.00001);
assert(Math.abs(layouts[0].figureHeight/layouts[1].figureHeight -
  ((trooper.figureHeight/66*25)/(macrocyte.figureHeight/56*28)))<.00001);
assert.equal(calculatePair([{baseMm:0,geometry:trooper},{baseMm:28,geometry:macrocyte}],200),null);
assert.equal(calculatePair([{baseMm:25,geometry:trooper},{baseMm:28,geometry:null}],200),null);
assert.equal(calculatePair([{baseMm:25,geometry:trooper},{baseMm:28,geometry:macrocyte}],0),null);
"""
    r=subprocess.run(["node","-e",source],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert r.returncode==0, r.stderr or r.stdout


def test_shared_native_markup_has_physical_bases_and_only_two_fight_invocations():
    assert "baseMm=Number(npo.baseSize)||28" in APP
    assert "baseMm=Number(playerDefinition(participant.id).baseSize)||25" in APP
    assert "baseMm=Number(playerDefinition(participant.id).baseSize)||32" in APP
    assert 'data-fight-base-mm="${baseMm}"' in APP
    assert "function scaleFightPortraits(){" in APP
    assert APP.count("    scaleFightPortraits();")==1  # Fight Result
    assert APP.count("      scaleFightPortraits();")==1  # Fight Resolution
    assert "window.TombWorldFightPortraitScale?.mount(modalBody)" in APP
    assert "function portraitImageMarkup(src,cssClass='',factionClass='')" in APP
    assert "function warmDeathKorpsPortraitImages(" in APP
    assert "function warmDeathwatchPortraitImages(" in APP


def test_styles_layering_and_fallback_are_scoped_to_fights():
    assert ".experimental-fight-pool .fight-portrait.is-table-scaled" in CSS
    assert ".fight-result-card.has-fight-portrait .fight-portrait.is-table-scaled" in CSS
    assert "max-height:none" in CSS
    assert "object-fit:fill" in CSS
    assert ".human-activation-shell" not in CSS.split("/* v10.0.191:",1)[1]
    assert "object-fit:contain" in CSS  # default when measuring is unavailable
    assert "object-position:center bottom" in CSS
    assert "MAX_FIGURE_HEIGHT_RATIO = 0.90" in ENGINE
    assert "figureHeight * baseMm / geometry.baseWidth" in ENGINE
    assert "centreX = width * .77" in ENGINE
    assert "image.style.bottom = (2 - layout.transparentBottom)" in ENGINE
    assert "new ResizeObserver(refresh)" in ENGINE
    assert "image.addEventListener('load', refresh, { once: true })" in ENGINE


def test_release_offline_shell_and_saved_state():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"fight-portrait-scale.js?v={CURRENT_APP_VERSION}" in HTML
    assert "'./fight-portrait-scale.js" not in SW or 'fight-portrait-scale.js?v=${APP_VERSION}' in SW
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const EXPERIMENTAL_FEATURES_KEY = 'tombWorldSolo.experimentalFeatures.v1';" in APP
