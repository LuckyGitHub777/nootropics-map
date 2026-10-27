// Guided reading page. Reviewed evidence is read from data/*.json (the system of record);
// the interpretive reading of the community chart is editorial copy and carries no data.
(() => {
  const $ = (id) => document.getElementById(id);
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  };
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const svgEl = (tag, attrs, parent) => {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    if (parent) parent.appendChild(node);
    return node;
  };
  const titleCase = (value) => String(value || '').replaceAll('_', ' ').replace(/^\w/, (c) => c.toUpperCase());

  // Each chain restates its claim; nothing beyond the claim is added.
  const PATHWAYS = {
    'CLM-SLEEP-HEALTH-001': ['Sleep', 'Enough for your age', 'Good quality', 'Foundational health behavior'],
    'CLM-EXERCISE-HEALTH-001': ['Regular physical activity', 'Immediate and long-term benefits', 'Sleep · anxiety · brain health', 'Chronic-disease risk'],
    'CLM-CREATINE-PERFORMANCE-001': ['Creatine supplementation', 'Repeated short, intense efforts', 'Strength · power · performance', 'Response varies by person'],
    'CLM-LIGHT-CIRCADIAN-001': ['Light exposure', 'Timing matters', 'Morning light advances the clock', 'Evening light delays it'],
    'CLM-MEDITATION-WELLBEING-001': ['Meditation & mindfulness', 'Some health and well-being outcomes', 'Quality varies by condition, practice and study']
  };

  /* ---------------- reviewed evidence ---------------- */
  let records = [];

  function buildRecords(interventions, claims, sources) {
    const claimById = new Map(claims.map((c) => [c.id, c]));
    const sourceById = new Map(sources.map((s) => [s.id, s]));
    return interventions.map((item) => {
      const itemClaims = item.claim_ids.map((id) => claimById.get(id)).filter(Boolean);
      const sourceIds = [...new Set(itemClaims.flatMap((c) => c.source_ids))];
      return { item, claims: itemClaims, sources: sourceIds.map((id) => sourceById.get(id)).filter(Boolean), sourceById };
    });
  }

  function renderPathways() {
    const box = $('paths');
    box.replaceChildren();
    records.forEach((rec, index) => {
      const claim = rec.claims[0];
      const chain = (claim && PATHWAYS[claim.id]) || [rec.item.name];
      const card = make('button', 'path-card');
      card.type = 'button';
      card.dataset.slug = rec.item.slug;
      card.append(
        make('small', null, `${rec.item.evidence_band} · ${claim ? claim.confidence : 'unrated'}`),
        make('strong', null, rec.item.name),
        make('span', null, chain[chain.length - 1])
      );
      card.addEventListener('click', () => showPathway(index));
      box.appendChild(card);
    });
    showPathway(0);
  }

  function showPathway(index) {
    const rec = records[index];
    if (!rec) return;
    const claim = rec.claims[0];
    $('paths').querySelectorAll('.path-card').forEach((card) => card.setAttribute('aria-pressed', String(card.dataset.slug === rec.item.slug)));
    const out = $('pathOut');
    out.replaceChildren();
    out.appendChild(make('p', 'eyebrow', `${rec.item.name} · ${titleCase(claim ? claim.status : 'not reviewed')}`));
    out.appendChild(make('h3', null, claim ? claim.claim : 'No reviewed claim yet.'));
    const flow = make('div', 'flow');
    ((claim && PATHWAYS[claim.id]) || []).forEach((step, i) => {
      if (i) { const arrow = make('b', null, '→'); arrow.setAttribute('aria-hidden', 'true'); flow.appendChild(arrow); }
      flow.appendChild(make('span', null, step));
    });
    out.appendChild(flow);
    out.appendChild(make('p', 'fine', `Source: ${rec.sources.map((s) => `${s.title} · ${s.publisher}`).join('; ')}`));
  }

  function renderReceipts() {
    const grid = $('receiptGrid');
    grid.replaceChildren();
    records.forEach((rec) => {
      const claim = rec.claims[0];
      const card = make('article', 'card receipt');
      card.id = `receipt-${rec.item.slug}`;
      const meta = make('div', 'rmeta');
      meta.append(make('span', null, `${rec.item.evidence_band} maturity`), make('span', null, claim ? `${claim.confidence} confidence` : ''));
      card.append(meta, make('h3', null, rec.item.name), make('p', 'claim', claim ? claim.claim : ''));

      const src = make('div', 'src');
      src.appendChild(make('span', null, rec.sources.length > 1 ? 'Sources' : 'Source'));
      rec.sources.forEach((s) => {
        const link = make('a', null, `${s.title} · ${s.publisher}`);
        link.href = s.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
        src.appendChild(link);
      });
      card.appendChild(src);

      const foot = make('div', 'receipt-foot');
      const details = make('details');
      details.appendChild(make('summary', null, 'Inspect receipt'));
      const body = make('div', 'receipt-body');
      const block = (label, content) => { const wrap = make('div'); wrap.appendChild(make('strong', null, label)); wrap.appendChild(content); body.appendChild(wrap); };
      if (claim) {
        block('Status', make('span', null, titleCase(claim.status)));
        const supports = make('ul');
        claim.source_claims.forEach((entry) => {
          const source = rec.sourceById.get(entry.source_id);
          supports.appendChild(make('li', null, `${entry.summary}${source ? ` (${source.publisher})` : ''}`));
        });
        block('What the sources support', supports);
        const limits = make('ul');
        claim.limitations.forEach((limit) => limits.appendChild(make('li', null, limit)));
        block('Limitations', limits);
      }
      block('Safety context', make('span', null, rec.item.safety_note));
      block('Reviewed', make('span', null, claim ? claim.last_reviewed : rec.item.reviewed_at));
      details.appendChild(body);
      const open = make('a', 'btn', 'Open on the evidence map');
      open.href = `./#${encodeURIComponent(rec.item.slug)}`;
      foot.append(details, open);
      card.appendChild(foot);
      grid.appendChild(card);
    });
  }

  function showLoadError() {
    const message = 'The reviewed records could not load. Reload the page, or open the evidence map.';
    $('pathOut').replaceChildren(make('p', 'status-note', message));
    $('receiptGrid').replaceChildren(make('p', 'status-note', message));
  }

  async function loadEvidence() {
    try {
      const [interventions, claims, sources] = await Promise.all([
        fetch('../data/interventions.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
        fetch('../data/claims.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
        fetch('../data/sources.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
      ]);
      records = buildRecords(interventions, claims, sources);
      $('claimCount').textContent = String(claims.length);
      $('sourceCount').textContent = String(sources.length);
      renderPathways();
      renderReceipts();
    } catch (error) {
      showLoadError();
    }
  }

  /* ---------------- guided reading ---------------- */
  const READING = {
    center: { id: 'center', label: 'The Nootroflix chart',
      simple: 'A scatter chart of 36,163 ratings from 2,802 people. It plots how often each intervention was rated “life-changing” against how many people rated it.',
      detail: 'It puts behaviors, diets, supplements, prescription drugs, research compounds and recreational drugs on one canvas. Read it as a map of what a self-selected online community found striking, not as a ranking of what works or what is safe.' },
    branches: [
      { id: 'origin', label: 'Origin', simple: 'A recommender system and a blog post, built on an earlier reader survey.', detail: 'The chart comes from the Troof blog’s 2022 analysis of Nootroflix ratings, which started from Slate Star Codex survey data.', leaves: [
        ['Nootroflix', 'A nootropics recommender. You rated what you had tried, and it predicted what else you might like.', 'Analysed in “What I learned gathering thousands of nootropic ratings” on the Troof blog (March 23, 2022).'],
        ['Slate Star Codex seed', 'It started from the 2016 Slate Star Codex nootropics survey.', 'Nootroflix combined that earlier reader survey with its own new ratings.'],
        ['36,163 ratings', '1,981 new people added 29,387 ratings. With the survey data: 36,163 ratings from 2,802 people.', 'Each person rated only what they had tried, so popular items collected hundreds of ratings while rare compounds may have ten or fewer.'],
        ['Who rated', 'Volunteers from blogs about rationality and self-experimentation.', 'They are more likely than most people to try unusual compounds and to expect strong effects. Every pattern on the chart describes this group, not people in general.']] },
      { id: 'reading', label: 'How to read it', simple: 'Two axes and one rating scale.', detail: 'Horizontal is how many people rated an item. Vertical is the modelled chance that a rating was a 10.', leaves: [
        ['Across: ratings', 'Further right means more people rated it. The scale is logarithmic: 10, 100, 1,000.', 'This measures popularity inside the dataset. It is not the number of scientific studies and says nothing about whether an effect is proven.'],
        ['Up: rated a 10', 'Higher means a larger share of raters gave it a 10, “life-changing”.', 'The analysis modelled people and items separately, so habitually generous raters count for less, and items with few ratings are pulled toward the average.'],
        ['The −0.006 tick', 'A probability cannot be negative. Treat that bottom tick on the published image as a drawing artifact.', 'It most likely comes from the axis transformation used to render the plot. Without the plotting code, give it no meaning.'],
        ['What “10” means', 'On the rating scale, 10 meant a strongly positive, life-changing effect on cognition.', 'The author notes that some people probably did not read the scale description and gave 10 to anything very good. The vertical values may therefore run high.']] },
      { id: 'boxes', label: 'The colored boxes', simple: 'Green and red mark two corners the author found interesting. Neither color means safe or unsafe.', detail: 'Gray covers everything else. All three describe rating patterns.', leaves: [
        ['Green box', 'Uncommon but great: few ratings, many 10s.', 'Research compounds and brain-stimulation methods sit here. It is also where small samples make results least reliable. Green does not mean safe or recommended.'],
        ['Red box', 'Common but mediocre: many ratings, few 10s.', 'Well-studied staples such as creatine, magnesium, theanine, melatonin and omega-3 land here. That means they rarely felt life-changing, not that they do nothing.'],
        ['Gray field', 'Everything outside the two boxes.', 'It holds many recreational drugs, research chemicals and prescription medicines. Gray is a leftover area, not a safety category.'],
        ['Upper right', 'Widely rated and often a 10.', 'Behaviors such as doing math, weightlifting and trying to get more sleep share this corner with prescription stimulants.']] },
      { id: 'contents', label: 'What’s on it', simple: 'Roughly three hundred entries across very different kinds of intervention.', detail: '“Nootropic” here means anything people tried for cognition. The mix is the point, and also the risk.', leaves: [
        ['Behaviors', 'Doing math, weightlifting, HIIT, low-intensity cardio, meditation, trying to get more sleep.', 'Free, widely available and low-risk for most people, yet several rate alongside potent drugs.'],
        ['Environment', 'Bright morning light, cold showers, 40 Hz light flicker.', 'Inputs from surroundings rather than substances. Morning light has a well-documented role in setting the body clock.'],
        ['Diet & supplements', 'Creatine, omega-3, magnesium, vitamin D, theanine, ketogenic diet, intermittent fasting.', 'Popular, often studied, and rarely dramatic on this chart.'],
        ['Prescription drugs', 'Stimulants, modafinil, antidepressants and sedatives also appear.', 'Strong, noticeable effects score well on this kind of chart. These drugs carry real risks and need a prescriber; a self-report rating is no guide to who should take them.'],
        ['Research compounds', 'Peptides and experimental molecules studied mostly in cells or animals.', 'Preclinical findings are not evidence of benefit or safety in healthy people.'],
        ['Recreational & risky', 'The source also lists recreational drugs and opioids.', 'People were asked only about cognitive effects, and the author warns that items on the list can be very dangerous. Being on the chart is not an endorsement.']] },
      { id: 'misleads', label: 'Why it misleads', simple: 'The chart collects experiences, not experiments.', detail: 'Five biases overlap, and they are strongest exactly where the chart looks most exciting.', leaves: [
        ['Self-selection', 'People who join a nootropics recommender are not typical.', 'They self-experiment more, expect more and tolerate more risk. Rare compounds are tried mostly by the most committed.'],
        ['Small samples', 'Top-left items rest on a handful of ratings.', 'With ten ratings, a few enthusiasts decide the result. Extreme small-sample winners tend to fall back when measured again.'],
        ['No blinding', 'Everyone knew what they had taken.', 'Expectation, effort and price shape how strongly people feel an effect. There is no placebo comparison anywhere in the data.'],
        ['Salience ≠ efficacy', 'Obvious effects feel bigger than slow ones.', 'A fast, noticeable effect is easy to call life-changing. A benefit that builds over months is easy to underrate.'],
        ['One crude number', 'Benefit, side effects, dose and duration are squeezed into one 0–10 rating.', 'Two people giving a 7 might mean very different things, and harms are not plotted at all.']] },
      { id: 'teaches', label: 'What it teaches', simple: 'Its value is the questions it raises.', detail: 'Read correctly, the chart is a hypothesis generator about human capability.', leaves: [
        ['Behavior competes', 'Exercise and sleep held their own against drugs.', 'The author’s own conclusion: sport, especially weightlifting, and sleep were rated very highly.'],
        ['Signal ≠ truth', 'Finding a surprise and confirming it are different jobs.', 'A discovery step surfaces unusual signals. A verification step tests whether they survive independent, controlled study.'],
        ['Never one score', 'A single ranking hides what matters.', 'Evidence quality, effect size, risk, cost, durability and access are separate dimensions.'],
        ['Lowest-risk first', 'Look at the cheapest, safest layers first.', 'Environment, behavior, learning and nutrition come before medical care, and medical care before anything experimental.'],
        ['Ask, don’t prescribe', 'Use it to ask “what deserves study?”, never “what should I take?”', 'Decisions about medicines belong with a clinician.']] },
      { id: 'built', label: 'What we built', simple: 'Nootropics Map: an evidence-first companion to charts like this one.', detail: 'Every claim on the evidence map traces to a public source.', leaves: [
        ['Evidence receipts', 'Every claim links to its sources, limitations and review date.', 'The site is a presentation layer over structured records: source, claim, evidence state, intervention, then the visual.'],
        ['Maturity × confidence', 'The map plots evidence maturity against confidence, not popularity.', 'Both axes are ordinal and educational. Neither is an effect size, and nothing is ranked.'],
        ['Five, carefully', 'The first release covers sleep, physical activity, creatine, morning light and meditation.', 'Breadth comes after the architecture is proven.'],
        ['Signal held back', 'The community signal layer is not part of the product yet.', 'It needs a provenance-complete dataset, its own methodology and uncertainty labels first.'],
        ['Why trust this?', 'A button on the map shows how conclusions were reached.', 'Method, sources, limitations and review dates are one click away.']] },
      { id: 'checked', label: 'How it’s checked', simple: 'Every change passes the same automated checks before it can ship.', detail: 'Checks run on every pull request, and publishing is a separate, deliberate step.', leaves: [
        ['Evidence validation', 'Every claim must cite sources that exist.', 'The build fails if a claim cites a missing source or an intervention points to a missing claim.'],
        ['Required checks', 'Changes reach the main branch only through a pull request with passing checks.', 'The required check covers evidence validation, a public-boundary scan, accessibility and contrast checks, JavaScript tests and a deployment test.'],
        ['Accessibility', 'Structure, labels, reduced motion and contrast are tested automatically.', 'Automated checks are not a substitute for testing with real assistive technology.'],
        ['Reproducible builds', 'The published site is rebuilt from source the same way every time.', 'Generated files are normalized so builds match across operating systems.'],
        ['Manual publication', 'Nothing goes live automatically.', 'Publishing happens only after checks pass, so a merge alone never changes the live site.']] }
    ]
  };

  const NODES = [{ kind: 'center', ...READING.center }];
  READING.branches.forEach((branch, bi) => {
    branch.num = String(bi + 1).padStart(2, '0');
    NODES.push({ kind: 'branch', id: branch.id, label: branch.label, simple: branch.simple, detail: branch.detail, branch });
    branch.leaves.forEach(([label, simple, detail], li) => NODES.push({ kind: 'leaf', id: `${branch.id}-${li}`, label, simple, detail, branch }));
  });
  let current = 0;

  const orbit = $('orbit');
  const C = 300, R = 196;
  const nodeEls = {}, lines = {};
  svgEl('circle', { class: 'o-ring', cx: C, cy: C, r: 118 }, orbit);
  svgEl('circle', { class: 'o-ring', cx: C, cy: C, r: R }, orbit);
  READING.branches.forEach((branch, i) => {
    const a = (-90 + i * 45) * Math.PI / 180;
    branch.x = C + R * Math.cos(a); branch.y = C + R * Math.sin(a); branch.a = a;
    lines[branch.id] = svgEl('line', { class: 'o-line', x1: C + 70 * Math.cos(a), y1: C + 70 * Math.sin(a), x2: branch.x - 12 * Math.cos(a), y2: branch.y - 12 * Math.sin(a) }, orbit);
  });
  const activate = (node, handler) => {
    node.addEventListener('click', handler);
    node.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handler(); } });
  };
  const center = svgEl('g', { class: 'o-node', tabindex: '0', role: 'button', 'aria-label': 'The Nootroflix chart, center' }, orbit);
  svgEl('circle', { class: 'hit', cx: C, cy: C, r: 74 }, center);
  svgEl('circle', { class: 'o-center', cx: C, cy: C, r: 70 }, center);
  svgEl('text', { class: 'o-ctitle', x: C, y: C - 4, 'text-anchor': 'middle' }, center).textContent = 'Nootroflix';
  svgEl('text', { class: 'o-ctitle', x: C, y: C + 20, 'text-anchor': 'middle', 'font-style': 'italic' }, center).textContent = 'chart';
  svgEl('text', { class: 'o-csub', x: C, y: C + 42, 'text-anchor': 'middle' }, center).textContent = '36,163 ratings';
  nodeEls.center = center;
  activate(center, () => go(0));
  READING.branches.forEach((branch) => {
    const g = svgEl('g', { class: 'o-node', tabindex: '0', role: 'button', 'aria-label': `${branch.num} ${branch.label}` }, orbit);
    const above = Math.sin(branch.a) < -0.1;
    const ly = above ? branch.y - 44 : branch.y + 50;
    const w = branch.label.length * 10 + 28;
    svgEl('rect', { class: 'hit', x: branch.x - w / 2, y: Math.min(branch.y, ly) - 26, width: w, height: Math.abs(ly - branch.y) + 46, rx: 10 }, g);
    svgEl('circle', { class: 'o-dot', cx: branch.x, cy: branch.y, r: 11 }, g);
    svgEl('circle', { class: 'o-core', cx: branch.x, cy: branch.y, r: 4 }, g);
    svgEl('text', { class: 'o-num halo', x: branch.x, y: ly - 22, 'text-anchor': 'middle' }, g).textContent = branch.num;
    svgEl('text', { class: 'o-label halo', x: branch.x, y: ly + 2, 'text-anchor': 'middle' }, g).textContent = branch.label;
    nodeEls[branch.id] = g;
    activate(g, () => go(NODES.findIndex((n) => n.id === branch.id)));
  });
  const branchList = $('branchList');
  READING.branches.forEach((branch) => {
    const chip = make('button', 'chip', `${branch.num} ${branch.label}`);
    chip.type = 'button'; chip.dataset.branch = branch.id;
    chip.addEventListener('click', () => go(NODES.findIndex((n) => n.id === branch.id)));
    branchList.appendChild(chip);
  });

  function go(index) {
    current = Math.max(0, Math.min(NODES.length - 1, index));
    const node = NODES[current];
    const branchId = node.kind === 'center' ? null : node.branch.id;
    $('readEyebrow').textContent = node.kind === 'center' ? 'Center' : node.kind === 'branch' ? `Branch ${node.branch.num}` : `${node.branch.num} · ${node.branch.label}`;
    $('readNodeTitle').textContent = node.label;
    $('readSimple').textContent = node.simple;
    $('readDetail').textContent = node.detail;
    $('readCount').textContent = `${current + 1} / ${NODES.length}`;
    $('readPrev').disabled = current === 0;
    $('readNext').disabled = current === NODES.length - 1;
    Object.entries(nodeEls).forEach(([key, el]) => el.classList.toggle('active', key === (branchId || 'center')));
    Object.entries(lines).forEach(([key, line]) => line.classList.toggle('lit', branchId ? key === branchId : true));
    branchList.querySelectorAll('.chip').forEach((chip) => chip.setAttribute('aria-pressed', String(chip.dataset.branch === branchId)));
    const leaves = $('readLeaves');
    leaves.replaceChildren();
    const targets = node.kind === 'center'
      ? READING.branches.map((b) => NODES.findIndex((n) => n.id === b.id))
      : NODES.map((_, j) => j).filter((j) => NODES[j].kind === 'leaf' && NODES[j].branch.id === branchId);
    targets.forEach((j) => {
      const chip = make('button', 'chip', NODES[j].label);
      chip.type = 'button';
      chip.setAttribute('aria-pressed', String(j === current));
      chip.addEventListener('click', () => go(j));
      leaves.appendChild(chip);
    });
  }
  $('readPrev').addEventListener('click', () => go(current - 1));
  $('readNext').addEventListener('click', () => go(current + 1));
  $('reading').addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea')) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); go(current + 1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(current - 1); }
  });

  function setDepth(depth) {
    document.documentElement.dataset.depth = depth;
    document.querySelectorAll('button[data-depth]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.depth === depth)));
    try { localStorage.setItem('nootropics-map-depth', depth); } catch (e) { /* storage unavailable */ }
  }
  document.querySelectorAll('button[data-depth]').forEach((b) => b.addEventListener('click', () => setDepth(b.dataset.depth)));
  let savedDepth = null;
  try { savedDepth = localStorage.getItem('nootropics-map-depth'); } catch (e) { /* storage unavailable */ }
  setDepth(savedDepth === 'detailed' ? 'detailed' : 'simple');

  go(0);
  loadEvidence();
})();
