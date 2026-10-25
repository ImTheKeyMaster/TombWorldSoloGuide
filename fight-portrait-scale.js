/* Shared real-base-scale portrait framing for Tomb Fight Resolution / Result. */
(() => {
  'use strict';

  const MAX_FIGURE_HEIGHT_RATIO = 0.90;
  const SAMPLE_LIMIT = 256;
  const ALPHA_THRESHOLD = 32;
  const measurements = new Map();
  let observer = null;
  let currentPair = null;

  // Work in the same downsampled pixel coordinates for all factions. Measuring
  // the base *inside* the alpha cutout avoids equating PNG/WebP file dimensions.
  function analyzePixels(data, width, height) {
    let top = height, bottom = -1, left = width, right = -1;
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (data[(y * width + x) * 4 + 3] < ALPHA_THRESHOLD) continue;
        top = Math.min(top, y);
        bottom = Math.max(bottom, y);
        left = Math.min(left, x);
        right = Math.max(right, x);
      }
    }
    if (bottom < top) return null;
    const figureHeight = bottom - top + 1;
    // The lower 2%-18% of the silhouette covers the miniature's base.
    // Use its widest contiguous opaque run, ignoring disconnected tails.
    const firstRow = Math.max(top, bottom - Math.ceil(figureHeight * .18));
    const lastRow = Math.max(firstRow, bottom - Math.floor(figureHeight * .02));
    let baseLeft = -1, baseRight = -1, baseWidth = 0;
    for (let y = firstRow; y <= lastRow; y++) {
      let start = -1;
      for (let x = left; x <= right + 1; x++) {
        const solid = x <= right && data[(y * width + x) * 4 + 3] >= ALPHA_THRESHOLD;
        if (solid && start < 0) start = x;
        if (!solid && start >= 0) {
          const run = x - start;
          if (run > baseWidth) {
            baseWidth = run;
            baseLeft = start;
            baseRight = x - 1;
          }
          start = -1;
        }
      }
    }
    // Do not apply a guessed base scale when an artwork lacks a visible base.
    if (baseWidth < Math.max(5, (right - left + 1) * .16)) return null;
    return {
      width, height, top, bottom, left, right, baseWidth,
      baseCenter: (baseLeft + baseRight) / 2,
      figureHeight
    };
  }

  function measureImage(img) {
    if (!img.complete || !img.naturalWidth || !img.naturalHeight) return null;
    const key = img.currentSrc || img.src;
    if (measurements.has(key)) return measurements.get(key);
    let result = null;
    try {
      const scale = Math.min(1, SAMPLE_LIMIT / Math.max(img.naturalWidth, img.naturalHeight));
      const width = Math.max(1, Math.round(img.naturalWidth * scale));
      const height = Math.max(1, Math.round(img.naturalHeight * scale));
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d', { willReadFrequently: true });
      if (!context) return null;
      context.drawImage(img, 0, 0, width, height);
      result = analyzePixels(context.getImageData(0, 0, width, height).data, width, height);
    } catch (error) {
      // Security restrictions, incomplete images or unsupported canvas are
      // allowed to fall back to the previously approved static portrait CSS.
      console.warn('[Fight portrait] Could not measure image.', error);
    }
    if (key) measurements.set(key, result);
    return result;
  }

  // A single common pixels-per-mm scale for both miniatures. The physically
  // taller figure is 90% of the shorter pill/card; the other retains its
  // authentic relative height and base diameter (e.g. 25mm vs 28mm).
  function calculatePair(items, cardHeight) {
    if (items.length !== 2 || !(cardHeight > 0)) return null;
    if (items.some(({baseMm, geometry}) => !(baseMm > 0) ||
      !geometry || !(geometry.baseWidth > 0) || !(geometry.figureHeight > 0))) return null;
    const heightsMm = items.map(({baseMm, geometry}) =>
      geometry.figureHeight * baseMm / geometry.baseWidth);
    const tallestMm = Math.max(...heightsMm);
    const pixelsPerMm = cardHeight * MAX_FIGURE_HEIGHT_RATIO / tallestMm;
    return items.map(({baseMm, geometry}, i) => {
      const pxPerSamplePixel = pixelsPerMm * baseMm / geometry.baseWidth;
      return {
        imageWidth: geometry.width * pxPerSamplePixel,
        imageHeight: geometry.height * pxPerSamplePixel,
        baseCenter: geometry.baseCenter * pxPerSamplePixel,
        transparentBottom: (geometry.height - 1 - geometry.bottom) * pxPerSamplePixel,
        figureHeight: heightsMm[i] * pixelsPerMm,
        baseDiameter: baseMm * pixelsPerMm
      };
    });
  }

  function mount(root) {
    if (observer) { observer.disconnect(); observer = null; }
    currentPair = null;
    if (!root || !root.querySelector) return;
    const container = root.querySelector('.experimental-fight-pools, .fight-result-participants');
    if (!container) return;
    const cards = Array.from(container.children).filter(card =>
      card.matches('.experimental-fight-pool, .fight-result-card.has-fight-portrait'));
    if (cards.length !== 2) return;
    const entries = cards.map(card => ({
      card,
      frame: card.querySelector('.fight-portrait[data-fight-base-mm]'),
      image: card.querySelector('.fight-portrait[data-fight-base-mm] > img.fight-portrait-artwork')
    }));
    if (entries.some(entry => !entry.frame || !entry.image)) return;
    currentPair = container;

    function refresh() {
      if (currentPair !== container || !container.isConnected) return;
      const items = entries.map(({frame, image}) => ({
        baseMm: Number(frame.dataset.fightBaseMm),
        geometry: measureImage(image)
      }));
      const availableHeight = Math.min(...cards.map(card => card.getBoundingClientRect().height));
      const layouts = calculatePair(items, availableHeight);
      if (!layouts) return; // Keep static CSS until both cutouts are available.
      entries.forEach(({card, frame, image}, i) => {
        const layout = layouts[i];
        const width = card.getBoundingClientRect().width;
        // Centre each *base*, not the transparent image canvas.
        const centreX = width * .77;
        // Fight Result: expose more of the miniature's right side without
        // changing its physical scale or base-to-bottom alignment. The active
        // Fight Resolution pools keep their original base centres.
        const resultLeftShift = container.classList?.contains('fight-result-participants')
          ? width * .12 : 0;
        image.style.width = layout.imageWidth + 'px';
        image.style.height = layout.imageHeight + 'px';
        image.style.left = (centreX - resultLeftShift - layout.baseCenter) + 'px';
        image.style.bottom = (2 - layout.transparentBottom) + 'px';
        frame.classList.add('is-table-scaled');
      });
    }

    entries.forEach(({image}) => {
      if (!image.complete || !image.naturalWidth) {
        image.addEventListener('load', refresh, { once: true });
      }
    });
    if (typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(refresh);
      cards.forEach(card => observer.observe(card));
    }
    refresh();
  }

  window.TombWorldFightPortraitScale = Object.freeze({
    mount, analyzePixels, calculatePair
  });
})();
