"""All ten rulebook/reference PDFs stay in GitHub but out of the PWA cache."""

import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_ten_pdf_references_exist_but_not_in_the_pwa_precache():
    pdfs = list(ROOT.rglob("*.pdf"))
    assert len(pdfs) == 10
    assert (ROOT / "Assets/Tomb-World-Mission-Pack.pdf").is_file()
    assert len(list((ROOT / "docs").glob("*.pdf"))) == 9
    precache = WORKER.split("const PRECACHE_ASSETS = [", 1)[1].split("];", 1)[0]
    assert ".pdf" not in precache.lower()


def test_extended_offline_media_package_does_not_load_pdf_assets():
    manifest = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text())
    ambient = json.loads((ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
    backgrounds = json.loads((ROOT / "Assets/Images/Backgrounds/manifest.json").read_text())
    assert all(not entry.get("file", "").lower().endswith(".pdf")
               for entry in manifest["entries"].values())
    assert not ambient["file"].lower().endswith(".pdf")
    assert all(not filename.lower().endswith(".pdf")
               for filename in backgrounds["landscape"])
    package = WORKER.split("async function prepareOfflinePackage", 1)[1].split(
        "async function ensureOfflinePackage", 1
    )[0]
    assert ".pdf" not in package.lower()


def test_pdf_fetches_are_never_intercepted_or_cached():
    # Exercises the real service-worker fetch listener, both for normal downloads
    # and direct PDF navigation, while confirming PNG and JS still get cached.
    script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},metrics={opens:0,puts:0,fetches:0};
const cache={
  async match(){return undefined;},
  async put(){metrics.puts++;}
};
const context={
  URL,Request,Response,Headers,console,
  caches:{open:async()=>{metrics.opens++;return cache;},keys:async()=>[],delete:async()=>true},
  fetch:async()=>{metrics.fetches++;return new Response('ok',{status:200});},
  self:{location:{origin:'https://example.test'},clients:{claim:async()=>{}},
    addEventListener:(type,callback)=>listeners[type]=callback,skipWaiting:()=>{}}
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
function request(path,mode='cors'){
  let response;
  const req={method:'GET',mode,headers:new Headers(),url:'https://example.test/app/'+path};
  listeners.fetch({request:req,respondWith:promise=>{response=promise;}});
  return response;
}
(async()=>{
  const pdfs=[
    'Assets/Tomb-World-Mission-Pack.pdf',
    ...fs.readdirSync('docs').filter(f=>f.endsWith('.pdf')).map(f=>'docs/'+encodeURIComponent(f))
  ];
  if(pdfs.length!==10)throw Error('expected ten PDFs');
  for(const file of pdfs){
    if(request(file)!==undefined)throw Error('PDF was intercepted: '+file);
    if(request(file+'?download=1','navigate')!==undefined)throw Error('PDF navigation was intercepted: '+file);
  }
  if(request('DOCS/Example.PDF')!==undefined)throw Error('case-insensitive PDF should bypass cache');
  if(Object.values(metrics).some(Boolean))throw Error('PDF visit accessed a PWA cache');
  const png=request('Assets/Maps/mission-01.png');
  if(!png)throw Error('PNG must remain available for offline caching');
  await png;
  const js=request('app.js');
  if(!js)throw Error('JS must remain available for offline caching');
  await js;
  if(metrics.puts!==2)throw Error('PNG/JS caching regressed');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_release_is_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\\n\\n## v{CURRENT_APP_VERSION}")
