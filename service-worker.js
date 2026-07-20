'use strict';

const APP_VERSION = '3.5.0';
const CACHE_PREFIX = 'tomb-world-solo-guide-';
const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;
const APP_SHELL = './index.html';
const PRECACHE_ASSETS = [
  './', APP_SHELL, `./app.js?v=${APP_VERSION}`, `./styles.css?v=${APP_VERSION}`,
  './manifest.webmanifest', './Assets/icon.svg',
  './Assets/Images/defeat.png', './Assets/Images/victory.png',
  './Assets/Maps/mission-01.png', './Assets/Maps/mission-02.png', './Assets/Maps/mission-03.png',
  './Assets/Maps/mission-04.png', './Assets/Maps/mission-05.png', './Assets/Maps/mission-06.png',
  './Assets/Tomb-World-Mission-Pack.pdf', './Missions/manifest.json',
  './Missions/01-shifting-labyrinth.json', './Missions/02-demolition-protocol.json',
  './Missions/03-recover-transponder.json', './Missions/04-destroy-sarcophagus.json',
  './Missions/05-scout-sub-crypt.json', './Missions/06-regroup.json',
  './Player_Operatives/manifest.json', './Player_Operatives/DeathKorps.json',
  './Player_Operatives/DeathWatch.json', './Player_Operatives/Kasrkin.json'
];

const canCache = response => response && response.ok && response.type === 'basic';

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_ASSETS)));
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
  if (/\.(?:png|svg|jpe?g|gif|webp|ico|pdf)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
  }
});
