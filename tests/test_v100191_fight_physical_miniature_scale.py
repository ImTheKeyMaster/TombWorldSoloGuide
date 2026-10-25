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


def test_mount_measures_image_bases_and_positions_pills_without_clipping_heads():
    source = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const bytes=(w,h,upper,baseFrom,baseLeft,baseRight)=>{
  const b = new Uint8ClampedArray(w*h*4);
  for(let y=upper;y<h-2;y++) for(let x=(y>=baseFrom?baseLeft:Math.floor(w*.35));
      x<=(y>=baseFrom?baseRight:Math.floor(w*.65));x++) b[(y*w+x)*4+3]=255;
  return b;
};
const images = [
  {complete:true,naturalWidth:110,naturalHeight:150,currentSrc:'trooper.png',
   pixels:bytes(110,150,20,125,20,89),style:{}},
  {complete:true,naturalWidth:100,naturalHeight:200,currentSrc:'macrocyte.webp',
   pixels:bytes(100,200,3,175,20,75),style:{}}
];
const frames=images.map((_,i)=>({dataset:{fightBaseMm:i===0?'25':'28'},
  classList:{has:[],add(value){this.has.push(value);}}}));
const cards=images.map((image,i)=>({
  matches:()=>true,
  getBoundingClientRect:()=>({height:200,width:170}),
  querySelector: selector=> selector.includes(' > img.')?image:frames[i]
}));
let isFightResult=false;
const container={children:cards,isConnected:true,
  classList:{contains(name){return name==='fight-result-participants' && isFightResult;}}};
const root={querySelector:()=>container};
const document={createElement:()=>{
  let active=null;
  return {width:0,height:0,getContext:()=>({
    drawImage:image=>{active=image;},
    getImageData:()=>({data:active.pixels})
  })};
}};
const win={};
(new Function('window','document',fs.readFileSync('fight-portrait-scale.js','utf8')))(win,document);
win.TombWorldFightPortraitScale.mount(root);
for(let i=0;i<2;i++){
  assert(frames[i].classList.has.includes('is-table-scaled'));
  for(const key of ['width','height','left','bottom']) assert(Number.isFinite(parseFloat(images[i].style[key])));
}
// The taller macrocyte has 90% of 200px, the trooper stays shorter.
// Both silhouettes land on precisely the same 2px baseline.
const {analyzePixels,calculatePair}=win.TombWorldFightPortraitScale;
const geometry=images.map(im=>analyzePixels(im.pixels,im.naturalWidth,im.naturalHeight));
const layouts=calculatePair(geometry.map((g,i)=>({geometry:g,baseMm:i===0?25:28})),200);
assert(Math.abs(Math.max(...layouts.map(x=>x.figureHeight))-180)<.001);
assert(layouts[0].figureHeight<layouts[1].figureHeight);
for(let i=0;i<2;i++){
  const b=parseFloat(images[i].style.bottom);
  assert(Math.abs(b+layouts[i].transparentBottom-2)<.001);
  const t=200-2-layouts[i].figureHeight;
  assert(t>=17.99, 'no miniature head may be cropped above its card');
}
// The approved Fight Result mockup shifts both models 12% of card width
// to the left, while preserving every scale/baseline value. Fight
// Resolution remains anchored at the original position.
const original=images.map(image=>({...image.style}));
isFightResult=true;
win.TombWorldFightPortraitScale.mount(root);
for(let i=0;i<2;i++){
  assert(Math.abs(parseFloat(original[i].left)-parseFloat(images[i].style.left)-170*.12)<.001);
  for(const key of ['width','height','bottom']) assert.equal(images[i].style[key],original[i][key]);
}
"""
    r = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert r.returncode == 0, r.stderr or r.stdout


def test_shared_native_markup_has_physical_bases_and_only_two_fight_invocations():
    assert "baseMm=Number(npo.baseSize)||28" in APP
    assert "baseMm=Number(playerDefinition(participant.id).baseSize)||25" in APP
    assert "baseMm=Number(playerDefinition(participant.id).baseSize)||32" in APP
    assert 'data-fight-base-mm="${baseMm}"' in APP
    assert "function scaleFightPortraits(){" in APP
    assert APP.count("scaleFightPortraits();")==2  # Fight Resolution and Fight Result
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
    assert "resultLeftShift = container.classList?.contains('fight-result-participants')" in ENGINE
    assert "? width * .12 : 0" in ENGINE
    assert 'right:12%' in CSS
    assert "image.style.bottom = (2 - layout.transparentBottom)" in ENGINE
    assert "new ResizeObserver(refresh)" in ENGINE
    assert "image.addEventListener('load', refresh, { once: true })" in ENGINE


def test_release_offline_shell_and_saved_state():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"fight-portrait-scale.js?v={CURRENT_APP_VERSION}" in HTML
    assert 'fight-portrait-scale.js?v=${APP_VERSION}' in SW
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const EXPERIMENTAL_FEATURES_KEY = 'tombWorldSolo.experimentalFeatures.v1';" in APP
