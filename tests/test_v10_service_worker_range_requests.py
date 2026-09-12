import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_range_and_partial_response_guards_are_present():
    assert "response.status === 200" in WORKER
    assert "request.headers.has('range')" in WORKER
    assert "if (request.headers.has('range')) return fetch(request);" in WORKER
    assert "await cacheResponse(cache, request, response);" in WORKER


def test_audio_range_runtime_and_normal_asset_caching():
    script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},cached=new Map(),putRequests=[],fetchRequests=[];
let cacheOpenCount=0;
const cache={
  async addAll(){},
  async match(request){return cached.get(request.url)?.clone();},
  async put(request,response){
    putRequests.push(request);
    if(request.url.endsWith('uncacheable.mp3')||request.headers.has('range')||response.status===206)throw Error('cache write failed');
    cached.set(request.url,response.clone());
  }
};
const response=(body,status)=>{
  const value=new Response(body,{status});
  Object.defineProperty(value,'type',{value:'basic'});
  return value;
};
const context={URL,Request,Response,console,caches:{open:async()=>{cacheOpenCount+=1;return cache;}},
  fetch:async request=>{
    fetchRequests.push(request);
    if(request.url.endsWith('partial.mp3'))return response('part',206);
    if(request.headers.has('range'))return response('range',206);
    return response('complete',200);
  },
  self:{location:{origin:'https://example.test'},addEventListener:(type,fn)=>listeners[type]=fn}
};
vm.createContext(context);vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
async function dispatch(path,headers){
  const request=new Request('https://example.test/'+path,{headers});
  let responsePromise;
  listeners.fetch({request,respondWith:value=>responsePromise=value});
  if(!responsePromise)throw Error('fetch event was not handled for '+path);
  return responsePromise;
}
(async()=>{
  let response=await dispatch('complete.mp3');
  if(response.status!==200||!cached.has('https://example.test/complete.mp3'))throw Error('complete audio was not cached');

  response=await dispatch('partial.mp3');
  if(response.status!==206||putRequests.some(request=>request.url.endsWith('partial.mp3')))throw Error('partial response was cached');

  const cacheOpensBeforeRange=cacheOpenCount;
  const fetchesBeforeRange=fetchRequests.length;
  response=await dispatch('range.ogg',{'Range':'bytes=0-99'});
  if(response.status!==206||putRequests.some(request=>request.url.endsWith('range.ogg')))throw Error('range request was cached');
  if(cacheOpenCount!==cacheOpensBeforeRange||fetchRequests.length!==fetchesBeforeRange+1)throw Error('range request did not bypass the cache');

  response=await dispatch('uncacheable.mp3');
  if(response.status!==200)throw Error('cache write failure rejected a valid response');

  for(const path of ['app.js','styles.css','Missions/manifest.json']){
    response=await dispatch(path);
    if(response.status!==200||!cached.has('https://example.test/'+path))throw Error(path+' caching changed');
  }
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_offline_audio_precaching_remains_complete_response_based():
    assert "cache.addAll(PRECACHE_ASSETS)" in WORKER
    assert "./Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3" in WORKER
    assert "await cache.addAll(files);" in WORKER
    assert "await cacheMissingAsset(cache,file);" in WORKER
