'use strict';

const APP_VERSION = '9.2.38';
const CACHE_PREFIX = 'tomb-world-battle-guide-';
const LEGACY_CACHE_PREFIXES = ['tomb-world-solo-guide-'];
const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;
const APP_SHELL = './index.html';
const NARRATION_MANIFEST = './Assets/Audio/Narration/narration-manifest.json';
const AMBIENT_CONFIG = './Assets/Audio/Narration/ambient-config.json';
const BACKGROUND_MANIFEST = './Assets/Images/Backgrounds/manifest.json';
const OFFLINE_PACKAGE_MARKER = './__offline-package-complete__';
const PRECACHE_ASSETS = [
  './', APP_SHELL, `./event-effects.js?v=${APP_VERSION}`, `./audio-capabilities.js?v=${APP_VERSION}`, `./narration.js?v=${APP_VERSION}`, `./ambient.js?v=${APP_VERSION}`, `./dice-sfx.js?v=${APP_VERSION}`, `./app.js?v=${APP_VERSION}`, `./mission-engine.js?v=${APP_VERSION}`, `./persistence.js?v=${APP_VERSION}`, `./deadly-encounters.js?v=${APP_VERSION}`, `./styles.css?v=${APP_VERSION}`,
  './manifest.webmanifest', './Assets/icon.svg', './Assets/icon-180.png', './Assets/icon-192.png', './Assets/icon-512.png', './Assets/icon-1024.png', './Assets/Icons/move-to-shoot.svg', './Assets/Images/eliminated-necron-skull.png',
  './Assets/Images/defeat.png', './Assets/Images/victory.png',
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

const canCache = response => response && response.ok && response.type === 'basic';
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

function ambientFile(config) {
  const file=config?.file;
  if(config?.schemaVersion!==1||typeof file!=='string'||!/^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file))return null;
  return `./Assets/Audio/Narration/${file}`;
}

async function cacheJson(cache,path) {
  let response;
  try {
    response=await fetch(path,{cache:'no-store'});
    if(!response.ok)throw new Error(`${path} returned ${response.status}`);
    await cache.put(path,response.clone());
  } catch(error) {
    response=await cache.match(path);
    if(!response)throw error;
  }
  return response.json();
}

async function cacheMissingAsset(cache,path) {
  if(await cache.match(path))return;
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
  const ambient=ambientFile(ambientConfig);
  const backgrounds=(backgroundManifest.landscape||[]).map(filename=>`./Assets/Images/Backgrounds/${filename}`);
  if(!ambient)throw new Error('Ambient configuration does not identify a supported offline audio file.');
  const assets=[NARRATION_MANIFEST,AMBIENT_CONFIG,BACKGROUND_MANIFEST,...narration,ambient,...backgrounds];
  let completed=3;
  if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_START',completed,assets.length);
  const progress=()=>{
    completed+=1;
    if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_PROGRESS',completed,assets.length);
  };
  try {
    await precacheNarration(cache,narration,progress,true);
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
  if(reportProgress)reportOfflineInstall('OFFLINE_INSTALL_COMPLETE',assets.length,assets.length);
}

async function ensureOfflinePackage() {
  const cache=await caches.open(CACHE_NAME);
  const marker=await cache.match(OFFLINE_PACKAGE_MARKER);
  if(marker){
    offlinePreparationStatus={type:'OFFLINE_PACKAGE_READY'};
    offlinePreparationClients.forEach(client=>postOfflineMessage(client,offlinePreparationStatus));
    const markerVersion=await marker.text();
    if(markerVersion===APP_VERSION)return;
    try {
      await prepareOfflinePackage({reportProgress:false});
    } catch(error) {
      console.warn('Updated offline media will be checked again on the next standalone launch.',error);
    }
    return;
  }
  await prepareOfflinePackage();
}

async function copyExtendedAssetsFromOldCaches(names) {
  const destination=await caches.open(CACHE_NAME);
  for(const name of names.filter(name=>isTombWorldCache(name)&&name!==CACHE_NAME)){
    try {
      const source=await caches.open(name);
      for(const request of await source.keys()){
        const pathname=new URL(request.url).pathname;
        const isExtended=pathname.includes('/Assets/Audio/Narration/')||pathname.includes('/Assets/Images/Backgrounds/')||pathname.endsWith('/__offline-package-complete__');
        if(!isExtended||await destination.match(request))continue;
        const response=await source.match(request);
        if(response)await destination.put(request,response);
      }
    } catch(error) {
      console.warn(`Offline media could not be reused from cache "${name}".`,error);
    }
  }
}

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(PRECACHE_ASSETS)));
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const names=await caches.keys();
    await copyExtendedAssetsFromOldCaches(names);
    await Promise.all(names.filter(name=>isTombWorldCache(name)&&name!==CACHE_NAME).map(name=>caches.delete(name)));
    await self.clients.claim();
  })());
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

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (!response.ok) return cachedFallback(cache, request, response);
    if (canCache(response)) await cache.put(request, response.clone());
    return response;
  } catch {
    return cachedFallback(cache, request);
  }
}

async function cachedFallback(cache, request, failedResponse) {
  const cached = await cache.match(request);
  if (cached) return cached;
  if (request.mode === 'navigate' || new URL(request.url).pathname.endsWith('/index.html')) {
    return (await cache.match(APP_SHELL)) || failedResponse || Response.error();
  }
  return failedResponse || Response.error();
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (canCache(response)) await cache.put(request, response.clone());
  return response;
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (request.mode === 'navigate' || url.pathname.endsWith('/index.html')) {
    event.respondWith(networkFirst(request));
    return;
  }
  if (/\.(?:js|css|json|webmanifest)$/i.test(url.pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }
  if (/\.(?:png|svg|jpe?g|gif|webp|ico|pdf|mp3|ogg)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
  }
});
