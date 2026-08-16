(function (global) {
  'use strict';

  function isAppleMobilePlatform() {
    const navigator = global.navigator || {};
    const platform = String(navigator.platform || '');
    const userAgent = String(navigator.userAgent || '');
    return /iPhone|iPad|iPod/i.test(platform + ' ' + userAgent)
      || (/Mac/i.test(platform) && Number(navigator.maxTouchPoints || 0) > 1);
  }

  function supportsInAppVolumeControl() {
    return !isAppleMobilePlatform();
  }

  global.TombWorldAudioCapabilities = Object.freeze({ supportsInAppVolumeControl });
})(typeof window === 'undefined' ? globalThis : window);
