(function (global) {
  'use strict';

  const CONFIG_URL = 'Assets/Audio/Narration/sfx-config.json';
  const AUDIO_ROOT_URL = 'Assets/Audio/Narration/';
  const AudioContext = global.AudioContext || global.webkitAudioContext;
  let context = null;
  let gainNode = null;
  let buffer = null;
  let initialization = null;

  function masterEnabled() {
    try { return global.TombWorldNarration?.isEnabled() !== false; } catch { return true; }
  }

  function validConfig(value) {
    return value?.schemaVersion === 1
      && typeof value.buttonClick === 'string'
      && /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))SFX\/[A-Za-z0-9._-]+\.wav$/i.test(value.buttonClick)
      && Number.isFinite(value.buttonClickGain) && value.buttonClickGain >= 0;
  }

  function ensureContext() {
    if (!context && AudioContext) {
      try { context = new AudioContext(); } catch { context = null; }
    }
    return context;
  }

  async function init() {
    if (initialization) return initialization;
    initialization = (async () => {
      if (!AudioContext || typeof global.fetch !== 'function') return false;
      try {
        const response = await global.fetch(CONFIG_URL);
        const config = response.ok ? await response.json() : null;
        if (!validConfig(config)) return false;
        const audioResponse = await global.fetch(new URL(config.buttonClick, new URL(AUDIO_ROOT_URL, global.location?.href || 'http://localhost/')).href);
        if (!audioResponse.ok) return false;
        ensureContext();
        gainNode = context.createGain();
        gainNode.gain.value = config.buttonClickGain;
        gainNode.connect(context.destination);
        buffer = await context.decodeAudioData(await audioResponse.arrayBuffer());
        return Boolean(buffer);
      } catch { return false; }
    })();
    return initialization;
  }

  async function unlock() {
    ensureContext();
    if (context?.state === 'suspended') {
      try { await context.resume(); } catch { /* A later user gesture can retry playback. */ }
    }
    void init();
    return context?.state === 'running';
  }

  async function play() {
    if (!masterEnabled()) return false;
    await unlock();
    if (!masterEnabled() || !await init() || context.state !== 'running') return false;
    try {
      const source = context.createBufferSource();
      source.buffer = buffer;
      source.connect(gainNode);
      source.onended = () => source.disconnect();
      source.start();
      return true;
    } catch { return false; }
  }

  function onDocumentClick(event) {
    if (!event.target || typeof event.target.closest !== 'function') return;
    const button = event.target.closest('button');
    if (!button || button.disabled) return;
    void play();
  }

  function onDocumentChange(event) {
    if (!event.target || typeof event.target.closest !== 'function') return;
    const select = event.target.closest('select');
    if (!select || select.disabled) return;
    void play();
  }

  global.document?.addEventListener?.('click', onDocumentClick);
  global.document?.addEventListener?.('change', onDocumentChange);
  global.TombWorldSfx = Object.freeze({ init, unlock, play });
})(typeof window === 'undefined' ? globalThis : window);
