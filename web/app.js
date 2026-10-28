(() => {
  'use strict';

  const state = {
    interventions: [],
    claims: [],
    sources: [],
    category: 'all',
    query: '',
    view: 'simple'
  };

  const evidenceRank = { emerging: 1, moderate: 2, strong: 3 };
  const confidenceRank = { unknown: 1, low: 1, moderate: 2, high: 3 };
  const evidenceLabel = { emerging: 'Emerging evidence', moderate: 'Moderate evidence', strong: 'Strong evidence' };
  const pointStyle = {
    emerging: { stroke: '#827d73', fill: '#827d73' },
    moderate: { stroke: '#9e9a8f', fill: '#9e9a8f' },
    strong: { stroke: '#d9c8a2', fill: '#d9c8a2' }
  };

  // search-resolution:start
  // Search context is navigation metadata, not evidence. Reviewed evidence comes only from data/*.json.
  // Each source-context term below was checked by name against the published 2022 result table (or, for
  // the later image, against its labels). No ratings, counts, coordinates or rankings are carried here,
  // and this list is deliberately not an inventory of either source.
  const SOURCE_CONTEXT = [
    { term: 'Creatine', source: 'published-2022', reviewed: 'creatine', relation: 'exact',
      note: 'Raters were asked how it felt, while the reviewed claim concerns strength, power and repeated high-intensity effort. The two answer different questions.' },
    { term: 'Meditation', source: 'published-2022', reviewed: 'meditation', relation: 'exact' },
    { term: 'Weightlifting', aliases: ['weight lifting'], source: 'published-2022', reviewed: 'physical-activity', relation: 'broader' },
    { term: 'Caffeine', source: 'published-2022' },
    { term: 'Theanine', aliases: ['l-theanine'], source: 'published-2022' },
    { term: 'Doing Math', source: 'later-image' }
  ];
  const REVIEWED_ALIASES = { 'physical-activity': ['exercise'] };
  const SOURCE_STATE_LINK = './explore.html#sourceState';

  const normalizeQuery = (text = '') => String(text).normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

  function phraseMatches(query, phrase) {
    const p = normalizeQuery(phrase);
    if (!query || !p) return false;
    if (p === query) return true;
    if (query.length < 3) return false;
    if (p.startsWith(query) || p.includes(` ${query}`)) return true;
    return (` ${query} `).includes(` ${p} `);
  }

  function resolveSearch(rawQuery, interventions) {
    const query = normalizeQuery(rawQuery);
    const display = String(rawQuery || '').trim().replace(/\s+/g, ' ');
    if (!query) return { state: 'empty' };
    const reviewed = interventions.filter((item) =>
      [item.name, item.slug.replace(/-/g, ' '), ...(REVIEWED_ALIASES[item.slug] || [])].some((p) => phraseMatches(query, p)));
    const contexts = SOURCE_CONTEXT.filter((entry) => [entry.term, ...(entry.aliases || [])].some((p) => phraseMatches(query, p)));
    if (reviewed.length) {
      const context = contexts.find((entry) => entry.relation === 'exact' && entry.reviewed === reviewed[0].slug) || null;
      return { state: 'reviewed', query: display, items: reviewed, context };
    }
    const bySlug = (slug) => interventions.find((item) => item.slug === slug);
    const broader = contexts.find((entry) => entry.relation === 'broader' && bySlug(entry.reviewed));
    if (broader) return { state: 'broader', query: display, items: [bySlug(broader.reviewed)], context: broader };
    const published = contexts.find((entry) => entry.source === 'published-2022');
    if (published) return { state: 'published-2022', query: display, items: [], context: published };
    const later = contexts.find((entry) => entry.source === 'later-image');
    if (later) return { state: 'later-image', query: display, items: [], context: later };
    if (query.length < 3) return { state: 'typing', query: display };
    return { state: 'not-mapped', query: display, items: [] };
  }

  function describeResolution(result) {
    const c = result.context;
    const first = result.items && result.items[0];
    switch (result.state) {
      case 'reviewed': {
        const many = result.items.length > 1;
        return {
          label: many ? 'Reviewed records' : 'Reviewed record',
          title: many ? result.items.map((item) => item.name).join(' · ') : first.name,
          body: many
            ? 'Reviewed Nootropics Map records match this search. Each evidence receipt states one bounded claim, its limitations and its sources.'
            : 'A reviewed Nootropics Map record exists. Its evidence receipt is the authoritative claim here, with its limitations and sources.',
          secondary: c
            ? `${c.term} also appears in the published 2022 community analysis as self-reported experience, kept separate from the reviewed claim.${c.note ? ` ${c.note}` : ''}`
            : '',
          actions: result.items.map((item) => ({ slug: item.slug, text: `Open the ${item.name} record` })),
          link: null
        };
      }
      case 'broader':
        return {
          label: 'Broader reviewed record',
          title: `Closest reviewed record: ${first.name}`,
          body: `There is no reviewed record for ${c.term} itself. The ${first.name} record is broader than the searched term: its claim is about ${first.name.toLowerCase()} in general, not ${c.term.toLowerCase()} specifically.`,
          secondary: `${c.term} also appears in the published 2022 community analysis as self-reported experience. That signal and the reviewed claim measure different outcomes, so they are not compared here.`,
          actions: [{ slug: first.slug, text: `Open the ${first.name} record` }],
          link: { href: SOURCE_STATE_LINK, text: 'How the source states differ' }
        };
      case 'published-2022':
        return {
          label: 'Published 2022 community source',
          title: c.term,
          body: `${c.term} appears in the published 2022 community analysis. There is no reviewed Nootropics Map record for it yet.`,
          secondary: 'Community ratings are self-reported experience: source context, not evidence of efficacy or safety.',
          actions: [],
          link: { href: SOURCE_STATE_LINK, text: 'How the source states differ' }
        };
      case 'later-image':
        return {
          label: 'Later supplied image',
          title: c.term,
          body: `${c.term} appears only in the later supplied chart image, separate from the published 2022 analysis, and is absent from its result table.`,
          secondary: `The dataset behind the later image has not been published, and there is no reviewed Nootropics Map record for ${c.term}.`,
          actions: [],
          link: { href: SOURCE_STATE_LINK, text: 'How the source states differ' }
        };
      case 'not-mapped':
        return {
          label: 'Not mapped in this release',
          title: `“${result.query}”`,
          body: 'Search covers reviewed records and selected source context currently mapped by Nootropics Map; it is not a complete inventory of the upstream dataset.',
          secondary: '',
          actions: [],
          link: null
        };
      default:
        return null;
    }
  }
  // search-resolution:end

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  const claimById = (id) => state.claims.find((item) => item.id === id);
  const sourceById = (id) => state.sources.find((item) => item.id === id);
  const itemBySlug = (slug) => state.interventions.find((item) => item.slug === slug);
  const hashSlug = () => {
    try { return decodeURIComponent(window.location.hash.replace(/^#/, '')); }
    catch { return ''; }
  };
  let syncingLocation = false;
  const confidenceFor = (item) => {
    const claims = item.claim_ids.map(claimById).filter(Boolean);
    if (!claims.length) return 'unknown';
    return claims.map((claim) => claim.confidence).sort((a, b) => confidenceRank[a] - confidenceRank[b])[0];
  };

  function sanitize(text = '') {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function matchingItems() {
    const q = state.query.trim().toLowerCase();
    return state.interventions.filter((item) => {
      const categoryMatch = state.category === 'all' || item.category === state.category;
      const haystack = [item.name, item.category, item.simple_summary, item.detailed_summary].join(' ').toLowerCase();
      return categoryMatch && (!q || haystack.includes(q));
    });
  }

  function renderCards() {
    const items = matchingItems();
    const grid = $('#cardGrid');
    grid.innerHTML = '';
    renderEmptyState(items.length);

    items.forEach((item) => {
      const claims = item.claim_ids.map(claimById).filter(Boolean);
      const button = document.createElement('article');
      button.className = 'evidence-card';
      button.tabIndex = 0;
      button.setAttribute('role', 'button');
      button.setAttribute('aria-label', `Open evidence for ${item.name}`);
      const summary = state.view === 'simple' ? item.simple_summary : item.detailed_summary;
      button.innerHTML = `
        <div class="card-top">
          <span class="category-tag">${sanitize(item.category)}</span>
          <span class="band-badge">${sanitize(evidenceLabel[item.evidence_band])}</span>
        </div>
        <h3>${sanitize(item.name)}</h3>
        <p class="card-summary">${sanitize(summary)}</p>
        <div class="card-foot">
          <span>${claims.length} evidence receipt${claims.length === 1 ? '' : 's'}</span>
          <strong>Inspect →</strong>
        </div>`;
      button.addEventListener('click', () => openDetail(item));
      button.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openDetail(item);
        }
      });
      grid.appendChild(button);
    });
  }

  function svgEl(tag, attrs = {}) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
  }

  function renderMap() {
    const svg = $('#evidenceMap');
    const mapKey = $('#mapKey');
    const items = matchingItems();
    const compact = window.matchMedia('(max-width: 650px)').matches;
    svg.replaceChildren();
    mapKey.replaceChildren();

    const width = compact ? 360 : 900;
    const height = compact ? 470 : 520;
    const margins = compact
      ? { left: 58, right: 28, top: 46, bottom: 68 }
      : { left: 90, right: 70, top: 58, bottom: 70 };
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

    const innerW = width - margins.left - margins.right;
    const innerH = height - margins.top - margins.bottom;
    const xFor = (rank) => margins.left + ((rank - 1) / 2) * innerW;
    const yFor = (rank) => margins.top + innerH - ((rank - 1) / 2) * innerH;

    [1,2,3].forEach((rank) => {
      const x = xFor(rank);
      const y = yFor(rank);
      svg.appendChild(svgEl('line', { x1:x, x2:x, y1:margins.top, y2:height-margins.bottom, class:'grid-line' }));
      svg.appendChild(svgEl('line', { x1:margins.left, x2:width-margins.right, y1:y, y2:y, class:'grid-line' }));
    });

    [['Emerging',1],['Moderate',2],['Strong',3]].forEach(([label,rank]) => {
      const t = svgEl('text', { x:xFor(rank), y:height-(compact ? 24 : 28), 'text-anchor':'middle', class:'axis-label' });
      t.textContent = label;
      svg.appendChild(t);
    });
    [['Low',1],['Moderate',2],['High',3]].forEach(([label,rank]) => {
      const t = svgEl('text', { x:compact ? 31 : 52, y:yFor(rank)+4, 'text-anchor':'middle', class:'axis-label' });
      t.textContent = label;
      svg.appendChild(t);
    });

    const collisions = new Map();
    const compactOffsets = [
      { x:-24, y:22 }, { x:-72, y:22 }, { x:-24, y:72 }, { x:-72, y:72 },
      { x:-48, y:47 }, { x:-96, y:47 }, { x:-24, y:122 }, { x:-72, y:122 }
    ];
    const desktopOffsets = [
      { x:-30, y:22 }, { x:-30, y:82 }, { x:-180, y:22 }, { x:-180, y:82 },
      { x:-105, y:52 }, { x:-255, y:22 }, { x:-255, y:82 }, { x:-105, y:112 }
    ];
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

    items.forEach((item, itemIndex) => {
      const xRank = evidenceRank[item.evidence_band];
      const confidence = confidenceFor(item);
      const yRank = confidenceRank[confidence];
      const key = `${xRank}:${yRank}`;
      const index = collisions.get(key) || 0;
      collisions.set(key, index + 1);

      let x;
      let y;
      if (compact) {
        const offset = compactOffsets[index] || { x:-48, y:122 + (index - compactOffsets.length + 1) * 36 };
        const radius = 17;
        x = clamp(xFor(xRank) + offset.x, margins.left + radius, width - margins.right - radius);
        y = clamp(yFor(yRank) + offset.y, margins.top + radius, height - margins.bottom - radius);
      } else {
        const offset = desktopOffsets[index] || { x:-105 - (index - desktopOffsets.length + 1) * 45, y:112 };
        const radius = 15;
        x = clamp(xFor(xRank) + offset.x, margins.left + radius, width - margins.right - radius);
        y = clamp(yFor(yRank) + offset.y, margins.top + radius, height - margins.bottom - radius);
      }

      const style = pointStyle[item.evidence_band];
      const group = svgEl('g', {
        class:'map-node', tabindex:'0', role:'button',
        'aria-label':`${item.name}: ${item.evidence_band} evidence maturity, ${confidence} confidence`
      });
      group.appendChild(svgEl('circle', { cx:x, cy:y, r:compact ? 17 : 15, class:'node-ring', stroke:style.stroke }));
      group.appendChild(svgEl('circle', { cx:x, cy:y, r:compact ? 13 : 6, class:'node-core', fill:style.fill }));

      const indexLabel = svgEl('text', { x, y:y+4, 'text-anchor':'middle', class:'node-index' });
      indexLabel.textContent = String(itemIndex + 1);
      group.appendChild(indexLabel);

      const labelOnLeft = !compact && xRank === 3;
      const labelX = labelOnLeft ? x - 22 : x + 22;
      const labelAnchor = labelOnLeft ? 'end' : 'start';
      const label = svgEl('text', { x:labelX, y:y-1, 'text-anchor':labelAnchor, class:'node-label' });
      label.textContent = item.name;
      group.appendChild(label);
      const sub = svgEl('text', { x:labelX, y:y+15, 'text-anchor':labelAnchor, class:'node-sublabel' });
      sub.textContent = item.category;
      group.appendChild(sub);

      group.addEventListener('click', () => openDetail(item));
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault(); openDetail(item);
        }
      });
      svg.appendChild(group);

      const keyButton = document.createElement('button');
      keyButton.type = 'button';
      keyButton.className = 'map-key-item';
      keyButton.setAttribute('aria-label', `Open evidence for ${item.name}`);
      const number = document.createElement('span');
      number.className = 'map-key-index';
      number.textContent = String(itemIndex + 1);
      const copy = document.createElement('span');
      const name = document.createElement('strong');
      name.textContent = item.name;
      const category = document.createElement('small');
      category.textContent = `${item.category} · ${evidenceLabel[item.evidence_band]}`;
      copy.append(name, category);
      keyButton.append(number, copy);
      keyButton.addEventListener('click', () => openDetail(item));
      mapKey.appendChild(keyButton);
    });

    $('#mapStatus').textContent = items.length === state.interventions.length
      ? 'All evidence records'
      : `${items.length} matching record${items.length === 1 ? '' : 's'}`;
  }

  function openDetail(item, updateLocation = true) {
    const claims = item.claim_ids.map(claimById).filter(Boolean);
    const sourceIds = [...new Set(claims.flatMap((claim) => claim.source_ids))];
    const sources = sourceIds.map(sourceById).filter(Boolean);

    const claimHtml = claims.map((claim) => `
      <section class="receipt">
        <span class="receipt-label">Evidence receipt · ${sanitize(claim.id)}</span>
        <h3>${sanitize(claim.claim)}</h3>
        <div class="detail-meta">
          <span class="meta-pill">Status: ${sanitize(claim.status.replaceAll('_',' '))}</span>
          <span class="meta-pill">Confidence: ${sanitize(claim.confidence)}</span>
          <span class="meta-pill">Reviewed: ${sanitize(claim.last_reviewed)}</span>
        </div>
        <p><strong>What the sources support</strong></p>
        <ul>${claim.source_claims.map((entry) => `<li><span class="source-claim-id">${sanitize(entry.source_id)}</span> ${sanitize(entry.summary)}</li>`).join('')}</ul>
        <p><strong>Limitations</strong></p>
        <ul>${claim.limitations.map((limit) => `<li>${sanitize(limit)}</li>`).join('')}</ul>
      </section>`).join('');

    const sourceHtml = sources.map((source) => `
      <a class="source-link" href="${encodeURI(source.url)}" target="_blank" rel="noopener noreferrer">
        <strong>${sanitize(source.title)}</strong>
        <span>${sanitize(source.publisher)} · ${sanitize(source.source_type.replaceAll('_',' '))}${source.publication_date ? ` · ${sanitize(source.publication_date)}` : ''}${source.doi ? ` · DOI ${sanitize(source.doi)}` : ''}</span>
        <small>Source checked ${sanitize(source.retrieved_at)}</small>
      </a>`).join('');

    $('#dialogContent').innerHTML = `
      <p class="eyebrow">${sanitize(item.category.toUpperCase())}</p>
      <h2>${sanitize(item.name)}</h2>
      <p class="dialog-lede">${sanitize(item.detailed_summary)}</p>
      <div class="detail-meta">
        <span class="meta-pill">Evidence: ${sanitize(item.evidence_band)}</span>
        <span class="meta-pill">Confidence: ${sanitize(confidenceFor(item))}</span>
        <span class="meta-pill">Reviewed: ${sanitize(item.reviewed_at)}</span>
      </div>
      <section class="receipt">
        <span class="receipt-label">Safety context</span>
        <p>${sanitize(item.safety_note)}</p>
      </section>
      ${claimHtml}
      <section class="receipt">
        <span class="receipt-label">Sources</span>
        <div class="source-list">${sourceHtml}</div>
      </section>`;
    const dialog = $('#detailDialog');
    if (updateLocation) {
      const targetHash = `#${encodeURIComponent(item.slug)}`;
      if (window.location.hash !== targetHash) {
        history.pushState({ nootropicsMapDetail: item.slug }, '', targetHash);
      }
    }
    if (!dialog.open) dialog.showModal();
  }

  function syncDetailFromLocation() {
    const slug = hashSlug();
    const item = itemBySlug(slug);
    const dialog = $('#detailDialog');
    if (item) {
      openDetail(item, false);
    } else if (dialog.open) {
      syncingLocation = true;
      dialog.close();
      syncingLocation = false;
    }
  }

  let announceTimer = null;
  let lastAnnounced = '';

  function renderResolution() {
    const panel = $('#searchResolution');
    const result = resolveSearch(state.query, state.interventions);
    const view = describeResolution(result);
    const announce = $('#searchAnnounce');
    clearTimeout(announceTimer);
    if (!view) {
      panel.hidden = true;
      panel.removeAttribute('data-state');
      if (result.state === 'empty') { announce.textContent = ''; lastAnnounced = ''; }
      return;
    }
    panel.dataset.state = result.state;
    $('#resolutionLabel').textContent = view.label;
    $('#resolutionTitle').textContent = view.title;
    $('#resolutionBody').textContent = view.body;
    const secondary = $('#resolutionSecondary');
    secondary.textContent = view.secondary;
    secondary.hidden = !view.secondary;

    const filtered = state.category !== 'all' && view.actions.some((action) => itemBySlug(action.slug)?.category !== state.category);
    const filterNote = $('#resolutionFilter');
    filterNote.hidden = !filtered;
    filterNote.textContent = filtered ? 'The current category filter hides this record from the map and library; the record still opens here.' : '';

    const actions = $('#resolutionActions');
    actions.replaceChildren();
    view.actions.forEach((action) => {
      const item = itemBySlug(action.slug);
      if (!item) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'resolution-action';
      button.textContent = `${action.text} →`;
      button.addEventListener('click', () => openDetail(item));
      actions.appendChild(button);
    });
    if (view.link) {
      const link = document.createElement('a');
      link.className = 'resolution-link';
      link.href = view.link.href;
      link.textContent = view.link.text;
      actions.appendChild(link);
    }
    actions.hidden = !actions.childElementCount;
    panel.hidden = false;

    // Announce once typing settles, and only when the resolved state changes, to keep screen readers quiet.
    const key = `${result.state}|${view.title}`;
    announceTimer = setTimeout(() => {
      if (key === lastAnnounced) return;
      lastAnnounced = key;
      announce.textContent = `${view.label}: ${view.title}.`;
    }, 650);
  }

  function renderEmptyState(count) {
    const empty = $('#emptyState');
    empty.hidden = count !== 0;
    if (count !== 0) return;
    const view = describeResolution(resolveSearch(state.query, state.interventions));
    empty.textContent = view && state.query.trim()
      ? `No reviewed record in this view matches this search. Search result above: ${view.label}.`
      : 'No reviewed record in this view matches this search.';
  }

  function update() {
    renderCards();
    renderMap();
    renderResolution();
  }

  function bindEvents() {
    $('#searchInput').addEventListener('input', (event) => {
      state.query = event.target.value;
      update();
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
        event.preventDefault(); $('#searchInput').focus();
      }
    });

    $$('.filter-chip').forEach((button) => button.addEventListener('click', () => {
      state.category = button.dataset.category;
      $$('.filter-chip').forEach((chip) => {
        const active = chip === button;
        chip.classList.toggle('active', active);
        chip.setAttribute('aria-pressed', String(active));
      });
      update();
    }));

    $$('.view-option').forEach((button) => button.addEventListener('click', () => {
      state.view = button.dataset.view;
      $$('.view-option').forEach((option) => {
        const active = option === button;
        option.classList.toggle('active', active);
        option.setAttribute('aria-pressed', String(active));
      });
      renderCards();
    }));

    $('#trustButton').addEventListener('click', () => $('#trustDialog').showModal());
    $('#methodButton').addEventListener('click', () => $('#methodDialog').showModal());

    const detailDialog = $('#detailDialog');
    detailDialog.addEventListener('close', () => {
      if (syncingLocation) return;
      const slug = hashSlug();
      if (!slug || !itemBySlug(slug)) return;
      if (history.state?.nootropicsMapDetail === slug) {
        history.back();
      } else {
        history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
      }
    });
    window.addEventListener('popstate', syncDetailFromLocation);
    window.addEventListener('hashchange', syncDetailFromLocation);

    const compactQuery = window.matchMedia('(max-width: 650px)');
    compactQuery.addEventListener('change', () => renderMap());
  }

  async function load() {
    try {
      const [interventions, claims, sources] = await Promise.all([
        fetch('../data/interventions.json').then((r) => r.json()),
        fetch('../data/claims.json').then((r) => r.json()),
        fetch('../data/sources.json').then((r) => r.json())
      ]);
      state.interventions = interventions;
      state.claims = claims;
      state.sources = sources;
      $('#interventionCount').textContent = interventions.length;
      $('#claimCount').textContent = claims.length;
      const latestReview = interventions.map((item) => item.reviewed_at).filter(Boolean).sort().at(-1);
      $('#reviewDate').textContent = latestReview
        ? new Date(`${latestReview}T00:00:00Z`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
        : '—';
      bindEvents();
      update();
      syncDetailFromLocation();
    } catch (error) {
      console.error(error);
      $('#cardGrid').innerHTML = '<p class="empty-state">Evidence data could not be loaded. Serve the repository over HTTP rather than opening the file directly.</p>';
    }
  }

  load();
})();
