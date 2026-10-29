'use strict';

const APP_VERSION = '10.1.1';
const CACHE_PREFIX = 'tomb-world-battle-guide-';
const LEGACY_CACHE_PREFIXES = ['tomb-world-solo-guide-'];
const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;
const APP_SHELL = './index.html';
const NARRATION_MANIFEST = './Assets/Audio/Narration/narration-manifest.json';
const AMBIENT_CONFIG = './Assets/Audio/Narration/ambient-config.json';
const BACKGROUND_MANIFEST = './Assets/Images/Backgrounds/manifest.json';
const OFFLINE_PACKAGE_MARKER = './__offline-package-complete__';
const PRECACHE_ASSETS = [
  './', APP_SHELL, `./analytics.js?release=${APP_VERSION}`, `./event-effects.js?v=${APP_VERSION}`, `./audio-capabilities.js?v=${APP_VERSION}`, `./narration.js?v=${APP_VERSION}`, `./narration-transcript.js?v=${APP_VERSION}`, `./ambient.js?v=${APP_VERSION}`, `./dice-sfx.js?v=${APP_VERSION}`, `./app.js?v=${APP_VERSION}`, `./fight-portrait-scale.js?v=${APP_VERSION}`, `./mission-engine.js?v=${APP_VERSION}`, `./persistence.js?v=${APP_VERSION}`, `./deadly-encounters.js?v=${APP_VERSION}`, `./styles.css?v=${APP_VERSION}`,
  './manifest.webmanifest', './Assets/favicon.ico', './Assets/icon-180.png', './Assets/icon-192.png', './Assets/icon-512.png', './Assets/icon-1024.png', './Assets/icon-maskable-192.png', './Assets/icon-maskable-512.png', './Assets/Icons/move-to-shoot.svg', './Assets/Images/eliminated-necron-skull.png',
  './Assets/Images/defeat.png', './Assets/Images/victory.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_aegis.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_blademaster.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_bombard.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_breacher.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_demolisher.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_disruptor.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_gunner.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_headtake.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_horder-slayer.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_marksman.png',
  './Assets/Images/TombUI/Deathwatch/Deathwatch_sergeant.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_bruiser.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_confidant.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_gunner_flamer.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_gunner-meltagun.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_gunner_grenade.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_gunner_plasma.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_medic.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_sniper.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_3.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_4.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_5.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_vox-operator_2.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_sapper.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_spotter.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_1.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_trooper_2.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_veteran.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_vox_operator.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_zealot.png',
  './Assets/Images/TombUI/DeathKorps/Death_Korps_watchmaster.png',
  `./Assets/Images/TombUI/NecronActivation/canoptek-macrocyte-accelerator.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-macrocyte-reanimator.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-macrocyte-warrior-1.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-macrocyte-warrior-2.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-macrocyte-warrior-3.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-scarab-swarm.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-tomb-crawler-1.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/canoptek-tomb-crawler-2.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/geomancer.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/necron-warrior-gauss-flayer.webp?v=${APP_VERSION}`,
  `./Assets/Images/TombUI/NecronActivation/necron-warrior-gauss-reaper.webp?v=${APP_VERSION}`,
  './Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3',
  `./Assets/Maps/mission-01.png?v=${APP_VERSION}`, `./Assets/Maps/mission-02.png?v=${APP_VERSION}`, `./Assets/Maps/mission-03.png?v=${APP_VERSION}`,
  `./Assets/Maps/mission-04.png?v=${APP_VERSION}`, `./Assets/Maps/mission-05.png?v=${APP_VERSION}`, `./Assets/Maps/mission-06.png?v=${APP_VERSION}`,
  './Missions/manifest.json',
  './Missions/mission.schema.json', './Missions/definition-01-shifting-labyrinth.json', './Missions/definition-02-demolition-protocol.json', './Missions/definition-03-recover-transponder.json', './Missions/definition-04-destroy-sarcophagus.json', './Missions/definition-05-scout-sub-crypt.json',
  './Missions/01-shifting-labyrinth.json', './Missions/02-demolition-protocol.json',
  './Missions/03-recover-transponder.json', './Missions/04-destroy-sarcophagus.json',
  './Missions/05-scout-sub-crypt.json', './Missions/06-regroup.json',
  './Player_Operatives/manifest.json', './Player_Operatives/DeathKorps.json',
  './Player_Operatives/DeathWatch.json', './Player_Operatives/Kasrkin.json', './Player_Operatives/TempestusAquilons.json', './Player_Operatives/SpectreSquad.json', './Player_Operatives/ScoutSquad.json'
];

// Cache the bootable app and game data before attempting larger images or audio.
// iOS can reject a single large Cache.addAll() update under storage pressure.
const CORE_PRECACHE_ASSETS=PRECACHE_ASSETS.filter(path=>!/\.(?:png|svg|jpe?g|gif|webp|ico|mp3|ogg)(?:\?|$)/i.test(path));
const OPTIONAL_PRECACHE_ASSETS=PRECACHE_ASSETS.filter(path=>!CORE_PRECACHE_ASSETS.includes(path));

const canCache = response => response && response.status === 200 && response.type === 'basic';
const isTombWorldCache = name => name.startsWith(CACHE_PREFIX) || LEGACY_CACHE_PREFIXES.some(prefix => name.startsWith(prefix));
const installPercent = (completed, total) => Math.min(100, Math.max(0, Math.round((completed / total) * 100)));
let offlinePreparationPromise=null;
const offlinePreparationClients=new Set();
let offlinePreparationStatus=null;

function postOfflineMessage(client,message) {
  try {
    client?.postMessage(message);
  } catch(error) {
    console.warn('Offline preparation status could not be reported to a client.',error);
  }
}

function reportOfflineInstall(type, completed, total) {
  const percent=type==='OFFLINE_INSTALL_COMPLETE'?100:installPercent(completed,total);
  offlinePreparationStatus={type,completed,total,percent};
  offlinePreparationClients.forEach(client=>postOfflineMessage(client,offlinePreparationStatus));
}

function narrationFiles(manifest) {
  const files=Object.values(manifest.entries||{})
    .filter(entry=>entry?.available===true&&typeof entry.file==='string'&&/^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$)).+\.mp3$/i.test(entry.file))
    .map(entry=>`./Assets/Audio/Narration/${entry.file}`);
  return [...new Set(files)];
}

function narrationAlignmentFiles(manifest) {
  const files=Object.entries(manifest.entries||{})
    .filter(([id,entry])=>entry?.available===true&&typeof id==='string')
    .map(([id])=>`./Assets/Audio/Narration/alignment/${id.replace(/[^A-Za-z0-9._-]/g,'_')}.json`);
  return [...new Set(files)];
}

function ambientFile(config) {
  const file=config?.file;
  if(config?.schemaVersion!==1||typeof file!=='string'||!/^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file))return null;
  return `./Assets/Audio/Narration/${file}`;
}

async function archivedCacheEntry(request) {
  for(const name of (await caches.keys()).filter(name=>isTombWorldCache(name)&&name!==CACHE_NAME).reverse()){
    const cache=await caches.open(name);
    const response=await cache.match(request,{ignoreSearch:true});
    if(response)return {cache,response};
  }
  return null;
}
async function archivedCacheMatch(request) {
  return (await archivedCacheEntry(request))?.response||null;
}
async function cleanSupersededCaches() {
  const names=await caches.keys();
  await Promise.all(names.filter(name=>isTombWorldCache(name)&&name!==CACHE_NAME).map(name=>caches.delete(name)));
}

async function cacheJson(cache,path) {
  let response;
  try {
    response=await fetch(path,{cache:'no-store'});
    if(!response.ok)throw new Error(`${path} returned ${response.status}`);
    await cache.put(path,response.clone());
  } catch(error) {
    response=await cache.match(path)||await archivedCacheMatch(path);
    if(!response)throw error;
    // The new package must own its manifests before older caches can be pruned.
    await cache.put(path,response.clone());
  }
  return response.json();
}

async function cacheMissingAsset(cache,path) {
  if(await cache.match(path))return;
  // A new versioned map/portrait must be fetched fresh, never silently replaced
  // by an old image whose only matching URL differs by ?v=.
  if(!/[?&](?:v|release)=/.test(path)){
    const archived=await archivedCacheEntry(path);
    if(archived){
      await cache.put(path,archived.response.clone());
      // Move unversioned media rather than duplicating entire audio libraries.
      await archived.cache.delete(path,{ignoreSearch:true});
      return;
    }
  }
  await cache.add(path);
}

async function precacheNarration(cache,files,onProgress,strict=false) {
  try {
    if(!files){
      const response=await cache.match(NARRATION_MANIFEST);
      files=narrationFiles(await response.json());
      if(files.length)await cache.addAll(files);
      return;
    }
    for(const file of files){
      await cacheMissingAsset(cache,file);
      onProgress?.();
    }
  } catch(error) {
    console.warn('Narration precache skipped because its manifest could not be read.',error);
    if(strict)throw error;
  }
}

async function precacheAmbient(cache,file,onProgress,strict=false) {
  try {
    if(!file){
      const response=await cache.match(AMBIENT_CONFIG);
      file=ambientFile(await response.json());
    }
    if(file)await cacheMissingAsset(cache,file);
    onProgress?.();
  } catch(error) {
    console.warn('Ambient precache skipped because its configuration could not be read.',error);
    if(strict)throw error;
  }
}

async function prepareOfflinePackage({reportProgress=true}={}) {
  const cache=await caches.open(CACHE_NAME);
  let narrationManifest,ambientConfig,backgroundManifest;
  try {
    [narrationManifest,ambientConfig,backgroundManifest]=await Promise.all([
      cacheJson(cache,NARRATION_MANIFEST),cacheJson(cache,AMBIENT_CONFIG),cacheJson(cache,BACKGROUND_MANIFEST)
    ]);
  } catch(error) {
    console.warn('Offline media manifests could not be prepared.',error);
    throw error;
  }
  const narration=narrationFiles(narrationManifest);
  const alignments=narrationAlignmentFiles(narrationManifest);
  const ambient=ambientFile(ambientConfig);
  const backgrounds=(backgroundManifest.landscape||[]).map(filename=>`./Assets/Images/Backgrounds/${filename}`);
  if(!ambient)throw new Error('Ambient configuration does not identify a supported offline audio file.');
  const assets=[...OPTIONAL_PRECACHE_ASSETS,NARRATION_MANIFEST,AMBIENT_CONFIG,BACKGROUND_MANIFEST,...narration,...alignments,ambient,...backgrounds];
  let completed=3;
  if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_START',completed,assets.length);
  const progress=()=>{
    completed+=1;
    if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_PROGRESS',completed,assets.length);
  };
  try {
    for(const asset of OPTIONAL_PRECACHE_ASSETS){
      await cacheMissingAsset(cache,asset);
      progress();
    }
    await precacheNarration(cache,narration,progress,true);
    await precacheNarration(cache,alignments,progress,true);
    await precacheAmbient(cache,ambient,progress,true);
    for(const asset of backgrounds){
      await cacheMissingAsset(cache,asset);
      progress();
    }
  } catch(error) {
    console.warn('Standalone offline media preparation could not be completed.',error);
    throw error;
  }
  await cache.put(OFFLINE_PACKAGE_MARKER,new Response(APP_VERSION,{headers:{'Content-Type':'text/plain'}}));
  try{await cleanSupersededCaches();}catch(error){console.warn('Old offline caches could not be cleaned up.',error);}
  if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_COMPLETE',assets.length,assets.length);
}

async function ensureOfflinePackage() {
  const cache=await caches.open(CACHE_NAME);
  const marker=await cache.match(OFFLINE_PACKAGE_MARKER);
  if(marker){
    const markerVersion=await marker.text();
    if(markerVersion===APP_VERSION){
      try{await cleanSupersededCaches();}catch(error){console.warn('Old offline caches could not be cleaned up.',error);}
      offlinePreparationStatus={type:'OFFLINE_PACKAGE_READY'};
      offlinePreparationClients.forEach(client=>postOfflineMessage(client,offlinePreparationStatus));
      return;
    }
  }
  await prepareOfflinePackage();
}

self.addEventListener('install',event=>{
  // A single failed large image must never prevent the offline app shell installing.
  event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(CORE_PRECACHE_ASSETS)));
});

self.addEventListener('activate',event=>{
  // Keep previous caches as fallbacks until an offline package can be rebuilt.
  // Deleting them here can strand an iPhone with a blank screen after an update.
  event.waitUntil(self.clients.claim());
});

self.addEventListener('message',event=>{
  if(event.data?.type==='SKIP_WAITING'){
    self.skipWaiting();
    return;
  }
  if(event.data?.type!=='ENSURE_OFFLINE_PACKAGE')return;
  if(event.source)offlinePreparationClients.add(event.source);
  if(offlinePreparationPromise){
    if(offlinePreparationStatus)postOfflineMessage(event.source,offlinePreparationStatus);
    event.waitUntil?.(offlinePreparationPromise);
    return;
  }
  offlinePreparationStatus=null;
  offlinePreparationPromise=ensureOfflinePackage()
    .catch(error=>offlinePreparationClients.forEach(client=>postOfflineMessage(client,{type:'OFFLINE_INSTALL_ERROR',message:'Offline setup could not be completed. It will be retried next time.'})))
    .finally(()=>{
      offlinePreparationPromise=null;
      offlinePreparationStatus=null;
      offlinePreparationClients.clear();
    });
  event.waitUntil?.(offlinePreparationPromise);
});

// A cold-start PWA must never wait on the network for a shell already stored
// on-device. The next release is fetched by the browser's service-worker
// update check, not by blocking the current app's startup.
async function archivedCacheMatchExact(request) {
  for(const name of (await caches.keys()).filter(name=>isTombWorldCache(name)&&name!==CACHE_NAME).reverse()) {
    const archived=await caches.open(name);
    const response=await archived.match(request);
    if(response)return response;
  }
  return null;
}
async function fetchWithStartupTimeout(request,timeoutMs=4500) {
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const response=await fetch(request,{signal:controller.signal});
    if(!response.ok)return response;
    // A weak cellular connection can deliver headers but hang on the body.
    // Keep the abort deadline active until the whole asset has arrived.
    const body=await response.blob();
    return new Response(body,{status:response.status,statusText:response.statusText,headers:response.headers});
  }finally{clearTimeout(timeout);}
}
const OFFLINE_STARTUP_HTML=`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#07140f">
<title>Tomb World Guide · Offline</title>
<style>html,body{margin:0;min-height:100%;background:#06100c;color:#e3f2e9;font:16px system-ui,sans-serif}
main{box-sizing:border-box;max-width:520px;margin:12vh auto;padding:28px 22px}
h1{font-size:1.5rem}p{line-height:1.5;color:#bad0c1}
button{background:#6ef0a6;color:#062012;border:0;border-radius:12px;padding:14px 22px;font-weight:750;font-size:1rem}</style>
</head><body><main><h1>Tomb World Guide</h1>
<p>The offline app files are not yet available on this device. Connect to Wi-Fi or cellular data, then retry. Your saved battle has not been deleted.</p>
<button onclick="location.reload()">Retry Loading</button></main></body></html>`;
function offlineStartupResponse() {
  return new Response(OFFLINE_STARTUP_HTML,{status:503,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}});
}
async function offlineFirstNavigation(request) {
  const cache=await caches.open(CACHE_NAME);
  const cached=await cache.match(request)||await cache.match(APP_SHELL)
    ||await archivedCacheMatch(request)||await archivedCacheMatch(APP_SHELL);
  if(cached)return cached;
  try{
    const response=await fetchWithStartupTimeout(request);
    if(!response.ok)return offlineStartupResponse();
    await cacheResponse(cache,request,response);
    return response;
  }catch(error){
    console.warn('[Offline startup] App shell not cached and network unavailable.',error);
    return offlineStartupResponse();
  }
}
async function offlineFirstCodeAndData(request) {
  const cache=await caches.open(CACHE_NAME);
  // Exact request URLs matter. Never mix JavaScript/CSS from a previous
  // release simply because the filename matches after stripping ?v=.
  const cached=await cache.match(request)||await archivedCacheMatchExact(request);
  if(cached)return cached;
  try{
    const response=await fetchWithStartupTimeout(request);
    if(!response.ok)return response;
    await cacheResponse(cache,request,response);
    return response;
  }catch(error){
    console.warn('[Offline startup] A required script or data file was unavailable.',request.url,error);
    return Response.error();
  }
}

async function cacheResponse(cache, request, response) {
  if (request.headers.has('range') || !canCache(response)) return;
  try {
    await cache.put(request, response.clone());
  } catch(error) {
    console.warn('Network response could not be cached.',error);
  }
}

async function cachedFallback(cache, request, failedResponse) {
  const cached = await cache.match(request);
  if (cached) return cached;
  if (request.mode === 'navigate' || new URL(request.url).pathname.endsWith('/index.html')) {
    return (await cache.match(APP_SHELL)) || await archivedCacheMatch(APP_SHELL) || failedResponse || Response.error();
  }
  const archived=await archivedCacheMatch(request);
  if(archived)return archived;
  return failedResponse || Response.error();
}

async function cacheFirst(request) {
  if (request.headers.has('range')) return fetch(request);
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;
  // Versioned artwork may have changed. Try the current version first,
  // falling back to old offline imagery only when the network is unavailable.
  if(/[?&](?:v|release)=/.test(request.url)){
    try{
      const response=await fetch(request);
      if(response.ok){await cacheResponse(cache,request,response);return response;}
    }catch{}
  }
  const archived=await archivedCacheMatch(request);
  if(archived)return archived;
  const response=await fetch(request);
  await cacheResponse(cache, request, response);
  return response;
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Reference PDFs are hosted online but must not be included in the PWA cache.
  if (/\.pdf$/i.test(url.pathname)) return;
  if (request.mode === 'navigate' || url.pathname.endsWith('/index.html')) {
    event.respondWith(offlineFirstNavigation(request));
    return;
  }
  if (/\.(?:js|css|json|webmanifest)$/i.test(url.pathname)) {
    event.respondWith(offlineFirstCodeAndData(request));
    return;
  }
  if (/\.(?:png|svg|jpe?g|gif|webp|ico|mp3|ogg)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
  }
});
