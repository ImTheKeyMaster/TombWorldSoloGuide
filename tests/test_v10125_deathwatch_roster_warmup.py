"""Approved Deathwatch green portraits are eagerly decoded and reused."""

from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
INDEX=(ROOT/"index.html").read_text(encoding="utf-8")
WORKER=(ROOT/"service-worker.js").read_text(encoding="utf-8")
README=(ROOT/"README.md").read_text(encoding="utf-8")


def test_warmup_started_on_team_load_and_roster_activation():
    assert "if(data.teamName?.toLowerCase()==='deathwatch')warmDeathwatchPortraitImages(data.operatives.map(operative=>operative.id));" in APP
    assert "if(selectedPlayerTeamName().toLowerCase()==='deathwatch')warmDeathwatchPortraitImages(candidates);" in APP
    assert "function deathwatchPortraitSvg(id,svgClass='')" in APP
    assert "detailImage.innerHTML=playerRosterPortraitMarkup(" in APP


def test_warmup_decodes_once_reuses_images_and_retries_failures():
    js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('const DEATHWATCH_PORTRAIT_ROOT=');
const end=source.indexOf('function deathwatchPortraitSvg(',start);
assert(start>=0&&end>start);
const pictures=[];
class Image{
 constructor(){this.decoding='';this.onerror=null;this.src='';this.decodeCalls=0;pictures.push(this);}
 decode(){this.decodeCalls++;return Promise.resolve();}
}
const document={documentElement:{dataset:{ui:'tomb',experimental:'off'}}};
const api=new Function('Image','document',source.slice(start,end)+
 '\nreturn {warm:warmDeathwatchPortraitImages,cache:warmedDeathwatchPortraitImages,url:deathwatchPortraitImage};'
)(Image,document);
const ids=['sergeant','aegis','bombard','demolisher'];
api.warm(ids);
assert.equal(pictures.length,4);
assert(pictures.every(x=>x.decoding==='async'&&x.decodeCalls===1));
assert.equal(pictures[0].src,'Assets/Images/TombUI/Deathwatch/Deathwatch_sergeant.png');
assert.equal(pictures[1].src,'Assets/Images/TombUI/Deathwatch/Deathwatch_aegis.png');
api.warm(ids);
assert.equal(pictures.length,4);
document.documentElement.dataset.experimental='on';
api.warm(ids);
assert.equal(pictures.length,4,'Both modes should share cached photographs');
pictures[1].onerror();
assert(!api.cache.has(api.url('aegis')));
api.warm(['aegis']);
assert.equal(pictures.length,5);
document.documentElement.dataset.ui='classic';
api.warm(['gunner']);
assert.equal(pictures.length,5);
"""
    result=subprocess.run(["node","-e",js],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_version_surfaces_agree():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
