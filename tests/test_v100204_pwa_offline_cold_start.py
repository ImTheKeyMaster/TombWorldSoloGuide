"""v10.0.204 cold-start PWA: cache-first shell/data, bounded network,
immediate dark loading screen, and non-destructive recovery when offline.
"""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"index.html").read_text(encoding="utf-8")
SW=(ROOT/"service-worker.js").read_text(encoding="utf-8")
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def node(source):
    output=subprocess.run(["node","-e",source],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert output.returncode==0,output.stderr or output.stdout


def test_cached_shell_and_core_never_wait_for_network_even_when_stalled():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('service-worker.js','utf8');
const from=src.indexOf('async function archivedCacheMatchExact('),to=src.indexOf('async function cacheFirst(request)',from);
assert(from>0&&to>from);
const offlineShell=new Response('<html>Offline app works</html>',{headers:{'Content-Type':'text/html'}});
const cachedScript=new Response('/* app boot */',{headers:{'Content-Type':'text/javascript'}});
let networkRequests=0;
const cache={match:async key=>{
  const path=typeof key==='string'?key:new URL(key.url).pathname;
  return path.endsWith('/index.html')||path==='./index.html'?offlineShell:
    path.endsWith('/app.js')?cachedScript:null;
},put:async()=>{}};
const ctx={
 CACHE_NAME:'guide-204',APP_SHELL:'./index.html',isTombWorldCache:()=>true,
 caches:{open:async()=>cache,keys:async()=>['guide-204']},
 fetch:()=>{networkRequests++;return new Promise(()=>{});},
 archivedCacheMatch:async()=>null,canCache:()=>true,console,
 Response,AbortController,setTimeout,clearTimeout
};
const api=new Function('ctx','with(ctx){'+src.slice(from,to)+'return {offlineFirstNavigation,offlineFirstCodeAndData};}')(ctx);
(async()=>{
 const page=await api.offlineFirstNavigation(new Request('https://example.com/index.html'));
 assert.equal(await page.text(),'<html>Offline app works</html>');
 const js=await api.offlineFirstCodeAndData(new Request('https://example.com/app.js?v=10.0.204'));
 assert.equal(await js.text(),'/* app boot */');
 assert.equal(networkRequests,0,'Cached boot files must never contact a stalled network');
})().catch(e=>{console.error(e);process.exitCode=1;});
""")


def test_archived_boot_dependencies_are_matched_with_exact_release_query():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),src=fs.readFileSync('service-worker.js','utf8');
const a=src.indexOf('async function archivedCacheMatchExact('),b=src.indexOf('async function fetchWithStartupTimeout(',a);
const calls=[];
const ctx={CACHE_NAME:'new',isTombWorldCache:()=>true,caches:{
  keys:async()=>['old','new'],
  open:async name=>({match:async request=>{calls.push([name,request.url]);return null;}})
}};
const fn=new Function('ctx','with(ctx){'+src.slice(a,b)+'return archivedCacheMatchExact;}')(ctx);
(async()=>{
 const req=new Request('https://example.com/app.js?v=10.0.204');
 assert.equal(await fn(req),null);
 assert.deepEqual(calls,[['old',req.url]],'Do not strip version query from code requests');
})().catch(e=>{console.error(e);process.exitCode=1;});
""")
    assert "archived.match(request);" in SW
    assert "archivedCacheMatchExact(request)" in SW
    assert "cache.match(request)||await archivedCacheMatchExact(request)" in SW


def test_missing_startup_shell_has_recovery_page_not_blank_or_white():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('service-worker.js','utf8');
const a=src.indexOf('async function archivedCacheMatchExact('),b=src.indexOf('async function cacheFirst(request)',a);
const cache={match:async()=>null,put:async()=>{}};
const ctx={
 CACHE_NAME:'new',APP_SHELL:'./index.html',
 caches:{open:async()=>cache,keys:async()=>[]},isTombWorldCache:()=>true,
 archivedCacheMatch:async()=>null,
 fetch:async()=>{throw Error('Offline');},
 canCache:()=>true,Response,AbortController,setTimeout,clearTimeout,console
};
const api=new Function('ctx','with(ctx){'+src.slice(a,b)+'return {offlineFirstNavigation,offlineFirstCodeAndData};}')(ctx);
(async()=>{
 const result=await api.offlineFirstNavigation(new Request('https://example.com/'));
 assert.equal(result.status,503);
 const html=await result.text();
 assert(html.includes('background:#06100c'));
 assert(html.includes('Retry Loading'));
 assert(html.includes('Your saved battle has not been deleted'));
 const unavailable=await api.offlineFirstCodeAndData(new Request('https://example.com/app.js?v=10.0.204'));
 assert.equal(unavailable.type,'error');
})().catch(e=>{console.error(e);process.exitCode=1;});
""")


def test_fetch_listener_routes_navigation_and_code_offline_first():
    fetch_handler=SW.split("self.addEventListener('fetch', event => {",1)[1]
    assert "event.respondWith(offlineFirstNavigation(request));" in fetch_handler
    assert "event.respondWith(offlineFirstCodeAndData(request));" in fetch_handler
    assert "event.respondWith(networkFirst(request));" not in fetch_handler
    assert "async function fetchWithStartupTimeout(request,timeoutMs=4500)" in SW
    assert "controller.abort()" in SW
    assert "event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(CORE_PRECACHE_ASSETS)))" in SW
    assert "Keep previous caches as fallbacks" in SW


def test_first_paint_and_boot_recovery_do_not_depend_on_external_scripts():
    assert "background:#06100c" in HTML
    assert '<section id="startupPlaceholder"' in HTML
    assert "window.setTimeout(() => {" in HTML
    assert "},9000);" in HTML
    assert 'id="startupRetry"' in HTML
    assert 'id="startupExport"' in HTML
    assert "tombWorldBattleGuide.v1" in HTML
    assert "tomb-world-battle-guide-recovery-save.json" in HTML
    assert 'media="print" onload="this.media=' in HTML
    assert "app-css-ready" in HTML
    assert "location.reload()" in HTML
    assert "localStorage.removeItem('tombWorldBattleGuide.v1')" not in HTML


def test_manifest_requests_are_bounded_and_startup_does_not_wait_for_window_load():
    assert "async function fetchInitialGameData(path,timeoutMs=7500)" in APP
    assert "return await fetch(path,{cache:'default',signal:controller.signal});" in APP
    assert "fetchInitialGameData('Missions/manifest.json')" in APP
    assert "fetchInitialGameData('Player_Operatives/manifest.json')" in APP
    assert "fetchInitialGameData(BACKGROUND_MANIFEST_PATH,4500)" in APP
    sw_registration=APP.split("function registerServiceWorker(){",1)[1].split("registerServiceWorker();",1)[0]
    assert "navigator.serviceWorker.register('./service-worker.js'" in sw_registration
    assert "window.addEventListener('load'" not in sw_registration
    assert "ENSURE_OFFLINE_PACKAGE" in sw_registration
    assert "12000" in sw_registration


def test_version_and_pwa_cache_match():
    assert CURRENT_APP_VERSION=="10.0.204"
    assert "const APP_VERSION = '10.0.204';" in APP
    assert "const APP_VERSION = '10.0.204';" in SW
    assert '<div class="version">V10.0.204</div>' in HTML
    assert 'styles.css?v=10.0.204' in HTML
    assert 'app.js?v=10.0.204' in HTML
