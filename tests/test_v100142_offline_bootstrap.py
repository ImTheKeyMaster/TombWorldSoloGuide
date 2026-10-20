"""Reproduce an iPhone offline restart after a media-heavy service-worker update."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def run_node(source):
    result = subprocess.run(
        ["node", "-e", source], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_offline_boot_after_a_large_media_cache_install_would_fail():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const listeners={},storage=new Map(),deleted=[],requests=[];
const scope='https://example.test/app/';
const key=value=>new URL(typeof value==='string'?value:value.url,scope).href;
const cacheFor=name=>{
  if(!storage.has(name))storage.set(name,new Map());
  const data=storage.get(name);
  return {
    async addAll(paths){
      assert(paths.includes('./index.html'));
      assert(paths.some(p=>p.includes('app.js?v=')));
      // An iPhone rejecting a portrait/audio during one giant addAll must not
      // abort installation of the HTML, JavaScript, CSS, and game data.
      if(paths.some(p=>/\.(?:png|webp|ogg|mp3)(?:\?|$)/.test(p)))
        throw Error('QuotaExceededError: an optional image was too large');
      for(const p of paths)data.set(key(p),new Response('new:'+p));
    },
    async match(path,options){
      const k=key(path);
      const result=data.get(k);
      if(result)return result.clone();
      if(options?.ignoreSearch){
        const plain=new URL(k).pathname;
        for(const [cached,response] of data)
          if(new URL(cached).pathname===plain)return response.clone();
      }
    },
    async add(path){throw Error('Should not load optional media during install');},
    async put(path,response){data.set(key(path),response.clone());},
    async keys(){return [...data.keys()].map(url=>new Request(url));}
  };
};
const old='tomb-world-battle-guide-previous';
storage.set(old,new Map([
  [key('./index.html'),new Response('old shell')],
  [key('./Assets/Images/TombUI/DeathKorps/Death_Korps_gunner.png'),new Response('old gunner')],
  [key('./Player_Operatives/manifest.json'),new Response('{"teams":[]}')]
]));
const context={
  URL,Request,Response,console,
  fetch:async request=>{requests.push(key(request));throw Error('offline');},
  caches:{
    open:async name=>cacheFor(name),
    keys:async()=>[...storage.keys()],
    delete:async name=>{deleted.push(name);return storage.delete(name);}
  },
  self:{
    location:{origin:'https://example.test'},
    clients:{claim:async()=>{}},
    addEventListener:(name,fn)=>{listeners[name]=fn;}
  }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
const dispatch=async event=>{
  let promise;
  listeners[event]({waitUntil:p=>promise=p});
  await promise;
};
(async()=>{
  await dispatch('install');
  await dispatch('activate');
  assert.deepEqual(deleted,[],'the last offline cache was deleted prematurely');
  const navigation={method:'GET',mode:'navigate',url:scope,headers:new Headers()};
  let outgoing;
  listeners.fetch({request:navigation,respondWith:p=>outgoing=p});
  assert.equal(await (await outgoing).text(),'new:./');
  // Simulate iOS evicting the current app shell: the previous one must
  // still recover the navigation rather than returning a white page.
  for(const cached of storage.values())
    for(const url of [...cached.keys()])
      if(url===key('./')||url===key('./index.html'))cached.delete(url);
  storage.get(old).set(key('./index.html'),new Response('old shell'));
  listeners.fetch({request:navigation,respondWith:p=>outgoing=p});
  assert.equal(await (await outgoing).text(),'old shell');
  const script={method:'GET',mode:'cors',url:key('app.js?v=older'),headers:new Headers()};
  storage.get(old).set(key('app.js?v=older'),new Response('old js'));
  listeners.fetch({request:script,respondWith:p=>outgoing=p});
  assert.equal(await (await outgoing).text(),'old js');
  const image={method:'GET',mode:'cors',url:key('Assets/Images/TombUI/DeathKorps/Death_Korps_gunner.png'),headers:new Headers()};
  listeners.fetch({request:image,respondWith:p=>outgoing=p});
  assert.equal(await (await outgoing).text(),'old gunner');
  assert(requests.length>=2,'offline errors were not exercised');
})().catch(e=>{console.error(e);process.exit(1)});
""")


def test_media_preparation_failure_never_invalidates_offline_core():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const listeners={},storage=new Map(),events=[];
const scope='https://example.test/app/';
const key=v=>new URL(typeof v==='string'?v:v.url,scope).href;
let failOptional=true;
const mediaResponse=path=>{
  const url=key(path);
  if(url.includes('narration-manifest'))return {entries:{}};
  if(url.includes('ambient-config'))return {schemaVersion:1,file:'Ambient/caverns.ogg'};
  if(url.includes('Backgrounds/manifest'))return {landscape:[]};
  return null;
};
const cache={
  async addAll(paths){for(const p of paths)storage.set(key(p),new Response('critical:'+p));},
  async add(path){
    if(failOptional&&String(path).includes('Death_Korps_gunner.png'))throw Error('storage quota exhausted');
    storage.set(key(path),new Response('static asset'));
  },
  async put(path,response){storage.set(key(path),response.clone());},
  async match(path){return storage.get(key(path))?.clone();},
  async keys(){return [...storage.keys()].map(url=>new Request(url));}
};
const context={
  URL,Request,Response,console,
  caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},
  fetch:async path=>{
    const data=mediaResponse(path);
    return new Response(data?JSON.stringify(data):'static media',{status:200});
  },
  self:{location:{origin:'https://example.test'},clients:{claim:async()=>{}},addEventListener:(name,handler)=>listeners[name]=handler}
};
vm.createContext(context);vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
const dispatch=async(type,data)=>{
  let pending;
  listeners[type]({data,source:{postMessage:event=>events.push(event)},waitUntil:p=>pending=p});
  if(pending)await pending;
};
(async()=>{
  await dispatch('install');
  assert(storage.has(key('./index.html')),'critical HTML missing');
  await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'});
  assert.equal(events.at(-1)?.type,'OFFLINE_INSTALL_ERROR');
  assert(!storage.has(key('./__offline-package-complete__')),'failed package falsely marked ready');
  assert(storage.has(key('./index.html')),'media failure removed app shell');
  failOptional=false;events.length=0;
  await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'});
  assert.equal(events.at(-1)?.type,'OFFLINE_INSTALL_COMPLETE');
  assert(storage.has(key('./__offline-package-complete__')));
  assert(storage.has(key('./Assets/Images/TombUI/DeathKorps/Death_Korps_gunner.png')));
  events.length=0;
  await dispatch('message',{type:'ENSURE_OFFLINE_PACKAGE'});
  assert.equal(events[0]?.type,'OFFLINE_PACKAGE_READY');
})().catch(e=>{console.error(e);process.exit(1)});
""")


def test_static_contract_version_and_no_saved_game_changes():
    assert "const CORE_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in WORKER
    assert "const OPTIONAL_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in WORKER
    assert "cache.addAll(CORE_PRECACHE_ASSETS)" in WORKER
    assert "cache.addAll(PRECACHE_ASSETS)" not in WORKER
    assert "archivedCacheMatch(request)" in WORKER
    assert "event.waitUntil(self.clients.claim());" in WORKER
    assert "V" + CURRENT_APP_VERSION in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
