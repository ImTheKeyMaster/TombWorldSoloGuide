(function (global) {
  'use strict';

  const CATEGORY_LABELS = Object.freeze({
    'mission-intro': 'MISSION BRIEFING',
    event: 'TOMB WORLD EVENT',
    grade: 'THREAT ESCALATION',
    outcome: 'MISSION OUTCOME',
    'deadly-encounter': 'DEADLY ENCOUNTER'
  });
  const AUTO_FOLLOW_SUSPEND_MS = 4000;
  const WORD_CLASS = 'narration-transcript-word';
  const WORD_STATE_CLASSES = Object.freeze({
    spoken: `${WORD_CLASS}--spoken`,
    current: `${WORD_CLASS}--current`,
    upcoming: `${WORD_CLASS}--upcoming`
  });
  let initialized = false;

  function formatTime(milliseconds) {
    const safeMilliseconds = Number.isFinite(Number(milliseconds)) && Number(milliseconds) > 0
      ? Number(milliseconds)
      : 0;
    const seconds = Math.floor(safeMilliseconds / 1000);
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  }

  function mapTranscriptWords(document, transcript, alignmentWords) {
    if (typeof transcript !== 'string' || !Array.isArray(alignmentWords) || !alignmentWords.length) return null;
    const nodes = [];
    const mappedWords = [];
    const lowerTranscript = transcript.toLocaleLowerCase();
    let cursor = 0;

    for (let index = 0; index < alignmentWords.length; index += 1) {
      const word = alignmentWords[index];
      const token = typeof word?.text === 'string' ? word.text : '';
      if (!token || /^\s+$/u.test(token)) continue;
      let matchIndex = transcript.indexOf(token, cursor);
      if (matchIndex < 0) matchIndex = lowerTranscript.indexOf(token.toLocaleLowerCase(), cursor);
      if (matchIndex < cursor || /[\p{L}\p{N}]/u.test(transcript.slice(cursor, matchIndex))) return null;
      if (matchIndex > cursor) nodes.push(document.createTextNode(transcript.slice(cursor, matchIndex)));
      const span = document.createElement('span');
      span.classList.add(WORD_CLASS, WORD_STATE_CLASSES.upcoming);
      span.dataset.wordIndex = String(index);
      span.textContent = transcript.slice(matchIndex, matchIndex + token.length);
      nodes.push(span);
      mappedWords.push({ element: span, startMs: Number(word.startMs), endMs: Number(word.endMs), alignmentIndex: index });
      cursor = matchIndex + token.length;
    }
    if (!mappedWords.length || mappedWords.some(word => !Number.isFinite(word.startMs) || !Number.isFinite(word.endMs))
        || /[\p{L}\p{N}]/u.test(transcript.slice(cursor))) return null;
    if (cursor < transcript.length) nodes.push(document.createTextNode(transcript.slice(cursor)));
    return { nodes, words: mappedWords };
  }

  function wordPositionAt(words, currentTimeMs) {
    let low = 0;
    let high = words.length;
    while (low < high) {
      const middle = (low + high) >> 1;
      if (words[middle].startMs <= currentTimeMs) low = middle + 1;
      else high = middle;
    }
    const candidate = low - 1;
    const current = candidate >= 0 && currentTimeMs < words[candidate].endMs ? candidate : -1;

    low = 0;
    high = words.length;
    while (low < high) {
      const middle = (low + high) >> 1;
      if (words[middle].endMs <= currentTimeMs) low = middle + 1;
      else high = middle;
    }
    return { current, spokenThrough: low - 1 };
  }

  function init() {
    if (initialized) return;
    const narration = global.TombWorldNarration;
    const dialog = global.document?.getElementById('narrationTranscriptDialog');
    const reopen = global.document?.getElementById('narrationTranscriptReopen');
    if (!narration || !dialog || !reopen) return;

    const category = global.document.getElementById('narrationTranscriptCategory');
    const body = global.document.getElementById('narrationTranscriptBody');
    const progress = global.document.getElementById('narrationTranscriptProgress');
    const progressFill = progress.querySelector('span');
    const time = global.document.getElementById('narrationTranscriptTime');
    const hide = global.document.getElementById('narrationTranscriptHide');
    const pause = global.document.getElementById('narrationTranscriptPause');
    const skip = global.document.getElementById('narrationTranscriptSkip');
    const stop = global.document.getElementById('narrationTranscriptStop');
    const pauseHelp = global.document.getElementById('narrationTranscriptPauseHelp');
    let hiddenForPlayback = false;
    let previousActive = false;
    let previousId = null;
    let previousFocus = null;
    let animationFrame = null;
    let renderedKey = null;
    let mappedTranscript = null;
    let currentWordIndex = -1;
    let spokenThroughIndex = -1;
    let previousCurrentTimeMs = null;
    let autoFollowSuspendedUntil = 0;
    let programmaticScrollUntil = 0;
    let lockedScrollY = 0;
    let previousBodyStyles = null;

    function dialogOpen() {
      return dialog.open === true;
    }

    function cancelProgressLoop() {
      if (animationFrame !== null) global.cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }

    function lockPageScroll() {
      const page = global.document.documentElement;
      const pageBody = global.document.body;
      if (!page || !pageBody || page.classList.contains('narration-transcript-open')) return;
      lockedScrollY = global.scrollY || page.scrollTop || 0;
      previousBodyStyles = {
        position: pageBody.style.position,
        top: pageBody.style.top,
        width: pageBody.style.width
      };
      page.classList.add('narration-transcript-open');
      pageBody.style.position = 'fixed';
      pageBody.style.top = `-${lockedScrollY}px`;
      pageBody.style.width = '100%';
    }

    function unlockPageScroll() {
      const page = global.document.documentElement;
      const pageBody = global.document.body;
      if (!page || !pageBody || !page.classList.contains('narration-transcript-open')) return;
      page.classList.remove('narration-transcript-open');
      pageBody.style.position = previousBodyStyles?.position || '';
      pageBody.style.top = previousBodyStyles?.top || '';
      pageBody.style.width = previousBodyStyles?.width || '';
      previousBodyStyles = null;
      global.scrollTo?.(0, lockedScrollY);
    }

    function updateProgress(state) {
      const currentTimeMs = Number.isFinite(Number(state.currentTimeMs)) && Number(state.currentTimeMs) > 0
        ? Number(state.currentTimeMs)
        : 0;
      const durationMs = Number.isFinite(Number(state.durationMs)) && Number(state.durationMs) > 0
        ? Number(state.durationMs)
        : 0;
      const ratio = durationMs ? Math.min(1, Math.max(0, currentTimeMs / durationMs)) : 0;
      const percent = Math.round(ratio * 100);
      progress.setAttribute('aria-valuenow', String(percent));
      progressFill.style.width = `${percent}%`;
      time.textContent = `${formatTime(currentTimeMs)} / ${formatTime(durationMs)}`;

      const masterDisabled = narration.isMasterEnabled?.() === false || state.pausedByMaster;
      pause.textContent = masterDisabled ? 'Paused' : (state.pausedByUser ? 'Resume' : 'Pause');
      pause.disabled = masterDisabled;
      if (masterDisabled) pause.setAttribute('aria-describedby', 'narrationTranscriptPauseHelp');
      else pause.removeAttribute('aria-describedby');
      pauseHelp.hidden = !masterDisabled;
    }

    function setWordState(index, state) {
      const element = mappedTranscript?.words[index]?.element;
      if (!element) return;
      element.classList.remove(WORD_STATE_CLASSES.spoken, WORD_STATE_CLASSES.current, WORD_STATE_CLASSES.upcoming);
      element.classList.add(WORD_STATE_CLASSES[state]);
    }

    function followCurrentWord(force = false) {
      const element = mappedTranscript?.words[currentWordIndex]?.element;
      if (!element || (!force && Date.now() < autoFollowSuspendedUntil) || !body.getBoundingClientRect) return;
      const viewport = body.getBoundingClientRect();
      const word = element.getBoundingClientRect();
      const safeTop = viewport.top + viewport.height * 0.25;
      const safeBottom = viewport.top + viewport.height * 0.75;
      if (!force && word.top >= safeTop && word.bottom <= safeBottom) return;
      const top = body.scrollTop + word.top - viewport.top - (viewport.height - word.height) / 2;
      programmaticScrollUntil = Date.now() + 800;
      const behavior = global.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
      if (typeof body.scrollTo === 'function') body.scrollTo({ top: Math.max(0, top), behavior });
      else body.scrollTop = Math.max(0, top);
    }

    function updateWordHighlighting(state, force = false) {
      if (!mappedTranscript || !dialogOpen()) return;
      const currentTimeMs = Number.isFinite(Number(state.currentTimeMs)) ? Math.max(0, Number(state.currentTimeMs)) : 0;
      const position = wordPositionAt(mappedTranscript.words, currentTimeMs);
      if (force || currentTimeMs < previousCurrentTimeMs) {
        mappedTranscript.words.forEach((word, index) => setWordState(index,
          index === position.current ? 'current' : (index <= position.spokenThrough ? 'spoken' : 'upcoming')));
      } else {
        if (currentWordIndex >= 0 && currentWordIndex !== position.current) {
          setWordState(currentWordIndex, currentWordIndex <= position.spokenThrough ? 'spoken' : 'upcoming');
        }
        if (position.spokenThrough > spokenThroughIndex) {
          for (let index = spokenThroughIndex + 1; index <= position.spokenThrough; index += 1) {
            if (index !== position.current) setWordState(index, 'spoken');
          }
        } else if (position.spokenThrough < spokenThroughIndex) {
          for (let index = position.spokenThrough + 1; index <= spokenThroughIndex; index += 1) {
            if (index !== position.current) setWordState(index, 'upcoming');
          }
        }
        if (position.current >= 0 && position.current !== currentWordIndex) setWordState(position.current, 'current');
      }
      const currentChanged = position.current !== currentWordIndex;
      const suspensionExpired = autoFollowSuspendedUntil && Date.now() >= autoFollowSuspendedUntil;
      currentWordIndex = position.current;
      spokenThroughIndex = position.spokenThrough;
      previousCurrentTimeMs = currentTimeMs;
      if (suspensionExpired) autoFollowSuspendedUntil = 0;
      if (currentWordIndex >= 0 && (force || currentChanged || suspensionExpired)) followCurrentWord(force);
    }

    function progressLoop() {
      animationFrame = null;
      const state = narration.getPlaybackState();
      if (!state.active || !dialogOpen()) return;
      updateProgress(state);
      updateWordHighlighting(state);
      animationFrame = global.requestAnimationFrame(progressLoop);
    }

    function startProgressLoop() {
      if (animationFrame === null && dialogOpen()) {
        animationFrame = global.requestAnimationFrame(progressLoop);
      }
    }

    function closeDialog(restoreToReopen) {
      cancelProgressLoop();
      if (dialogOpen()) dialog.close();
      unlockPageScroll();
      if (restoreToReopen) {
        reopen.hidden = false;
        reopen.focus();
      } else if (previousFocus?.isConnected && !previousFocus.hidden) {
        previousFocus.focus();
      }
    }

    function openDialog(state, resetScroll) {
      reopen.hidden = true;
      if (!dialogOpen()) {
        if (global.document.activeElement !== reopen) previousFocus = global.document.activeElement;
        lockPageScroll();
        dialog.showModal();
      }
      if (resetScroll) body.scrollTop = 0;
      updateProgress(state);
      updateWordHighlighting(state, true);
      startProgressLoop();
      hide.focus();
    }

    function renderTranscript(state) {
      category.textContent = CATEGORY_LABELS[state.category] || 'NARRATION';
      const transcript = state.transcriptAvailable
        ? state.transcript
        : (state.transcriptLoading ? 'Loading transcript…' : 'Transcript unavailable.');
      const key = `${state.id || ''}|${state.transcriptAvailable}|${state.transcriptLoading}|${String(transcript)}`;
      if (key === renderedKey) return;
      renderedKey = key;
      mappedTranscript = null;
      currentWordIndex = -1;
      spokenThroughIndex = -1;
      previousCurrentTimeMs = null;
      autoFollowSuspendedUntil = 0;
      const mapping = state.transcriptAvailable
        ? mapTranscriptWords(global.document, String(transcript), state.alignment?.words)
        : null;
      if (mapping) {
        mappedTranscript = mapping;
        body.replaceChildren(...mapping.nodes);
        return;
      }
      const paragraphs = String(transcript).split(/\n\s*\n/).map(text => {
        const paragraph = global.document.createElement('p');
        paragraph.textContent = text;
        return paragraph;
      });
      body.replaceChildren(...paragraphs);
    }

    function handleState(state = narration.getPlaybackState()) {
      const newPlayback = state.active && (!previousActive || state.id !== previousId);
      if (!state.active) {
        hiddenForPlayback = false;
        reopen.hidden = true;
        closeDialog(false);
        renderedKey = null;
        mappedTranscript = null;
      } else {
        renderTranscript(state);
        updateProgress(state);
        if (newPlayback) {
          hiddenForPlayback = false;
          openDialog(state, true);
        } else if (hiddenForPlayback) {
          reopen.hidden = false;
          cancelProgressLoop();
        } else if (dialogOpen()) {
          startProgressLoop();
        }
      }
      previousActive = state.active;
      previousId = state.id;
    }

    function hideTranscript() {
      const state = narration.getPlaybackState();
      hiddenForPlayback = state.active;
      closeDialog(state.active);
    }


    function suspendAutoFollow() {
      autoFollowSuspendedUntil = Date.now() + AUTO_FOLLOW_SUSPEND_MS;
    }

    hide.addEventListener('click', hideTranscript);
    dialog.addEventListener('close', unlockPageScroll);
    dialog.addEventListener('cancel', event => {
      event.preventDefault();
      hideTranscript();
    });
    reopen.addEventListener('click', () => {
      const state = narration.getPlaybackState();
      if (!state.active) return;
      hiddenForPlayback = false;
      openDialog(state, false);
    });
    body.addEventListener('wheel', suspendAutoFollow, { passive: true });
    body.addEventListener('touchstart', suspendAutoFollow, { passive: true });
    body.addEventListener('touchmove', suspendAutoFollow, { passive: true });
    body.addEventListener('pointerdown', suspendAutoFollow, { passive: true });
    body.addEventListener('scroll', () => {
      if (Date.now() >= programmaticScrollUntil) suspendAutoFollow();
    }, { passive: true });
    pause.addEventListener('click', async () => {
      const state = narration.getPlaybackState();
      if (!state.active || narration.isMasterEnabled?.() === false || state.pausedByMaster) return;
      if (state.pausedByUser) await narration.resumeNarration();
      else narration.pauseNarration();
      handleState();
    });
    skip.addEventListener('click', () => narration.skipCurrent());
    stop.addEventListener('click', () => narration.stop());
    global.addEventListener('tombworldnarrationstatechange', event => handleState(event.detail));
    global.addEventListener('pagehide', cancelProgressLoop, { once: true });
    initialized = true;
    handleState();
  }

  global.TombWorldNarrationTranscript = Object.freeze({ formatTime, mapTranscriptWords, wordPositionAt, init });
  if (global.document?.readyState === 'loading') global.document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})(typeof window === 'undefined' ? globalThis : window);
