"""v10.1.27: Compact portrait cards avoid transparent padding for all factions."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
SCALE = (ROOT / "fight-portrait-scale.js").read_text(encoding="utf-8")


def test_alpha_aware_layout_never_crops_visible_figure():
    script = r"""
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('fight-portrait-scale.js','utf8');
const ctx={window:{},Map,Math};
vm.runInNewContext(source,ctx);
const {calculateSpecialResultLayout}=ctx.window.TombWorldFightPortraitScale;
const cases=[
 {name:'Deathwatch',width:256,height:256,top:64,bottom:248,left:40,right:205,figureHeight:185,frameWidth:168},
 {name:'Death Korps',width:256,height:256,top:45,bottom:252,left:55,right:190,figureHeight:208,frameWidth:145},
 {name:'Necron',width:256,height:256,top:25,bottom:234,left:39,right:228,figureHeight:210,frameWidth:168},
 {name:'short',width:256,height:256,top:110,bottom:222,left:65,right:178,figureHeight:113,frameWidth:145}
];
for(const model of cases){
 const layout=calculateSpecialResultLayout(model,model.frameWidth);
 assert(layout,model.name);
 assert(layout.figureHeight<=150.01,model.name);
 assert(layout.frameHeight-layout.figureHeight>=8,model.name);
 const scale=layout.imageHeight/model.height;
 const visibleLeft=layout.imageLeft+model.left*scale;
 const visibleRight=layout.imageLeft+(model.right+1)*scale;
 assert(visibleLeft>=-0.01,model.name+' left cropped');
 assert(visibleRight<=model.frameWidth+0.01,model.name+' right cropped');
 const visibleBottom=layout.imageBottom+(model.height-1-model.bottom)*scale;
 assert(Math.abs(visibleBottom-4)<0.01,model.name+' bottom not aligned');
 const visibleTop=layout.frameHeight-4-layout.figureHeight;
 assert(visibleTop>=3.99,model.name+' top cropped');
}
assert.equal(calculateSpecialResultLayout(null,168),null);
assert.equal(calculateSpecialResultLayout(cases[0],0),null);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr or result.stdout


def test_shared_compact_result_in_both_modes_and_all_portrait_sources():
    assert "mountSpecialResult(modalBody)" in APP
    assert APP.count("mountSpecialResult(modalBody)") == 2
    assert "mountSpecialResult" in SCALE
    assert "measureImage(img)" in SCALE
    assert "img.addEventListener('load', refresh" in SCALE
    assert "height:146px;overflow:hidden;align-self:flex-end" in CSS
    assert "object-fit:contain;object-position:center bottom" in CSS
    assert "min-height:184px" not in CSS
    assert "fightParticipantPortrait({side:'player',id:operativeId},'aggressive-defence')" in APP
    assert "fightParticipantPortrait(participant,'hot-weapon')" in APP
    assert "experimentalNecronPortraitSvg(npo," in APP
    assert "deathwatchPortraitSvg(participant.id,'fight-portrait-artwork')" in APP
    assert "deathKorpsCombatPortraitSvg(participant.id,'fight-portrait-artwork')" in APP
