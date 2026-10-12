"""Regression tests for eagerly warming Deathwatch roster thumbnails."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_warmups_are_started_before_activation_and_after_team_load():
    assert "if(data.teamName?.toLowerCase()==='deathwatch')warmDeathwatchRosterImages(data.operatives.map(operative=>operative.id));" in APP
    assert "function showExperimentalDeathwatchRosterRail(candidates){\n    warmDeathwatchRosterImages(candidates);" in APP
    assert "if(selectedPlayerTeamName().toLowerCase()==='deathwatch')warmDeathwatchRosterImages(playerTeamData?.operatives?.map(operative=>operative.id)||[]);" in APP
    assert "experimentalDeathwatchGreenPortraitSvg(id," in APP
    assert "detailImage.innerHTML=experimentalDeathwatchGreenPortraitSvg(" in APP


def test_warmup_decodes_once_keeps_images_and_can_retry_failed_downloads():
    script = r"""
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf("const EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT=");
const end=source.indexOf("function experimentalDeathwatchGreenPortraitSvg(",start);
if(start<0||end<=start)throw Error('Cannot locate the Deathwatch portrait helpers');
const section=source.slice(start,end);
const created=[];
class MockImage {
  constructor(){this.decoding='';this.src='';this.onerror=null;this.decodeCalls=0;created.push(this);}
  decode(){this.decodeCalls++;return Promise.resolve();}
}
const document={documentElement:{dataset:{ui:'tomb'}}};
const {warmDeathwatchRosterImages:warm,cache,rosterSrc}=new Function('Image','document',section+
  'return {warmDeathwatchRosterImages,cache:warmedDeathwatchRosterImages,rosterSrc:experimentalDeathwatchRosterImage};'
)(MockImage,document);
const ids=['sergeant','aegis','bombard','demolisher'];
warm(ids);
if(created.length!==ids.length)throw Error('Expected one portrait per operative');
if(!created.every(image=>image.decodeCalls===1&&image.decoding==='async'))throw Error('Missing eager decode');
if(created[0].src!=='Assets/Images/TombUI/DeathwatchRoster/sergeant-fixed.svg')throw Error('Sergeant SVG not warmed');
if(created[1].src!=='Assets/Images/TombUI/DeathwatchRoster/aegis.webp')throw Error('Roster WebP path incorrect');
warm(ids);
if(created.length!==ids.length)throw Error('Images were downloaded/decoded again');
document.documentElement.dataset.ui='classic';
warm(['gunner']);
if(created.length!==ids.length)throw Error('Classic UI should not load experimental thumbnails');
document.documentElement.dataset.ui='tomb';
created[1].onerror();
if(cache.has(rosterSrc('aegis')))throw Error('Failed request must be retryable');
warm(['aegis']);
if(created.length!==ids.length+1)throw Error('Failed portrait was not retried');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_version_surfaces_agree():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in INDEX
    assert f"styles.css?v={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\\n\\n## v{CURRENT_APP_VERSION}")
