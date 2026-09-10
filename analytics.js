(() => {
  'use strict';

  const CLOUDFLARE_TOKEN = 'a5fcae7597364071bb35e87f0789706b';
  const BEACON_URL = 'https://static.cloudflareinsights.com/beacon.min.js';
  const BEACON_ELEMENT_ID = 'tomb-world-cloudflare-analytics';
  const PRODUCTION_HOSTNAME = 'imthekeymaster.github.io';
  const PRODUCTION_PATH_PREFIX = '/TombWorldSoloGuide/';
  const location = window.location;
  const isProductionAnalyticsSite = location.protocol === 'https:'
    && location.hostname === PRODUCTION_HOSTNAME
    && location.pathname.startsWith(PRODUCTION_PATH_PREFIX);

  if (!isProductionAnalyticsSite || navigator.onLine === false || document.getElementById(BEACON_ELEMENT_ID)) return;
  try {
    const beacon = document.createElement('script');
    beacon.id = BEACON_ELEMENT_ID;
    beacon.type = 'module';
    beacon.src = BEACON_URL;
    beacon.setAttribute('data-cf-beacon', JSON.stringify({token:CLOUDFLARE_TOKEN}));
    beacon.onerror = () => {};
    document.head.appendChild(beacon);
  } catch {
    // Analytics is optional and must never affect Guide startup.
  }
})();
