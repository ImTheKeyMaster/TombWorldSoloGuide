'use strict';

const APP_VERSION = '8.6.99';
const CACHE_PREFIX = 'tomb-world-solo-guide-';
const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;
const APP_SHELL = './index.html';
const NARRATION_MANIFEST = './Assets/Audio/Narration/narration-manifest.json';
const AMBIENT_CONFIG = './Assets/Audio/Narration/ambient-config.json';
const PRECACHE_ASSETS = [
  './', APP_SHELL, `./event-effects.js?v=${APP_VERSION}`, `./audio-capabilities.js?v=${APP_VERSION}`, `./narration.js?v=${APP_VERSION}`, `./ambient.js?v=${APP_VERSION}`, `./app.js?v=${APP_VERSION}`, `./mission-engine.js?v=${APP_VERSION}`, `./persistence.js?v=${APP_VERSION}`, `./deadly-encounters.js?v=${APP_VERSION}`, `./styles.css?v=${APP_VERSION}`,
  './manifest.webmanifest', './Assets/icon.svg', './Assets/Icons/move-to-shoot.svg',
  './Assets/Images/Backgrounds/manifest.json',
  './Assets/Images/defeat.png', './Assets/Images/victory.png',
  './Assets/Maps/mission-01.png', './Assets/Maps/mission-02.png', './Assets/Maps/mission-03.png',
  './Assets/Maps/mission-04.png', './Assets/Maps/mission-05.png', './Assets/Maps/mission-06.png',
  './Assets/Tomb-World-Mission-Pack.pdf', './Missions/manifest.json',
  './Missions/mission.schema.json', './Missions/definition-01-shifting-labyrinth.json', './Missions/definition-02-demolition-protocol.json', './Missions/definition-03-recover-transponder.json', './Missions/definition-04-destroy-sarcophagus.json', './Missions/definition-05-scout-sub-crypt.json',
  './Missions/01-shifting-labyrinth.json', './Missions/02-demolition-protocol.json',
  './Missions/03-recover-transponder.json', './Missions/04-destroy-sarcophagus.json',
  './Missions/05-scout-sub-crypt.json', './Missions/06-regroup.json',
  './Player_Operatives/manifest.json', './Player_Operatives/DeathKorps.json',
  './Player_Operatives/DeathWatch.json', './Player_Operatives/Kasrkin.json', './Player_Operatives/TempestusAquilons.json', './Player_Operatives/SpectreSquad.json', './Player_Operatives/ScoutSquad.json'
];

const canCache = response => response && response.ok && response.type === 'basic';

async function precacheNarration(cache) {
  try {
    const response=await cache.match(NARRATION_MANIFEST);
    const manifest=await response.json();
    const files=Object.values(manifest.entries||{})
      .filter(entry=>entry?.available===true&&typeof entry.file==='string'&&/^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$)).+\.mp3$/i.test(entry.file))
      .map(entry=>`./Assets/Audio/Narration/${entry.file}`);
    const uniqueFiles=[...new Set(files)];
    if(uniqueFiles.length)await cache.addAll(uniqueFiles);
  } catch (error) {
    console.warn('Narration precache skipped because its manifest could not be read.',error);
  }
}

async function precacheAmbient(cache) {
  try {
    const response = await cache.match(AMBIENT_CONFIG);
    const config = await response.json();
    const file = config?.file;
    if (config?.schemaVersion !== 1 || typeof file !== 'string' || !/^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file)) return;
    await cache.add(`./Assets/Audio/Narration/${file}`);
  } catch (error) {
    console.warn('Ambient precache skipped because its configuration could not be read.', error);
  }
}

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(async cache => {
    await cache.addAll(PRECACHE_ASSETS);
    try {
      await cache.add(NARRATION_MANIFEST);
    } catch (error) {
      console.warn('Narration manifest precache failed; the app shell remains available offline.',error);
    }
    await precacheNarration(cache);
    try {
      await cache.add(AMBIENT_CONFIG);
      await precacheAmbient(cache);
    } catch (error) {
      console.warn('Ambient configuration precache failed; gameplay and narration remain available offline.', error);
    }
    const response=await cache.match('./Assets/Images/Backgrounds/manifest.json');
    const manifest=await response.json();
    const backgrounds=(manifest.landscape||[]).map(filename=>`./Assets/Images/Backgrounds/${filename}`);
    await cache.addAll(backgrounds);
  }));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(names
        .filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
        .map(name => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
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
