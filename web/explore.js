// Compatibility route: the former guided-reading page now lives on the main page.
// Old section anchors map to their new homes; anything else opens the top of the page.
(() => {
  'use strict';
  const MOVED = {
    sourceState: 'snapshots',
    dataAboutData: 'data',
    lenses: 'evidence',
    pathways: 'evidence',
    receipts: 'evidence',
    reading: 'insights'
  };
  const from = window.location.hash.replace(/^#/, '');
  const target = MOVED[from] ? `./#${MOVED[from]}` : './';
  window.location.replace(target);
  document.addEventListener('DOMContentLoaded', () => {
    const link = document.getElementById('continue');
    if (link) link.setAttribute('href', target);
  });
})();
