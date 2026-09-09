(() => {
  'use strict';

  const MEASUREMENT_ID = 'G-JWESVY3VFE';
  const PRODUCTION_HOSTNAME = 'imthekeymaster.github.io';
  const PRODUCTION_PATH_PREFIX = '/TombWorldSoloGuide/';
  const location = window.location;
  const isProductionAnalyticsSite = location.protocol === 'https:'
    && location.hostname === PRODUCTION_HOSTNAME
    && location.pathname.startsWith(PRODUCTION_PATH_PREFIX);

  if (!isProductionAnalyticsSite || navigator.onLine === false || window.__tombWorldGa4Initialized) return;
  try {
    window.__tombWorldGa4Initialized = true;

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };

    const googleTag = document.createElement('script');
    googleTag.async = true;
    googleTag.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
    googleTag.onerror = () => {};
    document.head.appendChild(googleTag);

    window.gtag('js', new Date());
    window.gtag('config', MEASUREMENT_ID, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
  } catch {
    // Analytics is optional and must never affect Guide startup.
  }
})();
