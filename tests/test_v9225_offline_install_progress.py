import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source_between(source, start, end):
    return source[source.index(start) : source.index(end)]


def test_core_precache_excludes_pdf_and_large_optional_media_but_keeps_gameplay():
    precache = source_between(WORKER, "const PRECACHE_ASSETS", "const canCache")
    assert "Tomb-World-Mission-Pack.pdf" not in WORKER
    assert "narration-manifest.json" not in precache
    assert "ambient-config.json" not in precache
    assert "Backgrounds/manifest.json" not in precache
    for mission_number in range(1, 7):
        assert f"./Assets/Maps/mission-{mission_number:02}.png" in precache
    for asset in (
        "APP_SHELL",
        "./manifest.webmanifest",
        "./Assets/icon-192.png",
        "./Assets/Images/victory.png",
        "./Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3",
        "./Missions/manifest.json",
        "./Player_Operatives/manifest.json",
    ):
        assert asset in precache


def test_standalone_detection_and_request_are_page_owned_and_ios_compatible():
    assert "function isStandalonePwa()" in APP
    assert "window.matchMedia('(display-mode: standalone)').matches" in APP
    assert "navigator.standalone===true" in APP
    assert "const standalonePwa=isStandalonePwa();" in APP
    assert "if(standalonePwa)navigator.serviceWorker.ready.then" in APP
    assert "postMessage({type:'ENSURE_OFFLINE_PACKAGE'})" in APP
    assert "if(!standalonePwa)return;" in APP
    install = source_between(WORKER, "self.addEventListener('install'", "self.addEventListener('activate'")
    assert "ENSURE_OFFLINE_PACKAGE" not in install
    assert "prepareOfflinePackage" not in install


def test_extended_package_contains_narration_ambient_and_backgrounds_not_pdf():
    preparation = source_between(WORKER, "async function prepareOfflinePackage", "async function ensureOfflinePackage")
    assert "narrationFiles(narrationManifest)" in preparation
    assert "ambientFile(ambientConfig)" in preparation
    assert "backgroundManifest.landscape||[]" in preparation
    assert "precacheNarration(cache,narration" in preparation
    assert "precacheAmbient(cache,ambient" in preparation
    assert "Tomb-World-Mission-Pack.pdf" not in preparation


def test_marker_retry_update_reuse_and_cleanup_contracts_are_present():
    assert "const OFFLINE_PACKAGE_MARKER = './__offline-package-complete__';" in WORKER
    preparation = source_between(WORKER, "async function prepareOfflinePackage", "async function ensureOfflinePackage")
    assert preparation.index("for(const asset of backgrounds)") < preparation.index("cache.put(OFFLINE_PACKAGE_MARKER")
    assert "if(await cache.match(path))return;" in WORKER
    assert "if(markerVersion===APP_VERSION)return;" in WORKER
    assert "prepareOfflinePackage(client,{reportProgress:false})" in WORKER
    assert "copyExtendedAssetsFromOldCaches(names)" in WORKER
    assert "await copyExtendedAssetsFromOldCaches(names);" in WORKER
    assert ".map(name=>caches.delete(name))" in WORKER
    assert "OFFLINE_INSTALL_ERROR" in WORKER
    assert "It will be retried next time." in APP


def test_progress_payload_ui_and_completion_are_accessible_and_bounded():
    for message_type in (
        "OFFLINE_INSTALL_START",
        "OFFLINE_INSTALL_PROGRESS",
        "OFFLINE_INSTALL_COMPLETE",
    ):
        assert message_type in WORKER
        assert message_type in APP
    assert "Math.min(100, Math.max(0" in WORKER
    assert "Math.max(offlineInstallPercent" in APP
    assert "cache.put(OFFLINE_PACKAGE_MARKER" in WORKER
    assert 'role="status" aria-live="polite" aria-atomic="true"' in INDEX
    assert 'role="progressbar"' in INDEX
    assert "setTimeout(()=>{offlineInstallStatus.hidden=true;},1800)" in APP
    assert "width:min(360px,calc(100% - 30px))" in STYLES
    assert "env(safe-area-inset-top)" in STYLES
    assert "pointer-events:none" in STYLES


def test_worker_runtime_core_install_then_standalone_prepare_retry_and_completion():
    script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},messages=[],fetches=[],entries=new Map();
const key=value=>typeof value==='string'?value:value.url;
const cache={
  async addAll(paths){for(const path of paths)entries.set(key(path),new Response('core'));},
  async add(path){
    const response=await context.fetch(path);
    if(!response.ok)throw Error('failed '+path);
    entries.set(key(path),response.clone());
  },
  async match(path){const response=entries.get(key(path));return response?.clone();},
  async put(path,response){entries.set(key(path),response.clone());},
  async keys(){return [...entries.keys()].map(url=>new Request(new URL(url,'https://example.test/app/')));}
};
let failMedia=false;
const manifests={
  'narration-manifest':{entries:{one:{available:true,file:'events/one.mp3'}}},
  'ambient-config':{schemaVersion:1,file:'Ambient/caverns_25.ogg'},
  'Backgrounds/manifest':{landscape:['one.webp']}
};
const context={URL,Request,Response,console,caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async path=>{
    path=String(path);fetches.push(path);
    const manifest=Object.entries(manifests).find(([part])=>path.includes(part));
    if(manifest)return new Response(JSON.stringify(manifest[1]),{status:200});
    if(failMedia&&path.includes('events/one.mp3'))return new Response('',{status:503});
    return new Response('media',{status:200});
  },
  self:{location:{origin:'https://example.test'},clients:{claim:async()=>{}},skipWaiting:()=>{},addEventListener:(type,fn)=>listeners[type]=fn}
};
vm.createContext(context);vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
async function dispatch(type,data,client){let promise;listeners[type]({data,source:client,waitUntil:value=>promise=value});if(promise)await promise;}
(async()=>{
  await dispatch('install');
  if(fetches.length)throw Error('core install proactively fetched extended media');
  const client={postMessage:message=>messages.push(message)};
  failMedia=true;await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'},client);
  if(await cache.match('./__offline-package-complete__'))throw Error('failed package was marked complete');
  if(messages.at(-1)?.type!=='OFFLINE_INSTALL_ERROR')throw Error('failure was not reported');
  failMedia=false;messages.length=0;await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'},client);
  const complete=messages.at(-1);
  if(complete?.type!=='OFFLINE_INSTALL_COMPLETE'||complete.percent!==100||complete.completed!==complete.total)throw Error('completion invalid');
  if(!await cache.match('./__offline-package-complete__'))throw Error('successful package was not marked complete');
  let previous=-1;
  for(const message of messages.filter(item=>Number.isFinite(item.percent))){
    if(message.percent<previous||message.percent>100)throw Error('progress invalid');previous=message.percent;
  }
  const before=fetches.length;messages.length=0;await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'},client);
  if(messages[0]?.type!=='OFFLINE_PACKAGE_READY'||fetches.length!==before)throw Error('completed package repeated preparation');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_release_and_saved_game_surfaces_remain_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
