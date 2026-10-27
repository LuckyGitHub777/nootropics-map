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

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  const claimById = (id) => state.claims.find((item) => item.id === id);
  const sourceById = (id) => state.sources.find((item) => item.id === id);
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
    $('#emptyState').hidden = items.length !== 0;

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

  function openDetail(item) {
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
    $('#detailDialog').showModal();
  }

  function update() {
    renderCards();
    renderMap();
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
      $$('.filter-chip').forEach((chip) => chip.classList.toggle('active', chip === button));
      update();
    }));

    $$('.view-option').forEach((button) => button.addEventListener('click', () => {
      state.view = button.dataset.view;
      $$('.view-option').forEach((option) => option.classList.toggle('active', option === button));
      renderCards();
    }));

    $('#trustButton').addEventListener('click', () => $('#trustDialog').showModal());
    $('#methodButton').addEventListener('click', () => $('#methodDialog').showModal());

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
    } catch (error) {
      console.error(error);
      $('#cardGrid').innerHTML = '<p class="empty-state">Evidence data could not be loaded. Serve the repository over HTTP rather than opening the file directly.</p>';
    }
  }

  load();
})();
