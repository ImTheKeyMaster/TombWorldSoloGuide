(function (global) {
  'use strict';

  const CONFIG_URL = 'Assets/Audio/Narration/ambient-config.json';
  const AUDIO_ROOT_URL = 'Assets/Audio/Narration/';
  const AudioContext = global.AudioContext || global.webkitAudioContext;
  let context = null;
  let gainNode = null;
  let buffer = null;
  let config = null;
  let initialization = null;
  let source = null;
  let stopTimer = null;
  let contextUnlocked = false;
  let activeBattle = false;
  let narrationActive = false;
  let generation = 0;
  let gestureUnlocking = false;

  function ensureContext() {
    if (!context && AudioContext) context = new AudioContext();
    return context;
  }

  function masterEnabled() {
    try { return global.TombWorldNarration?.isEnabled() !== false; } catch { return true; }
  }

  function validConfig(value) {
    const file = value?.file;
    const gainsValid = ['normalGain', 'duckGain'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0);
    const timesValid = ['fadeInMs', 'fadeOutMs', 'duckAttackMs', 'duckReleaseMs'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0);
    return value?.schemaVersion === 1 && typeof file === 'string'
      && /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file)
      && gainsValid && timesValid && Number.isFinite(value.loopStartSeconds) && value.loopStartSeconds >= 0
      && (value.loopEndSeconds === null || (Number.isFinite(value.loopEndSeconds) && value.loopEndSeconds > value.loopStartSeconds));
  }

  async function init() {
    if (initialization) return initialization;
    const attempt = (async () => {
      if (!AudioContext || typeof global.fetch !== 'function') return false;
      try {
        const response = await global.fetch(CONFIG_URL);
        const value = response.ok ? await response.json() : null;
        if (!validConfig(value)) return false;
        const audioResponse = await global.fetch(new URL(value.file, new URL(AUDIO_ROOT_URL, global.location?.href || 'http://localhost/')).href);
        if (!audioResponse.ok) return false;
        const audioContext = ensureContext();
        const decodedBuffer = await audioContext.decodeAudioData(await audioResponse.arrayBuffer());
        const loopEnd = value.loopEndSeconds === null ? decodedBuffer.duration : value.loopEndSeconds;
        if (!(loopEnd > value.loopStartSeconds) || loopEnd > decodedBuffer.duration) return false;
        const ambientGain = audioContext.createGain();
        ambientGain.gain.value = 0;
        ambientGain.connect(audioContext.destination);
        buffer = decodedBuffer;
        gainNode = ambientGain;
        config = { ...value, loopEndSeconds: loopEnd };
        return true;
      } catch { return false; }
    })();
    initialization = attempt;
    const ready = await attempt;
    if (!ready && initialization === attempt) initialization = null;
    return ready;
  }

  function rampTo(value, milliseconds) {
    if (!context || !gainNode) return;
    const now = context.currentTime;
    const gain = gainNode.gain;
    gain.cancelScheduledValues(now);
    gain.setValueAtTime(gain.value, now);
    gain.linearRampToValueAtTime(value, now + milliseconds / 1000);
  }

  function stopSource(expectedGeneration, delayMs) {
    global.clearTimeout(stopTimer);
    stopTimer = global.setTimeout(() => {
      if (expectedGeneration !== generation || !source) return;
      try { source.stop(); } catch { /* The source may already have stopped. */ }
      source.disconnect();
      source = null;
      stopTimer = null;
    }, delayMs);
  }

  function fadeOutAndStop() {
    if (!source || !config) return;
    const expectedGeneration = generation;
    rampTo(0, config.fadeOutMs);
    stopSource(expectedGeneration, config.fadeOutMs + 25);
  }

  function startSource() {
    if (source || !context || !gainNode || !buffer || !config) return;
    global.clearTimeout(stopTimer);
    stopTimer = null;
    generation += 1;
    source = context.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    source.loopStart = config.loopStartSeconds;
    source.loopEnd = config.loopEndSeconds;
    source.connect(gainNode);
    gainNode.gain.cancelScheduledValues(context.currentTime);
    gainNode.gain.setValueAtTime(0, context.currentTime);
    source.start(0, config.loopStartSeconds);
    rampTo(narrationActive ? config.duckGain : config.normalGain, config.fadeInMs);
  }

  async function reconcile() {
    const token = generation;
    const ready = await init();
    if (!ready || token !== generation) return false;
    if (activeBattle && contextUnlocked && masterEnabled()) {
      if (context.state === 'suspended') {
        try { await context.resume(); } catch { return false; }
      }
      if (context.state !== 'running' || !activeBattle || !masterEnabled()) return false;
      if (source) {
        if (!stopTimer) return true;
        global.clearTimeout(stopTimer);
        stopTimer = null;
        generation += 1;
        rampTo(narrationActive ? config.duckGain : config.normalGain, config.fadeInMs);
      } else startSource();
      return Boolean(source);
    }
    fadeOutAndStop();
    return false;
  }

  async function unlock() {
    if (contextUnlocked && context?.state === 'running' && buffer && config && gainNode) return true;
    // Construct and resume from the shared click gesture for Safari/PWA audio permission.
    ensureContext();
    if (context?.state === 'suspended') {
      try { await context.resume(); } catch { /* Initialization below remains safely retryable. */ }
    }
    const ready = await init();
    if (!context) return false;
    if (context.state === 'suspended') {
      try { await context.resume(); } catch { /* A later user gesture may retry permission. */ }
    }
    contextUnlocked = context.state === 'running';
    if (contextUnlocked && ready) {
      global.document?.removeEventListener?.('click', onFirstAudioGesture, true);
      void reconcile();
    }
    return contextUnlocked && ready;
  }

  function setActive(isActive) {
    const nextActive = Boolean(isActive);
    if (nextActive === activeBattle) return;
    activeBattle = nextActive;
    void reconcile();
  }

  async function onFirstAudioGesture() {
    if ((contextUnlocked && buffer && config && gainNode) || gestureUnlocking) return;
    gestureUnlocking = true;
    try { await unlock(); } finally { gestureUnlocking = false; }
  }

  function stop() {
    activeBattle = false;
    generation += 1;
    global.clearTimeout(stopTimer);
    stopTimer = null;
    if (source) {
      rampTo(0, config?.fadeOutMs || 0);
      const oldSource = source;
      source = null;
      global.setTimeout(() => { try { oldSource.stop(); oldSource.disconnect(); } catch {} }, (config?.fadeOutMs || 0) + 25);
    }
  }

  function onNarrationActivity(event) {
    narrationActive = event.detail?.active === true;
    if (source && activeBattle && masterEnabled() && config) {
      rampTo(narrationActive ? config.duckGain : config.normalGain, narrationActive ? config.duckAttackMs : config.duckReleaseMs);
    }
  }

  function onMasterChange() { void reconcile(); }
  global.addEventListener?.('tombworldnarrationactivity', onNarrationActivity);
  global.addEventListener?.('tombworldnarrationchange', onMasterChange);
  global.document?.addEventListener?.('click', onFirstAudioGesture, true);

  global.TombWorldAmbient = Object.freeze({ init, unlock, setActive, stop });
})(typeof window === 'undefined' ? globalThis : window);
