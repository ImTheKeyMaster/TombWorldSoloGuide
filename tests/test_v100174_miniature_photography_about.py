"""Regress About's miniature-photography attribution without weakening IP notices."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
AUDIT = (ROOT / "docs/IP_ASSET_AUDIT.md").read_text(encoding="utf-8")
ABOUT = APP.split("  function showAbout(){", 1)[1].split("  function startNewGameSetup(){", 1)[0]


def test_photography_notice_is_distinct_and_preserves_existing_disclaimer():
    assert '<section><h3>Miniature Photography</h3>' in ABOUT
    assert ABOUT.index('<h3>Project Content</h3>') < ABOUT.index('<h3>Miniature Photography</h3>')
    assert ABOUT.index('<h3>Miniature Photography</h3>') < ABOUT.index('<h3>Software Disclaimer</h3>')
    assert 'creator’s personal collection' in ABOUT
    assert 'photographed independently' in ABOUT
    assert 'not official Games Workshop promotional product photographs' in ABOUT
    assert 'underlying miniature designs' in ABOUT
    assert 'trademarks' in ABOUT
    assert 'other intellectual property' in ABOUT
    assert 'separately sourced game materials, mission maps, or other artwork' in ABOUT
    assert 'not affiliated with, endorsed by, sponsored by, licensed by, or approved by Games Workshop' in ABOUT
    assert 'No challenge to any ownership, trademark, copyright' in ABOUT
    assert 'not a replacement for the official rules' in ABOUT
    assert 'provided &quot;as is&quot;' in ABOUT
    assert 'Cloudflare Web Analytics' in ABOUT
    assert 'id="aboutBack"' in ABOUT
    assert 'not copyrighted' not in ABOUT.lower()
    assert 'copyright-free' not in ABOUT.lower()
    assert 'not trademarked' not in ABOUT.lower()


def test_about_opens_and_back_navigation_remains_working():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function showAbout(){');
const end=source.indexOf('  function startNewGameSetup(){',start);
assert(start>0&&end>start);
let title,html,navigated=0,focused=0,backHandler=null;
const back={set onclick(fn){backHandler=fn;}};
const ctx={
  APP_VERSION:'10.0.174',
  showModal:(t,body)=>{title=t;html=body;},
  $:selector=>selector==='#aboutBack'?back:selector==='#menuAbout'?{focus:options=>{
    assert.deepEqual(options,{preventScroll:true});focused++;
  }}:null,
  showGameMenu:()=>{navigated++;},
  requestAnimationFrame:callback=>callback()
};
const showAbout=new Function('ctx','with(ctx){'+source.slice(start,end)+'\nreturn showAbout;}')(ctx);
showAbout();
assert.equal(title,'About');
assert.match(html,/Miniature Photography/);
assert.match(html,/creator’s personal collection/);
assert.match(html,/Games Workshop Notice/);
assert.match(html,/Contact/);
assert.match(html,/Version 10\.0\.174/);
assert.equal(navigated,0);
assert.equal(typeof backHandler,'function');
backHandler();
assert.equal(navigated,1);
assert.equal(focused,1);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_audit_records_attribution_without_global_photo_rights_claim():
    assert '2026-10-23 author-provided miniature photography clarification' in AUDIT
    assert 'creator reports that miniature photographs' in AUDIT
    assert 'Assets/Images/TombUI/DeathKorps/' in AUDIT
    assert 'Assets/Images/TombUI/Deathwatch/' in AUDIT
    assert 'Assets/Images/TombUI/NecronActivation/' in AUDIT
    assert 'not a completed item-by-item provenance or rights clearance' in AUDIT
    assert 'mission maps, icons, backgrounds, or other art' in AUDIT
    assert 'original v8.6.19 inventory and its classifications are retained' in AUDIT
    assert 'Likely official Games Workshop material' in AUDIT


def test_version_consistency_and_unchanged_storage_identifier():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert f'app.js?v={CURRENT_APP_VERSION}' in HTML
    assert f'styles.css?v={CURRENT_APP_VERSION}' in HTML
    assert README.startswith(f'# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}')
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function experimentalFeaturesEnabled()" in APP
