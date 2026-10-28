(() => {
  'use strict';

  const state = { interventions: [], claims: [], sources: [], query: '' };

  // Published 2022 community analysis (result table and plotting code). Seven cited values, not the dataset.
  // count = total ratings; p = modeled probability of a rating of 10; lo/hi = published model interval.
  const COMMUNITY_EXAMPLES = [
    { name: 'Weightlifting', count: 567, p: 0.121, lo: 0.093, hi: 0.153 },
    { name: 'Trying to get more sleep', count: 993, p: 0.075, lo: 0.060, hi: 0.093 },
    { name: 'Meditation', count: 429, p: 0.066, lo: 0.046, hi: 0.093 },
    { name: 'Caffeine', count: 2553, p: 0.030, lo: 0.025, hi: 0.037 },
    { name: 'Creatine', count: 1153, p: 0.014, lo: 0.010, hi: 0.020 },
    { name: 'Theanine', count: 1322, p: 0.013, lo: 0.009, hi: 0.018 },
    { name: 'Omega-3', count: 956, p: 0.010, lo: 0.006, hi: 0.014 }
  ];
  // Published plotting-code regions over the 116 plotted items.
  const REGIONS = { countSplit: 300, pSplit: 0.02, uncommonOften: 18, commonRarely: 20, elsewhere: 78 };

  const confidenceRank = { unknown: 0, low: 1, moderate: 2, high: 3 };
  const bandRank = { emerging: 1, moderate: 2, strong: 3 };
  const titleCase = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  // search-resolution:start
  // Search context is navigation metadata, not evidence. Reviewed evidence comes only from data/*.json.
  // Each source-context term below was checked by name against the published 2022 result table (or, for
  // the later image, against its labels). No ratings, counts, coordinates or rankings are carried here,
  // and this list is deliberately not an inventory of either source.
  const SOURCE_CONTEXT = [
    { term: 'Creatine', source: 'published-2022', reviewed: 'creatine', relation: 'exact',
      note: 'Raters judged its felt effect; the reviewed claim concerns strength and power. Different questions.' },
    { term: 'Meditation', source: 'published-2022', reviewed: 'meditation', relation: 'exact' },
    { term: 'Weightlifting', aliases: ['weight lifting'], source: 'published-2022', reviewed: 'physical-activity', relation: 'broader' },
    { term: 'Caffeine', source: 'published-2022' },
    { term: 'Theanine', aliases: ['l-theanine'], source: 'published-2022' },
    { term: 'Omega-3', aliases: ['omega 3'], source: 'published-2022' },
    { term: 'Doing Math', source: 'later-image' }
  ];
  const REVIEWED_ALIASES = { 'physical-activity': ['exercise'] };
  const SNAPSHOTS_LINK = '#snapshots';

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
          label: 'Reviewed',
          title: many ? result.items.map((item) => item.name).join(' · ') : first.name,
          body: 'A reviewed record with its claim, limitations and sources.',
          secondary: c ? `Also in the 2022 chart.${c.note ? ` ${c.note}` : ''}` : '',
          actions: result.items.map((item) => ({ slug: item.slug, text: `Open ${item.name}` })),
          link: null
        };
      }
      case 'broader':
        return {
          label: 'Related evidence',
          title: `${c.term} → ${first.name}`,
          body: `No record for ${c.term} itself. The ${first.name} record is broader than the searched term.`,
          secondary: `${c.term} is in the 2022 chart. The chart and the claim measure different outcomes.`,
          actions: [{ slug: first.slug, text: `Open ${first.name}` }],
          link: { href: SNAPSHOTS_LINK, text: 'About the two snapshots' }
        };
      case 'published-2022':
        return {
          label: '2022 chart',
          title: c.term,
          body: `${c.term} appears in the published 2022 community analysis. No reviewed record yet.`,
          secondary: 'Self-reported ratings: not evidence of efficacy or safety.',
          actions: [],
          link: { href: SNAPSHOTS_LINK, text: 'About the two snapshots' }
        };
      case 'later-image':
        return {
          label: 'Later image',
          title: c.term,
          body: `${c.term} appears only in the later supplied image, separate from the published 2022 analysis.`,
          secondary: 'Its data is undocumented, so no figures apply. No reviewed record.',
          actions: [],
          link: { href: SNAPSHOTS_LINK, text: 'About the two snapshots' }
        };
      case 'not-mapped':
        return {
          label: 'Not in the current index',
          title: `“${result.query}”`,
          body: 'Search covers reviewed records and selected chart items; it is not a complete inventory of the upstream dataset.',
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
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const svgEl = (tag, attrs = {}, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const fmtCount = (n) => n.toLocaleString('en-US');
  const fmtP = (p) => p.toFixed(3);

  // ---------- Community map (original diagram of seven published values) ----------
  function renderCommunityMap() {
    const svg = $('#communityMap');
    const compact = window.matchMedia('(max-width: 650px)').matches;
    svg.querySelectorAll(':scope > :not(title):not(desc)').forEach((node) => node.remove());
    const W = compact ? 360 : 960;
    const H = compact ? 420 : 560;
    const m = compact ? { l: 68, r: 14, t: 18, b: 58 } : { l: 92, r: 40, t: 26, b: 74 };
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const xMin = compact ? 100 : 10;
    const xMax = 4000;
    const yMin = 0.004;
    const yMax = 0.2;
    const x = (v) => m.l + (Math.log10(v / xMin) / Math.log10(xMax / xMin)) * (W - m.l - m.r);
    const y = (v) => H - m.b - (Math.log10(v / yMin) / Math.log10(yMax / yMin)) * (H - m.t - m.b);

    // Published regions.
    const xs = x(REGIONS.countSplit);
    const ys = y(REGIONS.pSplit);
    svg.appendChild(svgEl('rect', { x: m.l, y: m.t, width: xs - m.l, height: ys - m.t, class: 'region region-often' }));
    svg.appendChild(svgEl('rect', { x: xs, y: ys, width: W - m.r - xs, height: H - m.b - ys, class: 'region region-rarely' }));
    svg.appendChild(svgEl('line', { x1: xs, x2: xs, y1: m.t, y2: H - m.b, class: 'split' }));
    svg.appendChild(svgEl('line', { x1: m.l, x2: W - m.r, y1: ys, y2: ys, class: 'split' }));
    const regionText = compact
      ? [[`${REGIONS.uncommonOften} items`, (m.l + xs) / 2, m.t + 18, 'middle'], [`${REGIONS.commonRarely} items`, W - m.r - 8, H - m.b - 12, 'end']]
      : [[`Uncommon, often a 10 · ${REGIONS.uncommonOften} items`, m.l + 14, m.t + 24, 'start'], [`Common, rarely a 10 · ${REGIONS.commonRarely} items`, W - m.r - 14, H - m.b - 16, 'end']];
    regionText.forEach(([text, tx, ty, anchor]) => svg.appendChild(svgEl('text', { x: tx, y: ty, 'text-anchor': anchor, class: 'region-label' }, text)));

    // Axes.
    (compact ? [100, 1000] : [10, 100, 1000]).forEach((v) => {
      svg.appendChild(svgEl('line', { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, class: 'grid' }));
      svg.appendChild(svgEl('text', { x: x(v), y: H - m.b + 22, 'text-anchor': 'middle', class: 'tick' }, fmtCount(v)));
    });
    [0.01, 0.03, 0.1].forEach((v) => {
      svg.appendChild(svgEl('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }));
      svg.appendChild(svgEl('text', { x: m.l - (compact ? 7 : 10), y: y(v) + 4, 'text-anchor': 'end', class: 'tick' }, String(v)));
    });
    svg.appendChild(svgEl('text', { x: (m.l + W - m.r) / 2, y: H - (compact ? 14 : 20), 'text-anchor': 'middle', class: 'axis-title' }, 'Number of ratings →'));
    const yt = svgEl('text', { x: 0, y: 0, 'text-anchor': 'middle', class: 'axis-title', transform: `translate(${compact ? 13 : 26} ${(m.t + H - m.b) / 2}) rotate(-90)` }, compact ? 'Chance of a 10 →' : 'Reported life-changing probability →');
    svg.appendChild(yt);

    // Points with intervals and direct labels (desktop) or index numbers (compact).
    const labelSide = { 'Weightlifting': 'left', 'Trying to get more sleep': 'right', 'Meditation': 'left', 'Caffeine': 'left', 'Creatine': 'left', 'Theanine': 'right', 'Omega-3': 'left' };
    const labelDy = { 'Weightlifting': -2, 'Meditation': 4, 'Trying to get more sleep': 4, 'Creatine': -14, 'Theanine': 8, 'Omega-3': 6, 'Caffeine': 4 };
    const compactDy = { 'Creatine': -11, 'Theanine': 4, 'Omega-3': 3 };
    COMMUNITY_EXAMPLES.forEach((d, i) => {
      const cx = x(d.count);
      const cy = y(d.p);
      const g = svgEl('g', { class: 'point' });
      g.appendChild(svgEl('line', { x1: cx, x2: cx, y1: y(d.hi), y2: y(d.lo), class: 'interval' }));
      g.appendChild(svgEl('circle', { cx, cy, r: compact ? 4.5 : 5.5, class: 'dot' }));
      const left = labelSide[d.name] === 'left';
      if (compact) {
        g.appendChild(svgEl('text', { x: left ? cx - 9 : cx + 9, y: cy + 4.5 + (compactDy[d.name] ?? (labelDy[d.name] || 0) / 2), 'text-anchor': left ? 'end' : 'start', class: 'dot-index' }, String(i + 1)));
      } else {
        g.appendChild(svgEl('text', { x: left ? cx - 12 : cx + 12, y: cy + 4 + (labelDy[d.name] || 0), 'text-anchor': left ? 'end' : 'start', class: 'point-label' }, d.name));
      }
      svg.appendChild(g);
    });
  }

  function renderMapKey() {
    const body = $('#mapKeyBody');
    body.replaceChildren();
    COMMUNITY_EXAMPLES.forEach((d, i) => {
      const tr = el('tr');
      tr.append(el('td', 'key-index', String(i + 1)), el('th', 'key-name', d.name), el('td', 'key-num', fmtCount(d.count)), el('td', 'key-num', fmtP(d.p)));
      tr.querySelector('th').setAttribute('scope', 'row');
      body.appendChild(tr);
    });
  }

  // ---------- Evidence check ----------
  function meter(label, level, word) {
    const wrap = el('span', 'meter');
    wrap.setAttribute('aria-label', `${label}: ${word}`);
    wrap.appendChild(el('span', 'meter-label', label));
    const dots = el('span', 'meter-dots');
    dots.setAttribute('aria-hidden', 'true');
    for (let n = 1; n <= 3; n += 1) dots.appendChild(el('i', n <= level ? 'on' : ''));
    wrap.append(dots, el('span', 'meter-word', word));
    return wrap;
  }

  function matchingItems() {
    const q = normalizeQuery(state.query);
    if (!q) return state.interventions;
    return state.interventions.filter((item) => normalizeQuery([item.name, item.category, item.simple_summary].join(' ')).includes(q));
  }

  function renderEvidence() {
    const list = $('#evidenceList');
    const items = matchingItems();
    list.replaceChildren();
    $('#emptyState').hidden = items.length !== 0;
    items.forEach((item) => {
      const confidence = confidenceFor(item);
      const li = el('li');
      const button = el('button', 'evidence-row');
      button.type = 'button';
      button.setAttribute('aria-label', `${item.name}: ${item.evidence_band} evidence, ${confidence} confidence. Open claim and sources.`);
      const main = el('span', 'row-main');
      main.append(el('span', 'row-name', item.name), el('span', 'row-summary', item.simple_summary));
      button.append(main,
        meter('Evidence', bandRank[item.evidence_band] || 0, titleCase(item.evidence_band)),
        meter('Confidence', confidenceRank[confidence] || 0, titleCase(confidence)),
        el('span', 'row-open', 'Sources →'));
      button.addEventListener('click', () => openDetail(item));
      li.appendChild(button);
      list.appendChild(li);
    });
  }

  function renderSources() {
    const list = $('#reviewedSources');
    list.replaceChildren();
    state.sources.forEach((source) => {
      const li = el('li');
      const a = el('a', '', source.title);
      a.href = source.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      li.append(a, el('span', '', [source.publisher, source.publication_date ? source.publication_date.slice(0, 4) : ''].filter(Boolean).join(' · ')));
      list.appendChild(li);
    });
  }

  function openDetail(item, updateLocation = true) {
    const claims = item.claim_ids.map(claimById).filter(Boolean);
    const sources = [...new Set(claims.flatMap((claim) => claim.source_ids))].map(sourceById).filter(Boolean);
    const root = $('#dialogContent');
    root.replaceChildren();
    root.append(el('p', 'eyebrow', item.category), Object.assign(el('h2', '', item.name), { id: 'detailTitle' }), el('p', 'dialog-lede', item.detailed_summary));
    const meta = el('div', 'detail-meta');
    meta.append(meter('Evidence', bandRank[item.evidence_band] || 0, `Evidence: ${titleCase(item.evidence_band)}`),
      meter('Confidence', confidenceRank[confidenceFor(item)] || 0, `Confidence: ${titleCase(confidenceFor(item))}`),
      el('span', 'meta-text', `Reviewed ${item.reviewed_at}`));
    root.appendChild(meta);
    claims.forEach((claim) => {
      const sec = el('section', 'receipt');
      sec.append(el('p', 'receipt-label', 'Claim'), el('h3', '', claim.claim));
      sec.append(el('p', 'receipt-label', 'What the sources support'));
      const ul = el('ul');
      claim.source_claims.forEach((entry) => ul.appendChild(el('li', '', entry.summary)));
      sec.appendChild(ul);
      sec.append(el('p', 'receipt-label', 'Limitations'));
      const lim = el('ul');
      claim.limitations.forEach((text) => lim.appendChild(el('li', '', text)));
      sec.appendChild(lim);
      root.appendChild(sec);
    });
    const safety = el('section', 'receipt');
    safety.append(el('p', 'receipt-label', 'Safety context'), el('p', '', item.safety_note));
    root.appendChild(safety);
    const src = el('section', 'receipt');
    src.appendChild(el('p', 'receipt-label', 'Sources'));
    sources.forEach((source) => {
      const a = el('a', 'source-link');
      a.href = source.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.append(el('strong', '', source.title), el('span', '', [source.publisher, source.publication_date, source.doi ? `DOI ${source.doi}` : ''].filter(Boolean).join(' · ')), el('small', '', `Checked ${source.retrieved_at}`));
      src.appendChild(a);
    });
    root.appendChild(src);
    const dialog = $('#detailDialog');
    if (updateLocation) {
      const targetHash = `#${encodeURIComponent(item.slug)}`;
      if (window.location.hash !== targetHash) history.pushState({ nootropicsMapDetail: item.slug }, '', targetHash);
    }
    if (!dialog.open) dialog.showModal();
  }

  function syncDetailFromLocation() {
    const item = itemBySlug(hashSlug());
    const dialog = $('#detailDialog');
    if (item) {
      openDetail(item, false);
    } else if (dialog.open) {
      syncingLocation = true;
      dialog.close();
      syncingLocation = false;
    }
  }

  // ---------- Search ----------
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
    const actions = $('#resolutionActions');
    actions.replaceChildren();
    view.actions.forEach((action) => {
      const item = itemBySlug(action.slug);
      if (!item) return;
      const button = el('button', 'resolution-action', `${action.text} →`);
      button.type = 'button';
      button.addEventListener('click', () => openDetail(item));
      actions.appendChild(button);
    });
    if (view.link) {
      const link = el('a', 'resolution-link', view.link.text);
      link.href = view.link.href;
      actions.appendChild(link);
    }
    actions.hidden = !actions.childElementCount;
    panel.hidden = false;
    // Announce once typing settles, and only when the resolved state changes.
    const key = `${result.state}|${view.title}`;
    announceTimer = setTimeout(() => {
      if (key === lastAnnounced) return;
      lastAnnounced = key;
      announce.textContent = `${view.label}: ${view.title}.`;
    }, 650);
  }

  function bindEvents() {
    $('#searchInput').addEventListener('input', (event) => {
      state.query = event.target.value;
      renderEvidence();
      renderResolution();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        event.preventDefault();
        $('#searchInput').focus();
      }
    });
    const detailDialog = $('#detailDialog');
    detailDialog.addEventListener('close', () => {
      if (syncingLocation) return;
      const slug = hashSlug();
      if (!slug || !itemBySlug(slug)) return;
      if (history.state?.nootropicsMapDetail === slug) history.back();
      else history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
    });
    window.addEventListener('popstate', syncDetailFromLocation);
    window.addEventListener('hashchange', syncDetailFromLocation);
    window.matchMedia('(max-width: 650px)').addEventListener('change', renderCommunityMap);
  }

  async function load() {
    renderCommunityMap();
    renderMapKey();
    try {
      const [interventions, claims, sources] = await Promise.all([
        fetch('../data/interventions.json').then((r) => r.json()),
        fetch('../data/claims.json').then((r) => r.json()),
        fetch('../data/sources.json').then((r) => r.json())
      ]);
      state.interventions = interventions;
      state.claims = claims;
      state.sources = sources;
      const latest = interventions.map((item) => item.reviewed_at).filter(Boolean).sort().at(-1);
      $('#reviewNote').textContent = latest
        ? `${interventions.length} reviewed records · ${sources.length} sources · reviewed ${new Date(`${latest}T00:00:00Z`).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })}`
        : '';
      bindEvents();
      renderEvidence();
      renderSources();
      syncDetailFromLocation();
    } catch (error) {
      console.error(error);
      $('#evidenceList').replaceChildren(el('li', 'empty-state', 'Evidence data could not be loaded.'));
    }
  }

  load();
})();
